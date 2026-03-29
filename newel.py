"""
Electricity Bill Management System
Full Python + Tkinter Application
Real SMTP email sending, OTP login, CSV storage

UPDATED FEATURES:
- Consumer login asks Category (Domestic/Commercial/Industrial)
- Tariff Change asks Category
- Bill generation includes Due Date
- Consumer can view generated bill full details
- Admin & Staff can view full request details
- Consumer request history and profile update added
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
import smtplib
import random
import csv
import os
import json
import hashlib
import webbrowser
from datetime import datetime, timedelta
import pandas as pd

from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


# ===================== CONFIG =====================

SENDER_EMAIL = "snithishkumar1401@gmail.com"
SENDER_APP_PASSWORD = "xwni awtj kozl sqaa"

DATA_FOLDER = "data"
UPLOAD_FOLDER = "uploads"
CONSUMER_DATA_FOLDER = "consumer_data"

USERS_FILE = os.path.join(DATA_FOLDER, "users.csv")
REQUESTS_FILE = os.path.join(DATA_FOLDER, "requests.csv")
STAFF_FILE = os.path.join(DATA_FOLDER, "staff.csv")
PAYMENTS_FILE = os.path.join(DATA_FOLDER, "payments.csv")
BILLS_FILE = os.path.join(DATA_FOLDER, "bills.csv")

ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"

TARIFF_RATES = {"LT": 6, "HT": 10}

UPI_MERCHANT_ID = "yourupi@okaxis"  # change to your upi id

CATEGORIES = ["Domestic", "Commercial", "Industrial"]

# ==================================================

if not os.path.exists(DATA_FOLDER):
    os.makedirs(DATA_FOLDER)

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

if not os.path.exists(CONSUMER_DATA_FOLDER):
    os.makedirs(CONSUMER_DATA_FOLDER)


# ===================== CREATE CSV FILES =====================

# Create users.csv (UPDATED: category included)
if not os.path.exists(USERS_FILE):
    with open(USERS_FILE, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "consumer_no", "name", "email", "phone", "address",
            "district", "category", "connection_type", "meter_no",
            "password_hash", "last_reading", "last_bill_date"
        ])

# Create requests.csv
if not os.path.exists(REQUESTS_FILE):
    with open(REQUESTS_FILE, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "request_id", "consumer_no", "consumer_email",
            "service_type", "details_json", "document_path",
            "department_email", "status",
            "assigned_staff_id", "assigned_staff_name", "assigned_staff_email",
            "payment_status", "payment_reference", "bill_amount",
            "created_time", "updated_time"
        ])

# Create staff.csv
if not os.path.exists(STAFF_FILE):
    with open(STAFF_FILE, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["staff_id", "role", "name", "email", "password"])

        writer.writerow(["S101", "JE", "JE Staff", "je@gmail.com", "1234"])
        writer.writerow(["S102", "Wireman", "Wireman Staff", "wireman@gmail.com", "1234"])
        writer.writerow(["S103", "Junior Engineer", "Junior Engineer Staff", "jreng@gmail.com", "1234"])
        writer.writerow(["S104", "Electrician", "Electrician Staff", "electrician@gmail.com", "1234"])

# Create payments.csv
if not os.path.exists(PAYMENTS_FILE):
    with open(PAYMENTS_FILE, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "payment_id", "bill_id", "consumer_email",
            "amount", "utr_no", "payment_time", "status"
        ])

# Create bills.csv (UPDATED: due_date added)
if not os.path.exists(BILLS_FILE):
    with open(BILLS_FILE, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "bill_id", "request_id", "consumer_email", "consumer_no",
            "category", "connection_type",
            "prev_reading", "curr_reading", "units", "rate",
            "amount", "generated_time", "due_date", "status"
        ])


# ===================== HELPERS =====================

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def generate_otp():
    return str(random.randint(100000, 999999))

def generate_consumer_no():
    return "C" + str(random.randint(10000000, 99999999))

def generate_request_id():
    return "REQ" + datetime.now().strftime("%Y%m%d%H%M%S")

def generate_payment_id():
    return "PMT" + datetime.now().strftime("%Y%m%d%H%M%S")

def generate_bill_id():
    return "BILL" + datetime.now().strftime("%Y%m%d%H%M%S")
def notify_consumer_status_update(request_id, new_status):
    df = load_requests()
    row = df[df["request_id"] == request_id]

    if len(row) == 0:
        return

    consumer_email = row.iloc[0]["consumer_email"]
    service_type = row.iloc[0]["service_type"]

    send_email(
        consumer_email,
        f"Request Status Updated ({request_id})",
        f"Hello,\n\nYour request status has been updated.\n\n"
        f"Request ID: {request_id}\n"
        f"Service Type: {service_type}\n"
        f"New Status: {new_status}\n\n"
        f"Thank you.\nEBMS Team"
    )

def send_email(receiver_email, subject, message):
    try:
        msg = MIMEMultipart()
        msg["From"] = SENDER_EMAIL
        msg["To"] = receiver_email
        msg["Subject"] = subject
        msg.attach(MIMEText(message, "plain"))

        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_APP_PASSWORD)
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        print("Email Error:", e)
        return False


def load_users():
    return pd.read_csv(USERS_FILE)

def save_users(df):
    df.to_csv(USERS_FILE, index=False)

def load_requests():
    return pd.read_csv(REQUESTS_FILE)

def save_requests(df):
    df.to_csv(REQUESTS_FILE, index=False)

def load_staff():
    return pd.read_csv(STAFF_FILE)

def load_payments():
    return pd.read_csv(PAYMENTS_FILE)

def load_bills():
    return pd.read_csv(BILLS_FILE)

def save_bills(df):
    df.to_csv(BILLS_FILE, index=False)

def format_details(details_json):
    try:
        d = json.loads(details_json)
        text = ""
        for k, v in d.items():
            text += f"{k}: {v}\n"
        return text
    except:
        return details_json


# ===================== CONSUMER PERSONAL CSV =====================

def save_consumer_personal_file(consumer_no, details_dict):
    file_path = os.path.join(CONSUMER_DATA_FOLDER, f"{consumer_no}.csv")

    if not os.path.exists(file_path):
        with open(file_path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["Field", "Value"])

    with open(file_path, "a", newline="") as f:
        writer = csv.writer(f)
        for k, v in details_dict.items():
            writer.writerow([k, v])


# ===================== SERVICES CONFIG =====================

SERVICES = {
    "Ownership Transfer": [
        ("Consumer Email", "text"),
        ("Old Owner Name", "text"),
        ("New Owner Name", "text"),
        ("New Address", "text"),
        ("Proof Document", "file")
    ],

    "New Connection": [
        ("Consumer Email", "text"),
        ("Applicant Name", "text"),
        ("Address", "text"),
        ("Connection Type (LT/HT)", "dropdown", ["LT", "HT"]),
        ("Document Proof", "file")
    ],

    "Unit Upgrade": [
        ("Consumer Email", "text"),
        ("Consumer Number", "text"),
        ("Required Units/Load", "text"),
        ("Reason", "text"),
        ("Document Proof", "file")
    ],

    "Meter Complaint": [
        ("Consumer Email", "text"),
        ("Complaint Description", "text")
    ],

    "Tariff Change": [
        ("Consumer Email", "text"),
        ("Consumer Number", "text"),
        ("Category", "dropdown", CATEGORIES),
        ("Current Tariff", "dropdown", ["LT", "HT"]),
        ("New Tariff", "dropdown", ["LT", "HT"]),
        ("Reason", "text"),
        ("Proof Document", "file")
    ],

    "Bill Payment": [
        ("Consumer Email", "text"),
        ("Consumer Number", "text"),
        ("Meter Number", "text"),
        ("Connection Type", "dropdown", ["LT", "HT"]),
        ("Current Reading", "text")
    ]
}


# ===================== REQUEST SUBMIT FUNCTION =====================

def submit_request(service_type, consumer_email, details_dict, document_path, dept_email):
    users = load_users()
    user_row = users[users["email"] == consumer_email]

    if len(user_row) == 0:
        return None

    consumer_no = user_row.iloc[0]["consumer_no"]

    request_id = generate_request_id()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    payment_status = "Not Applicable"
    payment_reference = "None"
    bill_amount = 0

    if service_type == "Bill Payment":
        payment_status = "Waiting Bill Generation"

    with open(REQUESTS_FILE, "a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            request_id, consumer_no, consumer_email,
            service_type, json.dumps(details_dict),
            document_path, dept_email,
            "Pending",
            "Not Assigned", "Not Assigned", "Not Assigned",
            payment_status, payment_reference, bill_amount,
            now, now
        ])

    save_consumer_personal_file(consumer_no, details_dict)

    send_email(dept_email,
               f"New Request: {service_type} ({request_id})",
               f"New request received.\n\nRequest ID: {request_id}\nConsumer Email: {consumer_email}\n\nDetails:\n{details_dict}")

    send_email(consumer_email,
               f"Request Submitted ({service_type})",
               f"Your request submitted successfully.\n\nRequest ID: {request_id}\nStatus: Pending\nPayment Status: {payment_status}")

    return request_id


# ===================== MAIN APP =====================

class ElectricityBillSystem(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("Electricity Bill Management System")
        self.geometry("1250x720")
        self.configure(bg="#eaf0ff")

        self.current_user = None
        self.current_role = None
        self.current_staff_role = None

        self.otp_store = {}
        self.selected_service = None
        self.selected_bill_id = None

        container = tk.Frame(self, bg="#eaf0ff")
        container.pack(fill="both", expand=True)

        self.frames = {}

        for F in (
            LoginPage, RegisterPage, OTPPage,
            ConsumerDashboard, ProfileUpdatePage, RequestHistoryPage,
            PaymentHistoryPage, BillHistoryPage, BillViewPage,
            ServiceFormPage, AdminDashboard, StaffDashboard, PayNowPage
        ):
            frame = F(container, self)
            self.frames[F.__name__] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        self.show_frame("LoginPage")

    def show_frame(self, page_name):
        frame = self.frames[page_name]
        frame.tkraise()

        if page_name == "RequestHistoryPage":
            frame.load_history()

        if page_name == "PaymentHistoryPage":
            frame.load_history()

        if page_name == "BillHistoryPage":
            frame.load_history()

        if page_name == "AdminDashboard":
            frame.load_requests()

        if page_name == "StaffDashboard":
            frame.load_requests()

        if page_name == "ProfileUpdatePage":
            frame.load_profile()

        if page_name == "PayNowPage":
            frame.load_pending_bill()

    def open_service_form(self, service_name):
        self.selected_service = service_name
        form_page = self.frames["ServiceFormPage"]
        form_page.load_form(service_name)
        self.show_frame("ServiceFormPage")

    def open_bill_view(self, bill_id):
        self.selected_bill_id = bill_id
        bill_page = self.frames["BillViewPage"]
        bill_page.load_bill(bill_id)
        self.show_frame("BillViewPage")


# ===================== LOGIN PAGE =====================

class LoginPage(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg="#eaf0ff")
        self.app = app

        tk.Label(self, text="⚡ Electricity Bill Management System",
                 font=("Arial", 26, "bold"), bg="#eaf0ff", fg="#003366").pack(pady=20)

        self.card = tk.Frame(self, bg="white", bd=2, relief="groove")
        self.card.pack(pady=20, padx=30)

        tk.Label(self.card, text="Login Panel", font=("Arial", 18, "bold"),
                 bg="white", fg="#003366").grid(row=0, column=0, columnspan=2, pady=15)

        tk.Label(self.card, text="Select Role:", font=("Arial", 12), bg="white").grid(row=1, column=0, padx=10, pady=10)

        self.role_var = tk.StringVar(value="Consumer")
        self.role_combo = ttk.Combobox(self.card, textvariable=self.role_var,
                                       values=["Consumer", "Admin", "Staff"],
                                       state="readonly", width=25)
        self.role_combo.grid(row=1, column=1, padx=10, pady=10)
        self.role_combo.bind("<<ComboboxSelected>>", self.update_fields)

        self.category_label = tk.Label(self.card, text="Category:", font=("Arial", 12), bg="white")
        self.category_var = tk.StringVar()
        self.category_combo = ttk.Combobox(self.card, textvariable=self.category_var,
                                           values=CATEGORIES, state="readonly", width=25)

        self.staff_role_label = tk.Label(self.card, text="Staff Role:", font=("Arial", 12), bg="white")
        self.staff_role_var = tk.StringVar()
        self.staff_role_combo = ttk.Combobox(self.card, textvariable=self.staff_role_var,
                                             values=["JE", "Wireman", "Junior Engineer", "Electrician"],
                                             state="readonly", width=25)

        self.user_label = tk.Label(self.card, text="Email / Username:", font=("Arial", 12), bg="white")
        self.user_label.grid(row=3, column=0, padx=10, pady=10)

        self.email_entry = tk.Entry(self.card, font=("Arial", 12), width=28)
        self.email_entry.grid(row=3, column=1, padx=10, pady=10)

        self.pass_label = tk.Label(self.card, text="Password:", font=("Arial", 12), bg="white")
        self.pass_entry = tk.Entry(self.card, font=("Arial", 12), width=28, show="*")

        self.pass_label.grid(row=4, column=0, padx=10, pady=10)
        self.pass_entry.grid(row=4, column=1, padx=10, pady=10)

        tk.Button(self.card, text="Login", font=("Arial", 12, "bold"),
                  bg="#007700", fg="white", width=18,
                  command=self.login).grid(row=6, column=0, columnspan=2, pady=15)

        tk.Button(self.card, text="New Consumer Registration", font=("Arial", 11, "bold"),
                  bg="#003399", fg="white", width=22,
                  command=lambda: app.show_frame("RegisterPage")).grid(row=7, column=0, columnspan=2, pady=10)

        self.update_fields()

    def update_fields(self, event=None):
        role = self.role_var.get()

        self.staff_role_label.grid_forget()
        self.staff_role_combo.grid_forget()
        self.category_label.grid_forget()
        self.category_combo.grid_forget()

        if role == "Consumer":
            self.pass_label.grid_forget()
            self.pass_entry.grid_forget()
            self.user_label.config(text="Consumer Email:")

            self.category_label.grid(row=2, column=0, padx=10, pady=10)
            self.category_combo.grid(row=2, column=1, padx=10, pady=10)
            self.category_combo.set(CATEGORIES[0])

        elif role == "Admin":
            self.pass_label.grid(row=4, column=0, padx=10, pady=10)
            self.pass_entry.grid(row=4, column=1, padx=10, pady=10)
            self.user_label.config(text="Admin Username:")

        elif role == "Staff":
            self.staff_role_label.grid(row=2, column=0, padx=10, pady=10)
            self.staff_role_combo.grid(row=2, column=1, padx=10, pady=10)
            self.pass_label.grid(row=4, column=0, padx=10, pady=10)
            self.pass_entry.grid(row=4, column=1, padx=10, pady=10)
            self.user_label.config(text="Staff Email:")

    def login(self):
        role = self.role_var.get()
        email_or_user = self.email_entry.get().strip()
        password = self.pass_entry.get().strip()
        staff_role = self.staff_role_var.get().strip()
        category = self.category_var.get().strip()

        if role == "Consumer":
            if email_or_user == "":
                messagebox.showerror("Error", "Enter consumer email.")
                return

            users = load_users()
            row = users[users["email"] == email_or_user]

            if len(row) == 0:
                messagebox.showerror("Error", "Consumer not registered.")
                return

            real_category = str(row.iloc[0]["category"]).strip()

            if category != real_category:
                messagebox.showerror("Error", f"Wrong Category! Registered Category is {real_category}")
                return

            otp = generate_otp()
            self.app.otp_store[email_or_user] = otp

            if send_email(email_or_user, "EBMS OTP Login", f"Your OTP is: {otp}"):
                self.app.current_user = email_or_user
                self.app.current_role = "Consumer"
                messagebox.showinfo("OTP Sent", "OTP sent successfully.")
                self.app.show_frame("OTPPage")
            else:
                messagebox.showerror("Error", "OTP sending failed.")

        elif role == "Admin":
            if email_or_user == ADMIN_USERNAME and password == ADMIN_PASSWORD:
                self.app.current_role = "Admin"
                self.app.current_user = "admin"
                messagebox.showinfo("Success", "Admin Login Successful")
                self.app.show_frame("AdminDashboard")
            else:
                messagebox.showerror("Error", "Invalid Admin credentials")

        elif role == "Staff":
            if staff_role == "":
                messagebox.showerror("Error", "Select Staff Role.")
                return

            staff_df = load_staff()

            match = staff_df[
                (staff_df["email"].astype(str).str.strip() == email_or_user) &
                (staff_df["password"].astype(str).str.strip() == password) &
                (staff_df["role"].astype(str).str.strip() == staff_role)
            ]

            if len(match) == 1:
                self.app.current_role = "Staff"
                self.app.current_user = email_or_user
                self.app.current_staff_role = staff_role
                messagebox.showinfo("Success", f"{staff_role} Login Successful")
                self.app.show_frame("StaffDashboard")
            else:
                messagebox.showerror("Error", "Invalid Staff credentials")


# ===================== REGISTER PAGE =====================

class RegisterPage(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg="#eaf0ff")
        self.app = app

        tk.Label(self, text="New Consumer Registration",
                 font=("Arial", 22, "bold"), bg="#eaf0ff", fg="#003366").pack(pady=20)

        self.card = tk.Frame(self, bg="white", bd=2, relief="groove")
        self.card.pack(pady=10, padx=30)

        self.entries = {}

        fields = [
            "Name", "Email", "Phone", "Address",
            "District", "Category",
            "Connection Type (LT/HT)",
            "Meter Number", "Password"
        ]

        for i, field in enumerate(fields):
            tk.Label(self.card, text=field, font=("Arial", 12), bg="white").grid(row=i, column=0, padx=10, pady=6, sticky="w")

            if field == "Connection Type (LT/HT)":
                entry = ttk.Combobox(self.card, values=["LT", "HT"], state="readonly", width=35)
                entry.set("LT")

            elif field == "Category":
                entry = ttk.Combobox(self.card, values=CATEGORIES, state="readonly", width=35)
                entry.set("Domestic")

            else:
                entry = tk.Entry(self.card, font=("Arial", 12), width=38)
                if field == "Password":
                    entry.config(show="*")

            entry.grid(row=i, column=1, padx=10, pady=6)
            self.entries[field] = entry

        tk.Button(self, text="Register", font=("Arial", 12, "bold"),
                  bg="#006600", fg="white", width=18,
                  command=self.register_user).pack(pady=15)

        tk.Button(self, text="Back to Login", font=("Arial", 11, "bold"),
                  bg="gray", fg="white", width=18,
                  command=lambda: app.show_frame("LoginPage")).pack()

    def register_user(self):
        name = self.entries["Name"].get().strip()
        email = self.entries["Email"].get().strip()
        phone = self.entries["Phone"].get().strip()
        address = self.entries["Address"].get().strip()
        district = self.entries["District"].get().strip()
        category = self.entries["Category"].get().strip()
        conn_type = self.entries["Connection Type (LT/HT)"].get().strip()
        meter_no = self.entries["Meter Number"].get().strip()
        password = self.entries["Password"].get().strip()

        if not all([name, email, phone, address, district, category, conn_type, meter_no, password]):
            messagebox.showerror("Error", "Fill all fields.")
            return

        users = load_users()
        if email in users["email"].values:
            messagebox.showerror("Error", "Email already registered.")
            return

        consumer_no = generate_consumer_no()
        while consumer_no in users["consumer_no"].values:
            consumer_no = generate_consumer_no()

        with open(USERS_FILE, "a", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([
                consumer_no, name, email, phone, address,
                district, category, conn_type, meter_no,
                hash_password(password),
                0, "None"
            ])

        save_consumer_personal_file(consumer_no, {
            "Name": name,
            "Email": email,
            "Phone": phone,
            "Address": address,
            "District": district,
            "Category": category,
            "Connection Type": conn_type,
            "Meter Number": meter_no
        })

        send_email(email, "Registration Successful",
                   f"Welcome to EBMS!\nYour Consumer Number: {consumer_no}")

        messagebox.showinfo("Success", f"Registration Successful!\nConsumer No: {consumer_no}")
        self.app.show_frame("LoginPage")


# ===================== OTP PAGE =====================

class OTPPage(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg="#eaf0ff")
        self.app = app

        tk.Label(self, text="OTP Verification",
                 font=("Arial", 22, "bold"), bg="#eaf0ff", fg="#003366").pack(pady=30)

        card = tk.Frame(self, bg="white", bd=2, relief="groove")
        card.pack(pady=10, padx=30)

        tk.Label(card, text="Enter OTP sent to your email:",
                 font=("Arial", 12), bg="white").pack(pady=10)

        self.otp_entry = tk.Entry(card, font=("Arial", 16), width=15)
        self.otp_entry.pack(pady=10)

        tk.Button(card, text="Verify OTP", font=("Arial", 12, "bold"),
                  bg="#006600", fg="white", width=15,
                  command=self.verify_otp).pack(pady=15)

    def verify_otp(self):
        email = self.app.current_user
        otp_entered = self.otp_entry.get().strip()

        if email in self.app.otp_store and self.app.otp_store[email] == otp_entered:
            messagebox.showinfo("Success", "OTP Verified Successfully!")
            self.app.show_frame("ConsumerDashboard")
        else:
            messagebox.showerror("Error", "Invalid OTP")


# ===================== CONSUMER DASHBOARD =====================

class ConsumerDashboard(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg="#eaf0ff")
        self.app = app

        tk.Label(self, text="👤 Consumer Dashboard",
                 font=("Arial", 22, "bold"), bg="#eaf0ff", fg="#003366").pack(pady=15)

        notebook = ttk.Notebook(self)
        notebook.pack(fill="both", expand=True, padx=20, pady=10)

        tab1 = tk.Frame(notebook, bg="white")
        tab2 = tk.Frame(notebook, bg="white")
        tab3 = tk.Frame(notebook, bg="white")

        notebook.add(tab1, text="Services")
        notebook.add(tab2, text="Payments")
        notebook.add(tab3, text="Account")

        tk.Label(tab1, text="Available Services",
                 font=("Arial", 16, "bold"), bg="white", fg="#003366").pack(pady=10)

        for service in SERVICES.keys():
            tk.Button(tab1, text=service, font=("Arial", 12, "bold"),
                      width=28, bg="#003399", fg="white",
                      command=lambda s=service: app.open_service_form(s)).pack(pady=6)

        tk.Label(tab2, text="Payment & Bill Options",
                 font=("Arial", 16, "bold"), bg="white", fg="#003366").pack(pady=10)

        tk.Button(tab2, text="Pay Generated Bill", font=("Arial", 12, "bold"),
                  width=25, bg="#007700", fg="white",
                  command=lambda: app.show_frame("PayNowPage")).pack(pady=8)

        tk.Button(tab2, text="Payment History", font=("Arial", 12, "bold"),
                  width=25, bg="#0066aa", fg="white",
                  command=lambda: app.show_frame("PaymentHistoryPage")).pack(pady=8)

        tk.Button(tab2, text="Bill History", font=("Arial", 12, "bold"),
                  width=25, bg="#aa5500", fg="white",
                  command=lambda: app.show_frame("BillHistoryPage")).pack(pady=8)

        tk.Label(tab3, text="Consumer Options",
                 font=("Arial", 16, "bold"), bg="white", fg="#003366").pack(pady=10)

        tk.Button(tab3, text="Update Profile", font=("Arial", 12, "bold"),
                  width=25, bg="#006600", fg="white",
                  command=lambda: app.show_frame("ProfileUpdatePage")).pack(pady=8)

        tk.Button(tab3, text="Request History", font=("Arial", 12, "bold"),
                  width=25, bg="#009966", fg="white",
                  command=lambda: app.show_frame("RequestHistoryPage")).pack(pady=8)

        tk.Button(self, text="Logout", font=("Arial", 12, "bold"),
                  width=20, bg="red", fg="white",
                  command=self.logout).pack(pady=12)

    def logout(self):
        self.app.current_user = None
        self.app.current_role = None
        self.app.show_frame("LoginPage")


# ===================== PROFILE UPDATE PAGE =====================

class ProfileUpdatePage(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg="#eaf0ff")
        self.app = app

        tk.Label(self, text="Update Consumer Profile",
                 font=("Arial", 22, "bold"), bg="#eaf0ff", fg="#003366").pack(pady=20)

        card = tk.Frame(self, bg="white", bd=2, relief="groove")
        card.pack(pady=10, padx=30)

        self.entries = {}
        fields = ["Name", "Phone", "Address", "District", "Category", "Connection Type", "Meter Number"]

        for i, field in enumerate(fields):
            tk.Label(card, text=field, font=("Arial", 12), bg="white").grid(row=i, column=0, padx=10, pady=8, sticky="w")

            if field == "Connection Type":
                entry = ttk.Combobox(card, values=["LT", "HT"], state="readonly", width=35)
            elif field == "Category":
                entry = ttk.Combobox(card, values=CATEGORIES, state="readonly", width=35)
            else:
                entry = tk.Entry(card, font=("Arial", 12), width=38)

            entry.grid(row=i, column=1, padx=10, pady=8)
            self.entries[field] = entry

        tk.Button(self, text="Update Profile", font=("Arial", 12, "bold"),
                  bg="#006600", fg="white", width=18,
                  command=self.update_profile).pack(pady=15)

        tk.Button(self, text="Back", font=("Arial", 11, "bold"),
                  bg="red", fg="white", width=15,
                  command=lambda: app.show_frame("ConsumerDashboard")).pack()

    def load_profile(self):
        users = load_users()
        row = users[users["email"] == self.app.current_user]

        if len(row) == 0:
            return

        user = row.iloc[0]

        self.entries["Name"].delete(0, tk.END)
        self.entries["Name"].insert(0, user["name"])

        self.entries["Phone"].delete(0, tk.END)
        self.entries["Phone"].insert(0, user["phone"])

        self.entries["Address"].delete(0, tk.END)
        self.entries["Address"].insert(0, user["address"])

        self.entries["District"].delete(0, tk.END)
        self.entries["District"].insert(0, user["district"])

        self.entries["Category"].set(user["category"])
        self.entries["Connection Type"].set(user["connection_type"])

        self.entries["Meter Number"].delete(0, tk.END)
        self.entries["Meter Number"].insert(0, user["meter_no"])

    def update_profile(self):
        name = self.entries["Name"].get().strip()
        phone = self.entries["Phone"].get().strip()
        address = self.entries["Address"].get().strip()
        district = self.entries["District"].get().strip()
        category = self.entries["Category"].get().strip()
        conn_type = self.entries["Connection Type"].get().strip()
        meter_no = self.entries["Meter Number"].get().strip()

        if not all([name, phone, address, district, category, conn_type, meter_no]):
            messagebox.showerror("Error", "Fill all fields.")
            return

        df = load_users()
        df.loc[df["email"] == self.app.current_user, "name"] = name
        df.loc[df["email"] == self.app.current_user, "phone"] = phone
        df.loc[df["email"] == self.app.current_user, "address"] = address
        df.loc[df["email"] == self.app.current_user, "district"] = district
        df.loc[df["email"] == self.app.current_user, "category"] = category
        df.loc[df["email"] == self.app.current_user, "connection_type"] = conn_type
        df.loc[df["email"] == self.app.current_user, "meter_no"] = meter_no

        save_users(df)

        send_email(self.app.current_user, "Profile Updated", "Your profile updated successfully.")
        messagebox.showinfo("Success", "Profile updated successfully.")
        self.app.show_frame("ConsumerDashboard")


# ===================== REQUEST HISTORY PAGE =====================

class RequestHistoryPage(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg="#eaf0ff")
        self.app = app

        tk.Label(self, text="📜 Request History",
                 font=("Arial", 20, "bold"), bg="#eaf0ff", fg="#003366").pack(pady=10)

        self.tree = ttk.Treeview(self, columns=("ID", "Service", "Status", "Staff", "Payment", "Updated"),
                                 show="headings", height=18)

        for col in ("ID", "Service", "Status", "Staff", "Payment", "Updated"):
            self.tree.heading(col, text=col)

        self.tree.pack(fill="both", expand=True, padx=20, pady=10)

        tk.Button(self, text="View Full Details", bg="#003399", fg="white",
                  font=("Arial", 11, "bold"),
                  command=self.view_details).pack(pady=5)

        tk.Button(self, text="Back", bg="red", fg="white",
                  font=("Arial", 11, "bold"),
                  command=lambda: app.show_frame("ConsumerDashboard")).pack(pady=10)

    def load_history(self):
        for row in self.tree.get_children():
            self.tree.delete(row)

        df = load_requests()
        user_reqs = df[df["consumer_email"] == self.app.current_user]

        for _, r in user_reqs.iterrows():
            staff_text = f"{r['assigned_staff_name']} ({r['assigned_staff_id']})"
            self.tree.insert("", tk.END, values=(
                r["request_id"], r["service_type"], r["status"],
                staff_text, r["payment_status"], r["updated_time"]
            ))

    def view_details(self):
        selected = self.tree.focus()
        if not selected:
            messagebox.showerror("Error", "Select a request first.")
            return

        rid = self.tree.item(selected, "values")[0]
        df = load_requests()
        row = df[df["request_id"] == rid]

        if len(row) == 0:
            return

        r = row.iloc[0]
        details_text = format_details(r["details_json"])

        msg = f"""
