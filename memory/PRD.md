# ANDREPAU POS - Product Requirements Document

## Descriere Proiect
Aplicatie completa de gestiune magazin si POS (Point of Sale) pentru magazinul de materiale de constructii **ANDREPAU**. Aplicatie in limba romana, optimizata pentru Windows desktop si tablete.

## Arhitectura
- **Frontend**: React + Tailwind CSS + Shadcn UI (PWA)
- **Backend**: FastAPI + Python + MongoDB
- **Bridge Fiscal Local**: Python script (ruleaza pe PC-ul din magazin, polling cloud)
- **Desktop (Electron)**: Setup complet - PAUZA

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
7. Stoc & Inventar - Dashboard, export Excel
8. Rapoarte - Vanzari pe zi/luna, top produse, profit
9. Furnizori - CRUD complet
10. Cautare CUI (ANAF) - Cache local + OpenAPI.ro
11. NIR (Nota Intrare Receptie) - Receptie marfa manuala
12. Comenzi in Asteptare cu Rezervare Stoc
13. Mod Offline Baza - Detectare, cache produse, coada vanzari, sync automata
14. Shortcut-uri F-key - F9=Numerar, F7=Card, F11=Anulare
15. Prevenire Vanzari Duplicate - Transaction ID unic, backend idempotent
16. Alerte Stoc Minim
17. Dashboard Deschidere Zi
18. **Import NIR din PDF** - Parsare facturi furnizori (e-Factura, PyMuPDF blocks), extragere automata produse/cantitati/preturi/UM, potrivire cu produse existente, creare automata produse noi daca nu exista match
19. **Import CSV Produse** - Upload CSV cu preview, template descarcabil, detectare automata Nou/Actualizare
20. **Post-NIR Coduri de Bare** - Dupa orice NIR dialog cu toate produsele unde se pot scana/introduce coduri de bare
21. **Cautare Fuzzy + Pret** - Cautare multi-cuvant fuzzy (ex: "grund gri"), cautare dupa ultima parte din denumire, cautare dupa pret in POS si Produse

## Taskuri Viitoare

### P1: Mod Offline Avansat
- Service Worker complet, IndexedDB, sync coada offline

### P2: Raport Z (End of Day Dashboard)
- Sumar automat la sfarsitul zilei

### P3: Bridge Auto-Start
- Bridge sa porneasca automat cu Windows

### P4: Integrare Verifone V200c (blocat pe documentatie ECR)

### Electron (PAUZA)

## API Endpoints Principale
- `POST /api/auth/login` - Autentificare
- `GET/POST /api/products` - Produse CRUD (cautare fuzzy + pret)
- `GET /api/products/csv-template` - Template CSV
- `POST /api/products/import-csv` - Parse CSV preview
- `POST /api/products/import-csv/confirm` - Confirma import CSV
- `POST /api/products/bulk-barcode` - Actualizare bulk coduri de bare
- `POST /api/nir` - Creare NIR manual
- `POST /api/nir/from-pdf` - Creare NIR din PDF (auto-creare produse noi)
- `POST /api/nir/parse-pdf` - Parsare PDF factura
- `POST /api/fiscal/queue` - Comanda fiscala
- `GET /api/fiscal/pending` - Bridge poll
