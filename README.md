# Electrical Advisor & E-Commerce Platform — Backend

FastAPI + SQLAlchemy backend for the Indian Electrical Advisor + E-Commerce
platform. Covers Phase 1 (catalogue, cart, orders, auth) and the AI layer of
Phase 2 (Claude-assisted Advisor matching). The matching React frontend lives
in `../frontend` — see its README to run the two together.

## What's built in this phase

- **Auth** — register/login with JWT tokens, password hashing, role field
  (`customer` / `professional` / `admin` / `service_provider`)
- **Catalogue** — Category, Brand, Product (with images, specs, "who should
  buy this", "before you buy") + filtering/search on `/products`
- **Electrical Advisor** — the core USP: `POST /advisor/ask` takes a
  plain-language problem ("my fan is running slowly") and returns safe
  guidance, danger-level flagging, and the relevant product categories.
  Optionally AI-powered: if `ANTHROPIC_API_KEY` is set, Claude is used to
  understand more varied phrasing, but it only ever *picks which existing,
  admin-authored problem record* best fits the query — it never invents
  advice. Falls back to keyword matching automatically (no key needed, and
  also if the API call ever fails). The response includes `matched_via`
  (`"ai"` or `"keyword"`) so you can see which one answered.
- **Cart & Orders** — add to cart, checkout into an order (COD by default;
  payment gateway is a Phase-2+ integration)
- **Service requests** — Find an Electrician / Consultation / Installation /
  Inspection / Estimate, submitted against a user account
- **Admin-gated writes** — creating categories/brands/products requires an
  `admin` role token (full admin CRUD + dashboard is a frontend concern for
  a later phase)
- **Seed data** — realistic sample categories, brands, products and 7
  advisor problems (fan slow, MCB tripping, switch sparking, socket damaged,
  room with no power, need extra socket, need inverter)
- **Tests** — `tests/test_smoke.py` exercises the full flow end-to-end
  (register → login → browse → ask advisor → add to cart → place order);
  `tests/test_ai_advisor.py` covers the AI matcher and its fallback behaviour
  with the Anthropic call mocked out (no API key needed to run the suite)

## Setup

1. **Create a virtual environment (recommended) and install dependencies**
   ```bash
   cd backend
   python3 -m venv venv
   source venv/bin/activate        # on Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Configure environment variables**
   ```bash
   cp .env.example .env
   ```
   The defaults work immediately with SQLite — no database setup needed to
   try it out. For PostgreSQL, edit `DATABASE_URL` in `.env` and also
   install the extra driver:
   ```
   DATABASE_URL=postgresql://user:password@localhost:5432/electrical_platform
   ```
   ```bash
   pip install -r requirements-postgres.txt
   ```
   To turn on AI-powered problem matching, set `ANTHROPIC_API_KEY` in `.env`
   (get one at console.anthropic.com). Optional — the Advisor works without it.

3. **Seed sample data**
   ```bash
   python seed_data.py
   ```
   This also creates tables automatically. Safe to re-run.

4. **Run the server**
   ```bash
   uvicorn app.main:app --reload
   ```
   - API: http://127.0.0.1:8000
   - Interactive docs (Swagger): http://127.0.0.1:8000/docs

5. **Run tests**
   ```bash
   pytest
   ```

A demo admin account is created by the seed script:
`admin@example.com` / `Admin@123` — **change or remove this before any real
deployment.**

## Try the Advisor

```bash
curl -X POST http://127.0.0.1:8000/advisor/ask \
  -H "Content-Type: application/json" \
  -d '{"query": "my fan is running slowly"}'
```

## Project structure

```
backend/
├── app/
│   ├── main.py          # FastAPI app, router registration, CORS
│   ├── config.py        # settings from environment variables
│   ├── database.py      # SQLAlchemy engine/session
│   ├── dependencies.py  # get_current_user, require_admin
│   ├── models/          # SQLAlchemy models (User, Product, Advisor, Order, Service)
│   ├── schemas/         # Pydantic request/response models
│   ├── routes/          # API endpoints, one file per resource
│   ├── services/        # business logic (auth, advisor matching)
│   └── utils/           # password hashing, JWT helpers
├── seed_data.py
├── tests/test_smoke.py
├── requirements.txt
└── .env.example
```

## What's NOT built yet (by design — see roadmap)

- Admin dashboard UI (Phase 3) — the admin-only API endpoints exist, the
  screens don't yet
- Reviews, Wishlist, product bundles, quotations (straightforward additions
  once there's a UI need for them)
- WhatsApp integration, real payment gateway (checkout is COD-only for now),
  SEO content (Phase 4)
- B2B/professional account features (bulk orders, GST invoices)

## A note on AI costs

The AI matcher calls the Anthropic API on every `/advisor/ask` request where
`ANTHROPIC_API_KEY` is set — that's real, metered usage on your account, not
free. It's a short prompt against a small `max_tokens`, so per-call cost is
low, but at meaningful traffic you'll want to watch usage on
console.anthropic.com. Leaving the key unset costs nothing and the Advisor
still works fully via keyword matching.

## A note on the Advisor's safety design

Every advisor problem carries a `danger_level`. When it's `high`, the API
response includes an explicit instruction to switch off power and contact a
qualified electrician — this is enforced in code (`routes/advisor.py`), not
left to the frontend to remember to add.
# electrical_advisor
