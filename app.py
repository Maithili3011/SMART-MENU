import streamlit as st
import json
import os
import time
from datetime import datetime

# Page config
st.set_page_config(page_title="Smart Table Order", layout="wide")

# Hide sidebar + enhance styling
custom_css = """
    <style>
        [data-testid="stSidebar"] { display: none; }
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        html, body, [class*="css"]  {
            font-size: 18px;
        }
        .stButton>button {
            height: 2.5em;
            font-size: 18px;
        }
        .stMarkdown {
            font-size: 18px;
        }
        .stButton>button:hover {
            background-color: #FF4B4B;
            color: white;
            transform: scale(1.05);
            transition: 0.2s ease-in-out;
        }
    </style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

# File paths
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

# Ask for table number
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

# Alert placeholder
alert = st.empty()

# Show menu
st.subheader("📋 Menu")
for category, items in menu.items():
    with st.expander(category):
        for item in items:
            name = item["name"]
            price = item["price"]

            col1, col2, col3, col4 = st.columns([5, 1, 1, 2])

            with col1:
                st.markdown(f"**{name}** — ₹{price}")

            with col2:
                if st.button("➖", key=f"minus-{category}-{name}"):
                    if name in st.session_state.cart:
                        if st.session_state.cart[name]["quantity"] > 1:
                            st.session_state.cart[name]["quantity"] -= 1
                            alert.info(f"➖ Decreased {name}")
                        else:
                            del st.session_state.cart[name]
                            alert.warning(f"❌ Removed {name}")
                    st.rerun()

            with col3:
                if st.button("➕", key=f"plus-{category}-{name}"):
                    if name not in st.session_state.cart:
                        st.session_state.cart[name] = {"price": price, "quantity": 1}
                        alert.success(f"✔️ Added {name}")
                    else:
                        st.session_state.cart[name]["quantity"] += 1
                        alert.success(f"➕ Increased {name}")
                    st.rerun()

            with col4:
                qty = st.session_state.cart[name]["quantity"] if name in st.session_state.cart else 0
                st.markdown(f"Qty: {qty}")

# Show cart
st.subheader("🛒 Cart")
if st.session_state.cart:
    total = 0
    for name, item in list(st.session_state.cart.items()):
        col1, col2, col3, col4 = st.columns([4, 1, 1, 2])
        with col1:
            st.markdown(f"**{name}** x {item['quantity']}")
        with col2:
            if st.button("➖", key=f"decrease-{name}"):
                if item["quantity"] > 1:
                    st.session_state.cart[name]["quantity"] -= 1
                    alert.info(f"➖ Decreased {name}")
                else:
                    del st.session_state.cart[name]
                    alert.warning(f"❌ Removed {name}")
                st.rerun()
        with col3:
            if st.button("➕", key=f"increase-{name}"):
                st.session_state.cart[name]["quantity"] += 1
                alert.success(f"➕ Increased {name}")
                st.rerun()
        with col4:
            subtotal = item["price"] * item["quantity"]
            total += subtotal
            st.markdown(f"₹{subtotal}")

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

        st.success("✅ Order Placed Successfully!")
        st.balloons()
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
                st.warning("⚠️ Order has been cancelled.")
                st.rerun()
        st.markdown("---")

if not found:
    st.info("📭 No orders found.")

# Auto-refresh every 10 seconds
with st.empty():
    time.sleep(10)
    st.rerun()
