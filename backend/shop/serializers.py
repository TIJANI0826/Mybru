from django.db import transaction
from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Tea, Ingredient, Cart, CartItem, Order, OrderItem, Membership, Subscription, Profile, PickupLocation, DeliveryAddress, Payment, IngredientCategory

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
        fields = ['id', 'tier', 'name', 'description', 'price', 'features', 'max_customizations_per_month', 'includes_health_protocol', 'created_at']
        read_only_fields = ['id', 'created_at']


# Authentication Serializers
class CustomUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']
        read_only_fields = ['id']


class UserDetailedSerializer(serializers.ModelSerializer):
    """Enhanced user serializer that includes membership status"""
    has_active_subscription = serializers.SerializerMethodField()
    active_membership = serializers.SerializerMethodField()
    memberships = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'has_active_subscription', 'active_membership', 'memberships']
        read_only_fields = ['id']
    
    def get_has_active_subscription(self, obj):
        """Check if user has any active subscription"""
        return obj.memberships.filter(status='active').exists()
    
    def get_active_membership(self, obj):
        """Get the user's active membership details"""
        active_subscription = obj.memberships.filter(status='active').first()
        if active_subscription:
            return MembershipSerializer(active_subscription.membership).data
        return None
    
    def get_memberships(self, obj):
        """Get all user subscriptions"""
        subscriptions = obj.memberships.all()
        return SubscriptionSerializerSimple(subscriptions, many=True).data


class SubscriptionSerializerSimple(serializers.ModelSerializer):
    """Simplified subscription serializer"""
    membership = MembershipSerializer(read_only=True)
    
    class Meta:
        model = Subscription
        fields = ['id', 'membership', 'status', 'start_date', 'end_date']
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


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = ['id', 'subscription', 'amount', 'status', 'payment_method', 'transaction_ref', 'created_at', 'completed_at']
        read_only_fields = ['id', 'created_at', 'completed_at']


class SubscriptionSerializer(serializers.ModelSerializer):
    membership = MembershipSerializer(read_only=True)
    membership_id = serializers.IntegerField(write_only=True, required=False)
    payments = PaymentSerializer(many=True, read_only=True)

    class Meta:
        model = Subscription
        fields = ['id', 'user', 'membership', 'membership_id', 'status', 'start_date', 'end_date', 'renewal_date', 'auto_renew', 'customizations_used_this_month', 'payments']
        read_only_fields = ['id', 'user', 'start_date', 'renewal_date']

    def create(self, validated_data):
        membership_id = validated_data.pop('membership_id', None)
        user = self.context['request'].user
        
        if membership_id:
            membership = Membership.objects.get(id=membership_id)
            validated_data['membership'] = membership
        
        return Subscription.objects.create(user=user, **validated_data)


class ProfileSerializer(serializers.ModelSerializer):
    current_membership = MembershipSerializer(read_only=True)
    user_details = serializers.SerializerMethodField()

    class Meta:
        model = Profile
        fields = ['id', 'user', 'user_details', 'current_membership', 'bio', 'tea_preferences', 'health_goals', 'created_at', 'updated_at']
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']

    def get_user_details(self, obj):
        # Use SerializerMethodField to avoid potential import/order issues
        try:
            return CustomUserSerializer(obj.user).data if obj.user else None
        except Exception:
            # Fallback: return minimal user info
            user = getattr(obj, 'user', None)
            if not user:
                return None
            return {
                'id': getattr(user, 'id', None),
                'username': getattr(user, 'username', ''),
                'email': getattr(user, 'email', ''),
                'first_name': getattr(user, 'first_name', ''),
                'last_name': getattr(user, 'last_name', ''),
            }


class PickupLocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = PickupLocation
        fields = '__all__'


class IngredientCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = IngredientCategory
        fields = ['id', 'name', 'description']


class DeliveryAddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeliveryAddress
        fields = ['id', 'user', 'address_line1', 'address_line2', 'city', 'state', 'zip_code', 'is_default', 'created_at']
        read_only_fields = ['id', 'user', 'created_at']
