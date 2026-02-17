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
- Payment: Numerar, Card, Combinată
- Discount percentage
- Receipt generation
- Automatic stock decrease

### 2. Product Management ✅
- CRUD operations for products
- Fields: Nume, Categorie, Furnizor, Cod bare, Preț achiziție, Preț vânzare, TVA, Unitate măsură, Stoc, Stoc minim, Descriere
- Units: buc, sac, kg, metru, litru, rolă
- Fractional quantities support

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
- Database backup/export

## What's Been Implemented
- **Date**: 17.02.2026
- Full backend API with FastAPI + MongoDB
- React frontend with Shadcn/UI components
- JWT authentication
- Industrial Dark Mode theme (orange accents)
- Touchscreen-optimized (48px+ buttons)
- Romanian language throughout
- 55 demo products seeded
- 3 demo suppliers
- 2 demo users (admin, casier)

## Tech Stack
- Backend: FastAPI, MongoDB, Motor, PyJWT, bcrypt
- Frontend: React 19, Tailwind CSS, Shadcn/UI, Recharts
- Fonts: Barlow Condensed (headings), Inter (body), JetBrains Mono (prices)

## Prioritized Backlog

### P0 (Critical) - DONE
- [x] POS selling flow
- [x] Product management
- [x] Authentication

### P1 (High) - DONE
- [x] Stock dashboard
- [x] NIR module
- [x] Reports
- [x] Supplier management

### P2 (Medium) - Future
- [ ] Thermal printer integration (real ESC/POS commands)
- [ ] Cash drawer trigger
- [ ] Barcode label printing
- [ ] Multiple price lists
- [ ] Customer loyalty program

### P3 (Low) - Future
- [ ] Multi-location support
- [ ] Import/Export Excel
- [ ] Offline mode with sync
- [ ] Mobile app version

## Next Tasks
1. Integrate real thermal printer (ESC/POS protocol)
2. Add cash drawer control
3. Implement barcode label printing
4. Add customer management module
