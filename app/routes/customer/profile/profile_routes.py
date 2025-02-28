from flask import Blueprint, request, render_template, redirect, url_for, flash
from flask_bcrypt import Bcrypt
from flask_login import login_required, current_user
from bson.objectid import ObjectId
from app.models.auth_model.customer_auth import Customer, mongo

bcrypt = Bcrypt()
profile_bp = Blueprint("profile", __name__)

@profile_bp.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    """Customer Profile Page - View & Update Address/Profile Image"""
    customer = mongo.db.customers.find_one({"_id": ObjectId(current_user.id)})

    if request.method == "POST":
        profile_image = request.form.get("profile_image")
        address = {
            "full_name": request.form.get("full_name"),
            "phone": request.form.get("phone"),
            "street": request.form.get("street"),
            "city": request.form.get("city"),
            "town": request.form.get("town"),
            "village": request.form.get("village"),
            "pincode": request.form.get("pincode"),
            "state": request.form.get("state"),
            "country": request.form.get("country"),
        }

        Customer.update_profile(ObjectId(current_user.id), profile_image, address)
        flash("Profile updated successfully!", "success")
        return redirect(url_for("profile.profile"))

    return render_template("customers/profile.html", customer=customer)




