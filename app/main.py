from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from app.core.auth import auth_backend, fastapi_users
from app.routes.users import router as users_router
from app.routes.clients import router as clients_router
from app.routes.assistant import router as assistant_router
from app.routes.machines import router as machines_router
from app.routes.maintenance import router as maintenance_router
from app.routes.orders import router as orders_router
from app.routes.quotes import router as quotes_router
from app.core.exceptions import AccessDeniedError, InvalidCursorError, NotFoundError

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
app.include_router(clients_router, prefix="/clients", tags=["clients"])
app.include_router(assistant_router, prefix="/assistant", tags=["assistant"])
app.include_router(machines_router, prefix="/machines", tags=["machines"])
app.include_router(maintenance_router, prefix="/maintenance-tickets", tags=["maintenance"])
app.include_router(quotes_router, prefix="/quotes", tags=["quotes"])
app.include_router(orders_router, prefix="/orders", tags=["orders"])


@app.exception_handler(AccessDeniedError)
async def access_denied_handler(_: Request, exc: AccessDeniedError):
    return JSONResponse(status_code=403, content={"detail": str(exc)})


@app.exception_handler(NotFoundError)
async def not_found_handler(_: Request, exc: NotFoundError):
    return JSONResponse(status_code=404, content={"detail": str(exc)})


@app.exception_handler(InvalidCursorError)
async def invalid_cursor_handler(_: Request, exc: InvalidCursorError):
    return JSONResponse(status_code=400, content={"detail": str(exc)})

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")

@app.get("/")
async def root():
    return {"message": "Hello There!"}
