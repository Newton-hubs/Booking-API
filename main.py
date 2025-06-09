from fastapi import FastAPI, HTTPException
from db import init_db, seed_data, get_db_connection
from schemas import FitnessClass, BookingRequest, Booking
from typing import List
from datetime import datetime
from pytz import timezone
import pytz
import logging

app = FastAPI()
IST = timezone('Asia/Kolkata')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s',
    handlers=[logging.FileHandler("app.log"), logging.StreamHandler()]
)

@app.on_event("startup")
def startup_event():
    init_db()
    seed_data()

@app.get("/", tags=["Root"])
def read_root():
    return {"message": "Welcome to the Fitness Studio Booking API!"}

@app.get("/classes", response_model=List[FitnessClass], tags=["Classes"])
def get_classes():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, name, datetime, instructor, available_slots FROM classes WHERE datetime(datetime) > datetime('now') ORDER BY datetime ASC")
    rows = cur.fetchall()
    classes = []
    for row in rows:
        # Parse as naive datetime, then localize to IST
        dt_naive = datetime.strptime(row["datetime"], "%Y-%m-%d %H:%M:%S")
        dt_ist = IST.localize(dt_naive)
        classes.append(FitnessClass(
            id=row["id"],
            name=row["name"],
            datetime=dt_ist,
            instructor=row["instructor"],
            available_slots=row["available_slots"]
        ))
    conn.close()
    return classes

@app.post("/book", response_model=Booking, tags=["Bookings"])
def book_class(request: BookingRequest):
    conn = get_db_connection()
    cur = conn.cursor()
    # Check if class exists and has available slots
    cur.execute("SELECT id, available_slots FROM classes WHERE id = ?", (request.class_id,))
    class_row = cur.fetchone()
    if not class_row:
        conn.close()
        logging.warning(f"Booking failed: Class {request.class_id} not found for {request.client_email}")
        raise HTTPException(status_code=404, detail="Class not found")
    if class_row["available_slots"] <= 0:
        conn.close()
        logging.warning(f"Booking failed: No slots available for class {request.class_id} for {request.client_email}")
        raise HTTPException(status_code=400, detail="No slots available for this class")
    # Check if user already booked this class
    cur.execute("SELECT id FROM bookings WHERE class_id = ? AND client_email = ?", (request.class_id, request.client_email))
    existing_booking = cur.fetchone()
    if existing_booking:
        conn.close()
        logging.warning(f"Booking failed: User {request.client_email} already booked class {request.class_id}")
        raise HTTPException(status_code=400, detail="You have already booked this class")
    # Book the class
    booked_at = datetime.now(IST).strftime('%Y-%m-%d %H:%M:%S')
    cur.execute(
        "INSERT INTO bookings (class_id, client_name, client_email, booked_at) VALUES (?, ?, ?, ?)",
        (request.class_id, request.client_name, request.client_email, booked_at)
    )
    # Decrement available slots
    cur.execute(
        "UPDATE classes SET available_slots = available_slots - 1 WHERE id = ?",
        (request.class_id,)
    )
    booking_id = cur.lastrowid
    conn.commit()
    conn.close()
    logging.info(f"Booking successful: Class {request.class_id} booked for {request.client_email}")
    return Booking(
        id=booking_id,
        class_id=request.class_id,
        client_name=request.client_name,
        client_email=request.client_email,
        booked_at=IST.localize(datetime.strptime(booked_at, "%Y-%m-%d %H:%M:%S"))
    )

@app.get("/bookings", response_model=List[Booking], tags=["Bookings"])
def get_bookings(email: str):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, class_id, client_name, client_email, booked_at FROM bookings WHERE client_email = ?", (email,))
    rows = cur.fetchall()
    bookings = [
        Booking(
            id=row["id"],
            class_id=row["class_id"],
            client_name=row["client_name"],
            client_email=row["client_email"],
            booked_at=IST.localize(datetime.strptime(row["booked_at"], "%Y-%m-%d %H:%M:%S"))
        ) for row in rows
    ]
    conn.close()
    if not bookings:
        return []
    return bookings
