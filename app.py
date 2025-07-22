import streamlit as st
import json
import os
import time
from datetime import datetime

# Hide sidebar and Streamlit default styling
st.set_page_config(page_title="Smart Table Order", layout="wide")
hide_sidebar_style = """
    <style>
        [data-testid="stSidebar"] { display: none; }
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
    </style>
"""
st.markdown(hide_sidebar_style, unsafe_allow_html=True)

# Get absolute path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MENU_FILE = os.path.join(BASE_DIR, "menu.json")
ORDERS_FILE = os.path.join(BASE_DIR, "orders.json")

# Load menu
if os.path.exists(MENU_FILE):
    with open(MENU_FILE, "r") as f:
        menu = json.load(f)
else:
    st.error(f"❌ Menu file not found at {MENU_FILE}")
    st.stop()

# Load orders
if os.path.exists(ORDERS_FILE):
    with open(ORDERS_FILE, "r") as f:
        orders = json.load(f)
else:
    orders = []

# Ask for table number (shown on main page)
if "table_number" not in st.session_state:
    st.title("🍽️ Smart Table Ordering System")
    table_number = st.text_input("🔢 Enter your Table Number")
    if table_number:
        st.session_state.table_number = table_number
        st.session_state.cart = {}
        st.rerun()
else:
    st.title(f"🍽️ Smart Table Ordering — Table {st.session_state.table_number}")

# Initialize cart
if "cart" not in st.session_state:
    st.session_state.cart = {}

# Show menu
st.subheader("📋 Menu")
for category, items in menu.items():
    with st.expander(category):
        for item in items:
            col1, col2 = st.columns([6, 1])
            with col1:
                st.markdown(f"**{item['name']}** — ₹{item['price']}")
            with col2:
                if st.button("➕", key=f"{category}-{item['name']}"):
                    name = item["name"]
                    price = item["price"]
                    if name not in st.session_state.cart:
                        st.session_state.cart[name] = {"price": price, "quantity": 1}
                    else:
                        st.session_state.cart[name]["quantity"] += 1
                    st.rerun()

# Show cart
st.subheader("🛒 Cart")
if st.session_state.cart:
    total = 0
    for name, item in st.session_state.cart.items():
        subtotal = item["price"] * item["quantity"]
        total += subtotal
        st.markdown(f"{name} x {item['quantity']} = ₹{subtotal}")
    st.markdown(f"### 🧾 Total: ₹{total}")

    if st.button("✅ Place Order"):
        # Remove old orders for this table
        orders = [o for o in orders if o["table"] != st.session_state.table_number]

        # Add new order
        order = {
            "table": st.session_state.table_number,
            "items": st.session_state.cart,
            "status": "Pending",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        orders.append(order)
        with open(ORDERS_FILE, "w") as f:
            json.dump(orders, f, indent=2)

        st.success("✅ Order Placed!")
        del st.session_state.cart
        st.rerun()
else:
    st.info("🛍️ Your cart is empty.")

# Show order history
st.subheader("📦 Your Orders")
found = False
for order in reversed(orders):
    if order["table"] == st.session_state.table_number:
        found = True
        status = order["status"]
        st.markdown(f"🕒 *{order['timestamp']}* — **Status:** `{status}`")
        for name, item in order["items"].items():
            line = f"{name} x {item['quantity']} = ₹{item['price'] * item['quantity']}"
            if status == "Cancelled":
                st.markdown(f"<s>{line}</s>", unsafe_allow_html=True)
            else:
                st.markdown(line)

        if status not in ["Completed", "Cancelled"]:
            if st.button(f"❌ Cancel Order ({order['timestamp']})", key=order["timestamp"]):
                order["status"] = "Cancelled"
                with open(ORDERS_FILE, "w") as f:
                    json.dump(orders, f, indent=2)
                st.warning("Order cancelled.")
                st.rerun()
        st.markdown("---")

if not found:
    st.info("📭 No orders found.")

# Auto-refresh every 10 seconds
with st.empty():
    time.sleep(10)
    st.rerun()