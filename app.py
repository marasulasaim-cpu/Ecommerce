import os
from dotenv import load_dotenv
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from sqlalchemy.exc import IntegrityError
from datetime import datetime

# --- App Setup ---
app = Flask(__name__)
load_dotenv()

# PostgreSQL connection from .env
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')

db = SQLAlchemy(app)
migrate = Migrate(app, db)

# --- Models ---
class User(db.Model):
    __tablename__ = 'users'
    user_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    phone = db.Column(db.String(15))

    orders = db.relationship('Order', backref='user', cascade="all, delete-orphan")

class Inventory(db.Model):
    __tablename__ = 'inventory'
    item_id = db.Column(db.Integer, primary_key=True)
    product_name = db.Column(db.String(100), nullable=False)
    stock_qty = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False)

    purchases = db.relationship('Purchase', backref='item', cascade="all, delete-orphan")

class Order(db.Model):
    __tablename__ = 'orders'
    order_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id', ondelete="CASCADE"), nullable=False)
    order_date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(50), nullable=False)

    payments = db.relationship('Payment', backref='order', cascade="all, delete-orphan")
    purchases = db.relationship('Purchase', backref='order', cascade="all, delete-orphan")

class Payment(db.Model):
    __tablename__ = 'payments'
    payment_id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.order_id', ondelete="CASCADE"), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    method = db.Column(db.String(50), nullable=False)
    status = db.Column(db.String(50), nullable=False)

class Purchase(db.Model):
    __tablename__ = 'purchases'
    purchase_id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.order_id', ondelete="CASCADE"), nullable=False)
    item_id = db.Column(db.Integer, db.ForeignKey('inventory.item_id', ondelete="CASCADE"), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)

# --- Helper: Safe Commit ---
def safe_commit():
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "Integrity error (duplicate or invalid data)"}), 409
    return None

# --- Routes (Users, Inventory, Orders, Payments, Purchases) ---
# --- Users CRUD ---
@app.route('/users', methods=['POST'])
def create_user():
    data = request.get_json()
    new_user = User(name=data['name'], email=data['email'], phone=data.get('phone'))
    db.session.add(new_user)
    err = safe_commit()
    if err: return err
    return jsonify({"id": new_user.user_id}), 201

@app.route('/users', methods=['GET'])
def get_users():
    users = User.query.all()
    return jsonify([{"id": u.user_id, "name": u.name, "email": u.email, "phone": u.phone} for u in users])

@app.route('/users/<int:id>', methods=['PATCH'])
def update_user(id):
    user = User.query.get_or_404(id)
    data = request.get_json()
    user.name = data.get('name', user.name)
    user.email = data.get('email', user.email)
    user.phone = data.get('phone', user.phone)
    err = safe_commit()
    if err: return err
    return jsonify({"message": "User updated"})

@app.route('/users/<int:id>', methods=['DELETE'])
def delete_user(id):
    user = User.query.get_or_404(id)
    db.session.delete(user)
    err = safe_commit()
    if err: return err
    return '', 204

#--- Inventory CRUD ---
@app.route('/inventory', methods=['POST'])
def create_item():
    data = request.get_json()
    new_item = Inventory(product_name=data['product_name'], stock_qty=data['stock_qty'], price=data['price'])
    db.session.add(new_item)
    err = safe_commit()
    if err: return err
    return jsonify({"id": new_item.item_id}), 201

@app.route('/inventory/<int:item_id>', methods=['GET'])
def get_item(item_id):
    item = Inventory.query.get_or_404(item_id)
    return jsonify({"item_id": item.item_id, "product_name": item.product_name, "stock_qty": item.stock_qty, "price": item.price})

@app.route('/inventory/<int:item_id>', methods=['PATCH'])
def update_item(item_id):
    item = Inventory.query.get_or_404(item_id)
    data = request.get_json()
    item.product_name = data.get('product_name', item.product_name)
    item.stock_qty = data.get('stock_qty', item.stock_qty)
    item.price = data.get('price', item.price)
    err = safe_commit()
    if err: return err
    return jsonify({"message": "Item updated"})

@app.route('/inventory/<int:item_id>', methods=['DELETE'])
def delete_item(item_id):
    item = Inventory.query.get_or_404(item_id)
    db.session.delete(item)
    err = safe_commit()
    if err: return err
    return '', 204

@app.route('/inventory', methods=['GET'])
def get_inventory():
    items = Inventory.query.all()
    return jsonify([
        {
            "item_id": i.item_id,
            "product_name": i.product_name,
            "stock_qty": i.stock_qty,
            "price": i.price
        } for i in items
    ])


