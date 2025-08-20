
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class Order(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    nome = models.CharField(max_length=255)
    telefone = models.CharField(max_length=20)
    data_pedido = models.DateTimeField(default=timezone.now)  # <-- Aqui a data do pedido
    
    def __str__(self):
        return f"Pedido #{self.id} de {self.nome}"
    
    @property
    def get_order_total(self):
        # Acessa os itens do pedido usando o 'related_name'
        total = sum(item.total for item in self.items.all())
        return total

# ---
# Classe com o nome corrigido para 'OrderItem'
class OrderItem(models.Model):
    # O item agora está ligado ao Pedido (Order)
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items") 
    product = models.ForeignKey('Product', on_delete=models.CASCADE)
    qtde = models.PositiveIntegerField(default=1, verbose_name="Qtde")
    subtotal = models.DecimalField(default=0.00, max_digits=100, decimal_places=2)
    total = models.DecimalField(default=0.00, max_digits=100, decimal_places=2)
    added = models.DateTimeField(auto_now_add=True, verbose_name="Adicionado em") # Adicionando o campo 'added'

    def __str__(self):
        return f"{self.product.title} x {self.qtde}"

class Cart(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, verbose_name="Usuário")
    updated = models.DateTimeField(auto_now=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Carrinho {self.id} - Usuário {self.user}" if self.user else f"Carrinho {self.id}"


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey('Product', on_delete=models.CASCADE)
    qtde = models.PositiveIntegerField(default=1, verbose_name="Qtde")
    subtotal = models.DecimalField(default=0.00, max_digits=100, decimal_places=2)
    total = models.DecimalField(default=0.00, max_digits=100, decimal_places=2)
    added = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.product.title} x {self.qtde}"



class Banner(models.Model):
    """
    A model to represent a banner with a name, description, and an image.
    """
    nome = models.CharField(
        max_length=200,
        help_text="O nome do banner (ex: Banner de Promoção)"
    )
    descricao = models.TextField(
        help_text="Uma descrição curta sobre o banner."
    )
    imagem = models.ImageField(
        upload_to='banners/',
        help_text="A imagem do banner."
    )
    ativo = models.BooleanField(
        default=True,
        help_text="Indica se o banner está ativo e deve ser exibido."
    )

    class Meta:
        verbose_name = "Banner"
        verbose_name_plural = "Banners"

    def __str__(self):
        return self.nome

# ---
  

class Category(models.Model):
    """
    Um modelo para representar uma categoria de produtos.
    """
    name = models.CharField(
        max_length=120,
        unique=True,
        help_text="O nome da categoria. Deve ser único."
    )
    description = models.TextField(
        null=True,
        blank=True,
        help_text="Uma breve descrição da categoria."
    )
    image = models.ImageField(
        upload_to='categories/',
        null=True,
        blank=True,
        help_text="Uma imagem para representar a categoria."
    )
    active = models.BooleanField(
        default=True,
        help_text="Indica se a categoria está ativa e deve ser exibida."
    )

    class Meta:
        verbose_name = "Categoria"
        verbose_name_plural = "Categorias"

    def __str__(self):
        return self.name

# ---
  

class Product(models.Model):
    """
    Um modelo para representar um produto.
    """
    title = models.CharField(
        max_length=120,
        verbose_name="Título"
    )
    description = models.TextField(
        verbose_name="Descrição"
    )
    referencia = referencia = models.CharField(
    max_length=40,
    verbose_name="Referencia"
    )
    price = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        default=100.00,
        verbose_name="Preço Principal"
    )
    price2 = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        default=100.00,
        verbose_name="Preço Adicional"
    )
    image = models.FileField(
        upload_to='products/',
        null=True,
        blank=True,
        verbose_name="Imagem"
    )
    stock = models.PositiveIntegerField(
        default=0,
        verbose_name="Estoque"
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="products",
        verbose_name="Categoria"
    )
    active = models.BooleanField(
        default=True,
        verbose_name="Ativo"
    )

    class Meta:
        verbose_name = "Produto"
        verbose_name_plural = "Produtos"

    def __str__(self):
        return self.title


# ---


