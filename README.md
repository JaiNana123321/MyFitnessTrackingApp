# MyFitnessTrackingApp
CWRU CSDS 341 Intro to DBMS Final Project

Workoutify — README

Workoutify is a full-stack fitness tracking platform built with:
	•	Backend: FastAPI + SQLAlchemy + PostgreSQL
	•	Frontend: Streamlit
	•	Dev Environment: Docker Compose
	•	Generated/Seeded Dataset: Automatically generates realistic users, workouts, meals, sleep, and food entries.

⸻

Features

✔️ Track Fitness Data
	•	Workouts
	•	Sets (reps × weight)
	•	Sleep entries
	•	Meals + food items
	•	Custom foods & exercises

✔️ Analytics Endpoints
	•	Personal Records (PRs) per exercise
	•	Muscle Balance, showing weekly training volume per muscle
	•	Daily Summaries for sleep, calories, macros, and training load

✔️ Seed Data Generator

A script (seed_data.py) populates the database with realistic 30-day history:
	•	5 users
	•	10 exercises
	•	10 foods
	•	Daily sleep + 3 meals
	•	3–6 workouts per week
	•	One special user who trains 2× per day occasionally

⸻

Getting Started

1. Clone the Repository

git clone https://github.com/yourusername/workoutify.git
cd workoutify

2. Start Everything with Docker

docker compose up --build

This brings up:
	•	backend (FastAPI at http://localhost:8000)
	•	frontend (Streamlit at http://localhost:8501)
	•	database (Postgres)

⸻

Seed the Database

Run inside the backend container:

docker compose exec backend python seed_data.py

This will:
	•	Wipe existing data (unless you disable the wipe)
	•	Regenerate users, foods, exercises
	•	Populate 30 days of workouts, meals, and sleep

You can now log in via Streamlit with any of the seeded users (e.g. alice@example.com) or create your own user.

⸻

API Documentation

Workoutify exposes a full REST API covering all CRUD operations and analytics.

OpenAPI Spec

The complete OpenAPI specification is available here:

backend/openapi.yaml

You can load it in:
	•	Swagger Editor: https://editor.swagger.io
	•	Postman / Insomnia (import the YAML)
	•	VSCode Swagger Viewer extension

API Highlights

Endpoint	Description
POST /users/login	Login or create a user
GET /users/{id}/summary	Sleep, calories, macros, workout load
GET /users/{id}/PR	Personal Records per exercise
GET /users/{id}/Muscle-Balance	Weekly training volume per muscle
CRUD endpoints for Sleep, Workouts, Exercises, Foods, Meals	Complete data management

A full, detailed endpoint table is also included in the docs.

⸻

Frontend (Streamlit)

The Streamlit UI provides:
	•	A login screen
	•	Data entry forms (workouts, meals, sleep, food)
	•	Analytics dashboards with charts
	•	Muscle balance visualizations
	•	Personal record charts

Accessible at:

http://localhost:8501


⸻

Project Structure

backend/
    ├── main.py            # FastAPI entrypoint
    ├── models.py          # SQLAlchemy models
    ├── schemas.py         # Pydantic schemas
    ├── database.py        # Database session + Base
    ├── seed_data.py       # Seed generator script
    └── openapi.yaml       # Full API spec

frontend/
    └── app.py             # Streamlit UI

docker-compose.yaml
README.md


⸻

CLI Tool

A small interactive Python CLI is included:

docker compose exec backend python cli.py

It provides:
	•	Menu of all tables
	•	View all entries
	•	View entry by ID
	•	Delete entry by ID

Simple and perfect for debugging.

⸻

✨ Demo Credentials (Example)

alice@example.com
bob@example.com
charlie@example.com
dana@example.com
eric@example.com

All are auto-generated via the seeder.
