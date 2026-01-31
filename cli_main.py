# ========= SMART CANTEEN MANAGEMENT SYSTEM (FINAL + ROBUST PAYMENT) =========

import sqlite3
import datetime
import random
import os

# ---------------- DB PATH ----------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "canteen.db")

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

# ---------------- DB INIT ----------------
def init_db():
    cur.execute("""
    CREATE TABLE IF NOT EXISTS menu(
        id INTEGER PRIMARY KEY,
        name TEXT,
        price INTEGER
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS orders(
        order_id INTEGER PRIMARY KEY,
        customer TEXT,
        mobile TEXT,
        date TEXT,
        subtotal REAL,
        discount REAL,
        gst REAL,
        parcel REAL,
        grand REAL,
        payment TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS order_items(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_id INTEGER,
        item_name TEXT,
        price INTEGER,
        quantity INTEGER
    )
    """)

    cur.execute("SELECT COUNT(*) FROM menu")
    if cur.fetchone()[0] == 0:
        items = [
            (1, "Burger", 50),
            (2, "Pizza", 120),
            (3, "Sandwich", 40),
            (4, "Cold Drink", 30),
            (5, "Coffee", 25)
        ]
        cur.executemany("INSERT INTO menu VALUES (?,?,?)", items)

    conn.commit()

# ---------------- GLOBALS ----------------
cart = []
last_bill = None

# ---------------- MENU ----------------
def display_menu():
    print("\n------ CANTEEN MENU ------")
    print("ID\tItem\t\tPrice")
    cur.execute("SELECT * FROM menu")
    for r in cur.fetchall():
        print(r[0], "\t", r[1].ljust(12), r[2])

# ---------------- CART ----------------
def show_cart():
    if not cart:
        print("\n Cart is empty!")
        return

    subtotal = 0
    print("\nItem\t\tPrice Qty Total")
    for i in cart:
        t = i[1] * i[2]
        subtotal += t
        print(i[0].ljust(12), i[1], i[2], t)
    print("Subtotal:", subtotal)
    gst = subtotal * 0.05
    print("GST (5%):", gst)

def add_multiple_items():
    while True:
        try:
            item_id = int(input("Enter item ID: "))
            cur.execute("SELECT name, price FROM menu WHERE id=?", (item_id,))
            item = cur.fetchone()

            if not item:
                print("❌ Invalid item ID")
                continue

            qty = int(input("Enter quantity: "))
            if qty <= 0:
                print("❌ Invalid quantity")
                continue

            cart.append([item[0], item[1], qty])
            print("✅ Item added")

        except:
            print("❌ Invalid input")

        if input("Add more items? (y/n): ").lower() != 'y':
            break

def remove_item_quantity():
    if not cart:
        print("❌ Cart empty")
        return

    show_cart()
    name = input("Enter item name: ").lower()
    qty = int(input("Qty to remove: "))

    for item in cart:
        if item[0].lower() == name:
            if qty >= item[2]:
                cart.remove(item)
            else:
                item[2] -= qty
            print("✅ Cart updated")
            return

    print("❌ Item not found")

# ---------------- PAYMENT (ROBUST) ----------------
def payment_method(amount, order_id):
    while True:
        print("\n====== PAYMENT ======")
        print(f"Amount to Pay: {amount}")
        print("1. Cash")
        print("2. Online")

        ch = input("Choose option: ")

        # ---- CASH ----
        if ch == "1":
            while True:
                try:
                    cash = float(input("Enter cash given: "))

                    if cash < amount:
                        print(f"❌ Insufficient cash! Need {amount - cash} more.")
                    else:
                        change = cash - amount
                        print("\n💵 Payment Summary")
                        print("Cash Given :", cash)
                        print("Amount Due :", amount)
                        print("Change     :", change)
                        return "Cash", change

                except ValueError:
                    print("❌ Enter valid amount!")

        # ---- ONLINE ----
        elif ch == "2":
            print(f"""
    =================================
        SCAN & PAY via UPI
    =================================
        UPI ID   : canteen@upi
        AMOUNT   : ₹{amount}
        ORDER ID : {order_id}
    =================================
       [ QR CODE DISPLAY PLACEHOLDER ]
       
       █▀▀▀▀▀█ ▀▀▀▀▀ █▀▀▀▀▀█
       █ ███ █ ▀▀▀▀▀ █ ███ █
       █ ▀▀▀ █ ▄▄▄▄▄ █ ▀▀▀ █
       ▀▀▀▀▀▀▀ ▀ ▀ ▀ ▀▀▀▀▀▀▀
    =================================
            """)
            input("Press Enter after payment is done...")
            print("✅ Payment Received via UPI!")
            return "Online", 0



        else:
            print("❌ Invalid choice")

