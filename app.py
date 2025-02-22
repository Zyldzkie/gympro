import os
import random
from flask import (
    Flask,
    render_template,
    redirect,
    url_for,
    request,
    flash,
    session,
    jsonify,
)
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
from datetime import datetime
from sqlalchemy import text
from flask import request
import dateutil.parser
from flask import render_template, request, session
from sqlalchemy.orm import joinedload
from datetime import date
from datetime import timedelta
from calendar import monthcalendar
from collections import defaultdict
from datetime import datetime, timedelta




app = Flask(__name__)

app.config["SQLALCHEMY_DATABASE_URI"] = "mysql+mysqlconnector://root@localhost/gympro"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SECRET_KEY"] = "your_secret_key"
app.config["UPLOAD_FOLDER"] = "static/images"
APP_ROOT = os.path.dirname(os.path.abspath(__file__))
STATIC_FOLDER = os.path.join(APP_ROOT, "static")

db = SQLAlchemy(app)


class Feedback(db.Model):
    __tablename__ = "feedback"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    message = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User", backref="feedbacks", lazy=True)


class User(db.Model):
    __tablename__ = "user"
    id = db.Column(db.Integer, primary_key=True)
    firstname = db.Column(db.String(50))
    lastname = db.Column(db.String(50))
    email = db.Column(db.String(20), unique=True)
    password = db.Column(db.String(255))
    date_of_birth = db.Column(db.Date)
    gender = db.Column(db.String(10))
    contact_number = db.Column(db.String(15))
    role = db.Column(db.String(20), default="user")
    membership_status = db.Column(db.String(50), default="active")
    next_appointment = db.Column(db.DateTime)


class Notification(db.Model):
    __tablename__ = "notifications"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    message = db.Column(db.String(255), nullable=False)
    seen = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User", backref="notifications")


class Member(db.Model):
    __tablename__ = "members"
    id = db.Column(db.Integer, primary_key=True)
    id_number = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    status = db.Column(db.String(20), nullable=False)


class Appointment(db.Model):
    __tablename__ = "appointments"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    date = db.Column(db.DateTime, nullable=False)


class EquipmentBorrowing(db.Model):
    __tablename__ = "equipment_borrowing"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    equipment_id = db.Column(db.Integer, db.ForeignKey("inventory.id"), nullable=False)
    borrow_date = db.Column(db.DateTime, default=datetime.utcnow)
    return_date = db.Column(db.DateTime)
    status = db.Column(db.Integer, nullable=False, default="approve")

    inventory = db.relationship("Inventory", backref="borrowings")


class Inventory(db.Model):
    __tablename__ = "inventory"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False)
    condition = db.Column(db.String(50), nullable=False)
    quantity = db.Column(db.Integer, default=0)
    image = db.Column(db.String(255), nullable=True)
    added_date = db.Column(db.DateTime, default=datetime.utcnow)


from datetime import datetime


def serialize_booking(booking):
    return {
        "member_name": booking.member_name,
        "contact_number": booking.contact_number,
        "appointment_date": booking.appointment_date.strftime("%Y-%m-%d"),
        "appointment_time": booking.appointment_time.strftime("%H:%M:%S"),
        "message": booking.message,
        "status": booking.status,
    }


@app.route("/deletebooking", methods=["POST"])
def delete_booking():
    booking_id = request.form.get("id")

    booking = Booking.query.get(booking_id)

    if booking:

        db.session.delete(booking)
        db.session.commit()
        return (
            jsonify({"message": "Booking deleted successfully!", "id": booking_id}),
            200,
        )
    else:
        return jsonify({"message": "Booking not found!", "id": booking_id}), 404


class Booking(db.Model):
    __tablename__ = "booking"

    id = db.Column(db.Integer, primary_key=True)
    member_name = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    contact_number = db.Column(db.String(20), nullable=False)
    appointment_date = db.Column(db.Date, nullable=False)
    appointment_time = db.Column(db.Time, nullable=False)
    message = db.Column(db.Text)
    status = db.Column(db.String(20), default="approve")

    user = db.relationship("User", backref="bookings")


class Equipment(db.Model):
    __tablename__ = "equipment"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False)
    quantity = db.Column(db.Integer, default=0)
    status = db.Column(db.String(50), default="available")


def __repr__(self):
    return f"<Equipment {self.name}>"


@app.route("/home")
def home():
    return render_template("home.html")


@app.route("/about")
def about():
    return render_template("about-us-01.html")


@app.route("/contact")
def contact():
    return render_template("contact-us.html")


@app.route("/book_now")
def book_now():
    if "user_id" not in session:
        return redirect(url_for("login"))
    return render_template("book_now.html")


@app.route("/contact_support")
def contact_support():
    return render_template("contact_support.html")


