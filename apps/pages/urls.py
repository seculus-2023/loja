from django.urls import path
from pages import views

urlpatterns = [
    path('', views.index, name='home'),
    path('categorias/', views.category_list, name='category_list'),
    path('cart/', views.Car, name='cart'),
    path('contato/', views.contato, name='contato'),
    path('sobre/', views.sobre, name='sobre'),
    path("relatorio/pdf/", views.relatorio_pdf, name="relatorio_pdf"),
]
