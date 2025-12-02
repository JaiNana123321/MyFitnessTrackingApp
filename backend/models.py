# backend/models.py
from sqlalchemy import Column, Integer, String, DateTime, Float, ForeignKey
from sqlalchemy.orm import relationship
from database import Base

class User(Base):
    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String, nullable=True)
    surname = Column(String, nullable=True)
    email = Column(String, unique=True, index=True, nullable=False)
    location = Column(String, nullable=True)

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

    # One exercise -> many WorkoutSet rows
    sets = relationship("WorkoutSet", back_populates="exercise", cascade="all, delete-orphan")


class Workout(Base):
    __tablename__ = "workouts"

    workout_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    label = Column(String, nullable=True)

    user = relationship("User", back_populates="workouts")
    # One workout -> many sets
    sets = relationship("WorkoutSet", back_populates="workout", cascade="all, delete-orphan")


class WorkoutSet(Base):
    __tablename__ = "workout_sets"

    set_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    workout_id = Column(Integer, ForeignKey("workouts.workout_id", ondelete="CASCADE"), nullable=False)
    exercise_id = Column(Integer, ForeignKey("exercises.exercise_id", ondelete="CASCADE"), nullable=False)
    num_reps = Column(Integer, nullable=False)
    weight_amount = Column(Float, nullable=False)  # your schema says float
    set_order = Column(Integer, nullable=False)

    workout = relationship("Workout", back_populates="sets")
    exercise = relationship("Exercise", back_populates="sets")


class Meal(Base):
    __tablename__ = "meals"

    meal_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    time_of_meal = Column(DateTime, nullable=False)
    meal_name = Column(String, nullable=False)

    user = relationship("User", back_populates="meals")
    meal_items = relationship("MealItem", back_populates="meal", cascade="all, delete-orphan")

class Food(Base):
    __tablename__ = "foods"

    food_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    food_name = Column(String, nullable=False)
    calories = Column(Float, nullable=False)          # per serving
    carbs = Column(Float, nullable=False)             # per serving
    fats = Column(Float, nullable=False)              # per serving
    protein = Column(Float, nullable=False)           # per serving
    sugar = Column(Float, nullable=False)             # per serving
    category = Column(String, nullable=False)
    serving_size_grams = Column(Float, nullable=False)  # size of 1 serving in grams

    meal_items = relationship("MealItem", back_populates="food", cascade="all, delete-orphan")


class MealItem(Base):
    __tablename__ = "meal_items"

    meal_item_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    meal_id = Column(Integer, ForeignKey("meals.meal_id", ondelete="CASCADE"), nullable=False)
    food_id = Column(Integer, ForeignKey("foods.food_id", ondelete="CASCADE"), nullable=False)
    quantity = Column(Float, nullable=False)  # number of servings (relative to Food.serving_size_grams)

    meal = relationship("Meal", back_populates="meal_items")
    food = relationship("Food", back_populates="meal_items")