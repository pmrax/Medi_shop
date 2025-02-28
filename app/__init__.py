from flask import Flask
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from flask_pymongo import PyMongo
from flask_socketio import SocketIO
from dotenv import load_dotenv
import os
from bson import ObjectId
import cloudinary
import cloudinary.uploader
import cloudinary.api

# Load environment variables
load_dotenv()

bcrypt = Bcrypt()
login_manager = LoginManager()
mongo = PyMongo()  # Customer database (including cart)
seller_mongo = PyMongo()  # Seller database
product_mongo = PyMongo()  # Product database
order_mongo = PyMongo()  # Order database
socketio = SocketIO(cors_allowed_origins="*")  

def create_app():
    """Initialize the Flask app with configurations."""
    app = Flask(__name__)

    # Load Configurations
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")
    app.config["CUSTOMER_DB_URI"] = os.getenv("CUSTOMER_DB_URI")
    app.config["SELLER_DB_URI"] = os.getenv("SELLER_DB_URI")
    app.config["PRODUCT_DB_URI"] = os.getenv("PRODUCT_DB_URI")
    app.config["ORDER_DB_URI"] = os.getenv("ORDER_DB_URI")

    # MongoDB Initialization
    app.config["MONGO_URI"] = app.config["CUSTOMER_DB_URI"]
    mongo.init_app(app)  # Customer DB (includes cart)
    seller_mongo.init_app(app, uri=app.config["SELLER_DB_URI"])
    product_mongo.init_app(app, uri=app.config["PRODUCT_DB_URI"])  # Product DB
    order_mongo.init_app(app, uri=app.config["ORDER_DB_URI"])  # Order DB

    # Initialize other Flask extensions
    bcrypt.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"

    # Cloudinary Configuration
    cloudinary.config(
        cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
        api_key=os.getenv("CLOUDINARY_API_KEY"),
        api_secret=os.getenv("CLOUDINARY_API_SECRET")
    )

    # Import Models
    from app.models.auth_model.customer_auth import Customer
    from app.models.auth_model.seller_auth import Seller

    @login_manager.user_loader
    def load_user(user_id):
        """Load either a customer or a seller from MongoDB using user_id."""
        customer = mongo.db.customers.find_one({"_id": ObjectId(user_id)})
        if customer:
            return Customer(customer)
        
        seller = seller_mongo.db.sellers.find_one({"_id": ObjectId(user_id)})
        if seller:
            return Seller(seller)
        
        return None  

    # Register Customer Blueprints
    from app.routes.customer.dashboard.dashboard_routes import dashboard_bp
    from app.routes.customer.auth.auth_routes import auth_bp
    from app.routes.customer.profile.profile_routes import profile_bp
    from app.routes.customer.products.product_routes import product_bp
    from app.routes.customer.cart.cart_routes import cart_bp  # Cart routes
    from app.routes.customer.checkout_routes.checkout import checkout_bp 
    
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(profile_bp, url_prefix="/profile")
    app.register_blueprint(product_bp, url_prefix="/medicine")
    app.register_blueprint(cart_bp, url_prefix="/cart")  # Register cart routes
    app.register_blueprint(checkout_bp, url_prefix="/checkout")
    
    # Register Seller Blueprints
    from app.routes.seller.auth.seller_auth_routes import seller_auth_bp
    from app.routes.seller.seller_dashboard.seller_dashboard_routes import seller_dashboard_bp
    from app.routes.seller.medicines.products_routes import seller_product_bp

    app.register_blueprint(seller_auth_bp, url_prefix="/seller/auth")
    app.register_blueprint(seller_dashboard_bp, url_prefix="/seller/dashboard")
    app.register_blueprint(seller_product_bp, url_prefix="/seller/products")

    # Initialize SocketIO
    socketio.init_app(app)

    return app
