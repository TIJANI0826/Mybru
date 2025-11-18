from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.db import transaction

from .models import Cart, CartItem, Tea
from .serializers import CartSerializer, CartItemSerializer


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
    """Add a tea to the user's cart"""
    tea_id = request.data.get('tea_id')
    quantity = request.data.get('quantity', 1)
    
    try:
        tea = Tea.objects.get(id=tea_id)
    except Tea.DoesNotExist:
        return Response({'error': 'Tea not found'}, status=status.HTTP_404_NOT_FOUND)
    
    # Check stock
    if tea.quantity_in_stock < quantity:
        return Response(
            {'error': f'Not enough stock. Available: {tea.quantity_in_stock}'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Get or create cart
    cart, _ = Cart.objects.get_or_create(user=request.user)
    
    # Add or update cart item
    cart_item, created = CartItem.objects.get_or_create(
        cart=cart,
        tea=tea,
        defaults={'quantity': quantity}
    )
    
    if not created:
        cart_item.quantity += quantity
        if cart_item.quantity > tea.quantity_in_stock:
            return Response(
                {'error': f'Not enough stock. Available: {tea.quantity_in_stock}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        cart_item.save()
    
    # Reduce tea stock
    tea.quantity_in_stock -= quantity
    tea.save()
    
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
    
    with transaction.atomic():
        if new_quantity <= 0:
            # Remove item and restore stock
            tea.quantity_in_stock += old_quantity
            tea.save()
            cart_item.delete()
        else:
            # Calculate stock adjustment
            quantity_diff = new_quantity - old_quantity
            
            if quantity_diff > 0:
                # Increasing quantity - check stock
                if tea.quantity_in_stock < quantity_diff:
                    return Response(
                        {'error': f'Not enough stock. Available: {tea.quantity_in_stock}'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                tea.quantity_in_stock -= quantity_diff
            else:
                # Decreasing quantity - restore stock
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
    
    tea = cart_item.tea
    quantity = cart_item.quantity
    
    with transaction.atomic():
        # Restore stock
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
                # Restore stock
                tea = cart_item.tea
                tea.quantity_in_stock += cart_item.quantity
                tea.save()
            
            cart.items.all().delete()
        
        serializer = CartSerializer(cart)
        return Response(serializer.data, status=status.HTTP_200_OK)
    except Cart.DoesNotExist:
        return Response({'error': 'Cart not found'}, status=status.HTTP_404_NOT_FOUND)
