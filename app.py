import streamlit as st
import json
import os
import time
from datetime import datetime
from streamlit_lottie import st_lottie
import requests
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
import tempfile

# Page setup
st.set_page_config(page_title="Smart Table Order", layout="wide", page_icon="🍽️")

# Custom CSS
st.markdown("""
<style>
    body { background-color: #0f1117; color: #ecf0f1; }
    [data-testid="stSidebar"] { display: none; }
    #MainMenu, footer {visibility: hidden;}
    .main-title {
        font-size: 42px;
        font-weight: bold;
        color: #87CEEB;
        text-align: center;
        margin-bottom: 10px;
    }
    .section-header {
        font-size: 24px;
        font-weight: 600;
        color: #87CEFA;
        margin-top: 25px;
    }
    .menu-card {
        background-color: #1c1f26;
        padding: 10px;
        border-radius: 8px;
        margin-bottom: 10px;
    }
    .qty-box {
        font-size: 16px;
        color: #87CEEB;
        margin-top: 5px;
    }
    .btn-small {
        padding: 3px 10px;
        font-size: 14px;
        border-radius: 5px;
    }
</style>
""", unsafe_allow_html=True)

# Load Lottie animation
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

# PDF Bill Generator
def generate_bill_pdf(order):
    filename = f"bill_table_{order['table']}.pdf"

    # Use temporary directory (safe on all systems)
    output_dir = tempfile.gettempdir()
    file_path = os.path.join(output_dir, filename)

    c = canvas.Canvas(file_path)
    c.setFont("Helvetica-Bold", 16)
    c.drawString(200, 800, "Smart Table Billing Receipt")

    c.setFont("Helvetica", 12)
    c.drawString(50, 770, f"Table: {order['table']}")
    c.drawString(300, 770, f"Date: {order['timestamp']}")

    y = 740
    c.drawString(50, y, "Item")
    c.drawString(250, y, "Qty")
    c.drawString(300, y, "Price")
    c.drawString(400, y, "Total")

    y -= 20
    total = 0
    for name, item in order["items"].items():
        qty = item["quantity"]
        price = item["price"]
        subtotal = qty * price
        total += subtotal

        c.drawString(50, y, name)
        c.drawString(250, y, str(qty))
        c.drawString(300, y, f"₹{price}")
        c.drawString(400, y, f"₹{subtotal}")
        y -= 20

    c.setFont("Helvetica-Bold", 12)
    c.drawString(300, y - 10, "Grand Total:")
    c.drawString(400, y - 10, f"₹{total}")

    c.save()
    return file_path


# Welcome
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
    st.markdown(f"<div class='main-title'>🍽️ Table {st.session_state.table_number} - Menu</div>", unsafe_allow_html=True)

# Cart Init
if "cart" not in st.session_state:
    st.session_state.cart = {}

# Menu Section
st.markdown("<div class='section-header'>🧾 Menu</div>", unsafe_allow_html=True)
for category, items in menu.items():
    with st.expander(f"📂 {category}", expanded=True):
        for item in items:
            name, price = item["name"], item["price"]
            img_url = item.get("image", "")
            col1, col2, col3 = st.columns([5, 1, 1])

            with col1:
                st.markdown(f"**{name} — ₹{price}**", unsafe_allow_html=True)
                if img_url:
                    st.image(img_url, width=180)

            with col2:
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

            with col3:
                qty = st.session_state.cart[name]["quantity"] if name in st.session_state.cart else 0
                st.markdown(f"<div class='qty-box'>🛒 Qty: {qty}</div>", unsafe_allow_html=True)

# Cart Summary
st.markdown("<div class='section-header'>🛍️ Your Cart</div>", unsafe_allow_html=True)
if st.session_state.cart:
    total = 0
    for name, item in st.session_state.cart.items():
        subtotal = item["price"] * item["quantity"]
        total += subtotal
        st.markdown(f"<div class='menu-card'>✅ <b>{name}</b> x {item['quantity']} — ₹{subtotal}</div>", unsafe_allow_html=True)

    st.markdown(f"### 💰 Total: ₹{total}")
    if st.button("✅ Place Order"):
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
        st.success("🎉 Order Placed!")
        st.balloons()
        del st.session_state.cart
        st.rerun()
else:
    st.info("🧺 Your cart is empty.")
    
# Order history section
st.markdown("<div class='section-header'>📦 Order History</div>", unsafe_allow_html=True)
found = False

for order in reversed(orders):
    if order["table"] == st.session_state.table_number:
        found = True
        st.markdown(f"🕒 *{order['timestamp']}* — **Status:** `{order['status']}`")
        for name, item in order["items"].items():
            st.markdown(f"{name} × {item['quantity']} = ₹{item['price'] * item['quantity']}")
        
        # Add billing PDF option for completed orders
        if order["status"] == "Completed":
            bill_path = generate_bill_pdf(order)
            with open(bill_path, "rb") as bill_file:
                st.download_button(
                    label="📄 Download Bill PDF",
                    data=bill_file,
                    file_name=os.path.basename(bill_path),
                    mime="application/pdf"
                )

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
# Auto refresh
with st.empty():
    time.sleep(10)
    st.rerun()
