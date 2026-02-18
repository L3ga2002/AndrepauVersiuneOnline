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

### 1. POS / Casa de Marcat ✅
- Fast selling screen with product search
- Barcode scanner support
- Category filtering
- Cart with quantity selector
- Manual price edit for bulk products
- Live total calculation
- Payment: Numerar, Card, Tichete de masă, Combinată (Numerar+Card+Tichete)
- Discount percentage
- Receipt generation
- Automatic stock decrease
- Hold/Pending orders (salvare coș) - Buton "AȘTEAPTĂ" + vizualizare comenzi în așteptare
- Simplified invoice generation with ANAF CUI search for auto-fill company data

### 2. Product Management ✅
- CRUD operations for products
- Fields: Nume, Categorie, Furnizor, Cod bare, Preț achiziție (opțional), Preț vânzare, TVA, Unitate măsură, Stoc, Stoc minim, Descriere
- Units: buc, sac, kg, metru, litru, rolă
- Fractional quantities support
- Scan-to-Add: scanning unknown barcode prompts to add new product

### 3. Stock / Inventar ✅
- Dashboard: total produse, valoare stoc, stoc scăzut, fără stoc
- Low stock alerts
- NIR (Notă de Intrare Recepție) module

### 4. Reports ✅
- Sales today/week/month/year
- Profit calculation (admin only)
- Top 10 products sold
- Top categories
- Sales history (bonuri)
- Export CSV

### 5. Suppliers ✅
- CRUD operations
- Fields: Nume firmă, Telefon, Email, Adresă

### 6. User Roles ✅
- Admin: full access
- Casier: POS only + view access

### 7. Settings ✅
- User management (admin only)
- Database backup/export JSON
- Export produse Excel (.xlsx)

## What's Been Implemented

### Date: 18.02.2026 (Current Session)
- ✅ Fixed critical Select component bug (crashed forms on Products/Stock pages)
- ✅ Added Excel export functionality (/api/products/export/xls)
- ✅ Removed "Made with Emergent" badge
- ✅ Added **Hold Orders** feature - "AȘTEAPTĂ" button to save cart + "Comenzi în Așteptare" dialog
- ✅ Added **Combined Payment** - Pay with any combination of Cash + Card + Meal Vouchers
- ✅ Added **Invoice with ANAF Search** - Enter CUI, click "Caută", auto-fills company name, address, reg. number, VAT status
- ✅ All buttons renamed to Romanian: AȘTEAPTĂ (not HOLD), COMBINAT, FACT, etc.

### Date: 17.02.2026 (Previous Session)
- Full backend API with FastAPI + MongoDB
- React frontend with Shadcn/UI components
- JWT authentication
- Industrial Dark Mode theme (orange accents)
- Touchscreen-optimized (48px+ buttons)
- Romanian language throughout
- PWA (Progressive Web App) conversion
- 5,697 products imported from Excel file
- Pagination for large product catalogs
- Database indexing for performance

## Tech Stack
- Backend: FastAPI, MongoDB, Motor, PyJWT, bcrypt, openpyxl
- Frontend: React 19, Tailwind CSS, Shadcn/UI, Recharts
- Fonts: Barlow Condensed (headings), Inter (body), JetBrains Mono (prices)
- PWA: Service Worker, Manifest

## Prioritized Backlog

### P0 (Critical) - DONE ✅
- [x] POS selling flow
- [x] Product management
- [x] Authentication
- [x] Select component bug fix

### P1 (High) - DONE ✅
- [x] Stock dashboard
- [x] NIR module
- [x] Reports
- [x] Supplier management
- [x] Excel export
- [x] PWA conversion
- [x] Mass data import

### P2 (Medium) - Future
- [ ] INCOTEX Succes M7 cash register integration
- [ ] Bank POS terminal integration
- [ ] Thermal printer integration (real ESC/POS commands)
- [ ] Cash drawer trigger
- [ ] Barcode label printing

### P3 (Low) - Future
- [ ] Multiple price lists
- [ ] Customer loyalty program
- [ ] Multi-location support
- [ ] Offline mode with sync
- [ ] Mobile app version

## Next Tasks
1. Integrate INCOTEX Succes M7 cash register for fiscal receipts
2. Integrate bank card payment terminal
3. Add thermal printer support (ESC/POS protocol)
4. Implement cash drawer control

## Credentials
- **Admin**: admin / admin123
- **Casier**: casier / casier123
