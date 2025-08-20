from django.urls import path
from pages import views

urlpatterns = [
    path('', views.index, name='home'),
    path('categorias/', views.category_list, name='category_list'),
    path('cart/', views.Car, name='cart'),
    path('contato/', views.contato, name='contato'),
    path('sobre/', views.sobre, name='sobre'),
    path('pedido/', views.pedido, name='pedido'),
    path("relatorio/pdf/", views.relatorio_pdf, name="relatorio_pdf"),
    path('clear_cart/', views.clear_cart, name='clear_cart'),
    path('update_cart_item/', views.update_cart_item, name='update_cart_item'),
    path('save_order/', views.save_order, name='save_order'),
    
]
