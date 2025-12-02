import os
import requests
import streamlit as st
import pandas as pd
from datetime import datetime, date, time, timedelta


BACKEND_URL = os.getenv("BACKEND_URL", "http://backend:8000")

st.set_page_config(page_title="Workoutify", page_icon="🏋️")

# -------------------- SESSION STATE --------------------

if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

if "user" not in st.session_state:
    st.session_state["user"] = None  # will hold the user profile from /users/login

if "page" not in st.session_state:
    st.session_state["page"] = "dashboard"  # "dashboard" or "workout_form"


# -------------------- HELPERS TO FETCH LOOKUP DATA --------------------

def get_all_exercises():
    """Fetch all exercises from backend once per session and cache in session_state."""
    if "exercises" in st.session_state and st.session_state["exercises"] is not None:
        return st.session_state["exercises"]

    try:
        resp = requests.get(f"{BACKEND_URL}/exercises/all", timeout=5)
    except Exception as e:
        st.error(f"Error fetching exercises from backend: {e}")
        st.session_state["exercises"] = []
        return []

    if not resp.ok:
        st.error(f"Error fetching exercises: {resp.status_code} - {resp.text}")
        st.session_state["exercises"] = []
        return []

    data = resp.json()
    st.session_state["exercises"] = data
    return data


def get_all_foods():
    """Fetch all foods from backend once per session and cache in session_state."""
    if "foods" in st.session_state and st.session_state["foods"] is not None:
        return st.session_state["foods"]

    try:
        resp = requests.get(f"{BACKEND_URL}/foods/all", timeout=5)
    except Exception as e:
        st.error(f"Error fetching foods from backend: {e}")
        st.session_state["foods"] = []
        return []

    if not resp.ok:
        st.error(f"Error fetching foods: {resp.status_code} - {resp.text}")
        st.session_state["foods"] = []
        return []

    data = resp.json()
    st.session_state["foods"] = data
    return data

def fetch_user_summary(user_id: int, days: int = 7):
    """Call the backend /users/{user_id}/summary API and return JSON or None on failure."""
    try:
        resp = requests.get(
            f"{BACKEND_URL}/users/{user_id}/summary",
            params={"days": days},
            timeout=10,
        )
    except Exception as e:
        st.error(f"Error reaching backend for summary: {e}")
        return None

    if not resp.ok:
        st.error(f"Error fetching summary: {resp.status_code} - {resp.text}")
        return None

    return resp.json()

# -------------------- LOGIN --------------------

def login_page():
    st.title("Workoutify Login 🔐")

    email = st.text_input("Email")
    first_name = st.text_input("First name")
    last_name = st.text_input("Surname")
    login_btn = st.button("Log in")

    if login_btn:
        if not email or not first_name or not last_name:
            st.error("Please fill in email, first name, and surname.")
            return

        # Backend expects: email, name, surname
        payload = {
            "email": email,
            "name": first_name,
            "surname": last_name,
        }

        try:
            resp = requests.post(
                f"{BACKEND_URL}/users/login", json=payload, timeout=5
            )
        except Exception as e:
            st.error(f"Error reaching backend: {e}")
            return

        if resp.status_code == 200:
            user = resp.json()  # expected to include user_id, email, name, surname, etc.
            st.session_state["authenticated"] = True
            st.session_state["user"] = user
            st.session_state["page"] = "dashboard"
            st.success("Login successful!")
            st.rerun()
        else:
            st.error(f"Login failed: {resp.status_code} - {resp.text}")


# -------------------- DASHBOARD --------------------

