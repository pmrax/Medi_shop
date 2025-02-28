from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from bson import ObjectId
from datetime import datetime
from app.models.auth_model.seller_auth import Seller
from app import seller_mongo, bcrypt
import cloudinary.uploader

seller_auth_bp = Blueprint("seller_auth", __name__, url_prefix="/seller/auth")

# Seller Registration
@seller_auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        full_name = request.form.get("full_name")
        business_name = request.form.get("business_name")
        email = request.form.get("email")
        phone_number = request.form.get("phone_number")
        password = request.form.get("password")
        confirm_password = request.form.get("confirm_password")

        if password != confirm_password:
            flash("Passwords do not match!", "danger")
            return redirect(url_for("seller_auth.register"))

        existing_seller = seller_mongo.db.sellers.find_one({"$or": [{"email": email}, {"phone_number": phone_number}]})
        if existing_seller:
            flash("Email or phone number already registered!", "danger")
            return redirect(url_for("seller_auth.register"))

        hashed_password = bcrypt.generate_password_hash(password).decode("utf-8")

        seller_data = {
            "full_name": full_name,
            "business_name": business_name,
            "email": email,
            "phone_number": phone_number,
            "password_hash": hashed_password,
            "created_at": datetime.utcnow(),
            "profile_completed": False
        }
        seller_mongo.db.sellers.insert_one(seller_data)

        flash("Registration successful! Please log in.", "success")
        return redirect(url_for("seller_auth.login"))

    return render_template("sellers/auth/seller_register.html")

# Seller Login
@seller_auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        identifier = request.form.get("identifier")
        password = request.form.get("password")

        seller = seller_mongo.db.sellers.find_one({"$or": [{"email": identifier}, {"phone_number": identifier}]})
        if seller and "password_hash" in seller and bcrypt.check_password_hash(seller["password_hash"], password):
            seller_obj = Seller(seller)
            login_user(seller_obj)

            flash("Login successful!", "success")

            if not seller.get("profile_completed", False):
                flash("Please complete your profile to start selling.", "info")
                return redirect(url_for("seller_auth.profile"))

            return redirect(url_for("seller_dashboard.home"))

        flash("Invalid email/phone or password!", "danger")

    return render_template("sellers/auth/seller_login.html")

# Seller Logout
@seller_auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Logged out successfully!", "success")
    return redirect(url_for("seller_auth.login"))

@seller_auth_bp.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    if request.method == "POST":
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
                "landmark": request.form.get("landmark", ""),  
            },
            "bank_details": {
                "account_holder": request.form.get("account_holder"),
                "account_number": request.form.get("account_number"),
                "ifsc_code": request.form.get("ifsc_code"),
                "upi_id": request.form.get("upi_id", ""),  
            },
            "business_details": {
                "business_name": request.form.get("business_name"),
                "business_category": request.form.get("business_category"),
                "business_website": request.form.get("business_website", ""),
                "business_description": request.form.get("business_description", "")
            },
            "profile_completed": True, 
            "updated_at": datetime.utcnow() 
        }


        image_fields = ["profile_image", "store_logo", "store_banner"]
        for field in image_fields:
            if field in request.files and request.files[field].filename:
                image_url = upload_image_to_cloudinary(request.files[field], f"sellers/{current_user.id}")
                if image_url:
                    updates[field] = image_url


        result = seller_mongo.db.sellers.update_one(
            {"_id": ObjectId(current_user.id)}, {"$set": updates}
        )

        if result.matched_count == 0:
            flash("Error updating profile. Please try again.", "danger")
            return redirect(url_for("seller_dashboard.profile"))

        flash("Profile updated successfully!", "success")
        return redirect(url_for("seller_dashboard.home"))

    return render_template("sellers/seller_profile.html", seller=current_user)


def upload_image_to_cloudinary(image_file, folder):
    try:
        upload_result = cloudinary.uploader.upload(image_file, folder=folder)
        return upload_result.get("secure_url")
    except Exception as e:
        print(f"Cloudinary Upload Error: {e}")
        return None