Request ID: {r["request_id"]}
Consumer Email: {r["consumer_email"]}
Service Type: {r["service_type"]}
Status: {r["status"]}

Assigned Staff ID: {r["assigned_staff_id"]}
Assigned Staff Name: {r["assigned_staff_name"]}
Assigned Staff Email: {r["assigned_staff_email"]}

Payment Status: {r["payment_status"]}
Bill Amount: {r["bill_amount"]}
Document: {r["document_path"]}

------ DETAILS ------
{details_text}
"""
        messagebox.showinfo("Request Full Details", msg)


# ===================== SERVICE FORM PAGE =====================

class ServiceFormPage(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg="#eaf0ff")
        self.app = app

        self.service_name = ""
        self.entries = {}
        self.doc_path = "No Document"

        self.title_label = tk.Label(self, text="", font=("Arial", 20, "bold"),
                                    bg="#eaf0ff", fg="#003366")
        self.title_label.pack(pady=15)

        self.card = tk.Frame(self, bg="white", bd=2, relief="groove")
        self.card.pack(pady=10, padx=30)

        self.form_frame = tk.Frame(self.card, bg="white")
        self.form_frame.pack(pady=15)

        tk.Label(self.card, text="Department Officer Email (Receiver):",
                 font=("Arial", 12, "bold"), bg="white").pack(pady=5)

        self.dept_email_entry = tk.Entry(self.card, font=("Arial", 12), width=40)
        self.dept_email_entry.pack(pady=5)

        tk.Button(self, text="Submit Request", font=("Arial", 12, "bold"),
                  bg="#006600", fg="white", width=20,
                  command=self.submit_request_form).pack(pady=12)

        tk.Button(self, text="Back", font=("Arial", 11, "bold"),
                  bg="red", fg="white", width=15,
                  command=lambda: app.show_frame("ConsumerDashboard")).pack(pady=10)

    def load_form(self, service_name):
        self.service_name = service_name
        self.title_label.config(text=f"📌 {service_name} Form")

        for widget in self.form_frame.winfo_children():
            widget.destroy()

        self.entries = {}
        self.doc_path = "No Document"

        fields = SERVICES[service_name]

        for field in fields:
            label = field[0]
            ftype = field[1]

            tk.Label(self.form_frame, text=label, font=("Arial", 12), bg="white").pack(pady=4)

            if ftype == "text":
                entry = tk.Entry(self.form_frame, font=("Arial", 12), width=45)
                entry.pack()
                self.entries[label] = entry

            elif ftype == "dropdown":
                options = field[2]
                entry = ttk.Combobox(self.form_frame, values=options, state="readonly", width=42)
                entry.set(options[0])
                entry.pack()
                self.entries[label] = entry

            elif ftype == "file":
                btn = tk.Button(self.form_frame, text="Upload File",
                                font=("Arial", 11, "bold"),
                                bg="gray", fg="white",
                                command=self.upload_doc)
                btn.pack(pady=5)
                self.entries[label] = "file"

    def upload_doc(self):
        file_path = filedialog.askopenfilename()
        if file_path:
            filename = os.path.basename(file_path)
            dest_path = os.path.join(UPLOAD_FOLDER, filename)

            with open(file_path, "rb") as src, open(dest_path, "wb") as dst:
                dst.write(src.read())

            self.doc_path = dest_path
            messagebox.showinfo("Uploaded", "Document uploaded successfully.")

    def submit_request_form(self):
        dept_email = self.dept_email_entry.get().strip()
        if dept_email == "":
            messagebox.showerror("Error", "Enter Department Officer Email.")
            return

        details = {}

        for key, widget in self.entries.items():
            if widget == "file":
                continue

            value = widget.get().strip()
            if value == "":
                messagebox.showerror("Error", f"Fill field: {key}")
                return

            details[key] = value

        consumer_email = details.get("Consumer Email", "").strip()
        if consumer_email == "":
            messagebox.showerror("Error", "Enter Consumer Email.")
            return

        users = load_users()

        if consumer_email not in users["email"].values:
            messagebox.showerror("Error", "Consumer email not registered.")
            return

        # BILL PAYMENT VALIDATION
        if self.service_name == "Bill Payment":
            entered_consumer_no = details.get("Consumer Number", "").strip()
            entered_meter_no = details.get("Meter Number", "").strip()

            row = users[users["email"] == consumer_email]
            real_consumer_no = str(row.iloc[0]["consumer_no"]).strip()
            real_meter_no = str(row.iloc[0]["meter_no"]).strip()

            if entered_consumer_no != real_consumer_no:
                messagebox.showerror("Error", "Invalid Consumer Number for this email!")
                return

            if entered_meter_no != real_meter_no:
                messagebox.showerror("Error", "Invalid Meter Number for this email!")
                return

            try:
                curr = float(details["Current Reading"])
                conn_type = details["Connection Type"]

                prev = float(row.iloc[0]["last_reading"])

                if curr < prev:
                    messagebox.showerror("Error", f"Current reading cannot be less than last reading ({prev}).")
                    return

                units = curr - prev
                rate = TARIFF_RATES.get(conn_type, 6)
                amount = units * rate

                details["Previous Reading (System)"] = prev
                details["Units Consumed"] = units
                details["Rate"] = rate
                details["Amount (Estimated)"] = amount

            except:
                messagebox.showerror("Error", "Enter valid numeric reading.")
                return

        rid = submit_request(self.service_name, consumer_email, details, self.doc_path, dept_email)

        if rid:
            messagebox.showinfo("Success", f"Request Submitted!\nRequest ID: {rid}")
            self.app.show_frame("ConsumerDashboard")
        else:
            messagebox.showerror("Error", "Submission failed.")


# ===================== PAY NOW PAGE =====================

class PayNowPage(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg="#eaf0ff")
        self.app = app
        self.selected_bill_id = None
        self.amount = 0

        tk.Label(self, text="💳 Pay Generated Bill",
                 font=("Arial", 22, "bold"), bg="#eaf0ff", fg="#003366").pack(pady=15)

        self.tree = ttk.Treeview(self, columns=("BillID", "Amount", "DueDate", "Status", "GeneratedTime"),
                                 show="headings", height=12)

        for col in ("BillID", "Amount", "DueDate", "Status", "GeneratedTime"):
            self.tree.heading(col, text=col)

        self.tree.pack(fill="x", padx=20, pady=10)

        btn_frame = tk.Frame(self, bg="#eaf0ff")
        btn_frame.pack(pady=10)

        tk.Button(btn_frame, text="Open UPI Link (GPay/Paytm)",
                  font=("Arial", 11, "bold"),
                  bg="#007700", fg="white",
                  command=self.open_upi_link).grid(row=0, column=0, padx=10)

        tk.Button(btn_frame, text="Submit UTR / Transaction ID",
                  font=("Arial", 11, "bold"),
                  bg="#003399", fg="white",
                  command=self.submit_utr).grid(row=0, column=1, padx=10)

        tk.Button(btn_frame, text="View Bill",
                  font=("Arial", 11, "bold"),
                  bg="#aa5500", fg="white",
                  command=self.view_bill).grid(row=0, column=2, padx=10)

        tk.Button(self, text="Back",
                  font=("Arial", 11, "bold"),
                  bg="red", fg="white",
                  command=lambda: app.show_frame("ConsumerDashboard")).pack(pady=10)

    def load_pending_bill(self):
        for row in self.tree.get_children():
            self.tree.delete(row)

        df = load_bills()
        user_df = df[
            (df["consumer_email"] == self.app.current_user) &
            (df["status"] == "Generated - Pay Now")
        ]

        for _, r in user_df.iterrows():
            self.tree.insert("", tk.END, values=(
                r["bill_id"], r["amount"], r["due_date"], r["status"], r["generated_time"]
            ))

    def open_upi_link(self):
        selected = self.tree.focus()
        if not selected:
            messagebox.showerror("Error", "Select a generated bill first.")
            return

        bill_id, amount, due_date, status, gen_time = self.tree.item(selected, "values")
        self.selected_bill_id = bill_id
        self.amount = amount

        upi_link = f"upi://pay?pa={UPI_MERCHANT_ID}&pn=EBMS&am={amount}&cu=INR&tn=BillPayment-{bill_id}"
        webbrowser.open(upi_link)

        messagebox.showinfo("UPI Opened",
                            "UPI payment link opened.\nPay using GPay/Paytm/PhonePe.\nAfter payment enter UTR.")

    def submit_utr(self):
        if not self.selected_bill_id:
            messagebox.showerror("Error", "Select bill and open payment first.")
            return

        utr = simpledialog.askstring("Enter UTR", "Enter Transaction ID / UTR Number:")
        if not utr:
            return

        payment_id = generate_payment_id()
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        bills_df = load_bills()
        bill_row = bills_df[bills_df["bill_id"] == self.selected_bill_id]

        if len(bill_row) == 0:
            messagebox.showerror("Error", "Bill not found.")
            return

        amount = float(bill_row.iloc[0]["amount"])
        consumer_email = bill_row.iloc[0]["consumer_email"]
        request_id = bill_row.iloc[0]["request_id"]
        curr_reading = float(bill_row.iloc[0]["curr_reading"])

        with open(PAYMENTS_FILE, "a", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([
                payment_id, self.selected_bill_id,
                consumer_email, amount,
                utr, now, "Paid"
            ])

        bills_df.loc[bills_df["bill_id"] == self.selected_bill_id, "status"] = "Paid"
        save_bills(bills_df)

        req_df = load_requests()
        req_df.loc[req_df["request_id"] == request_id, "payment_status"] = "Paid"
        req_df.loc[req_df["request_id"] == request_id, "status"] = "Completed"
        req_df.loc[req_df["request_id"] == request_id, "updated_time"] = now
        save_requests(req_df)

        users_df = load_users()
        users_df.loc[users_df["email"] == consumer_email, "last_reading"] = curr_reading
        users_df.loc[users_df["email"] == consumer_email, "last_bill_date"] = now
        save_users(users_df)

        send_email(consumer_email, "Bill Payment Successful",
                   f"Your bill {self.selected_bill_id} payment is successful.\nUTR: {utr}\nAmount: ₹{amount}")

        messagebox.showinfo("Success", "Payment successful! Bill marked as PAID.")
        self.load_pending_bill()

    def view_bill(self):
        selected = self.tree.focus()
        if not selected:
            messagebox.showerror("Error", "Select a bill first.")
            return

        bill_id = self.tree.item(selected, "values")[0]
        self.app.open_bill_view(bill_id)


# ===================== BILL VIEW PAGE =====================

class BillViewPage(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg="#eaf0ff")
        self.app = app

        tk.Label(self, text="🧾 Bill Full Details",
                 font=("Arial", 22, "bold"), bg="#eaf0ff", fg="#003366").pack(pady=15)

        self.text = tk.Text(self, font=("Arial", 12), width=95, height=25)
        self.text.pack(padx=20, pady=10)

        tk.Button(self, text="Back",
                  font=("Arial", 11, "bold"),
                  bg="red", fg="white",
                  command=lambda: app.show_frame("BillHistoryPage")).pack(pady=10)

    def load_bill(self, bill_id):
        df = load_bills()
        row = df[df["bill_id"] == bill_id]

        if len(row) == 0:
            messagebox.showerror("Error", "Bill not found.")
            return

        b = row.iloc[0]

        msg = f"""
