import os
import sys
import time
import requests
from websocket import create_connection

# Add parent dir to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_session_manager():
    java_code = """
import java.util.Scanner;

public class TestManager {
    public static void main(String[] args) throws Exception {
        Scanner sc = new Scanner(System.in);
        System.out.print("Enter a number: ");
        if (sc.hasNextInt()) {
            int num = sc.nextInt();
            System.out.println("You entered: " + num);
        } else {
            System.out.println("No input received.");
        }
    }
}
"""

    email = f"ws_test_{int(time.time())}@example.com"
    username = f"ws_test_{int(time.time())}"
    password = "TestPass123"

    session_id = None
    token = None
    headers = None

    try:
        print("Registering test user...")
        auth_response = requests.post(
            "http://127.0.0.1:5001/api/auth/register",
            json={"email": email, "username": username, "password": password},
            timeout=10
        )
        auth_response.raise_for_status()
        token = auth_response.json().get("access_token")
        headers = {"Authorization": f"Bearer {token}"}

        print("Starting terminal session...")
        start_response = requests.post(
            "http://127.0.0.1:5001/api/compiler/terminal/start",
            json={"code": java_code, "language": "java"},
            headers=headers,
            timeout=30
        )
        start_response.raise_for_status()
        start_data = start_response.json()
        session_id = start_data.get("session_id")
        ws_url = start_data.get("ws_url")
        print(f"Session started: {session_id}")
        print(f"WS URL: {ws_url}")

        ws = create_connection(ws_url)
        ws.settimeout(5)

        msg1 = ws.recv()
        print(f"Received: {msg1}")
        ws.send("42\n")
        time.sleep(0.2)
        msg2 = ws.recv()
        print(f"Received: {msg2}")
        try:
            msg3 = ws.recv()
            print(f"Received: {msg3}")
        except Exception as e:
            print(f"Receive end: {e}")
        ws.close()
    except Exception as e:
        print(f"WebSocket test failed: {e}")
    finally:
        if session_id and headers:
            print("Stopping session...")
            try:
                requests.post(
                    "http://127.0.0.1:5001/api/compiler/terminal/stop",
                    json={"session_id": session_id},
                    headers=headers,
                    timeout=10
                )
            except Exception as e:
                print(f"Stop failed: {e}")

if __name__ == "__main__":
    test_session_manager()
