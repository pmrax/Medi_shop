from flask import Blueprint, request, render_template, flash, redirect, url_for
from flask_login import login_required, current_user
from app.models.checkout_model.checkout import CheckoutModel
from app.models.cart_model.cart import CartModel
from app import mongo, product_mongo, order_mongo

checkout_bp = Blueprint("checkout", __name__)

checkout_model = CheckoutModel(mongo.db, order_mongo.db)  
cart_model = CartModel(mongo.db, product_mongo.db) 

# -------------------- CHECKOUT PAGE --------------------
@checkout_bp.route("/", methods=["GET", "POST"])
@login_required
def checkout():
    """Display order summary, allow address update, and select payment method."""
    customer_data = checkout_model.get_customer_orders(current_user.id)
    cart_items = cart_model.get_cart_items(current_user.id)
    total_price = sum(item["price"] * item["quantity"] for item in cart_items)

    if not cart_items:
        flash("Your cart is empty!", "warning")
        return redirect(url_for("cart.view_cart"))

    if request.method == "POST":
        new_address = request.form.get("address")
        payment_method = request.form.get("payment_method")

        if new_address:
            checkout_model.update_address(current_user.id, new_address)

        if payment_method not in ["Online Payment", "Cash on Delivery"]:
            flash("Invalid payment method selected.", "danger")
            return render_template("checkout.html", customer=customer_data, cart_items=cart_items, total_price=total_price)

        order_id = checkout_model.create_order(current_user.id, cart_items, total_price, payment_method)
        cart_model.clear_cart(current_user.id) 

        flash("Order placed successfully!", "success")
        return redirect(url_for("order.confirmation", order_id=str(order_id)))

    return render_template("checkout.html", customer=customer_data, cart_items=cart_items, total_price=total_price)


