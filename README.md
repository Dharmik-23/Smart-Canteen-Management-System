# 🍔 Smart Canteen Management System

A full-stack Python web application built with **Streamlit** to streamline canteen operations. This system facilitates role-based interaction for Students, Staff, and Administrators, featuring digital menus, cart management, checking out with QR codes, and real-time order tracking.

---

## 🚀 Features

### 👨‍🎓 for Students (User)
- **Digital Menu**: Browse items by category with images and descriptions.
- **Smart Cart**: Add items, adjust quantities, and see live total calculations with GST.
- **Order Placement**: Secure checkout with Order ID generation.
- **Payment Integration**: Generate UPI QR codes for easy payment or choose Cash on Delivery.
- **Live Order Tracking**: Track status from 'Received' -> 'Preparing' -> 'Ready' -> 'Completed'.
- **Order History**: View past orders and details.
- **Feedback System**: Rate meals and leave comments after completion.

### 👨‍🍳 for Staff (Kitchen)
- **Kitchen Display System (KDS)**: Real-time view of incoming "Live Orders".
- **Status Updates**: Mark orders as 'Ready' or 'Completed' with a single click.
- **Stock View**: Quick glance at current inventory levels.

### 👮‍♂️ for Admin (Management)
- **Analytics Dashboard**: Overview of Total Revenue, Active Orders, and Sales trends.
- **Menu Management**: Add new items, update prices, and description.
- **Inventory Control**: Manage stock levels (Real-time deduction on orders).
- **Order Management**: Oversee all orders and manually update statuses if needed.

---

## 🛠️ Tech Stack

- **Frontend & Backend**: [Streamlit](https://streamlit.io/) (Python)
- **Database**: SQLite (Local `canteen.db`)
- **Data Processing**: Pandas
- **Visualization**: Plotly / Streamlit Metrics
- **Utilities**: 
  - `qrcode` (Payment QR Generation)
  - `Pillow` (Image Processing)

---

## 📂 Project Structure

```
Smart-Canteen-Management-System/
├── canteen.db           # SQLite Database (Auto-created)
├── cli_main.py          # Command Line Interface version (Optional)
├── database.py          # Database operations (CRUD functions)
├── main.py              # Main Streamlit Application Entry point
├── requirements.txt     # Python Dependencies
└── README.md            # Project Documentation
```

---

## ⚙️ Installation & Local Setup

1. **Clone the Repository** (or download the source):
   ```bash
   git clone <repository_url>
   cd Smart-Canteen-Management-System
   ```

2. **Install Dependencies**:
   Ensure you have Python installed. Then run:
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the App**:
   ```bash
   streamlit run main.py
   ```

4. **Access the App**:
   The app will open in your browser at `http://localhost:8501`.

---

## 🔑 Default Credentials

The system comes with a pre-configured Admin account:
- **Username**: `admin`
- **Password**: `admin123`

*Note: Students can Sign Up freely via the login page.*

---

## 📦 Deployment Note

This application essentially requires a **shared backend** (the `canteen.db` file) to allow Students and Kitchen Staff to communicate (Student places order -> Store in DB -> Staff sees order).

### Recommended: Streamlit Community Cloud
1. Push this code to a public GitHub repository.
2. Sign up at [share.streamlit.io](https://share.streamlit.io/).
3. Connect your GitHub and deploy the `main.py` file.
4. **Important**: For a persistent database on Cloud, consider migrating SQLite to a Cloud Database (like Supabase, Neon, or Google Sheets) or understand that SQLite data will reset when the app reboots.

### Note on GitHub Pages
**GitHub Pages** supports static sites (HTML/CSS/JS). Since this is a dynamic Python application requiring server-side logic and database persistence, **it cannot be hosted directly on GitHub Pages** without losing the shared database functionality. Use Streamlit Community Cloud or a VPS (like Render/Railway) instead.
