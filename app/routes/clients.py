import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi_users.exceptions import UserAlreadyExists, UserNotExists

from app.core.auth import current_superuser

from app.schemas import CreateClientRequest, CreateClientResponse
from app.services import ClientService, get_client_service

router = APIRouter(dependencies=[Depends(current_superuser)])

@router.post("/", response_model=CreateClientResponse, status_code=status.HTTP_201_CREATED)
async def create_client(
    client_data: CreateClientRequest,
    client_service: ClientService = Depends(get_client_service),
) -> CreateClientResponse:
    try:
        return await client_service.create_client(client_data.name)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.get("/", response_model=list[CreateClientResponse])
async def get_clients(
    client_service: ClientService = Depends(get_client_service),
) -> list[CreateClientResponse]:
    return await client_service.get_clients()

@router.delete("/{client_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_client(
    client_id: str,
    client_service: ClientService = Depends(get_client_service),
):
    try:
        await client_service.delete_client(client_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