def dashboard():
    user = st.session_state["user"] or {}
    email = user.get("email", "Unknown user")
    user_id = user.get("user_id") or user.get("id")

    st.sidebar.write(f"Logged in as: {email}")
    if st.sidebar.button("Log out"):
        st.session_state.clear()
        st.rerun()

    st.title("Workoutify Dashboard 🏋️")
    #st.success("Login successful! 🎉")

    st.write("This is your main dashboard. From here you can add workouts, sleep, meals, etc.")

    # ---- navigation buttons ----
    col1, col2, col3, col4 = st.columns([1, 1, 1, 1])

    with col1:
        if st.button("Add workout"):
            st.session_state["page"] = "workout_form"
            st.rerun()

    with col2:
        if st.button("Add meal"):
            st.session_state["page"] = "meal_form"
            st.rerun()
    
    with col3:
        if st.button("Add Food"):
            st.session_state["page"] = "food_form"
            st.rerun()

    with col4:
        if st.button("Add Sleep"):
            st.session_state["page"] = "sleep_form"
            st.rerun()

    # ---- summary charts ----
    if not user_id:
        st.warning("No user_id available; cannot load dashboard summary.")
        return

    st.markdown("---")
    st.subheader("Last 7 days overview 📊")

    summary = fetch_user_summary(int(user_id), days=7)
    if not summary:
        return  # errors already displayed

    # -------- Sleep chart --------
    sleep_data = summary.get("sleep", [])
    col_sleep, col_sleep_stats = st.columns([2, 1])

    with col_sleep:
        st.markdown("**Sleep duration (hours per day)**")
        if sleep_data:
            df_sleep = pd.DataFrame(sleep_data)
            # ensure date is treated nicely
            df_sleep["date"] = pd.to_datetime(df_sleep["date"])
            df_sleep = df_sleep.sort_values("date")
            df_sleep.set_index("date", inplace=True)

            st.bar_chart(df_sleep["hours"])
        else:
            st.info("No sleep data for the last 7 days.")

    with col_sleep_stats:
        if sleep_data:
            df_sleep = pd.DataFrame(sleep_data)
            avg_hours = df_sleep["hours"].mean()
            avg_quality = df_sleep["quality_score"].mean() if "quality_score" in df_sleep else None

            st.metric("Avg sleep (h)", f"{avg_hours:.1f}")
            if avg_quality is not None:
                st.metric("Avg quality", f"{avg_quality:.1f}/10")
        else:
            st.write("Sleep stats will appear once you log some sleep.")

    st.markdown("---")

    # -------- Workouts per day --------
    workouts_data = summary.get("workouts_per_day", [])
    col_w1, col_w2 = st.columns(2)

    with col_w1:
        st.markdown("**Workouts per day (count)**")
        if workouts_data:
            df_w = pd.DataFrame(workouts_data)
            df_w["date"] = pd.to_datetime(df_w["date"])
            df_w = df_w.sort_values("date")
            df_w.set_index("date", inplace=True)

            st.bar_chart(df_w["count"])
        else:
            st.info("No workouts logged in the last 7 days.")

    with col_w2:
        st.markdown("**Total weight lifted per day**")
        if workouts_data:
            df_w = pd.DataFrame(workouts_data)
            df_w["date"] = pd.to_datetime(df_w["date"])
            df_w = df_w.sort_values("date")
            df_w.set_index("date", inplace=True)

            # total_weight field we added in the summary API
            if "total_weight" in df_w:
                st.bar_chart(df_w["total_weight"])
            else:
                st.info("Backend summary does not yet include total_weight.")
        else:
            st.info("No volume data yet.")

    st.markdown("---")

    # -------- Nutrition per day --------
    st.markdown("**Daily calories & macros (servings-based)**")

    cal_data = summary.get("calories_per_day", [])
    if cal_data:
        df_c = pd.DataFrame(cal_data)
        df_c["date"] = pd.to_datetime(df_c["date"])
        df_c = df_c.sort_values("date")
        df_c.set_index("date", inplace=True)

        # Calories chart
        st.markdown("Calories per day")
        st.bar_chart(df_c["calories"])

        # Macros stacked bar – simple multi-series bar chart
        st.markdown("Macros per day (g)")
        macro_cols = [col for col in ["carbs", "fats", "protein"] if col in df_c.columns]
        if macro_cols:
            st.bar_chart(df_c[macro_cols])
        else:
            st.info("No macro data available in summary.")
    else:
        st.info("No nutrition data for the last 7 days.")

# ----------------------- Sleep Form --------------------

