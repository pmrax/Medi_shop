from flask import Blueprint, render_template
from flask_login import login_required
from app.models.product_model.seller_products import ProductModel  
from app import product_mongo
from bson import ObjectId

product_bp = Blueprint("product", __name__)

product_model = ProductModel(product_mongo.db)

@product_bp.route("/medicines")
@login_required 
def list_medicines():
    """Fetch all medicines with images and names for display"""
    medicines = product_model.get_all_medicines()
    return render_template("index.html", medicines=medicines)

@product_bp.route("/m?/<medicine_id>")
@login_required
def view_medicine(medicine_id):
    """Displays detailed information about a selected medicine"""
    medicine_details = product_model.get_medicine_details(ObjectId(medicine_id))
    
    if not medicine_details:
        return "Medicine not found",
    
    return render_template("default_medicine.html", medicine=medicine_details)

