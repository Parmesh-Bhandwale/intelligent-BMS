from sqlalchemy import Column, Integer, String, Text, ForeignKey, Float
from sqlalchemy.orm import relationship
from app.db.base import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=False)
    email = Column(String, unique=True, nullable=False)
    hashed_password = Column(String, nullable=False )

class Book(Base):
    __tablename__ = "books"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    author = Column(String, nullable=False)
    genre = Column(String)
    year_published = Column(Integer)
    summary = Column(Text, nullable=True)

    reviews = relationship("Review", back_populates="book", cascade="all, delete")

class Review(Base):
    __tablename__ = "reviews"

    id = Column(Integer, primary_key=True, index=True)
    book_id = Column(Integer, ForeignKey("books.id"))
    user_id = Column(Integer)  # Linked to Auth User
    review_text = Column(Text)
    rating = Column(Float)

    book = relationship("Book", back_populates="reviews")

class Recommendation(Base):
    __tablename__ = "recommendations"

    id = Column(Integer, primary_key=True, index=True)
    book_id = Column(Integer, ForeignKey("books.id"))
    recommended_book_id = Column(Integer, ForeignKey("books.id"))

    book = relationship("Book", foreign_keys=[book_id])
    recommended_book = relationship("Book", foreign_keys=[recommended_book_id])

class UserBookInteraction(Base):
    __tablename__ = "user_book_interactions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer)  # Linked to Auth User
    book_id = Column(Integer, ForeignKey("books.id"))
    interaction_type = Column(String)  # e.g., "viewed", "purchased", "rated"
    timestamp = Column(String)  # ISO formatted timestamp

    book = relationship("Book")

class AIModelUsage(Base):
    __tablename__ = "ai_model_usages"

    id = Column(Integer, primary_key=True, index=True)
    model_name = Column(String, nullable=False)
    usage_count = Column(Integer, default=0)

