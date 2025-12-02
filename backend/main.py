from datetime import datetime, timedelta, date
from typing import List

from fastapi import FastAPI, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func

from database import engine, SessionLocal
import models
import schemas


app = FastAPI()


# ---------- DB setup ----------

@app.on_event("startup")
def on_startup():
    # Create all tables (dev only – safe, only creates missing tables)
    models.Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ---------- Health ----------

@app.get("/health")
def health():
    return {"status": "ok"}


# ---------- Users / Login ----------

@app.post("/users/login", response_model=schemas.UserOut)
def login(user_in: schemas.UserLogin, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == user_in.email).first()
    if user is None:
        user = models.User(
            email=user_in.email,
            name=user_in.name,
            surname=user_in.surname,
            location=user_in.location,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    return user


# ---------- Sleep ----------

@app.post("/users/{user_id}/sleep", response_model=schemas.SleepOut)
def add_sleep(user_id: int, sleep_in: schemas.SleepCreate, db: Session = Depends(get_db)):
    user = db.get(models.User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    sleep = models.Sleep(
        user_id=user_id,
        start_time=sleep_in.start_time,
        end_time=sleep_in.end_time,
        quality_score=sleep_in.quality_score,
    )
    db.add(sleep)
    db.commit()
    db.refresh(sleep)
    return sleep


@app.get("/users/{user_id}/sleep/recent", response_model=List[schemas.SleepOut])
def get_recent_sleep(
    user_id: int,
    days: int = Query(7, ge=1, le=90),
    db: Session = Depends(get_db),
):
    cutoff = datetime.utcnow() - timedelta(days=days)
    sleeps = (
        db.query(models.Sleep)
        .filter(models.Sleep.user_id == user_id,
                models.Sleep.start_time >= cutoff)
        .order_by(models.Sleep.start_time.desc())
        .all()
    )
    return sleeps


# ---------- Workouts ----------

@app.post("/users/{user_id}/workouts/with_sets", response_model=schemas.WorkoutOut)
def create_workout_with_sets(
    user_id: int,
    payload: schemas.WorkoutWithSetsCreate,
    db: Session = Depends(get_db),
):
    user = db.get(models.User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    workout = models.Workout(
        user_id=user_id,
        start_time=payload.start_time,
        end_time=payload.end_time,
        label=payload.label,
    )
    db.add(workout)
    db.flush()  # assign workout_id

    for s in payload.sets:
        ws = models.WorkoutSet(
            workout_id=workout.workout_id,
            exercise_id=s.exercise_id,
            num_reps=s.num_reps,
            weight_amount=s.weight_amount,
            set_order=s.set_order,
        )
        db.add(ws)

    db.commit()
    db.refresh(workout)
    # force-load sets for response
    _ = workout.sets
    return workout


@app.get("/users/{user_id}/workouts/recent", response_model=List[schemas.WorkoutSummary])
def recent_workouts(
    user_id: int,
    days: int = Query(7, ge=1, le=90),
    db: Session = Depends(get_db),
):
    cutoff = datetime.utcnow() - timedelta(days=days)

    # get workouts and number of sets
    results = (
        db.query(
            models.Workout.workout_id,
            func.date(models.Workout.start_time).label("date"),
            models.Workout.label,
            func.count(models.WorkoutSet.set_id).label("num_sets"),
        )
        .outerjoin(models.WorkoutSet, models.Workout.workout_id == models.WorkoutSet.workout_id)
        .filter(models.Workout.user_id == user_id,
                models.Workout.start_time >= cutoff)
        .group_by(models.Workout.workout_id, func.date(models.Workout.start_time), models.Workout.label)
        .order_by(func.date(models.Workout.start_time).desc())
        .all()
    )

    return [
        schemas.WorkoutSummary(
            workout_id=row.workout_id,
            date=row.date,
            label=row.label,
            num_sets=row.num_sets,
        )
        for row in results
    ]


# ---------- Meals ----------

@app.post("/users/{user_id}/meals/with_items", response_model=schemas.MealOut)
def create_meal_with_items(
    user_id: int,
    payload: schemas.MealWithItemsCreate,
    db: Session = Depends(get_db),
):
    user = db.get(models.User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    meal = models.Meal(
        user_id=user_id,
        time_of_meal=payload.time_of_meal,
        meal_name=payload.meal_name,
    )
    db.add(meal)
    db.flush()  # assign meal_id

    for item in payload.items:
        mi = models.MealItem(
            meal_id=meal.meal_id,
            food_id=item.food_id,
            quantity=item.quantity,
            unit=item.unit,
        )
        db.add(mi)

    db.commit()
    db.refresh(meal)
    _ = meal.meal_items  # load items
    return meal


@app.get("/users/{user_id}/meals/day", response_model=List[schemas.MealOut])
def get_meals_for_day(
    user_id: int,
    date_str: str = Query(..., description="YYYY-MM-DD"),
    db: Session = Depends(get_db),
):
    try:
        target_date = datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format (expected YYYY-MM-DD)")

    next_day = target_date + timedelta(days=1)

    meals = (
        db.query(models.Meal)
        .filter(
            models.Meal.user_id == user_id,
            models.Meal.time_of_meal >= datetime.combine(target_date, datetime.min.time()),
            models.Meal.time_of_meal < datetime.combine(next_day, datetime.min.time()),
        )
        .order_by(models.Meal.time_of_meal.asc())
        .all()
    )

    # force-load items
    for m in meals:
        _ = m.meal_items

    return meals


# ---------- User Summary (for dashboard) ----------

@app.get("/users/{user_id}/summary", response_model=schemas.UserSummary)
def user_summary(
    user_id: int,
    days: int = Query(7, ge=1, le=90),
    db: Session = Depends(get_db),
):
    cutoff_date = (datetime.utcnow() - timedelta(days=days)).date()

    # Sleep entries
    sleeps = (
        db.query(models.Sleep)
        .filter(
            models.Sleep.user_id == user_id,
            models.Sleep.start_time >= datetime.combine(cutoff_date, datetime.min.time()),
        )
        .order_by(models.Sleep.start_time.asc())
        .all()
    )

    sleep_entries: List[schemas.SleepSummaryEntry] = []
    for s in sleeps:
        hours = (s.end_time - s.start_time).total_seconds() / 3600.0
        sleep_entries.append(
            schemas.SleepSummaryEntry(
                date=s.start_time.date(),
                hours=hours,
                quality_score=s.quality_score,
            )
        )

    # Workouts per day
    workout_rows = (
        db.query(
            func.date(models.Workout.start_time).label("date"),
            func.count(models.Workout.workout_id).label("count"),
        )
        .filter(
            models.Workout.user_id == user_id,
            models.Workout.start_time >= datetime.combine(cutoff_date, datetime.min.time()),
        )
        .group_by(func.date(models.Workout.start_time))
        .order_by(func.date(models.Workout.start_time).asc())
        .all()
    )

    workouts_per_day = [
        schemas.WorkoutsPerDay(date=row.date, count=row.count)
        for row in workout_rows
    ]

    # Calories per day
    # join Meal, MealItem, Food
    cal_rows = (
        db.query(
            func.date(models.Meal.time_of_meal).label("date"),
            func.sum(models.MealItem.quantity * models.Food.calories).label("calories"),
        )
        .join(models.MealItem, models.Meal.meal_id == models.MealItem.meal_id)
        .join(models.Food, models.MealItem.food_id == models.Food.food_id)
        .filter(
            models.Meal.user_id == user_id,
            models.Meal.time_of_meal >= datetime.combine(cutoff_date, datetime.min.time()),
        )
        .group_by(func.date(models.Meal.time_of_meal))
        .order_by(func.date(models.Meal.time_of_meal).asc())
        .all()
    )

    calories_per_day = [
        schemas.CaloriesPerDay(date=row.date, calories=row.calories or 0.0)
        for row in cal_rows
    ]

    return schemas.UserSummary(
        sleep=sleep_entries,
        workouts_per_day=workouts_per_day,
        calories_per_day=calories_per_day,
    )