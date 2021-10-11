import json
from django.contrib import messages
from django.contrib.auth import login
from django.http import HttpResponseRedirect
from django.shortcuts import redirect
from django.views import View
from django.views.generic import ListView
from django.db.models import Count

from .models import Customer, Product, Category, OrderItem, Order
from .forms import LoginForm, RegisterForm


class LogRegMixin(View):

    def post(self, request, *args, **kwargs):
        if 'login' in request.POST:
            form_login = LoginForm(data=request.POST)
            if form_login.is_valid():
                user = form_login.get_user()
                if user:
                    login(request, user)
            else:
                messages.error(request, 'Wrong password or username')

        elif 'register' in request.POST:
            form_register = RegisterForm(request.POST)
            if form_register.is_valid():
                user = form_register.save()
                if user:
                    login(request, user)
                    customer = Customer.objects.create(
                        user=request.user,
                        name=request.POST['first_name'],
                        last_name=request.POST['last_name'],
                        phone=request.POST['phone'],
                        email=request.POST['email'],
                    )
                    customer.save()
                    return redirect('store')
            else:
                messages.error(request, 'Registration error')

        return HttpResponseRedirect(self.request.path_info)


class GetDataMixin(LogRegMixin, ListView):
    model = Product

    def cart_data(self):
        if self.request.user.is_authenticated:
            try:
                customer = Customer.objects.get(user=self.request.user, name=self.request.user.customer)
            except Customer.DoesNotExist:
                customer = Customer(user=self.request.user, name=self.request.user.username,
                                    last_name=self.request.user.last_name, email=self.request.user.email)
                customer.save()

            order, created = Order.objects.get_or_create(customer=customer, complete=False)
            items = order.orderitem_set.all()
            cart_items = order.get_cart_items
        else:
            cookie_data = cookie_cart(self.request)
            cart_items = cookie_data['cart_items']
            order = cookie_data['order']
            items = cookie_data['items']

        self.cart_items = cart_items
        self.items = items
        self.order = order
        return {'cart_items': self.cart_items, 'order': self.order, 'items': self.items}

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)

        data = self.cart_data()
        context['cart_items'] = data['cart_items']
        context['items'] = data['items']
        context['order'] = data['order']
        context['categories'] = Category.objects.annotate(cnt=Count('product')).filter(cnt__gt=0)
        context['form_login'] = LoginForm()
        context['form_register'] = RegisterForm()

        return context


def cookie_cart(request):
    try:
        cart = json.loads(request.COOKIES['cart'])
    except:
        cart = {}
    print('Cart:', cart)
    items = []
    order = {
        'get_cart_total': 0,
        'get_cart_items': 0,
    }
    cart_items = order['get_cart_items']

    for i in cart:
        try:
            cart_items += cart[i]['quantity']

            product = Product.objects.get(id=i)
            total = (product.price * cart[i]['quantity'])

            order['get_cart_total'] += total
            order['get_cart_items'] += cart[i]['quantity']

            item = {
                'product': {
                    'id': product.id,
                    'name': product.name,
                    'slug': product.slug,
                    'price': product.price,
                    'imageURL': product.imageURL,
                    'count_in_stock': product.count_in_stock,
                },
                'quantity': cart[i]['quantity'],
                'get_total': total
            }
            items.append(item)
        except Product.DoesNotExist:
            pass
    return {'cart_items': cart_items, 'order': order, 'items': items}


def guest_order(request, data):
    print('User is not logged in...')
    print('COOKIES', request.COOKIES)

    name = data['form']['name']
    last_name = data['form']['last_name']
    email = data['form']['email']
    phone = data['form']['phone']

    cookie_data = cookie_cart(request)
    items = cookie_data['items']

    customer, create = Customer.objects.get_or_create(name=name, last_name=last_name, email=email, phone=phone)
    customer.save()

    order = Order.objects.create(
        customer=customer,
        complete=False,
    )

    for item in items:
        product = Product.objects.get(id=item['product']['id'])

        product.count_in_stock -= item['quantity']

        product.save()

        OrderItem.objects.create(
            product=product,
            order=order,
            quantity=item['quantity']
        )
    return customer, order
