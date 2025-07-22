import streamlit as st
import json
import os
import time
from datetime import datetime
from streamlit_lottie import st_lottie
import requests

# Page config
st.set_page_config(page_title="Smart Table Order", layout="wide", page_icon="🍽️")

# Style
st.markdown("""
<style>
    [data-testid="stSidebar"] { display: none; }
    #MainMenu, footer {visibility: hidden;}
    .main-title {
        font-family: 'Segoe UI', sans-serif;
        font-size: 38px;
        text-align: center;
        color: #2c3e50;
        margin-top: 20px;
    }
    .section-header {
        font-size: 26px;
        font-weight: 700;
        color: #2d3436;
        border-bottom: 2px solid #dcdde1;
        margin-top: 30px;
        margin-bottom: 10px;
    }
    .menu-item {
        background-color: #ffffff;
        border: 1px solid #ececec;
        border-radius: 8px;
        padding: 10px 14px;
        margin-bottom: 10px;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.05);
        font-size: 18px;
    }
    .cart-box {
        background-color: #fefefe;
        padding: 10px 14px;
        border-radius: 8px;
        margin-bottom: 10px;
        box-shadow: 1px 1px 4px rgba(0,0,0,0.04);
    }
</style>
""", unsafe_allow_html=True)

# Lottie loader
def load_lottie_url(url):
    r = requests.get(url)
    return r.json() if r.status_code == 200 else None

lottie_food = load_lottie_url("https://assets4.lottiefiles.com/packages/lf20_dglA3h.json")

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MENU_FILE = os.path.join(BASE_DIR, "menu.json")
ORDERS_FILE = os.path.join(BASE_DIR, "orders.json")

# Load data
menu = json.load(open(MENU_FILE)) if os.path.exists(MENU_FILE) else {}
orders = json.load(open(ORDERS_FILE)) if os.path.exists(ORDERS_FILE) else []

# Session setup
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
    st.markdown(f"<div class='main-title'>🍽️ Table {st.session_state.table_number} - Menu</div>", unsafe_allow_html=True)

if "cart" not in st.session_state:
    st.session_state.cart = {}

# Menu
st.markdown("<div class='section-header'>📋 Menu</div>", unsafe_allow_html=True)
for category, data in menu.items():
    items = data.get("items", []) if isinstance(data, dict) else menu[category]
    image_url = data.get("image") if isinstance(data, dict) else None

    with st.expander(f"{category}"):
        if image_url:
            st.image(image_url, width=200, use_column_width=False)
        for item in items:
            name = item["name"]
            price = item["price"]
            col1, col2, col3, col4 = st.columns([5, 1, 1, 2])
            with col1:
                st.markdown(f"<div class='menu-item'><b>{name}</b> — ₹{price}</div>", unsafe_allow_html=True)

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
st.markdown("<div class='section-header'>🛒 Cart</div>", unsafe_allow_html=True)
if st.session_state.cart:
    total = 0
    for name, item in list(st.session_state.cart.items()):
        subtotal = item["price"] * item["quantity"]
        total += subtotal
        st.markdown(f"<div class='cart-box'><b>{name}</b> × {item['quantity']} — ₹{subtotal}</div>", unsafe_allow_html=True)

    st.markdown(f"### 🧾 Total: ₹{total}")
    if st.button("✅ Place Order", key="place_order"):
        orders = [o for o in orders if o["table"] != st.session_state.table_number]
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
    st.info("Your cart is currently empty.")

# Order History
st.markdown("<div class='section-header'>📦 Order History</div>", unsafe_allow_html=True)
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
