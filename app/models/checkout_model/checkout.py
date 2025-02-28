from bson import ObjectId
from datetime import datetime

class CheckoutModel:
    def __init__(self, customer_db, order_db):
        """Initialize checkout model with customer and order databases."""
        self.customers = customer_db.customers  
        self.orders = order_db.orders  

    def create_order(self, customer_id, cart_items, total_price, payment_method, payment_status):
        """
        Store order details in the database, including customer information.

        :param customer_id: The ID of the customer placing the order
        :param cart_items: List of items in the cart
        :param total_price: Total price of the order
        :param payment_method: Payment method ('online payment', 'cash on delivery')
        :param payment_status: 'Paid' or 'Pending'
        :return: Inserted order ID
        """

        customer = self.customers.find_one({"_id": ObjectId(customer_id)}, {"password": 0})
        if not customer:
            return None  

        order_data = {
            "customer_id": ObjectId(customer_id),
            "customer_info": {
                "name": customer.get("name"),
                "email": customer.get("email"),
                "phone": customer.get("phone"),
                "address": customer.get("address"),
            },
            "items": cart_items,  
            "total_price": total_price,
            "payment_method": payment_method,
            "payment_status": payment_status, 
            "order_date": datetime.utcnow(),
            "status": "Pending",  
        }

        result = self.orders.insert_one(order_data)
        return str(result.inserted_id) 

    def get_customer_orders(self, customer_id):
        """Retrieve all orders placed by a specific customer."""
        return list(self.orders.find({"customer_id": ObjectId(customer_id)}))

    def update_order_status(self, order_id, status):
        """Update the status of an order."""
        self.orders.update_one(
            {"_id": ObjectId(order_id)}, 
            {"$set": {"status": status, "updated_at": datetime.utcnow()}}
        )

    def get_order_by_id(self, order_id):
        """Retrieve order details by order ID."""
        return self.orders.find_one({"_id": ObjectId(order_id)})

    def delete_order(self, order_id):
        """Delete an order (if needed)."""
        self.orders.delete_one({"_id": ObjectId(order_id)})




