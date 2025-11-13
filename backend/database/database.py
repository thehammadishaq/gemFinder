"""
Database Configuration
MongoDB setup using Motor and Beanie ODM
"""
from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient
from models.company_profile import CompanyProfile
from models.fundamentals import Fundamentals
from config.settings import settings


# MongoDB connection URL from settings
MONGODB_URL = settings.MONGODB_URL
DATABASE_NAME = settings.DATABASE_NAME

# Global client instance
client: AsyncIOMotorClient = None


async def init_db():
    """
    Initialize MongoDB connection and Beanie
    Call this on application startup
    """
    global client
    
    try:
        # Create Motor client with connection timeout
        client = AsyncIOMotorClient(
            MONGODB_URL,
            serverSelectionTimeoutMS=5000  # 5 second timeout
        )
        
        # Test connection
        await client.admin.command('ping')
        
        # Initialize Beanie with the database and document models
        await init_beanie(
            database=client[DATABASE_NAME],
            document_models=[CompanyProfile, Fundamentals]
        )
        
        print(f"✅ MongoDB connected to {DATABASE_NAME}")
        print(f"   Connection: {MONGODB_URL.split('@')[1] if '@' in MONGODB_URL else 'Atlas'}")
    except Exception as e:
        print(f"❌ MongoDB connection failed: {e}")
        print("\n📋 To fix this:")
        print("   1. Make sure MongoDB is running locally, OR")
        print("   2. Use MongoDB Atlas (cloud) - update MONGODB_URL in .env file")
        print("\n   Local MongoDB:")
        print("   - Windows: Start MongoDB service or run: mongod")
        print("   - Docker: docker run -d -p 27017:27017 --name mongodb mongo:latest")
        print("\n   MongoDB Atlas:")
        print("   - Sign up at: https://www.mongodb.com/cloud/atlas")
        print("   - Get connection string and update MONGODB_URL in .env")
        raise


async def close_db():
    """
    Close MongoDB connection
    Call this on application shutdown
    """
    global client
    if client:
        client.close()
        print("✅ MongoDB connection closed")


def get_database():
    """
    Get database instance
    """
    if client is None:
        raise RuntimeError("Database not initialized. Call init_db() first.")
    return client[DATABASE_NAME]
