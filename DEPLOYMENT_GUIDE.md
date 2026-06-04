# SmartSlot - Deployment Guide (Online Hosting)

This guide will help you deploy your Django Smart Car Parking System online with multiple hosting options.

## 🚀 Quick Deployment Options

### Option 1: **Render** (RECOMMENDED - Free Tier Available)
Best for: Quick deployment, free tier, automatic HTTPS

### Option 2: **Railway**
Best for: Easy deployment, good performance, pay-as-you-go

### Option 3: **PythonAnywhere**
Best for: Python-focused hosting, beginner-friendly

### Option 4: **AWS/DigitalOcean**
Best for: Production-grade, scalable, full control

---

## 📋 Pre-Deployment Checklist

### 1. Update Requirements.txt
Ensure all dependencies are listed (add missing for production):

```bash
cd c:\Users\maner\Downloads\SmartSlot\myenv\Smart-car-parking
pip freeze > Requirements.txt
```

Add these to Requirements.txt:
```
gunicorn>=21.0.0
whitenoise>=6.4.0
dj-database-url>=1.3.0
psycopg2-binary>=2.9.0
python-decouple>=3.8
```

### 2. Create .env File (for production)
```bash
# Create in project root
DEBUG=False
SECRET_KEY=your-secret-key-here-change-this
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
DATABASE_URL=postgresql://user:password@host:5432/dbname
ENABLE_YOLOV8=true
```

### 3. Create Procfile (for Render/Heroku)
```
Release: python manage.py migrate
Web: gunicorn ParkingProject.wsgi:application --bind 0.0.0.0:$PORT
```

### 4. Create runtime.txt
```
python-3.10.9
```

### 5. Update settings.py (already mostly done, verify)
```python
DEBUG = os.getenv('DEBUG', 'False') == 'True'
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', 'localhost').split(',')
```

---

## 🔧 OPTION 1: Deploy on RENDER (Easiest - Recommended)

### Step 1: Prepare Your Code
```bash
# 1. Add/update files needed for Render
# - requirements.txt (updated)
# - Procfile (created)
# - runtime.txt (created)
# - .gitignore

# 2. Create .gitignore
echo "*.pyc
__pycache__/
*.egg-info/
.env
*.sqlite3
db.sqlite3
media/
staticfiles/
.venv/
myenv/" > .gitignore

# 3. Initialize git if not already done
git init
git add .
git commit -m "Prepare for Render deployment"
```

### Step 2: Create GitHub Repository
```bash
# 1. Go to github.com and create new repo
# 2. Push your code
git remote add origin https://github.com/jayaprakashroya/smartslot.git
git branch -M main
git push -u origin main
```

### Step 3: Deploy on Render.com
1. Go to **https://render.com**
2. Sign up with GitHub
3. Click **"New +"** → **"Web Service"**
4. Connect your GitHub repo
5. Fill in settings:
   - **Name:** smartslot
   - **Region:** Choose closest to you
   - **Branch:** main
   - **Build Command:** `pip install -r requirements.txt && python manage.py collectstatic --noinput`
   - **Start Command:** `gunicorn ParkingProject.wsgi:application`

### Step 4: Add Environment Variables
In Render dashboard → Environment:
```
DEBUG=False
SECRET_KEY=django-insecure-[generate-new-long-random-string]
ALLOWED_HOSTS=yourapp.onrender.com
DATABASE_URL=postgresql://...
ENABLE_YOLOV8=false
```

### Step 5: Add PostgreSQL Database (Optional)
For production-grade DB:
1. Click **"New +"** → **"PostgreSQL"**
2. Connect to your Web Service
3. Render auto-fills DATABASE_URL

**Expected Result:** Your app at `yourapp.onrender.com` 🎉

---

## 🚂 OPTION 2: Deploy on RAILWAY

### Step 1: Install Railway CLI
```bash
npm install -g @railway/cli
# or use: winget install Railway.Railway
```

### Step 2: Connect Project
```bash
cd c:\Users\maner\Downloads\SmartSlot\myenv\Smart-car-parking
railway login
railway init
```

### Step 3: Add Services
```bash
railway add # Select Python, PostgreSQL
```

### Step 4: Configure
Edit `railway.json` or use Railway Dashboard to set:
- Start Command: `gunicorn ParkingProject.wsgi:application`
- Python Version: 3.10

### Step 5: Deploy
```bash
railway up
```

---

## 🐍 OPTION 3: Deploy on PYTHONANYWHERE

