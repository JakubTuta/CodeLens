import api.connection_manager as connection_manager

manager = connection_manager.ConnectionManager()


def get_connection_manager() -> connection_manager.ConnectionManager:
    return manager
