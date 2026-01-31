# Smart Canteen Management System

## Features
- **Role-based Login**: Admin, Staff, Student.
- **Digital Menu**: Dynamic menu from database with images/descriptions.
- **Ordering System**: Add to cart, live bill calculation with GST.
- **QR Code**: UPI Payment QR and Order Pickup QR generation.
- **Live Tracking**: Real-time status updates (Received -> Preparing -> Ready).
- **Admin Dashboard**:
  - Sales Analytics (Charts).
  - Live Kitchen Display (Kanban-style status updates).
  - Inventory Management (Edit Stock/Menu).
- **Feedback System**: Users can rate completed orders.

## Setup Instructions

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the Application**:
   ```bash
   streamlit run main.py
   ```

## Default Credentials
- **Admin Username**: `admin`
- **Admin Password**: `admin123`

## Database
The system uses SQLite (`canteen.db`). It will be automatically created/updated on first run.
