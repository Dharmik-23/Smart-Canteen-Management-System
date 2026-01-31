import sqlite3
import hashlib
import os
import datetime

# Database Path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "canteen.db")

def get_connection():
    return sqlite3.connect(DB_PATH, check_same_thread=False)

def init_db():
    conn = get_connection()
    c = conn.cursor()

    # --- USERS TABLE ---
    c.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        role TEXT NOT NULL, -- 'admin', 'staff', 'student'
        name TEXT,
        mobile TEXT
    )
    """)

    # --- MENU TABLE ---
    # Upgrading existing menu or creating new
    c.execute("""
    CREATE TABLE IF NOT EXISTS menu (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        price REAL NOT NULL,
        stock INTEGER DEFAULT 0,
        category TEXT DEFAULT 'General',
        description TEXT,
        image_url TEXT
    )
    """)
    
    # --- ROBUST MIGRATION ---
    # Get current columns to ensure we don't error out or miss inconsistent states
    c.execute("PRAGMA table_info(menu)")
    existing_cols = [row[1] for row in c.fetchall()]
    
    # Expected columns and their definitions (excluding core ones likely to exist)
    required_cols = {
        "stock": "INTEGER DEFAULT 0",
        "category": "TEXT DEFAULT 'General'",
        "description": "TEXT",
        "image_url": "TEXT"
    }

    for col, definition in required_cols.items():
        if col not in existing_cols:
            try:
                c.execute(f"ALTER TABLE menu ADD COLUMN {col} {definition}")
            except sqlite3.OperationalError:
                pass # Already exists

    # --- SEED DATA ---
    c.execute("SELECT COUNT(*) FROM menu")
    if c.fetchone()[0] == 0:
        seed_items = [
            ("Veg Burger", 50.0, 100, "Snacks", "Crispy veg patty with fresh veggies", ""),
            ("Margherita Pizza", 120.0, 50, "Main Course", "Classic cheese and tomato pizza", ""),
            ("Cold Coffee", 40.0, 80, "Beverages", "Chilled coffee with chocolate topping", ""),
            ("French Fries", 60.0, 150, "Snacks", "Salted crispy fries", "")
        ]
        c.executemany("INSERT INTO menu (name, price, stock, category, description, image_url) VALUES (?, ?, ?, ?, ?, ?)", seed_items)


    # --- ORDERS TABLE ---
    c.execute("""
    CREATE TABLE IF NOT EXISTS orders (
        order_id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        customer_name TEXT,
        mobile TEXT,
        order_date DATETIME,
        total_amount REAL,
        status TEXT DEFAULT 'Received', -- Received, Preparing, Ready, Completed, Cancelled
        payment_method TEXT,
        qr_code TEXT,
        FOREIGN KEY(user_id) REFERENCES users(id)
    )
    """)
    
    # Check for migration for status column if table exists without it
    # --- ROBUST ORDER MIGRATION ---
    c.execute("PRAGMA table_info(orders)")
    existing_order_cols = [row[1] for row in c.fetchall()]
    
    required_order_cols = {
        "status": "TEXT DEFAULT 'Received'",
        "qr_code": "TEXT"
    }

    for col, definition in required_order_cols.items():
        if col not in existing_order_cols:
             try:
                c.execute(f"ALTER TABLE orders ADD COLUMN {col} {definition}")
             except:
                 pass

    # --- ORDER ITEMS TABLE ---
    c.execute("""
    CREATE TABLE IF NOT EXISTS order_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_id INTEGER,
        item_name TEXT,
        price REAL,
        quantity INTEGER,
        FOREIGN KEY(order_id) REFERENCES orders(order_id)
    )
    """)

    # --- FEEDBACK TABLE ---
    c.execute("""
    CREATE TABLE IF NOT EXISTS feedback (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        order_id INTEGER,
        rating INTEGER,
        comment TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # Create default admin if not exists
    c.execute("SELECT * FROM users WHERE role='admin'")
    if not c.fetchone():
        # Default Admin: admin / admin123
        pwd_hash = hashlib.sha256("admin123".encode()).hexdigest()
        c.execute("INSERT INTO users (username, password, role, name, mobile) VALUES (?, ?, ?, ?, ?)", 
                  ("admin", pwd_hash, "admin", "System Admin", "0000000000"))

    conn.commit()
    conn.close()

# --- AUTH FUNCTIONS ---
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def signup_user(username, password, role, name, mobile):
    conn = get_connection()
    c = conn.cursor()
    try:
        c.execute("INSERT INTO users (username, password, role, name, mobile) VALUES (?, ?, ?, ?, ?)",
                  (username, hash_password(password), role, name, mobile))
        conn.commit()
        return True, "User registered successfully!"
    except sqlite3.IntegrityError:
        return False, "Username already exists."
    finally:
        conn.close()

def login_user(username, password):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT id, username, role, name FROM users WHERE username=? AND password=?", 
              (username, hash_password(password)))
    user = c.fetchone()
    conn.close()
    return user

