from sqlalchemy.dialects.postgresql import UUID

from src.extensions import db


class UserORM(db.Model):
    """Read-only mapping to the users table owned by the accounts part of the system."""

    __tablename__ = "users"

    id = db.Column(UUID(as_uuid=True), primary_key=True)
    email = db.Column(db.Text, nullable=False)
    name = db.Column(db.Text, nullable=False)
