from app.services.assistant_service import AssistantService, get_assistant_service
from app.services.client_service import ClientService, get_client_service
from app.services.fleet_service import FleetService, get_fleet_service
from app.services.maintenance_service import MaintenanceService, get_maintenance_service
from app.services.order_service import OrderService, get_order_service
from app.services.quote_service import QuoteService, get_quote_service
from app.services.telemetry_service import TelemetryService, get_telemetry_service
from app.services.user_manager import UserManager, get_user_manager

__all__ = [
    "AssistantService",
    "ClientService",
    "FleetService",
    "MaintenanceService",
    "OrderService",
    "QuoteService",
    "TelemetryService",
    "UserManager",
    "get_assistant_service",
    "get_client_service",
    "get_fleet_service",
    "get_maintenance_service",
    "get_order_service",
    "get_quote_service",
    "get_telemetry_service",
    "get_user_manager",
]
