# MongoDB Atlas to Local MongoDB Migration Guide (Ubuntu)

Complete step-by-step guide to migrate from MongoDB Atlas to local MongoDB with MongoDB Compass.

---

## Prerequisites

- Ubuntu system (you're using Ubuntu)
- Access to MongoDB Atlas account
- Your current Atlas connection string
- Admin/sudo access on your Ubuntu machine

---

## Phase 1: Install MongoDB Community Edition on Ubuntu

### Step 1.1: Import MongoDB Public GPG Key

```bash
curl -fsSL https://pgp.mongodb.com/server-7.0.asc | sudo gpg -o /usr/share/keyrings/mongodb-server-7.0.gpg --dearmor
```

### Step 1.2: Add MongoDB Repository

```bash
echo "deb [ arch=amd64,arm64 signed-by=/usr/share/keyrings/mongodb-server-7.0.gpg ] https://repo.mongodb.org/apt/ubuntu jammy/mongodb-org/7.0 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb-org-7.0.list
```

**Note:** If you're using a different Ubuntu version, replace `jammy` with:
- `focal` for Ubuntu 20.04
- `jammy` for Ubuntu 22.04
- `mantic` for Ubuntu 23.10
- `noble` for Ubuntu 24.04

### Step 1.3: Update Package List

```bash
sudo apt-get update
```

### Step 1.4: Install MongoDB

```bash
sudo apt-get install -y mongodb-org
```

### Step 1.5: Start MongoDB Service

```bash
sudo systemctl start mongod
```

### Step 1.6: Enable MongoDB to Start on Boot

```bash
sudo systemctl enable mongod
```

### Step 1.7: Verify MongoDB is Running

```bash
sudo systemctl status mongod
```

You should see `Active: active (running)`. Press `q` to exit.

### Step 1.8: Test MongoDB Connection

```bash
mongosh
```

If `mongosh` is not installed, install it:

```bash
sudo apt-get install -y mongodb-mongosh
```

Then test:

```bash
mongosh
```

You should see MongoDB shell. Type `exit` to quit.

### Step 1.9: Verify MongoDB Port

```bash
sudo netstat -tlnp | grep 27017
```

Or using `ss`:

```bash
sudo ss -tlnp | grep 27017
```

You should see MongoDB listening on port 27017.

---

## Phase 2: Install MongoDB Database Tools (for export/import)

### Step 2.1: Download MongoDB Database Tools

```bash
cd /tmp
wget https://fastdl.mongodb.org/tools/db/mongodb-database-tools-ubuntu2204-x86_64-100.9.4.tgz
```

**Note:** If the version/URL is outdated, visit: https://www.mongodb.com/try/download/database-tools

### Step 2.2: Extract the Archive

```bash
tar -xzf mongodb-database-tools-ubuntu2204-x86_64-100.9.4.tgz
```

### Step 2.3: Copy Tools to System Path

```bash
sudo cp mongodb-database-tools-ubuntu2204-x86_64-100.9.4/bin/* /usr/local/bin/
```

### Step 2.4: Verify Installation

```bash
mongodump --version
mongorestore --version
```

---

## Phase 3: Install MongoDB Compass

### Step 3.1: Download MongoDB Compass

```bash
cd /tmp
wget https://downloads.mongodb.com/compass/mongodb-compass_1.44.0_amd64.deb
```

**Note:** Check for latest version at: https://www.mongodb.com/try/download/compass

### Step 3.2: Install MongoDB Compass

```bash
sudo dpkg -i mongodb-compass_1.44.0_amd64.deb
```

### Step 3.3: Fix Dependencies (if needed)

```bash
sudo apt-get install -f
```

### Step 3.4: Launch MongoDB Compass

```bash
mongodb-compass
```

Or search for "MongoDB Compass" in your applications menu.

---

## Phase 4: Export Data from MongoDB Atlas

### Step 4.1: Create Export Directory

```bash
mkdir -p ~/mongodb_migration
cd ~/mongodb_migration
```

### Step 4.2: Export from MongoDB Atlas

Replace the connection string with your actual Atlas connection string:

```bash
mongodump --uri="mongodb+srv://username:password@cluster.mongodb.net/dbname?retryWrites=true&w=majority" --out=./atlas_export
```

**Important:** 
- Replace `username` with your Atlas username
- Replace `password` with your Atlas password
- Replace `cluster.mongodb.net` with your cluster URL
- Replace `dbname` with your database name (or remove it to export all databases)

**Example:**
```bash
mongodump --uri="mongodb+srv://myuser:mypass@cluster0.abc123.mongodb.net/company_profiles_db?retryWrites=true&w=majority" --out=./atlas_export
```

### Step 4.3: Verify Export

```bash
ls -la ./atlas_export/
```

You should see directories for each database exported.

### Step 4.4: Check Export Contents

```bash
ls -la ./atlas_export/company_profiles_db/
```

You should see `.bson` and `.metadata.json` files for each collection.

---

## Phase 5: Import Data to Local MongoDB

### Step 5.1: Import to Local MongoDB

```bash
mongorestore --uri="mongodb://localhost:27017" ./atlas_export/company_profiles_db
```

**Note:** If you exported multiple databases, restore each one:

```bash
mongorestore --uri="mongodb://localhost:27017" ./atlas_export/
```

### Step 5.2: Verify Import in MongoDB Shell

```bash
mongosh
```

Then in the MongoDB shell:

```javascript
show dbs
use company_profiles_db
show collections
db.companyprofiles.countDocuments()
db.fundamentals.countDocuments()
exit
```

### Step 5.3: Verify in MongoDB Compass

1. Open MongoDB Compass
2. Connect to: `mongodb://localhost:27017`
3. Browse to your database
4. Verify collections and document counts

---

## Phase 6: Update Application Configuration

### Step 6.1: Navigate to Backend Directory

```bash
cd ~/Desktop/gemFinder/backend
```

### Step 6.2: Check Current .env File

```bash
cat .env
```

### Step 6.3: Backup Current .env File

```bash
cp .env .env.atlas_backup
```

### Step 6.4: Update .env File

Edit the `.env` file and change the MongoDB URL:

```bash
nano .env
```

Or use your preferred editor. Change:

**From:**
```env
MONGODB_URL=mongodb+srv://username:password@cluster.mongodb.net/dbname?retryWrites=true&w=majority
```

**To:**
```env
MONGODB_URL=mongodb://localhost:27017
```

**Or if you have authentication enabled:**
```env
MONGODB_URL=mongodb://username:password@localhost:27017/company_profiles_db
```

Save and exit (Ctrl+X, then Y, then Enter for nano).

### Step 6.5: Verify .env Changes

```bash
grep MONGODB_URL .env
```

---

## Phase 7: Test Application Connection

### Step 7.1: Ensure MongoDB is Running

```bash
sudo systemctl status mongod
```

If not running, start it:

```bash
sudo systemctl start mongod
```

### Step 7.2: Test Backend Connection

Navigate to your backend directory and test:

```bash
cd ~/Desktop/gemFinder/backend
python3 -c "from database.database import init_db; import asyncio; asyncio.run(init_db())"
```

Or simply start your backend:

```bash
python3 main.py
```

You should see:
```
✅ MongoDB connected to company_profiles_db
   Connection: localhost:27017
```

### Step 7.3: Test API Endpoints

In another terminal, test your API:

```bash
curl http://localhost:8000/api/v1/profiles/
```

Or visit: http://localhost:8000/docs

---

## Phase 8: Optional - Set Up MongoDB Authentication (Recommended for Production)

### Step 8.1: Connect to MongoDB

```bash
mongosh
```

### Step 8.2: Create Admin User

```javascript
use admin
db.createUser({
  user: "admin",
  pwd: "your_secure_password",
  roles: [ { role: "userAdminAnyDatabase", db: "admin" }, "readWriteAnyDatabase" ]
})
exit
```

### Step 8.3: Enable Authentication

```bash
sudo nano /etc/mongod.conf
```

Find the `security:` section and uncomment/add:

```yaml
security:
  authorization: enabled
```

Save and exit.

### Step 8.4: Restart MongoDB

```bash
sudo systemctl restart mongod
```

### Step 8.5: Update .env with Authentication

```bash
nano ~/Desktop/gemFinder/backend/.env
```

Change to:

```env
MONGODB_URL=mongodb://admin:your_secure_password@localhost:27017/company_profiles_db?authSource=admin
```

---

## Phase 9: Verification Checklist

### ✅ Verify MongoDB Service

```bash
sudo systemctl status mongod
```

### ✅ Verify MongoDB Port

```bash
sudo ss -tlnp | grep 27017
```

### ✅ Verify Data Import

```bash
mongosh
use company_profiles_db
show collections
db.companyprofiles.countDocuments()
exit
```

### ✅ Verify Application Connection

```bash
cd ~/Desktop/gemFinder/backend
python3 main.py
```

### ✅ Verify MongoDB Compass Connection

- Open MongoDB Compass
- Connect to: `mongodb://localhost:27017`
- Browse your database and collections

---

## Troubleshooting Commands

### Check MongoDB Logs

```bash
sudo journalctl -u mongod -n 50
```

Or:

```bash
sudo tail -f /var/log/mongodb/mongod.log
```

### Restart MongoDB

```bash
sudo systemctl restart mongod
```

### Stop MongoDB

```bash
sudo systemctl stop mongod
```

### Check MongoDB Configuration

```bash
cat /etc/mongod.conf
```

### Check Disk Space

```bash
df -h
```

### Check MongoDB Data Directory

```bash
ls -lh /var/lib/mongodb/
```

---

## Rollback Plan (If Something Goes Wrong)

### Restore .env to Atlas

```bash
cd ~/Desktop/gemFinder/backend
cp .env.atlas_backup .env
```

### Restart Application

```bash
python3 main.py
```

Your application will connect back to Atlas.

---

## Cleanup (After Successful Migration)

### Remove Export Directory (Optional)

```bash
rm -rf ~/mongodb_migration
```

**Note:** Keep the backup until you're 100% sure everything works!

---

## Summary of Key Commands

```bash
# Install MongoDB
curl -fsSL https://pgp.mongodb.com/server-7.0.asc | sudo gpg -o /usr/share/keyrings/mongodb-server-7.0.gpg --dearmor
echo "deb [ arch=amd64,arm64 signed-by=/usr/share/keyrings/mongodb-server-7.0.gpg ] https://repo.mongodb.org/apt/ubuntu jammy/mongodb-org/7.0 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb-org-7.0.list
sudo apt-get update
sudo apt-get install -y mongodb-org
sudo systemctl start mongod
sudo systemctl enable mongod

# Install MongoDB Tools
cd /tmp
wget https://fastdl.mongodb.org/tools/db/mongodb-database-tools-ubuntu2204-x86_64-100.9.4.tgz
tar -xzf mongodb-database-tools-ubuntu2204-x86_64-100.9.4.tgz
sudo cp mongodb-database-tools-ubuntu2204-x86_64-100.9.4/bin/* /usr/local/bin/

# Install MongoDB Compass
cd /tmp
wget https://downloads.mongodb.com/compass/mongodb-compass_1.44.0_amd64.deb
sudo dpkg -i mongodb-compass_1.44.0_amd64.deb
sudo apt-get install -f

# Export from Atlas
mkdir -p ~/mongodb_migration && cd ~/mongodb_migration
mongodump --uri="YOUR_ATLAS_CONNECTION_STRING" --out=./atlas_export

# Import to Local
mongorestore --uri="mongodb://localhost:27017" ./atlas_export/company_profiles_db

# Update .env
cd ~/Desktop/gemFinder/backend
cp .env .env.atlas_backup
# Edit .env and change MONGODB_URL to: mongodb://localhost:27017
```

---

## Next Steps

1. ✅ MongoDB installed and running
2. ✅ MongoDB Compass installed
3. ✅ Data exported from Atlas
4. ✅ Data imported to local MongoDB
5. ✅ Application configured
6. ✅ Tested and verified

You're now running on local MongoDB! 🎉

