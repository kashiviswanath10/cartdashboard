# CartCompass-BI — E-Commerce Business Intelligence Dashboard

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.0%2B-000000?logo=flask&logoColor=white)](https://palletsprojects.com/p/flask/)
[![SQLite](https://img.shields.io/badge/SQLite-3-003B57?logo=sqlite&logoColor=white)](https://www.sqlite.org/)
[![Pandas](https://img.shields.io/badge/Pandas-2.0%2B-150458?logo=pandas&logoColor=white)](https://pandas.pydata.org/)
[![Chart.js](https://img.shields.io/badge/Chart.js-4.4-FF6384?logo=chartdotjs&logoColor=white)](https://www.chartjs.org/)
[![Tests](https://img.shields.io/badge/Tests-18%20Passed-10b981?logo=pytest&logoColor=white)](https://docs.pytest.org/)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

An executive, management-oriented E-Commerce Business Intelligence (BI) dashboard designed for college academic reviews and professional GitHub portfolios.

CartCompass-BI analyzes overall business performance using key performance indicators (KPIs), monthly revenue trajectories, product category breakdowns, regional sales distributions, and period-over-period growth metrics.

> **Notice:** All records in this project are generated using a reproducible synthetic e-commerce data pipeline (`seed=42`). The project does not claim to represent any actual commercial entity.

---

## Table of Contents
1. [Key Features](#1-key-features)
2. [Technology Stack](#2-technology-stack)
3. [Architecture Overview](#3-architecture-overview)
4. [Folder Structure](#4-folder-structure)
5. [Database Design](#5-database-design)
6. [Business Intelligence KPIs](#6-business-intelligence-kpis)
7. [Installation & Setup (Windows PowerShell)](#7-installation--setup-windows-powershell)
8. [Running the Application](#8-running-the-application)
9. [Running Automated Tests](#9-running-automated-tests)
10. [Generating Static Reports (Matplotlib)](#10-generating-static-reports-matplotlib)
11. [Troubleshooting](#11-troubleshooting)
12. [Publishing to GitHub](#12-publishing-to-github)
13. [Future Roadmap](#13-future-roadmap)

---

## 1. Key Features

- **Executive KPI Cards**: Real-time cards for Gross Sales, Realized Net Sales, Total Orders, Average Order Value (AOV), Total Discounts, Returns Refunded, and Period Growth.
- **Dynamic Chart.js Visualizations**:
  1. *Monthly Net Revenue Trend*: Smooth line chart with gradient fill and dual-series gross vs. net tracking.
  2. *Period-over-Period Performance*: Side-by-side grouped comparison against previous baseline periods.
  3. *Revenue by Category*: Horizontal bar chart highlighting category contribution.
  4. *Regional Sales Performance*: Geographical distribution of sales volume and AOV.
  5. *Order Fulfillment Status*: Doughnut breakdown of Delivered, Shipped, Pending, and Cancelled orders.
- **Configurable Currency Switcher**: Instant toggle between Indian Rupee (**₹ INR**, default) and US Dollar (**$ USD**) with live number formatting.
- **Flexible Timeframe Filtering**: Quick presets (*All Time*, *Last 12M*, *Last 6M*, *Q4 2025*) plus custom `start_date` and `end_date` date pickers.
- **Policy Control**: Toggle between *Realized Sales* (Delivered only) and *Active Orders* (Delivered + Shipped + Pending).
- **Publication-Grade Static Charts**: Generates high-resolution Matplotlib PNG charts in `analysis/outputs/`.
- **Zero-Dependency Lightweight Backend**: Built using Python's built-in `sqlite3` engine—no external database servers (MySQL or Postgres) required.

---

## 2. Technology Stack

| Layer | Technologies Used | Description |
| :--- | :--- | :--- |
| **Frontend** | HTML5, Modern CSS3, JavaScript (ES6+) | Vanilla CSS design system, responsive layout, Google Fonts (Inter & Outfit). |
| **Interactive Charts** | Chart.js 4.4 | Browser-side interactive, responsive visualizations. |
| **Backend API** | Python, Flask 3.1 | RESTful API blueprints, parameterized SQL execution, secure error handling. |
| **Database** | SQLite 3 (`sqlite3`) | Relational database with enforced foreign keys and performance indexes. |
| **Data Analysis** | Pandas, NumPy | Data cleaning pipeline, KPI aggregation, and validation. |
| **Static Reporting** | Matplotlib 3.11 | Headless generation of publication-quality static chart artifacts. |
| **Testing** | pytest 9.1 | 18 unit and integration tests with isolated test databases. |

---

## 3. Architecture Overview

CartCompass-BI follows a clean, modular tiered architecture:

```
┌────────────────────────────────────────────────────────┐
│           Presentation Layer (HTML5/CSS3/JS)           │
│  - KPI Cards       - Interactive Chart.js   - Filters  │
└───────────────────────────▲────────────────────────────┘
                            │ JSON REST API
┌───────────────────────────▼────────────────────────────┐
│            Flask API Layer (backend/app.py)            │
│  - /api/health     - /api/kpis      - /api/revenue/*   │
│  - /api/categories - /api/regions   - /api/status-*    │
└───────────────────────────▲────────────────────────────┘
                            │ Parameterized SQL
┌───────────────────────────▼────────────────────────────┐
│      Data Access & Analytics (backend/services)        │
│  - analytics.py: KPI formulas & Period-over-Period     │
│  - db.py: SQLite connection pool & PRAGMA foreign keys │
└───────────────────────────▲────────────────────────────┘
                            │
┌───────────────────────────▼────────────────────────────┐
│              SQLite Storage (cartcompass.db)           │
│  - products (28)   - orders (750)   - order_items(1300)│
└────────────────────────────────────────────────────────┘
```

---

## 4. Folder Structure

```
CartCompass-BI/
├── .gitignore                      # Git ignore rules (DBs, pycache, envs)
├── .env.example                    # Sample environment configurations
├── README.md                       # Complete documentation & run guide
├── requirements.txt                # Python package dependencies
├── cartcompass.db                  # SQLite runtime database
├── data/
│   ├── raw/                        # Generated raw CSV datasets
│   │   ├── products.csv
│   │   ├── orders.csv
│   │   └── order_items.csv
│   └── processed/                  # Cleaned master tables & summaries
│       ├── products_clean.csv
│       ├── orders_clean.csv
│       ├── order_items_clean.csv
│       ├── ecommerce_master_clean.csv
│       └── kpis_summary.json
├── database/
│   ├── schema.sql                  # DDL schema with constraints & indexes
│   └── init_db.py                  # Synthetic data generator & DB initializer
├── backend/
│   ├── app.py                      # Flask factory, routes, and frontend server
│   ├── config.py                   # App configurations & environment defaults
│   ├── db.py                       # SQLite connection manager with FK enforcement
│   ├── routes/
│   │   ├── kpis.py                 # GET /api/kpis
│   │   ├── revenue.py              # GET /api/revenue/monthly & /api/revenue/growth
│   │   ├── categories.py           # GET /api/categories
│   │   └── regions.py              # GET /api/regions
│   └── services/
│       └── analytics.py            # Business logic, SQL queries, period growth
├── analysis/
│   ├── clean_data.py               # Data validation, cleaning, and export
│   ├── calculate_kpis.py           # Pandas KPI calculations & summaries
│   ├── generate_charts.py          # Static Matplotlib chart generation
│   └── outputs/                    # Exported high-res PNG static charts
│       ├── monthly_revenue_trend.png
│       ├── category_revenue_distribution.png
│       ├── regional_performance.png
│       ├── order_status_breakdown.png
│       └── period_comparison.png
├── frontend/
│   ├── index.html                  # Dashboard UI layout
│   ├── css/
│   │   └── style.css               # Modern design tokens, cards, responsive layout
│   ├── js/
│   │   └── script.js               # Chart.js controller, currency switcher, filters
│   └── assets/                     # Icons and static web assets
├── tests/
│   ├── test_kpis.py                # Unit tests for KPI formulas & edge cases
│   └── test_api.py                 # Integration tests for Flask endpoints & SQLite
└── docs/
    └── KPI_DEFINITIONS.md          # Comprehensive KPI formulas & methodology
```

---

## 5. Database Design

SQLite database: `cartcompass.db`. Foreign keys are enabled on every connection via `PRAGMA foreign_keys = ON;`.

### Schema Summary

#### 1. `products`
| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `product_id` | INTEGER | PRIMARY KEY | Unique product identifier |
| `product_name` | TEXT | NOT NULL | Item commercial title |
| `category` | TEXT | NOT NULL | Catalog category (e.g., Electronics) |

#### 2. `orders`
| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `order_id` | INTEGER | PRIMARY KEY | Unique order number |
| `order_date` | TEXT | NOT NULL | ISO format date (`YYYY-MM-DD`) |
| `order_status` | TEXT | NOT NULL | `delivered`, `shipped`, `pending`, `cancelled` |
| `region` | TEXT | NOT NULL | Geographic region (`North`, `South`, `East`, `West`, `Central`) |

#### 3. `order_items`
| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `item_id` | INTEGER | PRIMARY KEY | Unique order line identifier |
| `order_id` | INTEGER | NOT NULL, FK -> `orders(order_id)` | Linked order |
| `product_id` | INTEGER | NOT NULL, FK -> `products(product_id)` | Linked product |
| `quantity` | INTEGER | NOT NULL, CHECK(`quantity > 0`) | Number of units purchased |
| `unit_price` | REAL | NOT NULL, CHECK(`unit_price >= 0`) | Selling price per unit |
| `discount` | REAL | NOT NULL, DEFAULT 0, CHECK(`discount >= 0`) | Promotional discount amount |
| `return_amount`| REAL | NOT NULL, DEFAULT 0, CHECK(`return_amount >= 0`) | Refund amount on returns |

#### Performance Indexes
- `idx_orders_order_date` on `orders(order_date)`
- `idx_orders_order_status` on `orders(order_status)`
- `idx_orders_region` on `orders(region)`
- `idx_order_items_order_id` on `order_items(order_id)`
- `idx_order_items_product_id` on `order_items(product_id)`
- `idx_products_category` on `products(category)`

---

## 6. Business Intelligence KPIs

| Metric | Formula | Business Policy |
| :--- | :--- | :--- |
| **Gross Sales** | $\sum (\text{Quantity} \times \text{Unit Price})$ | Pre-discount sales value of eligible orders. |
| **Discount Amount** | $\sum \text{Discount}$ | Total promotional reductions (currency amounts). |
| **Return Amount** | $\sum \text{Return Amount}$ | Total customer refunds on delivered orders. |
| **Net Sales** | $\text{Gross} - \text{Discount} - \text{Return}$ | Realized revenue from finalized orders. |
| **Total Orders** | $\text{COUNT}(\text{DISTINCT } \text{order\_id})$ | Distinct orders count (multi-item orders counted once). |
| **Average Order Value (AOV)** | $\frac{\text{Net Sales}}{\text{Total Orders}}$ | Safe zero handling ($0.00$ if orders $= 0$). |
| **Revenue Growth (%)** | $\frac{\text{Current Net} - \text{Prior Net}}{\text{Prior Net}} \times 100$ | Returns `N/A` if previous period net sales $\le 0$. |

For comprehensive formula derivations, cohort rules, and limitations, refer to [docs/KPI_DEFINITIONS.md](docs/KPI_DEFINITIONS.md).

---

## 7. Installation & Setup (Windows PowerShell)

### Prerequisites
- Windows 10 or 11
- Python 3.10 or higher installed (verify via `py --version` or `python --version`)
- Git installed (verify via `git --version`)

### Step 1: Open PowerShell and Navigate to the Project
```powershell
cd u:\CartCompass-BI
```

### Step 2: (Optional) Create and Activate a Virtual Environment
```powershell
# Create virtual environment named .venv
py -m venv .venv

# Activate in PowerShell
.\.venv\Scripts\Activate.ps1
```

> **Note on PowerShell Execution Policy:** If you encounter a script execution error, run:
> `Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned`

### Step 3: Install Required Dependencies
```powershell
py -m pip install -r requirements.txt
```

---

## 8. Running the Application

### Step 1: Initialize Database and Generate Synthetic Data
```powershell
py database/init_db.py --force
```
*Output: Generates 750 orders, 28 products, and 1,300 order items across 14 months, creating `cartcompass.db`.*

### Step 2: Launch the Flask Backend & Dashboard
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

### Step 3: Open the Dashboard in Your Browser
Visit your local URL:
```
http://127.0.0.1:5000
```

---

## 9. Running Automated Tests

Run the complete test suite using `pytest`:

```powershell
py -m pytest -v
```

### Expected Output:
```
============================= test session starts =============================
platform win32 -- Python 3.14.7, pytest-9.1.1
collected 18 items

tests/test_api.py::test_foreign_key_enforcement PASSED                   [  5%]
tests/test_api.py::test_health_endpoint PASSED                           [ 11%]
tests/test_api.py::test_kpis_endpoint PASSED                             [ 16%]
tests/test_api.py::test_kpis_date_filtering PASSED                       [ 22%]
tests/test_api.py::test_monthly_revenue_endpoint PASSED                  [ 27%]
tests/test_api.py::test_categories_endpoint PASSED                       [ 33%]
tests/test_api.py::test_regions_endpoint PASSED                          [ 38%]
tests/test_api.py::test_revenue_growth_endpoint PASSED                   [ 44%]
tests/test_api.py::test_status_distribution_endpoint PASSED              [ 50%]
tests/test_api.py::test_invalid_date_validation_error PASSED             [ 55%]
tests/test_api.py::test_nonexistent_api_endpoint_404 PASSED              [ 61%]
tests/test_kpis.py::test_gross_and_net_sales_calculation PASSED          [ 66%]
tests/test_kpis.py::test_cancelled_order_exclusion PASSED                [ 72%]
tests/test_kpis.py::test_distinct_order_counting PASSED                  [ 77%]
tests/test_kpis.py::test_average_order_value PASSED                      [ 83%]
tests/test_kpis.py::test_growth_rate_zero_denominator PASSED             [ 88%]
tests/test_kpis.py::test_monthly_and_category_aggregation PASSED         [ 94%]
tests/test_kpis.py::test_clean_and_validate_edge_cases PASSED            [100%]

============================= 18 passed in 1.23s ==============================
```

---

## 10. Generating Static Reports (Matplotlib)

To re-run the offline data processing and static chart generation pipeline:

```powershell
# 1. Run Data Validation & Cleaning
py analysis/clean_data.py

# 2. Run KPI Calculation Engine
py analysis/calculate_kpis.py

# 3. Generate High-Resolution Matplotlib Visualizations
py analysis/generate_charts.py
```

The resulting chart artifacts will be saved in `analysis/outputs/`:
- `monthly_revenue_trend.png`
- `category_revenue_distribution.png`
- `regional_performance.png`
- `order_status_breakdown.png`
- `period_comparison.png`

---

## 11. Troubleshooting

| Issue | Cause | Solution |
| :--- | :--- | :--- |
| `python was not found` | Windows Store app alias priority. | Use `py` command instead of `python` (e.g. `py backend/app.py`). |
| `UnicodeEncodeError: 'charmap'` | Windows default code page 1252 printing `₹`. | Handled automatically in codebase via `sys.stdout.reconfigure(encoding='utf-8')`. |
| `Address already in use (Port 5000)` | Another process is occupying port 5000. | Change `PORT=5050` in `.env` or run `py -c "from backend.app import app; app.run(port=5050)"`. |
| Empty charts on load | Database not populated. | Run `py database/init_db.py --force` to regenerate sample data. |

---

## 12. Publishing to GitHub

To push this repository to your personal GitHub account:

```powershell
# Check current git status
git status

# Add all project files
git add .

# Create initial commit
git commit -m "feat: complete CartCompass-BI dashboard implementation"

# Add your GitHub remote repository
git remote add origin https://github.com/<YOUR_USERNAME>/CartCompass-BI.git

# Set default branch and push
git branch -M main
git push -u origin main
```

---

## 13. Future Roadmap

- [ ] Export executive summary reports to PDF.
- [ ] Add inventory re-order alerts based on stock depletion velocity.
- [ ] Add multi-year comparative forecast modeling using statsmodels/ARIMA.
- [ ] User role-based access control (Admin vs Analyst).

---

## License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.