==================== ELECTRICITY BILL ====================

Bill ID: {b["bill_id"]}
Request ID: {b["request_id"]}

Consumer Email: {b["consumer_email"]}
Consumer No: {b["consumer_no"]}
Category: {b["category"]}
Connection Type: {b["connection_type"]}

Previous Reading: {b["prev_reading"]}
Current Reading: {b["curr_reading"]}
Units Consumed: {b["units"]}
Rate per Unit: {b["rate"]}

Total Amount: ₹{b["amount"]}

Generated Date: {b["generated_time"]}
Due Date: {b["due_date"]}

Bill Status: {b["status"]}

==========================================================
"""
        self.text.delete("1.0", tk.END)
        self.text.insert(tk.END, msg)


# ===================== PAYMENT HISTORY PAGE =====================

class PaymentHistoryPage(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg="#eaf0ff")
        self.app = app

        tk.Label(self, text="📌 Payment History",
                 font=("Arial", 22, "bold"), bg="#eaf0ff", fg="#003366").pack(pady=10)

        self.tree = ttk.Treeview(self, columns=("PaymentID", "BillID", "Amount", "UTR", "Time", "Status"),
                                 show="headings", height=18)

        for col in ("PaymentID", "BillID", "Amount", "UTR", "Time", "Status"):
            self.tree.heading(col, text=col)

        self.tree.pack(fill="both", expand=True, padx=20, pady=10)

        tk.Button(self, text="Back", bg="red", fg="white",
                  font=("Arial", 11, "bold"),
                  command=lambda: app.show_frame("ConsumerDashboard")).pack(pady=10)

    def load_history(self):
        for row in self.tree.get_children():
            self.tree.delete(row)

        df = load_payments()
        user_df = df[df["consumer_email"] == self.app.current_user]

        for _, r in user_df.iterrows():
            self.tree.insert("", tk.END, values=(
                r["payment_id"], r["bill_id"], r["amount"],
                r["utr_no"], r["payment_time"], r["status"]
            ))


# ===================== BILL HISTORY PAGE =====================

class BillHistoryPage(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg="#eaf0ff")
        self.app = app

        tk.Label(self, text="🧾 Bill History",
                 font=("Arial", 22, "bold"), bg="#eaf0ff", fg="#003366").pack(pady=10)

        self.tree = ttk.Treeview(self, columns=("BillID", "Units", "Amount", "DueDate", "Status"),
                                 show="headings", height=18)

        for col in ("BillID", "Units", "Amount", "DueDate", "Status"):
            self.tree.heading(col, text=col)

        self.tree.pack(fill="both", expand=True, padx=20, pady=10)

        tk.Button(self, text="View Bill Full Details",
                  bg="#003399", fg="white",
                  font=("Arial", 11, "bold"),
                  command=self.view_bill).pack(pady=5)

        tk.Button(self, text="Back", bg="red", fg="white",
                  font=("Arial", 11, "bold"),
                  command=lambda: app.show_frame("ConsumerDashboard")).pack(pady=10)

    def load_history(self):
        for row in self.tree.get_children():
            self.tree.delete(row)

        df = load_bills()
        user_df = df[df["consumer_email"] == self.app.current_user]

        for _, r in user_df.iterrows():
            self.tree.insert("", tk.END, values=(
                r["bill_id"], r["units"], r["amount"], r["due_date"], r["status"]
            ))

    def view_bill(self):
        selected = self.tree.focus()
        if not selected:
            messagebox.showerror("Error", "Select a bill first.")
            return

        bill_id = self.tree.item(selected, "values")[0]
        self.app.open_bill_view(bill_id)


# ===================== ADMIN DASHBOARD =====================

class AdminDashboard(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg="#eaf0ff")
        self.app = app

        tk.Label(self, text="🏢 Admin / Officer Dashboard",
                 font=("Arial", 20, "bold"), bg="#eaf0ff", fg="#003366").pack(pady=10)

        self.tree = ttk.Treeview(self, columns=("ID", "Consumer", "Service", "Status", "Staff", "Payment", "Amount"),
                                 show="headings", height=18)

        for col in ("ID", "Consumer", "Service", "Status", "Staff", "Payment", "Amount"):
            self.tree.heading(col, text=col)

        self.tree.pack(fill="both", expand=True, padx=20, pady=10)

        btn_frame = tk.Frame(self, bg="#eaf0ff")
        btn_frame.pack(pady=10)

        tk.Button(btn_frame, text="Refresh", bg="green", fg="white",
                  font=("Arial", 11, "bold"),
                  command=self.load_requests).grid(row=0, column=0, padx=10)

        tk.Button(btn_frame, text="View Full Details", bg="#003399", fg="white",
                  font=("Arial", 11, "bold"),
                  command=self.view_details).grid(row=0, column=1, padx=10)
        
        

        tk.Button(btn_frame, text="Open Document", bg="#444444", fg="white",
                  font=("Arial", 11, "bold"),
                  command=self.open_document).grid(row=0, column=2, padx=10)

        tk.Button(btn_frame, text="Assign Staff", bg="#ff8800", fg="white",
                  font=("Arial", 11, "bold"),
                  command=self.assign_staff).grid(row=0, column=3, padx=10)

        tk.Button(btn_frame, text="Generate Bill (Approve)", bg="blue", fg="white",
                  font=("Arial", 11, "bold"),
                  command=self.approve_bill_payment).grid(row=0, column=4, padx=10)

        tk.Button(btn_frame, text="Reject Bill Payment", bg="red", fg="white",
                  font=("Arial", 11, "bold"),
                  command=self.reject_payment).grid(row=0, column=5, padx=10)

        tk.Button(self, text="Logout", bg="gray", fg="white",
                  font=("Arial", 11, "bold"),
                  command=self.logout).pack(pady=10)

    def load_requests(self):
        for row in self.tree.get_children():
            self.tree.delete(row)

        df = load_requests()

        for _, r in df.iterrows():
            staff_text = f"{r['assigned_staff_name']} ({r['assigned_staff_id']})"
            self.tree.insert("", tk.END, values=(
                r["request_id"], r["consumer_email"], r["service_type"],
                r["status"], staff_text, r["payment_status"], r["bill_amount"]
            ))

    def view_details(self):
        selected = self.tree.focus()
        if not selected:
            messagebox.showerror("Error", "Select a request first.")
            return

        rid = self.tree.item(selected, "values")[0]
        df = load_requests()
        row = df[df["request_id"] == rid]

        if len(row) == 0:
            return

        r = row.iloc[0]
        details_text = format_details(r["details_json"])

        msg = f"""
