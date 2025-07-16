from config import get_settings
from .connection_manager import ConnectionManager

manager = ConnectionManager()


def get_connection_manager() -> ConnectionManager:
    return manager
