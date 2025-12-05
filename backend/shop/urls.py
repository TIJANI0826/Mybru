from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from . import oauth_views
from . import cart_views
from . import payment_views

router = DefaultRouter()
router.register(r'teas', views.TeaViewSet)
router.register(r'ingredients', views.IngredientViewSet)
router.register(r'ingredient-categories', views.IngredientCategoryViewSet)
router.register(r'carts', views.CartViewSet)
router.register(r'orders', views.OrderViewSet)
router.register(r'memberships', views.MembershipViewSet)
router.register(r'subscriptions', views.SubscriptionViewSet, basename='subscription')
router.register(r'payments', views.PaymentViewSet, basename='payment')
router.register(r'profiles', views.ProfileViewSet, basename='profile')
router.register(r'pickup-locations', views.PickupLocationViewSet)

urlpatterns = [
    path('', include(router.urls)),
    # Authentication endpoints
    path('auth/register/', views.register, name='register'),
    path('auth/login/', views.login, name='login'),
    path('auth/logout/', views.logout, name='logout'),
    path('auth/profile/', views.user_profile, name='user_profile'),
    path('auth/user/', views.get_user_detailed, name='get_user_detailed'),
    # Google OAuth endpoints
    path('auth/google/', oauth_views.google_oauth_callback, name='google_oauth_callback'),
    path('auth/google/login/', oauth_views.google_oauth_login, name='google_oauth_login'),
    # Cart endpoints
    path('cart/', cart_views.get_user_cart, name='get_user_cart'),
    path('cart/add/', cart_views.add_to_cart, name='add_to_cart'),
    path('cart/update/', cart_views.update_cart_item, name='update_cart_item'),
    path('cart/remove/', cart_views.remove_from_cart, name='remove_from_cart'),
    path('cart/clear/', cart_views.clear_cart, name='clear_cart'),
    path('checkout/place-order/', cart_views.place_order, name='place_order'),
    path('payment/initiate/', payment_views.initiate_payment, name='initiate_payment'),
    path('payment/verify/', payment_views.verify_payment, name='verify_payment'),
    path('payment/webhook/', payment_views.paystack_webhook, name='paystack_webhook'),
    path('payment/membership/initiate/', payment_views.initiate_membership_payment, name='initiate_membership_payment'),
    path('payment/membership/verify/', payment_views.verify_membership_payment, name='verify_membership_payment'),
    path('delivery-addresses/', views.DeliveryAddressViewSet.as_view({'get': 'list', 'post': 'create'}), name='delivery_addresses'),
]
