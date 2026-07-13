from fastapi import FastAPI

from app.core.auth import auth_backend, fastapi_users
from app.routes.users import router as users_router
from app.routes.clients import router as clients_router

app = FastAPI()

app.include_router(
    fastapi_users.get_auth_router(auth_backend), prefix="/auth/jwt", tags=["auth"]
)
app.include_router(users_router, prefix="/users", tags=["users"])
app.include_router(clients_router, prefix="/clients", tags=["clients"])


@app.get("/")
async def root():
    return {"message": "Hello World"}
