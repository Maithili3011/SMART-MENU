import streamlit as st
import json
import os
import time
from datetime import datetime
from fpdf import FPDF
from PIL import Image

# -------------- Streamlit Config & Styling --------------
st.set_page_config(page_title="Smart Table Order", layout="wide")
st.markdown("""
    <style>
    [data-testid="stSidebar"] { display: none; }
    #MainMenu, footer {visibility: hidden;}
    body {
        background-color: #0f0f0f;
    }

    /* Global font color */
    .css-18ni7ap, .css-10trblm, .css-qbe2hs, .css-hxt7ib {
        color: #f1f1f1 !important;
    }

    /* Sky blue styled buttons */
    .stButton > button {
        background-color: #00bcd4;
        color: #ffffff;
        font-weight: bold;
        font-size: 0.95rem;
        border: none;
        border-radius: 10px;
        padding: 0.5rem 1.2rem;
        box-shadow: 0 4px 8px rgba(0, 188, 212, 0.3);
        transition: background-color 0.3s, transform 0.1s;
    }

    .stButton > button:hover {
        background-color: #019ab0;
        transform: scale(1.02);
        box-shadow: 0 6px 12px rgba(0, 188, 212, 0.4);
    }

    .stButton > button:active {
        transform: scale(0.96);
        box-shadow: 0 3px 6px rgba(0, 188, 212, 0.2);
    }

    /* Download button specific */
    .stDownloadButton > button {
        background-color: #019ab0 !important;
        color: white !important;
        font-weight: bold;
        border-radius: 8px;
        padding: 0.4rem 0.8rem;
        font-size: 0.85rem;
    }

    /* Optional container border color */
    .block-container {
        border-left: 1px solid #2e2e2e;
        border-right: 1px solid #2e2e2e;
    }
    </style>
""", unsafe_allow_html=True)

# -------------- Paths --------------
BASE_DIR = os.path.dirname(os.path.abspath(_file_))
MENU_FILE = os.path.join(BASE_DIR, "menu.json")
ORDERS_FILE = os.path.join(BASE_DIR, "orders.json")
FEEDBACK_FILE = os.path.join(BASE_DIR, "feedback.json")
QR_IMAGE = os.path.join(BASE_DIR, "qr.jpg")

# -------------- Helper: Generate Invoice --------------
def generate_invoice(order):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, "Smart Café Invoice", ln=True, align="C")
    
    pdf.set_font("Arial", "", 12)
    pdf.cell(0, 10, f"Table: {order['table']}", ln=True)
    pdf.cell(0, 10, f"Date: {order['timestamp']}", ln=True)
    pdf.cell(0, 10, f"Payment: {order.get('payment', 'N/A')}", ln=True)
    pdf.ln(10)

    pdf.set_font("Arial", "B", 12)
    pdf.cell(80, 10, "Item", 1)
    pdf.cell(30, 10, "Qty", 1)
    pdf.cell(30, 10, "Price", 1)
    pdf.cell(40, 10, "Subtotal", 1)
    pdf.ln()

    pdf.set_font("Arial", "", 12)
    total = 0
    for name, item in order["items"].items():
        qty = item["quantity"]
        price = item["price"]
        subtotal = qty * price
        total += subtotal

        pdf.cell(80, 10, name, 1)
        pdf.cell(30, 10, str(qty), 1)
        pdf.cell(30, 10, f"Rs. {price}", 1)
        pdf.cell(40, 10, f"Rs. {subtotal}", 1)
        pdf.ln()

    pdf.set_font("Arial", "B", 12)
    pdf.cell(140, 10, "Total", 1)
    pdf.cell(40, 10, f"Rs. {total}", 1)
    pdf.ln(20)

    

    invoice_path = os.path.join(BASE_DIR, f"invoice_table_{order['table']}.pdf")
    pdf.output(invoice_path)
    return invoice_path

# -------------- Load Data --------------
menu = json.load(open(MENU_FILE, encoding="utf-8")) if os.path.exists(MENU_FILE) else {}
orders = json.load(open(ORDERS_FILE, encoding="utf-8")) if os.path.exists(ORDERS_FILE) else []
feedback = json.load(open(FEEDBACK_FILE, encoding="utf-8")) if os.path.exists(FEEDBACK_FILE) else []

# -------------- Table Number Session with Availability Check --------------
if "table_number" not in st.session_state:
    st.title("🍽️ Smart Table Ordering System")

    TOTAL_TABLES = 10  # You can increase this to any number you want
    all_tables = [str(i) for i in range(1, TOTAL_TABLES + 1)]

    # Get tables that are occupied (pending or preparing orders)
    occupied_tables = set()
    for order in orders:
        if order["status"] in ["pending", "preparing"]:
            occupied_tables.add(order["table"])

    # Available tables are those not in occupied list
    available_tables = [t for t in all_tables if t not in occupied_tables]

    if not available_tables:
        st.warning("🚫 No tables are currently available. Please wait or check back later.")
        st.stop()

    selected_table = st.selectbox("🔢 Select an Available Table", available_tables)

    if st.button("✅ Confirm Table"):
        st.session_state.table_number = selected_table
        st.session_state.cart = {}
        st.rerun()

    st.stop()
    
