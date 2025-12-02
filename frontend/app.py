import os
import requests
import streamlit as st
from datetime import datetime, date, time

BACKEND_URL = os.getenv("BACKEND_URL", "http://backend:8000")

if "user" not in st.session_state:
    st.session_state["user"] = None

if "page" not in st.session_state:
    st.session_state["page"] = "home"  # or "dashboard"

def show_login():
    st.title("Login")

    email = st.text_input("Email")
    name = st.text_input("Name (optional)")
    surname = st.text_input("Surname (optional)")

    if st.button("Login"):
        if not email:
            st.error("Please enter an email")
            return

        payload = {"email": email, "name": name or None, "surname": surname or None}
        try:
            resp = requests.post(f"{BACKEND_URL}/users/login", json=payload, timeout=5)
            if resp.ok:
                st.session_state["user"] = resp.json()
                st.session_state["page"] = "home"
                st.success("Logged in!")
                st.experimental_rerun()
            else:
                st.error(f"Login failed: {resp.status_code} - {resp.text}")
        except Exception as e:
            st.error(f"Could not reach backend: {e}")


def show_main_app():
    user = st.session_state["user"]
    user_id = user["user_id"]

    st.sidebar.title("User")
    st.sidebar.write(user["email"])
    if st.sidebar.button("Logout"):
        st.session_state["user"] = None
        st.session_state["page"] = "home"
        st.experimental_rerun()

    st.sidebar.title("Navigate")
    choice = st.sidebar.radio(
        "Go to",
        ["Dashboard", "Add Sleep", "Add Workout", "Add Meal"],
        index=["Dashboard", "Add Sleep", "Add Workout", "Add Meal"].index(
            "Dashboard" if st.session_state["page"] == "home" else st.session_state["page"]
        ),
    )

    if choice == "Dashboard":
        st.session_state["page"] = "Dashboard"
        show_dashboard(user_id)
    elif choice == "Add Sleep":
        st.session_state["page"] = "Add Sleep"
        show_add_sleep(user_id)
    elif choice == "Add Workout":
        st.session_state["page"] = "Add Workout"
        show_add_workout(user_id)
    elif choice == "Add Meal":
        st.session_state["page"] = "Add Meal"
        show_add_meal(user_id)


def show_dashboard(user_id: int):
    st.title("Dashboard")

    days = st.slider("Days to look back", min_value=7, max_value=60, value=7, step=1)

    try:
        resp = requests.get(f"{BACKEND_URL}/users/{user_id}/summary", params={"days": days}, timeout=5)
        if not resp.ok:
            st.error(f"Error fetching summary: {resp.status_code} - {resp.text}")
            return
        data = resp.json()
    except Exception as e:
        st.error(f"Could not reach backend: {e}")
        return

    sleep = data.get("sleep", [])
    workouts = data.get("workouts_per_day", [])
    calories = data.get("calories_per_day", [])

    col1, col2, col3 = st.columns(3)
    if sleep:
        avg_hours = sum(d["hours"] for d in sleep) / len(sleep)
        col1.metric("Avg Sleep (hrs)", f"{avg_hours:.1f}")
    if workouts:
        total_workouts = sum(d["count"] for d in workouts)
        col2.metric("Workouts", total_workouts)
    if calories:
        avg_cal = sum(d["calories"] for d in calories) / len(calories)
        col3.metric("Avg Calories", int(avg_cal))

    st.subheader("Sleep over time")
    if sleep:
        st.line_chart(
            {d["date"]: d["hours"] for d in sleep}
        )

    st.subheader("Workouts per day")
    if workouts:
        st.bar_chart(
            {d["date"]: d["count"] for d in workouts}
        )

    st.subheader("Calories per day")
    if calories:
        st.line_chart(
            {d["date"]: d["calories"] for d in calories}
        )

