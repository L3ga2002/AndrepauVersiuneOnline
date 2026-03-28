# ANDREPAU POS - Product Requirements Document

## Descriere Proiect
Aplicatie completa de gestiune magazin si POS (Point of Sale) pentru magazinul de materiale de constructii **ANDREPAU**. Aplicatie in limba romana, optimizata pentru Windows desktop si tablete.

## Arhitectura
- **Frontend**: React + Tailwind CSS + Shadcn UI (PWA)
- **Backend**: FastAPI + Python + MongoDB
- **Bridge Fiscal Local**: Python script (ruleaza pe PC-ul din magazin, polling cloud)
- **Comunicare Hardware**: Cloud Queue → Bridge polls → SuccesDrv → ONLINE.TXT → INCOTEX Succes M7
- **Desktop (Electron)**: Setup complet, comunica direct cu bridge-ul local - PAUZA

## Credentiale
- Admin: `admin` / `admin123`
- Casier: `casier` / `casier123`

## Ce s-a implementat

### Complet (Functional)
1. Sistem de autentificare - JWT, roluri admin/casier
2. Gestiune produse - CRUD complet, import Excel, categorii, cod bare
3. Pagina POS - Vanzare cu cos, cautare, categorii, discount, factura cu CUI
4. Integrare Bridge Fiscal (Cloud Polling)
5. Operatiuni Casa - Raport X/Z, Intrare/Iesire numerar, Deschide sertar, Istoric
6. Bridge Service v3.2 PRODUCTIE - Fara bon test, curatare ONLINE.TXT la pornire
7. Descarcare Bridge ZIP - Endpoint /api/bridge/download-direct
8. Stoc & Inventar - Dashboard, export Excel
9. Rapoarte - Vanzari pe zi/luna, top produse, profit
10. Furnizori - CRUD complet
11. Cautare CUI (ANAF) - Cache local + OpenAPI.ro
12. NIR (Nota Intrare Receptie) - Receptie marfa manuala
13. TVA actualizat - Conform Legea 141/2025 (21%)
14. Comenzi in Asteptare cu Rezervare Stoc
15. Mod Offline Baza - Detectare, cache produse, coada vanzari, sync automata
16. Shortcut-uri F-key - F9=Numerar, F7=Card, F11=Anulare
17. Prevenire Vanzari Duplicate - Transaction ID unic, backend idempotent
18. Alerte Stoc Minim - Severitate (critical/warning), deficit, sortare
19. Dashboard Deschidere Zi - Sold casa, status bridge, hold, alerte stoc
20. **Import NIR din PDF** - Parsare facturi furnizori (e-Factura, PyMuPDF blocks), extragere automata produse/cantitati/preturi/UM, potrivire cu produse existente, detectare furnizor si numar factura, preview editabil
21. **Import CSV Produse** - Upload CSV cu preview, template descarcabil, detectare automata Nou/Actualizare, suport virgula/punct-virgula, codificari multiple (UTF-8, Latin-1, CP1252)
22. **Post-NIR Coduri de Bare** - Dupa orice NIR (manual sau PDF), dialog cu toate produsele adaugate unde se pot scana/introduce coduri de bare, Enter muta la urmatorul, salvare bulk

## Taskuri Viitoare

### P1: Mod Offline Avansat
- Service Worker complet, IndexedDB, sync coada offline

### P2: Raport Z (End of Day Dashboard)
- Sumar automat la sfarsitul zilei

### P3: Bridge Auto-Start
- Bridge sa porneasca automat cu Windows/Electron

### P4: Integrare Verifone V200c
- Terminal POS card (blocat pe documentatie ECR)

### Electron (PAUZA)
- Build & Test Electron Desktop (.exe) - pauza la cererea utilizatorului

## API Endpoints Principale
- `POST /api/auth/login` - Autentificare
- `GET /api/daily/opening-summary` - Dashboard deschidere zi
- `GET/POST /api/products` - Produse CRUD
- `GET /api/products/csv-template` - Descarca template CSV
- `POST /api/products/import-csv` - Parseaza CSV si returneaza preview
- `POST /api/products/import-csv/confirm` - Confirma si executa importul CSV
- `POST /api/products/bulk-barcode` - Actualizare bulk coduri de bare
- `POST /api/sales` - Creare vanzare (cu transaction_id, idempotent)
- `POST /api/held-orders` - Hold cu rezervare stoc
- `GET /api/stock/alerts` - Alerte cu severity si deficit
- `POST /api/nir` - Creare NIR
- `POST /api/nir/parse-pdf` - Parseaza PDF factura si extrage produse
- `POST /api/fiscal/queue` - Comanda fiscala
- `GET /api/fiscal/pending` - Bridge poll
