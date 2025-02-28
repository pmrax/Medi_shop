from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from bson import ObjectId
from app import seller_mongo
import cloudinary.uploader
from datetime import datetime

seller_dashboard_bp = Blueprint("seller_dashboard", __name__, url_prefix="/seller/dashboard")

# Ensure Seller Profile is Completed
def check_profile_completion():
    seller = seller_mongo.db.sellers.find_one({"_id": ObjectId(current_user.id)})
    if not seller or not seller.get("profile_completed"):
        flash("Please complete your profile to access the dashboard.", "warning")
        return redirect(url_for("seller_dashboard.profile"))
    return None

# Seller Dashboard Home
@seller_dashboard_bp.route("/")
@login_required
def home():
    profile_redirect = check_profile_completion()
    if profile_redirect:
        return profile_redirect

    seller_id = ObjectId(current_user.id)
    orders = seller_mongo.db.orders.find({"seller_id": seller_id})

    return render_template(
        "sellers/seller_dashboard.html",
        seller=current_user,
        orders=list(orders)
    )

# Seller Profile Route (Complete Additional Details)
@seller_dashboard_bp.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    if request.method == "POST":
        # Validate required fields
        required_fields = [
            "pharmacy_license", "gst_number", "drug_license_number", "drug_license_expiry", "seller_type",
            "shop_address", "city", "state", "pincode", "country",
            "account_holder", "account_number", "ifsc_code",
            "business_name", "full_name", "phone_number", "email"
        ]
        missing_fields = [field for field in required_fields if not request.form.get(field)]

        if missing_fields:
            flash(f"Missing required fields: {', '.join(missing_fields)}", "danger")
            return redirect(url_for("seller_dashboard.profile"))

        # Collect additional profile details
        updates = {
            "pharmacy_license": request.form.get("pharmacy_license"),
            "gst_number": request.form.get("gst_number"),
            "drug_license_number": request.form.get("drug_license_number"),
            "drug_license_expiry": request.form.get("drug_license_expiry"),
            "seller_type": request.form.get("seller_type"),
            "full_name": request.form.get("full_name"),
            "phone_number": request.form.get("phone_number"),
            "email": request.form.get("email"),
            "address": {
                "shop_address": request.form.get("shop_address"),
                "city": request.form.get("city"),
                "state": request.form.get("state"),
                "pincode": request.form.get("pincode"),
                "country": request.form.get("country"),
                "landmark": request.form.get("landmark", ""),  # Optional field
            },
            "bank_details": {
                "account_holder": request.form.get("account_holder"),
                "account_number": request.form.get("account_number"),
                "ifsc_code": request.form.get("ifsc_code"),
                "upi_id": request.form.get("upi_id", ""),  # Optional field
            },
            "business_details": {
                "business_name": request.form.get("business_name"),
                "business_category": request.form.get("business_category"),
                "business_website": request.form.get("business_website", ""),
                "business_description": request.form.get("business_description", "")
            },
            "profile_completed": True,  # Mark profile as completed
            "updated_at": datetime.utcnow()  # Track update time
        }

        # Handle Image Uploads
        image_fields = ["profile_image", "store_logo", "store_banner"]
        for field in image_fields:
            if field in request.files and request.files[field].filename:
                image_url = upload_image_to_cloudinary(request.files[field], f"sellers/{current_user.id}")
                if image_url:
                    updates[field] = image_url

        # Update the seller's profile in the database
        result = seller_mongo.db.sellers.update_one(
            {"_id": ObjectId(current_user.id)}, {"$set": updates}
        )

        if result.matched_count == 0:
            flash("Error updating profile. Please try again.", "danger")
            return redirect(url_for("seller_dashboard.profile"))

        flash("Profile updated successfully!", "success")
        return redirect(url_for("seller_dashboard.home"))

    return render_template("sellers/seller_profile.html", seller=current_user)


# Cloudinary Image Upload Function
def upload_image_to_cloudinary(image_file, folder):
    try:
        upload_result = cloudinary.uploader.upload(image_file, folder=folder)
        return upload_result.get("secure_url")
    except Exception as e:
        print(f"Cloudinary Upload Error: {e}")
        return None