def show_add_sleep(user_id: int):
    st.title("Add Sleep")

    sleep_date = st.date_input("Sleep date", value=date.today())
    start_t = st.time_input("Start time", value=time(23, 0))
    end_t = st.time_input("End time", value=time(7, 0))
    quality = st.slider("Quality (1–10)", min_value=1, max_value=10, value=7)

    if st.button("Save Sleep"):
        start_dt = datetime.combine(sleep_date, start_t)
        # naive: assume end on same date or next day
        end_dt = datetime.combine(
            sleep_date if end_t > start_t else sleep_date.replace(day=sleep_date.day + 1),
            end_t,
        )

        payload = {
            "start_time": start_dt.isoformat(),
            "end_time": end_dt.isoformat(),
            "quality_score": quality,
        }
        try:
            resp = requests.post(
                f"{BACKEND_URL}/users/{user_id}/sleep", json=payload, timeout=5
            )
            if resp.ok:
                st.success("Sleep logged!")
            else:
                st.error(f"Error: {resp.status_code} - {resp.text}")
        except Exception as e:
            st.error(f"Could not reach backend: {e}")

def show_add_workout(user_id: int):
    st.title("Add Workout")

    label = st.text_input("Label", "Workout")
    w_date = st.date_input("Date", value=date.today())
    start_t = st.time_input("Start time", value=time(17, 0))
    end_t = st.time_input("End time", value=time(18, 0))

    exercise_id = st.number_input("Exercise ID", min_value=1, step=1)

    sets = []
    st.subheader("Sets")
    for set_order in range(1, 4):
        cols = st.columns(3)
        with cols[0]:
            reps = st.number_input(f"Reps (set {set_order})", min_value=1, step=1, key=f"reps_{set_order}")
        with cols[1]:
            weight = st.number_input(f"Weight (kg)", min_value=0.0, step=2.5, key=f"weight_{set_order}")
        with cols[2]:
            include = st.checkbox("Include?", value=True, key=f"include_{set_order}")
        if include:
            sets.append(
                {
                    "exercise_id": int(exercise_id),
                    "num_reps": int(reps),
                    "weight_amount": float(weight),
                    "set_order": set_order,
                }
            )

    if st.button("Save Workout"):
        start_dt = datetime.combine(w_date, start_t)
        end_dt = datetime.combine(w_date, end_t)
        payload = {
            "start_time": start_dt.isoformat(),
            "end_time": end_dt.isoformat(),
            "label": label,
            "sets": sets,
        }
        try:
            resp = requests.post(
                f"{BACKEND_URL}/users/{user_id}/workouts/with_sets", json=payload, timeout=5
            )
            if resp.ok:
                st.success("Workout saved!")
                st.json(resp.json())
            else:
                st.error(f"Error: {resp.status_code} - {resp.text}")
        except Exception as e:
            st.error(f"Could not reach backend: {e}")

def show_add_meal(user_id: int):
    st.title("Add Meal")

    m_date = st.date_input("Meal date", value=date.today())
    m_time = st.time_input("Time", value=time(12, 0))
    meal_name = st.text_input("Meal name", "Lunch")

    st.write("For now, enter a single food_id and quantity. You can expand later.")
    food_id = st.number_input("Food ID", min_value=1, step=1)
    quantity = st.number_input("Quantity", min_value=0.0, step=0.5)
    unit = st.text_input("Unit", "g")

    if st.button("Save Meal"):
        dt = datetime.combine(m_date, m_time)
        payload = {
            "time_of_meal": dt.isoformat(),
            "meal_name": meal_name,
            "items": [
                {"food_id": int(food_id), "quantity": float(quantity), "unit": unit}
            ],
        }
        try:
            resp = requests.post(
                f"{BACKEND_URL}/users/{user_id}/meals/with_items", json=payload, timeout=5
            )
            if resp.ok:
                st.success("Meal saved!")
                st.json(resp.json())
            else:
                st.error(f"Error: {resp.status_code} - {resp.text}")
        except Exception as e:
            st.error(f"Could not reach backend: {e}")


def main():
    if st.session_state["user"] is None:
        show_login()
    else:
        show_main_app()


if __name__ == "__main__":
    main()