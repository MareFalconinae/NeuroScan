import enum
import uuid

from sqlalchemy import (
    Column,
    String,
    Boolean,
    Float,
    DateTime,
    ForeignKey,
    Enum as SQLEnum,
    func,
)

from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from ..database import Base


class TumorClass(str, enum.Enum):
    GLIOMA = "glioma"
    MENINGIOMA = "meningioma"
    NOTUMOR = "notumor"
    PITUITARY = "pituitary"


class User(Base):
    __tablename__ = "users"

    user_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(32), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True, index=True)

    email_verified = Column(Boolean, nullable=False, default=True, server_default='true')

    scans = relationship("Scan", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User {self.username} ({self.email})>"


class PendingRegistration(Base):
    __tablename__ = "pending_registrations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(32), nullable=False)
    password_hash = Column(String(255), nullable=False)
    verification_code = Column(String(6), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    def __repr__(self):
        return f"<PendingRegistration {self.email}>"


class Scan(Base):
    __tablename__ = "scans"

    scan_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.user_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    file_path = Column(String(500), nullable=False)
    original_filename = Column(String(255), nullable=False)
    upload_date = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    has_tumor = Column(Boolean, nullable=False)
    tumor_class = Column(
        SQLEnum(TumorClass, name="tumor_class_enum", values_callable=lambda x: [e.value for e in x]),
        nullable=False,
    )
    confidence = Column(Float, nullable=False)
    all_probabilities = Column(JSONB, nullable=False)

    deleted_at = Column(DateTime(timezone=True), nullable=True, index=True)

    user = relationship("User", back_populates="scans")

    def __repr__(self):
        return f"<Scan {self.scan_id} {self.tumor_class}>"
