from getpass import getpass

from app.core.security import hash_password
from app.database.base import Base
from app.database.connection import SessionLocal, engine
from app.models.faculty import Faculty
from app.models.mark import Mark
from app.models.student import Student
from app.models.test import Test


def main() -> None:
    # Ensure all application tables exist before inserting the first administrator.
    Base.metadata.create_all(bind=engine)

    name = input("Admin display name: ").strip()
    email = input("Admin email: ").strip().lower()
    password = getpass("New admin password (minimum 12 characters): ")
    confirmation = getpass("Confirm password: ")

    if not name or not email:
        raise SystemExit("Name and email are required.")
    if len(password) < 12:
        raise SystemExit("Use a password with at least 12 characters.")
    if password != confirmation:
        raise SystemExit("Passwords do not match.")

    db = SessionLocal()
    try:
        existing = db.query(Faculty).filter(Faculty.email.ilike(email)).first()
        if existing:
            raise SystemExit("An account with this email already exists.")
        db.add(Faculty(
            name=name,
            email=email,
            password=hash_password(password),
            role="admin",
        ))
        db.commit()
        print("Admin account created. Store the credentials securely.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
