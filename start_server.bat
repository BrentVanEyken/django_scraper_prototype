@echo off

:: Open the first command prompt for Django
start cmd /k "cd django_scraper_prototype && venv\scripts\activate && cd myproject && python manage.py runserver"

:: Open the second command prompt for FastAPI
start cmd /k "cd fastAPI_scraper && venv\scripts\activate && uvicorn app.main:app --reload --port 8001"
