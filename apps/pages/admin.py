from django.contrib import admin
from django.http import HttpResponse
from django.template.loader import get_template
from xhtml2pdf import pisa
from .models import Banner, Category, Product, Cart, Order, OrderItem
from django.utils import timezone

def gerar_pdf_pedidos(modeladmin, request, queryset):
    orders = queryset.prefetch_related('items__product')
    total_geral = sum(order.get_order_total for order in orders)

    # Calcular período do relatório
    if orders.exists():
        data_inicio = min(order.data_pedido for order in orders).strftime('%d/%m/%Y')
        data_fim = max(order.data_pedido for order in orders).strftime('%d/%m/%Y')
        periodo = f"{data_inicio} a {data_fim}"
    else:
        periodo = "Sem pedidos neste período"

    template_path = 'relatorio_pedido_pdf.html'
    context = {
        'orders': orders,
        'total_geral': total_geral,
        'periodo': periodo
    }

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'inline; filename="relatorio_pedidos.pdf"'
    template = get_template(template_path)
    html = template.render(context)
    pisa_status = pisa.CreatePDF(html, dest=response)
    if pisa_status.err:
        return HttpResponse("Erro ao gerar PDF", status=500)
    return response

gerar_pdf_pedidos.short_description = "Gerar PDF dos pedidos selecionados"

class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'nome', 'telefone', 'get_order_total', 'data_pedido')
    list_filter = ('data_pedido',)
    actions = [gerar_pdf_pedidos]

admin.site.register(Banner)
admin.site.register(Category)
admin.site.register(Product)
admin.site.register(Cart)
admin.site.register(Order, OrderAdmin)
admin.site.register(OrderItem)
