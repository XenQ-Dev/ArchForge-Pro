# ArchForge Pro

**ArchForge Pro codebase — construction cost estimation for the Indian market**

The estimation platform that runs the whole project — intake, cost modelling, BOQ generation, expense tracking, phase scheduling, ML prediction, and branded PDF delivery — on a desktop-first offline engine built for Indian construction professionals.

Drop the project specs. Define the scope. Run the rule-based estimator. Generate the BOQ. Track real expenses against the estimate. Let the ML engine cross-check the numbers. Send the professional report.

---

## Features

### 1. Rule-based cost estimation engine — not a spreadsheet bolted on

ArchForge Pro keeps estimation logic in `app/controllers/estimation_engine.py`, where it shares cost intelligence, labour norms, quality multipliers, GST schedules, and material rate tables with the BOQ generator, variance engine, and ML predictor. The estimator reads project parameters, applies Indian Standard rates by construction quality (Economy / Standard / Premium / Luxury), runs material quantity schedules, layers labour and equipment percentages, applies contractor margin, and computes GST — all in one pass.

No manual formulas. No broken cell references. No hidden assumptions.

### 2. ML cost prediction — cross-check your estimate

A trained XGBoost model lives alongside a rule-based engine in `app/ml/`. Feed it a project's built-up area, floor count, quality tier, and type — it returns an independent predicted cost and confidence range. Use it to sanity-check the rule-based output or to price projects where detailed BOQ data isn't yet available.

Local inference only. No cloud, no API key, no cost per call.

### 3. BOQ generator — linked to the estimate

Generate a full Bill of Quantities from a saved estimate with one click. Line items carry description, quantity, unit, rate, and amount. Export to PDF (ReportLab, branded layout with charts) or Excel (openpyxl, formatted with header styles and column widths). BOQ items stay linked to the estimate they came from — change the estimate, regenerate the BOQ.

### 4. Expense tracking — actuals against the budget

Log every site expense with date, category, description, amount, and receipt reference. The variance engine computes actual vs. estimated in real time — by component (material, labour, equipment, contractor) and in aggregate. Monthly spend trends surface in the Expense Report automatically.

### 5. Phase timeline — nine standard construction phases

Every project gets nine default phases out of the box: Foundation → Structure → Brickwork → Plumbing → Electrical → Plastering → Flooring → Painting → Finishing & Handover. Track planned and actual start/end dates, completion percentage, and status per phase. The Project Summary Report renders a Gantt chart from this data automatically.

### 6. Five professional PDF reports — with embedded charts

Hit Generate and ArchForge Pro produces a branded, chart-rich PDF. No third-party service, no internet connection required.

| Report | Charts included |
|---|---|
| Cost Estimate Report | Pie (cost distribution) + Bar (component amounts) + Rate analysis |
| BOQ Report | Pie + Bar by work category |
| Expense Report | Pie (by category) + Line (monthly trend) |
| Variance Analysis | Donut (budget utilisation) + Bar (budget vs actual) + Component table |
| Project Summary | Pie + Bar + Phase table + Gantt chart |

### 7. Materials database

Maintain a catalogue of materials with unit rates, categories, and suppliers. The estimator draws from this catalogue when computing material costs. Update rates once — every future estimate picks up the change.

### 8. Offline-first, no subscriptions

ArchForge Pro runs entirely on the local machine. SQLite with WAL mode and indexed foreign keys. No cloud sync, no API calls, no recurring cost. The packaged `.exe` ships with the database, ML models, stylesheets, and all resources bundled by PyInstaller.

---

## Run ArchForge Pro

### From source

You need Python 3.11+ and pip.

```bash
git clone https://github.com/your-username/archforge-pro
cd archforge-pro
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -r requirements.txt
python main.py
```

### From the installer

Download the latest `ArchForgePro_Setup.exe` from Releases. Run it — no admin rights required (`PrivilegesRequired=lowest`). The installer places the app in `%LocalAppData%\ArchForgePro` and creates a Start Menu shortcut.

---

## Build from source

You need PyInstaller installed in the venv. Run:

```bat
build.bat
```

