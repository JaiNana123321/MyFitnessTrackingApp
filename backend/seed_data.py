"""
Seed the Workoutify database with realistic demo data.

- 5 users
- 10 exercises
- 10 foods
- For each user, last 30 days of:
    * Sleep: 5–10 hours per day
    * Meals: 3 meals per day (Breakfast, Lunch, Dinner)
    * Workouts: 3–6 days per week with 1 workout per day
      - For one special user, 1 day per week has 2 workouts

Run (inside Docker):
    docker compose exec backend python seed_data.py
"""

import random
from datetime import datetime, date, time, timedelta
from collections import defaultdict

from database import SessionLocal, engine
import models


# Ensure tables exist
models.Base.metadata.create_all(bind=engine)


def clear_existing_data(session):
    """
    WARNING: This deletes existing data in a safe FK order.
    Comment out this function call in main() if you don't want to wipe.
    """
    session.query(models.MealItem).delete()
    session.query(models.Meal).delete()
    session.query(models.WorkoutSet).delete()
    session.query(models.Workout).delete()
    session.query(models.Sleep).delete()
    session.query(models.Food).delete()
    session.query(models.Exercise).delete()
    session.query(models.User).delete()
    session.commit()


def create_users(session):
    users = [
        models.User(email="alice@example.com",   name="Alice",   surname="Anderson", location="Cleveland"),
        models.User(email="bob@example.com",     name="Bob",     surname="Brown",    location="Boston"),
        models.User(email="charlie@example.com", name="Charlie", surname="Clark",    location="Chicago"),
        models.User(email="dana@example.com",    name="Dana",    surname="Davis",    location="Denver"),
        models.User(email="eric@example.com",    name="Eric",    surname="Evans",    location="Seattle"),
    ]
    session.add_all(users)
    session.commit()
    for u in users:
        session.refresh(u)
    return users


def create_exercises(session):
    exercises = [
        ("Back Squat",        "Quads",     "Glutes"),
        ("Front Squat",       "Quads",     "Core"),
        ("Bench Press",       "Chest",     "Triceps"),
        ("Incline Bench",     "Chest",     "Shoulders"),
        ("Deadlift",          "Hamstrings","Back"),
        ("Barbell Row",       "Back",      "Biceps"),
        ("Overhead Press",    "Shoulders", "Triceps"),
        ("Lat Pulldown",      "Back",      "Biceps"),
        ("Romanian Deadlift", "Hamstrings","Glutes"),
        ("Bicep Curl",        "Biceps",    "Forearms"),
    ]

    objs = []
    for name, primary, secondary in exercises:
        e = models.Exercise(
            exercise_name=name,
            primary_muscle=primary,
            secondary_muscle=secondary,
        )
        objs.append(e)

    session.add_all(objs)
    session.commit()
    for e in objs:
        session.refresh(e)
    return objs


def create_foods(session):
    foods = [
        ("Chicken Breast", 165.0, 0.0, 3.6, 31.0, 0.0,  "Protein", 100.0),
        ("White Rice",     130.0, 28.0, 0.3, 2.7, 0.1,  "Carb",    100.0),
        ("Olive Oil",      119.0, 0.0,  13.5, 0.0, 0.0, "Fat",     15.0),
        ("Broccoli",       55.0,  11.0, 0.6, 3.7, 2.2,  "Veg",     100.0),
        ("Oats",           389.0, 66.0, 6.9, 16.9, 0.0, "Carb",    100.0),
        ("Greek Yogurt",   59.0,  3.6,  0.4, 10.0, 3.2, "Protein", 100.0),
        ("Banana",         89.0,  23.0, 0.3, 1.1, 12.0, "Fruit",   118.0),
        ("Peanut Butter",  188.0, 6.0,  16.0, 8.0, 3.0, "Fat",     32.0),
        ("Salmon",         208.0, 0.0,  13.0, 20.0, 0.0,"Protein", 100.0),
        ("Sweet Potato",   86.0,  20.0, 0.1, 1.6, 4.2,  "Carb",    130.0),
    ]

    objs = []
    for name, cal, carbs, fats, protein, sugar, cat, serving in foods:
        f = models.Food(
            food_name=name,
            calories=cal,
            carbs=carbs,
            fats=fats,
            protein=protein,
            sugar=sugar,
            category=cat,
            serving_size_grams=serving,
        )
        objs.append(f)

    session.add_all(objs)
    session.commit()
    for f in objs:
        session.refresh(f)
    return objs


def generate_date_range(days_back: int = 30):
    """
    Returns a list of dates from 'days_back' days ago up to yesterday (oldest first).
    """
    today = date.today()
    dates = [today - timedelta(days=i) for i in range(days_back, 0, -1)]
    return dates


def build_weekly_workout_schedule(dates):
    """
    For each week in 'dates', choose 3–6 days where a workout happens.
    Returns: dict[(year, week)] -> list[date chosen_for_workout]
    """
    by_week = defaultdict(list)
    for d in dates:
        iso = d.isocalendar()  # (year, week, weekday)
        key = (iso[0], iso[1])
        by_week[key].append(d)

    schedule = {}
    for key, week_dates in by_week.items():
        # choose 3–6 unique days, but not more than available
        k = random.randint(3, 6)
        k = min(k, len(week_dates))
        chosen = random.sample(week_dates, k=k)
        schedule[key] = chosen

    return schedule  # e.g., {(2025, 48): [date1, date3, ...], ...}


