# Omnigenius Backend

The API backend for [omnigenius.co](https://omnigenius.co) — powering the ORCA model with Chat, Search, Reason, and Auto modes.

## Architecture

Two Lambda functions behind a single AWS API Gateway:

| App | Routes | Purpose |
|---|---|---|
| **FastAPI** (`app/`) | `/v1/chat`, `/v1/search`, `/v1/reason` | Async streaming inference |
| **Flask** (`flask_app/`) | Everything else | Auth, billing, users, admin |

**Stack:** FastAPI + Flask · AWS Lambda (Graviton2) · API Gateway v2 · Supabase (Postgres) · Redis (ElastiCache) · Clerk (auth) · Stripe (billing) · Microsoft Graph (email) · S3 + CloudFront

---

## Local development

```bash
# 1. Clone and install
git clone https://github.com/your-org/omnigenius-backend.git
cd omnigenius-backend
make install

# 2. Configure environment
cp .env.example .env
# Fill in .env values (Supabase, Clerk, Stripe, etc.)

# 3. Start local Supabase
supabase start
supabase db push   # applies schema.sql

# 4. Run both servers
make dev-all
# FastAPI → http://localhost:8000
# Flask   → http://localhost:5000
```

---

## Project structure

```
omnigenius-backend/
├── app/                        # FastAPI (inference)
│   ├── main.py                 # App entrypoint + Mangum Lambda handler
│   ├── core/
│   │   └── config.py           # Pydantic settings
│   ├── api/v1/routes/
│   │   ├── auth.py
│   │   ├── chat.py             # POST /v1/chat
│   │   ├── conversations.py
│   │   └── ...
│   └── middleware/
│       ├── auth.py             # Clerk JWT verification
│       └── rate_limit.py
│
├── flask_app/                  # Flask (everything else)
│   ├── __init__.py             # App factory
│   ├── config.py
│   ├── extensions.py           # SQLAlchemy, Redis, Migrate
│   ├── wsgi.py                 # apig-wsgi Lambda handler
│   ├── routes/
│   │   ├── auth.py             # Clerk webhooks, signin/signup
│   │   ├── billing.py          # Stripe webhooks + checkout
│   │   ├── users.py
│   │   ├── admin.py
│   │   └── ...
│   ├── middleware/
│   │   ├── auth.py             # @clerk_required, @internal_only
│   │   └── rate_limit.py
│   └── services/
│       └── email.py            # Microsoft Graph API + SMTP fallback
│
├── supabase/
│   ├── schema.sql              # Full database schema (reference)
│   ├── config.toml             # Local Supabase CLI config
│   └── migrations/
│       └── 20260301000000_initial_schema.sql
│
├── template.yaml               # AWS SAM deployment (Lambda + API Gateway)
├── samconfig.toml              # SAM deploy parameters
├── openapi.json                # Full OpenAPI 3.1 spec
├── requirements.txt            # Python dependencies
├── Makefile                    # Dev + deploy commands
├── .env.example                # Environment variable reference
└── .gitignore
```

---

## Deployment

```bash
# Push secrets to AWS SSM (run once, from .env)
make ssm-push STAGE=production

# Build + deploy
make deploy           # production
make deploy-stg       # staging

# Tail logs
make logs
make logs-stg
```

---

## Database

Schema lives in `supabase/schema.sql`. Apply to a fresh database:

```bash
supabase db push                    # local
supabase db push --linked           # linked remote project
```

---

## Environment

Copy `.env.example` to `.env`. Required variables:

- `SUPABASE_URL` + `SUPABASE_SERVICE_ROLE_KEY`
- `CLERK_SECRET_KEY` + `CLERK_WEBHOOK_SECRET`
- `STRIPE_SECRET_KEY` + `STRIPE_WEBHOOK_SECRET`
- `MS_TENANT_ID` + `MS_CLIENT_ID` + `MS_CLIENT_SECRET` (Outlook / Graph API)
- `ORCA_SERVICE_URL` + `ORCA_SERVICE_API_KEY`
- `REDIS_URL`

See `.env.example` for full reference with descriptions.

---

## License

Proprietary — © 2026 Omnigenius LLC
