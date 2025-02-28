from flask_bcrypt import Bcrypt
from flask_login import UserMixin
from bson.objectid import ObjectId
import datetime
from app import mongo 

bcrypt = Bcrypt()

class Customer(UserMixin):
    def __init__(self, customer_data):
        self.id = str(customer_data["_id"])  
        self.username = customer_data.get("username")
        self.email = customer_data.get("email")
        self.mobile_no = customer_data.get("mobile_no")
        self.password_hash = customer_data.get("password_hash")
        self.profile_image = customer_data.get("profile_image", None)
        self.address = customer_data.get("address", {})
        self.created_at = customer_data.get("created_at", datetime.datetime.utcnow())

    @staticmethod
    def register(username, email, mobile_no, password, confirm_password):
        """Registers a new customer."""
        if password != confirm_password:
            return {"error": "Passwords do not match."}

        existing_user = mongo.db.customers.find_one({"$or": [{"email": email}, {"mobile_no": mobile_no}]})
        if existing_user:
            return {"error": "Email or mobile number already registered."}

        password_hash = bcrypt.generate_password_hash(password).decode("utf-8")

        customer_data = {
            "username": username,
            "email": email,
            "mobile_no": mobile_no,
            "password_hash": password_hash,
            "profile_image": None,
            "address": {
                "full_name": "",
                "phone": "",
                "street": "",
                "city": "",
                "town": "",
                "village": "",
                "pincode": "",
                "state": "",
                "country": ""
            },
            "created_at": datetime.datetime.utcnow()
        }

        inserted_id = mongo.db.customers.insert_one(customer_data).inserted_id
        return {"success": "Registration successful!", "user_id": str(inserted_id)}

    @staticmethod
    def login(identifier, password):
        """Logs in a customer using email or mobile number."""
        user = mongo.db.customers.find_one({"$or": [{"email": identifier}, {"mobile_no": identifier}]})

        if user and bcrypt.check_password_hash(user["password_hash"], password):
            return Customer(user) 
        return None

    @staticmethod
    def update_profile(customer_id, profile_image=None, address=None):
        """Updates customer profile image and address."""
        update_data = {}
        if profile_image:
            update_data["profile_image"] = profile_image
        if address:
            update_data["address"] = address

        if update_data:
            mongo.db.customers.update_one({"_id": ObjectId(customer_id)}, {"$set": update_data})
            return {"success": "Profile updated successfully!"}
        return {"error": "No data to update."}

    @staticmethod
    def get_customer_by_id(customer_id):
        """Fetches customer details by ID."""
        user = mongo.db.customers.find_one({"_id": ObjectId(customer_id)})
        return Customer(user) if user else None


