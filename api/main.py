from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi.errors import RateLimitExceeded
from slowapi import _rate_limit_exceeded_handler

import config
import database
from routers import scanner, system

# 1. Initialize Database
database.init_db()

# 2. Setup FastAPI App
app = FastAPI(
    title="Protego API",
    description="Taglish scam detection — mBERT + Early Fusion (770-dim)",
    version="3.0.0"
)

# 3. Setup Limiter & CORS
app.state.limiter = config.limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=config.ALLOWED_ORIGINS,
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["Content-Type"],
)

# 4. Plug in the Routes
app.include_router(scanner.router)
app.include_router(system.router)

@app.get("/")
def root():
    return {
        "status": "running",
        "mock_mode": config.MOCK_MODE,
        "device": str(config.DEVICE),
        "docs": "http://localhost:8000/docs"
    }