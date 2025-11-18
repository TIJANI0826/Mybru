# Authentication Setup Guide

## Overview
This guide covers the setup and integration of user authentication with Django backend and Google OAuth2 for the myBru project.

## Backend Setup

### 1. Install Required Packages
All required packages have been installed in your virtual environment:
- `djangorestframework` - REST API framework
- `djoser` - User authentication endpoints
- `django-cors-headers` - CORS support
- `python-decouple` - Environment variable management
- `google-auth-oauthlib` - Google OAuth support
- `pyjwt` - JWT token support
- `rest_framework_simplejwt` - Simple JWT implementation
- `social-auth-app-django` - Social authentication

### 2. Environment Variables Setup
Copy `.env.example` to `.env` and configure:

```bash
cd backend
cp .env.example .env
```

Edit `.env` with your actual values:
- `SECRET_KEY` - Django secret key (keep it secret in production!)
- `DEBUG` - Set to False in production
- `GOOGLE_OAUTH2_KEY` - Your Google OAuth2 Client ID
- `GOOGLE_OAUTH2_SECRET` - Your Google OAuth2 Client Secret
- `FRONTEND_URL` - Your frontend URL (default: http://localhost:3000)

### 3. Get Google OAuth2 Credentials

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the Google+ API
4. Go to "Credentials" and create an OAuth 2.0 Client ID (Web application)
5. Add authorized redirect URIs:
   - `http://localhost:8000/api/social-auth/google-oauth2-callback/`
   - `http://127.0.0.1:8000/api/social-auth/google-oauth2-callback/`
   - `http://localhost:3000` (for frontend)
6. Copy the Client ID and Client Secret to your `.env` file

### 4. Run Migrations

```bash
cd backend
venv\Scripts\python manage.py makemigrations
venv\Scripts\python manage.py migrate
```

### 5. Create a Superuser (Admin)

```bash
venv\Scripts\python manage.py createsuperuser
```

### 6. Start the Django Server

```bash
venv\Scripts\python manage.py runserver
```

The API will be available at: `http://localhost:8000/api/`

## API Endpoints

### Authentication Endpoints

#### Register a New User
- **URL:** `POST /api/auth/register/`
- **Body:**
```json
{
    "username": "newuser",
    "email": "user@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "password": "securepassword123",
    "password2": "securepassword123"
}
```
- **Response:** User object and token

#### Login
- **URL:** `POST /api/auth/login/`
- **Body:**
```json
{
    "username": "newuser",
    "password": "securepassword123"
}
```
- **Response:** User object and token

#### Get User Profile
- **URL:** `GET /api/auth/profile/`
- **Headers:** `Authorization: Token <your-token>`
- **Response:** Current user's profile information

#### Logout
- **URL:** `POST /api/auth/logout/`
- **Headers:** `Authorization: Token <your-token>`
- **Response:** Success message

#### Google OAuth Login
- **URL:** `POST /api/auth/google/login/`
- **Body:**
```json
{
    "id_token": "<google-id-token>"
}
```
- **Response:** User object and token

## Frontend Setup

### 1. Update Frontend Files
The following files have been created/updated:
- `frontend/login.html` - Login page with Google OAuth button
- `frontend/signup.html` - Sign up page with Google OAuth button
- `frontend/js/main.js` - Updated with authentication support

### 2. Configure Google OAuth in Frontend
Update the Google Client ID in both `login.html` and `signup.html`:

```javascript
client_id: 'YOUR_GOOGLE_CLIENT_ID_HERE', // Replace with your actual Client ID
```

### 3. Update HTML Pages
Update your other HTML pages to include links to login/signup in the navigation:

```html
<nav>
    <ul>
        <li><a href="home.html">Home</a></li>
        <li><a href="login.html">Login</a></li>
        <li><a href="signup.html">Sign Up</a></li>
        <li><a href="cart.html">Cart</a></li>
    </ul>
</nav>
```

### 4. Authentication in Frontend
The frontend stores the authentication token in localStorage:
- Key: `token` - Your API token
- Key: `user` - Current user object (JSON)

Use the token for authenticated requests:

```javascript
const token = localStorage.getItem('token');
const headers = {
    'Content-Type': 'application/json',
    'Authorization': `Token ${token}`
};
```

## Testing

### Test Traditional Authentication
1. Go to `http://localhost:3000/signup.html`
2. Create a new account
3. You should be redirected to the home page
4. Try logging out and logging back in

### Test Google OAuth
1. Go to `http://localhost:3000/login.html`
2. Click "Continue with Google"
3. Sign in with your Google account
4. You should be automatically logged in

### Test API Endpoints
Using curl or Postman:

```bash
# Register
curl -X POST http://localhost:8000/api/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","email":"test@example.com","password":"testpass123","password2":"testpass123"}'

# Login
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","password":"testpass123"}'

# Get Profile (replace TOKEN with actual token)
curl -X GET http://localhost:8000/api/auth/profile/ \
  -H "Authorization: Token TOKEN"
```

## File Structure

```
backend/
├── mybrutea_backend/
│   ├── settings.py          # Updated with auth config
│   ├── urls.py              # Updated with auth URLs
│   └── ...
├── shop/
│   ├── views.py             # Added auth views
│   ├── serializers.py       # Added custom user serializers
│   ├── oauth_views.py       # Google OAuth handlers
│   ├── urls.py              # Updated with auth endpoints
│   └── ...
├── .env                     # Environment variables (local)
├── .env.example             # Template for .env
└── requirements.txt         # (recommended to create)

frontend/
├── login.html               # NEW: Login page
├── signup.html              # NEW: Sign up page
├── js/main.js               # Updated with auth support
└── ...
```

## Troubleshooting

### CORS Issues
If you get CORS errors, make sure:
1. `CORS_ALLOWED_ORIGINS` in `.env` includes your frontend URL
2. The Django server is running
3. Frontend and backend are on different ports

### Google OAuth Not Working
- Verify your Google Client ID and Secret in `.env`
- Check that redirect URIs are properly configured in Google Cloud Console
- Ensure the frontend URL matches your `FRONTEND_URL` in `.env`

### Token Errors
- Clear localStorage if you change servers
- Verify the token format: `Token <your-token-here>`
- Make sure the token hasn't expired

### Database Issues
- Run migrations: `python manage.py migrate`
- Clear database if needed: `rm db.sqlite3` (development only!)
- Run migrations again

## Security Notes

⚠️ **Important for Production:**
1. Set `DEBUG=False` in `.env`
2. Use a strong `SECRET_KEY`
3. Set `ALLOWED_HOSTS` to your actual domain
4. Use HTTPS for all endpoints
5. Don't commit `.env` file to version control
6. Use environment-specific settings
7. Enable CSRF protection properly
8. Set secure cookie flags

## Next Steps

1. Test authentication flows thoroughly
2. Implement user profile management
3. Add email verification
4. Implement password reset functionality
5. Add user roles and permissions
6. Implement more OAuth providers if needed
7. Add 2FA/MFA for enhanced security

## Support

For more information, refer to:
- [Django REST Framework](https://www.django-rest-framework.org/)
- [Djoser Documentation](https://djoser.readthedocs.io/)
- [Google OAuth 2.0](https://developers.google.com/identity/protocols/oauth2)
- [Social Auth App Django](https://python-social-auth.readthedocs.io/)
