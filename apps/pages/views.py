from django.shortcuts import render   
from .models import Banner, Category, Product, Cart, CartItem, Product
from collections import namedtuple  # ⚠ Import necessário para namedtuple
from django.template.loader import get_template
from django.http import HttpResponse
from xhtml2pdf import pisa

import openpyxl
import uuid


def Car(request):
    banners = Banner.objects.filter(ativo=True)

    # Usuário logado
    if request.user.is_authenticated:
        cart, _ = Cart.objects.get_or_create(user=request.user)

        if request.method == 'POST':
            delete_cart_id = request.POST.get('delete_cart_id')
            if delete_cart_id:
                CartItem.objects.filter(id=delete_cart_id, cart=cart).delete()
            else:
                product_id = request.POST.get('product_id')
                qtde = int(request.POST.get('qtde', 1))
                product = Product.objects.filter(id=product_id).first()
                if product:
                    preco = product.price2 if product.price2 > 0 else product.price
                    if preco > 0:
                        cart_item = CartItem.objects.filter(cart=cart, product=product).first()
                        subtotal = preco * qtde
                        if cart_item:
                            cart_item.qtde = qtde
                            cart_item.subtotal = subtotal
                            cart_item.total = subtotal
                            cart_item.save()
                        else:
                            CartItem.objects.create(
                                cart=cart,
                                product=product,
                                qtde=qtde,
                                subtotal=subtotal,
                                total=subtotal
                            )

        items = cart.items.all().order_by('-added')
        cart_total = sum([item.total for item in items if item.total])
        total_itens = sum([item.qtde for item in items])
        return render(request, 'cart.html', {
            'banners': banners,
            'carts': items,
            'cart_total': cart_total,
            'total_itens': total_itens
        })

    # Usuário anônimo via sessão
    else:
        if 'cart' not in request.session:
            request.session['cart'] = []
        cart_session = request.session['cart']

        if request.method == 'POST':
            delete_cart_id = request.POST.get('delete_cart_id')
            if delete_cart_id:
                cart_session = [item for item in cart_session if str(item.get('id')) != str(delete_cart_id)]
                request.session['cart'] = cart_session
            else:
                product_id = request.POST.get('product_id')
                qtde = int(request.POST.get('qtde', 1))
                product = Product.objects.filter(id=product_id).first()
                if product:
                    preco = product.price2 if product.price2 > 0 else product.price
                    if preco > 0:
                        item_id = str(uuid.uuid4())
                        cart_session.append({
                            'id': item_id,
                            'product_id': product.id,  # só salva o ID
                            'qtde': qtde,
                            'subtotal': float(preco) * qtde,
                            'total': float(preco) * qtde
                        })
                        request.session['cart'] = cart_session

        # Monta lista de itens para template adicionando o product só para exibição
        carts = []
        for item in cart_session:
            product = Product.objects.filter(id=item.get('product_id')).first()
            item_copy = item.copy()  # evita alterar a sessão
            item_copy['product'] = product
            carts.append(item_copy)

        cart_total = sum([item['total'] for item in carts if item.get('total')])
        total_itens = sum([item['qtde'] for item in carts])

        return render(request, 'cart.html', {
            'banners': banners,
            'carts': carts,
            'cart_total': cart_total,
            'total_itens': total_itens
        })


# Create your views here.
def timeout_view(request):
    return render(request, 'timeout.html')
# Assuming this is your view for the page

def index(request):
    banners = Banner.objects.filter(ativo=True)
    # Limpa carrinho do usuário logado
    if request.user.is_authenticated:
        from .models import Cart
        Cart.objects.filter(user=request.user).delete()
    # Limpa carrinho da sessão para anônimo
    if 'cart' in request.session:
        request.session['cart'] = []
    return render(request, 'index.html', {'banners': banners})

def category_list(request):
    # Pega todas as categorias ativas do banco de dados
    banners = Banner.objects.filter(ativo=True)
    categories = Category.objects.filter(active=True)

    # Filtros do GET
    category_id = request.GET.get('category')
    search = request.GET.get('search', '').strip()

    filtered_categories = []
    for category in categories:
        products = category.products.filter(active=True)
        if category_id:
            if str(category.id) != str(category_id):
                continue
        if search:
            products = products.filter(title__icontains=search)
        category.active_products = products
        if products.exists():
            filtered_categories.append(category)

    return render(request, 'category_list.html', {
        'banners': banners,
        'categories': filtered_categories,
    })

def contato(request):
    banners = Banner.objects.filter(ativo=True)
    return render(request, 'contato.html', {'banners': banners})

def sobre(request):
    banners = Banner.objects.filter(ativo=True)
    return render(request, 'sobre.html', {'banners': banners})

def relatorio_carrinho(request):
    carts = Cart.objects.all()
    total_geral = sum([c.total for c in carts])
    return render(request, "relatorio.html", {"carts": carts, "total_geral": total_geral})

def relatorio_pdf(request):
    # Dados do carrinho
    carts = Cart.objects.all()
    total_geral = 1

    # Carregar template
    template_path = "relatorio_pdf.html"
    context = {"carts": carts, "total_geral": total_geral}

    # Resposta como PDF
    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = 'inline; filename="relatorio.pdf"'

    # Renderizar HTML
    template = get_template(template_path)
    html = template.render(context)

    # Gerar PDF
    pisa_status = pisa.CreatePDF(html, dest=response)

    if pisa_status.err:
        return HttpResponse("Erro ao gerar PDF", status=500)
    return response

def relatorio_excel(request):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Relatório Carrinho"

    # Cabeçalhos
    ws.append(["Produto", "Qtd", "Subtotal", "Total"])

    # Dados
    carts = Cart.objects.all()
    for c in carts:
        ws.append([c.product.title, c.qtde, c.subtotal, c.total])

    # Resposta HTTP
    response = HttpResponse(content_type="application/vnd.ms-excel")
    response["Content-Disposition"] = "attachment; filename=relatorio.xlsx"
    wb.save(response)
    return response
