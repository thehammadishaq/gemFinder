# Quick Start - MongoDB Setup

## Option 1: MongoDB Atlas (Cloud) - EASIEST ⭐

### Step 1: Sign Up
1. Go to: https://www.mongodb.com/cloud/atlas/register
2. Create free account
3. Create free cluster (M0 - Free tier)

### Step 2: Get Connection String
1. Click "Connect" on your cluster
2. Choose "Connect your application"
3. Copy the connection string
   - Example: `mongodb+srv://username:password@cluster.mongodb.net/dbname?retryWrites=true&w=majority`

### Step 3: Update .env File
Create `.env` file in `backend` folder:

```env
MONGODB_URL=mongodb+srv://username:password@cluster.mongodb.net/dbname?retryWrites=true&w=majority
DATABASE_NAME=company_profiles_db
HOST=0.0.0.0
PORT=8000
DEBUG=True
CORS_ORIGINS=http://localhost:5173,http://localhost:3000
```

**Replace:**
- `username` - Your MongoDB Atlas username
- `password` - Your MongoDB Atlas password
- `cluster.mongodb.net` - Your cluster URL
- `dbname` - Your database name (or remove it)

### Step 4: Start Backend
```powershell
python main.py
```

Done! ✅

---

## Option 2: Local MongoDB Installation

### Step 1: Download MongoDB
1. Visit: https://www.mongodb.com/try/download/community
2. Select:
   - Version: 7.0 (Latest)
   - Platform: Windows
   - Package: MSI
3. Download and run installer

### Step 2: Install MongoDB
During installation:
- ✅ Check "Install MongoDB as a Service"
- ✅ Check "Install MongoDB Compass" (optional)
- Service Name: `MongoDB` (default)
- Data Directory: Default (C:\Program Files\MongoDB\Server\7.0\data)

### Step 3: Start MongoDB Service
```powershell
# Run PowerShell as Administrator
Start-Service MongoDB

# Or use the script
.\check_mongodb_service.ps1
```

### Step 4: Verify MongoDB is Running
```powershell
Get-Service MongoDB
# Should show: Status: Running
```

### Step 5: Start Backend
```powershell
python main.py
```

---

## Which Option to Choose?

**Use MongoDB Atlas if:**
- ✅ You want quick setup (5 minutes)
- ✅ No installation needed
- ✅ Works from anywhere
- ✅ Free tier available

**Use Local MongoDB if:**
- ✅ You want offline access
- ✅ You need full control
- ✅ You're comfortable with installations

**Recommendation:** Start with MongoDB Atlas - it's faster and easier! 🚀

