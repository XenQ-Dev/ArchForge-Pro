"""
Database connection manager and schema initialiser.
Single source of truth for all DDL statements.
"""
import sqlite3
import logging

logger = logging.getLogger(__name__)

from app.utils.paths import data
DB_PATH = data("data/archforge.db")


def get_connection() -> sqlite3.Connection:
    """Return a connection with foreign-keys and row_factory set."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    return conn


def init_database() -> None:
    """Create all tables if they do not exist."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = get_connection()
    try:
        _create_tables(conn)
        _seed_defaults(conn)
        conn.commit()
        logger.info("Database initialised at %s", DB_PATH)
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# DDL
# ---------------------------------------------------------------------------
_SCHEMA = """
-- ─────────────────────────────────────────────────────────────────────────
-- SETTINGS
-- ─────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS settings (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

-- ─────────────────────────────────────────────────────────────────────────
-- PROJECTS
-- ─────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS projects (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    project_name        TEXT    NOT NULL,
    client_name         TEXT    NOT NULL,
    site_location       TEXT    NOT NULL,
    project_type        TEXT    NOT NULL CHECK(project_type IN ('Residential','Commercial','Industrial')),
    plot_area           REAL    NOT NULL CHECK(plot_area > 0),
    built_up_area       REAL    NOT NULL CHECK(built_up_area > 0),
    num_floors          INTEGER NOT NULL DEFAULT 1 CHECK(num_floors >= 1),
    construction_quality TEXT   NOT NULL CHECK(construction_quality IN ('Standard','Premium','Luxury')),
    start_date          TEXT    NOT NULL,
    expected_completion TEXT    NOT NULL,
    status              TEXT    NOT NULL DEFAULT 'Active' CHECK(status IN ('Active','Completed','On Hold','Cancelled')),
    notes               TEXT,
    created_at          TEXT    NOT NULL DEFAULT (datetime('now','localtime')),
    updated_at          TEXT    NOT NULL DEFAULT (datetime('now','localtime'))
);

CREATE TRIGGER IF NOT EXISTS projects_updated_at
AFTER UPDATE ON projects
BEGIN
    UPDATE projects SET updated_at = datetime('now','localtime') WHERE id = NEW.id;
END;

-- ─────────────────────────────────────────────────────────────────────────
-- MATERIAL RATE DATABASE
-- ─────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS material_categories (
    id   INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT    NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS materials (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    category_id INTEGER NOT NULL REFERENCES material_categories(id) ON DELETE CASCADE,
    name        TEXT    NOT NULL,
    unit        TEXT    NOT NULL,
    rate        REAL    NOT NULL CHECK(rate >= 0),
    gst_rate    REAL    NOT NULL DEFAULT 18.0,
    last_updated TEXT   NOT NULL DEFAULT (datetime('now','localtime')),
    UNIQUE(name, unit)
);

-- ─────────────────────────────────────────────────────────────────────────
-- COST ESTIMATES
-- ─────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS cost_estimates (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id       INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    material_cost    REAL    NOT NULL DEFAULT 0,
    labour_cost      REAL    NOT NULL DEFAULT 0,
    equipment_cost   REAL    NOT NULL DEFAULT 0,
    contractor_margin REAL   NOT NULL DEFAULT 0,
    gst_amount       REAL    NOT NULL DEFAULT 0,
    grand_total      REAL    NOT NULL DEFAULT 0,
    labour_pct       REAL    NOT NULL DEFAULT 25.0,
    equipment_pct    REAL    NOT NULL DEFAULT 5.0,
    contractor_pct   REAL    NOT NULL DEFAULT 10.0,
    gst_pct          REAL    NOT NULL DEFAULT 18.0,
    created_at       TEXT    NOT NULL DEFAULT (datetime('now','localtime')),
    updated_at       TEXT    NOT NULL DEFAULT (datetime('now','localtime'))
);

CREATE TRIGGER IF NOT EXISTS estimates_updated_at
AFTER UPDATE ON cost_estimates
BEGIN
    UPDATE cost_estimates SET updated_at = datetime('now','localtime') WHERE id = NEW.id;
END;

-- ─────────────────────────────────────────────────────────────────────────
-- ESTIMATE LINE ITEMS  (individual material quantities & costs)
-- ─────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS estimate_items (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    estimate_id INTEGER NOT NULL REFERENCES cost_estimates(id) ON DELETE CASCADE,
    item_name   TEXT    NOT NULL,
    quantity    REAL    NOT NULL DEFAULT 0,
    unit        TEXT    NOT NULL,
    rate        REAL    NOT NULL DEFAULT 0,
    amount      REAL    NOT NULL DEFAULT 0,
    category    TEXT    NOT NULL DEFAULT 'Material'
);

-- ─────────────────────────────────────────────────────────────────────────
-- BILL OF QUANTITIES
-- ─────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS boq (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id  INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    item_no     INTEGER NOT NULL,
    description TEXT    NOT NULL,
    quantity    REAL    NOT NULL DEFAULT 0,
    unit        TEXT    NOT NULL,
    rate        REAL    NOT NULL DEFAULT 0,
    amount      REAL    NOT NULL DEFAULT 0,
    created_at  TEXT    NOT NULL DEFAULT (datetime('now','localtime'))
);

-- ─────────────────────────────────────────────────────────────────────────
-- EXPENSE TRACKER
-- ─────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS expenses (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id  INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    expense_date TEXT   NOT NULL,
    category    TEXT    NOT NULL CHECK(category IN ('Material','Labour','Equipment','Miscellaneous')),
    description TEXT    NOT NULL,
    amount      REAL    NOT NULL CHECK(amount >= 0),
    receipt_ref TEXT,
    created_at  TEXT    NOT NULL DEFAULT (datetime('now','localtime'))
);

-- ─────────────────────────────────────────────────────────────────────────
-- PROJECT TIMELINE / PHASES
-- ─────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS project_phases (
    id                 INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id         INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    phase_order        INTEGER NOT NULL,
    phase_name         TEXT    NOT NULL,
    planned_start      TEXT,
    planned_end        TEXT,
    actual_start       TEXT,
    actual_end         TEXT,
    completion_pct     REAL    NOT NULL DEFAULT 0 CHECK(completion_pct BETWEEN 0 AND 100),
    status             TEXT    NOT NULL DEFAULT 'Pending' CHECK(status IN ('Pending','In Progress','Completed','Delayed')),
    notes              TEXT
);

-- ─────────────────────────────────────────────────────────────────────────
-- ML PREDICTIONS  (cache predictions per project)
-- ─────────────────────────────────────────────────────────────────────────
-- ─────────────────────────────────────────────────────────────────────────
-- INDEXES  (added for query performance)
-- ─────────────────────────────────────────────────────────────────────────
CREATE INDEX IF NOT EXISTS idx_projects_status      ON projects(status);
CREATE INDEX IF NOT EXISTS idx_projects_created     ON projects(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_estimates_project    ON cost_estimates(project_id);
CREATE INDEX IF NOT EXISTS idx_items_estimate       ON estimate_items(estimate_id);
CREATE INDEX IF NOT EXISTS idx_expenses_project     ON expenses(project_id);
CREATE INDEX IF NOT EXISTS idx_expenses_date        ON expenses(expense_date);
CREATE INDEX IF NOT EXISTS idx_boq_project          ON boq(project_id);
CREATE INDEX IF NOT EXISTS idx_phases_project       ON project_phases(project_id);
CREATE INDEX IF NOT EXISTS idx_materials_category   ON materials(category_id);

CREATE TABLE IF NOT EXISTS ml_predictions (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id       INTEGER REFERENCES projects(id) ON DELETE SET NULL,
    plot_area        REAL    NOT NULL,
    built_up_area    REAL    NOT NULL,
    num_floors       INTEGER NOT NULL,
    project_type     TEXT    NOT NULL,
    quality          TEXT    NOT NULL,
    predicted_cost   REAL,
    predicted_days   REAL,
    model_version    TEXT,
    predicted_at     TEXT    NOT NULL DEFAULT (datetime('now','localtime'))
);
"""


