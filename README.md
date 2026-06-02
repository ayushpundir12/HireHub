<div align="center">

```
██╗  ██╗██╗██████╗ ███████╗██╗  ██╗██╗   ██╗██████╗ 
██║  ██║██║██╔══██╗██╔════╝██║  ██║██║   ██║██╔══██╗
███████║██║██████╔╝█████╗  ███████║██║   ██║██████╔╝
██╔══██║██║██╔══██╗██╔══╝  ██╔══██║██║   ██║██╔══██╗
██║  ██║██║██║  ██║███████╗██║  ██║╚██████╔╝██████╔╝
╚═╝  ╚═╝╚═╝╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝ ╚═════╝ ╚═════╝ 
```

**A production-grade two-sided local services marketplace**

*Connecting clients with KYC-verified service professionals on demand*

[![Django](https://img.shields.io/badge/Django-5.0-092E20?style=flat-square&logo=django)](https://djangoproject.com)
[![DRF](https://img.shields.io/badge/DRF-3.15-red?style=flat-square)](https://django-rest-framework.org)
[![Next.js](https://img.shields.io/badge/Next.js-14-black?style=flat-square&logo=next.js)](https://nextjs.org)
[![Supabase](https://img.shields.io/badge/Supabase-PostgreSQL-3ECF8E?style=flat-square&logo=supabase)](https://supabase.com)
[![Redis](https://img.shields.io/badge/Redis-7-DC382D?style=flat-square&logo=redis)](https://redis.io)
[![Celery](https://img.shields.io/badge/Celery-5-37814A?style=flat-square)](https://docs.celeryq.dev)
[![Razorpay](https://img.shields.io/badge/Razorpay-Payments-02042B?style=flat-square)](https://razorpay.com)
[![Twilio](https://img.shields.io/badge/Twilio-SMS-F22F46?style=flat-square&logo=twilio)](https://twilio.com)

</div>

---

## What is HireHub?

HireHub is a **two-sided marketplace** where clients discover and book verified local service professionals — plumbers, electricians, chefs, carpenters, cleaners, and more. 

Every professional on the platform is KYC-verified and police-checked before going live. Every job completion is confirmed via a client-held OTP — no pro can mark a job done without the client physically confirming it.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                        FRONTEND                             │
│                    Next.js 14 (Vercel)                      │
└───────────────────────────┬─────────────────────────────────┘
                            │ REST API
┌───────────────────────────▼─────────────────────────────────┐
│                        BACKEND                              │
│              Django REST Framework (Railway)                │
│                                                             │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────┐   │
│  │  users   │ │  pros    │ │bookings  │ │ become_pro   │   │
│  └──────────┘ └──────────┘ └──────────┘ └──────────────┘   │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────┐   │
│  │payments  │ │dashboard │ │notifs    │ │   signals    │   │
│  └──────────┘ └──────────┘ └──────────┘ └──────────────┘   │
└──────┬───────────────┬──────────────────────────────────────┘
       │               │
┌──────▼──────┐ ┌──────▼──────┐
│  Supabase   │ │    Redis    │
│  PostgreSQL │ │   + Celery  │
│  + Storage  │ │   Workers   │
└─────────────┘ └─────────────┘
```

---

## Key Features

### 🔐 Authentication
- Email/password signup with dual OTP verification (email via SendGrid + phone via Twilio)
- Google & Facebook OAuth via Supabase Auth
- Custom DRF JWT authentication backend using Supabase JWKS
- Role-based access: `client`, `pro`, `admin`

### 🛡️ Pro Vetting Pipeline
- Multi-step onboarding: Profile → KYC docs → Police certificate → Skill certificates → Location proof
- Document upload to Supabase Storage (private bucket, signed URLs)
- Admin review panel with bulk approve/reject actions
- Automatic `ProProfile` creation on approval via Django admin action
- KYC status notifications via Celery tasks

### 📅 Booking State Machine
```
pending → confirmed → in_progress → awaiting_confirmation → completed
       ↘ cancelled        ↘ cancelled
```
- Pro accepts/declines incoming bookings
- OTP-based job completion — Twilio SMS delivered to client, pro submits OTP
- Client cannot be bypassed — fraud-proof completion flow

### ⚡ Performance
- Redis caching on all discovery endpoints (5 min TTL, MD5-keyed by query params)
- Cursor-based pagination on all list endpoints (no offset N+1 at scale)
- `select_related` throughout — zero N+1 queries
- DB-level aggregations using `TruncDay/Week/Month` for dashboard charts
- Cache invalidation on profile update and booking completion

### 💳 Payments (Razorpay)
- Razorpay Order creation for prepaid bookings
- HMAC-SHA256 signature verification on payment confirmation
- Webhook handler with idempotency check (event ID deduplication)
- Supports UPI, cards, netbanking, wallets

### 🔔 Notifications
- Event-driven in-app notification system
- Django signals → Celery tasks → Notification DB rows
- Triggers: booking received, confirmed, cancelled, completed, KYC approved/rejected, new review
- Unread count endpoint for bell badge polling

### 📊 Pro Dashboard
- KPI aggregations: total jobs, total earnings, avg rating, acceptance rate, pending bookings
- Earnings chart with daily/weekly/monthly toggle using DB-level `TruncDay/Week/Month`
- Redis-cached per pro (2 min TTL, invalidated on booking completion)

---

## Project Structure

```
backend/
├── apps/
│   ├── users/          # Auth, profiles, OTP, OAuth
│   ├── pros/           # Pro discovery, profiles, caching
│   ├── become_pro/     # KYC vetting pipeline
│   ├── bookings/       # Booking lifecycle, reviews, OTP completion
│   ├── payments/       # Razorpay integration
│   ├── dashboard/      # Pro KPIs + earnings chart
│   └── notifications/  # Event-driven notification system
├── core/
│   ├── settings.py
│   ├── urls.py
│   └── celery.py
└── manage.py

frontend/
├── app/                # Next.js 14 App Router
├── components/         # Reusable UI components
└── lib/                # API clients, utilities
```

---

## API Endpoints

### Auth — `/api/v1/auth/`
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/signup/` | Create account + trigger OTP |
| POST | `/verify/` | Verify email + phone OTP |
| POST | `/login/` | Login, returns JWT |
| POST | `/oauth/callback/` | Google/Facebook OAuth |
| POST | `/resend-otp/` | Resend email/phone OTP |
| GET/PATCH | `/profile/` | View/update own profile |
| POST | `/change-password/` | Change password via Supabase |
| POST | `/logout/` | Invalidate session |
| GET | `/me/` | Current user data |

### Pro Discovery — `/api/v1/`
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/pros/` | Filtered, cached, paginated pro list |
| GET | `/pros/<id>/` | Pro public profile |
| GET | `/pros/<id>/reviews/` | Pro reviews (public) |
| GET | `/categories/` | All categories with pro counts |
| GET/PATCH | `/pro/profile/` | Own profile (pro only) |

### Become Pro — `/api/v1/become-pro/`
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/apply/` | Start application |
| GET | `/status/` | Check application status |
| PATCH | `/step/personal/` | Personal info |
| PATCH | `/step/service/` | Service info |
| PATCH | `/step/kyc/` | KYC documents |
| PATCH | `/step/pcc/` | Police clearance |
| PATCH | `/step/skills/` | Skill certificates |
| PATCH | `/step/location/` | Location proof |
| POST | `/submit/` | Submit application |

### Bookings — `/api/v1/`
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/bookings/` | Create booking |
| GET | `/bookings/my/` | Client's bookings |
| GET | `/bookings/incoming/` | Pro's incoming bookings |
| PATCH | `/bookings/<id>/status/` | Update status (state machine) |
| POST | `/bookings/<id>/review/` | Leave review |
| POST | `/bookings/<id>/request-completion/` | Pro triggers OTP to client |
| POST | `/bookings/<id>/confirm-completion/` | Pro submits client OTP |

### Payments — `/api/v1/`
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/payments/initiate/` | Create Razorpay order |
| POST | `/payments/verify/` | Verify payment signature |
| POST | `/payments/webhook/` | Razorpay webhook handler |
| GET | `/payments/booking/<id>/` | Payment status |

### Dashboard — `/api/v1/`
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/dashboard/pro/` | KPIs |
| GET | `/dashboard/pro/earnings/?range=daily\|weekly\|monthly` | Earnings chart data |

### Notifications — `/api/v1/`
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/notifications/` | All notifications |
| GET | `/notifications/unread-count/` | Bell badge count |
| PATCH | `/notifications/<id>/read/` | Mark one read |
| POST | `/notifications/read-all/` | Mark all read |

---

## Local Setup

### Prerequisites
- Python 3.11+
- PostgreSQL (via Supabase)
- Redis
- Node.js 18+

### Backend

```bash
# Clone the repo
git clone https://github.com/yourusername/hirehub.git
cd hirehub/backend

# Create virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # Mac/Linux

# Install dependencies
pip install -r requirements.txt

# Create .env file
cp .env.example .env
# Fill in your keys (see Environment Variables section)

# Run migrations
python manage.py migrate

# Start server
python manage.py runserver

# Start Celery worker (separate terminal)
celery -A core worker --loglevel=info
```

### Frontend

```bash
cd hirehub/frontend
npm install
npm run dev
```

---

## Environment Variables

```env
# Django
SECRET_KEY=
DEBUG=True
ALLOWED_HOSTS=localhost

# Database (Supabase)
DB_NAME=postgres
DB_USER=postgres
DB_PASSWORD=
DB_HOST=
DB_PORT=5432

# Supabase
SUPABASE_URL=
SUPABASE_ANON_KEY=
SUPABASE_SERVICE_ROLE_KEY=
SUPABASE_PROJECT_REF=
SUPABASE_JWT_SECRET=

# Redis + Celery
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/0

# Email (SendGrid)
SENDGRID_API_KEY=
DEFAULT_FROM_EMAIL=noreply@hirehub.io

# Twilio (SMS OTP)
TWILIO_ACCOUNT_SID=
TWILIO_AUTH_TOKEN=
TWILIO_PHONE_NUMBER=

# Razorpay
RAZORPAY_KEY_ID=
RAZORPAY_KEY_SECRET=
RAZORPAY_WEBHOOK_SECRET=
```

---

## Data Models

```
users                    pro_profiles
─────────────────        ──────────────────────
id (UUID, Supabase)      id
email                    user → users
full_name                category
role (client/pro/admin)  bio
locality                 hourly_rate
phone_number             avg_rating ← auto-updated via signal
is_email_verified        total_jobs ← auto-updated via signal
is_number_verified       is_available
                         city, state

bookings                 reviews
────────────────────     ──────────────────
id                       id
client → users           booking → bookings (1:1)
pro → users              client → users
category                 pro → users
status (state machine)   rating (1-5)
payment_mode             comment
payment_status
scheduled_at
amount

pro_applications         notifications
─────────────────────    ──────────────────
id                       id
user → users             user → users
status (draft→approved)  type
kyc_document_*           title
pcc_document             message
skill_certificate_*      link
location_document        is_read
kyc/pcc/skills_verified
```

---

## Technical Decisions

| Decision | Choice | Why |
|----------|--------|-----|
| Auth | Supabase JWT | Handles OAuth, MFA, token refresh — no reinventing the wheel |
| ORM | Django ORM | `select_related`, `annotate`, `TruncDay` — powerful without raw SQL |
| Cache | Redis + django-redis | TTL-based, invalidation on write, fast |
| Pagination | Cursor-based | Stable at scale, no offset degradation |
| Task Queue | Celery + Redis | Async OTP, notifications, retries built-in |
| Payments | Razorpay | India-first, supports UPI, full test mode without business verification |
| Storage | Supabase Storage | Private buckets, signed URLs, CDN included |
| Completion | OTP via Twilio | Client must physically confirm — fraud-proof |

---

## Screenshots

> See `/docs/screenshots/` folder

---

## License

MIT

---

<div align="center">
Built by <strong>Your Name</strong> · <a href="https://linkedin.com/in/yourprofile">LinkedIn</a> · <a href="https://github.com/yourusername">GitHub</a>
</div>
