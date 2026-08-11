# Emergent Google Auth Testing Checklist

1. Seed a test user and a seven-day session in MongoDB using a custom `user_id`.
2. Verify `GET /api/auth/me` with an Authorization bearer token.
3. Verify protected saved-reading GET/POST requests only return data for the authenticated user.
4. Set an httpOnly `session_token` cookie in Playwright and confirm the dashboard loads.
5. Verify the Google login button uses the current browser origin and the OAuth callback exchanges `session_id` server-side.
6. Verify logout clears the session and returns to the sign-in screen.