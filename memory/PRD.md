# ANDREPAU POS - Product Requirements Document

## Original Problem Statement
Complete store management and POS application for "ANDREPAU" construction materials shop. Includes stable payments, atomic stock, INCOTEX SUCCES M7 cash register integration (via local Python bridge), and automated NIR (Goods Receipt Note) management.

## Architecture
```
/app/backend/
├── server.py          # FastAPI app setup, router includes (62 lines)
├── database.py        # MongoDB connection (db, client)
├── auth.py            # Auth helpers (hash, verify, token, dependencies)
├── models.py          # Pydantic models
├── utils.py           # Shared helpers (parse_number)
├── routes/
│   ├── auth.py        # Login, register, users
│   ├── products.py    # Products CRUD, import CSV/XLS, categories, bulk ops
│   ├── suppliers.py   # Suppliers CRUD
│   ├── sales.py       # Sales CRUD, fiscal settings
│   ├── nir.py         # NIR + PDF parsing
│   ├── reports.py     # Sales reports, stock dashboard, top products
│   ├── cash.py        # Cash operations, opening summary, TVA settings
│   ├── bridge.py      # Fiscal bridge (INCOTEX)
│   ├── held_orders.py # Held orders management
│   ├── exports.py     # Backup, CSV/XLS export
│   ├── anaf.py        # ANAF CUI search, companies cache
│   └── seed.py        # Database seeding

/app/frontend/src/
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
│   └── Layout.js          # Sidebar with theme toggle (light/dark)
```

## Completed Features (as of March 31, 2026)
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
- **[NEW] Server refactoring: 2481 lines → 12 route modules (62 lines server.py)**
- **[NEW] TVA default 21%**
- **[NEW] Save button for starting balance (Deschidere Zi)**
- **[NEW] Persistent POS cart (localStorage)**
- **[NEW] Cash calculator modal (suma primita → rest de dat)**
- **[NEW] Expandable receipt details in Reports**
- **[NEW] Light/Dark mode toggle**
- **[NEW] Card sales total on Start Day page**

## P1 Completed
1. ✅ TVA implicit 21%
2. ✅ Buton Salvare Sold Deschidere Zi
3. ✅ Coș POS persistent
4. ✅ Calculator Rest + Quick amounts
5. ✅ Detalii bon expandabile
6. ✅ Light Mode toggle
7. ✅ Sold casă vizibil la Operațiuni Casă (already existed)
8. ✅ Sumă card la Deschidere Zi
9. ✅ Server.py refactoring

## Remaining P1
- Copiere/Reprint bon (comandă COPIE INCOTEX hardware - NU bon fiscal nou)

## P2 Tasks
- Raport Z Dashboard (doar vizualizare)
- Secțiune Update-uri ANAF
- Optimizare Mobilă (responsive)

## P3/P4 Tasks
- Integrare Verifone V200c ECR (BLOCAT - banca trebuie să configureze Ethernet ECR cu IP static)
- Bridge Auto-Start pe Windows
- Import NIR din Excel dedicat
- Istoric Prețuri pe Furnizor
- Electron Desktop App (PAUZA)

## Deployment
- VPS: Hostinger Ubuntu 24.04
- Preview: https://fiscal-bridge-1.preview.emergentagent.com
- Backend: FastAPI on port 8001
- Frontend: React on port 3000
- Database: MongoDB
- Nginx: client_max_body_size 20M

## Credentials
- Admin: admin / admin123
- Casier: casier / casier123
