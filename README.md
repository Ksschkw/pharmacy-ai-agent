# Pharmacy Module API

## Overview
A production-ready API for managing prescriptions in a pharmacy system.

## Setup
1. Install dependencies: `pip install -r requirements.txt`
2. Set environment variables in `.env`:
   - `MONGO_URI`: MongoDB connection string
   - `API_KEY`: OpenRouter API key
   - `LOG_LEVEL`: Logging level (e.g., INFO)
3. Place PaddleOCR models in `paddle_models/models/`.
4. Run: `uvicorn app.main:app --reload`

## Docker
Build and run: `docker build -t pharmacy-api . && docker run -p 8000:8000 -v $(pwd)/.env:/app/.env pharmacy-api`

## API Endpoints
- `POST /api/v1/prescriptions/upload`: Upload prescription image
- `POST /api/v1/prescriptions/manual`: Add manual prescription
- `GET /api/v1/prescriptions/{patient_id}`: Get prescriptions by patient