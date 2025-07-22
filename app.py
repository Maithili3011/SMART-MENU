import streamlit as st
import json
import os
import time
from datetime import datetime
from streamlit_lottie import st_lottie
import requests

# Page config
st.set_page_config(page_title="Smart Table Order", layout="wide")

# CSS styles
custom_css = """
    <style>
        [data-testid="stSidebar"] { display: none; }
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        html, body {
            font-size: 18px;
            font-family: 'Segoe UI', sans-serif;
        }
        .stButton>button {
            height: 3em;
            width: 100%;
            font-size: 18px;
            border-radius: 10px;
            transition: 0.3s;
        }
        .stButton>button:hover {
            background-color: #ff4b4b;
            color: white;
            transform: scale(1.03);
        }
        .stMarkdown {
            font-size: 18px;
        }
        .glass {
            background: rgba(255, 255, 255, 0.15);
            border-radius: 20px;
            padding: 1.5em;
            backdrop-filter: blur(10px);
            -webkit-backdrop-filter: blur(10px);
        }
    </style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

# Lottie helper
def load_lottie_url(url):
    r = requests.get(url)
    if r.status_code == 200:
        return r.json()
    else:
        return None

# Load animation
order_anim = load_lottie_url("https://assets4.lottiefiles.com/packages/lf20_dyteqdpp.json")

# Paths
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

# Table number prompt
if "table_number" not in st.session_state:
    col1, col2 = st.columns([2, 3])
    with col1:
        st_lottie(order_anim, height=300, key="start_anim")
    with col2:
        st.title("🍽️ Smart Table Order")
        table_number = st.text_input("🔢 Enter your Table Number")
        if table_number:
            st.session_state.table_number = table_number
            st.session_state.cart = {}
            st.rerun()
else:
    st.title(f"🍽️ Welcome — Table {st.session_state.table_number}")

if "cart" not in st.session_state:
    st.session_state.cart = {}

alert = st.empty()

# Menu
st.subheader("📋 Menu")
for category, items in menu.items():
    with st.expander(f"🍴 {category}", expanded=True):
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
                            st.toast(f"➖ Decreased {name}", icon="➖")
                        else:
                            del st.session_state.cart[name]
                            st.toast(f"❌ Removed {name}", icon="🗑️")
                    st.rerun()
            with col3:
                if st.button("➕", key=f"plus-{category}-{name}"):
                    if name not in st.session_state.cart:
                        st.session_state.cart[name] = {"price": price, "quantity": 1}
                        st.toast(f"✔️ Added {name}", icon="🛒")
                    else:
                        st.session_state.cart[name]["quantity"] += 1
                        st.toast(f"➕ Increased {name}", icon="🛒")
                    st.rerun()
            with col4:
                qty = st.session_state.cart[name]["quantity"] if name in st.session_state.cart else 0
                st.markdown(f"Qty: {qty}")

# Cart display
st.subheader("🛒 Your Cart")
if st.session_state.cart:
    total = 0
    for name, item in list(st.session_state.cart.items()):
        col1, col2, col3, col4 = st.columns([4, 1, 1, 2])
        with col1:
            st.markdown(f"**{name}** x {item['quantity']}")
        with col2:
            if st.button("➖", key=f"dec-{name}"):
                if item["quantity"] > 1:
                    st.session_state.cart[name]["quantity"] -= 1
                    st.toast(f"➖ Decreased {name}")
                else:
                    del st.session_state.cart[name]
                    st.toast(f"❌ Removed {name}")
                st.rerun()
        with col3:
            if st.button("➕", key=f"inc-{name}"):
                st.session_state.cart[name]["quantity"] += 1
                st.toast(f"➕ Increased {name}")
                st.rerun()
        with col4:
            subtotal = item["price"] * item["quantity"]
            total += subtotal
            st.markdown(f"₹{subtotal}")

    st.markdown(f"### 🧾 Total: ₹{total}")

    if st.button("✅ Place Order"):
        # Remove existing orders from same table
        orders = [o for o in orders if o["table"] != st.session_state.table_number]

        # New order
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

# Order History
st.subheader("📦 Order History")
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
    st.info("📭 No previous orders.")

# Auto-refresh
with st.empty():
    time.sleep(10)
    st.rerun()
