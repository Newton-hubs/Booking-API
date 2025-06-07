# Project Planning: Fitness Studio Booking API

## Overview
A backend API for a fitness studio to manage class schedules and client bookings, supporting timezone management and robust error handling.

## Tech Stack
- Python (FastAPI recommended)
- SQLite (in-memory or file-based)
- pytest for testing
- Timezone: IST (with conversion support)

## Features
- List all upcoming classes
- Book a class (with slot validation)
- View bookings by client email
- Timezone-aware scheduling

## Project Structure
```
/booking_api/
    main.py
    models.py
    schemas.py
    db.py
    utils.py
    seed_data.py
    tests/
        test_main.py
    README.md
    TESTING.md
    requirements.txt
```

## Key Tasks
1. Set up FastAPI project and dependencies
2. Define data models (Class, Booking)
3. Implement SQLite in-memory/file DB with seed data
4. Create API endpoints:
    - GET /classes
    - POST /book
    - GET /bookings
5. Add timezone management utilities
6. Input validation and error handling
7. Logging setup
8. Unit tests for all endpoints
9. Prepare documentation (README, TESTING)
10. Initialize git repository and push code
