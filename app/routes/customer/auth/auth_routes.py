from flask import Blueprint, request, render_template, redirect, url_for, flash, session
from flask_bcrypt import Bcrypt
from flask_login import login_user, logout_user, login_required
from app.models.auth_model.customer_auth import Customer

bcrypt = Bcrypt()
auth_bp = Blueprint("auth", __name__)

@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    """Customer Registration"""
    if request.method == "POST":
        username = request.form.get("username")
        email = request.form.get("email")
        mobile_no = request.form.get("mobile_no")
        password = request.form.get("password")
        confirm_password = request.form.get("confirm_password")

        result = Customer.register(username, email, mobile_no, password, confirm_password)

        if "error" in result:
            flash(result["error"], "danger")
            return redirect(url_for("auth.register"))

        flash("Registration successful! Please log in.", "success")
        return redirect(url_for("auth.login"))

    return render_template("customers/auth/register.html")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    """Customer Login"""
    if request.method == "POST":
        identifier = request.form.get("identifier") 
        password = request.form.get("password")

        user = Customer.login(identifier, password)
        if user:
            login_user(user)
            session["customer_id"] = user.id  
            flash("Login successful!", "success")
            return redirect(url_for("dashboard.dashboard"))

        flash("Invalid credentials. Please try again.", "danger")

    return render_template("customers/auth/login.html")


@auth_bp.route("/logout")
@login_required
def logout():
    """Customer Logout"""
    logout_user()
    session.pop("customer_id", None)  
    flash("Logged out successfully.", "info")
    return redirect(url_for("dashboard.dashboard"))


