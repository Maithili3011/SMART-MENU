import streamlit as st
import json
import os
import time
from datetime import datetime
from streamlit_lottie import st_lottie
import requests

# Set up page
st.set_page_config(page_title="Smart Table Order", layout="wide", page_icon="🍽️")

# Custom CSS
st.markdown("""
<style>
    body {
        background-color: #0f1117;
        color: #ecf0f1;
    }
    [data-testid="stSidebar"] { display: none; }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .main-title {
        font-size: 42px;
        font-weight: bold;
        color: #87CEEB;
        text-align: center;
        margin-bottom: 10px;
    }
    .section-header {
        font-size: 26px;
        font-weight: 600;
        color: #87CEFA;
        margin-top: 25px;
    }
    .menu-card {
        background-color: #1c1f26;
        padding: 15px;
        border-radius: 10px;
        margin-bottom: 15px;
    }
    .qty-box {
        font-size: 18px;
        color: #87CEEB;
        margin-top: 8px;
    }
    .qty-btn button {
        padding: 0.3em 0.6em !important;
        font-size: 14px !important;
        height: 32px !important;
        width: 32px !important;
        border-radius: 8px !important;
    }
</style>
""", unsafe_allow_html=True)

# Load animation
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

menu = json.load(open(MENU_FILE)) if os.path.exists(MENU_FILE) else {}
orders = json.load(open(ORDERS_FILE)) if os.path.exists(ORDERS_FILE) else []

# Welcome screen
if "table_number" not in st.session_state:
    if lottie_food:
        st_lottie(lottie_food, height=200, key="welcome")
    st.markdown("<div class='main-title'>🍽️ Smart Table Ordering System</div>", unsafe_allow_html=True)
    table_number = st.text_input("🔢 Enter your Table Number")
    if table_number:
        st.session_state.table_number = table_number
        st.session_state.cart = {}
        st.rerun()
else:
    st.markdown(f"<div class='main-title'>🍽️ Table {st.session_state.table_number} - Browse Menu</div>", unsafe_allow_html=True)

# Initialize cart
if "cart" not in st.session_state:
    st.session_state.cart = {}

# Menu section
st.markdown("<div class='section-header'>🧾 Menu</div>", unsafe_allow_html=True)

for category, items in menu.items():
    with st.expander(f"📂 {category}", expanded=True):
        for item in items:
            name = item["name"]
            price = item["price"]
            img_url = item.get("image", "")

            col1, col2, col3 = st.columns([4, 1, 1])

            with col1:
                st.markdown(f"### {name} — ₹{price}", unsafe_allow_html=True)
                if img_url:
                    st.image(img_url, width=180, caption="", use_column_width=False)

            with col2:
                st.markdown("<div class='qty-btn'>", unsafe_allow_html=True)
                if st.button("➖", key=f"minus-{category}-{name}"):
                    if name in st.session_state.cart:
                        if st.session_state.cart[name]["quantity"] > 1:
                            st.session_state.cart[name]["quantity"] -= 1
                        else:
                            del st.session_state.cart[name]
                    st.rerun()

                if st.button("➕", key=f"plus-{category}-{name}"):
                    if name not in st.session_state.cart:
                        st.session_state.cart[name] = {"price": price, "quantity": 1}
                    else:
                        st.session_state.cart[name]["quantity"] += 1
                    st.rerun()
                st.markdown("</div>", unsafe_allow_html=True)

            with col3:
                qty = st.session_state.cart[name]["quantity"] if name in st.session_state.cart else 0
                st.markdown(f"<div class='qty-box'>🛒 Qty: {qty}</div>", unsafe_allow_html=True)

# Cart display
st.markdown("<div class='section-header'>🛍️ Your Cart</div>", unsafe_allow_html=True)
if st.session_state.cart:
    total = 0
    for name, item in st.session_state.cart.items():
        subtotal = item["price"] * item["quantity"]
        total += subtotal
        st.markdown(f"<div class='menu-card'>✅ <b>{name}</b> x {item['quantity']} — ₹{subtotal}</div>", unsafe_allow_html=True)

    st.markdown(f"### 💰 Total: ₹{total}")

    if st.button("✅ Place Order", key="place_order"):
        orders = [o for o in orders if o["table"] != st.session_state.table_number]
        new_order = {
            "table": st.session_state.table_number,
            "items": st.session_state.cart,
            "status": "Pending",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        orders.append(new_order)
        with open(ORDERS_FILE, "w") as f:
            json.dump(orders, f, indent=2)

        st.success("🎉 Order Placed Successfully!")
        st.balloons()
        del st.session_state.cart
        st.rerun()
else:
    st.info("🧺 Your cart is empty.")

# Order history
st.markdown("<div class='section-header'>📦 Order History</div>", unsafe_allow_html=True)
found = False
for order in reversed(orders):
    if order["table"] == st.session_state.table_number:
        found = True
        st.markdown(f"🕒 *{order['timestamp']}* — **Status:** `{order['status']}`")
        for name, item in order["items"].items():
            st.markdown(f"{name} × {item['quantity']} = ₹{item['price'] * item['quantity']}")
        if order["status"] not in ["Completed", "Cancelled"]:
            if st.button(f"❌ Cancel Order ({order['timestamp']})", key=order["timestamp"]):
                order["status"] = "Cancelled"
                with open(ORDERS_FILE, "w") as f:
                    json.dump(orders, f, indent=2)
                st.warning("🚫 Order Cancelled.")
                st.rerun()
        st.markdown("---")

if not found:
    st.info("📭 No previous orders found.")

# Auto-refresh every 10s
with st.empty():
    time.sleep(10)
    st.rerun()
