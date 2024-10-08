from django.shortcuts import get_object_or_404

from ecommerce.models import Product
from decimal import Decimal, ROUND_DOWN


class Cart:
    def __init__(self, request):
        self.request = request
        self.session = self.request.session

    def get_cart_items(self, request):
        return request.session.get('cart', {})

    def add_cart_item(self, request, product):
        cart = self.get_cart_items(request)
        product_id = str(product.id)

        if product_id not in cart:
            cart[product_id] = 1
        else:
            cart[product_id] += 1

        request.session['cart'] = cart

    def minus_cart_item(self, request, product):
        cart = self.get_cart_items(request)
        product_id = str(product.id)

        if product_id in cart:
            if cart[product_id] > 1:
                cart[product_id] -= 1
            else:
                del cart[product_id]

        request.session['cart'] = cart

    def remove_cart_item(self, request, product_id):
        cart = self.get_cart_items(request)
        if str(product_id) in cart:
            del cart[str(product_id)]
        request.session['cart'] = cart

    def get_total_price(self, request):
        total = Decimal('0')  # Ensure total is a Decimal
        cart = self.get_cart_items(request)

        # Preload product prices and stock into a dictionary
        products = {str(product.id): {'price': product.price, 'discount': product.discount} for product in
                    Product.objects.all()}

        for product_id, quantity in cart.items():
            if product_id in products:
                price = products[product_id]['price']
                stock = products[product_id]['discount']  # Fetch stock

                # Assuming stock holds the discount percentage
                discount_percentage = Decimal(stock if stock > 0 else 0)  # Ensure it's a Decimal
                discounted_price = price * (Decimal('1') - discount_percentage / Decimal('100'))

                total += int(quantity) * discounted_price  # Make sure quantity is int

        # Format total to 2 decimal places
        total = total.quantize(Decimal('0.00'), rounding=ROUND_DOWN)

        return total

    def get_product_keys(self, request):
        cart = self.get_cart_items(request)
        return cart.keys()

    def get_product_values(self, request):
        cart = self.get_cart_items(request)
        return cart.values()

    def get_cart(self, request):
        cart = self.get_cart_items(request)
        return cart.items()

    def cart_len(self, request):
        cart = self.get_cart_items(request)
        return len(cart)

    def get_quantity(self, request, product_id):
        cart = self.get_cart_items(request)
        return cart.get(str(product_id), 1)

    def get_total(self, request, product_id):
        cart = self.get_cart_items(request)
        total = Decimal(0)

        # product_id ni string ga aylantirish
        product_id_str = str(product_id)

        # Cartdan quantity ni olish, agar bo'lmasa 0 qaytaradi
        quantity = cart.get(product_id_str, 0)

        # Mahsulotni olish
        product = get_object_or_404(Product, id=product_id)

        # Mahsulot narxi va stock
        price = product.price
        stock = Decimal(product.discount)  # Stockni Decimal ga aylantirish

        # Narxni hisoblash
        if quantity > 0:  # Faqat agar cartda mahsulot bo'lsa
            total += Decimal(quantity) * (price * (Decimal('1') - stock / Decimal('100')))

        return total.quantize(Decimal('0.00'), rounding=ROUND_DOWN)
