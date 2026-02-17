<div align="center">

# 🏥 Pharmacy AI Agent

### Intelligent Prescription Processing & Inventory Management System

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green.svg)](https://fastapi.tiangolo.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![MongoDB](https://img.shields.io/badge/MongoDB-4.4+-green.svg)](https://www.mongodb.com/)

**An AI-powered pharmacy management system that automates prescription processing using OCR and LLM technology, with intelligent inventory forecasting.**

[Features](#-features) • [Architecture](#-architecture) • [Installation](#-installation) • [API Documentation](#-api-documentation) • [Tech Stack](#-tech-stack)

</div>

---

## 🎯 Overview

Pharmacy AI Agent is a production-ready RESTful API that revolutionizes pharmacy operations by combining computer vision, natural language processing, and predictive analytics. The system automatically extracts and structures prescription data from images, manages multi-tenant pharmacy inventories, and forecasts medication demand.

### Key Capabilities

- **🔍 OCR-Powered Prescription Processing**: Leverages PaddleOCR v5 for high-accuracy text extraction from prescription images
- **🤖 AI-Driven Data Parsing**: Uses LLM (via OpenRouter API) to intelligently structure extracted prescription data with error correction
- **📊 Demand Forecasting**: Implements usage-based algorithms to predict inventory needs and prevent stockouts
- **🏢 Multi-Tenant Architecture**: Secure pharmacy-level data isolation with JWT authentication
- **⚡ Async Processing**: Background task handling for resource-intensive OCR operations

---

## ✨ Features

### Prescription Management
- **Image Upload & Processing**: Accepts prescription images, performs OCR extraction, and parses medication details
- **Manual Entry**: Direct text input for prescriptions with AI-powered structuring
- **Patient History**: Retrieve all prescriptions for a specific patient
- **Dual Input Modes**: Supports both file uploads and manual text entry

### Inventory Management
- **Stock Tracking**: Real-time inventory monitoring with batch and expiration date tracking
- **Automated Deduction**: Updates stock levels and calculates rolling usage rates
- **Forecasting Reports**: Generates demand predictions (7-day and 30-day) with reorder alerts
- **Export Capabilities**: CSV and PDF report generation with timezone support (Africa/Lagos)

### Authentication & Security
- **JWT-Based Auth**: Secure token-based authentication for pharmacy tenants
- **Multi-Tenancy**: Complete data isolation between pharmacy instances
- **Password Hashing**: Secure credential storage (bcrypt-ready)

---

## 🏗️ Architecture

```
┌─────────────────┐
│  Client/Frontend│
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────────┐
│       FastAPI Layer                 │
│  (Routers: Prescriptions,           │
│   Inventory, Authentication)        │
└────────┬───────────────────┬────────┘
         │                   │
         ▼                   ▼
┌──────────────────┐  ┌──────────────┐
│  PaddleOCR       │  │  Multi-Tenant│
│  Service         │  │  Auth Service│
│  (Image → Text)  │  │  (JWT)       │
└────────┬─────────┘  └──────────────┘
         │
         ▼
┌──────────────────┐
│  LLM Parser      │
│  (OpenRouter API)│
│  (Text → JSON)   │
└────────┬─────────┘
         │
         ▼
┌─────────────────────────────────────┐
│         MongoDB Database            │
│  Collections: prescriptions,        │
│  inventory, patients, pharmacies,   │
│  reports                            │
└────────┬────────────────────────────┘
         │
         ▼
┌──────────────────┐
│  Forecasting     │
│  Module          │
│  (Analytics)     │
└──────────────────┘
```

### Data Flow: Prescription Processing

1. **Upload**: Client sends prescription image + metadata
2. **OCR Extraction**: PaddleOCR processes image → raw text
3. **AI Parsing**: LLM structures text into JSON (medications, dosages, doctor, date)
4. **Storage**: Prescription saved to MongoDB with pharmacy_id
5. **Linking**: Patient record updated with prescription reference

---

## 🚀 Installation

### Prerequisites

- Python 3.8+
- MongoDB 4.4+ (local or Atlas)
- OpenRouter API key ([Get one here](https://openrouter.ai/))

### Setup Steps

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/pharmacy-ai-agent.git
   cd pharmacy-ai-agent
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   
   # Windows
   venv\Scripts\activate
   
   # macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Download PaddleOCR models**
   ```bash
   python download_models.py
   ```
   This downloads the required OCR models to `paddle_models/models/`

5. **Configure environment variables**
   ```bash
   cp .env.example .env
   ```
   Edit `.env` and add your credentials:
   - `MONGO_URI`: Your MongoDB connection string
   - `API_KEY`: Your OpenRouter API key
   - `JWT_SECRET_KEY`: Generate a secure random string

6. **Run the application**
   ```bash
   uvicorn app.main:app --reload
   ```
   
   API will be available at: `http://localhost:8000`
   
   Interactive docs: `http://localhost:8000/docs`

---

## 📡 API Documentation

### Base URL
```
http://localhost:8000/api/v1
```

### Prescriptions

#### Upload Prescription Image
```http
POST /prescriptions/upload
Content-Type: multipart/form-data

Parameters:
- file: UploadFile (prescription image)
- patient_id: string
- physician_id: string
- prescription_number: string
- priority: string (e.g., "urgent", "normal")
- notes: string (optional)
- pharmacy_id: string (query param)

Response:
{
  "message": "Prescription upload initiated",
  "status": "processing"
}
```

#### Add Manual Prescription
```http
POST /prescriptions/manual
Content-Type: application/x-www-form-urlencoded

Parameters:
- patient_id: string
- physician_id: string
- prescription_number: string
- priority: string
- text: string (prescription text)
- notes: string (optional)
- pharmacy_id: string (query param)

Response:
{
  "message": "Prescription added",
  "prescription_id": "507f1f77bcf86cd799439011"
}
```

#### Get Patient Prescriptions
```http
GET /prescriptions/{patient_id}?pharmacy_id={pharmacy_id}

Response:
{
  "prescriptions": [
    {
      "_id": "507f1f77bcf86cd799439011",
      "patient_id": "P12345",
      "physician_id": "DR001",
      "prescription_number": "RX-2025-001",
      "parsed_data": {
        "medications": [
          {
            "name": "Amoxicillin",
            "dosage": "500mg",
            "frequency": "3 times daily"
          }
        ],
        "doctor": "Dr. Smith",
        "date_issued": "2025-01-15",
        "patient_name": "John Doe"
      },
      "ocr_raw": "...",
      "priority": "normal",
      "source": "file"
    }
  ]
}
```

### Inventory

#### Add Inventory Item
```http
POST /inventory
Content-Type: application/json

Body:
{
  "name": "Amoxicillin 500mg",
  "description": "Antibiotic capsules",
  "quantity": 1000,
  "unit_cost": 0.50,
  "selling_price": 1.20,
  "batch_number": "BATCH-2025-001",
  "expiration_date": "2026-12-31T00:00:00Z",
  "storage_location": "Shelf A3",
  "reorder_level": 100,
  "daily_usage_rate": 0
}

Query Params:
- pharmacy_id: string (required)
```

#### Get Inventory
```http
GET /inventory?pharmacy_id={pharmacy_id}

Response: Array of inventory items
```

#### Deduct Stock
```http
POST /inventory/deduct
Content-Type: application/x-www-form-urlencoded

Parameters:
- item_id: string
- quantity: float
- pharmacy_id: string (query param)

Response:
{
  "message": "Stock deducted",
  "item_id": "507f1f77bcf86cd799439011"
}
```

#### Generate Forecasting Report
```http
POST /inventory/report?pharmacy_id={pharmacy_id}

Response:
{
  "message": "Report generation started",
  "status": "processing"
}
```

#### Get Latest Report
```http
GET /inventory/report/latest?pharmacy_id={pharmacy_id}

Response:
{
  "report": {
    "_id": "...",
    "pharmacy_id": "PHARM001",
    "type": "demand_forecast",
    "summary": "Item: Amoxicillin | Current Stock: 850 | Usage Rate: 12.50/day | Days to Reorder: 60.0 | 7-Day Demand: 88 | 30-Day Demand: 375 | Alert: STABLE\n...",
    "created_at": "2025-01-15 14:30:00"
  }
}
```

#### Download Report (PDF)
```http
GET /inventory/report/download?pharmacy_id={pharmacy_id}

Response: PDF file download
```

#### Export Inventory (CSV)
```http
GET /inventory/export?pharmacy_id={pharmacy_id}

Response:
{
  "filename": "inventory_report_PHARM001.csv",
  "content": "name,description,quantity,...",
  "media_type": "text/csv"
}
```

### Authentication

#### Login
```http
POST /auth/login
Content-Type: application/x-www-form-urlencoded

Parameters:
- pharmacy_id: string
- password: string

Response:
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

---

## 🛠️ Tech Stack

### Backend Framework
- **FastAPI** - Modern, high-performance Python web framework
- **Uvicorn** - ASGI server for async request handling

### AI/ML Components
- **PaddleOCR v5** - State-of-the-art OCR for prescription text extraction
- **OpenRouter API** - LLM access (DeepSeek, Mistral) for intelligent parsing
- **Custom Forecasting** - Usage-based demand prediction algorithms

### Database
- **MongoDB** - NoSQL database for flexible prescription and inventory data
- **PyMongo** - Official MongoDB driver for Python

### Authentication & Security
- **JWT (PyJWT)** - Token-based authentication
- **Passlib** - Password hashing utilities
- **Python-dotenv** - Environment variable management

### Document Processing
- **OpenCV (cv2)** - Image preprocessing for OCR
- **ReportLab** - PDF report generation
- **Pytz** - Timezone handling (Africa/Lagos)

### Dependencies
See [`requirements.txt`](requirements.txt) for complete list.

---

## 📁 Project Structure

```
pharmacy-ai-agent/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI application entry point
│   ├── models/                 # Pydantic models
│   │   ├── prescription.py
│   │   ├── inventory.py
│   │   ├── patient.py
│   │   └── pharmacy.py
│   ├── routers/                # API endpoints
│   │   ├── prescriptions.py
│   │   ├── inventory.py
│   │   └── auth.py
│   └── services/               # Business logic
│       ├── ocr_service.py      # PaddleOCR integration
│       ├── ai_service.py       # LLM parsing
│       ├── database.py         # MongoDB connection
│       ├── forecasting.py      # Demand prediction
│       └── auth.py             # JWT handling
├── paddle_models/              # OCR model files
├── static/uploads/             # Uploaded prescription images
├── download_models.py          # OCR model downloader
├── requirements.txt
├── .env.example
├── .gitignore
├── LICENSE
└── README.md
```

---

## 🔮 Future Enhancements

This project was developed as a proof-of-concept and has several areas for expansion:

- [ ] **Frontend Interface**: React/Vue dashboard for pharmacy staff
- [ ] **Unit & Integration Tests**: Comprehensive test coverage
- [ ] **Docker Deployment**: Containerization with docker-compose
- [ ] **Real-time Notifications**: WebSocket alerts for low stock
- [ ] **Advanced Analytics**: ML-based seasonal demand forecasting
- [ ] **Barcode Scanning**: Integration with pharmacy barcode systems
- [ ] **Audit Logging**: Complete activity tracking for compliance
- [ ] **Role-Based Access Control**: Pharmacist, technician, admin roles
- [ ] **Drug Interaction Checker**: Safety validation for prescriptions
- [ ] **Insurance Integration**: Claims processing automation

---

## 🐛 Known Issues

- **OCR Service Bug**: `ocr_service.py` line 41 references `self.api_key` which is commented out in `__init__`. Currently works because API key is passed separately in routers, but direct service calls will fail.
- **No Test Coverage**: Unit tests not yet implemented
- **Limited Error Handling**: Some edge cases in OCR processing need better error messages

---

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 👤 Author

**Kosisochukwu**

- Portfolio: [HIM](https://kss-venv.onrender.com)
- GitHub: [@Ksschkw](https://github.com/Ksschkw)

---

## 🙏 Acknowledgments

- **PaddleOCR** team for the excellent OCR models
- **OpenRouter** for LLM API access
- **FastAPI** community for the amazing framework

---

<div align="center">

**⭐ Star this repo if you find it useful!**

</div>