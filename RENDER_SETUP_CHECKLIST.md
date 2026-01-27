# Complete Render Deployment Configuration Guide

## Step 1: Generate Secret Key (Do This First!)

Open your terminal and run:
```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

**Copy the output** - you'll need this for the SECRET_KEY field.

Example output:
```
t-zx*v$9@*@8qf#6h#j9z#n-cz#-f2q9z#n-cz#-f2q9z#n-cz
```

---

## Step 2: Fill in Render Form

### A. Basic Service Settings

| Field | Value |
|-------|-------|
| **Name** | `SmartSlot` |
| **Project** | Leave as `Select a project...` (optional) |
| **Language** | `Python 3` |
| **Branch** | `main` |
| **Region** | `Oregon (US West)` |
| **Root Directory** | Leave empty |

### B. Build & Start Commands

**Build Command** (already filled, but confirm):
```
pip install --upgrade pip && pip install -r Requirements.txt && python manage.py collectstatic --noinput
```

**Start Command** (already filled, but confirm):
```
gunicorn ParkingProject.wsgi:application --bind 0.0.0.0:$PORT
```

### C. Instance Type

For testing:
- ✅ Select **Free** ($0/month) - Good for initial testing
- After testing, upgrade to **Starter** ($7/month) for production

---

## Step 3: Environment Variables (IMPORTANT!)

Click **"Add Environment Variable"** for **EACH** of these:

### Variable 1: DEBUG
```
NAME: DEBUG
VALUE: false
```

### Variable 2: SECRET_KEY
```
NAME: SECRET_KEY
VALUE: [PASTE YOUR GENERATED KEY HERE]
```

Example (use YOUR generated key):
```
NAME: SECRET_KEY
VALUE: t-zx*v$9@*@8qf#6h#j9z#n-cz#-f2q9z#n-cz#-f2q9z#n-cz
```

### Variable 3: ALLOWED_HOSTS
```
NAME: ALLOWED_HOSTS
VALUE: smartslot.onrender.com,localhost,127.0.0.1
```

### Variable 4: DATABASE_URL
```
NAME: DATABASE_URL
VALUE: [YOU'LL ADD THIS AFTER CREATING DATABASE]
```

**Leave this blank for now** - Add after creating PostgreSQL database

### Variable 5: PYTHON_VERSION (Optional)
```
NAME: PYTHON_VERSION
VALUE: 3.10.0
```

---

## Step 4: Quick Checklist Before Clicking "Deploy"

- ✅ Name: `SmartSlot`
- ✅ Language: `Python 3`
- ✅ Branch: `main`
- ✅ Region: `Oregon (US West)`
- ✅ Build Command: Shows pip install & collectstatic
- ✅ Start Command: Shows gunicorn command
- ✅ Instance Type: Select `Free` or `Starter`
- ✅ Environment Variables Added:
  - ✅ DEBUG = false
  - ✅ SECRET_KEY = [your generated key]
  - ✅ ALLOWED_HOSTS = smartslot.onrender.com,localhost,127.0.0.1
  - ✅ PYTHON_VERSION = 3.10.0
  - ⏳ DATABASE_URL = [add after database creation]

---

## Step 5: Click "Deploy Web Service"

Wait 2-3 minutes for deployment to complete.

You should see:
- ✅ Build log showing successful pip install
- ✅ Service shows "Live" status
- ✅ You get a URL: `https://smartslot.onrender.com`

---

## Step 6: Create PostgreSQL Database

1. Go back to **Render Dashboard**
2. Click **"New +"** button
3. Select **"PostgreSQL"**

Fill in:

| Field | Value |
|-------|-------|
| **Name** | `smartslot-db` |
| **Database** | `smartslot` |
| **User** | `smartslot` |
| **Region** | `Oregon (US West)` |
| **PostgreSQL Version** | Latest (default) |
| **Instance Type** | `Free` or `Starter` |

4. Click **"Create Database"**
5. Wait 1-2 minutes for database creation

---

## Step 7: Get Database Connection URL

After database is created:

1. Open the `smartslot-db` service
2. Look for **"Internal Database URL"**
3. It looks like:
```
postgresql://smartslot:[password]@[host]:5432/smartslot
```

**Copy this entire URL**

---

## Step 8: Add DATABASE_URL to SmartSlot Service

1. Go back to **SmartSlot** web service
2. Click **"Environment"** tab
3. Click **"Add Environment Variable"**

```
NAME: DATABASE_URL
VALUE: [PASTE THE INTERNAL DATABASE URL HERE]
```

Example:
```
NAME: DATABASE_URL
VALUE: postgresql://smartslot:abc123@dpg-xyz.oregon-postgres.render.com:5432/smartslot
```

---

## Step 9: Redeploy Service

1. On SmartSlot service page, look for the **3-dot menu** (top right)
2. Click it and select **"Reboot"**
3. Wait for service to restart (2-3 minutes)

Check logs - you should see:
```
Running migrations...
Successfully migrated!
Gunicorn started on port [PORT]
```

---

## Step 10: Create Admin User

1. On SmartSlot service page
2. Click **"Shell"** tab at the top
3. Run these commands:

```bash
python manage.py migrate
```

Then create admin account:
```bash
python manage.py createsuperuser
```

When prompted, enter:
- **Username**: `admin` (or your choice)
- **Email**: `your-email@example.com`
- **Password**: Create a strong password (you'll need this to login)

---

## Step 11: Access Your App

Your app is now live at:
```
https://smartslot.onrender.com
```

### Admin Login
```
URL: https://smartslot.onrender.com/admin/
Username: admin
Password: [password you created]
```

### Main App
```
https://smartslot.onrender.com/
```

---

## Troubleshooting Checklist

### If deployment fails:

1. **Check Build Logs** (Logs tab)
   - Look for errors in pip install
   - Check if all packages installed successfully

2. **Check for Missing Environment Variables**
   - All 4 main variables must be set
   - No typos in variable names

3. **Database Connection Error**
   - Confirm DATABASE_URL is set correctly
   - Verify database service is running
   - Check service logs

### If you see "Application Error":

1. Run `python manage.py migrate` in Shell again
2. Restart the service (Reboot button)
3. Check service logs for specific errors

### If static files not showing:

```bash
# In Shell, run:
python manage.py collectstatic --noinput
```

Then reboot service.

---

## Environment Variables Summary

```
DEBUG=false
SECRET_KEY=<your-generated-secret-key>
ALLOWED_HOSTS=smartslot.onrender.com,localhost,127.0.0.1
DATABASE_URL=postgresql://smartslot:<password>@<host>:5432/smartslot
PYTHON_VERSION=3.10.0
```

---

## Cost Breakdown

| Service | Free Tier | Starter Tier |
|---------|-----------|-------------|
| Web Service | $0/month | $7/month |
| PostgreSQL DB | $15/month | $15/month |
| **Total** | **$15/month** | **$22/month** |

**Free tier note**: Services spin down after 15 minutes of inactivity. Starter tier ($7/month) keeps services always running.

---

## Important Notes

⚠️ **Never commit `.env` file to GitHub** - Use `.env.example` instead

⚠️ **Change default SECRET_KEY in production** - You did this above ✅

⚠️ **Use strong admin password** - This protects your system

⚠️ **Keep DATABASE_URL private** - Don't share this URL

⚠️ **Set DEBUG=false in production** - Important for security

---

## Next Steps (After Deployment)

1. Test the application at `https://smartslot.onrender.com`
2. Login to admin panel
3. Add parking lot configuration
4. Test vehicle detection features
5. Configure email notifications (optional)
6. Set up custom domain (optional)

---

## Getting Help

If you get stuck:

1. Check [RENDER_DEPLOYMENT.md](RENDER_DEPLOYMENT.md) in the repository
2. View Service Logs in Render dashboard
3. Check Django error messages
4. See [Render Documentation](https://render.com/docs)

---

**You're all set! Your SmartSlot parking system will be live shortly! 🚀**