@app.route("/")
def landing():
    return render_template("index.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        user = User.query.filter_by(email=email).first()

        if user:
            if user.membership_status != "active":
                flash(
                    "Account not yet verified. Please verify your account before logging in.",
                    "warning",
                )
                return redirect(url_for("login"))

            if user.password == password:
                session["user_id"] = user.id
                session["username"] = f"{user.firstname} {user.lastname}"
                session["role"] = user.role
                flash("Login successful!", "success")
                return redirect(url_for("dashboard"))
            else:
                flash("Invalid credentials, please try again.", "danger")
        else:
            flash("User not found.", "danger")

    return render_template("login2.html")


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        try:
            firstname = request.form["first_name"]
            lastname = request.form["last_name"]
            email = request.form["email"]
            password = request.form["password"]
            date_of_birth = request.form["date_of_birth"]
            gender = request.form["gender"]
            contact_number = request.form["contact_no"]

            existing_user = User.query.filter_by(email=email).first()
            if existing_user:
                flash(
                    "The email already exists. Please double-check before signing in.",
                    "danger",
                )
                return render_template("signup2.html")

            new_user = User(
                firstname=firstname,
                lastname=lastname,
                email=email,
                password=password,
                date_of_birth=date_of_birth,
                gender=gender,
                contact_number=contact_number,
                role="user",
                membership_status="inactive",
            )

            db.session.add(new_user)
            db.session.commit()
            flash("Account created successfully!", "success")

            otp = str(random.randint(100000, 999999))
            session["otp"] = otp
            session["email"] = email

            if not send_otp_email(email, otp):
                flash("Failed to send OTP email. Please try again or contact support.", "danger")
                return redirect(url_for("signup"))

            return redirect(url_for("otp"))

        except Exception as e:
            db.session.rollback()
            flash(f"An error occurred: {e}", "danger")

    return render_template("signup2.html")


def send_otp_email(email, otp):
    try:
        import smtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart

        # Email settings
        sender_email = "ktrnexus@gmail.com"
        sender_password = "notq jweu novy lefk"  # Use environment variable in production
        
        # Create message
        message = MIMEMultipart()
        message["From"] = sender_email
        message["To"] = email
        message["Subject"] = "GymPro - OTP Verification"

        # Create HTML body
        html = f"""
        <html>
            <body>
                <h2>GymPro Account Verification</h2>
                <p>Your One-Time Password (OTP) is: <strong>{otp}</strong></p>
                <p>This OTP will expire in 10 minutes.</p>
                <p>If you did not request this OTP, please ignore this email.</p>
            </body>
        </html>
        """
        
        # Attach HTML content
        message.attach(MIMEText(html, "html"))

        # Try Gmail first
        try:
            with smtplib.SMTP("smtp.gmail.com", 587) as server:
                server.starttls()
                server.login(sender_email, sender_password)
                server.send_message(message)
                return True
                
        except Exception as gmail_error:
            print(f"Gmail error: {gmail_error}")
            
            # Try Outlook as fallback
            try:
                with smtplib.SMTP("smtp-mail.outlook.com", 587) as server:
                    server.starttls()
                    server.login(sender_email, sender_password)
                    server.send_message(message)
                    return True
                    
            except Exception as outlook_error:
                print(f"Outlook error: {outlook_error}")
                
                # Try generic SMTP as last resort
                try:
                    with smtplib.SMTP("smtp.mail.yahoo.com", 587) as server:
                        server.starttls()
                        server.login(sender_email, sender_password)
                        server.send_message(message)
                        return True
                        
                except Exception as yahoo_error:
                    print(f"Yahoo error: {yahoo_error}")
                    raise Exception("Failed to send email through all providers")

    except Exception as e:
        print(f"Failed to send OTP email: {e}")
        return False


@app.route("/otp", methods=["GET", "POST"])
def otp():
    if request.method == "POST":
        entered_otp = request.form["otp"]

        if entered_otp == session.get("otp"):
            try:
                email = session.get("email")

                user = User.query.filter_by(email=email).first()
                if user:
                    user.membership_status = "active"
                    db.session.commit()

                flash("OTP verified successfully!", "success")
                return redirect(url_for("login"))
            except Exception as e:
                db.session.rollback()
                flash(
                    f"An error occurred while updating membership status: {e}", "danger"
                )
        else:
            flash("Invalid OTP, please try again.", "danger")
            

    return render_template("otp.html")


@app.route("/returnitem", methods=["POST"])
def returnitem():
    borrowing_id = request.form.get("id")
    is_cancel = request.form.get("cancel") == "true"
    
    borrowing = EquipmentBorrowing.query.get(borrowing_id)
    
    if borrowing:
        equipment = Inventory.query.get(borrowing.equipment_id)
        if equipment:
            if is_cancel:
                borrowing.status = "cancelled"
            else:
                borrowing.status = "returned"
            borrowing.return_date = datetime.utcnow()
            
            # Increment the equipment quantity
            equipment.quantity += 1
            
            try:
                db.session.commit()
                return jsonify({
                    "success": True,
                    "message": "Equipment returned successfully",
                    "equipment_id": equipment.id,
                    "new_quantity": equipment.quantity
                })
            except Exception as e:
                db.session.rollback()
                return jsonify({"success": False, "error": str(e)}), 500
    
    return jsonify({"success": False, "error": "Borrowing record not found"}), 404


@app.route("/admin/data")
def admin_data():

    if "user_id" in session and session.get("role") == "admin":
        total_members = User.query.count()
        total_bookings = Booking.query.count()
        total_equipment = EquipmentBorrowing.query.filter_by(status="approve").count()

        return jsonify(
            {
                "total_members": total_members,
                "total_bookings": total_bookings,
                "total_equipment": total_equipment,
            }
        )
    else:
        return jsonify({"error": "Unauthorized access"}), 403


@app.route("/admin")
def admin_dashboard():
    print("Admin Dashboard accessed")
    if "user_id" in session and session.get("role") == "admin":
        notification = Notification.query.count()
        print(f"Notification count: {notification}")
        return render_template("admin_dashboard.html", notification_count=notification)
    else:
        return "Unauthorized", 403


@app.route("/admin/graph-data")
def graph_data():

    result = db.session.execute(
        "SELECT month, COUNT(*) as visits FROM visits GROUP BY month"
    )
    rows = result.fetchall()

    data = {
        "labels": [row["month"] for row in rows],
        "visits": [row["visits"] for row in rows],
    }

    return jsonify(data)


@app.route("/user")
def user_dashboard():
    if "user_id" in session and session.get("role") == "user":
        user = db.session.get(User, session["user_id"])
        if user:
            appointment_count = Booking.query.filter_by(
                member_name=session["user_id"], status="accepted"
            ).count()
            borrow_count = EquipmentBorrowing.query.filter_by(
                user_id=session["user_id"], status="approve"
            ).count()
            notification_count = Notification.query.filter_by(
                user_id=session["user_id"]
            ).count()

            return render_template(
                "user_dashboard.html",
                user=user,
                appointment_count=appointment_count,
                borrow_count=borrow_count,
                notification_count=notification_count,
            )
        else:
            flash("User not found.")
            return redirect(url_for("login"))
    else:
        flash("Access denied. Users only.")
        return redirect(url_for("login"))


@app.route("/tables")
def tables():
    page = request.args.get("page")
    user_id = session.get("user_id")

    if page == "appointments":
        appointments = Booking.query.filter_by(member_name=user_id).all()
        print("Appointments:")
        for appointment in appointments:
            for column in Booking.__table__.columns:
                print(f"{column.name}: {getattr(appointment, column.name)}")
            print("------")

        return render_template("tables.html", data=appointments, page="appointments")

    elif page == "borrowed":

        borrowings = (
            EquipmentBorrowing.query.filter(
                EquipmentBorrowing.user_id == user_id,
                EquipmentBorrowing.status != "returned",
            )
            .options(joinedload(EquipmentBorrowing.inventory))
            .all()
        )

        print("Borrowings:")
        for borrowing in borrowings:
            for column in EquipmentBorrowing.__table__.columns:
                print(f"{column.name}: {getattr(borrowing, column.name)}")
            if borrowing.inventory:
                print(f"Equipment Name: {borrowing.inventory.name}")
            print("------")

        return render_template("tables.html", data=borrowings, page="borrowed")

    else:
        return "Invalid page", 404


@app.route("/updateuser", methods=["GET", "POST"])
def updateuser():
    if request.method == "POST":
        user_id = session.get("user_id")
        userlogin = request.form.get("userlogin")
        first_name = request.form.get("firstName")
        last_name = request.form.get("lastName")
        birthdate = request.form.get("birthdate")
        gender = request.form.get("gender")
        contact_number = request.form.get("contactNumber")
        new_password = request.form.get("newPassword")

        if "imageUpload" in request.files:
            profile_image = request.files["imageUpload"]
            if profile_image:
                print("true")
                filename = f"{user_id}.png"
                print(filename)
                image_path = os.path.join(STATIC_FOLDER, filename)
                print(image_path)
                profile_image.save(image_path)

        user = User.query.filter_by(id=user_id).first()
        if first_name:
            user.firstname = first_name
        if userlogin:
            user.id_number = userlogin
        if last_name:
            user.lastname = last_name
        if birthdate:
            user.date_of_birth = birthdate
        if gender:
            user.gender = gender
        if contact_number:
            user.contact_number = contact_number
        if new_password:
            user.password = new_password

        db.session.commit()

        session["user_id"] = user.id

        flash("User Updated Successfully", "success")

        if session.get("role") == "admin":
            return redirect(url_for("admin_settings"))

    return redirect(url_for("user_settings"))


@app.route("/api/data")
def get_dashboard_data():
    if "user_id" in session and session.get("role") == "user":
        try:
            total_members = User.query.count()
            upcoming_appointments = Appointment.query.filter_by(
                user_id=session["user_id"]
            ).count()
            borrowed_equipment = EquipmentBorrowing.query.filter_by(
                user_id=session["user_id"]
            ).count()
            notifications = Notification.query.filter_by(
                user_id=session["user_id"]
            ).count()

            return jsonify(
                {
                    "total_members": total_members,
                    "upcoming_appointments": upcoming_appointments,
                    "borrowed_equipment": borrowed_equipment,
                    "notifications": notifications,
                }
            )

        except Exception as e:
            print(f"Error occurred: {str(e)}")
            return jsonify({"error": str(e)}), 500
    else:
        return jsonify({"error": "Unauthorized access"}), 403


@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect(url_for("login"))

    if session.get("role") == "admin":
        return redirect(url_for("admin_dashboard"))
    return redirect(url_for("user_dashboard"))


@app.route("/api/user/notifications")
def get_user_notifications():
    if "user_id" not in session:
        return jsonify({"error": "User not logged in"}), 403

    user_id = session["user_id"]
    notifications = Notification.query.filter_by(user_id=user_id).all()
    notification_data = [
        {"message": notification.message, "seen": notification.seen}
        for notification in notifications
    ]

    return jsonify(notification_data)


@app.route("/api/members", methods=["GET"])
def get_members():
    if "user_id" not in session:
        return jsonify({"error": "Unauthorized access"}), 401

    members = User.query.filter(User.role != "admin").all()

    member_list = [
        {
            "id": member.id_number,
            "name": f"{member.firstname} {member.lastname}",
            "contact": member.contact_number,
            "dob": (
                member.date_of_birth.strftime("%Y/%m/%d")
                if member.date_of_birth
                else None
            ),
            "gender": member.gender,
        }
        for member in members
    ]
    return jsonify(member_list)


@app.route("/admin/membership")
def admin_membership():
    if "user_id" in session and session.get("role") == "admin":
        members = User.query.filter(User.role != "admin").all()

        excluded_columns = ["password", "role", "membership_status", "next_appointment"]
        column_headers = [
            column.name
            for column in User.__table__.columns
            if column.name not in excluded_columns
        ]

        return render_template(
            "admin_membership.html", members=members, column_headers=column_headers
        )
    else:
        flash("Access denied. Admins only.")
        return redirect(url_for("login"))


@app.route("/admin/members", methods=["GET"])
def fetch_members():
    members = User.query.filter(User.role != "admin").all()
    members_data = [
        {
            "id": member.id,
            "name": f"{member.firstname} {member.lastname}",
            "email": member.email,
            "status": member.status,
        }
        for member in members
    ]
    return jsonify(members_data)


@app.route("/admin/delete/<int:id>", methods=["POST"])
def delete_member(id):
    member = Member.query.get(id)
    if member:
        db.session.delete(member)
        db.session.commit()
    return redirect(url_for("admin_membership"))


@app.route("/admin/edit/<int:id>", methods=["POST"])
def edit_member(id):
    member = Member.query.get(id)
    if member:
        member.name = request.form["name"]
        member.email = request.form["email"]
        member.status = request.form["status"]
        db.session.commit()
    return redirect(url_for("admin_membership"))


@app.route("/admin/calendar")
def admin_calendar():
    if "user_id" in session and session.get("role") == "admin":
        today = date.today()
        appointments = Booking.query.filter(Booking.appointment_date >= today).all()

        # Updated serialization function
        def serialize_booking(booking):
            user = User.query.get(booking.member_name)
            return {
                "id": booking.id,
                "member_name": f"{user.firstname} {user.lastname}" if user else "Unknown",
                "user": {
                    "firstname": user.firstname if user else "",
                    "lastname": user.lastname if user else "",
                    "email": user.email if user else "",
                    "contact_number": user.contact_number if user else ""
                } if user else None,
                "contact_number": booking.contact_number,
                "appointment_date": booking.appointment_date.strftime("%Y-%m-%d"),
                "appointment_time": booking.appointment_time.strftime("%I:%M %p"),
                "message": booking.message if hasattr(booking, 'message') else None,
                "status": booking.status
            }

        serialized_appointments = [serialize_booking(appointment) for appointment in appointments]
        return render_template("admin_calendar.html", appointments=serialized_appointments)
    else:
        flash("Access denied. Admins only.")
        return redirect(url_for("login"))


@app.route("/admin_booking")
def admin_booking():
    bookings = Booking.query.join(User).all()

    return render_template("admin_booking.html", bookings=bookings)


@app.route("/update_booking_status/<int:booking_id>", methods=["POST"])
def update_booking_status(booking_id):
    try:
        booking = Booking.query.get(booking_id)
        new_status = request.form["status"]
        if not booking:
            return jsonify({"success": False, "error": "Booking not found"})

        user = User.query.filter_by(id=booking.member_name).first()

        if not user:
            return jsonify({"success": False, "error": "User not found"})

        if new_status.lower() == "rejected":

            rejection_reason = request.form.get(
                "rejection_reason", "No specific reason provided"
            )
            solution = request.form.get("solution", "No solution provided")

            notification_message = f"Your booking request has been rejected. Reason: {rejection_reason}. Solution: {solution}. Ensure you bring your receipt from the cashier when coming to the gym."

            notification = Notification(
                user_id=booking.member_name, message=notification_message
            )
            db.session.add(notification)

            db.session.delete(booking)
            db.session.commit()

        elif new_status.lower() == "accepted":

            booking.status = "Accepted"
            db.session.commit()

            notification_message = (
                f"Your booking request has been approved. Date of Request: {booking.appointment_date.strftime('%Y-%m-%d')} - "
                f"Time: {booking.appointment_time.strftime('%I:%M %p')}."
            )
            notification = Notification(user_id=user.id, message=notification_message)
            db.session.add(notification)
            db.session.commit()

        elif new_status.lower() == "pending":
            booking.status = "Pending"
            db.session.commit()

        return jsonify({"success": True})

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"success": False, "error": str(e)})


