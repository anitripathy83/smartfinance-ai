# SmartFinance AI 🤖💰
### AI-Powered Financial Intelligence ERP Module for Odoo 19

> Built for the Odoo Hackathon 2026 | Category: Business, Finance & Workforce ERP

---

## 🎯 What is SmartFinance AI?

SmartFinance AI is a custom Odoo module that transforms your ERP into an intelligent financial advisor. It automatically scans data across 6 Odoo modules every 24 hours, generates AI-powered insights, scores your business health, and answers financial questions in plain English — all without any manual input.

**The core idea:** A finance manager opens Odoo in the morning and immediately sees what needs attention, what is at risk, and what to do about it.

---

## ✨ Features

### 📊 KPI Dashboard
A live, unified dashboard showing every critical business metric in one screen:
- Cash inflow and outflow (last 30 days)
- Net cash position
- Overdue invoices count and total value
- CRM pipeline value and open deals
- Active employee headcount
- Overall financial health score

### 🚨 AI Insights Engine
A Python engine that runs daily and automatically:
- Detects overdue invoices and calculates total outstanding amount
- Monitors cash flow trends and flags declining inflow
- Identifies stale CRM opportunities at risk
- Flags incomplete employee profiles and departments without managers
- Tracks purchase orders awaiting vendor bills
- Color-codes alerts by severity: Critical, High, Medium, Low

Each insight includes what the problem is (with exact AED figures), why it matters, and a step-by-step recommended action.

### 🏥 Financial Health Score
A composite 0-100 score updated daily, calculated across 5 weighted dimensions:

| Dimension | Weight | How it is scored |
|-----------|--------|------------------|
| Cash Flow | 35% | Inflow vs outflow ratio |
| Invoicing | 30% | Overdue invoice rate |
| Workforce | 20% | Employee profile completeness |
| CRM | 10% | Pipeline win rate |
| Purchasing | 5% | Unbilled PO rate |

### 🤖 AI Assistant
A conversational interface that answers financial questions using live Odoo data:
- "What are my biggest financial risks?"
- "How is my cash flow this month?"
- "What do you recommend I do?"
- "What is my financial health score?"
- "How is my CRM pipeline?"

Quick-action buttons for instant answers — no typing required.

### 📋 One-Click Financial Report
Generates a complete executive financial summary in one click:
- Full metrics snapshot across all modules
- Auto-generated executive summary with key risks highlighted
- Timestamped and ready to share with management
- Historical reports saved for trend comparison

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
│   └── financial_report.py     # One-click report generator
│
├── views/
│   ├── insight_views.xml       # AI Insights kanban/list/form
│   ├── dashboard_views.xml     # Health Score views
│   ├── chat_views.xml          # AI Assistant interface
│   ├── kpi_dashboard_views.xml # KPI Dashboard form
│   ├── report_views.xml        # Financial Report form
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
cp -r smartfinance-ai /path/to/odoo/addons/
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
| Health Score | 0-100 score with dimension breakdown |
| AI Assistant | Chat interface with quick-action buttons |
| Financial Report | Auto-generated executive summary |

---

## 🛠️ Tech Stack

- **Backend:** Python 3, Odoo ORM
- **Frontend:** Odoo XML Views, QWeb
- **Database:** PostgreSQL
- **Platform:** Odoo 19 Community Edition

---

## 👨‍💻 Author

**The Odoo-Crewz**

Built for the Odoo Hackathon 2026  
GitHub: [@anitripathy83](https://github.com/anitripathy83)

---

## 📄 License

LGPL-3.0