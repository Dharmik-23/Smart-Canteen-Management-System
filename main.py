import streamlit as st
import pandas as pd
import database as db
import time
import qrcode
from PIL import Image
from io import BytesIO

# --- CONFIGURATION ---
st.set_page_config(
    page_title="Smart Canteen System",
    page_icon="🍔",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CUSTOM CSS ---
st.markdown("""
<style>
    .stButton>button {
        width: 100%;
        border-radius: 10px;
        height: 3em;
        font-weight: bold;
    }
    .main-header {
        font-size: 2.5rem;
        color: #FF4B4B;
        text-align: center;
        font-weight: 700;
        margin-bottom: 2rem;
    }
    .sub-header {
        font-size: 1.5rem;
        color: #333;
        margin-bottom: 1rem;
    }
    .card {
        padding: 1.5rem;
        border-radius: 10px;
        background-color: #f0f2f6;
        margin-bottom: 1rem;
    }
    .price-tag {
        font-size: 1.2rem;
        font-weight: bold;
        color: #2e7d32;
    }
</style>
""", unsafe_allow_html=True)

# --- INITIALIZATION ---
if 'db_initialized' not in st.session_state:
    db.init_db()
    st.session_state['db_initialized'] = True

if 'user' not in st.session_state:
    st.session_state['user'] = None

if 'cart' not in st.session_state:
    st.session_state['cart'] = []

# --- HELPER FUNCTIONS ---
def format_currency(amount):
    return f"₹{amount:.2f}"

def add_to_cart(item):
    # Check if item already in cart
    for cart_item in st.session_state['cart']:
        if cart_item['id'] == item[0]:
            cart_item['qty'] += 1
            st.toast(f"Added another {item[1]} to cart!")
            return
            
    # Add new item
    st.session_state['cart'].append({
        'id': item[0],
        'name': item[1],
        'price': item[2],
        'qty': 1
    })
    st.toast(f"{item[1]} added to cart!")

def generate_qr_code(data):
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    return img

# --- PAGES ---

def login_page():
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        st.markdown("<div class='main-header'>Smart Canteen Login</div>", unsafe_allow_html=True)
        
        tab1, tab2 = st.tabs(["Login", "Sign Up"])
        
        with tab1:
            with st.form("login_form"):
                username = st.text_input("Username")
                password = st.text_input("Password", type="password")
                submit = st.form_submit_button("Login")
                
                if submit:
                    user = db.login_user(username, password)
                    if user:
                        # user structure: (id, username, role, name)
                        st.session_state['user'] = {
                            'id': user[0],
                            'username': user[1],
                            'role': user[2],
                            'name': user[3]
                        }
                        st.success(f"Welcome back, {user[3]}!")
                        st.rerun()
                    else:
                        st.error("Invalid username or password")
        
        with tab2:
            with st.form("signup_form"):
                new_user = st.text_input("Username")
                new_pass = st.text_input("Password", type="password")
                full_name = st.text_input("Full Name")
                mobile = st.text_input("Mobile Number")
                # Role selection (hidden for students usually, but keeping open for demo)
                role = st.selectbox("Role", ["student", "staff", "admin"])
                
                signup_submit = st.form_submit_button("Sign Up")
                
                if signup_submit:
                    if new_user and new_pass:
                        success, msg = db.signup_user(new_user, new_pass, role, full_name, mobile)
                        if success:
                            st.success(msg)
                        else:
                            st.error(msg)
                    else:
                        st.warning("Please fill all fields")

def student_dashboard():
    st.sidebar.title(f"Welcome, {st.session_state['user']['name']}")
    
    # --- FEEDBACK POPUP LOGIC ---
    # Check if there are any completed orders without feedback
    my_orders = db.get_orders(st.session_state['user']['id'], "student")
    pending_feedbacks = [o for o in my_orders if o[6] == "Completed" and not db.has_feedback(o[0])]
    
    if pending_feedbacks:
        order_to_rate = pending_feedbacks[0] # Take the most recent one
        with st.container():
            st.info(f"🌟 Order #{order_to_rate[0]} is Completed! How was your food?")
            with st.expander("Rate your Meal Now", expanded=True):
                 with st.form(f"feedback_form_{order_to_rate[0]}"):
                    rating = st.slider("Rate (1-5)", 1, 5, 5)
                    comment = st.text_area("Any comments?")
                    if st.form_submit_button("Submit Feedback"):
                        db.submit_feedback(st.session_state['user']['id'], order_to_rate[0], rating, comment)
                        st.success("Thank you for your feedback!")
                        time.sleep(1)
                        st.rerun()

    menu = st.sidebar.radio("Navigation", ["Menu", "My Cart", "My Orders", "Logout"])
    
    if menu == "Logout":
        st.session_state['user'] = None
        st.session_state['cart'] = []
        st.rerun()
        
    elif menu == "Menu":
        st.markdown("<div class='main-header'>🍔 Canteen Menu</div>", unsafe_allow_html=True)
        
        items = db.get_menu_items()
        
        # Grid layout for menu
        
        cols = st.columns(3)
        for idx, item in enumerate(items):
            # item: (id, name, price, stock, category, desc, img)
            with cols[idx % 3]:
                with st.container(border=True):
                    st.subheader(item[1])
                    st.markdown(f"**Category:** {item[4]}")
                    if item[5]:
                        st.caption(item[5])
                    st.markdown(f"<div class='price-tag'>{format_currency(item[2])}</div>", unsafe_allow_html=True)
                    
                    if item[3] > 0:
                        st.write(f"In Stock: {item[3]}")
                        if st.button(f"Add {item[1]}", key=f"add_{item[0]}"):
                            add_to_cart(item)
                    else:
                        st.error("Out of Stock")

    elif menu == "My Cart":
        st.markdown("<div class='main-header'>🛒 Your Cart</div>", unsafe_allow_html=True)
        
        if not st.session_state['cart']:
            st.info("Your cart is empty. Go to Menu to add items.")
        else:
            total = 0
            for idx, item in enumerate(st.session_state['cart']):
                col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
                with col1:
                    st.write(f"**{item['name']}**")
                with col2:
                    st.write(format_currency(item['price']))
                with col3:
                    item['qty'] = st.number_input("Qty", min_value=1, value=item['qty'], key=f"qty_{idx}")
                with col4:
                    if st.button("🗑️", key=f"del_{idx}"):
                        st.session_state['cart'].pop(idx)
                        st.rerun()
                
                total += item['price'] * item['qty']
            
            st.divider()
            st.markdown(f"### Total: {format_currency(total)}")
            
            # Payment Section
            st.subheader("Checkout")
            payment_method = st.radio("Payment Method", ["Cash", "UPI/QR Code"])
            
            if payment_method == "UPI/QR Code":
                qr_data = f"upi://pay?pa=canteen@upi&pn=SmartCanteen&am={total}&cu=INR"
                img = generate_qr_code(qr_data)
                
                buf = BytesIO()
                img.save(buf)
                st.image(buf, caption="Scan to Pay", width=200)
            else:
                qr_data = "CASH"

            if st.button("Place Order", type="primary"):
                order_id = db.place_order(
                    st.session_state['user']['id'],
                    st.session_state['user']['name'],
                    "0000000000", # TODO: Store mobile in session
                    st.session_state['cart'],
                    total,
                    payment_method,
                    qr_data
                )
                st.success(f"Order Placed Successfully! Order ID: #{order_id}")
                st.session_state['cart'] = []
                st.balloons()
                time.sleep(2)
                st.rerun()

    elif menu == "My Orders":
        st.markdown("<div class='main-header'>📜 Order History</div>", unsafe_allow_html=True)
        orders = db.get_orders(st.session_state['user']['id'], "student")
        
        for order in orders:
            # order: (id, user_id, name, mobile, date, total, status, payment, qr)
            with st.expander(f"Order #{order[0]} - {order[4]} ({order[6]})"):
                st.write(f"**Date:** {order[4]}")
                st.write(f"**Total:** {format_currency(order[5])}")
                st.write(f"**Status:** {order[6]}")
                items = db.get_order_items(order[0])
                st.table(pd.DataFrame(items, columns=["ID", "Order ID", "Item", "Price", "Qty"]).drop(columns=["ID", "Order ID"]))

def admin_dashboard():
    st.sidebar.title("Admin Dashboard")
    menu = st.sidebar.radio("Go to", ["Overview", "Manage Menu", "All Orders", "Logout"])
    
    if menu == "Logout":
        st.session_state['user'] = None
        st.rerun()
        
    elif menu == "Overview":
        st.markdown("<div class='main-header'>📊 Admin Overview</div>", unsafe_allow_html=True)
        # Placeholder for stats
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Total Revenue", "₹12,450", "+15%")
        with col2:
            st.metric("Active Orders", "5", "-2")
            
    elif menu == "Manage Menu":
        st.subheader("Add New Item")
        with st.form("add_item"):
            name = st.text_input("Item Name")
            price = st.number_input("Price", min_value=1.0)
            stock = st.number_input("Stock", min_value=0)
            cat = st.text_input("Category", value="General")
            desc = st.text_area("Description")
            
            if st.form_submit_button("Add Item"):
                db.add_menu_item(name, price, stock, cat, desc)
                st.success("Item Added!")
                
        st.subheader("Existing Menu")
        items = db.get_menu_items()
        try:
            df = pd.DataFrame(items, columns=["ID", "Name", "Price", "Stock", "Category", "Description", "Image"])
            st.dataframe(df)
        except ValueError as e:
            st.error(f"Error displaying menu: {e}")
            st.write("Raw Data:", items)


    elif menu == "All Orders":
        st.subheader("All Orders")
        orders = db.get_orders(role="admin")
        
        for order in orders:
             with st.expander(f"Order #{order[0]} - {order[2]} - {order[6]}"):
                status_opts = ["Received", "Preparing", "Ready", "Completed", "Cancelled"]
                curr_status_idx = status_opts.index(order[6]) if order[6] in status_opts else 0
                new_status = st.selectbox("Update Status", status_opts, index=curr_status_idx, key=f"status_{order[0]}")
                
                if new_status != order[6]:
                    db.update_order_status(order[0], new_status)
                    st.toast(f"Order #{order[0]} updated to {new_status}")
                    time.sleep(1)
                    st.rerun()

def staff_dashboard():
    # Similar to Admin but restricted
    st.sidebar.title("Staff Dashboard")
    menu = st.sidebar.radio("Go to", ["Live Orders", "Menu Stock", "Logout"])
    
    if menu == "Logout":
        st.session_state['user'] = None
        st.rerun()
        
    elif menu == "Live Orders":
        st.header("Kitchen Display")
        orders = db.get_orders(role="staff")
        active_orders = [o for o in orders if o[6] not in ["Completed", "Cancelled"]]
        
        for order in active_orders:
            col1, col2 = st.columns([3, 1])
            with col1:
                st.subheader(f"Order #{order[0]} ({order[6]})")
                st.write(f"Customer: {order[2]}")
                items = db.get_order_items(order[0])
                for item in items:
                    st.write(f"- {item[4]} x {item[2]}")
            with col2:
                if st.button("Mark Ready", key=f"ready_{order[0]}"):
                     db.update_order_status(order[0], "Ready")
                     st.rerun()
                if st.button("Mark Completed", key=f"comp_{order[0]}"):
                     db.update_order_status(order[0], "Completed")
                     st.rerun()
            st.divider()

# --- MAIN APP ROUTER ---
def main():
    if not st.session_state['user']:
        login_page()
    else:
        role = st.session_state['user']['role']
        if role == 'admin':
            admin_dashboard()
        elif role == 'staff':
            staff_dashboard()
        else:
            student_dashboard()

if __name__ == "__main__":
    main()