def sleep_form():
    user = st.session_state["user"] or {}
    user_id = user.get("user_id") or user.get("id")  # adjust key if needed

    st.sidebar.write(f"Logged in as: {user.get('email', 'Unknown user')}")
    if st.sidebar.button("Log out"):
        st.session_state.clear()
        st.rerun()

    if not user_id:
        st.error("No user_id found in user profile. Check /users/login response.")
        if st.button("Back to dashboard"):
            st.session_state["page"] = "dashboard"
            st.rerun()
        return

    st.title("Add Sleep 😴")

    sleep_date = st.date_input("Sleep date (when you went to bed)", value=date.today())
    start_time_val = st.time_input("Sleep start time", value=time(23, 0))  # 11 PM
    end_time_val = st.time_input("Wake-up time", value=time(7, 0))        # 7 AM

    start_dt = datetime.combine(sleep_date, start_time_val)
    end_dt = datetime.combine(sleep_date, end_time_val)

    # If end <= start, assume it crosses midnight
    if end_dt <= start_dt:
        end_dt += timedelta(days=1)

    quality = st.slider(
        "Sleep quality (1 = bad, 10 = excellent)",
        min_value=1,
        max_value=10,
        value=7,
        step=1,
    )

    save_btn = st.button("Save sleep entry")

    if save_btn:
        payload = {
            "user_id": int(user_id),
            "start_time": start_dt.isoformat(),
            "end_time": end_dt.isoformat(),
            "quality_score": quality,
        }

        try:
            # Backend API: POST /sleep
            resp = requests.post(
                f"{BACKEND_URL}/sleep",
                json=payload,
                timeout=10,
            )
        except Exception as e:
            st.error(f"Error reaching backend: {e}")
            return

        if resp.ok:
            st.success("Sleep entry saved! ✅")
            try:
                st.json(resp.json())
            except Exception:
                pass
        else:
            st.error(f"Error saving sleep entry: {resp.status_code} - {resp.text}")

    if st.button("Back to dashboard"):
        st.session_state["page"] = "dashboard"
        st.rerun()


# ---------------------- Food Form --------------------

def food_form():
    user = st.session_state["user"] or {}

    st.sidebar.write(f"Logged in as: {user.get('email', 'Unknown user')}")
    if st.sidebar.button("Log out"):
        st.session_state.clear()
        st.rerun()

    st.title("Add Food 🍎")

    food_name = st.text_input("Food name (e.g., Chicken Breast, Rice)")
    category = st.text_input("Category (e.g., protein, carb, snack, drink)")

    col1, col2, col3 = st.columns(3)
    with col1:
        calories = st.number_input("Calories per serving", min_value=0.0, step=1.0)
    with col2:
        carbs = st.number_input("Carbs (g) per serving", min_value=0.0, step=0.5)
    with col3:
        fats = st.number_input("Fats (g) per serving", min_value=0.0, step=0.5)

    col4, col5, col6 = st.columns(3)
    with col4:
        protein = st.number_input("Protein (g) per serving", min_value=0.0, step=0.5)
    with col5:
        sugar = st.number_input("Sugar (g) per serving", min_value=0.0, step=0.5)
    with col6:
        serving_size = st.number_input("Serving size (g)", min_value=0.0, step=0.5)

    save_btn = st.button("Save food")

    if save_btn:
        if not food_name:
            st.error("Please enter a food name.")
            return
        if serving_size <= 0:
            st.error("Please enter a positive serving size.")
            return

        payload = {
            "food_name": food_name,
            "calories": float(calories),
            "carbs": float(carbs),
            "fats": float(fats),
            "protein": float(protein),
            "sugar": float(sugar),
            "category": category or "Uncategorized",
            "serving_size_grams": float(serving_size),
        }

        try:
            resp = requests.post(f"{BACKEND_URL}/foods", json=payload, timeout=10)
        except Exception as e:
            st.error(f"Error reaching backend: {e}")
            return

        if resp.ok:
            st.success("Food saved! ✅")
            try:
                st.json(resp.json())
            except Exception:
                pass
            # refresh foods cache
            st.session_state["foods"] = None
        else:
            st.error(f"Error saving food: {resp.status_code} - {resp.text}")

    if st.button("Back to dashboard"):
        st.session_state["page"] = "dashboard"
        st.rerun()


# -------------------- WORKOUT FORM --------------------

