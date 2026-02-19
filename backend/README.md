# CodeMaster Backend

Flask backend API for CodeMaster - AI-Powered Code Development Platform.

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

Copy `.env.example` to `.env` and update the configuration:

```bash
cp .env.example .env
```

Edit `.env` with your database, AI service, and other configurations.

### 3. Setup Database

Make sure PostgreSQL is running and update `DATABASE_URL` in `.env`.

Example for PostgreSQL 16 on port 5433:

```bash
DATABASE_URL=postgresql://postgres:admin@localhost:5433/codemaster
```

Install the PostgreSQL driver if needed:

```bash
pip install psycopg2-binary
```

Then run migrations:

```bash
flask db init
flask db migrate -m "Initial migration"
flask db upgrade
```

Create tables and seed the admin user:

```bash
python flask_bootstrap.py
```

### 4. Run the Application

```bash
python run.py
```

Or using Flask CLI:

```bash
flask run
```

The API will be available at `http://localhost:5000`

## API Endpoints

- `/api/health` - Health check
- `/api/auth/*` - Authentication endpoints
- `/api/profile/*` - Profile and account management endpoints
- `/api/generator/*` - Code generation endpoints
- `/api/explainer/*` - Code explanation endpoints
- `/api/compiler/*` - Compiler endpoints
- `/api/assessment/*` - Assessment endpoints
- `/api/analytics/*` - Analytics endpoints
- `/api/dashboard/*` - Dashboard endpoints
- `/api/settings/*` - User settings endpoints

## Account Management API

- `POST /api/profile/password` - Update password with current password and CSRF token
- `DELETE /api/profile` - Delete account with password confirmation and CSRF token
- `GET /api/auth/csrf` - Fetch CSRF token for authenticated sessions

### Request Headers

- `Authorization: Bearer <access_token>`
- `X-CSRF-Token: <csrf_token>`

### Password Update Payload

```json
{
  "current_password": "OldPassword1!",
  "new_password": "NewPassword1!"
}
```

### Account Deletion Payload

```json
{
  "password": "CurrentPassword1!"
}
```

## User Schema Additions

- `password_updated_at` - Timestamp for last password change
- `deletion_requested_at` - Timestamp for deletion requests
- `deleted_at` - Timestamp for soft deletion
- `csrf_token` - CSRF token for account actions

## Email Configuration

Set these in `.env` to enable deletion confirmation email:

- `SMTP_HOST`
- `SMTP_PORT`
- `SMTP_USERNAME`
- `SMTP_PASSWORD`
- `SMTP_USE_TLS`
- `SMTP_FROM_EMAIL`

## Development

```bash
FLASK_ENV=development flask run
```

## Testing

```bash
pytest
```
