from django.db import transaction
from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Tea, Ingredient, Cart, CartItem, Order, OrderItem, Membership, Subscription, Profile, PickupLocation, DeliveryAddress

class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = '__all__'

class TeaSerializer(serializers.ModelSerializer):
    ingredients = IngredientSerializer(many=True, read_only=True)

    class Meta:
        model = Tea
        fields = '__all__'

class CartItemSerializer(serializers.ModelSerializer):
    tea = TeaSerializer(read_only=True)
    ingredient = IngredientSerializer(read_only=True)

    class Meta:
        model = CartItem
        fields = '__all__'

class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)

    class Meta:
        model = Cart
        fields = '__all__'

class OrderItemSerializer(serializers.ModelSerializer):
    tea = TeaSerializer(read_only=True)
    ingredient = IngredientSerializer(read_only=True)
    order = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = OrderItem
        fields = '__all__'

class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True)

    class Meta:
        model = Order
        fields = '__all__'

    def create(self, validated_data):
        items_data = validated_data.pop('items')
        with transaction.atomic():
            order = Order.objects.create(**validated_data)
            for item_data in items_data:
                tea = item_data['tea']
                quantity = item_data['quantity']
                if tea.quantity_in_stock < quantity:
                    raise serializers.ValidationError(f"Not enough stock for {tea.name}")
                tea.quantity_in_stock -= quantity
                tea.save()
                OrderItem.objects.create(order=order, **item_data)
        return order

class MembershipSerializer(serializers.ModelSerializer):
    class Meta:
        model = Membership
        fields = '__all__'

class SubscriptionSerializer(serializers.ModelSerializer):
    membership = MembershipSerializer(read_only=True)

    class Meta:
        model = Subscription
        fields = '__all__'

class ProfileSerializer(serializers.ModelSerializer):
    membership = MembershipSerializer(read_only=True)

    class Meta:
        model = Profile
        fields = '__all__'


class PickupLocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = PickupLocation
        fields = '__all__'


class DeliveryAddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeliveryAddress
        fields = ['id', 'user', 'address_line1', 'address_line2', 'city', 'state', 'zip_code', 'is_default', 'created_at']
        read_only_fields = ['id', 'user', 'created_at']


# Authentication Serializers
class CustomUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']
        read_only_fields = ['id']


class CustomUserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})
    password2 = serializers.CharField(style={'input_type': 'password'}, write_only=True, label="Confirm password")

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'password', 'password2']

    def validate(self, data):
        if data['password'] != data.pop('password2'):
            raise serializers.ValidationError({"password": "Passwords must match."})
        return data

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data.get('email', ''),
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
            password=validated_data['password']
        )
        return user