### Step 1: Sign Up
Go to **https://www.pythonanywhere.com** and create account

### Step 2: Upload Code
```bash
# Via Web UI: Upload ZIP file or use Git
# Or via command line:
git clone https://github.com/jayaprakashroya/smartslot.git
```

### Step 3: Create Web App
1. Dashboard → **"Web"** → **"Add new web app"**
2. Choose **"Python 3.10"**
3. Choose **"Django"**

### Step 4: Configure WSGI File
Edit `/var/www/jayaprakashroya_pythonanywhere_com_wsgi.py`:
```python
import os
import sys

path = '/home/jayaprakashroya/smartslot'
if path not in sys.path:
    sys.path.append(path)

os.environ['DJANGO_SETTINGS_MODULE'] = 'ParkingProject.settings'

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
```

### Step 5: Set Environment Variables
In PythonAnywhere → Web → Environment variables:
```
DEBUG=False
SECRET_KEY=your-secret-key
DATABASE_URL=mysql://user@host/dbname
```

### Step 6: Reload
Click **"Reload"** button

---

## ⚠️ Important: YOLOv8 Model Considerations

Since YOLOv8 is a large AI model, consider:

**Option A: Keep YOLOv8 Local**
```python
# In settings.py
ENABLE_YOLOV8 = os.getenv('ENABLE_YOLOV8', 'false') == 'true'
```

**Option B: Upload Model to Cloud Storage**
- Use AWS S3, Google Cloud Storage, or similar
- Reference in environment variables
- Download on startup

**Recommendation:** Start with Option A (YOLOV8 disabled online) for static dashboard

---

## 📊 Database Migration Commands

After deployment, run:

```bash
# Via Render/Railway/SSH:
python manage.py migrate
python manage.py createsuperuser
python manage.py collectstatic --noinput
```

---

## 🎯 Post-Deployment Checklist

- [ ] Update ALLOWED_HOSTS to your domain
- [ ] Generate new SECRET_KEY ([online generator](https://djecrety.ir/))
- [ ] Set DEBUG=False
- [ ] Create admin user: `python manage.py createsuperuser`
- [ ] Test login at yourapp.com/admin
- [ ] Test parking dashboard at yourapp.com/
- [ ] Set up SSL/HTTPS (auto on Render/Railway)
- [ ] Configure CORS if using API from different domain

---

## 🔒 Security Settings (Already in Your Code)

Your project already has:
- HTTPS enforced (if DEBUG=False)
- Secure cookies
- HSTS headers
- CSP headers
- WhiteNoise for static files

---

## 💡 Quick Start Commands

### Generate New Secret Key:
```python
from django.core.management.utils import get_random_secret_key
print(get_random_secret_key())
```

### Collect Static Files:
```bash
python manage.py collectstatic --noinput
```

### Create Superuser via CLI:
```bash
python manage.py createsuperuser
```

---

## 📱 Access Your Live App

After deployment, access:
- **Main App:** https://yourapp.com
- **Admin Panel:** https://yourapp.com/admin
- **API Endpoints:** https://yourapp.com/api/

---

## 🐛 Troubleshooting

### 500 Error on Deploy
```bash
# Check logs
render logs  # or Railway/PythonAnywhere dashboard
# Run locally: python manage.py runserver --insecure
```

### Database Connection Error
```bash
# Verify DATABASE_URL format
postgresql://user:password@host:5432/dbname
```

### Static Files Not Loading
```bash
# Run migration
python manage.py collectstatic --noinput
```

### Template Not Found
```bash
# Check TEMPLATES setting in settings.py
# Verify template directory paths
```

---

## 📞 Support & Docs

- **Django:** https://docs.djangoproject.com/
- **Render Docs:** https://render.com/docs
- **Railway Docs:** https://docs.railway.app/
- **PythonAnywhere Help:** https://help.pythonanywhere.com/

---

## ✅ Recommended Deployment Path

1. **Test Locally First** (Already done)
2. **Choose Platform:** Render (easiest) or Railway (most efficient)
3. **Push to GitHub** (if not already)
4. **Deploy:** Follow relevant section above
5. **Test Online:** Access your domain
6. **Monitor:** Check logs regularly

**Total Time:** 15-30 minutes ⏱️

---

## 🎉 Success!

Your SmartSlot system is now live online at your domain! 

Access credentials remain:
- Admin: `admin` / `Admin@12345`
- User: `user` / `User@12345`

(Change these after first login in production!)
