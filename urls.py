from django.urls import path
from . import views

app_name = 'wishlist'

urlpatterns = [
    path('itemrequest/create/', views.ItemRequestCreate.as_view(), name='itemrequest-create'),
    path('itemrequest/<int:pk>/update/', views.ItemRequestUpdate.as_view(), name='itemrequest-update'),
    path('itemrequest/<int:pk>/detail/', views.ItemRequestDetail.as_view(), name='itemrequest-detail'),
    path('itemrequest/<int:pk>/delete/', views.ItemRequestSoftDelete.as_view(), name='itemrequest-delete'),
    path('itemrequest/list/', views.ItemRequestList.as_view(), name='itemrequest-list'),
]
