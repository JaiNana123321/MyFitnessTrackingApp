# backend/models.py
from sqlalchemy import Column, Integer, String, DateTime, Float, ForeignKey
from sqlalchemy.orm import relationship
from .database import Base  # from the file above


class User(Base):
    __tablename__ = "users"  # table name in Postgres

    user_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String, nullable=True)
    surname = Column(String, nullable=True)
    email = Column(String, unique=True, index=True, nullable=False)
    location = Column(String, nullable=True)

    # relationships
    sleeps = relationship("Sleep", back_populates="user", cascade="all, delete-orphan")
    workouts = relationship("Workout", back_populates="user", cascade="all, delete-orphan")
    meals = relationship("Meal", back_populates="user", cascade="all, delete-orphan")


class Sleep(Base):
    __tablename__ = "sleep"

    sleep_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    quality_score = Column(Integer, nullable=True)  # 1–10

    user = relationship("User", back_populates="sleeps")


class Exercise(Base):
    __tablename__ = "exercises"
    exercise_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    exercise_name = Column(String, nullable=False)
    primary_muscle = Column(String, nullable=True)
    secondary_muscle = Column(String, nullable=True)
    # relationship to WorkoutSet via back_populates if you like


class Workout(Base):
    __tablename__ = "workouts"
    workout_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    label = Column(String, nullable=True)

    user = relationship("User", back_populates="workouts")
    sets = relationship("WorkoutSet", back_populates="workout", cascade="all, delete-orphan")