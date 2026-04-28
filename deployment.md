# Deployment Guide

## Overview

This Django backend can be deployed to various platforms. Here are the most common options.

---

## 1. Heroku Deployment

### Prerequisites
- Heroku CLI installed
- Heroku account
- PostgreSQL database on Heroku

### Steps

1. **Create Heroku App**
   ```bash
   heroku create your-clinic-app
   ```

2. **Add PostgreSQL Add-on**
   ```bash
   heroku addons:create heroku-postgresql:hobby-dev
   ```

3. **Create Procfile** (in backend directory)
   ```
   web: gunicorn config.wsgi --log-file -
   release: python manage.py migrate
   ```

4. **Create runtime.txt**
   ```
   python-3.11.7
   ```

5. **Update requirements.txt**
   ```bash
   pip install gunicorn whitenoise psycopg2-binary
   pip freeze > requirements.txt
   ```

6. **Update settings.py** for production
   ```python
   # Add whitenoise for static files
   MIDDLEWARE = [
       'whitenoise.middleware.WhiteNoiseMiddleware',
       # ... other middleware
   ]
   
   # Database from Heroku
   import dj_database_url
   DATABASES = {
       'default': dj_database_url.config(
           default='sqlite:///db.sqlite3',
           conn_max_age=600
       )
   }
   ```

7. **Set environment variables**
   ```bash
   heroku config:set SECRET_KEY=your-secret-key
   heroku config:set DEBUG=False
   heroku config:set ALLOWED_HOSTS=your-clinic-app.herokuapp.com
   heroku config:set CORS_ALLOWED_ORIGINS=https://your-frontend.herokuapp.com
   ```

8. **Deploy**
   ```bash
   git push heroku main
   ```

9. **Run migrations**
   ```bash
   heroku run python manage.py migrate
   heroku run python manage.py createsuperuser
   ```

10. **View logs**
    ```bash
    heroku logs --tail
    ```

---

## 2. AWS EC2 Deployment

### Prerequisites
- AWS account
- EC2 instance running Ubuntu 22.04
- Elastic IP (optional)
- RDS MySQL database

### Steps

1. **Connect to EC2 instance**
   ```bash
   ssh -i your-key.pem ubuntu@your-instance-ip
   ```

2. **Install dependencies**
   ```bash
   sudo apt update
   sudo apt install python3-pip python3-venv python3-dev
   sudo apt install mysql-client libmysqlclient-dev
   sudo apt install supervisor nginx
   ```

3. **Clone project**
   ```bash
   cd /home/ubuntu
   git clone your-repo.git
   cd backend
   ```

4. **Setup virtual environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   pip install gunicorn
   ```

5. **Configure .env**
   ```bash
   cp .env.example .env
   nano .env
   # Add your RDS database credentials
   ```

6. **Run migrations**
   ```bash
   python manage.py migrate
   python manage.py createsuperuser
   python manage.py collectstatic --noinput
   ```

7. **Setup Supervisor** (auto-restart)
   ```bash
   sudo nano /etc/supervisor/conf.d/clinic.conf
   ```
   
   Add:
   ```ini
   [program:clinic]
   directory=/home/ubuntu/backend
   command=/home/ubuntu/backend/venv/bin/gunicorn config.wsgi:application --bind 127.0.0.1:8000
   autostart=true
   autorestart=true
   stderr_logfile=/var/log/clinic.err.log
   stdout_logfile=/var/log/clinic.out.log
   user=ubuntu
   ```

   Then:
   ```bash
   sudo supervisorctl reread
   sudo supervisorctl update
   sudo supervisorctl start clinic
   ```

8. **Setup Nginx**
   ```bash
   sudo nano /etc/nginx/sites-available/clinic
   ```
   
   Add:
   ```nginx
   server {
       listen 80;
       server_name your-domain.com;

       location / {
           proxy_pass http://127.0.0.1:8000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
       }

       location /media/ {
           alias /home/ubuntu/backend/media/;
       }

       location /static/ {
           alias /home/ubuntu/backend/static/;
       }
   }
   ```

   Then:
   ```bash
   sudo ln -s /etc/nginx/sites-available/clinic /etc/nginx/sites-enabled/
   sudo systemctl restart nginx
   ```

9. **Setup SSL (Let's Encrypt)**
   ```bash
   sudo apt install certbot python3-certbot-nginx
   sudo certbot --nginx -d your-domain.com
   ```

---

## 3. DigitalOcean App Platform

### Steps

1. **Create App.yaml** (in backend directory)
   ```yaml
   name: clinic-backend
   
   services:
   - name: api
     github:
       repo: your-username/your-repo
       branch: main
     build_command: pip install -r requirements.txt && python manage.py migrate
     run_command: gunicorn config.wsgi:application --bind 0.0.0.0:8080
     envs:
     - key: DEBUG
       value: "False"
     - key: SECRET_KEY
       scope: RUN_AND_BUILD_TIME
     - key: DATABASE_URL
       scope: RUN_AND_BUILD_TIME
       value: ${db.connection_string}
     http_port: 8080
     
   databases:
   - name: db
     engine: MYSQL
     version: "8"
   ```

2. **Push to GitHub**
   ```bash
   git add .
   git commit -m "Add DigitalOcean deployment config"
   git push origin main
   ```

3. **Deploy via DigitalOcean Console**
   - Go to DigitalOcean > Apps
   - Click "Create App"
   - Select GitHub repository
   - Review `app.yaml`
   - Click Deploy

---

## 4. Docker Deployment

### Create Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    libmysqlclient-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN python manage.py collectstatic --noinput

EXPOSE 8000

CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000"]
```

