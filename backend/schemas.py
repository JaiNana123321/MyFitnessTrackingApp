from datetime import datetime, date
from typing import List, Optional
from pydantic import BaseModel


# ---------- Users ----------

class UserLogin(BaseModel):
    email: str
    name: Optional[str] = None
    surname: Optional[str] = None
    location: Optional[str] = None


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
    start_time: datetime
    end_time: datetime
    quality_score: Optional[int] = None


class SleepOut(BaseModel):
    sleep_id: int
    user_id: int
    start_time: datetime
    end_time: datetime
    quality_score: Optional[int] = None

    class Config:
        orm_mode = True


# ---------- Workouts ----------

class WorkoutSetCreate(BaseModel):
    exercise_id: int
    num_reps: int
    weight_amount: float
    set_order: int


class WorkoutWithSetsCreate(BaseModel):
    start_time: datetime
    end_time: datetime
    label: Optional[str] = None
    sets: List[WorkoutSetCreate]


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


# ---------- Meals ----------

class MealItemCreate(BaseModel):
    food_id: int
    quantity: float
    unit: str


class MealWithItemsCreate(BaseModel):
    time_of_meal: datetime
    meal_name: str
    items: List[MealItemCreate]


class MealItemOut(BaseModel):
    meal_item_id: int
    meal_id: int
    food_id: int
    quantity: float
    unit: str

    class Config:
        orm_mode = True


class MealOut(BaseModel):
    meal_id: int
    user_id: int
    time_of_meal: datetime
    meal_name: str
    items: List[MealItemOut] = []

    class Config:
        orm_mode = True


class DailyMealsSummary(BaseModel):
    date: date
    total_calories: float


# ---------- Dashboard Summary ----------

class SleepSummaryEntry(BaseModel):
    date: date
    hours: float
    quality_score: Optional[int] = None


class WorkoutsPerDay(BaseModel):
    date: date
    count: int


class CaloriesPerDay(BaseModel):
    date: date
    calories: float


class UserSummary(BaseModel):
    sleep: List[SleepSummaryEntry]
    workouts_per_day: List[WorkoutsPerDay]
    calories_per_day: List[CaloriesPerDay]