# --- MENU FUNCTIONS ---
def get_menu_items():
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM menu")
    items = c.fetchall()
    conn.close()
    return items # List of tuples

def add_menu_item(name, price, stock, category, description):
    conn = get_connection()
    c = conn.cursor()
    c.execute("INSERT INTO menu (name, price, stock, category, description) VALUES (?, ?, ?, ?, ?)",
              (name, price, stock, category, description))
    conn.commit()
    conn.close()

def update_stock(item_id, quantity):
    conn = get_connection()
    c = conn.cursor()
    c.execute("UPDATE menu SET stock = stock - ? WHERE id = ?", (quantity, item_id))
    conn.commit()
    conn.close()

def update_menu_stock_direct(item_id, new_stock):
    conn = get_connection()
    c = conn.cursor()
    c.execute("UPDATE menu SET stock = ? WHERE id = ?", (new_stock, item_id))
    conn.commit()
    conn.close()

# --- ORDER FUNCTIONS ---
def place_order(user_id, name, mobile, cart_items, total_amount, payment_method, qr_data):
    conn = get_connection()
    c = conn.cursor()
    date_now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    c.execute("INSERT INTO orders (user_id, customer_name, mobile, order_date, total_amount, status, payment_method, qr_code) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
              (user_id, name, mobile, date_now, total_amount, "Received", payment_method, qr_data))
    order_id = c.lastrowid
    
    for item in cart_items:
        # item: {'id': 1, 'name': 'Burger', 'price': 50, 'qty': 2}
        c.execute("INSERT INTO order_items (order_id, item_name, price, quantity) VALUES (?, ?, ?, ?)",
                  (order_id, item['name'], item['price'], item['qty']))
        
        # Deduct stock
        c.execute("UPDATE menu SET stock = stock - ? WHERE id = ?", (item['qty'], item['id']))
        
    conn.commit()
    conn.close()
    return order_id

def get_orders(user_id=None, role="student"):
    conn = get_connection()
    c = conn.cursor()
    if role == "admin" or role == "staff":
        c.execute("SELECT * FROM orders ORDER BY order_id DESC")
    else:
        c.execute("SELECT * FROM orders WHERE user_id=? ORDER BY order_id DESC", (user_id,))
    rows = c.fetchall()
    conn.close()
    return rows

def update_order_status(order_id, new_status):
    conn = get_connection()
    c = conn.cursor()
    c.execute("UPDATE orders SET status = ? WHERE order_id = ?", (new_status, order_id))
    conn.commit()
    conn.close()

def get_order_items(order_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM order_items WHERE order_id=?", (order_id,))
    rows = c.fetchall()
    conn.close()
    return rows

# --- FEEDBACK ---
def submit_feedback(user_id, order_id, rating, comment):
    conn = get_connection()
    c = conn.cursor()
    c.execute("INSERT INTO feedback (user_id, order_id, rating, comment) VALUES (?, ?, ?, ?)",
              (user_id, order_id, rating, comment))
    conn.commit()
    conn.close()

def has_feedback(order_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT 1 FROM feedback WHERE order_id = ?", (order_id,))
    result = c.fetchone()
    conn.close()
    return result is not None

def get_feedbacks():
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT f.id, u.username, f.order_id, f.rating, f.comment, f.created_at FROM feedback f JOIN users u ON f.user_id = u.id ORDER BY f.created_at DESC")
    rows = c.fetchall()
    conn.close()
    return rows

# --- ANALYTICS ---

def get_revenue_stats():
    conn = get_connection()
    # Total revenue
    # Top selling items
    params = {}
    
    df_orders = "SELECT * FROM orders"
    df_items = "SELECT * FROM order_items"
    
    conn.close()
    return None # Will use pandas in main.py for easier analysis
