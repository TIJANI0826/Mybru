from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.db import transaction

from .models import Cart, CartItem, Tea, Ingredient
from .serializers import CartSerializer, CartItemSerializer
from .models import Order, OrderItem, PickupLocation, DeliveryAddress
from .serializers import OrderSerializer, DeliveryAddressSerializer, PickupLocationSerializer
from django.shortcuts import get_object_or_404
from decimal import Decimal


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_cart(request):
    """Get or create cart for the current user"""
    cart, created = Cart.objects.get_or_create(user=request.user)
    serializer = CartSerializer(cart)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_to_cart(request):
    """Add a tea or ingredient to the user's cart

    Accepts either `tea_id` or `ingredient_id` together with `quantity`.
    """
    tea_id = request.data.get('tea_id')
    ingredient_id = request.data.get('ingredient_id')
    quantity = int(request.data.get('quantity', 1))

    if not tea_id and not ingredient_id:
        return Response({'error': 'tea_id or ingredient_id is required'}, status=status.HTTP_400_BAD_REQUEST)

    cart, _ = Cart.objects.get_or_create(user=request.user)

    # Handle tea
    if tea_id:
        try:
            tea = Tea.objects.get(id=tea_id)
        except Tea.DoesNotExist:
            return Response({'error': 'Tea not found'}, status=status.HTTP_404_NOT_FOUND)

        # Check stock
        if tea.quantity_in_stock < quantity:
            return Response({'error': f'Not enough stock. Available: {tea.quantity_in_stock}'}, status=status.HTTP_400_BAD_REQUEST)

        cart_item, created = CartItem.objects.get_or_create(cart=cart, tea=tea, defaults={'quantity': quantity})
        if not created:
            cart_item.quantity += quantity
            if cart_item.quantity > tea.quantity_in_stock:
                return Response({'error': f'Not enough stock. Available: {tea.quantity_in_stock}'}, status=status.HTTP_400_BAD_REQUEST)
            cart_item.save()

        # Reduce tea stock
        tea.quantity_in_stock -= quantity
        tea.save()

    else:
        # Handle ingredient
        try:
            ingredient = Ingredient.objects.get(id=ingredient_id)
        except Ingredient.DoesNotExist:
            return Response({'error': 'Ingredient not found'}, status=status.HTTP_404_NOT_FOUND)

        if ingredient.stock < quantity:
            return Response({'error': f'Not enough stock. Available: {ingredient.stock}'}, status=status.HTTP_400_BAD_REQUEST)

        cart_item, created = CartItem.objects.get_or_create(cart=cart, ingredient=ingredient, defaults={'quantity': quantity})
        if not created:
            cart_item.quantity += quantity
            if cart_item.quantity > ingredient.stock:
                return Response({'error': f'Not enough stock. Available: {ingredient.stock}'}, status=status.HTTP_400_BAD_REQUEST)
            cart_item.save()

        # Reduce ingredient stock
        ingredient.stock -= quantity
        ingredient.save()

    serializer = CartSerializer(cart)
    return Response(serializer.data, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def update_cart_item(request):
    """Update quantity of a tea in the cart"""
    cart_item_id = request.data.get('cart_item_id')
    new_quantity = request.data.get('quantity')
    
    try:
        cart_item = CartItem.objects.get(id=cart_item_id)
    except CartItem.DoesNotExist:
        return Response({'error': 'Cart item not found'}, status=status.HTTP_404_NOT_FOUND)
    
    # Verify ownership
    if cart_item.cart.user != request.user:
        return Response({'error': 'Unauthorized'}, status=status.HTTP_403_FORBIDDEN)
    
    old_quantity = cart_item.quantity
    tea = cart_item.tea
    ingredient = getattr(cart_item, 'ingredient', None)
    
    with transaction.atomic():
        if new_quantity <= 0:
            # Remove item and restore stock
            if ingredient:
                ingredient.stock += old_quantity
                ingredient.save()
            else:
                tea.quantity_in_stock += old_quantity
                tea.save()
            cart_item.delete()
        else:
            # Calculate stock adjustment
            quantity_diff = new_quantity - old_quantity
            if ingredient:
                if quantity_diff > 0:
                    if ingredient.stock < quantity_diff:
                        return Response({'error': f'Not enough stock. Available: {ingredient.stock}'}, status=status.HTTP_400_BAD_REQUEST)
                    ingredient.stock -= quantity_diff
                else:
                    ingredient.stock += abs(quantity_diff)
                ingredient.save()
            else:
                if quantity_diff > 0:
                    if tea.quantity_in_stock < quantity_diff:
                        return Response({'error': f'Not enough stock. Available: {tea.quantity_in_stock}'}, status=status.HTTP_400_BAD_REQUEST)
                    tea.quantity_in_stock -= quantity_diff
                else:
                    tea.quantity_in_stock += abs(quantity_diff)
                tea.save()

            cart_item.quantity = new_quantity
            cart_item.save()
    
    cart = cart_item.cart
    serializer = CartSerializer(cart)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def remove_from_cart(request):
    """Remove a tea from the cart"""
    cart_item_id = request.data.get('cart_item_id')
    
    try:
        cart_item = CartItem.objects.get(id=cart_item_id)
    except CartItem.DoesNotExist:
        return Response({'error': 'Cart item not found'}, status=status.HTTP_404_NOT_FOUND)
    
    # Verify ownership
    if cart_item.cart.user != request.user:
        return Response({'error': 'Unauthorized'}, status=status.HTTP_403_FORBIDDEN)
    
    quantity = cart_item.quantity
    ingredient = getattr(cart_item, 'ingredient', None)
    tea = getattr(cart_item, 'tea', None)
    
    with transaction.atomic():
        # Restore stock
        if ingredient:
            ingredient.stock += quantity
            ingredient.save()
        elif tea:
            tea.quantity_in_stock += quantity
            tea.save()
        
        cart = cart_item.cart
        cart_item.delete()
    
    serializer = CartSerializer(cart)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def clear_cart(request):
    """Clear all items from the user's cart"""
    try:
        cart = Cart.objects.get(user=request.user)
        
        with transaction.atomic():
            for cart_item in cart.items.all():
                # Restore stock for tea or ingredient
                if cart_item.ingredient:
                    cart_item.ingredient.stock += cart_item.quantity
                    cart_item.ingredient.save()
                elif cart_item.tea:
                    cart_item.tea.quantity_in_stock += cart_item.quantity
                    cart_item.tea.save()
            
            cart.items.all().delete()
        
        serializer = CartSerializer(cart)
        return Response(serializer.data, status=status.HTTP_200_OK)
    except Cart.DoesNotExist:
        return Response({'error': 'Cart not found'}, status=status.HTTP_404_NOT_FOUND)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def place_order(request):
    """Create an Order from the user's cart and attach delivery or pickup info.

    Payload options:
    - delivery_type: 'pickup' or 'delivery'
    - If pickup: provide 'pickup_id' (PickupLocation id)
    - If delivery: provide either 'delivery_address_id' or address fields ('address_line1', etc.)
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

    # Calculate subtotal (note: stock already adjusted during cart operations)
    subtotal = Decimal('0.00')
    for ci in cart.items.all():
        if ci.ingredient:
            subtotal += (ci.ingredient.price * ci.quantity)
        elif ci.tea:
            subtotal += (ci.tea.price * ci.quantity)

    delivery_fee = Decimal('0.00')
    pickup_name = None

    if delivery_type == 'pickup' and pickup_id:
        pickup = get_object_or_404(PickupLocation, id=pickup_id)
        pickup_name = f"{pickup.name} - {pickup.branch}"
        # pickup.delivery_fee is a DecimalField -> keep as Decimal
        delivery_fee = (pickup.delivery_fee or Decimal('0.00'))
    else:
        # delivery path: try to resolve delivery address
        if delivery_address_id:
            addr = get_object_or_404(DeliveryAddress, id=delivery_address_id, user=user)
        else:
            # create a delivery address for the user from supplied fields
            addr_data = {
                'address_line1': data.get('address_line1'),
                'address_line2': data.get('address_line2'),
                'city': data.get('city'),
                'state': data.get('state'),
                'zip_code': data.get('zip_code'),
            }
            addr_serializer = DeliveryAddressSerializer(data=addr_data)
            if addr_serializer.is_valid():
                addr = addr_serializer.save(user=user)
            else:
                return Response({'error': 'Invalid delivery address', 'details': addr_serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        # copy address fields to order and optionally set a delivery fee
        # convert any provided delivery_fee to Decimal
        delivery_fee = Decimal(str(data.get('delivery_fee', '0')))

    total_price = subtotal + (delivery_fee or Decimal('0.00'))

    # Create order without modifying tea stock (stock already adjusted when adding to cart)
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
        delivery_fee=delivery_fee
    )

    # Move cart items into order items
    for ci in cart.items.all():
        if ci.ingredient:
            OrderItem.objects.create(order=order, ingredient=ci.ingredient, quantity=ci.quantity)
        else:
            OrderItem.objects.create(order=order, tea=ci.tea, quantity=ci.quantity)

    # Clear the cart (do not restore stock)
    cart.items.all().delete()

    serializer = OrderSerializer(order)
    return Response(serializer.data, status=status.HTTP_201_CREATED)
