import streamlit as st
import json
import os
import time
from datetime import datetime
from streamlit_lottie import st_lottie
import requests
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

# Set page config
st.set_page_config(page_title="Smart Table Order", layout="wide", page_icon="🍽️")

# Hide sidebar and default styling
st.markdown("""
    <style>
        [data-testid="stSidebar"] { display: none; }
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        .title-style {
            font-size: 36px;
            font-weight: bold;
            text-align: center;
            color: #ff4b4b;
        }
        .subheader-style {
            font-size: 24px;
            font-weight: 600;
            color: #333333;
        }
    </style>
""", unsafe_allow_html=True)

# Load Lottie animation from URL
def load_lottie_url(url):
    r = requests.get(url)
    if r.status_code != 200:
        return None
    return r.json()

lottie_food = load_lottie_url("https://assets4.lottiefiles.com/packages/lf20_dglA3h.json")

# Get paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MENU_FILE = os.path.join(BASE_DIR, "menu.json")
ORDERS_FILE = os.path.join(BASE_DIR, "orders.json")
PDF_DIR = os.path.join(BASE_DIR, "bills")
os.makedirs(PDF_DIR, exist_ok=True)

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
    if lottie_food:
        st_lottie(lottie_food, height=200, key="welcome")
    else:
        st.warning("⚠️ Animation failed to load.")
    st.markdown("<div class='title-style'>🍽️ Smart Table Ordering System</div>", unsafe_allow_html=True)
    table_number = st.text_input("🕧 Enter your Table Number")
    if table_number:
        st.session_state.table_number = table_number
        st.session_state.cart = {}
        st.rerun()
else:
    st.markdown(f"<div class='title-style'>🍽️ Table {st.session_state.table_number} - Menu</div>", unsafe_allow_html=True)

# Initialize cart
if "cart" not in st.session_state:
    st.session_state.cart = {}

# Show menu
st.markdown("<div class='subheader-style'>📋 Menu</div>", unsafe_allow_html=True)
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
                        else:
                            del st.session_state.cart[name]
                    st.rerun()

            with col3:
                if st.button("➕", key=f"plus-{category}-{name}"):
                    if name not in st.session_state.cart:
                        st.session_state.cart[name] = {"price": price, "quantity": 1}
                    else:
                        st.session_state.cart[name]["quantity"] += 1
                    st.rerun()

            with col4:
                qty = st.session_state.cart[name]["quantity"] if name in st.session_state.cart else 0
                st.markdown(f"Qty: {qty}")

# Show cart
st.markdown("<div class='subheader-style'>🛒 Cart</div>", unsafe_allow_html=True)
if st.session_state.cart:
    total = 0
    for name, item in list(st.session_state.cart.items()):
        col1, col2 = st.columns([6, 2])
        with col1:
            st.markdown(f"**{name}** x {item['quantity']}")
        with col2:
            subtotal = item["price"] * item["quantity"]
            total += subtotal
            st.markdown(f"₹{subtotal}")

    st.markdown(f"### 🧳 Total: ₹{total}")

    if st.button("✅ Place Order"):
        orders = [o for o in orders if o["table"] != st.session_state.table_number]
        order = {
            "table": st.session_state.table_number,
            "items": st.session_state.cart,
            "status": "Completed",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        orders.append(order)
        with open(ORDERS_FILE, "w") as f:
            json.dump(orders, f, indent=2)

        bill_path = os.path.join(PDF_DIR, f"Bill_Table_{order['table']}_{order['timestamp'].replace(':','-')}.pdf")
        c = canvas.Canvas(bill_path, pagesize=letter)
        c.setFont("Helvetica-Bold", 16)
        c.drawCentredString(300, 750, "Smart Table Billing Receipt")

        c.setFont("Helvetica", 12)
        c.drawString(50, 720, f"Table: {order['table']}")
        c.drawString(400, 720, f"Date: {order['timestamp']}")

        c.drawString(50, 690, "Item")
        c.drawString(250, 690, "Qty")
        c.drawString(320, 690, "Price")
        c.drawString(400, 690, "Total")

        y = 670
        total = 0
        for name, item in order["items"].items():
            c.drawString(50, y, name)
            c.drawString(250, y, str(item["quantity"]))
            c.drawString(320, y, f"₹{item['price']}")
            line_total = item["price"] * item["quantity"]
            c.drawString(400, y, f"₹{line_total}")
            total += line_total
            y -= 20

        c.setFont("Helvetica-Bold", 12)
        c.drawString(320, y - 10, "Grand Total:")
        c.drawString(400, y - 10, f"₹{total}")

        c.save()

        st.success("✅ Order Placed Successfully! PDF Generated.")
        st.write(f"**[Download Bill]({bill_path})**")
        st.balloons()
        del st.session_state.cart
        st.rerun()
else:
    st.info("🛎️ Your cart is empty.")

# Show order history
st.markdown("<div class='subheader-style'>📦 Your Orders</div>", unsafe_allow_html=True)
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
                st.warning("⚠️ Order cancelled.")
                st.rerun()
        st.markdown("---")

if not found:
    st.info("📬 No orders found.")

# Auto-refresh
with st.empty():
    time.sleep(10)
    st.rerun()