# ---------------- BILL ----------------
def generate_bill():
    global last_bill

    if not cart:
        print("❌ Cart empty")
        return

    while True:
        name = input("Customer Name: ")
        if name.replace(" ", "").isalpha():
            break
        print("❌ Invalid name. Please use characters only.")
    while True:
        try:
            mobile = input("Mobile: ")
            if not mobile:
                raise ValueError("Mobile number is required")
            if len(mobile) != 10:
                raise ValueError("Mobile number must be exactly 10 digits")
            if not mobile.isdigit():
                raise ValueError("Mobile number must contain digits only")
            break
        except ValueError as e:
            print(f"❌ {e}")

    order_id = random.randint(1000, 9999)
    date = datetime.datetime.now().strftime("%d-%m-%Y %H:%M")

    subtotal = sum(i[1] * i[2] for i in cart)
    discount = subtotal * 0.10 if subtotal >= 499 else 0
    parcel = 20 if input("Food Parcel? (yes/no): ").lower() == "yes" else 0
    gst = subtotal * 0.05
    grand = subtotal + gst + parcel - discount

    payment, change = payment_method(grand, order_id)

    if payment is None:
        print("❌ Bill generation aborted")
        return

    # SAVE ORDER
    cur.execute("""
    INSERT INTO orders VALUES (?,?,?,?,?,?,?,?,?,?)
    """, (order_id, name, mobile, date, subtotal, discount, gst, parcel, grand, payment))

    # SAVE ITEMS
    for i in cart:
        cur.execute("""
        INSERT INTO order_items(order_id,item_name,price,quantity)
        VALUES (?,?,?,?)
        """, (order_id, i[0], i[1], i[2]))

    conn.commit()

    last_bill = {
        "order_id": order_id,
        "grand": grand,
        "payment": payment,
        "change": change
    }

    print("\n========= FINAL BILL =========")
    print("Order ID     :", order_id)
    print("GST (5%)     :", gst)
    print("Grand Total  :", grand)
    print("Payment Mode :", payment)
    if payment == "Cash":
        print("Change Given :", change)
    print("==============================")

    cart.clear()

# ---------------- REVENUE ----------------
def show_revenue():
    cur.execute("SELECT SUM(grand) FROM orders")
    r = cur.fetchone()[0]
    print("\n Total Revenue:", r if r else 0)

# ---------------- HISTORY ----------------
def search_order_history():
    print("\n------ ORDER HISTORY SEARCH ------")
    mobile = input("Enter Customer Mobile Number: ")

    cur.execute("SELECT * FROM orders WHERE mobile=?", (mobile,))
    orders = cur.fetchall()

    if not orders:
        print("❌ No orders found for this mobile number.")
        return

    print(f"\nOrders for Mobile: {mobile}")
    print("Order ID\tDate\t\tAmount")
    for o in orders:
        # o[0] is order_id, o[3] is date, o[8] is grand
        print(f"{o[0]}\t\t{o[3]}\t{o[8]}")

# ---------------- MAIN ----------------
def main():
    init_db()

    while True:
        print("\n1.Menu\n2.Add Items\n3.Remove Item\n4.Show Cart")
        print("5.Generate Bill\n6.Show Revenue\n7.Search Order History\n8.Exit")

        ch = input("Choice: ")

        if ch == "1":
            display_menu()
        elif ch == "2":
            display_menu()
            add_multiple_items()
        elif ch == "3":
            remove_item_quantity()
        elif ch == "4":
            show_cart()
        elif ch == "5":
            generate_bill()
        elif ch == "6":
            show_revenue()
        elif ch == "7":
            search_order_history()
        elif ch == "8":
            print("Thank you! 😊")
            break
        else:
            print("❌ Invalid choice")

main()