def _create_tables(conn: sqlite3.Connection) -> None:
    conn.executescript(_SCHEMA)


# ---------------------------------------------------------------------------
# Seed default data
# ---------------------------------------------------------------------------
_DEFAULT_SETTINGS = {
    "gst_pct": "18.0",
    "labour_pct": "25.0",
    "equipment_pct": "5.0",
    "contractor_pct": "10.0",
    "currency": "INR",
    "currency_symbol": "₹",
    "company_name": "ArchForge Pro",
    "company_address": "",
    "company_phone": "",
    "company_email": "",
    "theme": "dark",
}

_MATERIAL_CATEGORIES = [
    "Concrete & Masonry",
    "Steel & Metals",
    "Sand & Aggregates",
    "Bricks & Blocks",
    "Tiles & Flooring",
    "Paint & Finishes",
    "Electrical",
    "Plumbing",
    "Doors & Windows",
    "Miscellaneous",
]

# (name, unit, rate_inr, gst_pct, category)
_DEFAULT_MATERIALS = [
    # Concrete & Masonry
    ("OPC Cement 53 Grade", "Bag (50kg)", 420.0, 28.0, "Concrete & Masonry"),
    ("PPC Cement", "Bag (50kg)", 390.0, 28.0, "Concrete & Masonry"),
    ("Ready Mix Concrete M20", "Cu.M", 5500.0, 18.0, "Concrete & Masonry"),
    ("Ready Mix Concrete M25", "Cu.M", 6000.0, 18.0, "Concrete & Masonry"),
    # Steel
    ("TMT Steel Fe500", "MT", 72000.0, 18.0, "Steel & Metals"),
    ("TMT Steel Fe550", "MT", 75000.0, 18.0, "Steel & Metals"),
    ("Structural Steel", "MT", 68000.0, 18.0, "Steel & Metals"),
    # Sand & Aggregates
    ("River Sand (M-Sand)", "Cu.M", 1800.0, 5.0, "Sand & Aggregates"),
    ("M-Sand (Manufactured)", "Cu.M", 1400.0, 5.0, "Sand & Aggregates"),
    ("Coarse Aggregate 20mm", "Cu.M", 2000.0, 5.0, "Sand & Aggregates"),
    ("Fine Aggregate 10mm", "Cu.M", 1900.0, 5.0, "Sand & Aggregates"),
    # Bricks & Blocks
    ("Red Brick (Modular)", "Nos", 9.0, 5.0, "Bricks & Blocks"),
    ("Fly Ash Brick", "Nos", 7.0, 5.0, "Bricks & Blocks"),
    ("AAC Block (600x200x150)", "Nos", 55.0, 12.0, "Bricks & Blocks"),
    ("Hollow Concrete Block", "Nos", 45.0, 12.0, "Bricks & Blocks"),
    # Tiles & Flooring
    ("Ceramic Floor Tile 600x600", "Sq.M", 450.0, 18.0, "Tiles & Flooring"),
    ("Vitrified Tile 800x800", "Sq.M", 950.0, 18.0, "Tiles & Flooring"),
    ("Marble Flooring (Makrana)", "Sq.M", 2500.0, 18.0, "Tiles & Flooring"),
    ("Granite Flooring", "Sq.M", 1800.0, 18.0, "Tiles & Flooring"),
    # Paint
    ("Interior Emulsion Paint", "Litre", 280.0, 18.0, "Paint & Finishes"),
    ("Exterior Weatherproof Paint", "Litre", 380.0, 18.0, "Paint & Finishes"),
    ("Primer (Wall)", "Litre", 180.0, 18.0, "Paint & Finishes"),
    ("Texture Paint", "Kg", 220.0, 18.0, "Paint & Finishes"),
    # Electrical
    ("Copper Wire 2.5 sq.mm", "Mtr", 55.0, 18.0, "Electrical"),
    ("Copper Wire 4 sq.mm", "Mtr", 85.0, 18.0, "Electrical"),
    ("PVC Conduit 20mm", "Mtr", 35.0, 18.0, "Electrical"),
    ("MCB (10A)", "Nos", 280.0, 18.0, "Electrical"),
    ("MCB Distribution Board (8W)", "Nos", 2200.0, 18.0, "Electrical"),
    ("Modular Switch (6A)", "Nos", 120.0, 18.0, "Electrical"),
    ("LED Light 12W", "Nos", 320.0, 18.0, "Electrical"),
    # Plumbing
    ("CPVC Pipe 25mm", "Mtr", 145.0, 18.0, "Plumbing"),
    ("UPVC Pipe 110mm (SWR)", "Mtr", 280.0, 18.0, "Plumbing"),
    ("Ball Valve 25mm", "Nos", 220.0, 18.0, "Plumbing"),
    ("Wash Basin (Ceramic)", "Nos", 3500.0, 18.0, "Plumbing"),
    ("EWC (Toilet)", "Nos", 8000.0, 18.0, "Plumbing"),
    ("Bathroom Fittings Set", "Set", 12000.0, 18.0, "Plumbing"),
    # Doors & Windows
    ("Teak Wood Door 900x2100", "Nos", 18000.0, 12.0, "Doors & Windows"),
    ("Flush Door 900x2100", "Nos", 6500.0, 12.0, "Doors & Windows"),
    ("UPVC Window 1200x1200", "Nos", 8500.0, 18.0, "Doors & Windows"),
    ("Aluminium Window 1200x1200", "Nos", 6800.0, 18.0, "Doors & Windows"),
    # Misc
    ("Waterproofing Compound", "Kg", 380.0, 18.0, "Miscellaneous"),
    ("Shuttering Plywood", "Sq.M", 650.0, 18.0, "Miscellaneous"),
    ("Binding Wire", "Kg", 72.0, 18.0, "Miscellaneous"),
]

