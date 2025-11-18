from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework.authtoken.models import Token
from social_django.models import UserSocialAuth
from django.contrib.auth.models import User
import json


@api_view(['POST'])
@permission_classes([AllowAny])
def google_oauth_callback(request):
    """
    Handle Google OAuth callback.
    Expected POST data: { 'access_token': '<google_access_token>' }
    """
    access_token = request.data.get('access_token')
    
    if not access_token:
        return Response({'error': 'Access token is required'}, status=400)
    
    try:
        # Use social-auth-app-django to authenticate with Google
        from social_core.backends.google import GoogleOAuth2
        backend = GoogleOAuth2()
        
        # Get user info from Google
        user_data = backend.user_data(access_token)
        
        # Get or create user
        email = user_data.get('email')
        first_name = user_data.get('given_name', '')
        last_name = user_data.get('family_name', '')
        
        if not email:
            return Response({'error': 'Email not provided by Google'}, status=400)
        
        # Try to get user by email
        user, created = User.objects.get_or_create(
            email=email,
            defaults={
                'username': email.split('@')[0],
                'first_name': first_name,
                'last_name': last_name,
            }
        )
        
        # Create or update UserSocialAuth
        UserSocialAuth.objects.get_or_create(
            user=user,
            provider='google-oauth2',
            defaults={'uid': user_data.get('id', email)}
        )
        
        # Get or create token
        token, _ = Token.objects.get_or_create(user=user)
        
        return Response({
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
            },
            'token': token.key
        }, status=200)
        
    except Exception as e:
        return Response({'error': f'OAuth error: {str(e)}'}, status=400)


@api_view(['POST'])
@permission_classes([AllowAny])
def google_oauth_login(request):
    """
    Authenticate user with Google using ID token from frontend.
    Expected POST data: { 'id_token': '<google_id_token>' }
    """
    id_token = request.data.get('id_token')
    
    if not id_token:
        return Response({'error': 'ID token is required'}, status=400)
    
    try:
        from google.oauth2 import id_token
        from google.auth.transport import requests
        from django.conf import settings
        
        # Verify the token
        idinfo = id_token.verify_oauth2_token(
            id_token,
            requests.Request(),
            settings.SOCIAL_AUTH_GOOGLE_OAUTH2_KEY
        )
        
        # Get user info
        email = idinfo.get('email')
        first_name = idinfo.get('given_name', '')
        last_name = idinfo.get('family_name', '')
        
        if not email:
            return Response({'error': 'Email not provided by Google'}, status=400)
        
        # Get or create user
        user, created = User.objects.get_or_create(
            email=email,
            defaults={
                'username': email.split('@')[0],
                'first_name': first_name,
                'last_name': last_name,
            }
        )
        
        # Create or update UserSocialAuth
        UserSocialAuth.objects.get_or_create(
            user=user,
            provider='google-oauth2',
            defaults={'uid': idinfo.get('sub')}
        )
        
        # Get or create token
        token, _ = Token.objects.get_or_create(user=user)
        
        return Response({
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
            },
            'token': token.key
        }, status=200)
        
    except ValueError as e:
        return Response({'error': f'Invalid token: {str(e)}'}, status=400)
    except Exception as e:
        return Response({'error': f'Authentication error: {str(e)}'}, status=400)