def workout_form():
    user = st.session_state["user"] or {}
    user_id = user.get("user_id") or user.get("id")

    st.sidebar.write(f"Logged in as: {user.get('email', 'Unknown user')}")
    if st.sidebar.button("Log out"):
        st.session_state.clear()
        st.rerun()

    if not user_id:
        st.error("No user_id found in user profile. Check /users/login response.")
        if st.button("Back to dashboard"):
            st.session_state["page"] = "dashboard"
            st.rerun()
        return

    st.title("Add Workout 💪")

    # Fetch exercises from backend for dropdown
    exercises = get_all_exercises()
    if not exercises:
        st.warning("No exercises available. Please add exercises.")

    exercise_labels = [
        f"{ex['exercise_name']} (id {ex['exercise_id']})" for ex in exercises
    ]
    # We'll use indices as selectbox options and map back to exercise_id
    exercise_indices = list(range(len(exercises)))

    # --- Workout meta info ---
    workout_date = st.date_input("Workout date", value=date.today())
    start_time_val = st.time_input("Start time", value=time(17, 0))  # 5 PM default
    end_time_val = st.time_input("End time", value=time(18, 0))      # 6 PM default

    start_dt = datetime.combine(workout_date, start_time_val)
    end_dt = datetime.combine(workout_date, end_time_val)
    if end_dt <= start_dt:
        end_dt += timedelta(days=1)  # assume past midnight

    label = st.text_input("Workout label (e.g., Push Day, Bench Session)")

    st.subheader("Sets")

    num_sets = st.number_input(
        "Number of sets",
        min_value=1,
        max_value=30,
        value=3,
        step=1,
    )

    sets_data = []
    for i in range(int(num_sets)):
        st.markdown(f"**Set {i + 1}**")

        if exercises:
            idx = st.selectbox(
                f"Exercise for set {i + 1}",
                options=exercise_indices,
                format_func=lambda j: exercise_labels[j],
                key=f"exercise_idx_{i}",
            )
            exercise_id = exercises[idx]["exercise_id"]
        else:
            exercise_id = st.number_input(
                f"Exercise ID for set {i + 1}",
                min_value=1,
                step=1,
                key=f"exercise_id_{i}",
            )

        num_reps = st.number_input(
            f"Reps for set {i + 1}",
            min_value=1,
            max_value=100,
            value=8,
            step=1,
            key=f"reps_{i}",
        )
        weight_amount = st.number_input(
            f"Weight for set {i + 1} (e.g., kg)",
            min_value=0.0,
            max_value=1000.0,
            value=0.0,
            step=1.0,
            key=f"weight_{i}",
        )

        sets_data.append(
            {
                "exercise_id": int(exercise_id),
                "num_reps": int(num_reps),
                "weight_amount": float(weight_amount),
                "set_order": i + 1,
            }
        )

        st.markdown("---")

    if st.button("Save workout"):
        if not label:
            st.error("Please enter a workout label.")
            return

        # 1) Create workout
        workout_payload = {
            "user_id": int(user_id),
            "start_time": start_dt.isoformat(),
            "end_time": end_dt.isoformat(),
            "label": label,
        }

        try:
            workout_resp = requests.post(
                f"{BACKEND_URL}/workouts",
                json=workout_payload,
                timeout=10,
            )
        except Exception as e:
            st.error(f"Error reaching backend when creating workout: {e}")
            return

        if not workout_resp.ok:
            st.error(f"Error creating workout: {workout_resp.status_code} - {workout_resp.text}")
            return

        workout_data = workout_resp.json()
        workout_id = workout_data.get("workout_id")
        if not workout_id:
            st.error("Backend did not return workout_id.")
            return

        # 2) Create workout sets
        all_ok = True
        for s in sets_data:
            set_payload = {
                "workout_id": int(workout_id),
                "exercise_id": s["exercise_id"],
                "num_reps": s["num_reps"],
                "weight_amount": s["weight_amount"],
                "set_order": s["set_order"],
            }
            try:
                set_resp = requests.post(
                    f"{BACKEND_URL}/workout_sets",
                    json=set_payload,
                    timeout=10,
                )
            except Exception as e:
                st.error(f"Error reaching backend when creating workout set: {e}")
                all_ok = False
                break

            if not set_resp.ok:
                st.error(f"Error creating set {s['set_order']}: {set_resp.status_code} - {set_resp.text}")
                all_ok = False
                # continue to attempt others, or break; here break to avoid partial confusion
                break

        if all_ok:
            st.success("Workout + sets saved! ✅")
            st.json(workout_data)  # optional

    if st.button("Back to dashboard"):
        st.session_state["page"] = "dashboard"
        st.rerun()


# --------------------- Meal Form --------------------

