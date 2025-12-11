# MongoDB Atlas Setup Guide (FREE Tier)

## Step-by-Step Instructions

### 1. Create MongoDB Atlas Account

1. Go to https://www.mongodb.com/cloud/atlas/register
2. Sign up with:
   - Email address
   - OR Google account
   - OR GitHub account
3. Complete email verification if required

### 2. Create a FREE Cluster

1. After login, click **"Build a Database"** or **"Create"**
2. Choose **"M0 FREE"** tier (512MB storage)
   - **IMPORTANT**: Select M0, it's FREE forever
3. Choose your preferred cloud provider:
   - AWS (recommended)
   - Google Cloud
   - Azure
4. Select a region close to you (e.g., Mumbai, Singapore, US-East)
5. Give your cluster a name (default: "Cluster0" is fine)
6. Click **"Create Cluster"**
7. Wait 1-3 minutes for cluster creation

### 3. Create Database User

1. You'll see a "Security Quickstart" screen
2. Under **"How would you like to authenticate your connection?"**
   - Select **"Username and Password"**
3. Create a database user:
   - Username: `admin` (or any name you prefer)
   - Password: Click **"Autogenerate Secure Password"** (SAVE THIS!)
     - Or create your own strong password
4. Click **"Create User"**
5. **IMPORTANT**: Save the username and password somewhere safe

### 4. Whitelist IP Address

1. Still on Security Quickstart, scroll to **"Where would you like to connect from?"**
2. Click **"Add My Current IP Address"**
3. For development, also add: **0.0.0.0/0** (allows from anywhere)
   - Click **"Add a Different IP Address"**
   - Enter: `0.0.0.0/0`
   - Description: "Allow from anywhere"
4. Click **"Finish and Close"**

### 5. Get Connection String

1. Click **"Connect"** button on your cluster
2. Choose **"Connect your application"**
3. Select:
   - Driver: **Python**
   - Version: **3.12 or later** (or any version)
4. Copy the connection string, it looks like:
   ```
   mongodb+srv://admin:<password>@cluster0.xxxxx.mongodb.net/?retryWrites=true&w=majority
   ```
5. **IMPORTANT**: Replace `<password>` with your actual password from Step 3

### 6. Update .env File

1. Open `.env` file in the project root
2. Replace the MONGODB_URL line:
   ```env
   # OLD (local MongoDB)
   MONGODB_URL=mongodb://localhost:27017

   # NEW (MongoDB Atlas)
   MONGODB_URL=mongodb+srv://admin:YOUR_PASSWORD_HERE@cluster0.xxxxx.mongodb.net/?retryWrites=true&w=majority
   ```
3. Save the file

### Example .env File

```env
# Environment
ENVIRONMENT=development
DEBUG=True

# MongoDB Configuration - MongoDB Atlas
MONGODB_URL=mongodb+srv://admin:MySecurePass123@cluster0.abcde.mongodb.net/?retryWrites=true&w=majority
DATABASE_NAME=org_management

# JWT Configuration
SECRET_KEY=dev-secret-key-for-local-development-please-change-in-production-min-32-chars
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# CORS Configuration
CORS_ORIGINS=http://localhost:3000,http://localhost:8000

# Logging
LOG_LEVEL=DEBUG
```

### 7. Test Connection

Run the test script:

```bash
python test_connection.py
```

If successful, you'll see:
```
[SUCCESS] All tests passed! MongoDB is ready.
```

### 8. Run the Application

```bash
uvicorn app.main:app --reload
```

Access at: http://localhost:8000

---

## Troubleshooting

### Error: "Authentication failed"
- Check username and password in connection string
- Make sure you replaced `<password>` with actual password
- Password may contain special characters, URL-encode them:
  - `@` → `%40`
  - `#` → `%23`
  - `%` → `%25`

### Error: "Connection timeout"
- Check IP whitelist in Atlas
- Ensure `0.0.0.0/0` is added for development
- Check your internet connection

### Error: "Database name not found"
- This is normal! Database will be created automatically
- Continue with the application

---

## Quick Reference

### MongoDB Atlas Dashboard
- URL: https://cloud.mongodb.com
- Cluster → Connect → Connection String

### Useful Commands
```bash
# Test connection
python test_connection.py

# Run application
uvicorn app.main:app --reload

# Access API docs
http://localhost:8000/docs
```

---

## What's FREE in M0 Tier?

✅ 512MB storage
✅ Shared RAM
✅ Shared vCPU
✅ No credit card required
✅ No time limit
✅ Automatic backups
✅ Built-in monitoring

---

## Need Help?

1. MongoDB Atlas Documentation: https://docs.atlas.mongodb.com
2. Connection String Format: https://docs.mongodb.com/manual/reference/connection-string/
3. Check cluster status in Atlas dashboard