Request ID: {r["request_id"]}
Consumer Email: {r["consumer_email"]}
Service Type: {r["service_type"]}
Status: {r["status"]}

Assigned Staff ID: {r["assigned_staff_id"]}
Assigned Staff Name: {r["assigned_staff_name"]}
Assigned Staff Email: {r["assigned_staff_email"]}

Payment Status: {r["payment_status"]}
Bill Amount: {r["bill_amount"]}
Document: {r["document_path"]}
Department Email: {r["department_email"]}

------ DETAILS ------
{details_text}
"""
        messagebox.showinfo("Request Full Details", msg)

    def open_document(self):
        selected = self.tree.focus()
        if not selected:
            messagebox.showerror("Error", "Select a request first.")
            return

        rid = self.tree.item(selected, "values")[0]
        df = load_requests()
        row = df[df["request_id"] == rid]

        if len(row) == 0:
            return

        doc_path = row.iloc[0]["document_path"]

        if doc_path == "No Document" or not os.path.exists(doc_path):
            messagebox.showerror("Error", "Document not found!")
            return

        webbrowser.open(doc_path)

    def assign_staff(self):
        selected = self.tree.focus()
        if not selected:
            messagebox.showerror("Error", "Select a request.")
            return

        rid = self.tree.item(selected, "values")[0]

        staff_df = load_staff()

        staff_list = []
        for _, s in staff_df.iterrows():
            staff_list.append(f"{s['staff_id']} - {s['name']} - {s['role']} - {s['email']}")

        staff_choice = simpledialog.askstring("Assign Staff",
                                              "Enter Staff ID from below:\n\n" + "\n".join(staff_list))

        if not staff_choice:
            return

        staff_choice = staff_choice.strip()

        staff_row = staff_df[staff_df["staff_id"].astype(str).str.strip() == staff_choice]

        if len(staff_row) == 0:
            messagebox.showerror("Error", "Invalid Staff ID!")
            return

        staff_id = staff_row.iloc[0]["staff_id"]
        staff_name = staff_row.iloc[0]["name"]
        staff_email = staff_row.iloc[0]["email"]

        df = load_requests()
        df.loc[df["request_id"] == rid, "assigned_staff_id"] = staff_id
        df.loc[df["request_id"] == rid, "assigned_staff_name"] = staff_name
        df.loc[df["request_id"] == rid, "assigned_staff_email"] = staff_email
        df.loc[df["request_id"] == rid, "status"] = "Assigned"
        df.loc[df["request_id"] == rid, "updated_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        save_requests(df)

        send_email(staff_email, "New Request Assigned",
                   f"Request {rid} has been assigned to you.\nPlease login to staff dashboard.")

        messagebox.showinfo("Success", f"Request {rid} assigned to {staff_name} ({staff_id})")
        self.load_requests()

    def approve_bill_payment(self):
        selected = self.tree.focus()
        if not selected:
            messagebox.showerror("Error", "Select a request.")
            return

        values = self.tree.item(selected, "values")
        request_id = values[0]
        service_type = values[2]
        consumer_email = values[1]

        if service_type != "Bill Payment":
            messagebox.showerror("Error", "Only Bill Payment can be processed here.")
            return

        req_df = load_requests()
        row = req_df[req_df["request_id"] == request_id]

        if len(row) == 0:
            return

        details = json.loads(row.iloc[0]["details_json"])

        try:
            curr_reading = float(details.get("Current Reading", 0))
        except:
            messagebox.showerror("Error", "Invalid current reading in request.")
            return

        users_df = load_users()
        user_row = users_df[users_df["email"] == consumer_email]

        if len(user_row) == 0:
            messagebox.showerror("Error", "Consumer not found.")
            return

        prev_reading = float(user_row.iloc[0]["last_reading"])
        conn_type = user_row.iloc[0]["connection_type"]
        category = user_row.iloc[0]["category"]

        units = curr_reading - prev_reading
        rate = TARIFF_RATES.get(conn_type, 6)
        amount = units * rate

        bill_id = generate_bill_id()
        gen_time = datetime.now()
        due_date = (gen_time + timedelta(days=15)).strftime("%Y-%m-%d")

        with open(BILLS_FILE, "a", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([
                bill_id, request_id, consumer_email, user_row.iloc[0]["consumer_no"],
                category, conn_type,
                prev_reading, curr_reading, units, rate,
                amount, gen_time.strftime("%Y-%m-%d %H:%M:%S"),
                due_date, "Generated - Pay Now"
            ])

        req_df.loc[req_df["request_id"] == request_id, "payment_status"] = "Bill Generated"
        req_df.loc[req_df["request_id"] == request_id, "bill_amount"] = amount
        req_df.loc[req_df["request_id"] == request_id, "status"] = "Approved"
        req_df.loc[req_df["request_id"] == request_id, "updated_time"] = gen_time.strftime("%Y-%m-%d %H:%M:%S")
        save_requests(req_df)

        send_email(consumer_email, "Bill Generated - Pay Now",
                   f"Your electricity bill has been generated.\n\n"
                   f"Bill ID: {bill_id}\n"
                   f"Due Date: {due_date}\n"
                   f"Units: {units}\n"
                   f"Amount: ₹{amount}\n\n"
                   f"Login and go to Bill History to view full bill.")

        messagebox.showinfo("Success", f"Bill Generated!\nBill ID: {bill_id}\nDue Date: {due_date}")
        self.load_requests()

    def reject_payment(self):
        selected = self.tree.focus()
        if not selected:
            messagebox.showerror("Error", "Select a request.")
            return

        values = self.tree.item(selected, "values")
        request_id = values[0]
        consumer_email = values[1]

        df = load_requests()
        df.loc[df["request_id"] == request_id, "payment_status"] = "Rejected"
        df.loc[df["request_id"] == request_id, "status"] = "Rejected"
        df.loc[df["request_id"] == request_id, "updated_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        save_requests(df)

        send_email(consumer_email, "Bill Payment Rejected",
                   f"Your Bill Payment Request {request_id} has been rejected.\nPlease contact office.")

        messagebox.showinfo("Success", "Bill Payment Rejected.")
        self.load_requests()

    def logout(self):
        self.app.current_user = None
        self.app.current_role = None
        self.app.show_frame("LoginPage")


# ===================== STAFF DASHBOARD =====================

class StaffDashboard(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg="#eaf0ff")
        self.app = app

        tk.Label(self, text="👷 Staff Dashboard",
                 font=("Arial", 20, "bold"), bg="#eaf0ff", fg="#003366").pack(pady=10)

        self.tree = ttk.Treeview(self, columns=("ID", "Consumer", "Service", "Status"),
                                 show="headings", height=18)

        for col in ("ID", "Consumer", "Service", "Status"):
            self.tree.heading(col, text=col)

        self.tree.pack(fill="both", expand=True, padx=20, pady=10)

        btn_frame = tk.Frame(self, bg="#eaf0ff")
        btn_frame.pack(pady=10)

        tk.Button(btn_frame, text="Refresh", bg="green", fg="white",
                  font=("Arial", 11, "bold"),
                  command=self.load_requests).grid(row=0, column=0, padx=10)

        tk.Button(btn_frame, text="View Full Details", bg="#003399", fg="white",
                  font=("Arial", 11, "bold"),
                  command=self.view_details).grid(row=0, column=1, padx=10)
        
        tk.Button(btn_frame, text="Update Status", bg="#ff8800", fg="white",
                  font=("Arial", 11, "bold"),
                  command=self.update_status).grid(row=0, column=2, padx=10)

        tk.Button(self, text="Logout", bg="red", fg="white",
                  font=("Arial", 11, "bold"),
                  command=self.logout).pack(pady=10)

    def load_requests(self):
        for row in self.tree.get_children():
            self.tree.delete(row)

        df = load_requests()
        df = df[df["assigned_staff_email"].astype(str).str.strip() == self.app.current_user.strip()]

        for _, r in df.iterrows():
            self.tree.insert("", tk.END, values=(
                r["request_id"], r["consumer_email"], r["service_type"], r["status"]
            ))

    def view_details(self):
        selected = self.tree.focus()
        if not selected:
            messagebox.showerror("Error", "Select a request first.")
            return

        rid = self.tree.item(selected, "values")[0]
        df = load_requests()
        row = df[df["request_id"] == rid]

        if len(row) == 0:
            return

        r = row.iloc[0]
        details_text = format_details(r["details_json"])

        msg = f"""
