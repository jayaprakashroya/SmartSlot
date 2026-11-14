@echo off
REM Start SmartSlot with YOLOv8 enabled
cd c:\Users\maner\Downloads\SmartSlot\myenv\Smart-car-parking

echo.
echo ============================================================
echo Starting SmartSlot - Smart Car Parking System
echo ============================================================
echo.
echo Enabling YOLOv8 AI Detection...
set ENABLE_YOLOV8=true

echo.
echo Running migrations...
python manage.py migrate

echo.
echo ============================================================
echo LOGIN CREDENTIALS
echo ============================================================
echo.
echo Admin Account:
echo   Username: admin
echo   Password: Admin@12345
echo   Access: http://localhost:8000/admin/
echo.
echo Regular User Account:
echo   Username: user
echo   Password: User@12345
echo   Access: http://localhost:8000/
echo.
echo ============================================================
echo.
echo Starting Django Development Server...
echo Server will be available at: http://localhost:8000
echo.
python manage.py runserver 0.0.0.0:8000
