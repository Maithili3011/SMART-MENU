import streamlit as st
import json
import os
from datetime import datetime
from streamlit_autorefresh import st_autorefresh
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from reportlab.lib import colors

# Auto-refresh every 5 seconds
st_autorefresh(interval=5000, key="admin_autorefresh")

# File paths
BASE_DIR = os.path.dirname(os.path.abspath(_file_))
ORDERS_FILE = os.path.join(BASE_DIR, "..", "orders.json")
MENU_FILE = os.path.join(BASE_DIR, "..", "menu.json")
FEEDBACK_FILE = os.path.join(BASE_DIR, "..", "feedback.json")

# Load JSON
def load_json(file_path):
    if os.path.exists(file_path):
        with open(file_path, "r") as f:
            return json.load(f)
    return []

# Save JSON
def save_json(file_path, data):
    with open(file_path, "w") as f:
        json.dump(data, f, indent=2)

# PDF Generator
def generate_invoice_pdf(order, save_dir="invoices"):
    os.makedirs(save_dir, exist_ok=True)
    filename = f"Invoice_Table{order['table']}{order['timestamp'].replace(':','-').replace(' ','')}.pdf"
    filepath = os.path.join(save_dir, filename)

    c = canvas.Canvas(filepath, pagesize=letter)
    width, height = letter
    margin = 50
    line_height = 20

    # Title Section
    c.setFont("Helvetica-Bold", 20)
    c.drawString(margin, height - 60, "📋 Customer Invoice")

    c.setFont("Helvetica", 12)
    c.drawString(margin, height - 90, "Café XYZ")  # Replace with your brand name
    c.drawString(margin, height - 105, "123 Main Street, City, Country")
    c.drawString(margin, height - 120, "Phone: +91-9876543210")

    # Invoice Details
    c.setFont("Helvetica-Bold", 12)
    c.drawString(margin, height - 160, f"Table No:")
    c.drawString(margin + 100, height - 160, f"{order['table']}")

    c.drawString(margin, height - 180, f"Date & Time:")
    c.drawString(margin + 100, height - 180, f"{order['timestamp']}")

    c.drawString(margin, height - 200, f"Payment Method:")
    c.drawString(margin + 100, height - 200, f"{order.get('payment', 'N/A')}")

    # Line separator
    c.setLineWidth(0.5)
    c.line(margin, height - 215, width - margin, height - 215)

    # Table Headers
    c.setFont("Helvetica-Bold", 12)
    y = height - 240
    c.drawString(margin, y, "Item")
    c.drawString(margin + 250, y, "Qty")
    c.drawString(margin + 300, y, "Price")
    c.drawString(margin + 370, y, "Subtotal")

    y -= line_height
    c.setLineWidth(0.3)
    c.line(margin, y + 10, width - margin, y + 10)

    # Table Content
    total = 0
    c.setFont("Helvetica", 11)

    for name, item in order["items"].items():
        qty = item["quantity"]
        price = item["price"]
        subtotal = qty * price
        total += subtotal

        c.drawString(margin, y, name)
        c.drawRightString(margin + 290, y, str(qty))
        c.drawRightString(margin + 360, y, f"₹{price}")
        c.drawRightString(margin + 440, y, f"₹{subtotal}")
        y -= line_height

        # Check for page overflow
        if y < 100:
            c.showPage()
            y = height - 60
            c.setFont("Helvetica", 11)

    # Line before total
    c.line(margin, y + 10, width - margin, y + 10)
    y -= 10

    # Total Amount
    c.setFont("Helvetica-Bold", 13)
    c.drawString(margin, y, "Total Amount")
    c.drawRightString(width - margin, y, f"₹{total}")

    # Footer
    y -= 40
    c.setFont("Helvetica-Oblique", 10)
    c.drawString(margin, y, "Thank you for dining with us!")
    y -= 15
    c.drawString(margin, y, "Visit Again - Café XYZ")

    c.showPage()
    c.save()

    return filepath

# Toast notification (new orders)
if 'last_order_count' not in st.session_state:
    st.session_state.last_order_count = 0

# App title
st.set_page_config(page_title="Admin Panel", layout="wide")
st.title("🛠️ Admin Panel")

# Load orders and menu
orders = load_json(ORDERS_FILE)
menu = load_json(MENU_FILE)

# Notify on new order
if len(orders) > st.session_state.last_order_count:
    st.toast("📥 New order received!", icon="✅")
