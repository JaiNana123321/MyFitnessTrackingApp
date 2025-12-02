# main.py
from datetime import datetime, timedelta
from typing import List

from fastapi import FastAPI, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func

from database import engine, SessionLocal
import models
import schemas


app = FastAPI()


# Initialize database tables on startup (dev convenience, safe no-op if tables exist)
@app.on_event("startup")
def on_startup():
    models.Base.metadata.create_all(bind=engine)


# Dependency to get a database session for each request
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Health check endpoint to verify the backend is alive and responding
@app.get("/health")
def health():
    return {"status": "ok"}


# Create a new user explicitly (usually used for seeding/testing, not main login flow)
@app.post("/users", response_model=schemas.UserOut)
def create_user(user_in: schemas.UserCreate, db: Session = Depends(get_db)):
    # SQL: SELECT * FROM users WHERE email = :email LIMIT 1;
    existing = db.query(models.User).filter(models.User.email == user_in.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="User with this email already exists")

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


# Delete a user and all their related data (sleep, workouts, meals via cascades)
@app.delete("/users/{user_id}")
def delete_user(user_id: int, db: Session = Depends(get_db)):
    # SQL: SELECT * FROM users WHERE user_id = :user_id;
    user = db.get(models.User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    # SQL: DELETE FROM users WHERE user_id = :user_id;
    db.delete(user)
    db.commit()
    return {"detail": "User deleted"}


# Login (or auto-create) a user using their email, no password/auth for now
@app.post("/users/login", response_model=schemas.UserOut)
def login(user_in: schemas.UserLogin, db: Session = Depends(get_db)):
    # SQL: SELECT * FROM users WHERE email = :email LIMIT 1;
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


# Create a new sleep entry for a user
@app.post("/sleep", response_model=schemas.SleepOut)
def create_sleep(sleep_in: schemas.SleepCreate, db: Session = Depends(get_db)):
    # SQL: SELECT * FROM users WHERE user_id = :user_id;
    user = db.get(models.User, sleep_in.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    sleep = models.Sleep(
        user_id=sleep_in.user_id,
        start_time=sleep_in.start_time,
        end_time=sleep_in.end_time,
        quality_score=sleep_in.quality_score,
    )
    db.add(sleep)
    db.commit()
    db.refresh(sleep)
    return sleep


# Delete a specific sleep entry by its ID
@app.delete("/sleep/{sleep_id}")
def delete_sleep(sleep_id: int, db: Session = Depends(get_db)):
    # SQL: SELECT * FROM sleep WHERE sleep_id = :sleep_id;
    sleep = db.get(models.Sleep, sleep_id)
    if not sleep:
        raise HTTPException(status_code=404, detail="Sleep entry not found")
    # SQL: DELETE FROM sleep WHERE sleep_id = :sleep_id;
    db.delete(sleep)
    db.commit()
    return {"detail": "Sleep entry deleted"}


# Get recent sleep entries for a user within the last N days
@app.get("/sleep/recent", response_model=List[schemas.SleepOut])
def get_sleep_recent(
    user_id: int = Query(...),
    days: int = Query(7, ge=1, le=90),
    db: Session = Depends(get_db),
):
    cutoff = datetime.utcnow() - timedelta(days=days)

    # SQL: SELECT * FROM sleep WHERE user_id = :user_id AND start_time >= :cutoff ORDER BY start_time DESC;
    sleeps = (
        db.query(models.Sleep)
        .filter(models.Sleep.user_id == user_id,
                models.Sleep.start_time >= cutoff)
        .order_by(models.Sleep.start_time.desc())
        .all()
    )
    return sleeps


# Get all sleep entries for a user (no date restriction)
@app.get("/sleep/all", response_model=List[schemas.SleepOut])
def get_sleep_all(
    user_id: int = Query(...),
    db: Session = Depends(get_db),
):
    # SQL: SELECT * FROM sleep WHERE user_id = :user_id ORDER BY start_time DESC;
    sleeps = (
        db.query(models.Sleep)
        .filter(models.Sleep.user_id == user_id)
        .order_by(models.Sleep.start_time.desc())
        .all()
    )
    return sleeps


# Create a new workout (without sets) for a user
@app.post("/workouts", response_model=schemas.WorkoutOut)
def create_workout(workout_in: schemas.WorkoutCreate, db: Session = Depends(get_db)):
    # SQL: SELECT * FROM users WHERE user_id = :user_id;
    user = db.get(models.User, workout_in.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    workout = models.Workout(
        user_id=workout_in.user_id,
        start_time=workout_in.start_time,
        end_time=workout_in.end_time,
        label=workout_in.label,
    )
    db.add(workout)
    db.commit()
    db.refresh(workout)
    # Force-load sets relationship (empty at creation) to keep response shape consistent
    _ = workout.sets
    return workout


# Delete a workout and all its sets (cascade)
@app.delete("/workouts/{workout_id}")
def delete_workout(workout_id: int, db: Session = Depends(get_db)):
    # SQL: SELECT * FROM workouts WHERE workout_id = :workout_id;
    workout = db.get(models.Workout, workout_id)
    if not workout:
        raise HTTPException(status_code=404, detail="Workout not found")
    # SQL: DELETE FROM workouts WHERE workout_id = :workout_id;
    db.delete(workout)
    db.commit()
    return {"detail": "Workout deleted"}


# Create a workout set for an existing workout and exercise
@app.post("/workout_sets", response_model=schemas.WorkoutSetOut)
def create_workout_set(set_in: schemas.WorkoutSetCreate, db: Session = Depends(get_db)):
    # SQL: SELECT * FROM workouts WHERE workout_id = :workout_id;
    workout = db.get(models.Workout, set_in.workout_id)
    if not workout:
        raise HTTPException(status_code=404, detail="Workout not found")

    # SQL: SELECT * FROM exercises WHERE exercise_id = :exercise_id;
    exercise = db.get(models.Exercise, set_in.exercise_id)
    if not exercise:
        raise HTTPException(status_code=404, detail="Exercise not found")

    ws = models.WorkoutSet(
        workout_id=set_in.workout_id,
        exercise_id=set_in.exercise_id,
        num_reps=set_in.num_reps,
        weight_amount=set_in.weight_amount,
        set_order=set_in.set_order,
    )
    db.add(ws)
    db.commit()
    db.refresh(ws)
    return ws


# Delete a specific workout set
@app.delete("/workout_sets/{set_id}")
def delete_workout_set(set_id: int, db: Session = Depends(get_db)):
    # SQL: SELECT * FROM workout_sets WHERE set_id = :set_id;
    ws = db.get(models.WorkoutSet, set_id)
    if not ws:
        raise HTTPException(status_code=404, detail="Workout set not found")
    # SQL: DELETE FROM workout_sets WHERE set_id = :set_id;
    db.delete(ws)
    db.commit()
    return {"detail": "Workout set deleted"}


# Get recent workouts for a user (summary view: date, label, number of sets)
@app.get("/workouts/recent", response_model=List[schemas.WorkoutSummary])
def get_workouts_recent(
    user_id: int = Query(...),
    days: int = Query(7, ge=1, le=90),
    db: Session = Depends(get_db),
):
    cutoff = datetime.utcnow() - timedelta(days=days)

    # SQL:
    # SELECT w.workout_id,
    #        DATE(w.start_time) AS date,
    #        w.label,
    #        COUNT(ws.set_id) AS num_sets
    # FROM workouts w
    # LEFT JOIN workout_sets ws ON w.workout_id = ws.workout_id
    # WHERE w.user_id = :user_id AND w.start_time >= :cutoff
    # GROUP BY w.workout_id, DATE(w.start_time), w.label
    # ORDER BY DATE(w.start_time) DESC;
    rows = (
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
        for row in rows
    ]


# Get all workouts for a user including their sets
@app.get("/workouts/all", response_model=List[schemas.WorkoutOut])
def get_workouts_all(
    user_id: int = Query(...),
    db: Session = Depends(get_db),
):
    # SQL: SELECT * FROM workouts WHERE user_id = :user_id ORDER BY start_time DESC;
    workouts = (
        db.query(models.Workout)
        .filter(models.Workout.user_id == user_id)
        .order_by(models.Workout.start_time.desc())
        .all()
    )

    # For each workout, load its sets (SQLAlchemy will issue SELECTs as needed)
    for w in workouts:
        # SQL: SELECT * FROM workout_sets WHERE workout_id = :workout_id;
        _ = w.sets

    return workouts


# Create a new food item in the catalog
@app.post("/foods", response_model=schemas.FoodOut)
def create_food(food_in: schemas.FoodCreate, db: Session = Depends(get_db)):
    food = models.Food(
        food_name=food_in.food_name,
        calories=food_in.calories,
        carbs=food_in.carbs,
        fats=food_in.fats,
        protein=food_in.protein,
        sugar=food_in.sugar,
        category=food_in.category,
        serving_size_grams=food_in.serving_size_grams,
    )
    db.add(food)
    db.commit()
    db.refresh(food)
    return food


# Delete a food item (may fail if referenced by meal_items depending on DB constraints)
@app.delete("/foods/{food_id}")
def delete_food(food_id: int, db: Session = Depends(get_db)):
    # SQL: SELECT * FROM foods WHERE food_id = :food_id;
    food = db.get(models.Food, food_id)
    if not food:
        raise HTTPException(status_code=404, detail="Food not found")
    # SQL: DELETE FROM foods WHERE food_id = :food_id;
    db.delete(food)
    db.commit()
    return {"detail": "Food deleted"}


# Get all food items (for dropdowns / autocomplete sources)
@app.get("/foods/all", response_model=List[schemas.FoodOut])
def get_foods_all(db: Session = Depends(get_db)):
    # SQL: SELECT * FROM foods ORDER BY food_name ASC;
    foods = db.query(models.Food).order_by(models.Food.food_name.asc()).all()
    return foods


# Search foods by a text query in the food_name
@app.get("/foods/search", response_model=List[schemas.FoodOut])
def search_foods(
    query: str = Query(..., min_length=1),
    db: Session = Depends(get_db),
):
    q = f"%{query.lower()}%"

    # SQL: SELECT * FROM foods WHERE LOWER(food_name) LIKE :q ORDER BY food_name ASC;
    foods = (
        db.query(models.Food)
        .filter(func.lower(models.Food.food_name).like(q))
        .order_by(models.Food.food_name.asc())
        .all()
    )
    return foods


# Create a new meal (without items) for a user
@app.post("/meals", response_model=schemas.MealOut)
def create_meal(meal_in: schemas.MealCreate, db: Session = Depends(get_db)):
    # SQL: SELECT * FROM users WHERE user_id = :user_id;
    user = db.get(models.User, meal_in.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    meal = models.Meal(
        user_id=meal_in.user_id,
        time_of_meal=meal_in.time_of_meal,
        meal_name=meal_in.meal_name,
    )
    db.add(meal)
    db.commit()
    db.refresh(meal)
    # SQL: SELECT * FROM meal_items WHERE meal_id = :meal_id;
    _ = meal.meal_items
    return meal


# Delete a meal and all its meal items (cascade)
@app.delete("/meals/{meal_id}")
def delete_meal(meal_id: int, db: Session = Depends(get_db)):
    # SQL: SELECT * FROM meals WHERE meal_id = :meal_id;
    meal = db.get(models.Meal, meal_id)
    if not meal:
        raise HTTPException(status_code=404, detail="Meal not found")
    # SQL: DELETE FROM meals WHERE meal_id = :meal_id;
    db.delete(meal)
    db.commit()
    return {"detail": "Meal deleted"}


# Create a new meal_item for an existing meal and food
@app.post("/meal_items", response_model=schemas.MealItemOut)
def create_meal_item(item_in: schemas.MealItemCreate, db: Session = Depends(get_db)):
    # SQL: SELECT * FROM meals WHERE meal_id = :meal_id;
    meal = db.get(models.Meal, item_in.meal_id)
    if not meal:
        raise HTTPException(status_code=404, detail="Meal not found")

    # SQL: SELECT * FROM foods WHERE food_id = :food_id;
    food = db.get(models.Food, item_in.food_id)
    if not food:
        raise HTTPException(status_code=404, detail="Food not found")

    # quantity is interpreted as "number of servings" of this Food
    mi = models.MealItem(
        meal_id=item_in.meal_id,
        food_id=item_in.food_id,
        quantity=item_in.quantity,
    )
    db.add(mi)
    db.commit()
    db.refresh(mi)
    return mi


# Delete a specific meal item
@app.delete("/meal_items/{meal_item_id}")
def delete_meal_item(meal_item_id: int, db: Session = Depends(get_db)):
    # SQL: SELECT * FROM meal_items WHERE meal_item_id = :meal_item_id;
    mi = db.get(models.MealItem, meal_item_id)
    if not mi:
        raise HTTPException(status_code=404, detail="Meal item not found")
    # SQL: DELETE FROM meal_items WHERE meal_item_id = :meal_item_id;
    db.delete(mi)
    db.commit()
    return {"detail": "Meal item deleted"}


# Get recent meals for a user (with all meal items) within the last N days
@app.get("/meals/recent", response_model=List[schemas.MealOut])
def get_meals_recent(
    user_id: int = Query(...),
    days: int = Query(7, ge=1, le=90),
    db: Session = Depends(get_db),
):
    cutoff = datetime.utcnow() - timedelta(days=days)

    # SQL: SELECT * FROM meals WHERE user_id = :user_id AND time_of_meal >= :cutoff ORDER BY time_of_meal DESC;
    meals = (
        db.query(models.Meal)
        .filter(models.Meal.user_id == user_id,
                models.Meal.time_of_meal >= cutoff)
        .order_by(models.Meal.time_of_meal.desc())
        .all()
    )

    for m in meals:
        # SQL: SELECT * FROM meal_items WHERE meal_id = :meal_id;
        _ = m.meal_items

    return meals


# Get all meals for a user (with all meal items)
@app.get("/meals/all", response_model=List[schemas.MealOut])
def get_meals_all(
    user_id: int = Query(...),
    db: Session = Depends(get_db),
):
    # SQL: SELECT * FROM meals WHERE user_id = :user_id ORDER BY time_of_meal DESC;
    meals = (
        db.query(models.Meal)
        .filter(models.Meal.user_id == user_id)
        .order_by(models.Meal.time_of_meal.desc())
        .all()
    )

    for m in meals:
        # SQL: SELECT * FROM meal_items WHERE meal_id = :meal_id;
        _ = m.meal_items

    return meals


# Dashboard summary: sleep, workout counts, and daily calories/macros over last N days
@app.get("/users/{user_id}/summary", response_model=schemas.UserSummary)
def user_summary(
    user_id: int,
    days: int = Query(7, ge=1, le=90),
    db: Session = Depends(get_db),
):
    cutoff_date = (datetime.utcnow() - timedelta(days=days)).date()

    # Sleep summary per entry (later grouped in frontend if needed)
    # SQL: SELECT * FROM sleep WHERE user_id = :user_id AND start_time >= :cutoff ORDER BY start_time ASC;
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

    # Workouts per day: count how many workouts occurred on each date
    # SQL:
    # SELECT DATE(start_time) AS date, COUNT(*) AS count
    # FROM workouts
    # WHERE user_id = :user_id AND start_time >= :cutoff
    # GROUP BY DATE(start_time)
    # ORDER BY DATE(start_time) ASC;
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

    # Daily nutrition: calories, carbs, fats, protein per day
    # SQL:
    # SELECT DATE(m.time_of_meal) AS date,
    #        SUM(mi.quantity * f.calories) AS calories,
    #        SUM(mi.quantity * f.carbs)    AS carbs,
    #        SUM(mi.quantity * f.fats)     AS fats,
    #        SUM(mi.quantity * f.protein)  AS protein
    # FROM meals m
    # JOIN meal_items mi ON m.meal_id = mi.meal_id
    # JOIN foods f ON mi.food_id = f.food_id
    # WHERE m.user_id = :user_id AND m.time_of_meal >= :cutoff
    # GROUP BY DATE(m.time_of_meal)
    # ORDER BY DATE(m.time_of_meal) ASC;
    macro_rows = (
        db.query(
            func.date(models.Meal.time_of_meal).label("date"),
            func.sum(models.MealItem.quantity * models.Food.calories).label("calories"),
            func.sum(models.MealItem.quantity * models.Food.carbs).label("carbs"),
            func.sum(models.MealItem.quantity * models.Food.fats).label("fats"),
            func.sum(models.MealItem.quantity * models.Food.protein).label("protein"),
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
        schemas.CaloriesPerDay(
            date=row.date,
            calories=row.calories or 0.0,
            carbs=row.carbs or 0.0,
            fats=row.fats or 0.0,
            protein=row.protein or 0.0,
        )
        for row in macro_rows
    ]

    return schemas.UserSummary(
        sleep=sleep_entries,
        workouts_per_day=workouts_per_day,
        calories_per_day=calories_per_day,
    )