# OAuth Setup Guide

## Required Environment Variables

Set these in `backend/.env`:

```
FRONTEND_BASE_URL=http://localhost:8080
BACKEND_PUBLIC_BASE_URL=http://localhost:5001

GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
GOOGLE_REDIRECT_URI=http://localhost:8080/auth/google/callback

GITHUB_CLIENT_ID=your-github-client-id
GITHUB_CLIENT_SECRET=your-github-client-secret
GITHUB_REDIRECT_URI=http://localhost:8080/auth/github/callback
```

## Google OAuth Console Setup

1. Open Google Cloud Console.
2. Go to APIs & Services → Credentials.
3. Create OAuth 2.0 Client ID (Web application).
4. Add Authorized redirect URI:
   - `http://localhost:8080/auth/google/callback`
5. Copy Client ID and Client Secret into `.env`.

## GitHub OAuth App Setup

1. Open GitHub Settings → Developer settings → OAuth Apps.
2. Create New OAuth App.
3. Set Homepage URL:
   - `http://localhost:8080`
4. Set Authorization callback URL:
   - `http://localhost:8080/auth/github/callback`
5. Copy Client ID and Client Secret into `.env`.

## Backend Endpoints Used

- Google:
  - `GET /api/auth/google/url`
  - `POST /api/auth/google/callback`
- GitHub:
  - `GET /api/auth/github/url`
  - `POST /api/auth/github/callback`

## Frontend Routes Used

- Google callback:
  - `/auth/google/callback`
- GitHub callback:
  - `/auth/github/callback`

## Run After Configuration

1. Restart backend.
2. Restart frontend.
3. Test login/signup with Google and GitHub buttons.
