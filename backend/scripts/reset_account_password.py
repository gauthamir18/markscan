from getpass import getpass

from app.core.security import hash_password
from app.database.connection import SessionLocal
from app.models.faculty import Faculty
from app.models.student import Student


def main() -> None:
    account_id = input("Faculty email or student roll number: ").strip()
    new_password = getpass("New password (minimum 12 characters): ")
    confirmation = getpass("Confirm new password: ")

    if len(new_password) < 12:
        raise SystemExit("Use a password with at least 12 characters.")
    if new_password != confirmation:
        raise SystemExit("Passwords do not match.")

    db = SessionLocal()
    try:
        faculty = db.query(Faculty).filter(Faculty.email.ilike(account_id)).first()
        student = db.query(Student).filter(Student.roll_no.ilike(account_id)).first()
        if faculty is not None and student is not None:
            raise SystemExit("Identifier matched more than one account; contact the database administrator.")
        account = faculty or student
        if account is None:
            raise SystemExit("No account found for that email or roll number.")

        account.password = hash_password(new_password)
        db.commit()
        print("Password reset successfully. Share the new password only through a private channel.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
