# Technical Architecture Documentation

## System Overview

The Pharmacy AI Agent is built on a modern microservices-inspired architecture with clear separation of concerns across routing, business logic, and data layers.

## Component Architecture

### 1. API Layer (FastAPI)

**Entry Point**: `app/main.py`

The FastAPI application serves as the orchestration layer, handling:
- HTTP request routing
- Dependency injection
- Background task scheduling
- Logging configuration
- CORS and middleware

**Routers** (`app/routers/`):
- `prescriptions.py`: Prescription upload, manual entry, retrieval
- `inventory.py`: Stock management, forecasting, reporting
- `auth.py`: Authentication endpoints

### 2. Service Layer

**OCR Service** (`app/services/ocr_service.py`):
- Initializes PaddleOCR with custom model paths
- Processes prescription images using computer vision
- Extracts raw text from images
- Integrates with AI service for parsing

**AI Service** (`app/services/ai_service.py`):
- Connects to OpenRouter API for LLM access
- Implements fallback strategy across multiple models (DeepSeek, Mistral)
- Structures prescription text into JSON schema
- Handles OCR error correction (character swaps, spacing issues)

**Database Service** (`app/services/database.py`):
- MongoDB connection management
- Connection pooling
- Database instance provider

**Forecasting Service** (`app/services/forecasting.py`):
- Calculates rolling daily usage rates
- Predicts 7-day and 30-day demand
- Generates reorder alerts (URGENT, LOW STOCK, STABLE)
- Creates human-readable reports

**Auth Service** (`app/services/auth.py`):
- JWT token generation and validation
- Password hashing and verification
- Token expiration management

### 3. Data Models

**Pydantic Models** (`app/models/`):
- `prescription.py`: Prescription schema with nested medication objects
- `inventory.py`: Inventory item with forecasting fields
- `patient.py`: Patient records with prescription references
- `pharmacy.py`: Multi-tenant pharmacy entities

## Data Flow Diagrams

### Prescription Upload Flow

```
┌─────────┐
│ Client  │
└────┬────┘
     │ POST /prescriptions/upload
     │ (image + metadata)
     ▼
┌─────────────────────┐
│ Prescriptions Router│
│ - Validate input    │
│ - Save image file   │
│ - Queue background  │
│   task              │
└────┬────────────────┘
     │ Returns immediately
     │ {"status": "processing"}
     ▼
┌──────────────────────┐
│ Background Task      │
│ process_ocr()        │
└────┬─────────────────┘
     │
     ▼
┌──────────────────────┐
│ OCR Service          │
│ - Load image (cv2)   │
│ - Run PaddleOCR      │
│ - Extract text       │
└────┬─────────────────┘
     │ Raw OCR text
     ▼
┌──────────────────────┐
│ AI Service           │
│ - Send to LLM API    │
│ - Parse JSON response│
│ - Validate schema    │
└────┬─────────────────┘
     │ Structured JSON
     ▼
┌──────────────────────┐
│ MongoDB              │
│ - Insert prescription│
│ - Update patient     │
│   record             │
└──────────────────────┘
```

### Inventory Forecasting Flow

```
┌─────────┐
│ Client  │
└────┬────┘
     │ POST /inventory/report
     ▼
┌─────────────────────┐
│ Inventory Router    │
│ - Queue background  │
│   task              │
└────┬────────────────┘
     │
     ▼
┌──────────────────────┐
│ Forecasting Service  │
│ generate_forecast_   │
│ report()             │
└────┬─────────────────┘
     │
     ▼
┌──────────────────────┐
│ For each item:       │
│ 1. Get usage_rate    │
│ 2. Calculate days to │
│    reorder           │
│ 3. Predict 7d/30d    │
│    demand            │
│ 4. Generate alert    │
└────┬─────────────────┘
     │
     ▼
┌──────────────────────┐
│ MongoDB              │
│ - Update inventory   │
│   forecast fields    │
│ - Insert report doc  │
└──────────────────────┘
```

## Database Schema

### Collections

#### `prescriptions`
```json
{
  "_id": ObjectId,
  "patient_id": "string",
  "physician_id": "string",
  "prescription_number": "string",
  "priority": "string",
  "notes": "string",
  "ocr_raw": "string",
  "parsed_data": {
    "medications": [
      {
        "name": "string",
        "dosage": "string",
        "frequency": "string"
      }
    ],
    "doctor": "string",
    "date_issued": "YYYY-MM-DD",
    "patient_name": "string"
  },
  "image_path": "string",
  "pharmacy_id": "string",
  "source": "file|manual",
  "created_at": ISODate
}
```

#### `inventory`
```json
{
  "_id": ObjectId,
  "name": "string",
  "description": "string",
  "quantity": "number",
  "unit_cost": "number",
  "selling_price": "number",
  "batch_number": "string",
  "expiration_date": ISODate,
  "storage_location": "string",
  "reorder_level": "number",
  "daily_usage_rate": "number",
  "pharmacy_id": "string",
  "forecast": {
    "usage_rate": "number",
    "days_until_reorder": "number",
    "predicted_demand_7d": "number",
    "predicted_demand_30d": "number",
    "last_forecast_date": ISODate
  },
  "created_at": ISODate
}
```

#### `patients`
```json
{
  "_id": ObjectId,
  "patient_id": "string",
  "pharmacy_id": "string",
  "prescription_ids": ["ObjectId", "ObjectId"]
}
```

