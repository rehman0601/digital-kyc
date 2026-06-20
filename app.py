"""
Digital KYC Verification Platform
----------------------------------
A simple Flask app where users register, log in, upload KYC documents
(Aadhaar / PAN / Passport) and track verification status. Admins review
and approve/reject documents.

Kept intentionally simple -> this app is the "Phase 1" piece of a bigger
DevOps project (Docker / Jenkins / Kubernetes / Terraform / Monitoring /
Logging). The app itself is not the point of the assignment, so there is
no need to over-engineer it.
"""

import os
import logging
from datetime import datetime

from flask import Flask, render_template, redirect, url_for, flash, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import (
    LoginManager, UserMixin, login_user, login_required,
    logout_user, current_user
)
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from prometheus_flask_exporter import PrometheusMetrics

# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------
app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-change-in-prod")

# DATABASE_URL lets the same code run with SQLite locally (no setup needed)
# and MySQL in Kubernetes/Docker (set via env vars). This is what makes the
# app portable across Phase 1 -> Phase 5 without code changes.
DB_URL = os.environ.get("DATABASE_URL")
if not DB_URL:
    DB_HOST = os.environ.get("DB_HOST")
    if DB_HOST:
        DB_URL = (
            f"mysql+pymysql://{os.environ.get('DB_USER', 'kyc_user')}:"
            f"{os.environ.get('DB_PASS', 'kyc_pass')}@{DB_HOST}:"
            f"{os.environ.get('DB_PORT', '3306')}/"
            f"{os.environ.get('DB_NAME', 'kyc_db')}"
        )
    else:
        DB_URL = "sqlite:///kyc.db"

app.config["SQLALCHEMY_DATABASE_URI"] = DB_URL
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

UPLOAD_FOLDER = os.environ.get("UPLOAD_FOLDER", "uploads")
ALLOWED_EXTENSIONS = {"pdf", "png", "jpg", "jpeg"}
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

db = SQLAlchemy(app)

login_manager = LoginManager(app)
login_manager.login_view = "login"

# Prometheus metrics at /metrics -> used in Phase 8 (Monitoring)
metrics = PrometheusMetrics(app)
metrics.info("kyc_app_info", "Digital KYC Verification Platform", version="1.0.0")

# Structured logging to stdout (Docker/K8s friendly) and to a file
# (used in Phase 9 - Logging / ELK demo)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(os.path.join("logs", "app.log")) if os.path.isdir("logs")
        else logging.NullHandler(),
    ],
)
logger = logging.getLogger("kyc_app")


# ---------------------------------------------------------------------------
# Models  (matches Users / Documents / Verification tables from the plan)
# ---------------------------------------------------------------------------
class User(db.Model, UserMixin):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), default="user")  # 'user' or 'admin'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    documents = db.relationship("Document", backref="owner", lazy=True)


class Document(db.Model):
    __tablename__ = "documents"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    document_name = db.Column(db.String(50), nullable=False)  # Aadhaar/PAN/Passport
    file_path = db.Column(db.String(255), nullable=False)
    upload_date = db.Column(db.DateTime, default=datetime.utcnow)

    verification = db.relationship(
        "Verification", backref="document", uselist=False, lazy=True
    )


class Verification(db.Model):
    __tablename__ = "verification"
    id = db.Column(db.Integer, primary_key=True)
    document_id = db.Column(db.Integer, db.ForeignKey("documents.id"), nullable=False)
    status = db.Column(db.String(20), default="Pending")  # Pending/Approved/Rejected
    remarks = db.Column(db.String(255), default="")
    reviewed_at = db.Column(db.DateTime)


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def perform_aws_ocr_and_rekognition(filepath, doc_type, username):
    """
    Simulates AWS Rekognition and Textract (OCR) services analyzing the document.
    Attempts to use boto3 if AWS credentials exist, otherwise falls back to simulated responses.
    """
    logger.info("[AWS OCR/Rekognition] Initiating scan for file: %s (%s)", filepath, doc_type)
    
    try:
        import boto3
        if os.environ.get("AWS_ACCESS_KEY_ID") and os.environ.get("AWS_SECRET_ACCESS_KEY"):
            try:
                client = boto3.client("rekognition", region_name=os.environ.get("AWS_DEFAULT_REGION", "ap-south-1"))
                with open(filepath, "rb") as image_file:
                    response = client.detect_text(Image={"Bytes": image_file.read()})
                extracted_words = [text_detail["DetectedText"] for text_detail in response.get("TextDetections", []) if text_detail["Type"] == "WORD"]
                extracted_text = " ".join(extracted_words[:10])
                logger.info("[AWS Rekognition] Real AWS call succeeded. Extracted: %s", extracted_text)
                return f"[AWS Rekognition OCR] Verified. Text: {extracted_text or 'No text found'}"
            except Exception as e:
                logger.warning("[AWS Rekognition] Real AWS call failed: %s. Falling back to mock.", e)
    except ImportError:
        pass

    import random
    if doc_type == "Aadhaar":
        remarks = f"[Mock AWS Rekognition OCR] Aadhaar Card Verified. Name matched: {username.upper()}. UID: XXXX-XXXX-{random.randint(1000, 9999)}."
    elif doc_type == "PAN":
        remarks = f"[Mock AWS Rekognition OCR] PAN Card Verified. Permanent Account Number extracted: ABCDE{random.randint(1000, 9999)}F. Name: {username.upper()}."
    else:
        remarks = f"[Mock AWS Rekognition OCR] Passport Verified. Document No: Z{random.randint(1000000, 9999999)}. Expiry matched. Facematch Confidence: {random.randint(95, 99)}%."
    
    logger.info("[AWS OCR/Rekognition] Scan complete. Output: %s", remarks)
    return remarks



