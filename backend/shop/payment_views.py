from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.conf import settings
from decimal import Decimal
import json
import hmac
import hashlib
import requests

from .models import Cart, Order, OrderItem, PickupLocation, DeliveryAddress
from .serializers import OrderSerializer, DeliveryAddressSerializer

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
        if event.get('event') == 'charge.success':
            data = event.get('data', {})
            reference = data.get('reference')
            # Payment already verified via GET /verify_payment endpoint
            # This is just a notification
            pass

        return Response(status=status.HTTP_200_OK)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
