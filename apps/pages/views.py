from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.template.loader import get_template
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Sum, F
from decimal import Decimal
from django.views.decorators.csrf import csrf_protect
from xhtml2pdf import pisa
from .models import Banner, Category, Product, Cart, CartItem, Order, OrderItem

import json
import uuid
import openpyxl

# ---------------- Pedido ----------------
def pedido(request):
    banners = Banner.objects.filter(ativo=True)

    # Usuário logado
    if request.user.is_authenticated:
        cart, _ = Cart.objects.get_or_create(user=request.user)
        carts = CartItem.objects.filter(cart=cart)

        total_itens = carts.aggregate(total=Sum('qtde'))['total'] or 0
        cart_total = carts.aggregate(total=Sum(F('qtde') * F('product__price')))['total'] or 0

        carts_list = []
        for c in carts:
            carts_list.append({
                "product": c.product,
                "qtde": c.qtde,
                "subtotal": c.qtde * c.product.price,
            })

    # Usuário anônimo (sessão)
    else:
        cart_session = request.session.get('cart', [])
        carts_list = []

        for item in cart_session:
            product = Product.objects.filter(id=item.get('product_id')).first()
            carts_list.append({
                "product": product,
                "qtde": item.get('qtde', 0),
                "subtotal": item.get('total', 0),
            })

        total_itens = sum([i["qtde"] for i in carts_list])
        cart_total = sum([i["subtotal"] for i in carts_list])

    return render(request, "pedido.html", {
        "banners": banners,
        "carts": carts_list,
        "total_itens": total_itens,
        "cart_total": cart_total,
    })


# ---------------- Salvar Pedido ----------------
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

        # Cria o pedido sem vincular usuário
        order = Order.objects.create(
            nome=nome,
            telefone=telefone
        )

        # Cria itens do pedido
        for i in items:
            product_id = i.get("product_id")
            qtde = int(i.get("qtde", 1))
            subtotal = float(i.get("subtotal", 0))  # converte para float
            total = float(subtotal)  # garantir tipo float

            product = Product.objects.filter(id=product_id).first()
            if product:
                OrderItem.objects.create(
                    order=order,
                    product=product,
                    qtde=qtde,
                    subtotal=subtotal,
                    total=total
                )

        # Limpa carrinho
        if request.user.is_authenticated:
            try:
                cart = Cart.objects.get(user=request.user)
                cart.items.all().delete()
            except Cart.DoesNotExist:
                pass
        else:
            request.session['cart'] = []

        return JsonResponse({"success": True, "order_id": order.id})

    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)})
    
        
# ---------------- limpa pedido ----------------

@csrf_exempt
def clear_cart(request):
    if request.method == "POST":
        # Usuário logado
        if request.user.is_authenticated:
            try:
                cart = Cart.objects.get(user=request.user)
                cart.items.all().delete()
            except Cart.DoesNotExist:
                pass
        else:
            # Usuário anônimo via sessão
            if 'cart' in request.session:
                request.session['cart'] = []

        return JsonResponse({"success": True})
    return JsonResponse({"success": False, "error": "Método inválido"})

# ---------------- Carrinho ----------------
def Car(request):
    banners = Banner.objects.filter(ativo=True)

    # Usuário logado
    if request.user.is_authenticated:
        cart, _ = Cart.objects.get_or_create(user=request.user)

        # POST = adicionar ou remover item
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
                        cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product)
                        cart_item.qtde = qtde
                        cart_item.subtotal = float(preco * qtde)
                        cart_item.total = float(preco * qtde)
                        cart_item.save()

        # Listar itens
        items = cart.items.all().order_by("-added")
        cart_total = float(sum([item.total for item in items if item.total]))
        total_itens = sum([item.qtde for item in items])
        return render(request, "cart.html", {
            "banners": banners,
            "carts": items,
            "cart_total": cart_total,
            "total_itens": total_itens
        })

    # Usuário anônimo via sessão
    else:
        if "cart" not in request.session:
            request.session["cart"] = []

        cart_session = request.session["cart"]

        # POST = adicionar ou remover item
        if request.method == "POST":
            delete_cart_id = request.POST.get("delete_cart_id")
            if delete_cart_id:
                cart_session = [item for item in cart_session if str(item.get("id")) != str(delete_cart_id)]
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
                                item["subtotal"] = float(preco * qtde)
                                item["total"] = float(preco * qtde)
                                found = True
                                break
                        if not found:
                            cart_session.append({
                                "id": str(uuid.uuid4()),
                                "product_id": product.id,
                                "qtde": qtde,
                                "subtotal": float(preco * qtde),
                                "total": float(preco * qtde)
                            })

            request.session["cart"] = cart_session

        # Preparar lista para template
        carts_list = []
        for item in cart_session:
            product = Product.objects.filter(id=item.get("product_id")).first()
            carts_list.append({
                "id": item.get("id"),
                "product": product,
                "qtde": item.get("qtde", 0),
                "subtotal": float(item.get("subtotal", 0)),
                "total": float(item.get("total", 0))
            })

        cart_total = float(sum([i["total"] for i in carts_list]))
        total_itens = sum([i["qtde"] for i in carts_list])

        return render(request, "cart.html", {
            "banners": banners,
            "carts": carts_list,
            "cart_total": cart_total,
            "total_itens": total_itens
        })
        
# ---------------- Atualizar item do carrinho ----------------
@csrf_exempt
def update_cart_item(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            product_id = data.get("product_id")
            qtde = int(data.get("qtde", 1))
            subtotal = float(data.get("subtotal", 0))  # converte para float

            if request.user.is_authenticated:
                cart, _ = Cart.objects.get_or_create(user=request.user)
                product = Product.objects.filter(id=product_id).first()
                if not product:
                    return JsonResponse({"success": False, "error": "Produto não encontrado."})

                cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product)
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
                    cart_session.append({
                        'id': str(uuid.uuid4()),
                        'product_id': product_id,
                        'qtde': qtde,
                        'subtotal': subtotal,
                        'total': subtotal
                    })
                request.session['cart'] = cart_session

            return JsonResponse({"success": True})
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)})

    return JsonResponse({"success": False, "error": "Método inválido"})

# ---------------- Outras Views ----------------
def timeout_view(request):
    return render(request, 'timeout.html')

def index(request):
    banners = Banner.objects.filter(ativo=True)
    if request.user.is_authenticated:
        Cart.objects.filter(user=request.user).delete()
    if 'cart' in request.session:
        request.session['cart'] = []
    return render(request, 'index.html', {'banners': banners})

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
    carts = Cart.objects.all()
    total_geral = 1
    template_path = "relatorio_pdf.html"
    context = {"carts": carts, "total_geral": total_geral}
    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = 'inline; filename="relatorio.pdf"'
    template = get_template(template_path)
    html = template.render(context)
    pisa_status = pisa.CreatePDF(html, dest=response)
    if pisa_status.err:
        return HttpResponse("Erro ao gerar PDF", status=500)
    return response

def relatorio_excel(request):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Relatório Carrinho"
    ws.append(["Produto", "Qtd", "Subtotal", "Total"])
    carts = Cart.objects.all()
    for c in carts:
        ws.append([c.product.title, c.qtde, c.subtotal, c.total])
    response = HttpResponse(content_type="application/vnd.ms-excel")
    response["Content-Disposition"] = "attachment; filename=relatorio.xlsx"
    wb.save(response)
    return response
