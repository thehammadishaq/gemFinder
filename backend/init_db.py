"""
Database Initialization Script
Run this script to initialize MongoDB connection and create indexes
"""
import asyncio
from database.database import init_db, close_db


async def main():
    print("Initializing MongoDB connection...")
    await init_db()
    print("✅ MongoDB initialized successfully!")
    print("✅ Indexes created automatically by Beanie")
    await close_db()


if __name__ == "__main__":
    asyncio.run(main())
