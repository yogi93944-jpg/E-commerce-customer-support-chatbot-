import os
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from database import (
    init_database, get_db, get_products, get_product, search_products,
    create_user, get_user_by_email, create_order, get_user_orders, get_all_orders,
    update_order_status, add_product, delete_product
)
from chatbot import chatbot_response

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "change-this-secret-key-before-deployment")
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

with app.app_context():
    init_database()

def current_user():
    user_id = session.get("user_id")
    if not user_id:
        return None
    db = get_db()
    return db.execute("SELECT id, name, email, is_admin FROM users WHERE id = ?", (user_id,)).fetchone()

def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("user_id"):
            flash("Please sign in first.", "warning")
            return redirect(url_for("login", next=request.path))
        return view(*args, **kwargs)
    return wrapped

def admin_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        user = current_user()
        if not user or not user["is_admin"]:
            flash("Admin access required.", "warning")
            return redirect(url_for("index"))
        return view(*args, **kwargs)
    return wrapped

@app.context_processor
def inject_globals():
    cart = session.get("cart", {})
    cart_count = sum(int(qty) for qty in cart.values())
    return {"current_user": current_user(), "cart_count": cart_count}

@app.route("/")
def index():
    query = request.args.get("q", "").strip()
    category = request.args.get("category", "").strip()
    if query:
        products = search_products(query)
    else:
        products = get_products(category=category or None)
    categories = ["Mobiles", "Laptops", "Audio", "Smart Watches", "Accessories", "Home"]
    return render_template("index.html", products=products, categories=categories,
                           selected_category=category, query=query)

@app.route("/product/<int:product_id>")
def product_detail(product_id):
    product = get_product(product_id)
    if not product:
        flash("Product not found.", "warning")
        return redirect(url_for("index"))
    return render_template("product.html", product=product)

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        if not name or not email or len(password) < 6:
            flash("Enter your name and email, and use a password with at least 6 characters.", "danger")
            return render_template("login.html", mode="register")
        if get_user_by_email(email):
            flash("That email is already registered. Please sign in.", "warning")
            return render_template("login.html", mode="register")
        create_user(name, email, generate_password_hash(password))
        user = get_user_by_email(email)
        session["user_id"] = user["id"]
        flash("Welcome to ShopBot!", "success")
        return redirect(url_for("index"))
    return render_template("login.html", mode="register")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        user = get_user_by_email(email)
        if not user or not check_password_hash(user["password_hash"], password):
            flash("Email or password is incorrect.", "danger")
            return render_template("login.html", mode="login")
        session["user_id"] = user["id"]
        flash("You are signed in.", "success")
        next_url = request.args.get("next")
        return redirect(next_url if next_url and next_url.startswith("/") else url_for("index"))
    return render_template("login.html", mode="login")

@app.route("/logout")
def logout():
    session.clear()
    flash("You have been signed out.", "success")
    return redirect(url_for("index"))

@app.route("/cart")
def cart():
    cart_items = []
    total = 0.0
    cart_data = session.get("cart", {})
    for product_id, quantity in cart_data.items():
        product = get_product(int(product_id))
        if product:
            item_total = float(product["price"]) * int(quantity)
            cart_items.append({"product": product, "quantity": int(quantity), "item_total": item_total})
            total += item_total
    return render_template("cart.html", cart_items=cart_items, total=total)

@app.route("/cart/add/<int:product_id>", methods=["POST"])
def add_to_cart(product_id):
    product = get_product(product_id)
    if not product:
        flash("Product not found.", "warning")
        return redirect(url_for("index"))
    cart_data = session.get("cart", {})
    key = str(product_id)
    cart_data[key] = min(int(cart_data.get(key, 0)) + 1, 10)
    session["cart"] = cart_data
    flash(f'{product["name"]} added to your cart.', "success")
    return redirect(request.referrer or url_for("index"))

@app.route("/cart/update", methods=["POST"])
def update_cart():
    cart_data = session.get("cart", {})
    for key in list(cart_data.keys()):
        try:
            quantity = int(request.form.get(f"qty_{key}", cart_data[key]))
        except (TypeError, ValueError):
            quantity = int(cart_data[key])
        if quantity <= 0:
            cart_data.pop(key, None)
        else:
            cart_data[key] = min(quantity, 10)
    session["cart"] = cart_data
    flash("Cart updated.", "success")
    return redirect(url_for("cart"))

@app.route("/checkout", methods=["GET", "POST"])
@login_required
def checkout():
    cart_data = session.get("cart", {})
    items = []
    total = 0.0
    for product_id, quantity in cart_data.items():
        product = get_product(int(product_id))
        if product:
            line_total = float(product["price"]) * int(quantity)
            items.append({"product": product, "quantity": int(quantity), "line_total": line_total})
            total += line_total
    if not items:
        flash("Your cart is empty.", "warning")
        return redirect(url_for("index"))
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        phone = request.form.get("phone", "").strip()
        address = request.form.get("address", "").strip()
        payment = request.form.get("payment", "Cash on Delivery")
        if not name or not phone or not address:
            flash("Please complete all delivery details.", "danger")
            return render_template("checkout.html", items=items, total=total)
        order_id = create_order(session["user_id"], items, total, name, phone, address, payment)
        session["cart"] = {}
        flash(f"Order #{order_id} placed successfully!", "success")
        return redirect(url_for("orders"))
    return render_template("checkout.html", items=items, total=total)

@app.route("/orders")
@login_required
def orders():
    return render_template("orders.html", orders=get_user_orders(session["user_id"]))

@app.route("/api/chat", methods=["POST"])
def api_chat():
    data = request.get_json(silent=True) or {}
    message = str(data.get("message", "")).strip()
    if not message:
        return jsonify({"reply": "Type a question and I’ll help you."})
    return jsonify({"reply": chatbot_response(message)})

@app.route("/admin", methods=["GET", "POST"])
@admin_required
def admin():
    if request.method == "POST":
        action = request.form.get("action")
        if action == "add":
            try:
                add_product(
                    name=request.form["name"].strip(),
                    category=request.form["category"].strip(),
                    price=float(request.form["price"]),
                    rating=float(request.form.get("rating", 4.2)),
                    discount=int(request.form.get("discount", 0)),
                    stock=int(request.form.get("stock", 10)),
                    image=request.form.get("image", "").strip() or None,
                    description=request.form.get("description", "").strip()
                )
                flash("Product added.", "success")
            except (ValueError, KeyError):
                flash("Please enter valid product details.", "danger")
        elif action == "delete":
            delete_product(int(request.form["product_id"]))
            flash("Product deleted.", "success")
        elif action == "status":
            update_order_status(int(request.form["order_id"]), request.form["status"])
            flash("Order status updated.", "success")
        return redirect(url_for("admin"))
    return render_template("admin.html", products=get_products(), orders=get_all_orders())

if __name__ == "__main__":
    # Allow devices on the same Wi-Fi to open ShopBot.
    app.run(host="0.0.0.0", port=5000, debug=False)
