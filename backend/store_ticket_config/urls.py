from django.urls import path, include
from rest_framework.routers import DefaultRouter
from store_ticket_config.views import TicketConfigViewSet

# Create a router and register the viewset
router = DefaultRouter()
router.register(r'ticket', TicketConfigViewSet, basename='ticket')

# Include the router-generated URLs
urlpatterns = [
    path('api/', include(router.urls)),  # This will automatically include the 'ticket' routes
]