@app.route('/orders', methods=['POST'])
def create_order():
    data = request.get_json()
    new_order = Order(
        user_id=data['user_id'],
        order_date=datetime.strptime(data['order_date'], "%Y-%m-%d").date(),
        status=data['status']
    )
    db.session.add(new_order)
    err = safe_commit()
    if err: return err
    return jsonify({"id": new_order.order_id}), 201

@app.route('/orders/<int:order_id>', methods=['GET'])
def get_order(order_id):
    order = Order.query.get_or_404(order_id)
    return jsonify({"order_id": order.order_id, "user_id": order.user_id, "order_date": str(order.order_date), "status": order.status})

@app.route('/orders/<int:order_id>', methods=['PATCH'])
def update_order(order_id):
    order = Order.query.get_or_404(order_id)
    data = request.get_json()
    order.status = data.get('status', order.status)
    err = safe_commit()
    if err: return err
    return jsonify({"message": "Order updated"})

@app.route('/orders/<int:order_id>', methods=['DELETE'])
def delete_order(order_id):
    order = Order.query.get_or_404(order_id)
    db.session.delete(order)
    err = safe_commit()
    if err: return err
    return '', 204

@app.route('/orders', methods=['GET'])
def get_orders():
    orders = Order.query.all()
    return jsonify([
        {
            "order_id": o.order_id,
            "user_id": o.user_id,
            "order_date": str(o.order_date),
            "status": o.status
        } for o in orders
    ])

# --- Payments CRUD ---
@app.route('/payments', methods=['POST'])
def create_payment():
    data = request.get_json()
    new_payment = Payment(order_id=data['order_id'], amount=data['amount'], method=data['method'], status=data['status'])
    db.session.add(new_payment)
    err = safe_commit()
    if err: return err
    return jsonify({"id": new_payment.payment_id}), 201

@app.route('/payments/<int:payment_id>', methods=['GET'])
def get_payment(payment_id):
    payment = Payment.query.get_or_404(payment_id)
    return jsonify({"payment_id": payment.payment_id, "order_id": payment.order_id, "amount": payment.amount, "method": payment.method, "status": payment.status})

@app.route('/payments/<int:payment_id>', methods=['PATCH'])
def update_payment(payment_id):
    payment = Payment.query.get_or_404(payment_id)
    data = request.get_json()
    payment.status = data.get('status', payment.status)
    err = safe_commit()
    if err: return err
    return jsonify({"message": "Payment updated"})

@app.route('/payments/<int:payment_id>', methods=['DELETE'])
def delete_payment(payment_id):
    payment = Payment.query.get_or_404(payment_id)
    db.session.delete(payment)
    err = safe_commit()
    if err: return err
    return '', 204

@app.route('/payments', methods=['GET'])
def get_payments():
    payments = Payment.query.all()
    return jsonify([
        {
            "payment_id": p.payment_id,
            "order_id": p.order_id,
            "amount": p.amount,
            "method": p.method,
            "status": p.status
        } for p in payments
    ])

# --- Purchases CRUD ---
@app.route('/purchases', methods=['POST'])
def create_purchase():
    data = request.get_json()
    new_purchase = Purchase(order_id=data['order_id'], item_id=data['item_id'], quantity=data['quantity'])
    db.session.add(new_purchase)
    err = safe_commit()
    if err: return err
    return jsonify({"id": new_purchase.purchase_id}), 201

@app.route('/purchases/<int:purchase_id>', methods=['GET'])
def get_purchase(purchase_id):
    purchase = Purchase.query.get_or_404(purchase_id)
    return jsonify({"purchase_id": purchase.purchase_id, "order_id": purchase.order_id, "item_id": purchase.item_id, "quantity": purchase.quantity})

@app.route('/purchases/<int:purchase_id>', methods=['PATCH'])
def update_purchase(purchase_id):
    purchase = Purchase.query.get_or_404(purchase_id)
    data = request.get_json()
    purchase.quantity = data.get('quantity', purchase.quantity)
    err = safe_commit()
    if err: return err
    return jsonify({"message": "Purchase updated"})

@app.route('/purchases/<int:purchase_id>', methods=['DELETE'])
def delete_purchase(purchase_id):
    purchase = Purchase.query.get_or_404(purchase_id)
    db.session.delete(purchase)
    err = safe_commit()
    if err: return err
    return '', 204

@app.route('/purchases', methods=['GET'])
def get_purchases():
    purchases = Purchase.query.all()
    return jsonify([
        {
            "purchase_id": pu.purchase_id,
            "order_id": pu.order_id,
            "item_id": pu.item_id,
            "quantity": pu.quantity
        } for pu in purchases
    ])

# --- Run App ---
if __name__ == "__main__":
    app.run(debug=True)
