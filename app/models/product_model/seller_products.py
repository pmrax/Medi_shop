from bson import ObjectId
from datetime import datetime
import cloudinary.uploader

class ProductModel:
    def __init__(self, db):
        """Initialize the product model with database collections."""
        self.medicines = db.medicines  # Collection for medicines
        self.seller_listings = db.seller_listings  # Collection for seller-specific listings
        self.reviews = db.reviews  # Collection for customer reviews

    def add_medicine(self, name, brand, composition, category, description, image_file, 
                     interactions, uses, dosage, side_effects, substitutes):
        """Adds a new medicine to the global product catalog or retrieves an existing one."""
        
        # Check if medicine already exists
        existing_medicine = self.medicines.find_one({
            "name": name,
            "brand": brand,
            "composition": composition
        })

        if existing_medicine:
            return str(existing_medicine["_id"])  # Return existing medicine ID

        # Upload image if provided
        image_url = self.upload_image(image_file) if image_file else None

        # Create new medicine entry
        medicine_data = {
            "name": name,
            "brand": brand,
            "composition": composition,
            "category": category,
            "description": description,
            "image_url": image_url,
            "interactions": interactions,
            "uses": uses,
            "dosage": dosage,
            "side_effects": side_effects,
            "substitutes": substitutes,
            "created_at": datetime.utcnow()
        }
        inserted_id = self.medicines.insert_one(medicine_data).inserted_id
        return str(inserted_id)

    def add_seller_listing(self, seller_id, medicine_id, price, stock, return_policy, additional_details={}):
        """Adds a seller's listing for an existing medicine."""
        listing_data = {
            "seller_id": ObjectId(seller_id),
            "medicine_id": ObjectId(medicine_id),
            "price": price,
            "stock": stock,
            "return_policy": return_policy,
            "additional_details": additional_details,
            "created_at": datetime.utcnow()
        }
        self.seller_listings.insert_one(listing_data)

    def upload_image(self, image_file):
        """Uploads an image to Cloudinary and returns the image URL."""
        try:
            result = cloudinary.uploader.upload(image_file)
            return result.get("secure_url")  
        except Exception as e:
            print(f"Cloudinary Upload Error: {e}")
            return None

    def add_review(self, customer_id, medicine_id, rating, comment):
        """Allows customers to submit reviews for a medicine."""
        review_data = {
            "customer_id": ObjectId(customer_id),
            "medicine_id": ObjectId(medicine_id),
            "rating": rating,
            "comment": comment,
            "created_at": datetime.utcnow()
        }
        self.reviews.insert_one(review_data)

    def get_medicine_details(self, medicine_id):
        """Fetch medicine details along with available sellers and average rating."""
        medicine = self.medicines.find_one({"_id": ObjectId(medicine_id)})
        if not medicine:
            return None

        sellers = list(self.seller_listings.find({"medicine_id": ObjectId(medicine_id)}))

        reviews = list(self.reviews.find({"medicine_id": ObjectId(medicine_id)}))
        
        avg_rating = round(sum(r["rating"] for r in reviews) / len(reviews), 1) if reviews else None

        return {
            "medicine": medicine,
            "sellers": sellers,
            "reviews": reviews,
            "average_rating": avg_rating
        }

    def get_all_medicines(self):
        """Fetch all medicines with at least one seller listing."""
        pipeline = [
            {
                "$lookup": {
                    "from": "seller_listings",
                    "localField": "_id",
                    "foreignField": "medicine_id",
                    "as": "sellers"
                }
            },
            {
                "$match": {
                    "sellers": {"$ne": []} 
                }
            },
            {
                "$lookup": {
                    "from": "reviews",
                    "localField": "_id",
                    "foreignField": "medicine_id",
                    "as": "reviews"
                }
            },
            {
                "$addFields": {
                    "average_rating": {
                        "$cond": {
                            "if": {"$gt": [{"$size": "$reviews"}, 0]},
                            "then": {"$avg": "$reviews.rating"},
                            "else": None
                        }
                    }
                }
            }
        ]
        return list(self.medicines.aggregate(pipeline))



