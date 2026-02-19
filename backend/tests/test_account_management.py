import unittest
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app import create_app, db
from app.models.user import User


class AccountManagementTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app('testing')
        self.app.config['TESTING'] = True
        self.app.config['JWT_SECRET_KEY'] = 'test-secret-key-32bytes-long-123456'
        self.client = self.app.test_client()
        with self.app.app_context():
            db.create_all()
            user = User(email='test@example.com', username='tester')
            user.set_password('Test1234!')
            user.ensure_csrf_token()
            db.session.add(user)
            db.session.commit()

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def _login(self, email: str, password: str):
        response = self.client.post('/api/auth/login', json={'email': email, 'password': password})
        return response

    def test_password_update_flow(self):
        login_response = self._login('test@example.com', 'Test1234!')
        self.assertEqual(login_response.status_code, 200)
        data = login_response.get_json()
        token = data['access_token']
        csrf_token = data['csrf_token']

        update_response = self.client.post(
            '/api/profile/password',
            json={'current_password': 'Test1234!', 'new_password': 'Newpass123!'},
            headers={'Authorization': f'Bearer {token}', 'X-CSRF-Token': csrf_token}
        )
        self.assertEqual(update_response.status_code, 200)

        profile_response = self.client.get('/api/profile', headers={'Authorization': f'Bearer {token}'})
        self.assertEqual(profile_response.status_code, 401)

        relogin_response = self._login('test@example.com', 'Newpass123!')
        self.assertEqual(relogin_response.status_code, 200)

    def test_account_delete_flow(self):
        login_response = self._login('test@example.com', 'Test1234!')
        self.assertEqual(login_response.status_code, 200)
        data = login_response.get_json()
        token = data['access_token']
        csrf_token = data['csrf_token']

        delete_response = self.client.delete(
            '/api/profile',
            json={'password': 'Test1234!'},
            headers={'Authorization': f'Bearer {token}', 'X-CSRF-Token': csrf_token}
        )
        self.assertEqual(delete_response.status_code, 200)

        login_again = self._login('test@example.com', 'Test1234!')
        self.assertEqual(login_again.status_code, 401)


if __name__ == '__main__':
    unittest.main()
