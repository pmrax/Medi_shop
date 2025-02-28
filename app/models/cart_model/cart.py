from bson import ObjectId
from datetime import datetime

class CartModel:
    def __init__(self, customer_db, product_db):
        """Initialize the cart model with separate customer and product databases."""
        self.cart = customer_db.cart  
        self.medicines = product_db.medicines  

    def add_to_cart(self, customer_id, medicine_id, price, quantity=1):
        """Add a medicine to the customer's cart or update quantity if it exists."""
        existing_item = self.cart.find_one({
            "customer_id": ObjectId(customer_id),
            "medicine_id": ObjectId(medicine_id)
        })

        if existing_item:
            new_quantity = existing_item["quantity"] + quantity
            self.cart.update_one(
                {"_id": existing_item["_id"]}, {"$set": {"quantity": new_quantity, "updated_at": datetime.utcnow()}}
            )
        else:
            cart_item = {
                "customer_id": ObjectId(customer_id),
                "medicine_id": ObjectId(medicine_id),
                "price": price,
                "quantity": quantity,
                "added_at": datetime.utcnow(),
            }
            self.cart.insert_one(cart_item)

    def get_cart_items(self, customer_id):
        """Fetch all cart items for a specific customer with medicine details manually."""
        cart_items = list(self.cart.find({"customer_id": ObjectId(customer_id)}))

        for item in cart_items:
            medicine = self.medicines.find_one({"_id": item["medicine_id"]})  
            if medicine:
                item["medicine"] = medicine 

        return cart_items

    def remove_from_cart(self, cart_id):
        """Remove an item from the cart."""
        self.cart.delete_one({"_id": ObjectId(cart_id)})

    def clear_cart(self, customer_id):
        """Clear all items in a customer's cart."""
        self.cart.delete_many({"customer_id": ObjectId(customer_id)})
