# Fitness Studio Booking API

A FastAPI project for managing fitness class schedules and bookings.

## Features
- List all upcoming classes
- Book a class (with slot validation)
- View bookings by client email
- Timezone-aware scheduling (IST by default)
- Error handling and logging

## Setup Instructions

1. **Clone the repository**
   ```powershell
   git clone <your-repo-url>
   cd "Booking API"
   ```

2. **Install dependencies**
   ```powershell
   pip install -r requirements.txt
   ```

3. **Run the API**
   ```powershell
   uvicorn main:app --reload
   ```

4. **API Docs**
   Visit [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

## Sample Requests

### List Classes
```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/classes" -Method Get
```

### Book a Class
```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/book" -Method Post -ContentType "application/json" -Body '{"class_id": 1, "client_name": "John Doe", "client_email": "john@example.com"}'
```

### View Bookings by Email
```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/bookings?email=john@example.com" -Method Get
```

## Timezone Management
All classes are created in IST. If you change the timezone, all class times and slots will be adjusted accordingly.

## Logging
Logs are written to both `app.log` and the console for all booking attempts and errors.

## License
MIT
