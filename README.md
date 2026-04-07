# SmartFinance AI 🤖💰
### AI-Powered Financial Intelligence ERP Module for Odoo 19

> Built for the Odoo Hackathon 2026 | Category: Business, Finance & Workforce ERP

---

## 🎯 What is SmartFinance AI?

SmartFinance AI is a custom Odoo module that transforms your ERP into an intelligent financial advisor. It automatically scans data across 6 Odoo modules every 24 hours, generates AI-powered insights, scores your business health, benchmarks your KPIs against industry standards, detects cross-module correlations, and answers financial questions in plain English — all without any manual input.

**The core idea:** A finance manager opens Odoo in the morning and immediately sees what needs attention, what is at risk, how they compare to industry, and what to do about it.

---

## ✨ Features (7 Modules)

### 📊 1. KPI Dashboard
A live, unified dashboard showing every critical business metric in one screen:
- Cash inflow and outflow (last 30 days)
- Net cash position
- Overdue invoices count and total value
- CRM pipeline value and open deals
- Active employee headcount
- Overall financial health score

### 🚨 2. AI Insights Engine
A Python engine that runs daily and automatically detects problems across 6 Odoo modules:
- Overdue invoices with total AED value
- Cash flow decline trends
- Stale CRM opportunities at risk
- Incomplete employee profiles
- Departments without managers
- Purchase orders awaiting vendor bills

Each insight includes severity (Critical / High / Medium / Low), full analysis, and step-by-step recommended actions.

### 🏥 3. Financial Health Score
A composite 0-100 score updated daily across 5 weighted dimensions:

| Dimension | Weight | How it is scored |
|-----------|--------|------------------|
| Cash Flow | 35% | Inflow vs outflow ratio |
| Invoicing | 30% | Overdue invoice rate |
| Workforce | 20% | Employee profile completeness |
| CRM | 10% | Pipeline win rate |
| Purchasing | 5% | Unbilled PO rate |

### 🤖 4. AI Assistant
A conversational interface that answers financial questions using live Odoo data:
- Quick-action buttons for instant answers
- Covers overdue invoices, cash flow, CRM pipeline, workforce, risks, and recommendations
- All answers pulled from live Odoo data in real time

### 📋 5. One-Click Financial Report
Generates a complete executive financial summary in one click:
- Full metrics snapshot across all modules
- Auto-generated executive summary with key risks highlighted
- Timestamped and ready to share with management
- Historical reports saved for trend comparison

### 🔗 6. Cross-Module Correlation Engine
Detects statistical relationships between metrics across different Odoo modules using Pearson correlation analysis:

| Correlation | Modules |
|-------------|---------|
| Invoice Volume vs Cash Inflow | Invoicing ↔ Accounting |
| Headcount vs CRM Win Rate | HR ↔ CRM |
| Expense Spikes vs Overdue Invoices | Expenses ↔ Invoicing |
| CRM Pipeline Value vs Cash Inflow | CRM ↔ Accounting |
| Purchase Volume vs Cash Outflow | Purchase ↔ Accounting |

Each correlation includes a score (-1 to +1), strength classification, business interpretation, and recommended action.

### 📈 7. Smart Benchmarking
Compares your live KPIs against industry standard benchmarks and tells you exactly where you stand:

| KPI | Industry Benchmark |
|-----|--------------------|
| Invoice Collection Period | 30 days |
| CRM Win Rate | 20% |
| Overdue Invoice Rate | Less than 10% |
| Cash Flow Ratio | Greater than 1.2x |
| Revenue per Employee | AED 200,000/year |
| Expense to Revenue Ratio | Less than 15% |

Status levels: Outperforming ✅ / On Track 🟡 / Needs Attention ⚠️ / Critical 🔴

---

## 🏗️ Architecture
```
smartfinance_ai/
│
├── models/
│   ├── financial_insight.py    # AI Insight and Health Score models
│   ├── insight_engine.py       # Daily analysis engine (6 analyzers)
│   ├── ai_chat.py              # AI Assistant chat models
│   ├── kpi_dashboard.py        # KPI Dashboard computed fields
│   ├── financial_report.py     # One-click report generator
│   ├── correlation_engine.py   # Cross-module Pearson correlation
│   └── benchmarking.py         # Industry benchmarking engine
│
├── views/
│   ├── insight_views.xml       # AI Insights kanban/list/form
│   ├── dashboard_views.xml     # Health Score views
│   ├── chat_views.xml          # AI Assistant interface
│   ├── kpi_dashboard_views.xml # KPI Dashboard form
│   ├── report_views.xml        # Financial Report form
│   ├── correlation_views.xml   # Correlation Engine views
│   ├── benchmarking_views.xml  # Smart Benchmarking views
│   └── menu_views.xml          # Module menu structure
│
├── security/
│   └── ir.model.access.csv     # Access control rules
│
└── data/
    └── cron_jobs.xml           # Daily analysis scheduler
```

---

## 🔗 Odoo Modules Integrated

| Module | Data Used |
|--------|-----------|
| Accounting | Invoices, payments, journal entries |
| Invoicing | Customer invoices, overdue detection |
| CRM | Opportunities, pipeline value, win rate |
| HR Employees | Headcount, profile completeness, departments |
| Expenses | Employee expense reports, anomaly detection |
| Purchase | Purchase orders, vendor bill status |

---

## 🚀 Installation

### Requirements
- Odoo 19 Community Edition
- Python 3.10+
- PostgreSQL 13+

### Steps

**1. Clone this repository:**
```bash
git clone https://github.com/anitripathy83/smartfinance-ai.git
```

**2. Copy the module to your Odoo addons path:**
```bash
cp -r smartfinance_ai /path/to/odoo/addons/
```

**3. Restart Odoo server:**
```bash
python odoo-bin -c odoo.conf -u smartfinance_ai
```

**4. In Odoo:**
- Go to Settings and activate Developer Mode
- Go to Apps → Update App List
- Search **SmartFinance AI** and click Install

**5. Trigger first analysis:**
- Go to Settings → Technical → Scheduled Actions
- Find **SmartFinance AI — Daily Analysis** → click **Run Manually**

---

## 📸 Module Overview

| Screen | Description |
|--------|-------------|
| KPI Dashboard | Live metrics — cash flow, invoices, CRM, workforce |
| AI Insights | Color-coded alerts grouped by severity |
| Health Score | 0-100 composite score with dimension breakdown |
| AI Assistant | Conversational interface with quick-action buttons |
| Financial Report | Auto-generated executive summary |
| Correlations | Cross-module Pearson correlation analysis |
| Benchmarking | KPI comparison against industry standards |

---

## 🛠️ Tech Stack

- **Backend:** Python 3, Odoo ORM
- **Frontend:** Odoo XML Views, QWeb
- **Database:** PostgreSQL
- **Analytics:** Pearson Correlation Coefficient, Statistical Benchmarking
- **Platform:** Odoo 19 Community Edition

---

## 👨‍💻 Author

**The Odoo-Crewz**

Built for the Odoo Hackathon 2026
GitHub: [@anitripathy83](https://github.com/anitripathy83)

---

## 📄 License

LGPL-3.0