def meal_form():
    user = st.session_state["user"] or {}
    user_id = user.get("user_id") or user.get("id")

    st.sidebar.write(f"Logged in as: {user.get('email', 'Unknown user')}")
    if st.sidebar.button("Log out"):
        st.session_state.clear()
        st.rerun()

    if not user_id:
        st.error("No user_id found in user profile. Check /users/login response.")
        if st.button("Back to dashboard"):
            st.session_state["page"] = "dashboard"
            st.rerun()
        return

    st.title("Add Meal 🍽️")

    # Fetch foods for dropdown
    foods = get_all_foods()
    if not foods:
        st.warning("No foods available. Please add foods first.")
    food_labels = [
        f"{f['food_name']} (id {f['food_id']}, {f['serving_size_grams']}g serving)"
        for f in foods
    ]
    food_indices = list(range(len(foods)))

    # --- Meal meta info ---
    meal_date = st.date_input("Meal date", value=date.today())
    meal_time = st.time_input("Time of meal", value=time(12, 0))  # default noon
    time_of_meal = datetime.combine(meal_date, meal_time)

    meal_name = st.text_input("Meal name (e.g., Breakfast, Lunch, Dinner)")

    st.subheader("Meal items")

    num_items = st.number_input(
        "Number of items",
        min_value=1,
        max_value=15,
        value=2,
        step=1,
    )

    items = []
    for i in range(int(num_items)):
        st.markdown(f"**Item {i + 1}**")

        if foods:
            idx = st.selectbox(
                f"Food for item {i + 1}",
                options=food_indices,
                format_func=lambda j: food_labels[j],
                key=f"food_idx_{i}",
            )
            food_id = foods[idx]["food_id"]
        else:
            food_id = st.number_input(
                f"Food ID for item {i + 1}",
                min_value=1,
                step=1,
                key=f"food_id_{i}",
            )

        quantity = st.number_input(
            f"Quantity (servings) for item {i + 1}",
            min_value=0.0,
            max_value=10000.0,
            value=1.0,
            step=0.5,
            key=f"quantity_{i}",
        )

        items.append(
            {
                "food_id": int(food_id),
                "quantity": float(quantity),  # servings, no unit
            }
        )

        st.markdown("---")

    if st.button("Save meal"):
        if not meal_name:
            st.error("Please enter a meal name.")
            return

        # 1) Create meal
        meal_payload = {
            "user_id": int(user_id),
            "time_of_meal": time_of_meal.isoformat(),
            "meal_name": meal_name,
        }

        try:
            meal_resp = requests.post(
                f"{BACKEND_URL}/meals",
                json=meal_payload,
                timeout=10,
            )
        except Exception as e:
            st.error(f"Error reaching backend when creating meal: {e}")
            return

        if not meal_resp.ok:
            st.error(f"Error creating meal: {meal_resp.status_code} - {meal_resp.text}")
            return

        meal_data = meal_resp.json()
        meal_id = meal_data.get("meal_id")
        if not meal_id:
            st.error("Backend did not return meal_id.")
            return

        # 2) Create meal items
        all_ok = True
        for item in items:
            item_payload = {
                "meal_id": int(meal_id),
                "food_id": item["food_id"],
                "quantity": item["quantity"],
            }
            try:
                item_resp = requests.post(
                    f"{BACKEND_URL}/meal_items",
                    json=item_payload,
                    timeout=10,
                )
            except Exception as e:
                st.error(f"Error reaching backend when creating meal item: {e}")
                all_ok = False
                break

            if not item_resp.ok:
                st.error(f"Error creating meal item (food_id={item['food_id']}): "
                         f"{item_resp.status_code} - {item_resp.text}")
                all_ok = False
                break

        if all_ok:
            st.success("Meal + items saved! ✅")
            st.json(meal_data)

    if st.button("Back to dashboard"):
        st.session_state["page"] = "dashboard"
        st.rerun()


# -------------------- ROUTING --------------------

if not st.session_state["authenticated"]:
    login_page()
else:
    if st.session_state["page"] == "dashboard":
        dashboard()
    elif st.session_state["page"] == "workout_form":
        workout_form()
    elif st.session_state["page"] == "meal_form":
        meal_form()
    elif st.session_state["page"] == "food_form":
        food_form()
    elif st.session_state["page"] == "sleep_form":
        sleep_form()
    else:
        st.session_state["page"] = "dashboard"
        dashboard()