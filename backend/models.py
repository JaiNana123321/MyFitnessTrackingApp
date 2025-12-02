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

    sets = relationship("WorkoutSet", back_populates="workout_set", cascade="all, delete-orphan")

class WorkoutSet(Base):
    __tablename__ = "workout_set"
    set_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    workout_id = Column(Integer, ForeignKey("workouts.workout_id", ondelete="CASCADE"), nullable=False)
    exercise_id = Column(Integer, ForeignKey("exercises.exercise_id", ondelete="CASCADE"), nullable=False)
    num_reps = Column(Integer, nullable=False)
    weight_amount = Column(Integer, nullable=False)
    set_order = Column(Integer, nullable=False)
    
    sets = relationship("Workouts", back_populates="workouts", cascade="all, delete-orphan")


class Workout(Base):
    __tablename__ = "workouts"
    workout_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    label = Column(String, nullable=True)

    user = relationship("User", back_populates="workouts")
    sets = relationship("WorkoutSet", back_populates="workout", cascade="all, delete-orphan")
    
class Meals(Base):
    __tablename__  = "meals"
    meal_id = Column(Integer,primary_key=True, index = True, autoincrement=True),
    user_id = Column(Integer, ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    time_of_meal = Column(DateTime, nullable = False)
    meal_name = Column(String, nullable=False)

    user = relationship("User", back_populates="meals")

class Meal_Items(Base):
    __tablename__ = "meal_items"
    meal_item_id = Column(Integer,primary_key=True, index = True, autoincrement= True),
    meal_id = Column(Integer, ForeignKey("meals.meal_id", ondelete = "CASCADE"), nullable = False)
    food_id = Column(Integer, ForeignKey("food.food_id", ondelete = "CASCADE"), nullable = False)
    quantity = Column(Float, nullable = False)
    unit = Column(String, nullable = False)

    food = relationship("Food", back_populates= "meal_items")
    meals = relationship("Meals", back_populates= "meal_items")
    
    
class Food(Base):
    __tablename__ = "food"
    food_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    food_name = Column(String, nullable=False)
    calories = Column(Float, nullable=False)
    carbs = Column(Float, nullable=False)
    fats = Column(Float, nullable=False)
    protien = Column(Float, nullable=False)
    sugar = Column(Float, nullable=False)
    category = Column(String, nullable=False)
    
    meal = relationship("Meals", back_populates="meals", cascade="all, delete-orphan")