Request ID: {r["request_id"]}
Consumer Email: {r["consumer_email"]}
Service Type: {r["service_type"]}
Status: {r["status"]}

Assigned Staff ID: {r["assigned_staff_id"]}
Assigned Staff Name: {r["assigned_staff_name"]}
Assigned Staff Email: {r["assigned_staff_email"]}

Document: {r["document_path"]}

------ DETAILS ------
{details_text}
"""
        messagebox.showinfo("Request Full Details", msg)
    def update_status(self):
        selected = self.tree.focus()
        if not selected:
            messagebox.showerror("Error", "Select a request first.")
            return

        rid = self.tree.item(selected, "values")[0]

        new_status = simpledialog.askstring(
            "Update Status",
            "Enter new status (Example: In Progress / Completed / Rejected):"
        )

        if not new_status:
            return

        new_status = new_status.strip()

        df = load_requests()

        if rid not in df["request_id"].values:
            messagebox.showerror("Error", "Request not found.")
            return

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        df.loc[df["request_id"] == rid, "status"] = new_status
        df.loc[df["request_id"] == rid, "updated_time"] = now

        save_requests(df)

        notify_consumer_status_update(rid, new_status)

        messagebox.showinfo("Success", f"Status updated to: {new_status}\nConsumer notified by email.")
        self.load_requests()   
    

    def logout(self):
        self.app.current_user = None
        self.app.current_role = None
        self.app.show_frame("LoginPage")


# ===================== RUN APP =====================

if __name__ == "__main__":
    app = ElectricityBillSystem()
    app.mainloop()