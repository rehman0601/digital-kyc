# Seed Database with Mock Data for Demo/Screenshots
import os
from werkzeug.security import generate_password_hash
from app import app, db, User, Document, Verification
from datetime import datetime, timedelta

def seed():
    with app.app_context():
        # Ensure database tables exist
        db.create_all()

        # Check if users already exist
        if User.query.filter_by(username="john_doe").first():
            print("Database already contains seed data.")
            return

        # 1. Create Mock Users
        john = User(
            username="john_doe",
            email="john.doe@example.com",
            password=generate_password_hash("password123"),
            role="user"
        )
        jane = User(
            username="jane_smith",
            email="jane.smith@example.com",
            password=generate_password_hash("password123"),
            role="user"
        )
        db.session.add(john)
        db.session.add(jane)
        db.session.commit()
        print("Created users: john_doe, jane_smith")

        # 2. Add Documents and Verifications for John
        doc_aadhaar = Document(
            user_id=john.id,
            document_name="Aadhaar",
            file_path="uploads/john_aadhaar.png",
            upload_date=datetime.utcnow() - timedelta(days=2)
        )
        doc_pan = Document(
            user_id=john.id,
            document_name="PAN",
            file_path="uploads/john_pan.png",
            upload_date=datetime.utcnow() - timedelta(hours=5)
        )
        db.session.add(doc_aadhaar)
        db.session.add(doc_pan)
        db.session.commit()

        ver_aadhaar = Verification(
            document_id=doc_aadhaar.id,
            status="Approved",
            remarks="[Mock AWS Rekognition OCR] Aadhaar Card Verified. Name matched: JOHN DOE. UID: XXXX-XXXX-5821. Match confidence: 99.2%",
            reviewed_at=datetime.utcnow() - timedelta(days=1)
        )
        ver_pan = Verification(
            document_id=doc_pan.id,
            status="Pending",
            remarks="[Mock AWS Rekognition OCR] PAN Card Scan Completed. Permanent Account Number extracted: ABCDE4581F. Name: JOHN DOE. Awaiting admin review.",
            reviewed_at=None
        )
        db.session.add(ver_aadhaar)
        db.session.add(ver_pan)

        # 3. Add Documents and Verifications for Jane
        doc_passport = Document(
            user_id=jane.id,
            document_name="Passport",
            file_path="uploads/jane_passport.jpg",
            upload_date=datetime.utcnow() - timedelta(days=3)
        )
        db.session.add(doc_passport)
        db.session.commit()

        ver_passport = Verification(
            document_id=doc_passport.id,
            status="Rejected",
            remarks="[Mock AWS Rekognition OCR] Face match confidence below 90% threshold. Document picture is blurry. Please re-upload.",
            reviewed_at=datetime.utcnow() - timedelta(days=2)
        )
        db.session.add(ver_passport)

        db.session.commit()
        print("Database seeded successfully with Aadhaar, PAN, and Passport data!")

if __name__ == "__main__":
    seed()
