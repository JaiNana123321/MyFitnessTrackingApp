# cli_interactive.py
"""
Interactive CLI for inspecting and deleting data in the Workoutify database.

- Connects directly to the database using SQLAlchemy.
- Uses a simple text menu:
    1) Choose a table
    2) For that table: view all, view by ID, delete by ID

Run with:
    python cli_interactive.py

If using Docker:
    docker compose exec backend python cli_interactive.py
"""

from typing import Callable, Dict, Any

from database import SessionLocal
import models


# ---------- DB helper ----------

def get_db():
    return SessionLocal()


# ---------- Pretty printers for each model ----------

def print_user(u: models.User):
    print(
        f"[User] id={u.user_id} "
        f"email={u.email} "
        f"name={u.name} "
        f"surname={u.surname} "
        f"location={u.location}"
    )


def print_exercise(e: models.Exercise):
    print(
        f"[Exercise] id={e.exercise_id} "
        f"name={e.exercise_name} "
        f"primary={e.primary_muscle} "
        f"secondary={e.secondary_muscle}"
    )


def print_food(f: models.Food):
    print(
        f"[Food] id={f.food_id} "
        f"name={f.food_name} "
        f"cal={f.calories} "
        f"carbs={f.carbs} "
        f"fats={f.fats} "
        f"protein={f.protein} "
        f"sugar={f.sugar} "
        f"category={f.category} "
        f"serving={f.serving_size_grams}g"
    )


def print_sleep(s: models.Sleep):
    print(
        f"[Sleep] id={s.sleep_id} "
        f"user_id={s.user_id} "
        f"start={s.start_time} "
        f"end={s.end_time} "
        f"quality={s.quality_score}"
    )


def print_workout(w: models.Workout):
    print(
        f"[Workout] id={w.workout_id} "
        f"user_id={w.user_id} "
        f"start={w.start_time} "
        f"end={w.end_time} "
        f"label={w.label}"
    )


def print_meal(m: models.Meal):
    print(
        f"[Meal] id={m.meal_id} "
        f"user_id={m.user_id} "
        f"time={m.time_of_meal} "
        f"name={m.meal_name}"
    )


def print_meal_item(mi: models.MealItem):
    print(
        f"[MealItem] id={mi.meal_item_id} "
        f"meal_id={mi.meal_id} "
        f"food_id={mi.food_id} "
        f"quantity={mi.quantity}"
    )


# ---------- Table metadata to reuse generic CRUD helpers ----------

TableInfo = Dict[str, Any]

TABLES: Dict[str, TableInfo] = {
    "1": {
        "name": "Users",
        "model": models.User,
        "pk": "user_id",
        "printer": print_user,
    },
    "2": {
        "name": "Exercises",
        "model": models.Exercise,
        "pk": "exercise_id",
        "printer": print_exercise,
    },
    "3": {
        "name": "Foods",
        "model": models.Food,
        "pk": "food_id",
        "printer": print_food,
    },
    "4": {
        "name": "Sleep",
        "model": models.Sleep,
        "pk": "sleep_id",
        "printer": print_sleep,
    },
    "5": {
        "name": "Workouts",
        "model": models.Workout,
        "pk": "workout_id",
        "printer": print_workout,
    },
    "6": {
        "name": "Meals",
        "model": models.Meal,
        "pk": "meal_id",
        "printer": print_meal,
    },
    "7": {
        "name": "Meal Items",
        "model": models.MealItem,
        "pk": "meal_item_id",
        "printer": print_meal_item,
    },
}


# ---------- Generic operations ----------

def view_all(table: TableInfo):
    db = get_db()
    try:
        model = table["model"]
        printer: Callable = table["printer"]
        # SQL: SELECT * FROM <table> ORDER BY <pk>;
        pk_col = getattr(model, table["pk"])
        rows = db.query(model).order_by(pk_col).all()
        if not rows:
            print(f"No entries found in {table['name']}.")
            return
        print(f"--- All entries in {table['name']} ---")
        for row in rows:
            printer(row)
    finally:
        db.close()


def view_one(table: TableInfo):
    db = get_db()
    try:
        model = table["model"]
        printer: Callable = table["printer"]
        pk_name: str = table["pk"]
        pk_input = input(f"Enter {pk_name} to view: ").strip()
        if not pk_input.isdigit():
            print("Invalid ID; must be an integer.")
            return
        pk_val = int(pk_input)

        # SQL: SELECT * FROM <table> WHERE <pk> = :id;
        row = db.get(model, pk_val)
        if not row:
            print(f"{table['name']} entry with {pk_name}={pk_val} not found.")
            return
        print(f"--- Entry in {table['name']} ---")
        printer(row)
    finally:
        db.close()


def delete_one(table: TableInfo):
    db = get_db()
    try:
        model = table["model"]
        printer: Callable = table["printer"]
        pk_name: str = table["pk"]
        pk_input = input(f"Enter {pk_name} to DELETE: ").strip()
        if not pk_input.isdigit():
            print("Invalid ID; must be an integer.")
            return
        pk_val = int(pk_input)

        # SQL: SELECT * FROM <table> WHERE <pk> = :id;
        row = db.get(model, pk_val)
        if not row:
            print(f"{table['name']} entry with {pk_name}={pk_val} not found.")
            return

        print("About to delete the following entry:")
        printer(row)
        confirm = input("Type 'yes' to confirm delete: ").strip().lower()
        if confirm != "yes":
            print("Delete cancelled.")
            return

        # SQL: DELETE FROM <table> WHERE <pk> = :id;
        db.delete(row)
        db.commit()
        print(f"Deleted {table['name']} entry with {pk_name}={pk_val}.")
    finally:
        db.close()


# ---------- Menus ----------

def table_menu(table_key: str):
    table = TABLES[table_key]
    while True:
        print()
        print(f"==== {table['name']} Menu ====")
        print("1) View all entries")
        print("2) View entry by ID")
        print("3) Delete entry by ID")
        print("0) Back to main menu")
        choice = input("Choose an option: ").strip()

        if choice == "1":
            view_all(table)
        elif choice == "2":
            view_one(table)
        elif choice == "3":
            delete_one(table)
        elif choice == "0":
            break
        else:
            print("Invalid choice, please try again.")


def main_menu():
    while True:
        print()
        print("========== Workoutify CLI ==========")
        print("Choose a table:")
        for key, info in sorted(TABLES.items(), key=lambda x: int(x[0])):
            print(f"{key}) {info['name']}")
        print("0) Exit")

        choice = input("Enter number: ").strip()

        if choice == "0":
            print("Goodbye!")
            break
        elif choice in TABLES:
            table_menu(choice)
        else:
            print("Invalid choice, please try again.")


if __name__ == "__main__":
    main_menu()