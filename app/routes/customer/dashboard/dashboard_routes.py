from flask import render_template, Blueprint
from app import product_mongo 
from bson.json_util import dumps

dashboard_bp = Blueprint("dashboard", __name__)

@dashboard_bp.route("/")
def dashboard():
    """Customer Dashboard - Displays Available Medicines"""


    medicines = list(product_mongo.db.medicines.find({}, {"name": 1, "image_url": 1}))

    return render_template("index.html", medicines=medicines)
