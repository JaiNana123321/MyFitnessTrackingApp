import os
import requests
import streamlit as st
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

        payload = {
            "email": email,
            "first_name": first_name,
            "last_name": last_name,
        }

        try:
            resp = requests.post(
                f"{BACKEND_URL}/users/login", json=payload, timeout=5
            )
        except Exception as e:
            st.error(f"Error reaching backend: {e}")
            return

        if resp.status_code == 200:
            # Backend handles both login + create if user doesn't exist.
            user = resp.json()  # expected to be the user profile
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

    st.sidebar.write(f"Logged in as: {email}")
    if st.sidebar.button("Log out"):
        st.session_state.clear()
        st.rerun()

    st.title("Workoutify Dashboard 🏋️")
    st.success("Login successful! 🎉")

    st.write("This is your main dashboard. From here you can add workouts, sleep, meals, etc.")

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

#----------------------- Sleep Form --------------------
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

    # Date + times
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
        value=7,          # default
        step=1,
    )

    save_btn = st.button("Save sleep entry")

    if save_btn:
        payload = {
            "start_time": start_dt.isoformat(),
            "end_time": end_dt.isoformat(),
            "quality_score": quality,
        }

        try:
            resp = requests.post(
                f"{BACKEND_URL}/users/{user_id}/sleep",
                json=payload,
                timeout=10,
            )
        except Exception as e:
            st.error(f"Error reaching backend: {e}")
            return

        if resp.ok:
            st.success("Sleep entry saved! ✅")
            try:
                st.json(resp.json())  # optional, to inspect response
            except Exception:
                pass
        else:
            st.error(f"Error saving sleep entry: {resp.status_code} - {resp.text}")

    if st.button("Back to dashboard"):
        st.session_state["page"] = "dashboard"
        st.rerun()



#---------------------- Food Form--------------------
def food_form():
    user = st.session_state["user"] or {}

    # Sidebar (still show login + logout)
    st.sidebar.write(f"Logged in as: {user.get('email', 'Unknown user')}")
    if st.sidebar.button("Log out"):
        st.session_state.clear()
        st.rerun()

    st.title("Add Food 🍎")

    food_name = st.text_input("Food name (e.g., Chicken Breast, Rice)")
    category = st.text_input("Category (e.g., protein, carb, snack, drink)")

    col1, col2, col3 = st.columns(3)
    with col1:
        calories = st.number_input("Calories", min_value=0.0, step=1.0)
    with col2:
        carbs = st.number_input("Carbs (g)", min_value=0.0, step=0.5)
    with col3:
        fats = st.number_input("Fats (g)", min_value=0.0, step=0.5)

    col4, col5, col6 = st.columns(3)
    with col4:
        protein = st.number_input("Protein (g)", min_value=0.0, step=0.5)
    with col5:
        sugar = st.number_input("Sugar (g)", min_value=0.0, step=0.5)
    with col6:
        serving_size = st.number_input("Serving size (g)", min_value=0.0, step=0.5)

    save_btn = st.button("Save food")

    if save_btn:
        if not food_name:
            st.error("Please enter a food name.")
            return

        payload = {
            "food_name": food_name,
            "calories": float(calories),
            "carbs": float(carbs),
            "fats": float(fats),
            "protein": float(protein),
            "sugar": float(sugar),
            "category": category or None,
        }

        try:
            # ⚠️ Adjust the path if your backend uses a different endpoint than /foods
            resp = requests.post(f"{BACKEND_URL}/foods", json=payload, timeout=10)
        except Exception as e:
            st.error(f"Error reaching backend: {e}")
            return

        if resp.ok:
            st.success("Food saved! ✅")
            # optional: see what backend returns
            try:
                st.json(resp.json())
            except Exception:
                pass
        else:
            st.error(f"Error saving food: {resp.status_code} - {resp.text}")

    if st.button("Back to dashboard"):
        st.session_state["page"] = "dashboard"
        st.rerun()

# -------------------- WORKOUT FORM --------------------
def workout_form():
    user = st.session_state["user"] or {}
    # adjust key name if your backend returns something else
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
        max_value=10,
        value=3,
        step=1,
    )

    sets_data = []
    for i in range(int(num_sets)):
        st.markdown(f"**Set {i + 1}**")

        # For now, ask for exercise_id directly (you can later swap this for a selectbox of exercises)
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

        # you could also filter out sets with exercise_id missing, but we require >=1 here
        payload = {
            "start_time": start_dt.isoformat(),
            "end_time": end_dt.isoformat(),
            "label": label,
            "sets": sets_data,  # <-- important
        }

        try:
            resp = requests.post(
                f"{BACKEND_URL}/users/{user_id}/workouts/with_sets",
                json=payload,
                timeout=10,
            )
        except Exception as e:
            st.error(f"Error reaching backend: {e}")
            return

        if resp.ok:
            st.success("Workout + sets saved! ✅")
            st.json(resp.json())  # optional, just to see what the backend returns
        else:
            st.error(f"Error saving workout: {resp.status_code} - {resp.text}")

    if st.button("Back to dashboard"):
        st.session_state["page"] = "dashboard"
        st.rerun()
#---------------------Meal Form--------------------
def meal_form():
    user = st.session_state["user"] or {}
    user_id = user.get("user_id") or user.get("id")  # adjust if your user profile uses a different key

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

        # For now, just ask for food_id directly. Later you could use a selectbox of foods.
        food_id = st.number_input(
            f"Food ID for item {i + 1}",
            min_value=1,
            step=1,
            key=f"food_id_{i}",
        )
        quantity = st.number_input(
            f"Quantity for item {i + 1}",
            min_value=0.0,
            max_value=10000.0,
            value=1.0,
            step=0.5,
            key=f"quantity_{i}",
        )
        unit = st.text_input(
            f"Unit for item {i + 1} (e.g., g, ml, piece)",
            key=f"unit_{i}",
            value="g",
        )

        items.append(
            {
                "food_id": int(food_id),
                "quantity": float(quantity),
                "unit": unit,
            }
        )

        st.markdown("---")

    if st.button("Save meal"):
        if not meal_name:
            st.error("Please enter a meal name.")
            return

        # You could filter out entries with missing food_id here if you want.
        payload = {
            "time_of_meal": time_of_meal.isoformat(),
            "meal_name": meal_name,
            "items": items,  # ⚠️ If your backend expects 'meal_items' instead, rename this key.
        }

        try:
            resp = requests.post(
                f"{BACKEND_URL}/users/{user_id}/meals/with_items",
                json=payload,
                timeout=10,
            )
        except Exception as e:
            st.error(f"Error reaching backend: {e}")
            return

        if resp.ok:
            st.success("Meal + items saved! ✅")
            st.json(resp.json())  # optional to inspect response
        else:
            st.error(f"Error saving meal: {resp.status_code} - {resp.text}")

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
        # fallback
        st.session_state["page"] = "dashboard"
        dashboard()
