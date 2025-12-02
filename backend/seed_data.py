# seed_data.py
import random
from datetime import datetime, timedelta

from database import SessionLocal, engine
import models

# Optional: ensure tables exist (harmless if already created)
models.Base.metadata.create_all(bind=engine)


def clear_existing_data(session):
    """
    WARNING: This deletes existing data in a safe FK order.
    Comment this out if you want to keep old data.
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
        models.User(
            email="alice@example.com",
            name="Alice",
            surname="Anderson",
            location="Cleveland",
        ),
        models.User(
            email="bob@example.com",
            name="Bob",
            surname="Brown",
            location="Boston",
        ),
        models.User(
            email="charlie@example.com",
            name="Charlie",
            surname="Clark",
            location="Chicago",
        ),
    ]
    session.add_all(users)
    session.commit()
    # refresh to get IDs
    for u in users:
        session.refresh(u)
    return users


def create_exercises(session):
    exercises = [
        models.Exercise(
            exercise_name="Back Squat",
            primary_muscle="Quads",
            secondary_muscle="Glutes",
        ),
        models.Exercise(
            exercise_name="Bench Press",
            primary_muscle="Chest",
            secondary_muscle="Triceps",
        ),
        models.Exercise(
            exercise_name="Deadlift",
            primary_muscle="Hamstrings",
            secondary_muscle="Back",
        ),
        models.Exercise(
            exercise_name="Overhead Press",
            primary_muscle="Shoulders",
            secondary_muscle="Triceps",
        ),
    ]
    session.add_all(exercises)
    session.commit()
    for e in exercises:
        session.refresh(e)
    return exercises

def create_foods(session):
    foods = [
        models.Food(
            food_name="Chicken Breast",
            calories=165.0,
            carbs=0.0,
            fats=3.6,
            protein=31.0,
            sugar=0.0,
            category="Protein",
            serving_size_grams=100.0,  # e.g., per 100g
        ),
        models.Food(
            food_name="White Rice",
            calories=130.0,
            carbs=28.0,
            fats=0.3,
            protein=2.7,
            sugar=0.1,
            category="Carb",
            serving_size_grams=100.0,
        ),
        models.Food(
            food_name="Olive Oil",
            calories=119.0,
            carbs=0.0,
            fats=13.5,
            protein=0.0,
            sugar=0.0,
            category="Fat",
            serving_size_grams=15.0,   # e.g., per tbsp ≈ 15g
        ),
        models.Food(
            food_name="Broccoli",
            calories=55.0,
            carbs=11.0,
            fats=0.6,
            protein=3.7,
            sugar=2.2,
            category="Veg",
            serving_size_grams=100.0,
        ),
    ]
    session.add_all(foods)
    session.commit()
    for f in foods:
        session.refresh(f)
    return foods

def create_sleep_for_user(session, user, days_back=5):
    """
    Create a few nights of sleep for a given user.
    """
    sleeps = []
    today = datetime.now().date()
    for i in range(days_back):
        # sleep from ~23:00 to ~07:00 with some random jitter
        date = today - timedelta(days=i + 1)
        start = datetime.combine(date, datetime.min.time()) + timedelta(hours=23) \
                + timedelta(minutes=random.randint(-30, 30))
        end = start + timedelta(hours=7, minutes=random.randint(-30, 30))
        quality = random.randint(5, 9)

        sleep = models.Sleep(
            user_id=user.user_id,
            start_time=start,
            end_time=end,
            quality_score=quality,
        )
        session.add(sleep)
        sleeps.append(sleep)

    session.commit()
    return sleeps


def create_workouts_for_user(session, user, exercises, num_workouts=3):
    """
    Create a few workouts per user, with 3–5 sets each from random exercises.
    """
    workouts = []
    today = datetime.now().date()
    for i in range(num_workouts):
        date = today - timedelta(days=i * 2 + 1)
        start = datetime.combine(date, datetime.min.time()) + timedelta(hours=17)
        end = start + timedelta(hours=1)

        workout = models.Workout(
            user_id=user.user_id,
            start_time=start,
            end_time=end,
            label=random.choice(["Leg Day", "Push", "Pull", "Full Body"]),
        )
        session.add(workout)
        session.flush()  # get workout_id without committing

        # Create sets
        num_sets = random.randint(3, 5)
        for set_order in range(1, num_sets + 1):
            exercise = random.choice(exercises)
            reps = random.choice([5, 8, 10, 12])
            weight = random.choice([40.0, 60.0, 80.0, 100.0])

            ws = models.WorkoutSet(
                workout_id=workout.workout_id,
                exercise_id=exercise.exercise_id,
                num_reps=reps,
                weight_amount=weight,
                set_order=set_order,
            )
            session.add(ws)

        workouts.append(workout)

    session.commit()
    return workouts


def create_meals_for_user(session, user, foods, num_days=3):
    """
    Create a few days of meals for each user, with 2–3 meals per day
    and 1–3 food items per meal.
    """
    meals = []
    today = datetime.now().date()
    for i in range(num_days):
        date = today - timedelta(days=i + 1)
        num_meals = random.randint(2, 3)

        for m in range(num_meals):
            hour = random.choice([8, 13, 19])  # breakfast/lunch/dinner-ish
            time_of_meal = datetime.combine(date, datetime.min.time()) + timedelta(hours=hour)

            meal = models.Meal(
                user_id=user.user_id,
                time_of_meal=time_of_meal,
                meal_name=random.choice(["Breakfast", "Lunch", "Dinner"]),
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

            meals.append(meal)

    session.commit()
    return meals

def main():
    session = SessionLocal()

    # Comment this out if you don't want to wipe existing data
    clear_existing_data(session)

    users = create_users(session)
    exercises = create_exercises(session)
    foods = create_foods(session)

    for user in users:
        create_sleep_for_user(session, user, days_back=5)
        create_workouts_for_user(session, user, exercises, num_workouts=3)
        create_meals_for_user(session, user, foods, num_days=3)

    print("✅ Seed completed: 3 users, 4 exercises, 4 foods, plus sleep/workouts/meals.")


if __name__ == "__main__":
    main()