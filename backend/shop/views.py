from rest_framework import viewsets, status
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.authtoken.models import Token
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from django.utils import timezone
from datetime import timedelta

from .models import Tea, Ingredient, Cart, Order, Membership, PickupLocation, IngredientCategory, Subscription, Payment, Profile
from .models import DeliveryAddress
from .serializers import TeaSerializer, IngredientSerializer, CartSerializer, OrderSerializer, MembershipSerializer, CustomUserSerializer, CustomUserCreateSerializer, PickupLocationSerializer, DeliveryAddressSerializer, IngredientCategorySerializer, SubscriptionSerializer, PaymentSerializer, ProfileSerializer, UserDetailedSerializer

class TeaViewSet(viewsets.ModelViewSet):
    queryset = Tea.objects.all()
    serializer_class = TeaSerializer
    permission_classes = [AllowAny]

class IngredientViewSet(viewsets.ModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = [AllowAny]

class CartViewSet(viewsets.ModelViewSet):
    queryset = Cart.objects.all()
    serializer_class = CartSerializer
    permission_classes = [IsAuthenticated]

class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
    
    def get_queryset(self):
        user = self.request.user
        # staff users can see all orders; regular users only their own
        if user.is_staff or user.is_superuser:
            return Order.objects.all()
        return Order.objects.filter(user=user)

class MembershipViewSet(viewsets.ModelViewSet):
    queryset = Membership.objects.all()
    serializer_class = MembershipSerializer
    permission_classes = [AllowAny]  # Anyone can view membership tiers


class SubscriptionViewSet(viewsets.ModelViewSet):
    serializer_class = SubscriptionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Users see only their own subscriptions; staff see all
        user = self.request.user
        if user.is_staff or user.is_superuser:
            return Subscription.objects.all()
        return Subscription.objects.filter(user=user)

    def perform_create(self, serializer):
        subscription = serializer.save()
        # Update the user's profile current_membership to this membership
        try:
            profile, created = Profile.objects.get_or_create(user=self.request.user)
            profile.current_membership = subscription.membership
            profile.save()
        except Exception:
            # If updating profile fails, we still return the created subscription
            pass

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def cancel(self, request, pk=None):
        """Cancel a subscription"""
        subscription = self.get_object()
        if subscription.user != request.user and not request.user.is_staff:
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
        
        subscription.status = 'cancelled'
        subscription.end_date = timezone.now()
        subscription.auto_renew = False
        subscription.save()
        return Response({'status': 'Subscription cancelled'}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def pause(self, request, pk=None):
        """Pause a subscription"""
        subscription = self.get_object()
        if subscription.user != request.user and not request.user.is_staff:
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
        
        subscription.status = 'paused'
        subscription.auto_renew = False
        subscription.save()
        return Response({'status': 'Subscription paused'}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def resume(self, request, pk=None):
        """Resume a paused subscription"""
        subscription = self.get_object()
        if subscription.user != request.user and not request.user.is_staff:
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
        
        if subscription.status != 'paused':
            return Response({'error': 'Only paused subscriptions can be resumed'}, status=status.HTTP_400_BAD_REQUEST)
        
        subscription.status = 'active'
        subscription.auto_renew = True
        subscription.renewal_date = timezone.now() + timedelta(days=30)
        subscription.save()
        return Response({'status': 'Subscription resumed'}, status=status.HTTP_200_OK)


class PaymentViewSet(viewsets.ModelViewSet):
    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Users see only payments for their subscriptions; staff see all
        user = self.request.user
        if user.is_staff or user.is_superuser:
            return Payment.objects.all()
        return Payment.objects.filter(subscription__user=user)

    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def create_payment(self, request):
        """Create a new payment for a subscription"""
        subscription_id = request.data.get('subscription_id')
        payment_method = request.data.get('payment_method', 'paystack')
        
        try:
            subscription = Subscription.objects.get(id=subscription_id, user=request.user)
        except Subscription.DoesNotExist:
            return Response({'error': 'Subscription not found'}, status=status.HTTP_404_NOT_FOUND)
        
        # Create payment record
        payment = Payment.objects.create(
            subscription=subscription,
            amount=subscription.membership.price,
            status='pending',
            payment_method=payment_method,
            transaction_ref=f"TXN-{subscription.user.id}-{timezone.now().timestamp()}"
        )
        
        return Response(
            PaymentSerializer(payment).data,
            status=status.HTTP_201_CREATED
        )


class ProfileViewSet(viewsets.ModelViewSet):
    serializer_class = ProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Users see only their own profile; staff see all
        user = self.request.user
        if user.is_staff or user.is_superuser:
            return Profile.objects.all()
        return Profile.objects.filter(user=user)

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def my_profile(self, request):
        """Get the current user's profile"""
        profile, created = Profile.objects.get_or_create(user=request.user)
        return Response(ProfileSerializer(profile).data)


class PickupLocationViewSet(viewsets.ModelViewSet):
    queryset = PickupLocation.objects.all()
    serializer_class = PickupLocationSerializer
    permission_classes = [AllowAny]


class IngredientCategoryViewSet(viewsets.ModelViewSet):
    queryset = IngredientCategory.objects.all()
    serializer_class = IngredientCategorySerializer
    permission_classes = [AllowAny]


class DeliveryAddressViewSet(viewsets.ModelViewSet):
    queryset = DeliveryAddress.objects.all()
    serializer_class = DeliveryAddressSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def get_queryset(self):
        # limit addresses to the authenticated user
        return DeliveryAddress.objects.filter(user=self.request.user)


# Authentication Views
@api_view(['POST'])
@permission_classes([AllowAny])
def register(request):
    """Register a new user"""
    serializer = CustomUserCreateSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        token, created = Token.objects.get_or_create(user=user)
        return Response({
            'user': CustomUserSerializer(user).data,
            'token': token.key,
            'message': 'User registered successfully'
        }, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([AllowAny])
def login(request):
    """Login user with email and password"""
    email = request.data.get('email')
    password = request.data.get('password')
    
    if not email or not password:
        return Response(
            {'error': 'Email and password are required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        user_obj = User.objects.get(email=email)
        username = user_obj.username
    except User.DoesNotExist:
        return Response(
            {'error': 'Invalid credentials'},
            status=status.HTTP_401_UNAUTHORIZED
        )

    user = authenticate(username=username, password=password)
    if user is None:
        return Response(
            {'error': 'Invalid credentials'},
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    token, created = Token.objects.get_or_create(user=user)
    return Response({
        'user': CustomUserSerializer(user).data,
        'token': token.key
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_detailed(request):
    """Get current user with detailed info including membership status"""
    serializer = UserDetailedSerializer(request.user)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_profile(request):
    """Get current user profile"""
    return Response(CustomUserSerializer(request.user).data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout(request):
    """Logout user (delete token)"""
    request.user.auth_token.delete()
    return Response({'message': 'Logged out successfully'}, status=status.HTTP_200_OK)
