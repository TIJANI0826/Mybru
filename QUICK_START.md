# Quick Start Guide

## Starting the Backend

1. Open a terminal in the `backend` folder
2. Activate the virtual environment:
   ```bash
   venv\Scripts\activate
   ```
3. Run migrations (if not done yet):
   ```bash
   python manage.py migrate
   ```
4. Start the development server:
   ```bash
   python manage.py runserver
   ```
   The API will be available at: `http://localhost:8000/api/`

## Starting the Frontend

1. Open another terminal in the `frontend` folder
2. You can use a simple HTTP server or any local server
3. For Python 3:
   ```bash
   python -m http.server 3000
   ```
4. Access the frontend at: `http://localhost:3000/`

## Configuration Checklist

Before running the application:

- [ ] Copy `.env.example` to `.env` in the backend folder
- [ ] Add your Google OAuth2 credentials to `.env`
- [ ] Update Google Client ID in `login.html` and `signup.html`
- [ ] Update `FRONTEND_URL` in `.env` if using a different port
- [ ] Run `python manage.py migrate` to set up the database
- [ ] Test authentication endpoints using Postman or curl

## Available Endpoints

### Authentication
- `POST /api/auth/register/` - Create new account
- `POST /api/auth/login/` - Login with credentials
- `GET /api/auth/profile/` - Get current user (requires token)
- `POST /api/auth/logout/` - Logout user
- `POST /api/auth/google/login/` - Login with Google OAuth

### Tea Shop
- `GET /api/teas/` - List all teas
- `GET /api/teas/{id}/` - Get specific tea
- `GET /api/memberships/` - List memberships
- `POST /api/orders/` - Create order (requires authentication)

## Common Issues & Solutions

### Port Already in Use
- Backend (8000): `python manage.py runserver 8001`
- Frontend (3000): `python -m http.server 8001`

### Module Not Found
- Ensure virtual environment is activated
- Run: `pip install -r requirements.txt` (if exists)

### Database Errors
- Run: `python manage.py makemigrations`
- Run: `python manage.py migrate`
- Run: `python manage.py createsuperuser` for admin

### CORS Errors
- Check that backend is running
- Update `FRONTEND_URL` in `.env` if needed
- Make sure frontend port matches in `.env`

### Google OAuth Not Working
- Verify Google Client ID in HTML files
- Check OAuth credentials in `.env`
- Ensure redirect URIs are configured in Google Console

## Admin Panel

Access Django admin at: `http://localhost:8000/admin/`
Use the superuser credentials created with `createsuperuser` command.

## Next Steps

1. Test the complete authentication flow
2. Integrate authentication with existing pages
3. Add user profile management features
4. Implement email verification (optional)
5. Add product management in admin panel
6. Set up payment integration with Paystack
