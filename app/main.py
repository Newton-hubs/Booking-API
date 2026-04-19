from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import engine
from app.models import Base
from app.routers import auth, classes, bookings
from app.core.config import get_settings
from app.core.logging import logger

settings = get_settings()

@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)  # ← move it here
    logger.info(f"Server started | env={settings.app_env} db={settings.database_url[:30]}...")
    
app = FastAPI(
    title="Fitness Studio Booking API",
    description=(
        "REST API for managing fitness class bookings.\n\n"
        "**Authentication**: Register at `/auth/register`, then login at `/auth/login` "
        "to receive a JWT. Pass the token as `Bearer <token>` in the `Authorization` header.\n\n"
        "**Roles**: `user` can browse and book classes. `admin` can additionally create "
        "and delete classes."
    ),
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(classes.router)
app.include_router(bookings.router)


@app.get("/", tags=["Health"])
def health_check():
    return {
        "status": "ok",
        "service": "Fitness Studio Booking API",
        "version": "2.0.0",
        "environment": settings.app_env,
    }


@app.on_event("startup")
def on_startup():
    logger.info(f"Server started | env={settings.app_env} db={settings.database_url[:30]}...")
