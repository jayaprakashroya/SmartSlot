# Deploying SmartSlot to Render

This guide explains how to deploy the SmartSlot application to Render.

## Prerequisites

- GitHub account with the SmartSlot repository
- Render account (free at https://render.com)

## Step 1: Sign Up on Render

1. Go to [render.com](https://render.com)
2. Sign up with GitHub (recommended for easier integration)
3. Connect your GitHub account to Render

## Step 2: Connect Your Repository

1. In Render dashboard, click "New +"
2. Select "Web Service"
3. Connect your GitHub repository `jayaprakashroya/SmartSlot`
4. Select the repository and choose the `main` branch

## Step 3: Configure the Service

### Basic Settings
- **Name**: `smartslot` (or your preferred name)
- **Runtime**: Python
- **Build Command**: 
  ```
  pip install --upgrade pip && pip install -r Requirements.txt && python manage.py collectstatic --noinput
  ```
- **Start Command**:
  ```
  gunicorn ParkingProject.wsgi:application --bind 0.0.0.0:$PORT
  ```
- **Instance Type**: Free (for testing) or Starter ($7/month for production)

### Environment Variables

Set these in Render dashboard:

```
DEBUG=false
SECRET_KEY=<generate-a-random-secret-key>
ALLOWED_HOSTS=smartslot.onrender.com,localhost
DATABASE_URL=<PostgreSQL URL from Render Database>
```

#### Generate Secret Key

Run this locally and copy the output:
```python
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

## Step 4: Create a PostgreSQL Database

1. In Render dashboard, click "New +"
2. Select "PostgreSQL"
3. Configure:
   - **Name**: `smartslot-db`
   - **Database**: `smartslot`
   - **User**: `smartslot`
   - **Region**: Choose closest to your users
   - **Instance Type**: Free (for testing)

4. After creation, copy the **Internal Database URL**
5. Add it as `DATABASE_URL` environment variable to your web service

## Step 5: Update Django Settings

Modify `ParkingProject/settings.py` for production:

```python
import os
from pathlib import Path
import dj_database_url

# SECURITY SETTINGS
DEBUG = os.getenv('DEBUG', 'False') == 'True'
SECRET_KEY = os.getenv('SECRET_KEY', 'change-me-in-production')
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', 'localhost').split(',')

# Database
if os.getenv('DATABASE_URL'):
    DATABASES = {
        'default': dj_database_url.config(
            default=os.getenv('DATABASE_URL'),
            conn_max_age=600
        )
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

# HTTPS & Security (for production)
if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_SECURITY_POLICY = {
        "default-src": ("'self'",),
    }

# Static Files
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'

# Media Files (Optional: use S3 for production)
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'
```

## Step 6: Update requirements.txt

Add these to your `Requirements.txt`:

```
gunicorn==21.2.0
dj-database-url==2.1.0
whitenoise==6.6.0
psycopg2-binary==2.9.9
```

Install locally first:
```bash
pip install -r Requirements.txt
```

## Step 7: Run Migrations

Before first deployment, you'll need to run migrations. You can do this:

### Option A: Via Render Shell
1. Go to Render Web Service
2. Click "Shell" at the top
3. Run:
   ```bash
   python manage.py migrate
   python manage.py createsuperuser
   ```

### Option B: Add Migration Hook to render.yaml
Already included in the provided `render.yaml`

## Step 8: Deploy

1. Push your changes to GitHub:
```bash
git add .
git commit -m "Add Render deployment configuration"
git push origin main
```

2. Render automatically deploys on push
3. Check the **Logs** tab in Render for build progress
4. Once deployed, your app is live at `https://smartslot.onrender.com`

## Step 9: Configure Your Domain (Optional)

1. In Render Web Service settings, go to **Custom Domain**
2. Add your domain
3. Update DNS records as shown in Render

## Troubleshooting

### Build Fails
- Check **Build Logs** in Render
- Ensure all dependencies are in `Requirements.txt`
- Verify `ParkingProject/settings.py` handles missing environment variables

### Database Connection Error
- Verify `DATABASE_URL` is set correctly
- Check PostgreSQL database is running
- Run migrations: Access Render Shell and run `python manage.py migrate`

### 500 Internal Server Error
- Check **Service Logs** in Render
- Verify `ALLOWED_HOSTS` includes your Render domain
- Ensure `DEBUG=False` and `SECRET_KEY` is properly set

### Static Files Not Loading
- Run `python manage.py collectstatic` during build (already in build command)
- Check STATIC_ROOT path in settings

## Monitoring

1. **Logs**: View real-time logs in Render dashboard
2. **Metrics**: Check CPU, Memory, and Disk usage
3. **Alerts**: Set up email notifications for service issues

## Cost Estimation

- **Free Tier**: Limited memory, spins down after inactivity
- **Starter Plan**: $7/month for web service
- **PostgreSQL Database**: $15/month (free tier available)
- **Total**: ~$22/month for production setup

## Next Steps

1. Upload YOLOv8 models to cloud storage (S3/Azure)
2. Configure email for notifications
3. Set up domain name
4. Monitor performance and optimize

## Useful Commands

```bash
# Test locally with production settings
DEBUG=False python manage.py runserver

# Collect static files
python manage.py collectstatic --noinput

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser
```

## Additional Resources

- [Render Django Documentation](https://render.com/docs/deploy-django)
- [Django Deployment Checklist](https://docs.djangoproject.com/en/stable/howto/deployment/checklist/)
- [Render Environment Variables](https://render.com/docs/environment-variables)

---

For more help, visit [Render Support](https://support.render.com)