#### `pharmacies`
```json
{
  "_id": ObjectId,
  "pharmacy_id": "string",
  "password_hash": "string",
  "name": "string",
  "created_at": ISODate
}
```

#### `reports`
```json
{
  "_id": ObjectId,
  "pharmacy_id": "string",
  "type": "demand_forecast",
  "summary": "string (multi-line report)",
  "created_at": ISODate
}
```

## Multi-Tenancy Implementation

### Strategy: Pharmacy-Level Isolation

All data is scoped by `pharmacy_id` to ensure complete tenant isolation:

1. **Authentication**: Login returns JWT with embedded `pharmacy_id`
2. **Dependency Injection**: `get_current_pharmacy_id()` extracts tenant from request
3. **Query Filtering**: All database queries include `pharmacy_id` filter
4. **Data Validation**: Endpoints verify pharmacy ownership before mutations

### Security Considerations

- JWT tokens expire after configured duration
- Passwords hashed using bcrypt (via passlib)
- API keys stored in environment variables only
- File uploads scoped to prevent path traversal

## Forecasting Algorithm

### Usage Rate Calculation

The system uses an **exponential moving average** to smooth usage patterns:

```python
new_usage_rate = (old_usage_rate * 0.7) + (recent_usage / 7 * 0.3)
```

This gives 70% weight to historical data and 30% to recent activity.

### Demand Prediction

```python
predicted_demand_7d = daily_usage_rate * 7
predicted_demand_30d = daily_usage_rate * 30
days_until_reorder = (current_stock - reorder_level) / daily_usage_rate
```

### Alert Thresholds

- **URGENT REORDER**: < 3 days until reorder level
- **LOW STOCK ALERT**: < 7 days until reorder level
- **STABLE**: ≥ 7 days of stock remaining

## Technology Decisions

### Why PaddleOCR?

- **Accuracy**: State-of-the-art text detection and recognition
- **Offline Capability**: Models run locally (no API costs)
- **Medical Text**: Handles handwritten and printed prescriptions
- **Customizable**: Supports custom model fine-tuning

### Why OpenRouter?

- **Model Diversity**: Access to multiple LLMs (DeepSeek, Mistral, etc.)
- **Fallback Strategy**: Automatic retry with different models
- **Cost Efficiency**: Free tier available for development
- **Structured Output**: Reliable JSON parsing

### Why MongoDB?

- **Schema Flexibility**: Prescription data varies significantly
- **Nested Documents**: Natural fit for medication arrays
- **Scalability**: Horizontal scaling for multi-tenant growth
- **Aggregation**: Powerful analytics for forecasting

### Why FastAPI?

- **Performance**: Async support for concurrent requests
- **Type Safety**: Pydantic integration for validation
- **Auto Documentation**: Swagger UI out-of-the-box
- **Modern Python**: Leverages type hints and async/await

## Performance Considerations

### Async Processing

OCR operations are CPU-intensive and run in background tasks to prevent blocking:

```python
background_tasks.add_task(process_ocr, file_path, prescription_data)
```

### Connection Pooling

MongoDB connections are reused via singleton pattern in `database.py`.

### Image Storage

Uploaded images stored in `static/uploads/` with patient-scoped naming to prevent collisions.

## Deployment Recommendations

### Production Checklist

- [ ] Use production MongoDB instance (Atlas recommended)
- [ ] Configure reverse proxy (Nginx) for static file serving
- [ ] Enable HTTPS with SSL certificates
- [ ] Set up log aggregation (ELK stack or CloudWatch)
- [ ] Implement rate limiting on API endpoints
- [ ] Configure CORS for specific frontend domains
- [ ] Use environment-specific `.env` files
- [ ] Set up automated backups for MongoDB
- [ ] Monitor API performance with APM tools
- [ ] Implement health check endpoints

### Scaling Strategy

1. **Horizontal Scaling**: Run multiple FastAPI instances behind load balancer
2. **Database Sharding**: Shard MongoDB by `pharmacy_id` for large deployments
3. **Caching Layer**: Add Redis for frequently accessed prescriptions
4. **CDN**: Serve static prescription images via CDN
5. **Queue System**: Replace background tasks with Celery + RabbitMQ for distributed processing

## Error Handling

### OCR Failures

- Invalid image formats → HTTP 500 with error detail
- OCR extraction errors → Stored with `{"error": "..."}` in `parsed_data`
- LLM API failures → Fallback to multiple models, return raw text if all fail

### Database Errors

- Connection failures → Logged and returned as HTTP 500
- Duplicate keys → Handled with appropriate HTTP 409 responses
- Query timeouts → Configurable timeout limits

## Logging Strategy

### Log Levels

- **INFO**: Successful operations, startup events
- **WARNING**: Fallback model usage, missing optional fields
- **ERROR**: OCR failures, API errors, database issues

### Log Files

- `pharmacy.log`: Rotating file handler (1MB max, 5 backups)
- Structured format: `%(asctime)s - %(name)s - %(levelname)s - %(message)s`

## Future Architecture Improvements

1. **Event-Driven Architecture**: Implement message queue for prescription processing
2. **Microservices Split**: Separate OCR service into standalone container
3. **GraphQL API**: Add GraphQL layer for flexible frontend queries
4. **Real-time Updates**: WebSocket support for live inventory alerts
5. **Caching**: Redis integration for session management and query caching
6. **API Versioning**: Implement versioned endpoints for backward compatibility
