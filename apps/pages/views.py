from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.template.loader import get_template
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Sum, F
from django.contrib.admin.views.decorators import staff_member_required
from xhtml2pdf import pisa
import uuid
import json
import openpyxl

from .models import Banner, Category, Product, Cart, CartItem, Order, OrderItem

# ---------------- Utilitários ----------------
def calcular_totais_itens(carts):
    """Retorna total_itens e total_valor de uma lista de itens"""
    total_itens = sum([getattr(c, 'qtde', 0) for c in carts])
    total_valor = sum([getattr(c, 'total', 0) for c in carts])
    return total_itens, total_valor

# ---------------- Views de Página ----------------
def index(request):
    banners = Banner.objects.filter(ativo=True)
    if request.user.is_authenticated:
        Cart.objects.filter(user=request.user).delete()
    if 'cart' in request.session:
        request.session['cart'] = []
    return render(request, 'index.html', {'banners': banners})

def timeout_view(request):
    return render(request, 'timeout.html')

def contato(request):
    banners = Banner.objects.filter(ativo=True)
    return render(request, 'contato.html', {'banners': banners})

def sobre(request):
    banners = Banner.objects.filter(ativo=True)
    return render(request, 'sobre.html', {'banners': banners})

def category_list(request):
    banners = Banner.objects.filter(ativo=True)
    categories = Category.objects.filter(active=True)

    category_id = request.GET.get('category')
    search = request.GET.get('search', '').strip()
    filtered_categories = []

    for category in categories:
        products = category.products.filter(active=True)
        if category_id and str(category.id) != str(category_id):
            continue
        if search:
            products = products.filter(title__icontains=search)
        category.active_products = products
        if products.exists():
            filtered_categories.append(category)

    return render(request, 'category_list.html', {'banners': banners, 'categories': filtered_categories})

# ---------------- Carrinho ----------------
def Car(request):
    banners = Banner.objects.filter(ativo=True)

    if request.user.is_authenticated:
        cart, _ = Cart.objects.get_or_create(user=request.user)

        if request.method == "POST":
            delete_cart_id = request.POST.get("delete_cart_id")
            if delete_cart_id:
                CartItem.objects.filter(id=delete_cart_id, cart=cart).delete()
            else:
                product_id = request.POST.get("product_id")
                qtde = int(request.POST.get("qtde", 1))
                product = Product.objects.filter(id=product_id).first()
                if product:
                    preco = product.price2 if product.price2 > 0 else product.price
                    if preco > 0:
                        cart_item, _ = CartItem.objects.get_or_create(cart=cart, product=product)
                        cart_item.qtde = qtde
                        cart_item.subtotal = preco * qtde
                        cart_item.total = preco * qtde
                        cart_item.save()

        items = cart.items.all().order_by("-added")
        total_itens, cart_total = calcular_totais_itens(items)

        return render(request, "cart.html", {"banners": banners, "carts": items, "cart_total": cart_total, "total_itens": total_itens})

    else:
        if "cart" not in request.session:
            request.session["cart"] = []

        cart_session = request.session["cart"]
        if request.method == "POST":
            delete_cart_id = request.POST.get("delete_cart_id")
            if delete_cart_id:
                cart_session = [i for i in cart_session if str(i.get("id")) != str(delete_cart_id)]
            else:
                product_id = request.POST.get("product_id")
                qtde = int(request.POST.get("qtde", 1))
                product = Product.objects.filter(id=product_id).first()
                if product:
                    preco = product.price2 if product.price2 > 0 else product.price
                    if preco > 0:
                        found = False
                        for item in cart_session:
                            if str(item.get("product_id")) == str(product_id):
                                item["qtde"] = qtde
                                item["subtotal"] = preco * qtde
                                item["total"] = preco * qtde
                                found = True
                                break
                        if not found:
                            cart_session.append({"id": str(uuid.uuid4()), "product_id": product.id, "qtde": qtde, "subtotal": preco * qtde, "total": preco * qtde})

            request.session["cart"] = cart_session

        carts_list = []
        for item in cart_session:
            product = Product.objects.filter(id=item.get("product_id")).first()
            carts_list.append({"id": item.get("id"), "product": product, "qtde": item.get("qtde", 0), "subtotal": item.get("subtotal", 0), "total": item.get("total", 0)})

        total_itens, cart_total = calcular_totais_itens(carts_list)

        return render(request, "cart.html", {"banners": banners, "carts": carts_list, "cart_total": cart_total, "total_itens": total_itens})

# ---------------- Pedido ----------------
def pedido(request):
    banners = Banner.objects.filter(ativo=True)

    if request.user.is_authenticated:
        cart, _ = Cart.objects.get_or_create(user=request.user)
        items = cart.items.all()
    else:
        items = request.session.get('cart', [])

    total_itens, cart_total = calcular_totais_itens(items)

    return render(request, "pedido.html", {"banners": banners, "carts": items, "total_itens": total_itens, "cart_total": cart_total})

