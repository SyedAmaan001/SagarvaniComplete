# 🌊 Sagarvani — ORCA Marine Intelligence Platform

> **Conversational Marine Decision Intelligence for Safer and Smarter Coastal Operations**

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-Backend-009688.svg)](https://fastapi.tiangolo.com/)
[![Redis](https://img.shields.io/badge/Redis-Durable%20State-red.svg)](https://redis.io/)
[![Pytest](https://img.shields.io/badge/Tests-44%20Passing-brightgreen.svg)](https://pytest.org/)
[![Status](https://img.shields.io/badge/Status-Active%20Development-orange.svg)]()

---

## 🌊 Overview

**Sagarvani** is a conversational marine intelligence platform built around **ORCA — Marine Intelligence**.

ORCA is designed to sit above existing marine, oceanographic, meteorological, satellite and geospatial data sources and transform fragmented information into a coordinated, explainable decision-support layer.

Instead of simply displaying raw weather, ocean or GIS data, ORCA is designed to:

1. Understand a user's natural-language request.
2. Identify the location, time, activity, vessel and constraints.
3. Plan the information required to answer the request.
4. Retrieve information through specialized tools and agents.
5. Normalize information from different sources.
6. Apply deterministic safety and geofencing constraints.
7. Rank feasible options.
8. Verify data freshness, conflicts and provenance.
9. Return an explainable recommendation.

The core principle is:

> **AI plans and explains. Deterministic systems enforce safety constraints.**

---

# 🎯 Problem

Marine information is fragmented across multiple systems.

A fisherman or maritime operator may need to combine:

- Weather forecasts
- Wind and wave conditions
- Ocean currents
- Sea-surface temperature
- Potential Fishing Zones
- Cyclone warnings
- Restricted areas
- Geospatial boundaries
- Vessel constraints
- Route information

These datasets may have different formats, update cycles, sources and reliability.

The challenge is therefore not simply:

> "Can we display marine data?"

The real challenge is:

> **Can we combine the right information for a particular location, time and user context and turn it into a safe, explainable decision?**

Sagarvani/ORCA addresses this through a coordinated intelligence and decision layer.

---

# 🚀 Vision

ORCA is intended to support questions such as:

```text
Can I safely go fishing tomorrow morning?

Where is the nearest useful Potential Fishing Zone?

What are the sea conditions near me?

Which fishing areas should I avoid?

Find a productive area that is also safe and not restricted.

What is the safest route to the selected area?

The intended system combines marine conditions, weather, hazards, geospatial constraints and user context before producing a recommendation.

🧠 Safe-First Decision Intelligence

A key design principle of ORCA is:

        Candidate Areas
              │
              ▼
      ┌─────────────────┐
      │ Safety / Hazard │
      │     Gate        │
      └────────┬────────┘
               │
       Remove unsafe /
       restricted areas
               │
               ▼
      ┌─────────────────┐
      │ Multi-Objective │
      │    Ranking      │
      └────────┬────────┘
               │
               ▼
      ┌─────────────────┐
      │ Evidence &      │
      │ Verification    │
      └────────┬────────┘
               │
               ▼
      ┌─────────────────┐
      │ Recommendation  │
      │ + Map + Reason  │
      └─────────────────┘

Safety constraints are not treated as another AI score.

Unsafe or restricted options should be eliminated before productive options are ranked.

🔄 ORCA Decision Flow

The intended end-to-end workflow is:

User Query
    ↓
Interpret
    ↓
Plan
    ↓
Retrieve
    ↓
Normalize
    ↓
Reason
    ↓
Apply Safety Constraints
    ↓
Rank
    ↓
Verify
    ↓
Respond
1. Interpret

Extract:

User intent
Location
Time
Activity
Vessel information
Constraints
Language
2. Plan

The planner determines which information and tools are actually required.

ORCA should avoid blindly calling every available data source.

3. Retrieve

Specialized agents/tools retrieve relevant marine, weather, hazard and geospatial information.

4. Normalize

Different external sources are converted into a common internal representation containing information such as:

parameter
value
unit
latitude
longitude
valid_time
source
observed_or_forecast
quality
5. Reason

Marine, weather, spatial and contextual information is combined.

6. Constrain

Hard safety and geofence rules are applied.

Examples include:

Restricted areas
Marine hazards
Severe weather
Cyclone conditions
Unsafe sea state
Route constraints
7. Rank

Only feasible options are ranked according to the user's objective.

8. Verify

The system checks:

Data freshness
Source provenance
Conflicting results
Confidence
Missing critical information
9. Respond

The final decision package can contain:

Recommendation
Reasoning/evidence
Map information
Route
Warnings
Alternatives
Source information
🏗️ Current Architecture

The current implementation is centered around a FastAPI backend with an orchestration service, gateway abstractions and durable Redis-backed state.

                         ┌─────────────────────┐
                         │       Client        │
                         └──────────┬──────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │       FastAPI       │
                         │      API Layer      │
                         └──────────┬──────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │ OrchestrationService│
                         └──────────┬──────────┘
                                    │
                    ┌───────────────┼───────────────┐
                    │               │               │
                    ▼               ▼               ▼
              Interpreter       Planner         State
               Gateway         Gateway          Manager
                    │               │               │
                    │               │               ▼
                    │               │            Redis
                    │               │
                    └───────────────┘

The project deliberately keeps gateway and orchestration responsibilities separated so that external services can be replaced without rewriting the core orchestration layer.

💾 Durable State Management

Phase 6 introduced:

RedisStateManager

The production state backend uses Redis for durable request state.

Implemented capabilities include:

Persistent request state
Request recovery after process restart
Atomic state transitions
Distributed locking
Idempotency using client_request_id
Configurable key prefixes
Automatic TTL expiration
Structured error persistence

The project also retains:

InMemoryStateManager

for lightweight local development and unit testing.

State architecture
StateManager
    │
    ├── InMemoryStateManager
    │
    └── RedisStateManager

Production configuration can select Redis while tests can continue using the in-memory implementation.

⚙️ Current Implementation Status

The project is being developed incrementally.

Phase	Status
Phase 4 — API & Async Request Lifecycle	✅ Complete
Phase 5 — Failure & Edge-case Testing	✅ Complete
Phase 6 — Durable Redis State Management	✅ Complete
Phase 7 — Durable Task Execution	🚧 Next
Phase 8 — Real Service Integration	⏳ Planned
Phase 9 — Production Hardening	⏳ Planned
🧪 Testing

The current implementation has 44 automated tests.

Test coverage includes:

Unit Tests
Request/response models
Pydantic contracts
State transitions
Idempotency
State locking
Mock gateways
Contract validation
Redis state management
Integration Tests
Orchestration service
FastAPI routes
Request lifecycle
Status/result endpoints
Resilience Tests

The test suite covers failure and edge-case scenarios including:

Transient failures
Timeouts
Malformed responses
Delivery failures
Visualization metadata
State recovery
Concurrent access

Run the complete test suite:

pytest

Current verified result:

44 passed
📁 Repository Structure

The repository is organized around the backend orchestration architecture.

Sagarvani Complete/
│
├── app/
│   ├── config/
│   │   └── settings.py
│   │
│   ├── models/
│   │   └── requests.py
│   │
│   ├── services/
│   │   ├── state_manager.py
│   │   └── orchestration_service.py
│   │
│   ├── gateways/
│   │   ├── planner/
│   │   └── interpreter/
│   │
│   └── main.py
│
├── planner/
│   └── ...
│
├── tests/
│   ├── unit/
│   │   ├── test_models_and_contracts.py
│   │   ├── test_state_manager.py
│   │   ├── test_redis_state_manager.py
│   │   ├── test_gateways.py
│   │   └── test_contract_validator.py
│   │
│   └── integration/
│       ├── test_orchestration_service.py
│       ├── test_api_routes.py
│       └── test_resilience.py
│
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md

The exact structure may evolve as Phase 7 introduces the durable task execution layer.

🛠️ Technology Stack
Backend
Python 3.10+
FastAPI
Pydantic
AsyncIO
State Management
Redis
redis-py
fakeredis for isolated testing
Testing
Pytest
Async test infrastructure
Unit tests
Integration tests
Resilience tests
Planned Intelligence Layer

The broader ORCA architecture is designed around:

Planner Agent
Marine Data Agent
Weather/Hazard Agent
Geospatial Agent
Risk/Decision Agent
Evidence/Validation Agent
Conversation/Interpreter Agent

These components will be integrated progressively rather than treated as one monolithic AI system.

🌐 Data Ecosystem

The ORCA concept is designed to work with authoritative marine and geospatial data sources.

Potential sources include:

Source	Intended Use
INCOIS	PFZ, ocean forecasts, sea-state information
MOSDAC / ISRO	Satellite and oceanographic products
IMD	Weather, cyclone and warning information
INCOIS ERDDAP	Machine-readable ocean datasets
Government GIS sources	Maritime boundaries and restricted areas
Bhuvan / NRSC	Geospatial and earth-observation information

The project deliberately uses a Marine Data Gateway concept so that agents do not independently scrape or directly depend on every external source.

Instead:

External Sources
       │
       ▼
Marine Data Gateway
       │
       ├── Authentication
       ├── Retrieval
       ├── Normalization
       ├── Quality Checks
       ├── Provenance
       └── Caching
       │
       ▼
ORCA Agents

Data access, authentication, API availability and production usage permissions must be validated before individual integrations are considered production-ready.

🗄️ Environment Configuration

Create a local .env file based on the project's environment configuration.

Example:

STATE_BACKEND=redis

REDIS_URL=redis://localhost:6379

REDIS_KEY_PREFIX=orca:

REDIS_TTL_SECONDS=3600

Additional environment variables will be introduced as durable task execution and external service integrations are implemented.

⚠️ Security

Never commit:

.env
API keys
Passwords
Access tokens
Private credentials
Production secrets

The repository .gitignore already excludes environment files and virtual environments.

🚀 Local Development
1. Clone
git clone https://github.com/SyedAmaan001/SagarvaniComplete.git
cd SagarvaniComplete
2. Create virtual environment
Windows
python -m venv .venv
.venv\Scripts\Activate.ps1
Linux / macOS
python3 -m venv .venv
source .venv/bin/activate
3. Install dependencies
pip install -r requirements.txt
4. Configure environment

Create:

.env

and configure the required settings.

5. Start Redis

For local development, run a Redis instance and configure:

REDIS_URL=redis://localhost:6379
6. Start FastAPI
uvicorn app.main:app --reload

The API will be available at:

http://localhost:8000

Interactive API documentation:

http://localhost:8000/docs

ReDoc:

http://localhost:8000/redoc
🔌 API

The current backend exposes the orchestration lifecycle through FastAPI.

Core routes include:

POST /orchestrate
GET  /status
GET  /result
GET  /health

The exact request and response contracts are defined by the Pydantic models and API implementation.

Use Swagger UI for the currently deployed API contract:

http://localhost:8000/docs
🔐 Reliability Design

ORCA is designed with reliability as a first-class concern.

Current mechanisms include:

State durability

Redis persists request state beyond the lifetime of an individual process.

Idempotency

client_request_id is used to prevent duplicate request creation.

Distributed locking

Redis-backed locking protects critical state transitions.

State validation

Invalid state transitions are rejected using the project's state transition rules.

Error persistence

Structured errors are preserved inside the request state.

TTL

Request state can automatically expire after a configurable period.

🚧 Phase 7 — Durable Task Execution

The current remaining limitation is background execution.

The existing in-process task model is based on:

asyncio.create_task(...)

This means a process crash can interrupt an active task.

Phase 7 will introduce a durable task execution mechanism:

                FastAPI
                   │
                   ▼
              Redis State
                   │
                   ▼
            Durable Queue
                   │
          ┌────────┴────────┐
          ▼                 ▼
       Worker 1          Worker 2
          │                 │
          └────────┬────────┘
                   ▼
         OrchestrationService
                   │
                   ▼
              Redis State

Planned capabilities:

Durable task queue
Worker processes
Retry policies
Backoff
Crash recovery
Duplicate task protection
Concurrent worker handling
Idempotent task execution
🔮 Future Roadmap
Phase 7 — Durable Task Execution

Replace process-local background execution with a durable worker/task system.

Phase 8 — Real Service Integration

Replace mock Planner and Interpreter gateways with real service integrations.

This phase will include:

HTTP gateway validation
Service authentication
Timeout handling
Retry policies
Contract validation
Real integration tests
Phase 9 — Production Hardening

Planned areas include:

Structured logging
Metrics
Observability
Distributed tracing
Security
Configuration validation
Deployment automation
Production monitoring
Operational recovery
Future ORCA Expansion

The broader platform can progressively expand toward:

Marine data gateway integrations
PFZ intelligence
Weather and hazard analysis
Geospatial reasoning
Route planning
Risk scoring
Evidence/provenance
Multilingual interaction
Low-bandwidth access
Voice/helpline interfaces
Satellite data interpretation
Wider coastal coverage
🌍 Target Users

ORCA is designed to support multiple stakeholders.

🎣 Fishermen
Safer fishing decisions
Marine and weather information
PFZ discovery
Local-language interaction
Route planning
Hazard awareness
🧑‍🔬 Researchers
Integrated marine datasets
Faster analysis
Cross-source queries
Visualization
Scenario-based analysis
🚢 Maritime Operators
Operational planning
Marine conditions
Route risk
Context-aware recommendations
🏛️ Coastal & Disaster Authorities
Hazard awareness
Affected-area summaries
Spatial intelligence
Alerts
Situation awareness
💡 Why ORCA?

A conventional marine application may look like:

Weather API
    +
Ocean API
    +
PFZ Map
    +
GIS Map

ORCA instead aims to provide:

                User Context
                     │
                     ▼
                  Planner
                     │
        ┌────────────┼────────────┐
        ▼            ▼            ▼
      Marine       Weather      GIS
       Data         Data        Data
        │            │            │
        └────────────┼────────────┘
                     ▼
             Situation Model
                     │
                     ▼
              Safety Gate
                     │
                     ▼
              Decision Engine
                     │
                     ▼
                Verification
                     │
                     ▼
        Recommendation + Evidence

The differentiator is therefore not simply having a chatbot.

It is the decision loop:

Understand
   ↓
Plan
   ↓
Retrieve
   ↓
Reason
   ↓
Constrain
   ↓
Rank
   ↓
Verify
   ↓
Explain
🧭 Development Philosophy

ORCA follows several engineering principles:

1. Safety First

AI-generated recommendations must not override deterministic safety constraints.

2. Evidence First

Important decisions should be traceable to source data, timestamps and validation.

3. Modular Agents

Agents should have clear inputs, tools and outputs rather than unrestricted agent-to-agent conversations.

4. Gateway-Based Data Access

External data sources should be normalized through common gateway interfaces.

5. Incremental Development

The project is built phase-by-phase and validated before moving to the next architectural layer.

6. Testability

Critical behavior should be represented by automated tests.

7. Production-Aware Architecture

Durable state, idempotency, distributed locking and crash recovery are considered during development rather than added after the system is complete.

🏆 Project

Smart India Hackathon 2026

Problem Statement ID : SIH26176
Problem Statement    : ORCA Marine Ecosystem Reasoning with Collaborative Agents
Theme                : Disaster Management
Category             : Software
Team                 : Team Helios Luna
Institution           : Dayananda Sagar University

The project concept proposes a Karnataka-coast pilot before progressively expanding coverage and capabilities.

📚 References

The ORCA concept is based on the proposed use of authoritative marine, meteorological, satellite and geospatial sources, including INCOIS, MOSDAC/ISRO, IMD, ERDDAP and government GIS datasets.

Relevant sources identified in the project documentation include:

INCOIS
INCOIS ERDDAP
MOSDAC / ISRO
IMD
Bhuvan / NRSC
Government geospatial datasets

API availability, authentication requirements, update frequency and usage permissions should be validated before production integration.

🤝 Contributing

Contributions and improvements are welcome.

Create a feature branch:

git checkout -b feature/your-feature

Make your changes:

git add .
git commit -m "Add your feature"

Push:

git push origin feature/your-feature

Then open a Pull Request.

📄 License

This project is intended to be distributed under the MIT License.

See LICENSE for details.