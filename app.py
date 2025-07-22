import streamlit as st
import json
import os
import time
from datetime import datetime
from streamlit_lottie import st_lottie
import requests

# Setup
st.set_page_config(page_title="Smart Table Order", layout="wide", page_icon="🍽️")

# Custom CSS styling
st.markdown("""
<style>
    [data-testid="stSidebar"] { display: none; }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .main-title {
        font-family: 'Segoe UI', sans-serif;
        font-size: 38px;
        text-align: center;
        color: #2c3e50;
        margin-top: 20px;
    }
    .section-header {
        font-size: 24px;
        font-weight: 600;
        color: #34495e;
        margin-bottom: 15px;
    }
    .menu-item {
        font-size: 18px;
        padding: 8px;
    }
    .btn-style {
        border: none;
        background-color: #3498db;
        color: white;
        padding: 6px 14px;
        font-size: 16px;
        border-radius: 5px;
    }
    .cart-box {
        background-color: #f8f9fa;
        padding: 10px 15px;
        border-radius: 6px;
        margin-bottom: 10px;
    }
</style>
""", unsafe_allow_html=True)

# Lottie animation loader
def load_lottie_url(url):
    r = requests.get(url)
    if r.status_code != 200:
        return None
    return r.json()

lottie_food = load_lottie_url("https://assets4.lottiefiles.com/packages/lf20_dglA3h.json")

# File paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MENU_FILE = os.path.join(BASE_DIR, "menu.json")
ORDERS_FILE = os.path.join(BASE_DIR, "orders.json")

# Load data
menu = json.load(open(MENU_FILE)) if os.path.exists(MENU_FILE) else {}
orders = json.load(open(ORDERS_FILE)) if os.path.exists(ORDERS_FILE) else []

# Welcome screen
if "table_number" not in st.session_state:
    if lottie_food:
        st_lottie(lottie_food, height=200, key="welcome")
    st.markdown("<div class='main-title'>Smart Table Ordering System</div>", unsafe_allow_html=True)
    table_number = st.text_input("Enter your Table Number")
    if table_number:
        st.session_state.table_number = table_number
        st.session_state.cart = {}
        st.rerun()
else:
    st.markdown(f"<div class='main-title'>Table {st.session_state.table_number} - Menu</div>", unsafe_allow_html=True)

# Initialize cart
if "cart" not in st.session_state:
    st.session_state.cart = {}

# Menu display
st.markdown("<div class='section-header'>Menu</div>", unsafe_allow_html=True)
for category, items in menu.items():
    with st.expander(f"{category}"):
        for item in items:
            name = item["name"]
            price = item["price"]

            col1, col2, col3, col4 = st.columns([6, 1, 1, 2])
            col1.markdown(f"<div class='menu-item'><b>{name}</b> - ₹{price}</div>", unsafe_allow_html=True)

            if col2.button("➖", key=f"minus-{category}-{name}"):
                if name in st.session_state.cart:
                    if st.session_state.cart[name]["quantity"] > 1:
                        st.session_state.cart[name]["quantity"] -= 1
                    else:
                        del st.session_state.cart[name]
                st.rerun()

            if col3.button("➕", key=f"plus-{category}-{name}"):
                if name not in st.session_state.cart:
                    st.session_state.cart[name] = {"price": price, "quantity": 1}
                else:
                    st.session_state.cart[name]["quantity"] += 1
                st.rerun()

            qty = st.session_state.cart[name]["quantity"] if name in st.session_state.cart else 0
            col4.markdown(f"Quantity: {qty}")

# Cart
st.markdown("<div class='section-header'>Cart</div>", unsafe_allow_html=True)
if st.session_state.cart:
    total = 0
    for name, item in list(st.session_state.cart.items()):
        subtotal = item["price"] * item["quantity"]
        total += subtotal
        with st.container():
            st.markdown(f"<div class='cart-box'><b>{name}</b> × {item['quantity']} — ₹{subtotal}</div>", unsafe_allow_html=True)

    st.markdown(f"### Total: ₹{total}")
    if st.button("✅ Place Order", key="place_order"):
        orders = [o for o in orders if o["table"] != st.session_state.table_number]
        order = {
            "table": st.session_state.table_number,
            "items": st.session_state.cart,
            "status": "Pending",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        with open(ORDERS_FILE, "w") as f:
            orders.append(order)
            json.dump(orders, f, indent=2)

        st.success("✅ Order Placed Successfully!")
        st.balloons()
        del st.session_state.cart
        st.rerun()
else:
    st.info("Your cart is currently empty.")

# Order History
st.markdown("<div class='section-header'>Order History</div>", unsafe_allow_html=True)
found = False
for order in reversed(orders):
    if order["table"] == st.session_state.table_number:
        found = True
        st.markdown(f"🕒 *{order['timestamp']}* — **Status:** `{order['status']}`")
        for name, item in order["items"].items():
            line = f"{name} × {item['quantity']} = ₹{item['price'] * item['quantity']}"
            if order["status"] == "Cancelled":
                st.markdown(f"<s>{line}</s>", unsafe_allow_html=True)
            else:
                st.markdown(line)

        if order["status"] not in ["Completed", "Cancelled"]:
            if st.button(f"❌ Cancel Order ({order['timestamp']})", key=order["timestamp"]):
                order["status"] = "Cancelled"
                with open(ORDERS_FILE, "w") as f:
                    json.dump(orders, f, indent=2)
                st.warning("Order Cancelled.")
                st.rerun()
        st.markdown("---")

if not found:
    st.info("No previous orders found.")

# Auto-refresh
with st.empty():
    time.sleep(10)
    st.rerun()