@app.route("/admin/borrowing")
def admin_borrowing():
    if "user_id" in session and session.get("role") == "admin":
        borrowings = EquipmentBorrowing.query.all()
        for borrowing in borrowings: 
            member = User.query.filter_by(id=borrowing.user_id).first()
            
            if member:  # Check if the member is found
                borrowing.member_name = f"{member.firstname} {member.lastname}"
            else:
                borrowing.member_name = "Unknown Member"  # Set default if member is not found
                
        return render_template("admin_borrowing.html", borrowings=borrowings)
       
    else:
        flash("Access denied.", "error")
        return redirect(url_for("login"))


@app.route("/admin/inventory", methods=["GET", "POST"])
def admin_inventory():
    if request.method == "POST":
        item_name = request.form["item_name"]
        condition = request.form["condition"]
        quantity = int(request.form["quantity"])

        image_file = request.files["image"]
        if image_file and image_file.filename != "":

            filename = secure_filename(image_file.filename)
            image_file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))
            image_path = filename
        else:
            image_path = None

        new_item = Inventory(
            name=item_name, condition=condition, quantity=quantity, image=image_path
        )
        db.session.add(new_item)
        db.session.commit()
        flash("Item added to inventory successfully.")
        return redirect(url_for("admin_inventory"))

    inventory_items = Inventory.query.all()
    return render_template("admin_inventory.html", inventory_items=inventory_items)


