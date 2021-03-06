from django.shortcuts import render
from django.http import JsonResponse
import json
import datetime
from .models import *
from .utils import cookieCart, cartData, guestOrder


def store(request):
    data = cartData(request)
    cartItems = data['cartItems']

    try:
        viewType = json.loads(request.COOKIES.get('view'))['viewType']
    except:
        viewType = 'grid_view'

    products = Product.objects.all()
    context = {'products': products,
               'cartItems': cartItems, 'viewType': viewType}
    return render(request, 'store/store.html', context)


def cart(request):
    data = cartData(request)
    cartItems = data['cartItems']
    order = data['order']
    items = data['items']

    context = {'items': items, 'order': order, 'cartItems': cartItems}
    return render(request, 'store/cart.html', context)


def checkout(request):
    data = cartData(request)
    cartItems = data['cartItems']
    order = data['order']
    items = data['items']

    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')

    context = {'items': items, 'order': order,
               'cartItems': cartItems, 'clientIP': ip}
    return render(request, 'store/checkout.html', context)


def product(request, slug):
    data = cartData(request)
    cartItems = data['cartItems']

    product = Product.objects.get(id=slug)
    context = {'product': product, 'cartItems': cartItems}
    return render(request, 'store/product.html', context)


def updateItem(request):
    data = json.loads(request.body)
    productId = data['productId']
    action = data['action']

    customer = request.user.customer
    product = Product.objects.get(id=productId)
    order, created = Order.objects.get_or_create(
        customer=customer, complete=False)

    orderItem, created = OrderItem.objects.get_or_create(
        order=order, product=product)

    if action == 'add':
        orderItem.quantity = (orderItem.quantity + 1)
    elif action == 'remove':
        orderItem.quantity = (orderItem.quantity - 1)

    orderItem.save()

    if orderItem.quantity <= 0:
        orderItem.delete()

    return JsonResponse('Item was added', safe=False)


def processOrder(request):
    transaction_id = datetime.datetime.now().timestamp()
    data = json.loads(request.body)

    if request.user.is_authenticated:
        customer = request.user.customer
        order, created = Order.objects.get_or_create(
            customer=customer, complete=False)

    else:
        customer, order = guestOrder(request, data)

    total = format(float(data['form']['total'].replace(',', '.')), '.2f')
    order.transaction_id = transaction_id

    order.complete = True
    order.save()

    if order.shipping == True:
        ShippingAddress.objects.create(
            customer=customer,
            order=order,
            address=data['shipping']['address'],
            zipcode=data['shipping']['zipcode'],
            city=data['shipping']['city'],
        )

    return JsonResponse('Payment complete!', safe=False)


def success(request):
    data = cartData(request)
    cartItems = data['cartItems']
    context = {'cartItems': cartItems}
    return render(request, 'store/success.html', context)


def fail(request):
    data = cartData(request)
    cartItems = data['cartItems']
    context = {'cartItems': cartItems}
    return render(request, 'store/fail.html', context)


def payment_complete(request):
    context = {}
    return render(request, 'store/payment_complete.html', context)