This produces `dist\ArchForgePro\` with the self-contained executable. To create the Windows installer, open `installer.iss` in Inno Setup 6 and compile.

---

## What's in the box

| Area | Capabilities |
|---|---|
| Projects | Create, edit, delete, search, filter by status, sort by any column, double-click to edit |
| Cost Estimator | Rule-based engine, quality-tiered rates, labour/equipment/GST parameters, Ctrl+Enter to calculate, Ctrl+S to save |
| BOQ | Generate from estimate, itemised quantities, PDF + Excel export |
| Expenses | Ledger with categories and receipt refs, monthly trend, variance against estimate |
| Timeline | Nine standard phases, planned vs actual dates, completion %, Gantt in reports |
| Reports | Five PDF report types with embedded matplotlib charts, branded header |
| ML Prediction | XGBoost model, local inference, confidence range output |
| Materials | Rate catalogue by category and supplier |
| Settings | Company name, address, GST number, contact details for report headers |
| Theme | Dark mode (default) and light mode, brutalist monospace terminal aesthetic |

---

## Inside the codebase

```
app/
  controllers/
    estimation_engine.py   Rule-based cost estimator
    report_controller.py   PDF generation with matplotlib charts
  models/
    database.py            SQLite setup, WAL mode, indexes
    project_model.py       Projects CRUD + dashboard stats
    estimate_model.py      Estimates CRUD
    boq_model.py           BOQ CRUD
    expense_model.py       Expenses CRUD + monthly aggregation
    timeline_model.py      Phases CRUD + defaults
    material_model.py      Materials catalogue
    settings_model.py      App settings
  views/
    main_window.py         Sidebar, nav, theme toggle, global mouse tracker
    pages/                 One file per page (dashboard, projects, estimator, ...)
    dialogs/               Project dialog, expense dialog, ...
  ml/
    predictor.py           XGBoost inference
    trainer.py             Model training pipeline
  utils/
    paths.py               Dev vs PyInstaller frozen path resolver
    animated_bg.py         Dot-grid cursor animation (cached grid, theme-aware)
    sphere_widget.py       Atlas globe (QPainter CompositionMode_Difference)
    chart_widget.py        Matplotlib dashboard charts with vivid palette
    formatters.py          INR formatting, date formatting
  resources/
    styles/
      dark_theme.qss       Brutalist terminal dark theme
      light_theme.qss      High-contrast light theme (pure black text)
    images/                App icon, atlas image
main.py                    Splash screen + entry point
build.bat                  PyInstaller build script
installer.iss              Inno Setup installer script
```

---

## Tech stack

| Layer | Technology |
|---|---|
| UI framework | PyQt6 |
| Database | SQLite (WAL mode, parameterized queries, `sqlite3.Row`) |
| Charts (UI) | Matplotlib (module-level theme state, vivid palette) |
| Charts (PDF) | Matplotlib → PNG → ReportLab embed |
| PDF generation | ReportLab |
| Excel export | openpyxl |
| ML | Scikit-learn, XGBoost |
| Packaging | PyInstaller (`--onedir --windowed`) |
| Installer | Inno Setup 6 |
| Language | Python 3.11 |

---

## Keyboard shortcuts

| Shortcut | Action |
|---|---|
| `Ctrl+N` | New project (Projects page) |
| `Ctrl+F` | Focus search bar (Projects page) |
| `Ctrl+Enter` | Calculate estimate (Estimator page) |
| `Ctrl+S` | Save estimate (Estimator page) |
| `Double-click row` | Edit project |
| `Enter` | Edit selected project |
| `Delete` | Delete selected project |
| `Escape` | Clear search / deselect |
| `D` / `L` | Switch to Dark / Light mode (sidebar) |

---

## Status

ArchForge Pro is a feature-complete desktop application for Indian construction cost estimation. The core workflow — project intake, rule-based estimation, BOQ generation, expense tracking, phase timeline, ML prediction, and PDF report delivery — is fully implemented and packaged as a Windows executable.

Areas that could extend further: integration with live material rate APIs (currently static catalogue), cloud sync for multi-device use, and mobile companion for on-site expense logging.

---

## License

ArchForge Pro — Final Year Computer Engineering Project.  
Copyright © 2026 Gagan Naik.  
Built with ArchForge Pro, PyQt6, ReportLab, Matplotlib, and XGBoost.
