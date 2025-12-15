from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.conf import settings
from django.utils import timezone
from decimal import Decimal
import json
import hmac
import hashlib
import requests

from .models import Cart, Order, OrderItem, PickupLocation, DeliveryAddress, Subscription
from .serializers import OrderSerializer, DeliveryAddressSerializer
from django.contrib.auth import get_user_model
User = get_user_model()

# Get frontend URL from settings for Paystack redirect
FRONTEND_URL = settings.FRONTEND_URL


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def initiate_payment(request):
    """Initiate a Paystack payment for the user's cart.
    
    Payload:
    - delivery_type: 'pickup' or 'delivery'
    - pickup_id: (if pickup)
    - delivery_address_id: (if delivery, existing address)
    - address_line1, address_line2, city, state, zip_code: (if delivery, new address)
    - delivery_fee: (optional, for delivery)
    
    Returns:
    - authorization_url: URL to redirect user to Paystack for payment
    - access_code: Paystack access code for verification
    - reference: Unique reference for this payment
    """
    user = request.user
    
    try:
        cart = Cart.objects.get(user=user)
    except Cart.DoesNotExist:
        return Response({'error': 'Cart not found'}, status=status.HTTP_404_NOT_FOUND)

    if not cart.items.exists():
        return Response({'error': 'Cart is empty'}, status=status.HTTP_400_BAD_REQUEST)

    data = request.data or {}
    delivery_type = data.get('delivery_type', 'pickup')
    pickup_id = data.get('pickup_id')
    delivery_address_id = data.get('delivery_address_id')

    # Calculate subtotal
    subtotal = Decimal('0.00')
    for ci in cart.items.all():
        if ci.ingredient:
            subtotal += (ci.ingredient.price * ci.quantity)
        elif ci.tea:
            subtotal += (ci.tea.price * ci.quantity)

    delivery_fee = Decimal('0.00')

    if delivery_type == 'pickup' and pickup_id:
        pickup = PickupLocation.objects.get(id=pickup_id)
        delivery_fee = pickup.delivery_fee or Decimal('0.00')
    elif delivery_type == 'delivery':
        delivery_fee = Decimal(str(data.get('delivery_fee', '0')))

    total_price = subtotal + delivery_fee

    # Store order details in session for verification after payment
    # We'll create a temporary order record to track payment
    order_data = {
        'delivery_type': delivery_type,
        'pickup_id': pickup_id,
        'delivery_address_id': delivery_address_id,
        'address_line1': data.get('address_line1'),
        'address_line2': data.get('address_line2'),
        'city': data.get('city'),
        'state': data.get('state'),
        'zip_code': data.get('zip_code'),
        'delivery_fee': float(delivery_fee),
        'total_price': float(total_price),
    }

    # Generate unique reference for this payment
    import uuid
    reference = f"ORDER-{user.id}-{uuid.uuid4().hex[:12].upper()}"

    # Store payment intent in session
    request.session[f'payment_{reference}'] = order_data

    # Initialize Paystack payment
    paystack_key = settings.PAYSTACK_SECRET_KEY
    amount_in_kobo = int(float(total_price) * 100)  # Paystack uses kobo (1/100 of naira)

    paystack_payload = {
        'amount': amount_in_kobo,
        'email': user.email,
        'reference': reference,
        'metadata': {
            'user_id': user.id,
            'username': user.username,
            'order_data': order_data
        }
    }

    headers = {
        'Authorization': f'Bearer {paystack_key}',
        'Content-Type': 'application/json'
    }

    try:
        response = requests.post(
            'https://api.paystack.co/transaction/initialize',
            json=paystack_payload,
            headers=headers,
            timeout=10
        )

        if response.status_code == 200:
            paystack_response = response.json()
            if paystack_response.get('status'):
                return Response({
                    'status': True,
                    'authorization_url': paystack_response['data']['authorization_url'],
                    'access_code': paystack_response['data']['access_code'],
                    'reference': reference
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'error': 'Failed to initialize payment',
                    'details': paystack_response.get('message', 'Unknown error')
                }, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({
                'error': 'Paystack service error',
                'details': response.text
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    except requests.RequestException as e:
        return Response({
            'error': 'Could not connect to payment service',
            'details': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def verify_payment(request):
    """Verify payment from Paystack and create order if successful.
    
    Query params:
    - reference: Paystack payment reference
    """
    reference = request.query_params.get('reference')
    
    if not reference:
        return Response({'error': 'Reference is required'}, status=status.HTTP_400_BAD_REQUEST)

    paystack_key = settings.PAYSTACK_SECRET_KEY
    headers = {
        'Authorization': f'Bearer {paystack_key}'
    }

    try:
        response = requests.get(
            f'https://api.paystack.co/transaction/verify/{reference}',
            headers=headers,
            timeout=10
        )

        if response.status_code == 200:
            paystack_response = response.json()

            if not paystack_response.get('status'):
                return Response({
                    'error': 'Payment verification failed',
                    'details': paystack_response.get('message', 'Unknown error')
                }, status=status.HTTP_400_BAD_REQUEST)

            data = paystack_response.get('data', {})
            if data.get('status') != 'success':
                return Response({
                    'error': 'Payment was not successful',
                    'status': data.get('status')
                }, status=status.HTTP_400_BAD_REQUEST)

            # Payment successful - create order
            user = request.user
            
            try:
                cart = Cart.objects.get(user=user)
            except Cart.DoesNotExist:
                return Response({'error': 'Cart not found'}, status=status.HTTP_404_NOT_FOUND)

            if not cart.items.exists():
                return Response({'error': 'Cart is empty'}, status=status.HTTP_400_BAD_REQUEST)

            # Retrieve stored order data from metadata
            metadata = data.get('metadata', {})
            order_data = metadata.get('order_data', {})

            delivery_type = order_data.get('delivery_type', 'pickup')
            pickup_id = order_data.get('pickup_id')
            delivery_address_id = order_data.get('delivery_address_id')
            total_price = Decimal(str(order_data.get('total_price', '0')))
            delivery_fee = Decimal(str(order_data.get('delivery_fee', '0')))

            pickup_name = None

            if delivery_type == 'pickup' and pickup_id:
                pickup = PickupLocation.objects.get(id=pickup_id)
                pickup_name = f"{pickup.name} - {pickup.branch}"
            else:
                # Delivery path
                if delivery_address_id:
                    addr = DeliveryAddress.objects.get(id=delivery_address_id, user=user)
                else:
                    # Create a delivery address from stored data
                    addr_data = {
                        'address_line1': order_data.get('address_line1'),
                        'address_line2': order_data.get('address_line2'),
                        'city': order_data.get('city'),
                        'state': order_data.get('state'),
                        'zip_code': order_data.get('zip_code'),
                    }
                    addr_serializer = DeliveryAddressSerializer(data=addr_data)
                    if addr_serializer.is_valid():
                        addr = addr_serializer.save(user=user)
                    else:
                        return Response({
                            'error': 'Invalid delivery address',
                            'details': addr_serializer.errors
                        }, status=status.HTTP_400_BAD_REQUEST)

            # Create order
            order = Order.objects.create(
                user=user,
                total_price=total_price,
                delivery_type=delivery_type,
                pickup_location=pickup_name if pickup_name else (addr.address_line1 if delivery_type == 'delivery' else ''),
                delivery_address_line1=(addr.address_line1 if delivery_type == 'delivery' else None),
                delivery_address_line2=(addr.address_line2 if delivery_type == 'delivery' else None),
                delivery_city=(addr.city if delivery_type == 'delivery' else None),
                delivery_state=(addr.state if delivery_type == 'delivery' else None),
                delivery_zip_code=(addr.zip_code if delivery_type == 'delivery' else None),
                delivery_fee=delivery_fee,
                payment_reference=reference,
                payment_status='paid'
            )

            # Move cart items to order
            for ci in cart.items.all():
                if ci.ingredient:
                    OrderItem.objects.create(order=order, ingredient=ci.ingredient, quantity=ci.quantity)
                else:
                    OrderItem.objects.create(order=order, tea=ci.tea, quantity=ci.quantity)

            # Clear cart
            cart.items.all().delete()

            serializer = OrderSerializer(order)
            return Response({
                'status': True,
                'message': 'Payment verified and order created successfully',
                'order': serializer.data
            }, status=status.HTTP_201_CREATED)

        else:
            return Response({
                'error': 'Payment verification service error',
                'details': response.text
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    except requests.RequestException as e:
        return Response({
            'error': 'Could not verify payment',
            'details': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
def paystack_webhook(request):
    """Handle Paystack webhook for payment confirmation.
    
    This endpoint should be registered with Paystack to receive payment notifications.
    """
    paystack_key = settings.PAYSTACK_SECRET_KEY

    # Verify webhook signature
    signature = request.META.get('HTTP_X_PAYSTACK_SIGNATURE', '')
    body = request.body

    hash_obj = hmac.new(
        paystack_key.encode('utf-8'),
        body,
        hashlib.sha512
    )
    computed_signature = hash_obj.hexdigest()

    if signature != computed_signature:
        return Response({'error': 'Invalid signature'}, status=status.HTTP_401_UNAUTHORIZED)
    try:
        event = request.data
        # We only process successful charge events
        if event.get('event') == 'charge.success':
            data = event.get('data', {})
            reference = data.get('reference')
            metadata = data.get('metadata', {}) or {}

            # Idempotency: if we've already recorded this reference, acknowledge
            if Order.objects.filter(payment_reference=reference).exists() or Subscription.objects.filter(payment_reference=reference).exists():
                return Response(status=status.HTTP_200_OK)

            ptype = metadata.get('type') or metadata.get('payment_type')

            # MEMBERSHIP flow
            if ptype == 'membership' or metadata.get('membership_id'):
                try:
                    membership_id = metadata.get('membership_id') or metadata.get('membership')
                    if not membership_id:
                        return Response(status=status.HTTP_200_OK)

                    from .models import Membership
                    from datetime import timedelta

                    try:
                        membership = Membership.objects.get(id=membership_id)
                    except Membership.DoesNotExist:
                        return Response(status=status.HTTP_200_OK)

                    user_id = metadata.get('user_id')
                    if not user_id:
                        return Response(status=status.HTTP_200_OK)

                    try:
                        user = User.objects.get(id=user_id)
                    except User.DoesNotExist:
                        return Response(status=status.HTTP_200_OK)

                    amount_paid = Decimal(str(data.get('amount', 0) / 100))

                    subscription, created = Subscription.objects.get_or_create(
                        user=user,
                        membership=membership,
                        defaults={
                            'payment_reference': reference,
                            'payment_status': 'paid',
                            'amount_paid': amount_paid,
                            'renewal_date': timezone.now() + timedelta(days=30),
                            'status': 'active'
                        }
                    )

                    if not created:
                        subscription.payment_reference = reference
                        subscription.payment_status = 'paid'
                        subscription.amount_paid = amount_paid
                        subscription.status = 'active'
                        subscription.renewal_date = timezone.now() + timedelta(days=30)
                        subscription.save()
                except Exception:
                    # Acknowledge to avoid webhook retries; log if needed
                    pass

            # ORDER flow
            elif ptype == 'order' or metadata.get('order_data'):
                try:
                    user_id = metadata.get('user_id')
                    if not user_id:
                        return Response(status=status.HTTP_200_OK)

                    try:
                        user = User.objects.get(id=user_id)
                    except User.DoesNotExist:
                        return Response(status=status.HTTP_200_OK)

                    try:
                        cart = Cart.objects.get(user=user)
                    except Cart.DoesNotExist:
                        return Response(status=status.HTTP_200_OK)

                    if not cart.items.exists():
                        return Response(status=status.HTTP_200_OK)

                    order_data = metadata.get('order_data', {})
                    delivery_type = order_data.get('delivery_type', 'pickup')
                    pickup_id = order_data.get('pickup_id')
                    delivery_address_id = order_data.get('delivery_address_id')
                    total_price = Decimal(str(order_data.get('total_price', '0')))
                    delivery_fee = Decimal(str(order_data.get('delivery_fee', '0')))

                    pickup_name = None
                    addr = None

                    if delivery_type == 'pickup' and pickup_id:
                        try:
                            pickup = PickupLocation.objects.get(id=pickup_id)
                            pickup_name = f"{pickup.name} - {pickup.branch}"
                        except PickupLocation.DoesNotExist:
                            pickup_name = ''
                    else:
                        if delivery_address_id:
                            try:
                                addr = DeliveryAddress.objects.get(id=delivery_address_id, user=user)
                            except DeliveryAddress.DoesNotExist:
                                addr = None

                    # Create order
                    order = Order.objects.create(
                        user=user,
                        total_price=total_price,
                        delivery_type=delivery_type,
                        pickup_location=pickup_name if pickup_name else (addr.address_line1 if addr else ''),
                        delivery_address_line1=(addr.address_line1 if addr else None),
                        delivery_address_line2=(addr.address_line2 if addr else None),
                        delivery_city=(addr.city if addr else None),
                        delivery_state=(addr.state if addr else None),
                        delivery_zip_code=(addr.zip_code if addr else None),
                        delivery_fee=delivery_fee,
                        payment_reference=reference,
                        payment_status='paid'
                    )

                    for ci in cart.items.all():
                        if ci.ingredient:
                            OrderItem.objects.create(order=order, ingredient=ci.ingredient, quantity=ci.quantity)
                        else:
                            OrderItem.objects.create(order=order, tea=ci.tea, quantity=ci.quantity)

                    cart.items.all().delete()
                except Exception:
                    pass

        return Response(status=status.HTTP_200_OK)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


# Membership Payment Endpoints

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def initiate_membership_payment(request):
    """Initiate a Paystack payment for membership subscription.
    
    Payload:
    - membership_id: ID of the membership tier to subscribe to
    
    Returns:
    - authorization_url: URL to redirect user to Paystack for payment
    - access_code: Paystack access code for verification
    - reference: Unique reference for this payment
    """
    from .models import Membership
    
    user = request.user
    data = request.data or {}
    membership_id = data.get('membership_id')
    
    if not membership_id:
        return Response({'error': 'membership_id is required'}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        membership = Membership.objects.get(id=membership_id)
    except Membership.DoesNotExist:
        return Response({'error': 'Membership not found'}, status=status.HTTP_404_NOT_FOUND)
    
    # Check if user already has active subscription for this membership
    subscription = Subscription.objects.filter(
        user=user,
        membership=membership,
        status='active'
    ).first()
    
    if subscription:
        return Response(
            {'error': f'User already has active subscription to {membership.tier}'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Calculate amount in naira (convert to smallest unit - kobo)
    amount_in_naira = membership.price
    amount_in_kobo = int(amount_in_naira * 100)
    
    # Generate payment reference
    payment_reference = f"MEMBERSHIP-{user.id}-{membership.id}-{int(timezone.now().timestamp())}"
    
    paystack_headers = {
        'Authorization': f'Bearer {settings.PAYSTACK_SECRET_KEY}',
        'Content-Type': 'application/json'
    }
    
    paystack_payload = {
        'email': user.email,
        'amount': amount_in_kobo,
        'reference': payment_reference,
        'metadata': {
            'user_id': user.id,
            'membership_id': membership.id,
            'membership_tier': membership.tier,
            'type': 'membership'
        }
    }
    
    try:
        response = requests.post(
            'https://api.paystack.co/transaction/initialize',
            headers=paystack_headers,
            json=paystack_payload
        )
        response.raise_for_status()
        
        paystack_response = response.json()
        
        if paystack_response.get('status'):
            # Store payment reference in session for later verification
            request.session['membership_payment_reference'] = payment_reference
            
            return Response({
                'status': True,
                'authorization_url': paystack_response['data']['authorization_url'],
                'access_code': paystack_response['data']['access_code'],
                'reference': payment_reference,
                'amount': float(amount_in_naira)
            })
        else:
            return Response(
                {'error': paystack_response.get('message', 'Failed to initialize payment')},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    except requests.exceptions.RequestException as e:
        return Response({'error': f'Payment service error: {str(e)}'}, status=status.HTTP_502_BAD_GATEWAY)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def verify_membership_payment(request):
    """Verify a Paystack payment and create membership subscription.

    Query parameters:
    - reference: Paystack payment reference

    Returns:
    - success: True if payment was verified
    - subscription_id: ID of created subscription
    - membership_tier: Name of membership tier
    - amount: Amount paid
    - status: Subscription status
    """
    from .models import Membership, Subscription
    from datetime import timedelta
    from .serializers import SubscriptionSerializer

    user = request.user
    reference = request.query_params.get('reference')

    if not reference:
        return Response({'error': 'reference is required'}, status=status.HTTP_400_BAD_REQUEST)

    paystack_headers = {
        'Authorization': f'Bearer {settings.PAYSTACK_SECRET_KEY}'
    }

    try:
        response = requests.get(
            f'https://api.paystack.co/transaction/verify/{reference}',
            headers=paystack_headers,
            timeout=10
        )
        response.raise_for_status()

        paystack_response = response.json()

        if not paystack_response.get('status'):
            return Response(
                {'error': 'Payment verification failed', 'message': paystack_response.get('message')},
                status=status.HTTP_400_BAD_REQUEST
            )

        data = paystack_response.get('data', {})

        # Verify status is successful
        if data.get('status') != 'success':
            return Response(
                {'error': f"Payment status is {data.get('status')}"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Extract metadata
        metadata = data.get('metadata', {})
        membership_id = metadata.get('membership_id')

        if not membership_id:
            return Response({'error': 'Invalid payment metadata'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            membership = Membership.objects.get(id=membership_id)
        except Membership.DoesNotExist:
            return Response({'error': 'Membership not found'}, status=status.HTTP_404_NOT_FOUND)

        # Create or update subscription
        amount_paid = Decimal(str(data.get('amount', 0) / 100))  # Convert from kobo to naira

        subscription, created = Subscription.objects.get_or_create(
            user=user,
            membership=membership,
            defaults={
                'payment_reference': reference,
                'payment_status': 'paid',
                'amount_paid': amount_paid,
                'renewal_date': timezone.now() + timedelta(days=30),
                'status': 'active'
            }
        )

        if not created:
            subscription.payment_reference = reference
            subscription.payment_status = 'paid'
            subscription.amount_paid = amount_paid
            subscription.status = 'active'
            subscription.renewal_date = timezone.now() + timedelta(days=30)
            subscription.save()

        return Response({
            'success': True,
            'subscription_id': subscription.id,
            'membership_tier': membership.tier,
            'amount': float(amount_paid),
            'status': subscription.status,
            'renewal_date': subscription.renewal_date.isoformat(),
            'subscription': SubscriptionSerializer(subscription).data
        })

    except requests.exceptions.RequestException as e:
        return Response({'error': f'Payment verification error: {str(e)}'}, status=status.HTTP_502_BAD_GATEWAY)
    except Exception as e:
        return Response({'error': f'Error creating subscription: {str(e)}'}, status=status.HTTP_400_BAD_REQUEST)
