# 🚀 Render Deployment - Database Connection Fix

## The Problem
Your Render app is timing out trying to connect to Supabase because the `DATABASE_URL` environment variable is not properly configured.

**Error Summary:**
```
connection to server at "addyskbgjhqmzrseqvnh.supabase.co" ... port 5432 failed: timeout expired
connection to server at "localhost" (127.0.0.1), port 5432 failed: Connection refused
```

## Quick Fix (5 minutes)

### Step 1: Get Your Supabase CONNECTION STRING

1. Go to **Supabase Dashboard**: https://app.supabase.com
2. Select your project
3. Go to **Settings → Database**
4. Under **Connection String**, copy the **URI** (not Connection Pooler)
5. Replace `[YOUR-PASSWORD]` with your database password
6. Should look like:
   ```
   postgresql://postgres:YOUR_PASSWORD@addyskbgjhqmzrseqvnh.supabase.co:5432/postgres
   ```

### Step 2: Set Environment Variable on Render

1. Go to your Render service: https://dashboard.render.com
2. Select your **hr-web-app** service
3. Click **Environment** (tab on top)
4. Add/Update these variables:

   | Key | Value |
   |-----|-------|
   | `DATABASE_URL` | `postgresql://postgres:YOUR_PASSWORD@addyskbgjhqmzrseqvnh.supabase.co:5432/postgres` |
   | `FLASK_ENV` | `production` |
   | `SECRET_KEY` | (use existing or generate new) |
   | `SMTP_SERVER` | `smtp.gmail.com` |
   | `SMTP_PORT` | `587` |
   | `SENDER_EMAIL` | (your Gmail) |
   | `SENDER_PASSWORD` | (App Password) |

5. Click **Save Changes**
6. Render will automatically **redeploy**

### Step 3: Verify Connection

After redeployment (2-3 minutes):
1. Go to your app: https://hr-web-app-5.onrender.com
2. Check the **Logs** tab - should see: `✅ Connected to Supabase/Online database`
3. Try to log in

---

## 🔧 If Still Getting Timeout

### A. Check Supabase Firewall (if enabled)

1. Supabase Dashboard → **Settings → Network**
2. If you have IP restrictions, add Render's IP:
   - Render IPs: `52.7.109.63`, `34.236.247.197`, `34.232.177.147` (or check Render docs)
   - Or disable IP restrictions for testing

### B. Verify Connection String Format

Your string should be:
```
postgresql://postgres:PASSWORD@addyskbgjhqmzrseqvnh.supabase.co:5432/postgres
```

❌ **WRONG:**
- `postgres://` (old format, should be `postgresql://`)
- Missing password
- Wrong hostname

### C. Check for Special Characters

If your password has special characters (`@`, `#`, `%`, etc.), URL-encode them:
- `@` → `%40`
- `#` → `%23`
- `%` → `%25`

Example:
```
postgresql://postgres:pass%40word@host:5432/postgres
```

---

## 📋 Updated Connection Code (Already Applied)

Your `models/db.py` has been updated to:

✅ **Support `DATABASE_URL`** from environment  
✅ **Add SSL/TLS** (`sslmode=require`)  
✅ **Add timeouts** (connect: 10s, statement: 30s)  
✅ **Better error logging** showing what failed  
✅ **Graceful fallback** to local PostgreSQL (for development)

---

## 🧪 Test Locally First

Before redeploying:

1. Copy your Supabase URL to `.env`:
   ```bash
   DATABASE_URL=postgresql://postgres:PASSWORD@addyskbgjhqmzrseqvnh.supabase.co:5432/postgres
   ```

2. Run locally:
   ```bash
   python -m flask run
   ```

3. Should see:
   ```
   ✅ Connected to Supabase/Online database
   ```

---

## 📞 Still Not Working?

Check these in order:

1. **Run SQL migration** on Supabase (if you haven't already):
   - Supabase Dashboard → SQL Editor
   - Paste and run all commands from `migrations.sql`

2. **Verify database exists**:
   ```bash
   psql postgresql://postgres:PASSWORD@addyskbgjhqmzrseqvnh.supabase.co:5432/postgres -c "SELECT version();"
   ```

3. **Check Render logs**:
   - Render Dashboard → Your Service → Logs
   - Look for exact error message

4. **Restart deployment**:
   - Render Dashboard → Manual Deploy → Deploy latest commit

---

## 📝 Render Environment Variables Summary

```
# Required
DATABASE_URL=postgresql://postgres:PASSWORD@addyskbgjhqmzrseqvnh.supabase.co:5432/postgres

# Optional (but recommended)
FLASK_ENV=production
SECRET_KEY=<generate-a-long-random-string>
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SENDER_EMAIL=<your-email@gmail.com>
SENDER_PASSWORD=<Gmail-App-Password>
SUPPORT_EMAIL=support@company.com
```

---

## ✨ After Fix

Once connected, your app will:
- ✅ Load login page
- ✅ Show company selector
- ✅ Access all features
- ✅ Log all activities
- ✅ Store data in Supabase

Good luck! 🎉