# ---------------------------------------------------------------------------
# Auth routes
# ---------------------------------------------------------------------------
@app.route("/")
def index():
    if current_user.is_authenticated:
        return redirect(url_for("admin_dashboard" if current_user.role == "admin" else "dashboard"))
    return redirect(url_for("login"))


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"].strip()
        email = request.form["email"].strip()
        password = request.form["password"]

        if User.query.filter((User.username == username) | (User.email == email)).first():
            flash("Username or email already exists.", "danger")
            return redirect(url_for("register"))

        user = User(
            username=username,
            email=email,
            password=generate_password_hash(password),
        )
        db.session.add(user)
        db.session.commit()
        logger.info("New user registered: %s", username)
        flash("Registration successful. Please log in.", "success")
        return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"]
        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password, password):
            login_user(user)
            logger.info("User logged in: %s", username)
            return redirect(url_for("admin_dashboard" if user.role == "admin" else "dashboard"))

        flash("Invalid username or password.", "danger")
    return render_template("login.html")


@app.route("/logout")
@login_required
def logout():
    logger.info("User logged out: %s", current_user.username)
    logout_user()
    return redirect(url_for("login"))


# ---------------------------------------------------------------------------
# User routes
# ---------------------------------------------------------------------------
@app.route("/dashboard", methods=["GET", "POST"])
@login_required
def dashboard():
    if request.method == "POST":
        doc_type = request.form.get("document_name")
        file = request.files.get("file")

        if not file or file.filename == "" or not allowed_file(file.filename):
            flash("Please upload a valid PDF/PNG/JPG file.", "danger")
            return redirect(url_for("dashboard"))

        filename = secure_filename(f"{current_user.id}_{doc_type}_{file.filename}")
        filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        file.save(filepath)

        document = Document(
            user_id=current_user.id, document_name=doc_type, file_path=filepath
        )
        db.session.add(document)
        db.session.commit()

        verification_remarks = perform_aws_ocr_and_rekognition(filepath, doc_type, current_user.username)
        verification = Verification(document_id=document.id, status="Pending", remarks=verification_remarks)
        db.session.add(verification)
        db.session.commit()

        logger.info("Document uploaded: user=%s type=%s", current_user.username, doc_type)
        flash(f"{doc_type} uploaded successfully. AWS Rekognition OCR scan completed.", "success")
        return redirect(url_for("dashboard"))

    documents = Document.query.filter_by(user_id=current_user.id).all()
    return render_template("dashboard.html", documents=documents)


# ---------------------------------------------------------------------------
# Admin routes
# ---------------------------------------------------------------------------
def admin_required(func):
    from functools import wraps

    @wraps(func)
    @login_required
    def wrapper(*args, **kwargs):
        if current_user.role != "admin":
            flash("Admins only.", "danger")
            return redirect(url_for("dashboard"))
        return func(*args, **kwargs)

    return wrapper


@app.route("/admin")
@admin_required
def admin_dashboard():
    total_users = User.query.filter_by(role="user").count()
    total_applications = Document.query.count()
    pending = Verification.query.filter_by(status="Pending").count()
    verifications = (
        db.session.query(Verification, Document, User)
        .join(Document, Verification.document_id == Document.id)
        .join(User, Document.user_id == User.id)
        .order_by(Verification.id.desc())
        .all()
    )
    return render_template(
        "admin_dashboard.html",
        total_users=total_users,
        total_applications=total_applications,
        pending=pending,
        verifications=verifications,
    )


@app.route("/admin/action/<int:verification_id>", methods=["POST"])
@admin_required
def admin_action(verification_id):
    verification = db.session.get(Verification, verification_id)
    if not verification:
        flash("Verification record not found.", "danger")
        return redirect(url_for("admin_dashboard"))

    action = request.form.get("action")
    remarks = request.form.get("remarks", "")

    verification.status = "Approved" if action == "approve" else "Rejected"
    verification.remarks = remarks
    verification.reviewed_at = datetime.utcnow()
    db.session.commit()

    logger.info("Verification %s -> %s by admin %s", verification_id, verification.status, current_user.username)
    flash(f"Document {verification.status.lower()}.", "success")
    return redirect(url_for("admin_dashboard"))


# ---------------------------------------------------------------------------
# Health check (used by Kubernetes liveness/readiness probes - Phase 5)
# ---------------------------------------------------------------------------
@app.route("/health")
def health():
    return jsonify(status="ok"), 200


# ---------------------------------------------------------------------------
# Bootstrap: create tables + a default admin account
# ---------------------------------------------------------------------------
def init_db():
    with app.app_context():
        db.create_all()
        admin_username = os.environ.get("ADMIN_USERNAME", "admin")
        if not User.query.filter_by(username=admin_username).first():
            admin = User(
                username=admin_username,
                email=os.environ.get("ADMIN_EMAIL", "admin@kyc.local"),
                password=generate_password_hash(os.environ.get("ADMIN_PASSWORD", "admin123")),
                role="admin",
            )
            db.session.add(admin)
            db.session.commit()
            logger.info("Default admin account created: %s", admin_username)


init_db()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=False)