def create_sleep_for_user(session, user, dates):
    """
    For each date, create one sleep entry lasting 5–10 hours.
    We'll assume sleep starts late evening of that date.
    """
    for d in dates:
        # Sleep start between 22:00 and 01:00
        start_hour = random.choice([22, 23, 0])
        start_dt = datetime.combine(d, time(start_hour, 0))
        # Sleep duration 5–10 hours
        hours = random.uniform(5.0, 10.0)
        end_dt = start_dt + timedelta(hours=hours)

        quality = random.randint(5, 9)

        s = models.Sleep(
            user_id=user.user_id,
            start_time=start_dt,
            end_time=end_dt,
            quality_score=quality,
        )
        session.add(s)

    session.commit()


def create_meals_for_user(session, user, dates, foods):
    """
    For each date, create 3 meals: Breakfast, Lunch, Dinner.
    Each meal has 1–3 food items with 0.5–2.0 servings.
    """
    meal_templates = [
        ("Breakfast", time(8, 0)),
        ("Lunch",     time(13, 0)),
        ("Dinner",    time(19, 0)),
    ]

    for d in dates:
        for meal_name, t in meal_templates:
            time_of_meal = datetime.combine(d, t)

            meal = models.Meal(
                user_id=user.user_id,
                time_of_meal=time_of_meal,
                meal_name=meal_name,
            )
            session.add(meal)
            session.flush()  # get meal_id

            num_items = random.randint(1, 3)
            for _ in range(num_items):
                food = random.choice(foods)
                quantity = random.choice([0.5, 1.0, 1.5, 2.0])  # servings

                mi = models.MealItem(
                    meal_id=meal.meal_id,
                    food_id=food.food_id,
                    quantity=quantity,
                )
                session.add(mi)

    session.commit()


def create_workouts_for_user(session, user, dates, exercises, is_special_user=False):
    """
    Create workouts for a user over the given dates:
    - 3–6 days per week, 1 workout per selected day
    - For is_special_user: one extra workout (2 workouts in 1 day) per week
    """
    # Build weekly schedule (which days in each week have workouts)
    weekly_schedule = build_weekly_workout_schedule(dates)

    # Map date -> number of workouts on that date
    date_to_num_workouts = defaultdict(int)

    for (year, week), days_in_week in weekly_schedule.items():
        # base: 1 workout per chosen day
        for d in days_in_week:
            date_to_num_workouts[d] += 1

        # special user: add one extra workout on a random chosen day
        if is_special_user and days_in_week:
            extra_day = random.choice(days_in_week)
            date_to_num_workouts[extra_day] += 1

    # Now actually create the workout + sets for each date
    for d in dates:
        num_workouts = date_to_num_workouts.get(d, 0)
        for n in range(num_workouts):
            # Workout times: 17:00 or 19:00 if second workout
            start_hour = 17 if n == 0 else 19
            start_dt = datetime.combine(d, time(start_hour, 0))
            end_dt = start_dt + timedelta(hours=1)

            workout = models.Workout(
                user_id=user.user_id,
                start_time=start_dt,
                end_time=end_dt,
                label=random.choice(["Push", "Pull", "Legs", "Upper", "Full Body"]),
            )
            session.add(workout)
            session.flush()  # get workout_id

            # Create sets: 3–6 sets per workout
            num_sets = random.randint(3, 6)
            for set_order in range(1, num_sets + 1):
                exercise = random.choice(exercises)
                reps = random.choice([5, 8, 10, 12])
                weight = random.choice([30.0, 40.0, 50.0, 60.0, 80.0, 100.0])

                ws = models.WorkoutSet(
                    workout_id=workout.workout_id,
                    exercise_id=exercise.exercise_id,
                    num_reps=reps,
                    weight_amount=weight,
                    set_order=set_order,
                )
                session.add(ws)

    session.commit()


def main():
    session = SessionLocal()

    # Comment this out if you don't want to wipe existing data
    clear_existing_data(session)

    users = create_users(session)
    exercises = create_exercises(session)
    foods = create_foods(session)

    # Use last 30 days (oldest first)
    dates = generate_date_range(days_back=30)

    # Make first user the "special" one with 2-workout days
    special_user_id = users[0].user_id

    for u in users:
        is_special = (u.user_id == special_user_id)
        create_sleep_for_user(session, u, dates)
        create_meals_for_user(session, u, dates, foods)
        create_workouts_for_user(session, u, dates, exercises, is_special_user=is_special)

    print("✅ Seed completed:")
    print("  - 5 users")
    print("  - 10 exercises")
    print("  - 10 foods")
    print("  - 30 days of sleep, meals, and workouts per user")
    print(f"  - User id={special_user_id} has one day per week with 2 workouts.")


if __name__ == "__main__":
    main()