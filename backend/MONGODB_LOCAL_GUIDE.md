# MongoDB Local Setup Guide (Without Docker)

## Option 1: Install MongoDB Community Edition

### Step 1: Download MongoDB
1. Visit: https://www.mongodb.com/try/download/community
2. Select:
   - Version: Latest (7.0 or 6.0)
   - Platform: Windows
   - Package: MSI
3. Click "Download"

### Step 2: Install MongoDB
1. Run the downloaded `.msi` file
2. During installation:
   - ✅ Check "Install MongoDB as a Service"
   - ✅ Check "Install MongoDB Compass" (optional GUI tool)
   - Service Name: `MongoDB` (default)
   - Data Directory: `C:\Program Files\MongoDB\Server\7.0\data`
   - Log Directory: `C:\Program Files\MongoDB\Server\7.0\log`

### Step 3: Start MongoDB Service
After installation, MongoDB service should start automatically.

**Check if running:**
```powershell
Get-Service MongoDB
```

**If not running, start it:**
```powershell
# Run PowerShell as Administrator
Start-Service MongoDB
```

**Or use the script:**
```powershell
cd backend
.\start_mongodb_local.ps1
```

---

## Option 2: Manual Start (If MongoDB is installed but service not configured)

### Step 1: Create Data Directory
```powershell
New-Item -ItemType Directory -Path "C:\data\db" -Force
```

### Step 2: Find MongoDB Installation
Common locations:
- `C:\Program Files\MongoDB\Server\7.0\bin\mongod.exe`
- `C:\Program Files\MongoDB\Server\6.0\bin\mongod.exe`

### Step 3: Start MongoDB Manually
```powershell
# Replace path with your MongoDB installation path
& "C:\Program Files\MongoDB\Server\7.0\bin\mongod.exe" --dbpath "C:\data\db"
```

**Or use the script (it will find MongoDB automatically):**
```powershell
cd backend
.\start_mongodb_local.ps1
```

---

## Option 3: MongoDB Atlas (Cloud - No Installation Needed)

If you don't want to install MongoDB locally:

1. **Sign up:** https://www.mongodb.com/cloud/atlas/register
2. **Create free cluster** (M0 - Free tier)
3. **Get connection string:**
   - Click "Connect" on your cluster
   - Choose "Connect your application"
   - Copy the connection string
4. **Update `.env` file:**
   ```
   MONGODB_URL=mongodb+srv://username:password@cluster.mongodb.net/dbname?retryWrites=true&w=majority
   DATABASE_NAME=company_profiles_db
   ```

---

## Verify MongoDB is Running

### Check if MongoDB is running:
```powershell
# Check service
Get-Service MongoDB

# Check process
Get-Process mongod

# Test connection
mongosh
# Or
mongo
```

### Test connection from Python:
```python
from motor.motor_asyncio import AsyncIOMotorClient
import asyncio

async def test():
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    result = await client.admin.command('ping')
    print("✅ MongoDB connected:", result)

asyncio.run(test())
```

---

## Troubleshooting

### Port 27017 already in use:
```powershell
# Find what's using port 27017
netstat -ano | findstr :27017

# Kill the process (replace PID with actual process ID)
taskkill /PID <PID> /F
```

### MongoDB service won't start:
1. Check logs: `C:\Program Files\MongoDB\Server\7.0\log\mongod.log`
2. Check if data directory exists and has permissions
3. Try starting manually to see error messages

### Can't find MongoDB:
1. Check if MongoDB is installed:
   ```powershell
   Get-ChildItem "C:\Program Files\MongoDB" -ErrorAction SilentlyContinue
   ```
2. Add MongoDB to PATH:
   - Add `C:\Program Files\MongoDB\Server\7.0\bin` to System PATH
   - Restart PowerShell

---

## Quick Start Script

Use the provided script:
```powershell
cd backend
.\start_mongodb_local.ps1
```

This script will:
- ✅ Find MongoDB installation
- ✅ Create data directory if needed
- ✅ Start MongoDB
- ✅ Verify it's running

---

## After MongoDB is Running

Start your backend:
```powershell
python main.py
```

MongoDB should connect automatically! 🎉

