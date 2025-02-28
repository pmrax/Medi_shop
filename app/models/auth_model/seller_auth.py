import cloudinary.uploader
from flask_pymongo import PyMongo
from flask_bcrypt import Bcrypt
from flask_login import UserMixin
from datetime import datetime
from bson import ObjectId
import os

bcrypt = Bcrypt()
seller_mongo = PyMongo()  

class Seller(UserMixin):
    def __init__(self, seller_data):
        self.id = str(seller_data["_id"])
        self.full_name = seller_data.get("full_name")
        self.business_name = seller_data.get("business_name")
        self.email = seller_data.get("email")
        self.phone_number = seller_data.get("phone_number")
        self.password_hash = seller_data.get("password_hash")
        self.created_at = seller_data.get("created_at", datetime.utcnow())

        self.pharmacy_license = seller_data.get("pharmacy_license")
        self.license_document = seller_data.get("license_document")
        self.gst_number = seller_data.get("gst_number")
        self.drug_license_number = seller_data.get("drug_license_number")
        self.drug_license_expiry = seller_data.get("drug_license_expiry")
        self.seller_type = seller_data.get("seller_type")
        self.address = seller_data.get("address", {})
        self.bank_details = seller_data.get("bank_details", {})
        self.compliance_docs = seller_data.get("compliance_docs", {})
        self.business_details = seller_data.get("business_details", {}) 

        self.profile_image = seller_data.get("profile_image")
        self.store_logo = seller_data.get("store_logo")
        self.store_banner = seller_data.get("store_banner")

    @property
    def is_seller(self):
        """Ensure this user is recognized as a seller."""
        return True  
    
    @classmethod
    def register(cls, seller_data):
        """Registers a new seller with basic details."""
        existing_seller = seller_mongo.db.sellers.find_one({
            "$or": [{"email": seller_data["email"]}, {"phone_number": seller_data["phone_number"]}]
        })

        if existing_seller:
            return {"error": "Email or phone number already registered."}

        # Hash password
        seller_data["password_hash"] = bcrypt.generate_password_hash(seller_data.pop("password")).decode("utf-8")
        seller_data.pop("confirm_password", None) 

        seller_data.update({
            "pharmacy_license": None,
            "license_document": None,
            "gst_number": None,
            "drug_license_number": None,
            "drug_license_expiry": None,
            "seller_type": None,
            "address": {},
            "bank_details": {},
            "compliance_docs": {},
            "business_details": {}, 
            "profile_image": None,
            "store_logo": None,
            "store_banner": None,
            "created_at": datetime.utcnow(),
            "profile_completed": False  
        })

        inserted_id = seller_mongo.db.sellers.insert_one(seller_data).inserted_id
        return {"success": "Seller registration successful!", "seller_id": str(inserted_id)}

    @classmethod
    def login(cls, identifier, password):
        """Logs in a seller using email or phone number."""
        seller = seller_mongo.db.sellers.find_one({
            "$or": [{"email": identifier}, {"phone_number": identifier}]
        })

        if seller and bcrypt.check_password_hash(seller["password_hash"], password):
            return cls(seller)
        return None

    @classmethod
    def update_profile(cls, seller_id, updates):
        """Updates seller profile details including images."""
        # Handle image uploads if provided
        if "profile_image" in updates and updates["profile_image"]:
            updates["profile_image"] = cls.upload_image_to_cloudinary(updates["profile_image"], folder="seller_profiles")

        if "store_logo" in updates and updates["store_logo"]:
            updates["store_logo"] = cls.upload_image_to_cloudinary(updates["store_logo"], folder="store_logos")

        if "store_banner" in updates and updates["store_banner"]:
            updates["store_banner"] = cls.upload_image_to_cloudinary(updates["store_banner"], folder="store_banners")

        result = seller_mongo.db.sellers.update_one(
            {"_id": ObjectId(seller_id)}, {"$set": updates}
        )
        if result.matched_count == 0:
            return {"error": "Seller not found."}
        return {"success": "Profile updated successfully!"}

    @classmethod
    def get_seller_by_id(cls, seller_id):
        """Fetches seller details by ID."""
        try:
            seller = seller_mongo.db.sellers.find_one({"_id": ObjectId(seller_id)})
            return cls(seller) if seller else None
        except Exception as e:
            return {"error": str(e)}

    @staticmethod
    def upload_image_to_cloudinary(image_path, folder):
        """Uploads an image to Cloudinary and returns the URL."""
        try:
            result = cloudinary.uploader.upload(image_path, folder=folder)
            return result.get("secure_url") 
        except Exception as e:
            print(f"Cloudinary Upload Error: {e}")
            return None


