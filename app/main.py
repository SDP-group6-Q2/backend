from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.auth import auth_backend, fastapi_users
from app.routes.users import router as users_router
from app.routes.assistant import router as assistant_router

import logging
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(
    fastapi_users.get_auth_router(auth_backend), prefix="/auth/jwt", tags=["auth"]
)
app.include_router(users_router, prefix="/users", tags=["users"])
app.include_router(assistant_router, prefix="/assistant", tags=["assistant"])

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")

@app.get("/")
async def root():
    return {"message": "Hello There!"}
