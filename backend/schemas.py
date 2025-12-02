# schemas.py
from datetime import datetime, date
from typing import List, Optional
from pydantic import BaseModel


# ---------- Users ----------

class UserBase(BaseModel):
    email: str
    name: Optional[str] = None
    surname: Optional[str] = None
    location: Optional[str] = None


class UserCreate(UserBase):
    pass


class UserLogin(UserBase):
    # same fields as UserBase; for now no password
    pass


class UserOut(BaseModel):
    user_id: int
    email: str
    name: Optional[str]
    surname: Optional[str]
    location: Optional[str]

    class Config:
        orm_mode = True


# ---------- Sleep ----------

class SleepCreate(BaseModel):
    user_id: int
    start_time: datetime
    end_time: datetime
    quality_score: Optional[int] = None


class SleepOut(BaseModel):
    sleep_id: int
    user_id: int
    start_time: datetime
    end_time: datetime
    quality_score: Optional[int]

    class Config:
        orm_mode = True


# ---------- Workouts & Sets ----------

class WorkoutCreate(BaseModel):
    user_id: int
    start_time: datetime
    end_time: datetime
    label: Optional[str] = None


class WorkoutSetCreate(BaseModel):
    workout_id: int
    exercise_id: int
    num_reps: int
    weight_amount: float
    set_order: int


class WorkoutSetOut(BaseModel):
    set_id: int
    workout_id: int
    exercise_id: int
    num_reps: int
    weight_amount: float
    set_order: int

    class Config:
        orm_mode = True


class WorkoutOut(BaseModel):
    workout_id: int
    user_id: int
    start_time: datetime
    end_time: datetime
    label: Optional[str]
    sets: List[WorkoutSetOut] = []

    class Config:
        orm_mode = True


class WorkoutSummary(BaseModel):
    workout_id: int
    date: date
    label: Optional[str]
    num_sets: int


# ---------- Foods ----------

class FoodCreate(BaseModel):
    food_name: str
    calories: float
    carbs: float
    fats: float
    protein: float
    sugar: float
    category: str
    serving_size_grams: float


class FoodOut(BaseModel):
    food_id: int
    food_name: str
    calories: float
    carbs: float
    fats: float
    protein: float
    sugar: float
    category: str
    serving_size_grams: float

    class Config:
        orm_mode = True



# ---------- Meals & Meal Items ----------

class MealItemCreate(BaseModel):
    meal_id: int
    food_id: int
    quantity: float  # number of servings (no unit)


class MealItemOut(BaseModel):
    meal_item_id: int
    meal_id: int
    food_id: int
    quantity: float  # number of servings

    class Config:
        orm_mode = True
class MealCreate(BaseModel):
    user_id: int
    time_of_meal: datetime
    meal_name: str


class MealOut(BaseModel):
    meal_id: int
    user_id: int
    time_of_meal: datetime
    meal_name: str
    meal_items: List[MealItemOut] = []

    class Config:
        orm_mode = True

class ExerciseCreate(BaseModel):
    exercise_name: str
    primary_muscle: Optional[str] = None
    secondary_muscle: Optional[str] = None


class ExerciseOut(BaseModel):
    exercise_id: int
    exercise_name: str
    primary_muscle: Optional[str] = None
    secondary_muscle: Optional[str] = None

    class Config:
        orm_mode = True


class ExercisePR(BaseModel):
    exercise_id: int
    exercise_name: str
    pr_weight: float  # max weight_amount this user has ever used for that exercise

    class Config:
        orm_mode = True

class MuscleBalanceEntry(BaseModel):
    week_start: date          # Monday (or DB's week start) of that training week
    primary_muscle: str
    volume: float             # sum of num_reps * weight_amount for that week + muscle

    class Config:
        orm_mode = True

# ---------- Dashboard Summary ----------

class SleepSummaryEntry(BaseModel):
    date: date
    hours: float
    quality_score: Optional[int] = None


class WorkoutsPerDay(BaseModel):
    date: date
    count: int
    total_weight: float

class CaloriesPerDay(BaseModel):
    date: date
    calories: float
    carbs: float
    fats: float
    protein: float

class UserSummary(BaseModel):
    sleep: List[SleepSummaryEntry]
    workouts_per_day: List[WorkoutsPerDay]
    calories_per_day: List[CaloriesPerDay]