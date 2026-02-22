---
name: domain-reorganization
description: Organize codebases using Domain-Driven Design (DDD) principles to fix scattered logic.
---

# Domain-Driven Reorganization

## The Problem

Codebases often degrade into 'graveyards' of `utils` generic folders, or files where database models are mixed with API routes and business logic. This makes the system hard to navigate and refactor.

## The Process

1. **Analyze**: Scan the codebase for:
    * Generic folders like `utils`, `common`, `helpers` containing unrelated functions.
    * Files with mixed responsibilities (e.g., a single file doing SQL queries, HTTP handling, and complex math).
    * Import patterns: See which modules are tightly coupled.

2. **Cluster**: Identify related logic.
    * Group functions and classes by **Domain Concept** (e.g., 'Lifting Formulas', 'User Management', 'Leaderboard Calculation') rather than technical type (e.g., 'Controllers', 'Models').

3. **Propose**: Suggest a **Domain-Driven Design (DDD)** structure.
    * **Domain Layer**: `/domain/<concept>/`
        * Contains pure business logic, rules, and formulas (e.g., Wilks coefficient calculation).
        * *Zero dependencies* on frameworks or databases.
    * **Infrastructure Layer**: `/infrastructure/<tech>/`
        * Contains technical details (e.g., Database ORM models, 3rd party API clients).
        * Implements interfaces defined by the Domain.
    * **Interface/API Layer**: `/api/<version>/<resource>/`
        * Contains slim route handlers (FastAPI/Flask/Express).
        * Orchestrates calls to Domain and Infrastructure.

## Example

**Before:**

* `/utils/math.py` (contains lifting formulas)
* `/routes.py` (contains everything)
* `/models.py` (contains DB models)

**After:**

* `/domain/lifting/formulas.py` (Pure Wilks/IPF logic)
* `/infrastructure/db/models.py` (SQLAlchemy/Pydantic models)
* `/api/v1/entries/routes.py` (Slim endpoints for lifting entries)
