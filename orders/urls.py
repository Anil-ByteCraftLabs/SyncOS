from django.urls import path
from .views import OrderCreateView, OrderDetailView

urlpatterns = [
    path('create/', OrderCreateView.as_view(), name='order-create'),
    path('detail/<str:order_number>/', OrderDetailView.as_view(), name='order-detail'),
]