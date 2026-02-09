$env:DATABASE_URL = 'postgresql://neondb_owner:npg_c0RomSFYAfp2@ep-divine-firefly-ai2f81p5-pooler.c-4.us-east-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require'
cd 'c:\Users\maner\Downloads\SmartSlot\myenv\Smart-car-parking'
Write-Host "Verifying Neon data..." -ForegroundColor Cyan
python verify_neon.py
Write-Host ""
Write-Host "Done." -ForegroundColor Green