st.session_state.last_order_count = len(orders)

# Display current orders
st.subheader("📦 Current Orders")

if not orders:
    st.info("No orders yet.")
else:
    for idx, order in enumerate(reversed(orders)):
        status = order.get("status", "Pending")
        if status != "Completed":
            table = order.get("table", "?")
            timestamp = order.get("timestamp", "N/A")
            items = order.get("items", {})
            payment_method = order.get("payment", "N/A")
            total = sum(details.get("price", 0) * details.get("quantity", 0) for details in items.values())

            with st.container():
                st.markdown(f"### 🪑 Table {table} - ⏳ {status}")
                st.caption(f"🕒 {timestamp}")
                st.markdown(f"💳 Payment Method: *{payment_method}*")
                if payment_method == "Cash":
                    st.markdown(f"<div style='color:yellow; font-weight:bold;'>⚠️ Customer will pay by CASH at Table {table}</div>", unsafe_allow_html=True)

                st.markdown("#### 🍽️ Ordered Items")
                for name, details in items.items():
                    qty = details.get("quantity", 0)
                    price = details.get("price", 0)
                    subtotal = price * qty
                    st.markdown(f"🔸 {name} x {qty} = ₹{subtotal}")

                st.markdown(f"*💰 Total: ₹{total}*")

                # Actions
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("✅ Mark as Completed", key=f"complete_{idx}"):
                        orders[len(orders) - 1 - idx]["status"] = "Completed"
                        save_json(ORDERS_FILE, orders)
                        st.success(f"Order from Table {table} marked as Completed")
                        st.rerun()

                with col2:
                    if st.button("🗑️ Delete", key=f"delete_{idx}"):
                        orders.pop(len(orders) - 1 - idx)
                        save_json(ORDERS_FILE, orders)
                        st.warning("Order deleted")
                        st.rerun()

# Divider
st.markdown("---")
st.subheader("📜 Order History (Completed Orders)")

# Completed orders
history_orders = [o for o in reversed(orders) if o.get("status") == "Completed"]
if not history_orders:
    st.info("No completed orders yet.")
else:
    for idx, order in enumerate(history_orders):
        table = order.get("table", "?")
        timestamp = order.get("timestamp", "N/A")
        items = order.get("items", {})
        payment_method = order.get("payment", "N/A")
        total = sum(details.get("price", 0) * details.get("quantity", 0) for details in items.values())

        with st.expander(f"🧾 Table {table} | {timestamp} | ₹{total}", expanded=False):
            st.markdown(f"💳 Payment Method: *{payment_method}*")

            for name, details in items.items():
                qty = details.get("quantity", 0)
                price = details.get("price", 0)
                subtotal = qty * price
                st.markdown(f"🔸 {name} x {qty} = ₹{subtotal}")

            st.markdown(f"*💰 Total: ₹{total}*")

            col1, col2 = st.columns(2)
            with col1:
                if st.button("🧾 Generate Invoice", key=f"invoice_{idx}"):
                    filepath = generate_invoice_pdf(order)
                    with open(filepath, "rb") as f:
                        st.download_button("📥 Download Invoice", data=f, file_name=os.path.basename(filepath), mime="application/pdf")

            with col2:
                if st.button("🗑️ Delete", key=f"delete_history_{idx}"):
                    orders.remove(order)
                    save_json(ORDERS_FILE, orders)
                    st.warning("🗑️ Order deleted from history")
                    st.rerun()

# Divider
st.markdown("---")
st.subheader("💬 Customer Feedback")

feedback = load_json(FEEDBACK_FILE)
if not feedback:
    st.info("No feedback received yet.")
else:
    for idx, fb in enumerate(reversed(feedback)):
        actual_index = len(feedback) - 1 - idx  # Index in the original list
        table = fb.get("table", "?")
        message = fb.get("message", "No message")
        rating = fb.get("rating", "N/A")
        time = fb.get("timestamp", "Unknown time")

        with st.chat_message("user"):
            st.markdown(f"*🪑 Table {table}* — 🕒 {time}")
            st.write(f"⭐ Rating: {rating}")
            st.write(f"💬 {message}")

            if st.button("🗑️ Delete Feedback", key=f"delete_feedback_{idx}"):
                feedback.pop(actual_index)
                save_json(FEEDBACK_FILE, feedback)
                st.warning("Feedback deleted.")
                st.rerun()