@app.route("/edit_item/<int:item_id>", methods=["POST"])
def edit_inventory_item(item_id):
    global inventory_items
    for item in inventory_items:
        if item["id"] == item_id:
            item["quantity"] = request.form["quantity"]
            break
    return redirect(url_for("admin_inventory"))


@app.route("/delete_inventory_item/<int:item_id>", methods=["POST"])
def delete_inventory_item(item_id):
    item = Inventory.query.get(item_id)
    if item:

        if item.image:
            image_path = os.path.join(app.config["UPLOAD_FOLDER"], item.image)
            if os.path.exists(image_path):
                os.remove(image_path)

        db.session.delete(item)
        db.session.commit()
        flash("Item deleted from inventory.")
    return redirect(url_for("admin_inventory"))


@app.route("/admin/notifications")
def admin_notifications():
    notifications = Notification.query.all()

    for notification in notifications:
        print(
            f"ID: {notification.id}, User ID: {notification.user_id}, Message: {notification.message}, Seen: {notification.seen}, Created At: {notification.created_at}"
        )

    return render_template("admin_notifications.html", notifications=notifications)


@app.route("/admin/settings")
def admin_settings():
    user_id = session.get("user_id")
    if user_id:
        user = User.query.filter_by(id=user_id).first()
        if user:
            return render_template("admin_settings.html", user=user)
        else:
            return "User not found", 404
    else:
        return redirect(url_for("login"))


