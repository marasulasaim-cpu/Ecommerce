# seed.py
from app import app, db, User, Inventory, Order, Payment, Purchase
from datetime import date

def seed_data():
    # --- Users ---
    u1 = User(name="Alice Johnson", email="alice@example.com", phone="9876543210")
    u2 = User(name="Bob Smith", email="bob@example.com", phone="1234567890")

    # --- Inventory ---
    i1 = Inventory(product_name="Laptop", stock_qty=15, price=1200.00)
    i2 = Inventory(product_name="Smartphone", stock_qty=30, price=699.99)

    # --- Orders ---
    o1 = Order(user=u1, order_date=date(2026, 8, 19), status="Pending")

    # --- Payments ---
    p1 = Payment(order=o1, amount=1200.00, method="Credit Card", status="Completed")

    # --- Purchases ---
    pu1 = Purchase(order=o1, item=i1, quantity=2)

    # Add everything to the session
    db.session.add_all([u1, u2, i1, i2, o1, p1, pu1])
    db.session.commit()

    print("✅ Database seeded successfully!")

if __name__ == "__main__":
    # Run inside Flask app context
    with app.app_context():
        seed_data()
