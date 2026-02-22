import uuid
from sqlalchemy import Column, Integer, String, Text, ForeignKey, Float
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from app.model.base import Base, TimestampMixin


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    roles = Column(String, nullable=False)  # Store roles as a comma-separated string


class Book(Base, TimestampMixin):
    __tablename__ = "books"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String, nullable=False)
    author = Column(String, nullable=False)
    genre = Column(String)
    year_published = Column(Integer)
    content = Column(Text, nullable=False)
    summary = Column(Text, nullable=True)
    status = Column(String, default="pending")  # pending | processing | done | failed
    
    reviews = relationship(
        "Review",
        back_populates="book",
        cascade="all, delete-orphan"
    )


class Review(Base):
    __tablename__ = "reviews"

    id = Column(Integer, primary_key=True, index=True)

    # 🔴 FIX: must be UUID, not Integer
    book_id = Column(
        UUID(as_uuid=True),
        ForeignKey("books.id", ondelete="CASCADE"),
        nullable=False
    )

    user_id = Column(Integer, nullable=False)
    review_text = Column(Text)
    rating = Column(Float)

    book = relationship("Book", back_populates="reviews")


class Recommendation(Base):
    __tablename__ = "recommendations"

    id = Column(Integer, primary_key=True, index=True)

    # 🔴 FIX: UUID FKs
    book_id = Column(
        UUID(as_uuid=True),
        ForeignKey("books.id", ondelete="CASCADE"),
        nullable=False
    )

    recommended_book_id = Column(
        UUID(as_uuid=True),
        ForeignKey("books.id", ondelete="CASCADE"),
        nullable=False
    )

    book = relationship("Book", foreign_keys=[book_id])
    recommended_book = relationship("Book", foreign_keys=[recommended_book_id])


class UserBookInteraction(Base):
    __tablename__ = "user_book_interactions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False)

    # 🔴 FIX: UUID FK
    book_id = Column(
        UUID(as_uuid=True),
        ForeignKey("books.id", ondelete="CASCADE"),
        nullable=False
    )

    interaction_type = Column(String, nullable=False)
    timestamp = Column(String, nullable=False)

    book = relationship("Book")


class AIModelUsage(Base):
    __tablename__ = "ai_model_usages"

    id = Column(Integer, primary_key=True, index=True)
    model_name = Column(String, nullable=False)
    usage_count = Column(Integer, default=0)
