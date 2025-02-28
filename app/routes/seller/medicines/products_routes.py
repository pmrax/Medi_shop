from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from bson import ObjectId
from app.models.product_model.seller_products import ProductModel
from app import seller_mongo, product_mongo  
import cloudinary.uploader
from functools import wraps

seller_product_bp = Blueprint("seller_product", __name__)

product_model = ProductModel(product_mongo.db)

def seller_required(func):
    """Ensures that only sellers can access certain routes."""
    @wraps(func)
    @login_required
    def wrapper(*args, **kwargs):
        if not hasattr(current_user, "id"):
            flash("Access restricted to sellers only.", "danger")
            return redirect(url_for("seller_dashboard.dashboard"))
        return func(*args, **kwargs)
    return wrapper


def check_profile_completion():
    seller = seller_mongo.db.sellers.find_one({"_id": ObjectId(current_user.id)})
    if not seller or not seller.get("profile_completed"):
        flash("Please complete your profile to access the dashboard.", "warning")
        return redirect(url_for("seller_dashboard.profile"))
    return None

# ------------------------ ADD PRODUCT ------------------------
@seller_product_bp.route("/add", methods=["GET", "POST"])
@seller_required
def add_product():
    if request.method == "POST":
        name = request.form.get("name")
        brand = request.form.get("brand")
        composition = request.form.get("composition")
        category = request.form.get("category")
        description = request.form.get("description")
        uses = request.form.get("uses")
        dosage = request.form.get("dosage")
        side_effects = request.form.get("side_effects")
        interactions = request.form.get("interactions")
        substitutes = request.form.get("substitutes")
        price = float(request.form.get("price"))
        stock = int(request.form.get("stock"))
        return_policy = request.form.get("return_policy")
        image_file = request.files.get("image")

        medicine_id = product_model.add_medicine(
            name, brand, composition, category, description, image_file,
            interactions, uses, dosage, side_effects, substitutes
        )

        product_model.add_seller_listing(
            seller_id=current_user.id,
            medicine_id=medicine_id,
            price=price,
            stock=stock,
            return_policy=return_policy
        )

        flash("Product added successfully!", "success")
        return redirect(url_for("seller_product.add_product"))

    return render_template("sellers/products/add_products.html")


# ------------------------ MANAGE PRODUCTS ------------------------
@seller_product_bp.route("/manage", endpoint="manage_products")
@seller_required
def manage_products():
    """Shows all products added by the current seller, including full medicine details."""
    seller_id = ObjectId(current_user.id)

    # Aggregate to fetch seller listings along with medicine details
    seller_listings = list(product_mongo.db.seller_listings.aggregate([
        {
            "$match": {"seller_id": seller_id}
        },
        {
            "$lookup": {
                "from": "medicines",
                "localField": "medicine_id",
                "foreignField": "_id",
                "as": "medicine"
            }
        },
        {
            "$unwind": "$medicine"  # Convert list to object
        }
    ]))

    return render_template("sellers/products/manage_products.html", listings=seller_listings)

# ------------------------ EDIT PRODUCT ------------------------
@seller_product_bp.route("/edit/<listing_id>", methods=["GET", "POST"])
@seller_required
def edit_product(listing_id):
    """Allows a seller to edit their product details."""
    
    # Fetch seller listing with medicine details using aggregation
    listing = product_mongo.db.seller_listings.aggregate([
        {"$match": {"_id": ObjectId(listing_id), "seller_id": ObjectId(current_user.id)}},
        {"$lookup": {
            "from": "medicines",
            "localField": "medicine_id",
            "foreignField": "_id",
            "as": "medicine"
        }}
    ])
    
    listing = list(listing)
    if not listing:
        flash("Product not found or unauthorized access.", "danger")
        return redirect(url_for("seller_product.manage_products"))
    
    listing = listing[0]  # Get first result
    listing["medicine"] = listing["medicine"][0] if listing.get("medicine") else {}

    if request.method == "POST":
        # Update seller listing data
        new_price = float(request.form.get("price"))
        new_stock = int(request.form.get("stock"))
        new_return_policy = request.form.get("return_policy")

        seller_update_data = {
            "price": new_price,
            "stock": new_stock,
            "return_policy": new_return_policy
        }
        
        # Update medicine data
        medicine_update_data = {
            "name": request.form.get("name"),
            "brand": request.form.get("brand"),
            "category": request.form.get("category"),
            "composition": request.form.get("composition"),
            "description": request.form.get("description"),
            "uses": request.form.get("uses"),
            "dosage": request.form.get("dosage"),
            "side_effects": request.form.get("side_effects"),
            "interactions": request.form.get("interactions"),
            "substitutes": request.form.get("substitutes"),
        }

        image_file = request.files.get("image")

        # Upload new image if provided
        if image_file:
            new_image_url = product_model.upload_image(image_file)
            medicine_update_data["image_url"] = new_image_url

        # Update seller's product listing
        product_mongo.db.seller_listings.update_one({"_id": ObjectId(listing_id)}, {"$set": seller_update_data})

        # Update medicine details (only if seller is the first one to list it)
        if listing["medicine"].get("created_by") == str(current_user.id):
            product_mongo.db.medicines.update_one({"_id": listing["medicine"]["_id"]}, {"$set": medicine_update_data})

        flash("Product updated successfully!", "success")
        return redirect(url_for("seller_product.manage_products"))

    return render_template("sellers/products/edit_product.html", listing=listing)

# ------------------------ DELETE PRODUCT ------------------------
@seller_product_bp.route("/delete/<listing_id>", methods=["POST"])
@seller_required
def delete_product(listing_id):
    """Allows a seller to delete their product listing."""
    listing = product_mongo.db.seller_listings.find_one({
        "_id": ObjectId(listing_id), "seller_id": ObjectId(current_user.id)
    })
    
    if not listing:
        flash("Product not found or you don't have permission to delete it.", "danger")
        return redirect(url_for("seller_product.manage_products"))

    product_mongo.db.seller_listings.delete_one({"_id": ObjectId(listing_id)})
    flash("Product deleted successfully!", "success")
    return redirect(url_for("seller_product.manage_products"))

# ------------------------ UPDATE STOCK ------------------------
@seller_product_bp.route("/update_stock/<listing_id>", methods=["POST"])
@seller_required
def update_stock(listing_id):
    """Allows sellers to update the stock quantity of a product."""
    new_stock = int(request.form.get("stock"))

    listing = product_mongo.db.seller_listings.find_one({
        "_id": ObjectId(listing_id), "seller_id": ObjectId(current_user.id)
    })
    
    if not listing:
        flash("Product not found or you don't have permission to update stock.", "danger")
        return redirect(url_for("seller_product.manage_products"))

    product_mongo.db.seller_listings.update_one({"_id": ObjectId(listing_id)}, {"$set": {"stock": new_stock}})
    flash("Stock updated successfully!", "success")
    return redirect(url_for("seller_product.manage_products"))
