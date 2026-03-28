# ANDREPAU POS - Product Requirements Document

## Descriere Proiect
Aplicatie completa de gestiune magazin si POS (Point of Sale) pentru magazinul de materiale de constructii **ANDREPAU**. Aplicatie in limba romana, optimizata pentru Windows desktop si tablete.

## Arhitectura
- **Frontend**: React + Tailwind CSS + Shadcn UI (PWA)
- **Backend**: FastAPI + Python + MongoDB
- **Bridge Fiscal Local**: Python script (v3.2 PRODUCTIE, ruleaza pe PC-ul din magazin)
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
6. Bridge Service v3.2 PRODUCTIE
7. Stoc & Inventar - Dashboard, export Excel
8. Rapoarte - Vanzari pe zi/luna, top produse, profit
9. Furnizori - CRUD complet
10. Cautare CUI (ANAF) - Cache local + OpenAPI.ro
11. NIR (Nota Intrare Receptie) - Receptie marfa manuala
12. Comenzi in Asteptare cu Rezervare Stoc
13. Mod Offline Baza
14. Shortcut-uri F-key - F9=Numerar, F7=Card, F11=Anulare
15. Prevenire Vanzari Duplicate
16. Alerte Stoc Minim
17. Dashboard Deschidere Zi
18. **Import NIR din PDF** - Parsare facturi furnizori (e-Factura, PyMuPDF blocks), extragere automata produse/cantitati/preturi/UM, potrivire cu produse existente, **creare automata produse noi** daca nu exista match, detectare furnizor S.R.L./S.A./L.T.D.
19. **Import CSV Produse** - Upload CSV cu preview, template descarcabil, detectare automata Nou/Actualizare
20. **Post-NIR Coduri de Bare** - Dupa orice NIR dialog cu toate produsele unde se pot scana/introduce coduri de bare
21. **Cautare Fuzzy + Pret Combinat** - "diluant 5" gaseste DILUANT cu pret ~5 RON; "grund gri" gaseste GRUND METAL DK GRI; orice cuvant din orice pozitie din denumire; cautare dupa pret singur
22. **Facturi PDF Test** - 3 facturi test (DEDEMAN 8 prod, HORNBACH 6 prod, LEROY MERLIN 9 prod) descarcabile din aplicatie

## Taskuri Viitoare

### P1: Mod Offline Avansat
### P2: Raport Z (End of Day Dashboard)
### P3: Bridge Auto-Start
### P4: Integrare Verifone V200c (blocat pe documentatie ECR)
### Electron (PAUZA)

## API Endpoints Principale
- `POST /api/auth/login` - Autentificare
- `GET/POST /api/products` - Produse CRUD (cautare fuzzy + pret combinat)
- `GET /api/products/csv-template` - Template CSV
- `POST /api/products/import-csv` - Parse CSV preview
- `POST /api/products/import-csv/confirm` - Confirma import CSV
- `POST /api/products/bulk-barcode` - Actualizare bulk coduri de bare
- `POST /api/nir` - Creare NIR manual
- `POST /api/nir/from-pdf` - Creare NIR din PDF (auto-creare produse noi)
- `POST /api/nir/parse-pdf` - Parsare PDF factura
- `GET /api/nir/test-invoices` - Lista facturi PDF test
- `GET /api/nir/test-invoices/{filename}` - Descarca factura test
- `POST /api/fiscal/queue` - Comanda fiscala
- `GET /api/fiscal/pending` - Bridge poll