@app.route("/view_session")
def view_session():
    return jsonify(dict(session))


@app.route("/faq")
def faq():
    return render_template("faq.html")


@app.route("/logout")
def logout():
    session.pop("user_id", None)
    session.pop("role", None)
    session.pop("username", None)
    return redirect(url_for("landing"))


@app.errorhandler(404)
def not_found(e):
    return render_template("404.html"), 404


@app.route("/upload_profile_picture", methods=["POST"])
def upload_profile_picture():
    pass


@app.route("/user_appointments", methods=["GET"])
def user_appointments():
    # Redirect to the calendar view
    return redirect(url_for("calendar_view"))


@app.route("/calendar_view", methods=["GET"])
def calendar_view():
    MAX_SLOTS_PER_DAY = 30
    START_DATE = date.today()
    MONTHS_TO_DISPLAY = 1  # Display current month only

    # Generate calendar data
    calendar_data = []

    current_month = START_DATE.month
    current_year = START_DATE.year

    # Calculate start and end dates for the current month
    start_of_month = date(current_year, current_month, 1)
    end_of_month = date(
        current_year, current_month + 1, 1
    ) - timedelta(days=1) if current_month < 12 else date(current_year, 12, 31)

    # Iterate through all days in the current month
    current_date = start_of_month
    while current_date <= end_of_month:
        # Determine if it's a weekend or holiday
        is_weekend = current_date.weekday() >= 5
        bookings_count = Booking.query.filter_by(appointment_date=current_date).count()

        # Set status for the day
        if is_weekend:
            status = "red"  # Weekend
        elif bookings_count >= MAX_SLOTS_PER_DAY:
            status = "red"  # Fully booked
        else:
            status = "green"  # Slots available

        available_slots = max(0, MAX_SLOTS_PER_DAY - bookings_count)

        # Append day's data
        calendar_data.append(
            {
                "date": current_date,
                "status": status,
                "available_slots": available_slots,
            }
        )
        current_date += timedelta(days=1)

    return render_template(
        "calendar_view.html", calendar_data=calendar_data, start_date=START_DATE
    )


