from flask import Blueprint, request, jsonify, flash, render_template
from flask_login import login_required, current_user
from bson import ObjectId
from app.models.cart_model.cart import CartModel
from app.models.product_model.seller_products import ProductModel 
from app import mongo, product_mongo  

cart_bp = Blueprint("cart", __name__)

cart_model = CartModel(mongo.db, product_mongo.db)

# -------------------- ADD TO CART --------------------
@cart_bp.route("/add", methods=["POST"])
@login_required
def add_to_cart():
    """Add a medicine to the cart."""
    try:
        medicine_id = request.form.get("medicine_id")
        price = float(request.form.get("price"))
        quantity = int(request.form.get("quantity", 1))

        if not medicine_id or not price:
            return jsonify({"error": "Invalid medicine data"}), 400

        cart_model.add_to_cart(current_user.id, medicine_id, price, quantity)
        flash("Medicine added to cart!", "success")

        cart_items = cart_model.get_cart_items(current_user.id)
        total_price = sum(item["price"] * item["quantity"] for item in cart_items)

        return render_template("cart.html", cart_items=cart_items, total_price=total_price)

    except Exception as e:
        print(f"Error adding to cart: {e}")
        return jsonify({"error": "Failed to add to cart"}), 500


# -------------------- VIEW CART --------------------
@cart_bp.route("/view", methods=["GET"])
@login_required
def view_cart():
    """Fetch and display cart items."""
    try:
        cart_items = cart_model.get_cart_items(current_user.id)
        total_price = sum(item["price"] * item["quantity"] for item in cart_items)

        return render_template("cart.html", cart_items=cart_items, total_price=total_price)

    except Exception as e:
        print(f"Error fetching cart: {e}")
        return jsonify({"error": "Failed to fetch cart"}), 500


# -------------------- REMOVE ITEM FROM CART --------------------
@cart_bp.route("/remove/<cart_id>", methods=["POST"])
@login_required
def remove_from_cart(cart_id):
    """Remove an item from the cart."""
    try:
        cart_model.remove_from_cart(cart_id)
        flash("Item removed from cart.", "success")

        cart_items = cart_model.get_cart_items(current_user.id)
        total_price = sum(item["price"] * item["quantity"] for item in cart_items)

        return render_template("cart.html", cart_items=cart_items, total_price=total_price)

    except Exception as e:
        print(f"Error removing cart item: {e}")
        return jsonify({"error": "Failed to remove item"}), 500


# -------------------- CLEAR CART --------------------
@cart_bp.route("/clear", methods=["POST"])
@login_required
def clear_cart():
    """Clear all items in the customer's cart."""
    try:
        cart_model.clear_cart(current_user.id)
        flash("Cart cleared successfully.", "success")

        return render_template("cart.html", cart_items=[], total_price=0.0)

    except Exception as e:
        print(f"Error clearing cart: {e}")
        return jsonify({"error": "Failed to clear cart"}), 500

