# ANDREPAU POS - Product Requirements Document

## Original Problem Statement
Complete store management and POS application for "ANDREPAU" construction materials shop. Includes stable payments, atomic stock, INCOTEX SUCCES M7 cash register integration (via local Python bridge), and automated NIR (Goods Receipt Note) management.

**Architecture Transition**: User wants to keep VPS for online access (boss can manage NIR from office) but also have a LOCAL OFFLINE mode on the shop PC for cash receipts when internet is down.

## Architecture
```
/app/backend/
├── server.py          # FastAPI app + static file serving for local mode
├── database.py        # MongoDB connection (db, client)
├── auth.py            # Auth helpers (hash, verify, token, dependencies)
├── models.py          # Pydantic models
├── utils.py           # Shared helpers (parse_number)
├── fiscal_bridge.py   # Local Python bridge for INCOTEX printer
├── routes/
│   ├── auth.py        # Login, register, users
│   ├── products.py    # Products CRUD, import CSV/XLS, categories, bulk ops
│   ├── suppliers.py   # Suppliers CRUD
│   ├── sales.py       # Sales CRUD, fiscal settings
│   ├── nir.py         # NIR + PDF parsing
│   ├── reports.py     # Sales reports, stock dashboard, top products
│   ├── cash.py        # Cash operations, opening summary, TVA settings
│   ├── bridge.py      # Fiscal bridge (INCOTEX) + local_setup zip download
│   ├── held_orders.py # Held orders management
│   ├── exports.py     # Backup, CSV/XLS export
│   ├── anaf.py        # ANAF CUI search, companies cache
│   └── seed.py        # Database seeding

/app/frontend/src/
├── context/
│   └── AuthContext.js     # Dynamic API URL (localhost vs VPS)
├── pages/
│   ├── POSPage.js         # POS interface with persistent cart, cash calculator
│   ├── StartDayPage.js    # Day opening with balance save, card sales summary
│   ├── ProductsPage.js    # Products management + import
│   ├── ReportsPage.js     # Reports with expandable receipt details
│   ├── StockPage.js       # Stock & inventory
│   ├── CashOperationsPage.js # Cash operations with balance display
│   ├── SuppliersPage.js   # Suppliers management
│   └── SettingsPage.js    # App settings
├── components/
│   └── Layout.js          # Sidebar with theme toggle + connection indicator

/app/local_setup/
├── install_andrepau.bat   # First-time Windows installation
├── start_andrepau.bat     # Start all services (MongoDB + FastAPI + Bridge + Browser)
├── stop_andrepau.bat      # Stop services
├── update_local.bat       # Git pull + rebuild + restart
└── README_INSTALARE.txt   # Installation guide in Romanian
```

## Deployment
- VPS: Hostinger Ubuntu 24.04
- Preview: https://desktop-pos-manager.preview.emergentagent.com
- Backend: FastAPI on port 8001
- Frontend: React on port 3000
- Database: MongoDB
- Nginx: client_max_body_size 20M
- **Pasi deploy VPS: Save to Github → pe VPS: `/opt/update.sh`**
- **Pasi deploy LOCAL: `local_setup/update_local.bat`**

## How Online/Offline Works
- **Online (VPS)**: Browser → VPS URL → everything normal
- **Offline (local)**: Browser → localhost:8001 → local FastAPI serves React build + API
- Frontend auto-detects: if hostname=localhost → uses local API, otherwise → VPS API
- Connection indicator in sidebar: green "ONLINE (VPS)" or blue "MOD LOCAL (Offline)"
- Bridge fiscal: starts with `start_andrepau.bat`, polls local FastAPI

## Completed Features
- Full POS interface with product search, barcode, categories
- Stable payment processing (numerar, card, tichete, combinat)
- Atomic stock deduction after fiscal receipt
- INCOTEX SUCCES M7 integration via local Python bridge
- Held sales management
- NIR creation from supplier PDF invoices (e-Factura)
- CSV/XLS import with pagination (6000+ products supported)
- MongoDB bulk operations for large imports
- Duplicate receipt prevention (transaction_id)
- F-key shortcuts (F7 Card, F9 Cash, F11 Clear)
- ANAF v9 CUI lookup with caching
- Server refactoring: 2481 lines → 12 route modules
- TVA default 21%
- Save button for starting balance (Deschidere Zi)
- Persistent POS cart (localStorage)
- Cash calculator modal (suma primita → rest de dat)
- Expandable receipt details in Reports
- Light/Dark mode toggle
- Card sales total on Start Day page
- **[NEW] Dynamic API URL (localhost detection for offline mode)**
- **[NEW] Connection mode indicator in sidebar (ONLINE/OFFLINE)**
- **[NEW] FastAPI serves React build for local Windows mode**
- **[NEW] Windows scripts: install, start, stop, update**
- **[NEW] Bridge autostart in start_andrepau.bat**
- **[NEW] Bridge download includes local_setup scripts**
- **[NEW] Sync mechanism: offline sales → VPS (backend endpoints)**
- **[NEW] Sync banner in sidebar (pending count + sync button)**
- **[NEW] Settings: "Instalare Locala" tab with download kit**
- **[NEW] Settings: "Sincronizare" tab (visible only in local mode)**
- **[NEW] Auto VPS health check every 30s (in local mode)**

## Remaining P1
- Copiere/Reprint bon (comanda COPIE INCOTEX hardware - NU bon fiscal nou)

## P2 Tasks
- Raport Z Dashboard (doar vizualizare)
- Sectiune Update-uri ANAF
- Optimizare Mobila (responsive)

## P3/P4 Tasks
- Integrare Verifone V200c ECR (BLOCAT - banca trebuie sa configureze Ethernet ECR)
- Import NIR din Excel dedicat
- Istoric Preturi pe Furnizor

## Credentials
- Admin: admin / admin123
- Casier: casier / casier123