@app.route("/book_appointment", methods=["POST"])
def book_appointment():
    appointment_date = request.form.get("appointment_date")
    timeslot = request.form.get("appointment_time")  # 'morning' or 'afternoon'
    user_id = session.get("user_id")
    if not user_id:
        flash("Please log in first.", "danger")
        return redirect(url_for("calendar_view"))

    # Check total bookings for the selected date and time period
    if timeslot == "morning":
        chosen_time = datetime.strptime("08:00:00", "%H:%M:%S").time()
        booking_count = Booking.query.filter_by(
            appointment_date=dateutil.parser.parse(appointment_date).date()
        ).filter(Booking.appointment_time < datetime.strptime("12:00:00", "%H:%M:%S").time()).count()
        
        if booking_count >= 15:
            flash("Sorry, all morning slots are fully booked. Please select another time or date.", "danger")
            return redirect(url_for("calendar_view"))
    else:  # afternoon
        chosen_time = datetime.strptime("13:00:00", "%H:%M:%S").time()
        booking_count = Booking.query.filter_by(
            appointment_date=dateutil.parser.parse(appointment_date).date()
        ).filter(Booking.appointment_time >= datetime.strptime("13:00:00", "%H:%M:%S").time()).count()
        
        if booking_count >= 15:
            flash("Sorry, all afternoon slots are fully booked. Please select another time or date.", "danger")
            return redirect(url_for("calendar_view"))

    # Check if user already has a booking for this date and time
    already_booked = Booking.query.filter_by(
        member_name=user_id,
        appointment_date=dateutil.parser.parse(appointment_date).date(),
        appointment_time=chosen_time
    ).first()

    if already_booked:
        flash("You already have a booking for that date and time!", "danger")
        return redirect(url_for("calendar_view"))

    # Store new booking
    new_booking = Booking(
        member_name=user_id,
        appointment_date=dateutil.parser.parse(appointment_date).date(),
        appointment_time=chosen_time,
        status="accepted",
    )
    db.session.add(new_booking)
    db.session.commit()

    flash("Appointment successfully booked!", "success")
    return redirect(url_for("calendar_view"))


@app.route("/user/borrow_equipment", methods=["POST"])
def submit_borrow_request():
    if "user_id" not in session:
        flash("Please log in to borrow equipment.", "error")
        return redirect(url_for("login"))

    user_id = session["user_id"]
    equipment_id = request.form.get("equipment_id")
    return_date = request.form.get("return_date")

    result = db.session.execute(
        text("SELECT quantity FROM inventory WHERE id = :id"), {"id": equipment_id}
    )
    quantity = result.fetchone()[0]

    if quantity is None or quantity <= 0:
        flash("Equipment is out of stock!", "error")
        return redirect(url_for("user_equipments"))

    new_quantity = quantity - 1

    db.session.execute(
        text("UPDATE inventory SET quantity = :quantity WHERE id = :id"),
        {"quantity": new_quantity, "id": equipment_id},
    )
    new_borrowing = EquipmentBorrowing(
        user_id=user_id,
        equipment_id=equipment_id,
        return_date=datetime.strptime(return_date, "%Y-%m-%d"),
    )
    db.session.add(new_borrowing)
    db.session.commit()

    flash("Borrow request submitted successfully!", "success")
    return redirect(url_for("user_equipments"))


