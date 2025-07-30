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
        .css-1aumxhk {padding-top: 1rem;}
        .stButton > button {
            padding: 0.2rem 0.5rem;
            font-size: 0.75rem;
            height: 2rem;
            border-radius: 6px;
            background-color: #a8dadc !important;
            color: #1d3557 !important;
        }
        .stDownloadButton > button {
            background-color: #457b9d !important;
            color: white !important;
            font-weight: bold;
            padding: 0.3rem 0.6rem;
            font-size: 0.8rem;
            height: 2.2rem;
            border-radius: 6px;
        }
    </style>
""", unsafe_allow_html=True)

# -------------- Paths --------------
BASE_DIR = os.path.dirname(os.path.abspath(_file_))
MENU_FILE = os.path.join(BASE_DIR, "menu.json")
ORDERS_FILE = os.path.join(BASE_DIR, "orders.json")
FEEDBACK_FILE = os.path.join(BASE_DIR, "feedback.json")
PAYMENT_FILE = os.path.join(BASE_DIR, "payments.json")
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

    if os.path.exists(QR_IMAGE):
        pdf.image(QR_IMAGE, x=10, y=pdf.get_y(), w=40)

    invoice_path = os.path.join(BASE_DIR, f"invoice_table_{order['table']}.pdf")
    pdf.output(invoice_path)
    return invoice_path

# -------------- Load Data --------------
menu = json.load(open(MENU_FILE)) if os.path.exists(MENU_FILE) else {}
orders = json.load(open(ORDERS_FILE)) if os.path.exists(ORDERS_FILE) else []
feedback = json.load(open(FEEDBACK_FILE)) if os.path.exists(FEEDBACK_FILE) else []
payments = json.load(open(PAYMENT_FILE)) if os.path.exists(PAYMENT_FILE) else []

# -------------- Table Number Session --------------
if "table_number" not in st.session_state:
    st.title("🍽️ Smart Table Ordering System")
    table_number = st.text_input("🔢 Enter your Table Number")
    if table_number:
        st.session_state.table_number = table_number
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
                st.markdown(f"*{item['name']}* — ₹{item['price']}")
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
            st.markdown(f"*{name}* x {item['quantity']} = ₹{subtotal}")
        with col2:
            if st.button("➖", key=f"dec-{name}"):
                st.session_state.cart[name]["quantity"] -= 1
                if st.session_state.cart[name]["quantity"] <= 0:
                    del st.session_state.cart[name]
                st.rerun()

    st.markdown(f"### 🧾 Total: ₹{total}")

    if st.button("✅ Place Order"):
        orders = [o for o in orders if o["table"] != st.session_state.table_number]
        new_order = {
            "table": st.session_state.table_number,
            "items": st.session_state.cart,
            "status": "pending",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        orders.append(new_order)
        with open(ORDERS_FILE, "w", encoding="utf-8") as f:
            json.dump(orders, f, indent=2)
        st.success("✅ Order Placed!")
        del st.session_state.cart
        st.rerun()
else:
    st.info("🛍️ Your cart is empty.")

# -------------- Order History, Invoice, Payment, Feedback --------------
st.subheader("📦 Your Orders")
feedback_given = False
found = False

for order in reversed(orders):
    if order["table"] == st.session_state.table_number:
        found = True
        status = order["status"]
        st.markdown(f"🕒 {order['timestamp']} — *Status:* {status}")

        for name, item in order["items"].items():
            st.markdown(f"{name} x {item['quantity']} = ₹{item['price'] * item['quantity']}")

        if status == "Completed":
            invoice_path = generate_invoice(order)
            st.success("✅ Order Completed! Download your invoice below:")
            with open(invoice_path, "rb") as f:
                st.download_button("📄 Download Invoice", data=f.read(), file_name=os.path.basename(invoice_path))

            # 🔻 Payment Method Selection
            table_payment = next((p for p in payments if p["table"] == order["table"] and p["timestamp"] == order["timestamp"]), None)

            if not table_payment:
                st.subheader("💳 Select Payment Method")
                payment_option = st.radio("Choose a payment method:", ["Cash", "Card", "Online"])
                if st.button("💰 Confirm Payment"):
                    payments.append({
                        "table": order["table"],
                        "method": payment_option,
                        "timestamp": order["timestamp"]
                    })
                    with open(PAYMENT_FILE, "w", encoding="utf-8") as f:
                        json.dump(payments, f, indent=2)
                    st.success(f"✅ Payment method '{payment_option}' selected for Table {order['table']}")
                    st.balloons()
                    st.rerun()
            else:
                st.info(f"✅ Payment method *{table_payment['method']}* already submitted for Table {order['table']}")

            # 💬 Feedback Section
            st.markdown("---")
            st.markdown("""
                <div style="background-color:#f1faee; padding:20px; border-radius:10px; border:1px solid #a8dadc; box-shadow:2px 2px 8px rgba(0,0,0,0.1);">
                    <h4 style="color:#1d3557;">💬 We'd love your feedback!</h4>
                </div>
            """, unsafe_allow_html=True)

            with st.form("feedback_form"):
                col1, col2 = st.columns([2, 1])
                with col1:
                    name = st.text_input("👤 Your Name", key="fb_name")
                    message = st.text_area("✏️ Comments or Suggestions", key="fb_message", height=100)
                with col2:
                    rating = st.slider("⭐ Rating", 1, 5, 3, key="fb_rating")
                    st.markdown(f"<p style='margin-top: 20px;'>Rate from 1 (Poor) to 5 (Excellent)</p>", unsafe_allow_html=True)

                submitted = st.form_submit_button("📩 Submit Feedback")
                if submitted:
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
                        st.warning("Please enter both your name and a comment.")

        elif status == "Preparing" and "alerted" not in st.session_state:
            st.session_state.alerted = True
            st.audio("https://actions.google.com/sounds/v1/alarms/beep_short.ogg")

        st.markdown("---")

if not found:
    st.info("📭 No orders found.")

# -------------- Auto-refresh every 10 seconds --------------
with st.empty():
    time.sleep(10)
    st.rerun()
