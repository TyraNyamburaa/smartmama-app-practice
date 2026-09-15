# SmartMama - Backend API

This is the core Python backend for the SmartMama application. It handles maternal health data (mother registration, pregnancy tracking, routine visit logging), automated risk classification, and secure SMS-based summary delivery to support Community Health Volunteers (CHVs) monitoring pregnant mothers.

This is the link to our hosted API
[([Heroku API URL](https://smartmama-dae0e93a9bfe.herokuapp.com/docs))]



## Database Architecture & Design (ERD)

The relational schema maps CHVs to the mothers they register, mothers to their pregnancies and locations, and each pregnancy to its household visit logs and generated risk assessments. For a visual layout of our system tables, foreign key relationships, and entity properties, view our complete ERD documentation[(https://lucid.app/lucidchart/0f7649cb-8104-4a8b-aaff-d72d5e0c3463/edit?invitationId=inv_ec7de662-9524-4cab-8d2c-a3b46a31863b)]



## How to Get Set Up

If you are just cloning our repo or setting up a new local environment, follow these quick steps:

1. **Fire up the virtual environment:** We keep dependencies isolated inside the local `env` folder. Activate it by running:
   ```bash
   source env/bin/activate
   ```
2. **Install the packages:** Once your environment is active, pull down all the required libraries using the terminal command:
   ```bash
   pip install -r requirements.txt
   ```
3. **Configure your environment variables:** You will need a local `.env` file in the project root to store your secrets. Add `.env` to your `.gitignore` file to ensure security credentials are never tracked by Git. Make sure it includes:
   ```env
   DATABASE_URL=Put your postgres db url link here
   SECRET_KEY=your_secret_hash_phrase_32_chars_or_more
   ALGORITHM=HS256
   ACCESS_TOKEN_EXPIRE_MINUTES=60
   MAX_LOGIN_ATTEMPTS=3
   LOCKOUT_DURATION_MINUTES=15
   SMSLEOPARD_API_KEY=your_sms_leopard_api_key
   SMSLEOPARD_API_SECRET=your_sms_leopard_api_secret
   SMSLEOPARD_SENDER_ID=your_SMS_Leopard_sender_id
   FRONTEND_URL=https://your-mother-portal-domain for the summary view
   ```


## Running the Project

To spin up the local development server, run the terminal command:
```bash
uvicorn main:app --reload
```
- Interactive API docs (Swagger UI): `http://127.0.0.1:8000/docs`



## How We Branch & Deploy

We maintain strict isolation between experimental features and stable live endpoints using a structured **branch deployment strategy**:

*   **dev:** This is our active integration branch. All feature modules, schema changes, and security adjustments are merged here first for review.
*   **main:** This branch contains our production-ready code.

### Deployment Flow

Our schema is now managed through **Alembic migrations** rather than automatic table creation, which run as part of deployment:
1.  **Procfile Configuration:** A `Procfile` instructs our hosting platform how to run migrations before starting the app:
    ```text
    release: alembic upgrade head
    web: uvicorn smartmama.main:app --host 0.0.0.0 --port $PORT
    ```
2.  **Config Vars Management:** Database credentials, the JWT secret, and SMS Leopard keys are stored strictly in the hosting platform's environment/config variable panel — never committed to the repo.



## Architecture, Python, & SQLAlchemy Integration

The system leverages object-oriented Python scripting and the **SQLAlchemy ORM (Object-Relational Mapper)** to manage database interactions without writing raw SQL, structured as a strict layered architecture:

```text
[Client Request] ──► Security Layer ──► Routers ──► Services ──► Repositories ──► SQLAlchemy ORM ──► PostgreSQL DB
```

*   **Python Engine:** Powers all operational workflows, request parsing, and backend validation using FastAPI.
*   **SQLAlchemy Models:** Define database tables as Python classes — CHV, Mother, Location, Pregnancy, VisitLog, and RiskAssessment.
*   **Routers / Schemas:** Map API paths and execute Pydantic-based input validation.
*   **Services:** Process business logic — risk classification, ownership/authorization checks, and SMS-triggering rules.
*   **Repositories:** Abstract database queries using SQLAlchemy sessions, keeping raw data access out of routers and services.
*   **Alembic migrations:** Tracks modifications to our SQLAlchemy models as versioned migration scripts:
    ```bash
    alembic init alembic
    alembic revision --autogenerate -m "Description of the change"
    alembic upgrade head
    ```



## Security & Identity Protection

*   **Password & PIN Verification:** Plaintext CHV passwords and mother PINs are hashed irreversibly using `bcrypt` prior to saving, and compared via constant-time verification — never as plaintext.
*   **Forgot Password:** Generates a secure, time-limited reset token, delivered via email, which must be exchanged for a new password before it expires.
*   **JWT Access Tokens (python-jose):** Authenticated CHVs receive a stateless JWT comprising a Header, a Payload with the CHV's identity, and an anti-tamper signature.
*   **CHV Login Lockout:** Repeated failed login attempts (default: 5) trigger a temporary lockout, configurable via `.env`, to block brute-force credential attacks.
*   **Mother PIN Lockout:** A mother's summary link is locked after 3 incorrect PIN attempts for 15 minutes, independent of the CHV lockout above — protecting the public, unauthenticated portal specifically.
*   **Hardening:** Enforces rate-limiting (`slowapi`) on public portal endpoints, a CORS allow-list restricting which frontend origins may call the API, parameterized queries throughout (no raw string interpolation), and cryptographically random (`secrets.token_urlsafe`) summary-link tokens.

---

## Core Endpoint Reference

### 1. CHV Authentication
*   **POST** `/api/v1/auth/chv/signup` (Public)
*   **POST** `/api/v1/auth/chv/login` (Public)
*   **Response (200/201):** `{"access_token": "jwt_string", "token_type": "bearer"}`
*   **Response (401 Unauthorized):** Invalid email or password

### 2. Mother Registration
*   **POST** `/api/v1/mothers` (Private - Requires CHV Token)
*   **GET** `/api/v1/mothers` / `/api/v1/mothers/{mother_id}` (Private - Requires CHV Token)

### 3. Visit Logging
*   **POST** `/api/v1/visits` (Private - Requires CHV Token) — logs a visit, computes maternal risk classification server-side
*   **GET** `/api/v1/visits/my-visits` / `/api/v1/visits/mother_history/{mother_id}` / `/api/v1/visits/mother/{mother_id}/trend` (Private - Requires CHV Token)

### 4. Risk Assessment & SMS Portal
*   **POST** `/api/v1/risk-assessment/generate/{visit_id}` (Private - Requires CHV Token) — generates a summary link; auto-sends SMS for High-risk visits
*   **GET** `/api/v1/risk-assessment/portal/{token}` (Public, rate-limited)
*   **POST** `/api/v1/risk-assessment/portal/{token}/verify` (Public, rate-limited + PIN lockout)



## Postman Integration

### Example of a Pre-request Script
```javascript
pm.collectionVariables.set(
  "chv_email",
  "chv_" + Math.floor(1000 + Math.random() * 9000) + "@example.com"
);
```

### Example of a Post-response Test Script
```javascript
const data = pm.response.json();

pm.test("Response time is fast (under 2000ms)", function () {
    pm.expect(pm.response.responseTime).to.be.below(2000);
});

pm.test("Response format header is application/json", function () {
    pm.response.to.have.header("Content-Type");
    pm.expect(pm.response.headers.get("Content-Type")).to.include("application/json");
});

pm.test("risk_level is one of the expected values", function () {
    pm.expect(["Low", "Medium", "High"]).to.include(data.risk_level);
});
```