st.title(f"🍽️ Smart Ordering — Table {st.session_state.table_number}")
if "cart" not in st.session_state:
    st.session_state.cart = {}

# -------------- Display Menu --------------
st.subheader("📋 Menu")
for category, items in menu.items():
    with st.expander(category):
        for item in items:
            col1, col2 = st.columns([6, 1])
            with col1:
                st.markdown(f"{item['name']} — ₹{item['price']}")
            with col2:
                if st.button("➕", key=f"{category}-{item['name']}"):
                    name, price = item["name"], item["price"]
                    st.session_state.cart[name] = st.session_state.cart.get(name, {"price": price, "quantity": 0})
                    st.session_state.cart[name]["quantity"] += 1
                    st.rerun()

# -------------- Display Cart --------------
st.subheader("🛒 Cart")
if st.session_state.cart:
    total = 0
    for name, item in list(st.session_state.cart.items()):
        subtotal = item["price"] * item["quantity"]
        total += subtotal

        col1, col2 = st.columns([6, 1])
        with col1:
            st.markdown(f"{name} x {item['quantity']} = ₹{subtotal}")
        with col2:
            if st.button("➖", key=f"dec-{name}"):
                st.session_state.cart[name]["quantity"] -= 1
                if st.session_state.cart[name]["quantity"] <= 0:
                    del st.session_state.cart[name]
                st.rerun()

    st.markdown(f"### 🧾 Total: ₹{total}")

    payment_method = st.selectbox("💳 Select Payment Method", ["Cash", "Card", "Online"], key="payment_select")
    if st.button("✅ Place Order"):
        if payment_method:
            orders = [o for o in orders if o["table"] != st.session_state.table_number]
            new_order = {
                "table": st.session_state.table_number,
                "items": st.session_state.cart,
                "status": "pending",
                "payment": payment_method,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            orders.append(new_order)
            with open(ORDERS_FILE, "w", encoding="utf-8") as f:
                json.dump(orders, f, indent=2)

            if payment_method == "Cash":
                st.warning(f"🚨 Admin Alert: Table {st.session_state.table_number} selected *CASH* payment.")
                st.audio("https://actions.google.com/sounds/v1/alarms/alarm_clock.ogg", format="audio/ogg")

            # ✅ Fancy animation popup on order placement
            st.markdown("""
                <div id="popup" style="
                    position: fixed;
                    top: 30%;
                    left: 50%;
                    transform: translate(-50%, -50%);
                    background: #00bcd4;
                    color: white;
                    padding: 30px 50px;
                    border-radius: 20px;
                    font-size: 24px;
                    font-weight: bold;
                    box-shadow: 0 0 30px rgba(0,188,212,0.5);
                    z-index: 9999;
                    text-align: center;
                    animation: fadeout 3s ease-in-out forwards;
                ">
                    ✅ Order Placed!
                </div>
                <script>
                    setTimeout(function(){
                        var popup = document.getElementById("popup");
                        if (popup) popup.style.display = "none";
                    }, 3000);
                </script>
                <style>
                    @keyframes fadeout {
                        0% {opacity: 1;}
                        80% {opacity: 1;}
                        100% {opacity: 0;}
                    }
                </style>
            """, unsafe_allow_html=True)

            del st.session_state.cart
            st.rerun()
        else:
            st.error("❌ Please select a payment method.")
else:
    st.info("🛍️ Your cart is empty.")

# -------------- Order History & Feedback --------------
st.subheader("📦 Your Orders")
found = False
for order in reversed(orders):
    if order["table"] == st.session_state.table_number:
        found = True
        status = order["status"]
        st.markdown(f"🕒 {order['timestamp']} — Status: {status} — Payment: {order.get('payment', 'N/A')}")

        for name, item in order["items"].items():
            st.markdown(f"{name} x {item['quantity']} = ₹{item['price'] * item['quantity']}")

        if status == "Completed":
            invoice_path = generate_invoice(order)
            st.success("✅ Order Completed! Download your invoice below:")
            with open(invoice_path, "rb") as f:
                st.download_button("📄 Download Invoice", data=f.read(), file_name=os.path.basename(invoice_path))

            # Show Feedback Form only after order is completed
            st.subheader("💬 Feedback")
            name = st.text_input("Your Name")
            rating = st.slider("How was your experience?", 1, 5, 3)
            message = st.text_area("Any comments or suggestions?")
            if st.button("📩 Submit Feedback"):
                if name and message:
                    feedback.append({
                        "table": st.session_state.table_number,
                        "name": name,
                        "rating": rating,
                        "message": message,
                        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    })
                    with open(FEEDBACK_FILE, "w", encoding="utf-8") as f:
                        json.dump(feedback, f, indent=2)
                    st.success("🎉 Thank you for your feedback!")
                else:
                    st.warning("Please enter both name and feedback.")

        if status == "Preparing" and "alerted" not in st.session_state:
            st.session_state.alerted = True
            st.audio("https://actions.google.com/sounds/v1/alarms/beep_short.ogg")

        st.markdown("---")

if not found:
    st.info("📭 No orders found.")
# -------------- Auto-refresh every 10 seconds --------------
with st.empty():
    time.sleep(10)
    st.rerun()
