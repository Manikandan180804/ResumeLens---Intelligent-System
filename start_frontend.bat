@echo off
echo Starting Modern Web Frontend...
echo Open browser at: http://localhost:8501
echo.
cd frontend
python -m http.server 8501
