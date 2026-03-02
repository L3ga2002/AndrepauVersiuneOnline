# ANDREPAU POS - Product Requirements Document

## Problem Statement
Create a store management + POS application for a construction materials and tools shop called ANDREPAU.
- Romanian language interface
- Optimized for Windows desktop + tablet (touchscreen)
- Fast selling in physical store + stock management

## User Personas
1. **Administrator** - Full access to all features (products, suppliers, reports, settings, users)
2. **Casier** - Limited to POS selling, products view, stock view, and reports

## Core Requirements

### 1. POS / Casa de Marcat
- Fast selling screen with product search
- Barcode scanner support
- Category filtering
- Cart with quantity selector
- Manual price edit for bulk products
- Live total calculation
- Payment: Numerar, Card, Tichete de masa, Combinata (Numerar+Card+Tichete)
- Discount percentage
- Receipt generation
- Automatic stock decrease
- Hold/Pending orders (salvare cos) - Buton "ASTEAPTA" + vizualizare comenzi in asteptare
- Simplified invoice generation with ANAF CUI search for auto-fill company data

### 2. Product Management
- CRUD operations for products
- Fields: Nume, Categorie, Furnizor, Cod bare, Pret achizitie (optional), Pret vanzare, TVA, Unitate masura, Stoc, Stoc minim, Descriere
- Units: buc, sac, kg, metru, litru, rola
- Fractional quantities support
- Scan-to-Add: scanning unknown barcode prompts to add new product

### 3. Stock / Inventar
- Dashboard: total produse, valoare stoc, stoc scazut, fara stoc
- Low stock alerts
- NIR (Nota de Intrare Receptie) module

### 4. Reports
- Sales today/week/month/year
- Profit calculation (admin only)
- Top 10 products sold
- Top categories
- Sales history (bonuri)
- Export CSV

### 5. Suppliers
- CRUD operations
- Fields: Nume firma, Telefon, Email, Adresa

### 6. User Roles
- Admin: full access
- Casier: POS only + view access

### 7. Settings
- User management (admin only)
- Database backup/export JSON
- Export produse Excel (.xlsx)

### 8. Cash Register Integration (INCOTEX Succes M7)
- Bridge service (fiscal_bridge.py) for file-based communication with SuccesDrv
- Commands via ONLINE.TXT, responses via ERROR.TXT
- Operations: Receipt printing, Report X, Report Z, Cash In/Out, Open Drawer
- Built-in test page at http://localhost:5555/test
- Auto-detection of SuccesDrv path
- Windows batch scripts for easy install/start

## What's Been Implemented

### Date: 02.03.2026
- Fiscal Bridge Service v2.0 - production-ready with:
  - File-based communication (ONLINE.TXT / ERROR.TXT)
  - Built-in HTML test page at /test
  - Diagnostic endpoint at /diagnostic
  - Auto-detection of SuccesDrv folder path
  - Windows installer (install_bridge.bat) and starter (start_bridge.bat)
  - All fiscal endpoints: receipt, cancel, report X/Z, cash in/out, drawer
- Cash Operations Page (Operatiuni Casa) - fully functional:
  - Bridge connection status indicator with auto-refresh
  - Daily stats (Sold Casa, Incasari Cash/Card, Bonuri)
  - Report X, Report Z (with confirmation), Cash In/Out, Open Drawer, History
  - Configurable bridge URL (saved in localStorage)
  - Clear instructions when bridge is disconnected
- Backend improvements:
  - transaction_id for duplicate sale prevention
  - fiscal_number and fiscal_status on sales
  - Sale cancellation with stock restore (/api/sales/{id}/cancel)
  - Fiscal settings endpoint (/api/settings/fiscal)
- Testing: 100% pass rate (34/34 backend, all frontend)

### Date: 18.02.2026
- Fixed critical Select component bug
- Added Excel export functionality
- Removed "Made with Emergent" badge
- Added Hold Orders feature
- Added Combined Payment
- Added Invoice with ANAF Search
- IMPORTED 3,774,060 COMPANIES from ONRC

### Date: 17.02.2026
- Full backend API with FastAPI + MongoDB
- React frontend with Shadcn/UI components
- JWT authentication
- Industrial Dark Mode theme (orange accents)
- PWA conversion
- 5,697 products imported from Excel

## Tech Stack
- Backend: FastAPI, MongoDB, Motor, PyJWT, bcrypt, openpyxl
- Frontend: React 19, Tailwind CSS, Shadcn/UI, Recharts
- Bridge: Flask + flask-cors (Python, runs locally on store PC)
- Fonts: Barlow Condensed (headings), Inter (body), JetBrains Mono (prices)
- PWA: Service Worker, Manifest

## Architecture
- Cloud: React PWA + FastAPI backend + MongoDB
- Local (store PC): fiscal_bridge.py (Flask) communicates with SuccesDrv via file I/O
- PWA calls bridge at http://localhost:5555 (Chrome allows HTTPS->localhost)

## Prioritized Backlog

### P0 - DONE
- [x] POS selling flow
- [x] Product management
- [x] Authentication
- [x] Select component bug fix
- [x] Cash register integration (bridge service)
- [x] Cash operations page

### P1 - DONE
- [x] Stock dashboard
- [x] NIR module
- [x] Reports
- [x] Supplier management
- [x] Excel export
- [x] PWA conversion
- [x] Mass data import

### P2 - TODO
- [ ] Integrate POS payment flow with fiscal bridge (print receipt before stock deduction)
- [ ] Fix "100" text appearing in sidebar (stock alerts badge)
- [ ] Minimum stock alerts page with notifications
- [ ] Professional logging for all operations

### P3 - Future
- [ ] NIR from PDF import (parse supplier invoices)
- [ ] Verifone V200c bank POS terminal integration
- [ ] Multiple price lists
- [ ] Customer loyalty program
- [ ] Barcode label printing

## Key Files
- /app/backend/server.py - Main FastAPI backend
- /app/backend/fiscal_bridge.py - Local bridge service for cash register
- /app/backend/install_bridge.bat - Windows installer
- /app/backend/start_bridge.bat - Windows starter
- /app/frontend/src/pages/CashOperationsPage.js - Cash operations UI
- /app/frontend/src/pages/POSPage.js - POS selling UI

## Credentials
- **Admin**: admin / admin123
- **Casier**: casier / casier123
