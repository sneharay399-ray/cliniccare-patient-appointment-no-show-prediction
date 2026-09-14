# Patient Appointment & No-Show Prediction System
### ClinicCare — Academic Agentic AI Project

> ⚠️ **DISCLAIMER**: The no-show prediction model is an **academic/demonstration system**. It is NOT medically validated and MUST NOT be used for clinical decision-making.

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Problem Statement](#2-problem-statement)
3. [Project Objective](#3-project-objective)
4. [Features](#4-features)
5. [User Roles](#5-user-roles)
6. [Technology Stack](#6-technology-stack)
7. [Project Architecture](#7-project-architecture)
8. [Database Structure](#8-database-structure)
9. [ML Model Explanation](#9-ml-model-explanation)
10. [Agentic AI Workflow](#10-agentic-ai-workflow)
11. [Installation Instructions](#11-installation-instructions)
12. [Environment Variables](#12-environment-variables)
13. [How to Run](#13-how-to-run)
14. [Sample Data](#14-sample-data)
15. [API Reference](#15-api-reference)
16. [Non-Functional Requirements](#16-non-functional-requirements)
17. [System Requirements](#17-system-requirements)
18. [Known Limitations](#18-known-limitations)
19. [Future Improvements](#19-future-improvements)

---

## 1. Project Overview

**ClinicCare** is a complete, full-stack healthcare web application that enables patients to manage doctor appointments online and empowers clinic staff to monitor appointment activity and identify patients at risk of missing appointments.

The system demonstrates **Agentic AI** concepts by automating an end-to-end decision-support workflow: automated risk assessment → reminder scheduling → notification simulation → dashboard update — without requiring manual admin intervention for each step.

### Stack at a Glance

| Layer | Technology |
|-------|-----------|
| Frontend | React 18 + Vite + TailwindCSS + React Router v6 + Recharts |
| Backend | Node.js 18+ + Express 4 + better-sqlite3 + bcryptjs + jsonwebtoken |
| ML Service | Python 3.9+ + Flask 3 + scikit-learn + NumPy + pandas |
| Database | SQLite (dev) — PostgreSQL-compatible schema |

---

## 2. Problem Statement

Missed medical appointments (no-shows) are a significant problem in healthcare:
- They waste clinician time and clinic resources
- They delay care for other patients
- They increase operational costs
- No-show rates in healthcare settings typically range from 10–30%

The goal is to predict which upcoming appointments are at high risk of being missed and proactively send reminders to those patients before their appointment.

---

## 3. Project Objective

1. Allow patients to register, log in, browse doctors, and book/reschedule/cancel appointments
2. Allow doctors to view their schedule and patient attendance information
3. Allow administrators to manage all appointments and view analytics
4. Automatically predict no-show risk using patient attendance history (ML)
5. Automatically schedule and simulate SMS/email reminders (Agentic workflow)
6. Provide reports and analytics on appointment trends, no-show rates, and risk distribution

---

## 4. Features

| Feature | Description |
|---------|-------------|
| Patient registration & login | Full name, email, age, gender, phone, DOB, medical ID |
| Doctor & department listing | Browse by department, view specialization and available slots |
| Slot-based appointment booking | Select doctor → available slot → confirm |
| Appointment management | View, reschedule, cancel upcoming appointments |
| Role-based dashboards | Separate UIs for Patient, Doctor, Admin |
| No-show risk prediction | ML-based score displayed per appointment (Low/Medium/High) |
| Agentic reminder workflow | Automated: assess risk → schedule → simulate send → record result |
| Reminder simulation | Mock SMS and Email with status tracking (scheduled/sent/failed) |
| Admin dashboard | KPIs, charts, doctor load, risk distribution, cancellation/no-show rates |
| Reports & analytics | Filterable: by date, doctor, department, status |
| Double-booking prevention | Checked server-side on every booking |
| Attendance history | All historical attendance records stored and used for ML |
| Model evaluation metrics | ROC-AUC, accuracy, precision, recall, F1, confusion matrix |

---

## 5. User Roles

### Patient
- Register and log in
- View doctors and departments
- View available slots
- Book appointments (doctor + slot selection, 3-step wizard)
- View upcoming and past appointments
- Reschedule upcoming appointments
- Cancel upcoming appointments
- View appointment details + no-show risk
- View reminder status

### Doctor
- Log in
- View personal dashboard with today's schedule and stats
- View patient information relevant to appointments
- Mark appointments as completed or no-show
- View no-show risk per patient
- View full schedule with date and status filters

### Admin
- Log in
- Full dashboard with KPIs and charts (bar, pie, line)
- Manage all appointments (edit, complete, mark no-show)
- View all patients and their attendance history
- View all doctors and departments
- Trigger the agentic reminder workflow
- View and resend individual notifications
- Generate filtered reports (appointments, no-show analysis, trends)

---

## 6. Technology Stack

| Layer        | Technology                                        |
|--------------|---------------------------------------------------|
| Frontend     | React 18, Vite, TailwindCSS, React Router v6, Recharts, Axios |
| Backend      | Node.js 18+, Express 4, better-sqlite3, bcryptjs, jsonwebtoken, node-fetch |
| Database     | SQLite (local dev) — schema is PostgreSQL-compatible |
| ML Service   | Python 3.9+, Flask 3, Flask-CORS, scikit-learn, NumPy, pandas, joblib |
| Auth         | JWT (role-based: patient / doctor / admin) |

### Why SQLite for development?
SQLite requires zero server setup for local academic demonstration. The schema uses standard SQL-92 syntax and is fully compatible with PostgreSQL — migration requires only swapping `better-sqlite3` for `pg`/`knex` and updating the connection string.

---

## 7. Project Architecture

```
healthcare-app/
├── backend/                  # Node.js REST API (Port 4000)
│   ├── src/
│   │   ├── index.js          # Express server entry point
│   │   ├── db.js             # Database init + seed data (SQLite)
│   │   ├── auth.js           # JWT helpers + role middleware
│   │   └── routes/
│   │       ├── auth.js       # Login, register, /me
│   │       ├── patients.js   # Patient CRUD (admin), own profile (patient)
│   │       ├── doctors.js    # Doctor listing + schedule + slots
│   │       ├── departments.js # Department listing + management
│   │       ├── appointments.js # Appointment CRUD + stats + ML integration
│   │       ├── notifications.js # Reminder simulation + agentic trigger
│   │       └── reports.js    # Filterable analytics reports
│   ├── data/
│   │   └── clinic.db         # SQLite database (auto-created)
│   ├── .env.example          # Environment variable template
│   └── package.json
│
├── ml-service/               # Python Flask ML predictor (Port 5001)
│   ├── app.py                # Full prediction service (documented)
│   ├── model.joblib          # Cached trained model (auto-generated)
│   ├── model_metrics.json    # Evaluation metrics (auto-generated)
│   └── requirements.txt      # Python dependencies
│
└── frontend/                 # React 18 SPA (Port 5173 dev / 4173 preview)
    ├── index.html
    ├── vite.config.js        # Proxy: /api → backend:4000
    ├── tailwind.config.js
    └── src/
        ├── App.jsx            # Router + protected routes
        ├── api.js             # Axios client with JWT interceptor
        ├── main.jsx           # Entry point
        ├── index.css          # TailwindCSS + custom component classes
        ├── context/
        │   └── AuthContext.jsx # Auth state + login/register/logout
        ├── components/
        │   ├── Layout.jsx     # Page wrapper + footer
        │   ├── Navbar.jsx     # Role-adaptive responsive navigation
        │   └── UI.jsx         # Shared: RiskBadge, StatusBadge, StatCard,
        │                      #         Spinner, Alert
        └── pages/
            ├── Home.jsx        # Landing page with features + doctor list
            ├── Login.jsx       # Login form (all roles)
            ├── Register.jsx    # Patient self-registration form
            ├── Doctors.jsx     # Public doctor browser with filters
            ├── patient/
            │   ├── PatientDashboard.jsx   # Stats + upcoming appts + quick actions
            │   ├── BookAppointment.jsx    # 3-step booking wizard
            │   ├── MyAppointments.jsx     # View, reschedule, cancel
            │   ├── AppointmentDetail.jsx  # Detail + risk display + reminders
            │   ├── MyReminders.jsx        # Patient reminder status view
            │   └── PatientProfile.jsx     # Edit own profile
            ├── doctor/
            │   ├── DoctorDashboard.jsx    # Today's schedule + high-risk list
            │   └── DoctorSchedule.jsx     # Full schedule with filters
            └── admin/
                ├── AdminDashboard.jsx     # KPIs + charts + recent appointments
                ├── AdminAppointments.jsx  # Full appointment management table
                ├── AdminPatients.jsx      # Patient list + attendance modal
                ├── AdminDoctors.jsx       # Doctor cards with details
                ├── AdminNotifications.jsx # Reminder log + agentic trigger
                └── AdminReports.jsx       # Filterable reports (3 tabs)
```

### Request Flow

```
Browser ──► Vite Dev Server ──► /api proxy ──► Express Backend ──► SQLite DB
                                                     │
                                              ML Service (Flask)
                                              POST /predict → risk score
```

---

## 8. Database Structure

### Tables

| Table              | Purpose |
|--------------------|---------|
| `users`            | All users (patients, doctors, admin) with hashed passwords and roles |
| `patients`         | Patient-specific profile (medical_id, age, gender, dob, phone) |
| `doctors`          | Doctor profiles linked to users and departments |
| `departments`      | Clinic departments/specializations |
| `slots`            | Available time slots per doctor per day |
| `appointments`     | Core appointment records with status |
| `attendance_history` | Immutable log of each appointment outcome |
| `predictions`      | ML prediction results stored per appointment |
| `notifications`    | Mock SMS/email records with scheduled/sent/failed status |

### Key Relationships

```
departments ──< doctors ──< appointments >── patients ──> users
                                │                              │
                         attendance_history              (users also for doctors/admin)
                                │
                           predictions
                                │
                          notifications
```

### Appointment Statuses

| Status | Description |
|--------|-------------|
| `upcoming` | Booked, not yet occurred |
| `completed` | Patient attended |
| `cancelled` | Cancelled by patient or admin |
| `no-show` | Patient did not attend |

---

## 9. ML Model Explanation

> ⚠️ **ACADEMIC/DEMO ONLY** — Trained on synthetic data. Not medically validated.

### Algorithm

**Logistic Regression** (`sklearn.linear_model.LogisticRegression`)

Pipeline: `StandardScaler` → `LogisticRegression(class_weight='balanced')`

### Why Logistic Regression?

- Fast inference (sub-millisecond) — suitable for real-time API calls
- Interpretable coefficients
- Works well on tabular data with engineered rate features
- Handles class imbalance via `class_weight='balanced'`

### Features (10 total)

| # | Feature | Description |
|---|---------|-------------|
| 1 | `age` | Patient age in years |
| 2 | `gender` | Encoded: female=0, male=1, unknown=2 |
| 3 | `specialty` | Encoded department index (0–7) |
| 4 | `appointment_hour` | Hour of appointment (8–17) |
| 5 | `day_of_week` | 0=Sunday … 6=Saturday |
| 6 | `total_appointments` | Patient's total historical appointments |
| 7 | `previous_no_shows` | Count of previous no-shows |
| 8 | `previous_cancellations` | Count of previous cancellations |
| 9 | `no_show_rate` | **Derived**: previous_no_shows / total (strongest predictor) |
| 10 | `cancellation_rate` | **Derived**: previous_cancellations / total |

### Training Data

3,000 synthetic records generated from a realistic logistic model with coefficients based on published no-show research literature. Labels are probabilistically generated — **not real patient data**.

Training/test split: 80% / 20% (stratified)

### Evaluation Metrics (from `model_metrics.json`)

| Metric | Value |
|--------|-------|
| ROC-AUC | ~0.71 |
| Accuracy | ~0.67 |
| Precision | ~0.68 |
| Recall | ~0.65 |
| F1-Score | ~0.67 |

The full confusion matrix is stored in `ml-service/model_metrics.json` and exposed via `GET http://localhost:5001/metrics`.

### Risk Classification

| Score | Level |
|-------|-------|
| ≥ 0.70 | 🔴 HIGH RISK |
| 0.40–0.69 | 🟡 MEDIUM RISK |
| < 0.40 | 🟢 LOW RISK |

### ML Service Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `http://localhost:5001/health` | GET | Health check |
| `http://localhost:5001/predict` | POST | Predict no-show risk |
| `http://localhost:5001/metrics` | GET | Model evaluation metrics |
| `http://localhost:5001/retrain` | POST | Force model retraining |

---

## 10. Agentic AI Workflow

The system implements an **automated decision-support workflow** that runs without manual admin intervention for individual appointments:

```
Step 1: [Backend]    Retrieve upcoming appointments due for reminder
          ↓ (scheduled_at <= now AND status = 'upcoming')
Step 2: [Backend]    Gather patient attendance history from DB
          ↓ (COUNT no-shows, cancellations, total appointments)
Step 3: [ML Service] Analyse features → generate no-show probability
          ↓ (POST /predict with age, gender, specialty, history)
Step 4: [ML Service] Classify risk as Low / Medium / High
          ↓ (prob ≥ 0.7 = high, ≥ 0.4 = medium, < 0.4 = low)
Step 5: [Backend]    Schedule reminder notification (email + SMS per booking)
          ↓ (INSERT into notifications, scheduled 24h before appointment)
Step 6: [Backend]    Simulate sending SMS/email (mock service, 95% success)
          ↓ (Math.random() > 0.05 = success, else failed)
Step 7: [Backend]    Record notification result (UPDATE status to sent/failed)
          ↓ (UPDATE notifications SET status=?, sent_at=?)
Step 8: [Frontend]   Admin dashboard displays updated risk + reminder info
```

**Triggering the workflow**: Admin clicks **"Run Reminder Workflow"** on the Notifications page → `POST /api/notifications/trigger`

**What is automated vs manual**:

| Aspect | Automated | Manual |
|--------|-----------|--------|
| Risk prediction at booking | ✅ Runs automatically | — |
| Risk re-evaluation at reschedule | ✅ Runs automatically | — |
| Notification scheduling at booking | ✅ Runs automatically | — |
| Batch reminder processing | — | 👤 Admin trigger (production: cron) |
| Attendance recording | — | 👤 Doctor/admin marks status |

**Traditional vs Intelligent functionality**:

| Component | Type |
|-----------|------|
| Patient registration, login, booking UI | Traditional application |
| Database CRUD operations | Traditional application |
| Role-based access control | Traditional application |
| No-show risk scoring (ML) | Intelligent / AI |
| Automated reminder decision | Intelligent (rule-based + ML) |
| Risk-level classification | Intelligent / AI |
| Dashboard analytics | Traditional (aggregation) |

---

## 11. Installation Instructions

### Prerequisites

- **Node.js 18+** and npm (for backend and frontend)
- **Python 3.9+** and pip (for ML service)

### Step 1 — Navigate to the project

```bash
cd healthcare-app
```

### Step 2 — Install Backend Dependencies

```bash
cd backend
npm install
```

### Step 3 — Install ML Service Dependencies

```bash
cd ml-service
pip install -r requirements.txt
```

### Step 4 — Install Frontend Dependencies

```bash
cd frontend
npm install
```

---

## 12. Environment Variables

### Backend (`backend/.env.example`)

```env
PORT=4000
JWT_SECRET=change-me-in-production-to-random-256-bit-key
ML_SERVICE_URL=http://localhost:5001
NODE_ENV=development
CORS_ORIGINS=http://localhost:5173,http://localhost:4173
```

Copy to `backend/.env` and update as needed. **Never commit `.env` to version control.**

### Frontend

The frontend uses Vite's built-in proxy to forward `/api` requests to the backend. No `.env` file is required for local development.

---

## 13. How to Run

Start all three services in separate terminals:

### Terminal 1 — ML Service

```bash
cd healthcare-app/ml-service
python app.py
# → Running on http://localhost:5001
# Model trains on first run (~5s), cached to model.joblib
```

### Terminal 2 — Backend

```bash
cd healthcare-app/backend
cp .env.example .env          # first time only
npm run dev
# → Backend running on http://localhost:4000
# Database auto-created and seeded on first run
```

### Terminal 3 — Frontend

```bash
cd healthcare-app/frontend
npm run dev
# → Frontend running on http://localhost:5173
```

Open **http://localhost:5173** in your browser.

> **Note**: The backend calls the ML service for predictions when appointments are booked. If the ML service is not running, predictions gracefully degrade to "N/A" — the booking still succeeds.

### How to Reset the Database

```bash
# Delete the SQLite file and restart the backend
rm healthcare-app/backend/data/clinic.db
# Restart the backend — it re-creates and re-seeds automatically
```

### How to Retrain the ML Model

```bash
# Option 1: Delete cached files and restart ML service
rm healthcare-app/ml-service/model.joblib
rm healthcare-app/ml-service/model_metrics.json
python app.py   # retrains on startup

# Option 2: API call (ML service must be running)
curl -X POST http://localhost:5001/retrain
```

---

## 14. Sample Data

The system automatically seeds the following on first run:

| Entity | Count | Details |
|--------|-------|---------|
| Departments | 8 | General Practice, Cardiology, Dermatology, Orthopedics, Neurology, Pediatrics, Oncology, Psychiatry |
| Doctors | 6 | Dr. Adams (GP), Dr. Bell (Cardiology), Dr. Chen (Derm.), Dr. Davis (Ortho.), Dr. Evans (Neuro.), Dr. Foster (Pediatrics) |
| Patients | 8 | Alice, Bob, Carol, David, Eva, Frank, Grace, Henry |
| Past appointments | ~40 | Mix of completed, no-show, cancelled |
| Upcoming appointments | 8 | One per patient, with seeded ML predictions |
| Notifications | 16 | Email + SMS per upcoming appointment |
| Slots | ~960 | 12 time slots × 6 doctors × ~14 weekdays |

### Demo Credentials

| Role    | Email                    | Password    |
|---------|--------------------------|-------------|
| Admin   | admin@clinic.com         | Admin@123   |
| Doctor  | dr.adams@clinic.com      | Doctor@123  |
| Doctor  | dr.bell@clinic.com       | Doctor@123  |
| Doctor  | dr.chen@clinic.com       | Doctor@123  |
| Patient | alice@example.com        | Patient@123 |
| Patient | bob@example.com          | Patient@123 |
| Patient | carol@example.com        | Patient@123 |

---

## 15. API Reference

### Auth

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/api/auth/login` | Public | Login (all roles) |
| POST | `/api/auth/register` | Public | Patient self-registration |
| GET | `/api/auth/me` | Bearer | Current user info |

### Departments

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/api/departments` | Public | List all departments |
| GET | `/api/departments/:id` | Public | Single department |
| POST | `/api/departments` | Admin | Create department |
| PATCH | `/api/departments/:id` | Admin | Update department |

### Doctors

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/api/doctors` | Public | List all doctors |
| GET | `/api/doctors/:id` | Public | Doctor + slots |
| GET | `/api/doctors/:id/slots` | Public | Available slots |
| GET | `/api/doctors/me/appointments` | Doctor | Own appointments |
| PATCH | `/api/doctors/:id` | Admin | Update doctor |

### Patients

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/api/patients` | Admin | All patients with stats |
| GET | `/api/patients/me` | Patient | Own profile |
| PATCH | `/api/patients/me` | Patient | Update own profile |
| GET | `/api/patients/:id` | Admin/Doctor | Specific patient |

### Appointments

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/api/appointments` | Auth | Role-filtered list |
| GET | `/api/appointments/stats` | Admin | Dashboard statistics |
| GET | `/api/appointments/:id` | Auth | Single appointment |
| POST | `/api/appointments` | Auth | Book appointment |
| PATCH | `/api/appointments/:id` | Auth | Update/reschedule |

### Notifications

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/api/notifications` | Auth | Role-filtered list |
| GET | `/api/notifications/stats` | Admin | Notification statistics |
| POST | `/api/notifications/trigger` | Admin | Run agentic reminder workflow |
| POST | `/api/notifications/:id/resend` | Admin | Resend notification |

### Reports

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/api/reports/appointments` | Admin | Filtered appointment report |
| GET | `/api/reports/no-show` | Admin | No-show analysis |
| GET | `/api/reports/trends` | Admin | Monthly/weekly trends |

### ML Service (internal)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `http://localhost:5001/health` | Health check |
| POST | `http://localhost:5001/predict` | Predict no-show risk |
| GET | `http://localhost:5001/metrics` | Model evaluation metrics |
| POST | `http://localhost:5001/retrain` | Force model retraining |

---

## 16. Non-Functional Requirements

These are **target production requirements** — they are NOT load-tested in this academic prototype:

| Requirement | Target | Status |
|-------------|--------|--------|
| Concurrent patient sessions | 500+ (horizontal scaling with PM2) | Target |
| Booking confirmation time | < 2 seconds under normal load | ✅ < 200ms locally |
| Role-based access control | patient / doctor / admin | ✅ Implemented |
| Encryption in transit | HTTPS in production (Nginx + Let's Encrypt) | Target |
| Uptime (booking module) | 99% target | Target |
| Password storage | bcrypt (cost factor 10) | ✅ Implemented |
| Input validation | Server-side on all routes | ✅ Implemented |
| Double-booking prevention | Server-side conflict check | ✅ Implemented |

---

## 17. System Requirements

### Target Production Server

- **OS**: Ubuntu 22.04 LTS
- **CPU**: 4 vCPU minimum
- **RAM**: 8 GB minimum
- **Storage**: 20 GB minimum (database + logs + application)
- **Runtime**: Node.js 18 LTS + Python 3.9+
- **Database**: PostgreSQL 15+ (replace SQLite for production)

### Development Requirements

- Node.js 18+
- Python 3.9+
- npm 9+
- Modern browser

### Client

- Modern browser (Chrome 90+, Firefox 88+, Safari 14+, Edge 90+)
- Desktop, tablet, or mobile

---

## 18. Known Limitations

1. **SQLite for development**: Not suitable for high-concurrency production; migrate to PostgreSQL
2. **Synthetic ML training data**: Model trained on generated data — performance on real data is unknown
3. **No real SMS/email**: Notification service is fully simulated; Twilio/SendGrid required for production
4. **Manual reminder trigger**: Agentic workflow must be manually triggered; in production, use node-cron
5. **No email verification**: Patient registration has no email confirmation step
6. **Single admin**: No admin user management UI (admin created via DB seed only)
7. **Slot regeneration**: Slots are seeded once; a production system needs daily slot generation
8. **No file uploads**: No support for medical documents or prescriptions
9. **No real-time updates**: Dashboard requires manual refresh; WebSocket would improve UX
10. **Legacy dead-code files**: Top-level `pages/BookAppointment.jsx`, `pages/MyAppointments.jsx` are unused legacy files — they do not affect the running application

---

## 19. Future Improvements

- [ ] Replace SQLite with PostgreSQL for production
- [ ] Integrate Twilio SMS and SendGrid email APIs
- [ ] Add cron-based automated reminder scheduling (node-cron)
- [ ] Implement patient email verification
- [ ] Add doctor availability calendar management
- [ ] Retrain ML model on real anonymised data (with ethics approval)
- [ ] Compare logistic regression with Random Forest / XGBoost
- [ ] Implement WebSocket for real-time dashboard updates
- [ ] Add patient appointment confirmation flow (confirm via link in reminder)
- [ ] Add export to CSV/PDF for reports
- [ ] Build mobile app (React Native)
- [ ] Add telehealth video consultation module
- [ ] Add admin user management UI
- [ ] Implement daily slot auto-generation via scheduled job
- [ ] Add pagination for large appointment/patient lists
- [ ] Add rate limiting and API throttling for production

---

*ClinicCare © 2024 — Academic Agentic AI Demonstration Project*
*⚠️ No-show predictions are NOT medically validated and are for demonstration purposes only.*
