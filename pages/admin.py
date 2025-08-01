import streamlit as st
from streamlit_autorefresh import st_autorefresh
from datetime import datetime
import os
import json
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

# Auto-refresh every 5 seconds
st_autorefresh(interval=5000, key="admin_autorefresh")

# File paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ORDERS_FILE = os.path.join(BASE_DIR, "..", "orders.json")

# Load orders
def load_json(filepath):
    if os.path.exists(filepath):
        with open(filepath, "r") as f:
            return json.load(f)
    return []

# Save orders
def save_json(filepath, data):
    with open(filepath, "w") as f:
        json.dump(data, f, indent=4)

# Generate invoice PDF
def generate_bill_pdf(order):
    output_dir = os.path.join(BASE_DIR, "..", "invoices")
    os.makedirs(output_dir, exist_ok=True)

    filename = f"invoice_table_{order['table']}_{datetime.now().strftime('%Y%m%d%H%M%S')}.pdf"
    path = os.path.join(output_dir, filename)

    c = canvas.Canvas(path, pagesize=letter)
    width, height = letter

    c.setFont("Helvetica-Bold", 16)
    c.drawString(200, 750, "Smart Table Invoice")

    c.setFont("Helvetica", 12)
    c.drawString(50, 720, f"Table: {order['table']}")
    c.drawString(300, 720, f"Date: {datetime.now().strftime('%d-%m-%Y %H:%M:%S')}")

    c.drawString(50, 690, "Items:")
    y = 670
    total = 0
    for name, details in order["items"].items():
        qty = details["quantity"]
        price = details["price"]
        subtotal = qty * price
        total += subtotal
        c.drawString(60, y, f"{name} x {qty} = ₹{subtotal}")
        y -= 20

    c.drawString(50, y - 10, f"Total: ₹{total}")
    c.drawString(50, y - 30, f"Payment Method: {order.get('payment', 'N/A')}")

    c.save()
    return path

# Load data
orders = load_json(ORDERS_FILE)

st.title("🧑‍🍳 Admin Panel – Smart Table Ordering System")

# Display orders
st.subheader("📦 Current Orders")

if not orders:
    st.info("No orders yet.")
else:
    for idx, order in enumerate(reversed(orders)):
        current_status = order.get("status", "Pending")
        if current_status != "Completed":
            table = order.get("table", "?")
            timestamp = order.get("timestamp", "N/A")
            items = order.get("items", {})
            payment_method = order.get("payment", "N/A")
            total = sum(details.get("price", 0) * details.get("quantity", 0) for details in items.values())

            with st.container():
                st.markdown(f"### 🪑 Table {table} - ⏳ Status: **{current_status}**")
                st.caption(f"🕒 {timestamp}")
                st.markdown(f"💳 Payment Method: **{payment_method}**")

                if payment_method == "Cash":
                    st.markdown(
                        f"<div style='color:orange; font-weight:bold;'>⚠️ Customer will pay by CASH at Table {table}</div>",
                        unsafe_allow_html=True
                    )

                st.markdown("#### 🍽️ Ordered Items")
                for name, details in items.items():
                    qty = details.get("quantity", 0)
                    price = details.get("price", 0)
                    subtotal = price * qty
                    st.markdown(f"🔸 {name} x {qty} = ₹{subtotal}")

                st.markdown(f"**💰 Total: ₹{total}**")

                col1, col2, col3 = st.columns(3)

                # 🔁 STATUS FLOW dropdown
                with col1:
                    status_options = ["Pending", "Preparing", "Ready", "Completed"]
                    if current_status not in status_options:
                        status_options.insert(0, current_status)

                    new_status = st.selectbox(
                        "Update Status",
                        status_options,
                        index=status_options.index(current_status),
                        key=f"status_{idx}"
                    )

                    if new_status != current_status:
                        orders[len(orders) - 1 - idx]["status"] = new_status
                        save_json(ORDERS_FILE, orders)
                        st.success(f"✅ Order from Table {table} updated to '{new_status}'")
                        st.rerun()

                # ✅ Mark as Completed & download invoice
                with col2:
                    if st.button("✅ Mark as Completed", key=f"complete_{idx}"):
                        orders[len(orders) - 1 - idx]["status"] = "Completed"
                        save_json(ORDERS_FILE, orders)

                        pdf_path = generate_bill_pdf(order)
                        st.success(f"🧾 Invoice generated for Table {table}")

                        with open(pdf_path, "rb") as f:
                            st.download_button(
                                label="⬇️ Download Invoice",
                                data=f,
                                file_name=os.path.basename(pdf_path),
                                mime="application/pdf",
                                key=f"download_{idx}"
                            )

                        st.rerun()

                # 🗑️ Delete
                with col3:
                    if st.button("🗑️ Delete", key=f"delete_{idx}"):
                        orders.pop(len(orders) - 1 - idx)
                        save_json(ORDERS_FILE, orders)
                        st.warning(f"🗑️ Order from Table {table} deleted")
                        st.rerun()