@csrf_exempt
def save_order(request):
    if request.method != "POST":
        return JsonResponse({"success": False, "error": "Método inválido"})
    try:
        data = json.loads(request.body)
        nome = data.get("nome")
        telefone = data.get("telefone")
        items = data.get("items", [])

        if not nome or not telefone:
            return JsonResponse({"success": False, "error": "Nome e telefone são obrigatórios."})

        order = Order.objects.create(
            nome=nome,
            telefone=telefone,
            user=request.user if request.user.is_authenticated else None
        )

        for i in items:
            product_id = i.get("product_id")
            qtde = int(i.get("qtde", 1))
            subtotal = float(i.get("subtotal", 0))
            total = subtotal
            product = Product.objects.filter(id=product_id).first()
            if product:
                OrderItem.objects.create(order=order, product=product, qtde=qtde, subtotal=subtotal, total=total)

        # Limpa carrinho
        if request.user.is_authenticated:
            Cart.objects.filter(user=request.user).delete()
        else:
            request.session['cart'] = []

        return JsonResponse({"success": True, "order_id": order.id})
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)})

@csrf_exempt
def clear_cart(request):
    if request.method == "POST":
        if request.user.is_authenticated:
            Cart.objects.filter(user=request.user).delete()
        else:
            request.session['cart'] = []
        return JsonResponse({"success": True})
    return JsonResponse({"success": False, "error": "Método inválido"})

@csrf_exempt
def update_cart_item(request):
    if request.method != "POST":
        return JsonResponse({"success": False, "error": "Método inválido"})
    try:
        data = json.loads(request.body)
        product_id = data.get("product_id")
        qtde = int(data.get("qtde", 1))
        subtotal = float(data.get("subtotal", 0))

        if request.user.is_authenticated:
            cart, _ = Cart.objects.get_or_create(user=request.user)
            product = Product.objects.filter(id=product_id).first()
            if not product:
                return JsonResponse({"success": False, "error": "Produto não encontrado"})
            cart_item, _ = CartItem.objects.get_or_create(cart=cart, product=product)
            cart_item.qtde = qtde
            cart_item.subtotal = subtotal
            cart_item.total = subtotal
            cart_item.save()
        else:
            if 'cart' not in request.session:
                request.session['cart'] = []
            cart_session = request.session['cart']
            found = False
            for item in cart_session:
                if str(item.get('product_id')) == str(product_id):
                    item['qtde'] = qtde
                    item['subtotal'] = subtotal
                    item['total'] = subtotal
                    found = True
                    break
            if not found:
                cart_session.append({'id': str(uuid.uuid4()), 'product_id': product_id, 'qtde': qtde, 'subtotal': subtotal, 'total': subtotal})
            request.session['cart'] = cart_session

        return JsonResponse({"success": True})
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)})

# ---------------- Relatórios ----------------
@staff_member_required
def relatorio_pedido(request):
    orders = Order.objects.prefetch_related('items__product').all()
    total_geral = sum(order.get_order_total for order in orders)
    return render(request, 'relatorio_pedido.html', {'orders': orders, 'total_geral': total_geral})

@staff_member_required
def relatorio_pedido_excel(request):
    orders = Order.objects.prefetch_related('items__product').all()
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Relatório de Pedidos"
    ws.append(["Pedido ID", "Nome", "Telefone", "Produto", "Qtde", "Subtotal", "Total"])

    for order in orders:
        for item in order.items.all():
            ws.append([order.id, order.nome, order.telefone, item.product.title, item.qtde, float(item.subtotal), float(item.total)])

    response = HttpResponse(content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    response['Content-Disposition'] = 'attachment; filename=relatorio_pedidos.xlsx'
    wb.save(response)
    return response

@staff_member_required
def relatorio_pedido_pdf(request):
    orders = Order.objects.prefetch_related('items__product').all()

    # Para cada item, adiciona a URL da imagem
    for order in orders:
        for item in order.items.all():
            if item.product.image:
                item.product.image_url = f"{settings.MEDIA_URL}{item.product.image}"
            else:
                item.product.image_url = None

    total_geral = sum(order.get_order_total for order in orders)

    template_path = 'relatorio_pedido_pdf.html'
    context = {
        'orders': orders,
        'total_geral': total_geral,
    }
    template = get_template(template_path)
    html = template.render(context)

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'inline; filename="relatorio_pedidos.pdf"'
    pisa_status = pisa.CreatePDF(html, dest=response)

    if pisa_status.err:
        return HttpResponse("Erro ao gerar PDF", status=500)
    return response