_DEFAULT_PHASES = [
    (1, "Foundation"),
    (2, "Structure / RCC Frame"),
    (3, "Brickwork / Masonry"),
    (4, "Plumbing"),
    (5, "Electrical"),
    (6, "Plastering"),
    (7, "Flooring"),
    (8, "Painting"),
    (9, "Finishing & Handover"),
]


def _seed_defaults(conn: sqlite3.Connection) -> None:
    # Settings
    for k, v in _DEFAULT_SETTINGS.items():
        conn.execute(
            "INSERT OR IGNORE INTO settings(key,value) VALUES(?,?)", (k, v)
        )

    # Material categories
    for cat in _MATERIAL_CATEGORIES:
        conn.execute(
            "INSERT OR IGNORE INTO material_categories(name) VALUES(?)", (cat,)
        )

    # Materials — only insert if table is empty
    existing = conn.execute("SELECT COUNT(*) FROM materials").fetchone()[0]
    if existing == 0:
        for name, unit, rate, gst, cat in _DEFAULT_MATERIALS:
            cat_id = conn.execute(
                "SELECT id FROM material_categories WHERE name=?", (cat,)
            ).fetchone()
            if cat_id:
                conn.execute(
                    """INSERT OR IGNORE INTO materials(category_id,name,unit,rate,gst_rate)
                       VALUES(?,?,?,?,?)""",
                    (cat_id[0], name, unit, rate, gst),
                )
