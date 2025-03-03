from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('food_list/', views.food_list, name='food_list'),
    path('add_food/', views.add_food, name='add_food'),
    path('view_food/', views.view_food, name='view_food'),
    path('food_overview/', views.food_overview, name='food_overview'),
    path('cooked_food/<int:id>/', views.cooked_food, name='cooked_food'),
    path('delete_pending_food/<int:id>/', views.delete_pending_food, name='delete_pending_food'),
    path('ingredients_book/', views.ingredients_book, name='ingredients_book'),
    path('delete_food/<int:id>/', views.delete_food, name='delete_food'),
    path('inventory/', views.inventory_list, name='inventory_list'),
    path('reorder/', views.reorder_list, name='reorder_list'),
    path('delete_inventory/<int:id>/', views.delete_inventory_item, name='delete_inventory_item'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT)


