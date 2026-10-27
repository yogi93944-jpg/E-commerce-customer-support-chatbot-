import os
import sqlite3
from flask import g

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ecommerce.db")

SEED_PRODUCTS = [
    ("Nova X5 Smartphone", "Mobiles", 24999, 4.6, 18, 24, "https://images.unsplash.com/photo-1598327105666-5b89351aff97?w=700", "A bright display, fast performance and all-day battery life."),
    ("PixelPro 12", "Mobiles", 32999, 4.5, 12, 18, "https://images.unsplash.com/photo-1511707171634-5f897ff02aa9?w=700", "A clean, modern smartphone for photos, apps and everyday use."),
    ("AirBook Slim 14", "Laptops", 58999, 4.7, 10, 12, "https://images.unsplash.com/photo-1496181133206-80ce9b88a853?w=700", "A lightweight laptop for work, study and entertainment."),
    ("Pro Creator Laptop", "Laptops", 82999, 4.8, 8, 8, "https://images.unsplash.com/photo-1517336714731-489689fd1ca8?w=700", "Powerful laptop for creative projects and multitasking."),
    ("Sonic Wireless Headphones", "Audio", 3999, 4.4, 20, 35, "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=700", "Comfortable wireless headphones with rich everyday sound."),
    ("BassBeat Earbuds", "Audio", 1999, 4.2, 25, 40, "https://images.unsplash.com/photo-1606220945770-b5b6c2c55bf1?w=700", "Compact earbuds for music, calls and travel."),
    ("Pulse Smart Watch", "Smart Watches", 4999, 4.3, 15, 22, "https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=700", "Track activity and keep useful notifications on your wrist."),
    ("Active Fit Watch", "Smart Watches", 6999, 4.5, 10, 16, "https://images.unsplash.com/photo-1544117519-31a4b719223d?w=700", "A sporty watch designed for everyday movement."),
    ("Mechanical Keyboard", "Accessories", 2799, 4.6, 14, 30, "https://images.unsplash.com/photo-1587829741301-dc798b83add3?w=700", "A satisfying keyboard for typing, studying and gaming."),
    ("Ergo Wireless Mouse", "Accessories", 999, 4.1, 10, 50, "https://images.unsplash.com/photo-1527814050087-3793815479db?w=700", "A comfortable wireless mouse for desk setups."),
    ("Smart Home Speaker", "Home", 3499, 4.3, 12, 20, "https://images.unsplash.com/photo-1589003077984-894e133dabab?w=700", "A compact speaker for podcasts, music and home listening."),
    ("HD Webcam", "Accessories", 2299, 4.2, 16, 28, "https://images.unsplash.com/photo-1587826080692-f439cd0b70da?w=700", "A simple webcam for online classes and video meetings.")
]

def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db

def close_db(_error=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()

def init_database():
    db = sqlite3.connect(DB_PATH)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys = ON")
    db.executescript("""
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        category TEXT NOT NULL,
        price REAL NOT NULL,
        rating REAL NOT NULL DEFAULT 4.2,
        discount INTEGER NOT NULL DEFAULT 0,
        stock INTEGER NOT NULL DEFAULT 10,
        image TEXT,
        description TEXT DEFAULT ''
    );
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        is_admin INTEGER NOT NULL DEFAULT 0
    );
    CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        items_json TEXT NOT NULL,
        total REAL NOT NULL,
        customer_name TEXT NOT NULL,
        phone TEXT NOT NULL,
        address TEXT NOT NULL,
        payment TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'Processing',
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(user_id) REFERENCES users(id)
    );
    """)
    count = db.execute("SELECT COUNT(*) FROM products").fetchone()[0]
    if count == 0:
        db.executemany("""INSERT INTO products
            (name, category, price, rating, discount, stock, image, description)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)""", SEED_PRODUCTS)
    # Demo admin account: admin@shopbot.local / Admin123!
    admin = db.execute("SELECT id FROM users WHERE email = ?", ("admin@shopbot.local",)).fetchone()
    if not admin:
        from werkzeug.security import generate_password_hash
        db.execute("INSERT INTO users(name,email,password_hash,is_admin) VALUES(?,?,?,1)",
                   ("ShopBot Admin", "admin@shopbot.local", generate_password_hash("Admin123!")))
    db.commit()
    db.close()

def get_products(category=None):
    db = get_db()
    if category:
        return db.execute("SELECT * FROM products WHERE category = ? ORDER BY id DESC", (category,)).fetchall()
    return db.execute("SELECT * FROM products ORDER BY id DESC").fetchall()

def search_products(query):
    db = get_db()
    term = f"%{query}%"
    return db.execute("SELECT * FROM products WHERE name LIKE ? OR category LIKE ? OR description LIKE ? ORDER BY id DESC",
                      (term, term, term)).fetchall()

def get_product(product_id):
    return get_db().execute("SELECT * FROM products WHERE id = ?", (product_id,)).fetchone()

def create_user(name, email, password_hash):
    db = get_db()
    db.execute("INSERT INTO users(name,email,password_hash) VALUES(?,?,?)", (name, email, password_hash))
    db.commit()

def get_user_by_email(email):
    return get_db().execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()

def create_order(user_id, items, total, customer_name, phone, address, payment):
    import json
    summary = [{"id": item["product"]["id"], "name": item["product"]["name"],
                "quantity": item["quantity"], "price": float(item["product"]["price"])} for item in items]
    db = get_db()
    cur = db.execute("""INSERT INTO orders(user_id,items_json,total,customer_name,phone,address,payment)
                        VALUES(?,?,?,?,?,?,?)""",
                     (user_id, json.dumps(summary), total, customer_name, phone, address, payment))
    db.commit()
    return cur.lastrowid

def get_user_orders(user_id):
    import json
    rows = get_db().execute("SELECT * FROM orders WHERE user_id = ? ORDER BY id DESC", (user_id,)).fetchall()
    return [dict(row, items=json.loads(row["items_json"])) for row in rows]

def get_all_orders():
    import json
    rows = get_db().execute("""SELECT orders.*, users.email AS user_email
                               FROM orders JOIN users ON users.id=orders.user_id ORDER BY orders.id DESC""").fetchall()
    return [dict(row, items=json.loads(row["items_json"])) for row in rows]

def update_order_status(order_id, status):
    allowed = {"Processing", "Shipped", "Delivered", "Cancelled"}
    if status not in allowed:
        return
    db = get_db()
    db.execute("UPDATE orders SET status = ? WHERE id = ?", (status, order_id))
    db.commit()

def add_product(name, category, price, rating, discount, stock, image, description):
    db = get_db()
    db.execute("""INSERT INTO products(name,category,price,rating,discount,stock,image,description)
                  VALUES(?,?,?,?,?,?,?,?)""",
               (name, category, price, rating, discount, stock, image, description))
    db.commit()

def delete_product(product_id):
    db = get_db()
    db.execute("DELETE FROM products WHERE id = ?", (product_id,))
    db.commit()
