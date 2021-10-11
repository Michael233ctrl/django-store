import json
import datetime

from django.contrib import messages
from django.http import JsonResponse, HttpResponseRedirect
from django.core.paginator import Paginator

from .forms import CustomerForm, RatingForm
from .utils import GetDataMixin, guest_order
from .models import Customer, Order, Product, Category, OrderItem, ShippingAddress, Review


class StoreView(GetDataMixin):
    template_name = 'store/store.html'

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)

        products = Product.objects.all().order_by('-created_at')
        p = Paginator(products, 4)
        page = self.request.GET.get('page')
        paginate_by_products = p.get_page(page)

        context['products'] = paginate_by_products

        search_input = self.request.GET.get('search-area') or ''
        if search_input:
            context['products'] = Product.objects.filter(name__contains=search_input)
        context['search_input'] = search_input

        return context


class GetCategoryView(GetDataMixin):
    template_name = 'store/category.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['category'] = Category.objects.get(id=self.kwargs['pk'])

        products = Product.objects.filter(category__id=self.kwargs['pk']).order_by('-created_at')
        p = Paginator(products, 4)
        page = self.request.GET.get('page')
        paginate_by_products = p.get_page(page)
        context['products'] = paginate_by_products

        return context


class ProductDetailView(GetDataMixin):
    template_name = 'store/product_detail.html'

    def post(self, request, *args, **kwargs):
        if 'write-review' in request.POST:
            product = Product.objects.get(slug=kwargs['product_slug'])
            already_exists = product.review_set.filter(customer=request.user.customer).exists()
            if already_exists:
                messages.error(request, 'The product already reviewed')
                return HttpResponseRedirect(self.request.path_info)
            else:
                form = RatingForm(request.POST)
                if form.is_valid():
                    review_form = form.cleaned_data
                    review = Review.objects.create(
                        product=product,
                        customer=request.user.customer,
                        rating=review_form['rating'],
                        comment=review_form['comment']
                    )
                    review.save()

                    reviews = product.review_set.all()
                    product.num_reviews = len(reviews)

                    total = 0
                    for i in reviews:
                        total += i.rating
                    product.rating = total / len(reviews)
                    product.save()
        else:
            return super().post(request, *args, **kwargs)

        return self.get(request, *args, **kwargs)

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)

        product = Product.objects.get(slug=self.kwargs['product_slug'])
        category = product.category
        products = category.product_set.all().exclude(id=product.id).order_by('?')[:3]
        count_in_stock = list()
        for i in range(1, (product.count_in_stock + 1)):
            count_in_stock.append(i)

        if self.request.user.is_authenticated:
            try:
                order_item = OrderItem.objects.get(order=self.order, product=product)
                context['order_item'] = order_item
            except OrderItem.DoesNotExist:
                pass

        context['product'] = product
        context['category'] = category
        context['products'] = products
        context['count_in_stock'] = count_in_stock
        context['reviews'] = product.review_set.all()
        context['form_review'] = RatingForm()

        return context


class CartView(GetDataMixin):
    template_name = 'store/cart.html'


class CheckoutView(GetDataMixin):
    template_name = 'store/checkout.html'


class UserProfileView(GetDataMixin):
    model = Order
    template_name = 'store/user-profile.html'

    def post(self, request, *args, **kwargs):
        form = CustomerForm(request.POST, request.FILES, instance=request.user.customer)
        if form.is_valid():
            form.save()
        return self.get(request, *args, **kwargs)

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super(UserProfileView, self).get_context_data(**kwargs)
        customer = self.request.user.customer
        form = CustomerForm(instance=customer)
        orders = Order.objects.filter(customer=customer)
        context['orders'] = orders
        context['form'] = form
        return context


class OrderDetail(GetDataMixin):
    template_name = 'store/order_page.html'

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super(OrderDetail, self).get_context_data(**kwargs)
        order = Order.objects.get(id=self.kwargs['pk'], customer=self.request.user.customer)
        context['order'] = order
        context['shipping'] = order.shippingaddress_set.all()
        context['items'] = order.orderitem_set.all()
        return context


def update_item(request):
    data = json.loads(request.body)
    product_id = data['productId']
    action = data['action']
    try:
        qty = data['qty']
    except:
        qty = ''

    customer, created = Customer.objects.get_or_create(user=request.user)
    product = Product.objects.get(id=product_id)
    order, created = Order.objects.get_or_create(customer=customer, complete=False)
    order_item, created = OrderItem.objects.get_or_create(order=order, product=product)

    if action == 'add':
        order_item.quantity = (order_item.quantity + 1)
    elif action == 'addByQty':
        order_item.quantity += int(qty)
    elif action == 'remove':
        order_item.quantity = (order_item.quantity - 1)
    elif action == 'delete':
        order_item.quantity = 0

    if order_item.quantity >= product.count_in_stock:
        order_item.quantity = product.count_in_stock

    order_item.save()

    if order_item.quantity <= 0:
        order_item.delete()

    return JsonResponse('Item was added', safe=False)


def process_order(request):
    transaction_id = datetime.datetime.now().timestamp()
    data = json.loads(request.body)

    if request.user.is_authenticated:
        customer, created = Customer.objects.get_or_create(user=request.user)
        order, created = Order.objects.get_or_create(customer=customer, complete=False)

        for order_item in order.orderitem_set.all().values('product', 'quantity'):
            for product in Product.objects.filter(id=order_item['product']):
                product.count_in_stock -= order_item['quantity']
                product.save()

    else:
        customer, order = guest_order(request, data)

    total = float(data['form']['total'])
    order.transaction_id = transaction_id

    if total == float(order.get_cart_total):
        order.complete = True
    order.save()

    ShippingAddress.objects.create(
        customer=customer,
        order=order,
        address=data['shipping']['address'],
        city=data['shipping']['city'],
        postal_code=data['shipping']['postal_code'],
        country=data['shipping']['country'],
    )

    return JsonResponse('Payment complete!', safe=False)
