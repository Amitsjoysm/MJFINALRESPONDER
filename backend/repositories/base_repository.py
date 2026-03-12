"""Repository pattern for database operations (Dependency Inversion)"""
from typing import List, Optional, Dict, Any
from abc import ABC, abstractmethod
from motor.motor_asyncio import AsyncIOMotorDatabase
import logging

logger = logging.getLogger(__name__)

class BaseRepository(ABC):
    """Abstract base repository (Interface Segregation)"""
    
    def __init__(self, db: AsyncIOMotorDatabase, collection_name: str):
        self.db = db
        self.collection = db[collection_name]
    
    @abstractmethod
    async def find_by_id(self, id: str) -> Optional[Dict]:
        """Find document by ID"""
        pass
    
    @abstractmethod
    async def find_many(self, filters: Dict, limit: int = 100) -> List[Dict]:
        """Find multiple documents"""
        pass
    
    @abstractmethod
    async def create(self, data: Dict) -> str:
        """Create new document"""
        pass
    
    @abstractmethod
    async def update(self, id: str, data: Dict) -> bool:
        """Update document"""
        pass
    
    @abstractmethod
    async def delete(self, id: str) -> bool:
        """Delete document"""
        pass

class GenericRepository(BaseRepository):
    """Generic repository implementation"""
    
    async def find_by_id(self, id: str) -> Optional[Dict]:
        """Find document by ID"""
        try:
            return await self.collection.find_one({"id": id})
        except Exception as e:
            logger.error(f"Error finding document: {e}")
            return None
    
    async def find_one(self, filters: Dict) -> Optional[Dict]:
        """Find single document"""
        try:
            return await self.collection.find_one(filters)
        except Exception as e:
            logger.error(f"Error finding document: {e}")
            return None
    
    async def find_many(self, filters: Dict, limit: int = 100, skip: int = 0, sort: List = None) -> List[Dict]:
        """Find multiple documents"""
        try:
            cursor = self.collection.find(filters).skip(skip).limit(limit)
            if sort:
                cursor = cursor.sort(sort)
            return await cursor.to_list(limit)
        except Exception as e:
            logger.error(f"Error finding documents: {e}")
            return []
    
    async def count(self, filters: Dict) -> int:
        """Count documents"""
        try:
            return await self.collection.count_documents(filters)
        except Exception as e:
            logger.error(f"Error counting documents: {e}")
            return 0
    
    async def create(self, data: Dict) -> str:
        """Create new document"""
        try:
            result = await self.collection.insert_one(data)
            return data.get('id')
        except Exception as e:
            logger.error(f"Error creating document: {e}")
            raise
    
    async def update(self, id: str, data: Dict) -> bool:
        """Update document"""
        try:
            result = await self.collection.update_one(
                {"id": id},
                {"$set": data}
            )
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Error updating document: {e}")
            return False
    
    async def update_many(self, filters: Dict, data: Dict) -> int:
        """Update multiple documents"""
        try:
            result = await self.collection.update_many(filters, {"$set": data})
            return result.modified_count
        except Exception as e:
            logger.error(f"Error updating documents: {e}")
            return 0
    
    async def delete(self, id: str) -> bool:
        """Delete document"""
        try:
            result = await self.collection.delete_one({"id": id})
            return result.deleted_count > 0
        except Exception as e:
            logger.error(f"Error deleting document: {e}")
            return False
    
    async def delete_many(self, filters: Dict) -> int:
        """Delete multiple documents"""
        try:
            result = await self.collection.delete_many(filters)
            return result.deleted_count
        except Exception as e:
            logger.error(f"Error deleting documents: {e}")
            return 0

class RepositoryFactory:
    """Factory for creating repositories (Factory Pattern)"""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self._repositories = {}
    
    def get_repository(self, collection_name: str) -> GenericRepository:
        """Get or create repository for collection"""
        if collection_name not in self._repositories:
            self._repositories[collection_name] = GenericRepository(self.db, collection_name)
        return self._repositories[collection_name]
    
    def get_user_repository(self) -> GenericRepository:
        return self.get_repository('users')
    
    def get_email_repository(self) -> GenericRepository:
        return self.get_repository('emails')
    
    def get_email_account_repository(self) -> GenericRepository:
        return self.get_repository('email_accounts')
    
    def get_intent_repository(self) -> GenericRepository:
        return self.get_repository('intents')
    
    def get_knowledge_base_repository(self) -> GenericRepository:
        return self.get_repository('knowledge_base')
    
    def get_calendar_provider_repository(self) -> GenericRepository:
        return self.get_repository('calendar_providers')
    
    def get_calendar_event_repository(self) -> GenericRepository:
        return self.get_repository('calendar_events')
    
    def get_follow_up_repository(self) -> GenericRepository:
        return self.get_repository('follow_ups')