@app.route("/user_equipments")
def user_equipments():
    today = datetime.utcnow().date()
    user_id = session.get("user_id")

    if not user_id:
        return "Please log in first", 401

    borrowed_today = EquipmentBorrowing.query.filter(
        EquipmentBorrowing.user_id == user_id,
        EquipmentBorrowing.status != "returned",
    ).first()

    borrowedalready = borrowed_today is not None

    equipment_list = Inventory.query.all()

    return render_template(
        "user_equipments.html",
        equipment_list=equipment_list,
        borrowedalready=borrowedalready,
    )


@app.route("/user_feedback")
def user_feedback():
    return render_template("user_feedback.html")


@app.route("/user_notifications")
def user_notifications():
    if "user_id" not in session:
        flash("Please log in to view notifications.", "error")
        return redirect(url_for("login"))

    user_id = session["user_id"]
    notifications = Notification.query.filter_by(user_id=user_id).all()

    return render_template("user_notifications.html", notifications=notifications)


@app.route("/delete_notification/<int:notification_id>", methods=["DELETE"])
def delete_notification(notification_id):
    if "user_id" not in session:
        return jsonify({"success": False, "message": "User not logged in"}), 403

    notification = Notification.query.get(notification_id)

    if not notification or notification.user_id != session["user_id"]:
        return (
            jsonify(
                {"success": False, "message": "Notification not found or unauthorized"}
            ),
            404,
        )

    try:
        db.session.delete(notification)
        db.session.commit()
        return jsonify({"success": True})
    except Exception as e:
        print(f"Error: {e}")
        return (
            jsonify(
                {
                    "success": False,
                    "message": "An error occurred while deleting the notification.",
                }
            ),
            500,
        )


@app.route("/borrowactions", methods=["POST"])
def borrow_actions():
    booking_id = request.form.get("booking_id")
    user_id = request.form.get("user_id")
    status = request.form.get("status")
    borrowing_record = EquipmentBorrowing.query.filter_by(id=booking_id).first()

    if borrowing_record:
        message = ""
        inventory_name = borrowing_record.inventory.name if borrowing_record.inventory else "Unknown Item"

        if status == "accepted":
            borrowing_record.status = "accepted"
            message = f"Your borrowing request for item '{inventory_name}' has been accepted. Ensure you bring your receipt from the cashier when coming to the gym for access or equipment."

        elif status == "returned":
            borrowing_record.status = "returned"
            # Increment the inventory quantity when item is returned
            if borrowing_record.inventory:
                borrowing_record.inventory.quantity += 1
            message = f"Your borrowed item '{inventory_name}' has been returned successfully. Ensure you bring your receipt from the cashier when coming to the gym for access or equipment."

        elif (
            borrowing_record.return_date
            and borrowing_record.return_date < datetime.utcnow()
            and borrowing_record.status != "returned"
        ):
            message = f"Reminder: The item '{inventory_name}' is overdue and must be returned. Ensure you bring your receipt from the cashier when coming to the gym for access or equipment."

        if message:
            notification = Notification(
                user_id=borrowing_record.user_id, message=message
            )
            db.session.add(notification)

        try:
            db.session.commit()
            flash("Borrowing record updated and user notified successfully.", "success")
        except Exception as e:
            db.session.rollback()
            flash(f"Error updating record: {str(e)}", "error")

    else:
        flash("Borrowing record not found.", "error")

    return redirect(url_for("admin_borrowing"))


@app.route("/user_settings")
def user_settings():
    user_id = session.get("user_id")

    if user_id:
        user = User.query.filter_by(id=user_id).first()
        if user:
            return render_template("user_settings.html", user=user)
        else:
            return "User not found", 404
    else:
        return redirect(url_for("login"))


@app.route("/feedback")
def feedback():
    feedbacks = Feedback.query.all()

    for feedback in feedbacks:
        if feedback.user:  # Check if feedback is associated with a user
            print(
                f"Feedback ID: {feedback.id}, User ID: {feedback.user_id}, Feedback: {feedback.message}, User Name: {feedback.user.firstname} {feedback.user.lastname}"
            )
        else:
            print(
                f"Feedback ID: {feedback.id}, User ID: {feedback.user_id}, Feedback: {feedback.message}, User Name: None (No user associated)"
            )

    return render_template("feedback.html", feedback=feedbacks)


