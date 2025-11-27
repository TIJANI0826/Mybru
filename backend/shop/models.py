from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class IngredientCategory(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "Ingredient Categories"

class Ingredient(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    category = models.ForeignKey(IngredientCategory, on_delete=models.SET_NULL, null=True, blank=True, related_name='ingredients')
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.PositiveIntegerField()
    image = models.ImageField(upload_to='ingredients/', blank=True, null=True)

    def __str__(self):
        return self.name

class Tea(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    ingredients = models.ManyToManyField(Ingredient)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity_in_stock = models.PositiveIntegerField(default=0)
    image = models.ImageField(upload_to='teas/', blank=True, null=True)

    def __str__(self):
        return self.name

class Cart(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='shop_cart')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Cart for {self.user.username}"

class CartItem(models.Model):
    cart = models.ForeignKey(Cart, related_name='items', on_delete=models.CASCADE)
    tea = models.ForeignKey(Tea, on_delete=models.CASCADE, null=True, blank=True)
    ingredient = models.ForeignKey('Ingredient', on_delete=models.CASCADE, null=True, blank=True)
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        if self.ingredient:
            return f"{self.quantity} of {self.ingredient.name}"
        return f"{self.quantity} of {self.tea.name}"

class Order(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='shop_orders')
    created_at = models.DateTimeField(auto_now_add=True)
    ordered = models.BooleanField(default=False)
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    delivery_type = models.CharField(max_length=50, default='pickup')
    pickup_location = models.CharField(max_length=255, blank=True, null=True)
    delivery_address_line1 = models.CharField(max_length=255, blank=True, null=True)
    delivery_address_line2 = models.CharField(max_length=255, blank=True, null=True)
    delivery_city = models.CharField(max_length=100, blank=True, null=True)
    delivery_state = models.CharField(max_length=100, blank=True, null=True)
    delivery_zip_code = models.CharField(max_length=20, blank=True, null=True)
    delivery_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    def __str__(self):
        return f"Order {self.id} by {self.user.username}"

class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    tea = models.ForeignKey(Tea, on_delete=models.CASCADE, null=True, blank=True)
    ingredient = models.ForeignKey('Ingredient', on_delete=models.CASCADE, null=True, blank=True)
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        if self.ingredient:
            return f"{self.quantity} of {self.ingredient.name} in order {self.order.id}"
        return f"{self.quantity} of {self.tea.name} in order {self.order.id}"

class Membership(models.Model):
    """
    Membership tiers for myBru:
    - CASUAL: Non-registered or basic members who purchase readymade blends or DIY ingredients
    - CLASSIC: Registered members who engage myBru to customize their blends
    - PREMIUM: Registered members with personalized blends + natural health protocols
    """
    TIER_CHOICES = [
        ('CASUAL', 'Casual'),
        ('CLASSIC', 'Classic'),
        ('PREMIUM', 'Premium'),
    ]
    
    tier = models.CharField(max_length=20, choices=TIER_CHOICES, unique=True)
    name = models.CharField(max_length=100)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)  # Monthly price in NGN
    features = models.JSONField(default=list)  # List of features/benefits
    max_customizations_per_month = models.PositiveIntegerField(default=0)  # 0 = unlimited
    includes_health_protocol = models.BooleanField(default=False) 
    created_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        ordering = ['price']

    def __str__(self):
        return f"{self.tier} - {self.name}"


class Subscription(models.Model):
    """
    Active or past subscriptions for a user to a membership tier
    """
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('paused', 'Paused'),
        ('cancelled', 'Cancelled'),
        ('expired', 'Expired'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='memberships')
    membership = models.ForeignKey(Membership, on_delete=models.CASCADE, related_name='subscriptions')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    start_date = models.DateTimeField(auto_now_add=True)
    end_date = models.DateTimeField(null=True, blank=True)
    renewal_date = models.DateTimeField(null=True, blank=True)  # Next auto-renewal date
    auto_renew = models.BooleanField(default=True)
    customizations_used_this_month = models.PositiveIntegerField(default=0)
    
    class Meta:
        ordering = ['-start_date']
        unique_together = ['user', 'membership', 'status']

    def __str__(self):
        return f"{self.user.username} - {self.membership.tier} ({self.status})"


class Payment(models.Model):
    """
    Payment records for membership subscriptions
    """
    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    ]
    
    PAYMENT_METHOD_CHOICES = [
        ('card', 'Card'),
        ('paystack', 'Paystack'),
        ('bank_transfer', 'Bank Transfer'),
    ]
    
    subscription = models.ForeignKey(Subscription, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=10, decimal_places=2)  # Amount in NGN
    status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending')
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES)
    transaction_ref = models.CharField(max_length=255, unique=True)  # Paystack or bank reference
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Payment {self.transaction_ref} - {self.status}"


class Profile(models.Model):
    """
    User profile with current membership tier and preferences
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    current_membership = models.ForeignKey(Membership, null=True, blank=True, on_delete=models.SET_NULL)
    bio = models.TextField(blank=True, null=True)
    tea_preferences = models.JSONField(default=list)  # List of preferred tea types/ingredients
    health_goals = models.TextField(blank=True, null=True)  # For premium members' health protocols
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username}'s profile"


class DeliveryAddress(models.Model):
    user = models.ForeignKey(User, related_name='delivery_addresses', on_delete=models.CASCADE)
    address_line1 = models.CharField(max_length=255)
    address_line2 = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100, blank=True, null=True)
    zip_code = models.CharField(max_length=20, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_default = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.username} - {self.address_line1}, {self.city}"

class PickupLocation(models.Model):
    name = models.CharField(max_length=100)
    address = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    branch = models.CharField(max_length=100)
    delivery_fee = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return self.name
