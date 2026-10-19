# CartCompass-BI — E-Commerce Business Intelligence Dashboard

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.0%2B-000000?logo=flask&logoColor=white)](https://palletsprojects.com/p/flask/)
[![SQLite](https://img.shields.io/badge/SQLite-3-003B57?logo=sqlite&logoColor=white)](https://www.sqlite.org/)
[![Pandas](https://img.shields.io/badge/Pandas-2.0%2B-150458?logo=pandas&logoColor=white)](https://pandas.pydata.org/)
[![Chart.js](https://img.shields.io/badge/Chart.js-4.4-FF6384?logo=chartdotjs&logoColor=white)](https://www.chartjs.org/)
[![Tests](https://img.shields.io/badge/Tests-20%20Passed-10b981?logo=pytest&logoColor=white)](https://docs.pytest.org/)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

An executive, multi-page **E-Commerce Business Intelligence (BI) Dashboard** engineered for management performance reviews, academic project evaluations, and GitHub portfolio showcases.

CartCompass-BI analyzes high-level store performance through real-time Key Performance Indicators (KPIs), multi-year monthly revenue cash flows, product category contributions, geographical delivery territory analytics, period-over-period baseline growth rates, dynamic CSV dataset upload/recalculation, and automated narrative executive insights.

> **Notice:** All transaction records in this repository are generated through a deterministic, reproducible synthetic e-commerce data pipeline (`seed=42`). The data does not represent any real-world commercial entity.

---

## Table of Contents
1. [Executive Dashboard Pages](#1-executive-dashboard-pages)
2. [Design System & Aesthetics](#2-design-system--aesthetics)
3. [Technology Stack](#3-technology-stack)
4. [Architecture Overview](#4-architecture-overview)
5. [Folder Structure](#5-folder-structure)
6. [Database Design & Performance Indexes](#6-database-design--performance-indexes)
7. [Business Intelligence KPIs & Mathematical Formulations](#7-business-intelligence-kpis--mathematical-formulations)
8. [Installation & Setup (Windows PowerShell)](#8-installation--setup-windows-powershell)
9. [Running the Application](#9-running-the-application)
10. [Automated Test Suite (pytest)](#10-automated-test-suite-pytest)
11. [Publication-Grade Charts Engine (Matplotlib)](#11-publication-grade-charts-engine-matplotlib)
12. [Troubleshooting Guide](#12-troubleshooting-guide)
13. [Academic Review & Portfolio Checklist](#13-academic-review--portfolio-checklist)
14. [License](#14-license)

---

## 1. Executive Dashboard Pages

CartCompass-BI is structured as a cohesive, 6-page enterprise analytics application:

| Page | URL Route | Description & Visualizations |
| :--- | :--- | :--- |
| **1. Overview** | `/` or `/index.html` | **Executive Cockpit**: Real-time KPI summary (Gross Sales, Net Sales, Orders, AOV, YoY Growth), glowing 14-month revenue trajectory line chart, category revenue distribution doughnut, regional performance horizontal bar chart, and category audit table. |
| **2. Revenue Analytics** | `/revenue` or `/revenue.html` | **Cash Flow & Margin Analysis**: Net cash realization rate %, spread between booked invoices and realized proceeds, dual-series gross vs. net trajectory, grouped current vs. previous period comparison bar chart, and 14-month financial ledger table. |
| **3. Categories** | `/categories` or `/categories.html` | **Merchandise Portfolio**: Top-performing vertical highlights (by net revenue and unit volume), horizontal bar comparisons with value callouts, portfolio percentage share doughnut, and complete vertical performance audit table with YoY growth. |
| **4. Regions** | `/regions` or `/regions.html` | **Geographical Logistics**: Leading territorial hub metrics, revenue volume horizontal bar chart, dual-axis territory comparison (AOV vs. Order Volume), and regional delivery efficiency table with target pacing. |
| **5. Reports & Audit** | `/reports` or `/reports.html` | **Formal Management Audit**: 7 executive KPI cards, data-driven narrative takeaway boxes, fulfillment status distribution doughnut, publication-grade Matplotlib static chart gallery (16:9 uniform widescreen ratio), formal KPI mathematical equations, and one-click Print / Export to PDF. |
| **6. Upload Data** | `/upload` or `/upload.html` | **Dynamic Data Ingestion**: Drag-and-drop CSV dataset ingestion pipeline with batch validation, SQLite database updates, automated recomputation of all store KPIs and analytical charts, and downloadable sample CSV templates. |

---

## 2. Design System & Aesthetics

The frontend features a bespoke executive dark theme styled after high-end market intelligence terminals:

- **Curated Color Palette**:
  - Background Base: `#0A0E1A` (Deep Obsidian Navy)
  - Card Containers: `#12192B` (Executive Slate Blue)
  - Card Borders & Dividers: `#1D2844` / `#2B3B64`
  - Active Pills & Brand Highlight: `#FF6B00` (Vibrant Tangerine Orange)
  - Realized Value & Trend Accents: `#00D2D3` (Cyan) and `#10B981` (Emerald Green)
  - Warnings & Deductions: `#F43F5E` (Rose Red) and `#F59E0B` (Amber)
- **Modern Typography**: Embedded Google Fonts pairing **Outfit** (headings, bold metrics) with **Inter** (tables, labels, narrative text).
- **Dual-Currency Engine**: Instant toggle between Indian Rupee (**₹ INR**, default) and US Dollar (**$ USD**) with live recalculation and regional formatting (`₹ Lakhs/Cr` vs `$k/$M`).
- **Offline / Standalone Fallback**: Integrated client-side dataset fallback (`DEMO_DATA`). If the Flask backend is unreachable or the application is opened statically (e.g. GitHub Pages or file server), the entire interface functions seamlessly with full sample metrics and charts.
- **Print & PDF Mode**: Tailored `@media print` stylesheets strip dark backgrounds and sidebars, automatically generating a formal black-and-white management document suitable for submission.

---

## 3. Technology Stack

| Component | Technology | Rationale & Specifications |
| :--- | :--- | :--- |
| **Frontend Structure** | HTML5 (Semantic) | Accessible, lightweight semantic structure with mobile drawer navigation. |
| **Styling & Theme** | Modern Vanilla CSS3 | Custom design system using CSS variables, flexbox, CSS grid, and media queries. |
| **Interactive Visualizations** | Chart.js 4.4 | GPU-accelerated responsive canvas charts with custom tooltips and dark theme defaults. |
| **Backend API** | Python 3.10+, Flask 3.1 | Modular application factory pattern using Flask Blueprints with parameterized queries. |
| **Relational Database** | SQLite 3 (`sqlite3`) | Embedded SQL database with foreign key enforcement and multi-column indexes. |
| **Data Analysis** | Pandas 2.0+, NumPy | Data cleaning pipeline, aggregate KPI formulations, and cohort transformations. |
| **Static Reporting** | Matplotlib 3.11 | Headless static chart generation exporting uniform 16:9 publication PNGs. |
| **Test Suite** | pytest 9.1 | 20 automated unit and integration tests with isolated SQLite fixtures. |

---

## 4. Architecture Overview

CartCompass-BI implements a decoupled, 3-tier architecture:

```
┌────────────────────────────────────────────────────────────────────────┐
│             Presentation Tier (HTML5, Modern CSS3, JavaScript)         │
│  - 6 Multi-Page Views   - Dark Theme System   - Chart.js Visualizations│
│  - ₹ / $ Currency Engine - Live Status Pill    - Print-to-PDF Styles    │
│  - Drag-and-Drop Ingestion UI                  - Real-Time Recalculation│
└───────────────────────────────────▲────────────────────────────────────┘
                                    │ JSON REST API / Static Assets
┌───────────────────────────────────▼────────────────────────────────────┐
│                    Flask API Tier (backend/app.py)                     │
│  - /api/health          - /api/kpis           - /api/revenue/monthly   │
│  - /api/categories      - /api/regions        - /api/status-distribution│
│  - /api/upload          - /api/template/sample-csv                     │
│  - /api/chart-images/*  - Clean URL Routing   - Parameter Validation   │
└───────────────────────────────────▲────────────────────────────────────┘
                                    │ Parameterized SQL Queries
┌───────────────────────────────────▼────────────────────────────────────┐
│              Data Access & Analytics (backend/services)                │
│  - analytics.py: GAAP realized formulas, baseline growth, aggregations │
│  - db.py: SQLite connection manager with PRAGMA foreign_keys = ON      │
└───────────────────────────────────▲────────────────────────────────────┘
                                    │
┌───────────────────────────────────▼────────────────────────────────────┐
│                  Relational Storage (cartcompass.db)                   │
│  - products (28)        - orders (750)        - order_items (1,300)    │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 5. Folder Structure

```
CartCompass-BI/
├── frontend/                       # Client-side presentation layer
│   ├── index.html                  # Page 1: Overview Dashboard Cockpit
│   ├── revenue.html                # Page 2: Revenue & Cash Flow Analytics
│   ├── categories.html             # Page 3: Category Performance & Share
│   ├── regions.html                # Page 4: Regional Logistics & Hubs
│   ├── reports.html                # Page 5: Executive Audit & Reports
│   ├── upload.html                 # Page 6: Dynamic CSV Upload & Ingestion Engine
│   ├── assets/                     # Static client-side assets
│   │   └── charts/                 # Synchronized 16:9 publication charts
│   ├── css/
│   │   └── style.css               # Executive dark design system & print styles
│   └── js/
│       ├── common.js               # Shared state, currency switcher, demo fallback
│       ├── overview.js             # Overview page interactive controllers
│       ├── revenue.js              # Revenue analytics controllers
│       ├── categories.js           # Category breakdown controllers
│       ├── regions.js              # Regional performance controllers
│       ├── reports.js              # Executive audit, insights & print handlers
│       └── upload.js               # CSV drag/drop, batch upload & recalculation handler
├── backend/                        # Server application layer
│   ├── app.py                      # Application factory & clean URL router
│   ├── config.py                   # Configuration defaults & environment settings
│   ├── db.py                       # SQLite connection pool with FK enforcement
│   ├── routes/                     # Modular REST API endpoints (Blueprints)
│   │   ├── kpis.py                 # GET /api/kpis
│   │   ├── revenue.py              # GET /api/revenue/monthly & /api/revenue/growth
│   │   ├── categories.py           # GET /api/categories
│   │   ├── regions.py              # GET /api/regions
│   │   └── upload.py               # POST /api/upload & GET /api/template/sample-csv
│   └── services/
│       └── analytics.py            # KPI business logic & SQL query formulations
├── database/                       # Relational schema and seed scripts
│   ├── schema.sql                  # DDL table schemas, constraints & indexes
│   └── init_db.py                  # Synthetic data generator & DB initializer
├── analysis/                       # Offline data science & report generation
│   ├── clean_data.py               # Data validation, cleaning, and master export
│   ├── calculate_kpis.py           # Pandas KPI calculations & summaries
│   ├── generate_charts.py          # Matplotlib 16:9 static chart generator
│   └── outputs/                    # Exported high-res PNG static charts (300 DPI)
├── data/                           # Data storage
│   ├── raw/                        # Generated raw CSV datasets
│   ├── processed/                  # Cleaned master tables & JSON/CSV summaries
│   └── sample_ecommerce_data.csv   # Template sample CSV file for batch imports
├── tests/                          # Automated verification suite
│   ├── test_kpis.py                # Unit tests for KPI calculations & edge cases
│   └── test_api.py                 # Integration tests for Flask endpoints & DB
├── docs/                           # Project documentation
│   └── KPI_DEFINITIONS.md          # Comprehensive mathematical formulas & methodology
├── .env.example                    # Sample environment configurations
├── .gitignore                      # Git ignore specifications
├── LICENSE                         # MIT License
├── requirements.txt                # Python package dependencies
└── README.md                       # Complete project documentation
```

---

## 6. Database Design & Performance Indexes

The SQLite database (`cartcompass.db`) adheres to relational 3NF design principles. Foreign keys are enforced on every database connection via `PRAGMA foreign_keys = ON;`.

### Table Schemas

#### 1. `products`
| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `product_id` | INTEGER | PRIMARY KEY | Unique product identifier |
| `product_name` | TEXT | NOT NULL | Item commercial title |
| `category` | TEXT | NOT NULL | Catalog vertical (e.g. *Electronics*, *Fashion & Apparel*) |

#### 2. `orders`
| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `order_id` | INTEGER | PRIMARY KEY | Unique order number |
| `order_date` | TEXT | NOT NULL | ISO format date (`YYYY-MM-DD`) |
| `order_status` | TEXT | NOT NULL | `delivered`, `shipped`, `pending`, `cancelled` |
| `region` | TEXT | NOT NULL | Geographic hub (`North`, `South`, `East`, `West`, `Central`) |

#### 3. `order_items`
| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `item_id` | INTEGER | PRIMARY KEY | Unique order item line identifier |
| `order_id` | INTEGER | NOT NULL, FK -> `orders(order_id)` | Linked order |
| `product_id` | INTEGER | NOT NULL, FK -> `products(product_id)` | Linked product |
| `quantity` | INTEGER | NOT NULL, CHECK(`quantity > 0`) | Number of units purchased |
| `unit_price` | REAL | NOT NULL, CHECK(`unit_price >= 0`) | Unit selling price |
| `discount` | REAL | NOT NULL, DEFAULT 0, CHECK(`discount >= 0`) | Promotional discount applied |
| `return_amount`| REAL | NOT NULL, DEFAULT 0, CHECK(`return_amount >= 0`) | Refund amount on returns |

### Performance Indexes
To ensure fast execution on analytical aggregations, the following indexes are active:
- `idx_orders_order_date` on `orders(order_date)`
- `idx_orders_order_status` on `orders(order_status)`
- `idx_orders_region` on `orders(region)`
- `idx_order_items_order_id` on `order_items(order_id)`
- `idx_order_items_product_id` on `order_items(product_id)`
- `idx_products_category` on `products(category)`

---

## 7. Business Intelligence KPIs & Mathematical Formulations

CartCompass-BI implements strict accounting and business rules:

| Metric | Mathematical Formulation | Enforced Business Logic |
| :--- | :--- | :--- |
| **Gross Booked Sales** | $$\sum (\text{Quantity} \times \text{Unit Price})$$ | Invoiced transaction value prior to promotional deductions or returns. |
| **Promotional Discounts** | $$\sum \text{Discount}$$ | Aggregate promotional value subtracted from customer invoices. |
| **Refunded Returns** | $$\sum \text{Return Amount}$$ | Total return refunds granted to customers on delivered orders. |
| **Realized Net Sales** | $$\text{Gross} - \text{Discounts} - \text{Returns}$$ | Realized cash inflows. Cancelled orders are strictly excluded. |
| **Distinct Order Count** | $$\text{COUNT}(\text{DISTINCT } \text{order\_id})$$ | Unique orders counted once regardless of the number of line items. |
| **Average Order Value (AOV)** | $$\frac{\text{Net Sales}}{\text{Total Orders}}$$ | Handled with zero-division safety ($0.00$ if eligible order count is $0$). |
| **Period Growth Rate (%)** | $$\frac{\text{Current Net} - \text{Prior Net}}{\text{Prior Net}} \times 100$$ | Evaluated against an identical-duration previous period. Returns `N/A` if baseline $\le 0$. |

*For complete mathematical derivations and edge-case proofs, see [docs/KPI_DEFINITIONS.md](docs/KPI_DEFINITIONS.md).*

---

## 8. Installation & Setup (Windows PowerShell)

### Prerequisites
- Windows 10 or 11
- Python 3.10 or higher installed (check with `py --version`)
- Git installed (check with `git --version`)

### Step 1: Open PowerShell and Navigate to the Repository
```powershell
cd u:\CartCompass-BI
```

### Step 2: (Recommended) Create and Activate Virtual Environment
```powershell
# Create virtual environment
py -m venv .venv

# Activate virtual environment
.\.venv\Scripts\Activate.ps1
```

> **PowerShell Script Policy Tip:** If script execution is blocked on your system, enable it for your current user:
> ```powershell
> Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
> ```

### Step 3: Install Required Python Packages
```powershell
py -m pip install -r requirements.txt
```

---

## 9. Running the Application

### Step 1: Initialize the SQLite Database
```powershell
py database/init_db.py --force
```
*Creates `cartcompass.db` populated with 750 orders, 28 products, and 1,300 order items across 14 months.*

### Step 2: Start the Flask Backend Server
```powershell
py backend/app.py
```
*Console output:*
```
Starting CartCompass-BI on http://127.0.0.1:5000
 * Serving Flask app 'backend.app'
 * Debug mode: on
 * Running on http://127.0.0.1:5000
```

### Step 3: Access the Multi-Page Dashboard in Your Browser
Open your browser and navigate to:
- **Overview Dashboard**: `http://127.0.0.1:5000/`
- **Revenue Analytics**: `http://127.0.0.1:5000/revenue`
- **Category Intelligence**: `http://127.0.0.1:5000/categories`
- **Regional Performance**: `http://127.0.0.1:5000/regions`
- **Executive Audit & Reports**: `http://127.0.0.1:5000/reports`
- **Dynamic Upload & Ingestion**: `http://127.0.0.1:5000/upload`

---

## 10. Automated Test Suite (pytest)

Run the automated test suite to verify database integrity, KPI calculations, and API routes:

```powershell
py -m pytest -v
```

### Test Suite Execution Output
```
============================= test session starts =============================
platform win32 -- Python 3.14.7, pytest-9.1.1
collected 20 items

tests/test_api.py::test_foreign_key_enforcement PASSED                   [  5%]
tests/test_api.py::test_health_endpoint PASSED                           [ 10%]
tests/test_api.py::test_kpis_endpoint PASSED                             [ 15%]
tests/test_api.py::test_kpis_date_filtering PASSED                       [ 20%]
tests/test_api.py::test_monthly_revenue_endpoint PASSED                  [ 25%]
tests/test_api.py::test_categories_endpoint PASSED                       [ 30%]
tests/test_api.py::test_regions_endpoint PASSED                          [ 35%]
tests/test_api.py::test_revenue_growth_endpoint PASSED                   [ 40%]
tests/test_api.py::test_status_distribution_endpoint PASSED              [ 45%]
tests/test_api.py::test_invalid_date_validation_error PASSED             [ 50%]
tests/test_api.py::test_nonexistent_api_endpoint_404 PASSED              [ 55%]
tests/test_api.py::test_sample_template_download PASSED                  [ 60%]
tests/test_api.py::test_upload_missing_file_error PASSED                 [ 65%]
tests/test_kpis.py::test_gross_and_net_sales_calculation PASSED          [ 70%]
tests/test_kpis.py::test_cancelled_order_exclusion PASSED                [ 75%]
tests/test_kpis.py::test_distinct_order_counting PASSED                  [ 80%]
tests/test_kpis.py::test_average_order_value PASSED                      [ 85%]
tests/test_kpis.py::test_growth_rate_zero_denominator PASSED             [ 90%]
tests/test_kpis.py::test_monthly_and_category_aggregation PASSED         [ 95%]
tests/test_kpis.py::test_clean_and_validate_edge_cases PASSED            [100%]

============================= 20 passed in 2.26s ==============================
```

---

## 11. Publication-Grade Charts Engine (Matplotlib)

To re-run the offline data analysis pipeline and regenerate the high-resolution static charts:

```powershell
# 1. Clean and validate dataset
py analysis/clean_data.py

# 2. Compute aggregated summaries
py analysis/calculate_kpis.py

# 3. Generate uniform 16:9 widescreen chart artifacts
py analysis/generate_charts.py
```

### Exported Publication Visualizations
All charts are exported at 300 DPI with a standardized **16:9 widescreen ratio (3000 × 1687 pixels)** in `analysis/outputs/`:
1. `monthly_revenue_trend.png` — 14-month realized net sales trend with peak annotations.
2. `category_revenue_distribution.png` — Horizontal Pareto bar chart showing net sales across verticals.
3. `regional_performance.png` — Geographical distribution comparing territorial revenue and order count.
4. `order_status_breakdown.png` — Proportional doughnut visualization of fulfillment distribution.
5. `period_comparison.png` — Side-by-side grouped bar comparison between H1 2025 and H2 2025.

---

## 12. Troubleshooting Guide

| Issue Observed | Root Cause | Solution |
| :--- | :--- | :--- |
| `python was not found` | Windows Store app alias precedence. | Use the standard Windows Python launcher `py` (e.g. `py backend/app.py`). |
| `Address already in use: Port 5000` | Port 5000 is occupied by another process. | Change port in `.env` or run `py -c "from backend.app import app; app.run(port=5050)"`. |
| Empty charts or tables in UI | Database not yet initialized. | Run `py database/init_db.py --force` to populate `cartcompass.db`. |
| Browser shows stale styles or charts | Browser HTTP asset caching. | Press `Ctrl + F5` (or `Cmd + Shift + R`) to force a hard refresh. |
| PowerShell script activation error | Restricted script execution policy. | Run `Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned`. |

---

## 13. Academic Review & Portfolio Checklist

- [x] **Relational Schema Integrity**: Enforced foreign keys, check constraints, and non-negative line item pricing.
- [x] **Analytical Rigor**: Strict GAAP cash realization policy (cancelled orders excluded, returns deducted).
- [x] **Executive UI/UX**: Multi-page dark terminal aesthetic, responsive navigation, and dual-currency toggle.
- [x] **Dynamic Data Ingestion**: Drag-and-drop CSV dataset ingestion, batch validation, automated KPI recomputation, and sample template export.
- [x] **Publication Artifacts**: 5 uniform 16:9 Matplotlib charts exported at 300 DPI.
- [x] **Automated Testing**: 20 automated tests passing via `pytest`.
- [x] **Documentation**: Clean README, mathematical derivations (`KPI_DEFINITIONS.md`), and MIT License.

---

## 14. License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for complete details.