@app.route("/deletenotification", methods=["POST"])
def deletenotification():
    notification_id = request.form.get("notification_id")

    if not notification_id:
        return jsonify({"success": False, "error": "No notification_id provided"})

    try:
        notification_id = int(notification_id)
        print(f"Received notification_id: {notification_id}")

        notification = Notification.query.filter_by(id=notification_id).first()
        print(f"Found notification: {notification}")

        if notification:
            db.session.delete(notification)
            db.session.commit()
            return jsonify({"success": True})
        else:
            return jsonify({"success": False, "error": "Notification not found"})

    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)})


@app.route("/deletefeedback", methods=["POST"])
def delete_feedback():
    feedback_id = request.form.get("feedback_id")

    if not feedback_id:
        return jsonify({"success": False, "error": "Feedback ID is required."})

    try:
        feedback = Feedback.query.get(feedback_id)

        if not feedback:
            return jsonify({"success": False, "error": "Feedback not found."})

        db.session.delete(feedback)
        db.session.commit()

        return jsonify({"success": True, "message": "Feedback deleted successfully."})

    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)})


@app.route("/submitFeedback", methods=["POST"])
def submit_feedback():
    feedback_text = request.form.get("feedbackText")
    user_id = session.get("user_id")
    if user_id is None:
        return "User not logged in", 403
    feedback = Feedback(
        user_id=user_id, message=feedback_text, created_at=datetime.utcnow()
    )
    db.session.add(feedback)
    db.session.commit()
    flash("Feedback sent successfully!", "success")
    return redirect(url_for("user_feedback"))


@app.route('/get_bookings')
def get_bookings():
    bookings = Booking.query.all()
    events = []
    booking_counts = defaultdict(int)

    for booking in bookings:
        start_dt = datetime.combine(booking.appointment_date, booking.appointment_time)
        hour = start_dt.hour

        if (8 <= hour < 12) or (13 <= hour < 16):
            period = '8am-11am' if hour < 12 else '1pm-4pm'
            booking_counts[(booking.appointment_date, period)] += 1

    for (date, period), count in booking_counts.items():
        start_time, end_time = period.split('-')
        start_dt = datetime.combine(date, datetime.strptime(start_time, '%I%p').time())
        end_dt = datetime.combine(date, datetime.strptime(end_time, '%I%p').time())

        max_slots = 15
        available_slots = max_slots - count
        background_color = '#f08080' if available_slots == 0 else '#90ee90'

        events.append({
            'title': f'{period}: {available_slots} slots left',
            'start': start_dt.isoformat(),
            'end': end_dt.isoformat(),
            'backgroundColor': background_color,
            'borderColor': background_color,
            'display': 'block'
        })

    return jsonify(events)

@app.route('/delete_appointment', methods=['POST'])
def delete_appointment():
    if 'user_id' not in session:
        return jsonify({"success": False, "error": "Not logged in"}), 401

    try:
        data = request.get_json()
        start_time = datetime.fromisoformat(data['start_time'].replace('Z', '+00:00'))
        booking = Booking.query.filter_by(
            member_name=session['user_id'],
            appointment_date=start_time.date(),
            appointment_time=start_time.time()
        ).first()

        if booking:
            db.session.delete(booking)
            db.session.commit()
            return jsonify({"success": True})
        else:
            print("Booking not found")  
            data = request.get_json()
            print(data)
            
            return jsonify({"success": False, "error": "Booking not found"}), 404

    except Exception as e:
        print(f"Error deleting appointment: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

# Add new routes for deleting borrowing and booking records
@app.route('/delete_borrowing/<int:borrowing_id>', methods=['DELETE'])
def delete_borrowing(borrowing_id):
    if 'user_id' not in session or session.get('role') != 'admin':
        return jsonify({'success': False, 'message': 'Unauthorized access'}), 403
    
    try:
        borrowing = EquipmentBorrowing.query.get(borrowing_id)
        if borrowing:
            db.session.delete(borrowing)
            db.session.commit()
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'message': 'Borrowing record not found'})
    
    except Exception as e:
        print(f"Error deleting borrowing record: {e}")
        return jsonify({'success': False, 'message': 'Error deleting borrowing record'}), 500

@app.route('/delete_booking/<int:booking_id>', methods=['DELETE'])
def delete_booking_by_admin(booking_id):
    if 'user_id' not in session or session.get('role') != 'admin':
        return jsonify({'success': False, 'message': 'Unauthorized access'}), 403
    
    try:
        booking = Booking.query.get(booking_id)
        if booking:
            db.session.delete(booking)
            db.session.commit()
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'message': 'Booking not found'})
    
    except Exception as e:
        print(f"Error deleting booking: {e}")
        return jsonify({'success': False, 'message': 'Error deleting booking'}), 500

if __name__ == "__main__":
    app.run(debug=True)

    app.run(debug=True)