### Create docker-compose.yml

```yaml
version: '3.8'

services:
  db:
    image: mysql:8.0
    environment:
      MYSQL_DATABASE: clinic_db
      MYSQL_ROOT_PASSWORD: root_password
    volumes:
      - db_data:/var/lib/mysql

  web:
    build: .
    command: >
      sh -c "python manage.py migrate &&
             python manage.py runserver 0.0.0.0:8000"
    environment:
      DEBUG: "False"
      SECRET_KEY: "your-secret-key"
      DB_NAME: clinic_db
      DB_USER: root
      DB_PASSWORD: root_password
      DB_HOST: db
      DB_PORT: 3306
    ports:
      - "8000:8000"
    depends_on:
      - db

volumes:
  db_data:
```

### Run with Docker

```bash
docker-compose up -d
docker-compose run web python manage.py createsuperuser
```

---

## Production Settings

### Update settings.py

```python
import os
from decouple import config

# Security
SECRET_KEY = config('SECRET_KEY')
DEBUG = config('DEBUG', default=False, cast=bool)
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost', cast=Csv())

# HTTPS
if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_SECURITY_POLICY = {
        'default-src': ("'self'",),
    }

# Database connection pooling
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'CONN_MAX_AGE': 600,
        # ... other settings
    }
}

# Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': '/var/log/django/clinic.log',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}
```

---

## Monitoring & Maintenance

### Set up monitoring

```bash
# Install monitoring tools
pip install sentry-sdk django-health-check

# Add to INSTALLED_APPS in settings.py
INSTALLED_APPS += [
    'health_check',
]
```

### Backup database

```bash
# MySQL backup
mysqldump -u root -p clinic_db > backup_$(date +%Y%m%d).sql

# Upload to S3
aws s3 cp backup_$(date +%Y%m%d).sql s3://your-bucket/backups/
```

### Monitor logs

```bash
# Heroku
heroku logs --tail

# EC2
tail -f /var/log/clinic.out.log

# Docker
docker-compose logs -f web
```

---

## Domain Configuration

### Point domain to your app

**For Heroku:**
```bash
# Add custom domain
heroku domains:add your-domain.com

# Update DNS CNAME record
your-domain.com CNAME your-clinic-app.herokuapp.com
```

**For AWS/DigitalOcean:**
```
# Update A record to point to your server IP
@ A your-server-ip
www CNAME your-domain.com
```

---

## SSL Certificate

### Let's Encrypt (Free)

```bash
# Using certbot
sudo certbot certonly --standalone -d your-domain.com

# Files created:
# /etc/letsencrypt/live/your-domain.com/fullchain.pem
# /etc/letsencrypt/live/your-domain.com/privkey.pem

# Auto-renewal
sudo systemctl enable certbot.timer
sudo systemctl start certbot.timer
```

---

## Environment Variables for Production

```env
# Django
SECRET_KEY=generate-a-secure-random-key-here
DEBUG=False
ALLOWED_HOSTS=your-domain.com,www.your-domain.com

# Database
DB_ENGINE=django.db.backends.mysql
DB_NAME=clinic_db
DB_USER=clinic_user
DB_PASSWORD=secure-password-here
DB_HOST=your-rds-endpoint.rds.amazonaws.com
DB_PORT=3306

# CORS
CORS_ALLOWED_ORIGINS=https://your-frontend-domain.com

# Email (optional, for notifications)
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password

# Sentry (error tracking)
SENTRY_DSN=your-sentry-dsn-here
```

---

## Health Checks

### Add health check endpoint

```python
# In clinic/urls.py
from django.urls import path
from django.views.generic import TemplateView

urlpatterns = [
    path('health/', lambda request: JsonResponse({'status': 'ok'})),
]
```

---

## Performance Optimization

1. **Enable caching**
   ```python
   CACHES = {
       'default': {
           'BACKEND': 'django.core.cache.backends.redis.RedisCache',
           'LOCATION': 'redis://127.0.0.1:6379/1',
       }
   }
   ```

2. **Use CDN for static files** (AWS CloudFront, Cloudflare)

3. **Database indexing** - Already configured in models

4. **Connection pooling** - Use MySQL connection pool

5. **API rate limiting**
   ```python
   REST_FRAMEWORK = {
       'DEFAULT_THROTTLE_CLASSES': [
           'rest_framework.throttling.AnonRateThrottle',
           'rest_framework.throttling.UserRateThrottle'
       ],
       'DEFAULT_THROTTLE_RATES': {
           'anon': '100/hour',
           'user': '1000/hour'
       }
   }
   ```

---

## Troubleshooting

### 502 Bad Gateway (Nginx)
```bash
# Check Gunicorn is running
sudo supervisorctl status clinic

# Check Gunicorn logs
tail -f /var/log/clinic.out.log
```

### Database connection errors
```bash
# Test MySQL connection
mysql -u clinic_user -p -h your-rds-endpoint.rds.amazonaws.com -D clinic_db

# Check environment variables
echo $DB_HOST
```

### Static files not loading
```bash
# Collect static files
python manage.py collectstatic --noinput

# Verify permissions
ls -la static/
```

---

## Rollback Strategy

Keep previous version available:

```bash
# Heroku
heroku releases
heroku releases:rollback

# Manual backup
git tag v1.0.0
git push --tags
```

---

## Support

- Check deployment logs first
- Review Django security documentation
- Test locally before production deployment
- Use staging environment for testing

Happy deploying! 🚀
