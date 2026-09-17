# Rosati's Ops

A back-office web app for the owner of a pizza store (modeled on Rosati's Pizza, Raleigh NC). It covers sales, deals, inventory, menu, orders and customers in one dashboard, and answers the question a spreadsheet can't: **which of my decisions actually make money?**

## Modules

| Module | Question it answers |
|---|---|
| Sales & Analytics | How is the store doing? |
| Deal Profit Optimizer | Which of the 6 live deals (10% off, Free 12", BOGO, Wednesday pasta, Family, Pizza Night) actually make profit after food cost and orders that would have happened anyway? |
| Inventory | What am I running low on? Includes manual stock counts |
| Menu & Pricing | What does each item earn? |
| Orders / Channels | Same $30 order, different profit: carryout vs. DoorDash / Uber Eats / Grubhub commissions |
| Customers & Loyalty | Who are my regulars? |

Data is a few weeks of reproducible seeded orders (`data.py`) built on the real menu and deals. All costs are editable defaults.

## Layout

```
backend/app/     FastAPI: routers/, logic/ (profit, inventory), data/ (seed + store)
frontend/        React 19 + TypeScript + Vite + Recharts
api/index.py     Vercel serverless entry (reuses backend/app)
data.py          seeded data foundation; `python3 data.py` prints a summary
```

## Run locally

```bash
# backend
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# frontend (proxies /api to :8000)
cd frontend
npm install
npm run dev
```

No database is needed locally: price and cost edits are saved to `backend/data_overrides.json`. Set `POSTGRES_URL` or `DATABASE_URL` to store them in Postgres instead.

## Deploy

`vercel.json` builds the frontend and serves the FastAPI app as a serverless function under `/api`. Set `POSTGRES_URL` in the Vercel project.

## Stack

FastAPI · Pydantic · PostgreSQL (psycopg) · React · TypeScript · Vite · Recharts · Vercel

> Independent portfolio project. Not affiliated with Rosati's Pizza.
