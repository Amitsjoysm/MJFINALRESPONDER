"""Dependency Injection Container (Dependency Inversion Principle)"""
from motor.motor_asyncio import AsyncIOMotorDatabase
from typing import Dict
import logging

from repositories.base_repository import RepositoryFactory, GenericRepository
from services.auth_service_v2 import AuthService
# from services.ai_agent_service import AIAgentService  # Used directly by workers, not via container
from utils.encryption import initialize_encryption

logger = logging.getLogger(__name__)

class ServiceContainer:
    """Service container for dependency injection"""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self._repository_factory = None
        self._services = {}
        self._initialized = False
    
    def initialize(self, encryption_key: str):
        """Initialize all services"""
        if self._initialized:
            return
        
        logger.info("Initializing service container...")
        
        # Initialize encryption
        initialize_encryption(encryption_key)
        
        # Initialize repository factory
        self._repository_factory = RepositoryFactory(self.db)
        
        # Initialize services
        self._services['auth'] = AuthService(
            self._repository_factory.get_user_repository()
        )
        
        # Note: AI Agent Service is used directly by workers, not via container
        # Workers instantiate AIAgentService(db) directly
        
        self._initialized = True
        logger.info("Service container initialized")
    
    def get_repository_factory(self) -> RepositoryFactory:
        """Get repository factory"""
        if not self._initialized:
            raise RuntimeError("Service container not initialized")
        return self._repository_factory
    
    def get_auth_service(self) -> AuthService:
        """Get auth service"""
        if not self._initialized:
            raise RuntimeError("Service container not initialized")
        return self._services['auth']
    
    # AI Agent Service is used directly by workers, not via container
    # def get_ai_agent_service(self):
    #     """Get AI agent service"""
    #     if not self._initialized:
    #         raise RuntimeError("Service container not initialized")
    #     return self._services['ai_agent']
    
    def get_repository(self, name: str) -> GenericRepository:
        """Get repository by name"""
        if not self._initialized:
            raise RuntimeError("Service container not initialized")
        return self._repository_factory.get_repository(name)

# Global service container
service_container: ServiceContainer = None

def initialize_container(db: AsyncIOMotorDatabase, encryption_key: str) -> ServiceContainer:
    """Initialize global service container"""
    global service_container
    service_container = ServiceContainer(db)
    service_container.initialize(encryption_key)
    return service_container

def get_container() -> ServiceContainer:
    """Get global service container"""
    if service_container is None:
        raise RuntimeError("Service container not initialized")
    return service_container
