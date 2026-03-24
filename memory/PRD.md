# ANDREPAU POS - Product Requirements Document

## Descriere Proiect
Aplicatie completa de gestiune magazin si POS (Point of Sale) pentru magazinul de materiale de constructii **ANDREPAU**. Aplicatie in limba romana, optimizata pentru Windows desktop si tablete.

## Arhitectura
- **Frontend**: React + Tailwind CSS + Shadcn UI (PWA)
- **Backend**: FastAPI + Python + MongoDB
- **Bridge Fiscal Local**: Python script (ruleaza pe PC-ul din magazin, polling cloud)
- **Comunicare Hardware**: Cloud Queue → Bridge polls → SuccesDrv → ONLINE.TXT → INCOTEX Succes M7

## Credentiale
- Admin: `admin` / `admin123`
- Casier: `casier` / `casier123`

## Ce s-a implementat

### Complet (Functional) - Actualizat 24.03.2026
1. **Sistem de autentificare** - JWT, roluri admin/casier
2. **Gestiune produse** - CRUD complet, import Excel, categorii, cod bare
3. **Pagina POS** - Vanzare cu cos, cautare produse, categorii, discount, factura cu CUI
4. **Integrare Bridge Fiscal (Cloud Polling)** - PWA → Cloud API → Bridge polls → Printer
5. **Operatiuni Casa** - Raport X/Z, Intrare/Iesire numerar, Deschide sertar, Istoric, Status bridge
6. **Bridge Service v3.0** - Cloud polling, comenzi corecte din Manual SuccesDRV 8.5
7. **Descarcare Bridge ZIP** - Endpoint /api/bridge/download-direct
8. **Stoc & Inventar** - Dashboard, export Excel
9. **Rapoarte** - Vanzari pe zi/luna, top produse, profit
10. **Furnizori** - CRUD complet
11. **Cautare CUI (ANAF)** - Cache local cu firme romanesti + OpenAPI.ro
12. **NIR (Nota Intrare Receptie)** - Receptie marfa
13. **TVA actualizat** - Conform Legea 141/2025 (21% standard)

### Nou implementat - Sesiune curenta (24.03.2026)
14. **Comenzi in Asteptare cu Rezervare Stoc** - Hold orders salvate in backend, stoc dedus la hold, restaurat la restore/cancel. La expirare 24h stocul RAMANE dedus.
15. **Mod Offline Baza** - Detectare offline, cache produse localStorage, coada vanzari offline, sincronizare automata
16. **Shortcut-uri F-key** - F9=Numerar, F7=Card, F11=Anulare cos (etichete vizibile pe butoane)
17. **Afisare produse imbunatatita** - Nume pe 3 linii cu tooltip, stoc vizibil per produs
18. **Eliminare dialog bon** - Vanzarea se finalizeaza direct cu toast, fara popup
19. **Prevenire Vanzari Duplicate (P2)** - Transaction ID unic (TXN-{timestamp}-{random}) trimis cu fiecare vanzare. Backend idempotent - returneaza aceeasi vanzare la retrimitere.
20. **Alerte Stoc Minim Imbunatatite (P1)** - Severitate (critical/warning), coloana deficit, sortare dupa severitate, icoane vizuale, rezumat pe categorii
21. **Logare Profesionala (P3)** - Tag-uri [SALE], [CASH], [FISCAL], [STOCK] pe toate operatiunile critice cu detalii complete (BON, TXN, user, amount)

### Format Comenzi Fiscale (INCOTEX Succes M7 via SuccesDRV 8.5)
```
Command 0:  0;NrOperator;Parola;1[;I]           Deschidere bon
Command 1:  1;Denumire;UM;CotaTVA;Pret_bani;Cantitate  Articol
Command 5:  5;Suma_bani;FormaPl;1;0             Plata (CARD: 5;;2;1;0)
Command 14: 14                                   Anulare (fara ;)
Command 15: 15                                   Raport Z (fara ;)
Command 25: 25;T;Valoare_bani;Motiv;NrOp        Cash In(T=2)/Out(T=1)
Command 30: 30                                   Raport X (fara ;)
Command 40: 40;Nume;CodFiscal;Adresa            Info client (inainte de cmd 0)
```

## Taskuri Viitoare

### P0: Mod Offline Avansat
- Service Worker complet, IndexedDB, sync coada offline

### P1: Bridge Auto-Start
- Bridge sa porneasca automat cu Windows/PWA

### P2: Import NIR din PDF
- Parsare facturi furnizori din PDF

### P3: Integrare Verifone V200c
- Terminal POS card (blocat pana la obtinerea documentatiei ECR)

## Structura Fisiere Cheie
```
/app/backend/
  server.py              - API principal FastAPI + Fiscal Job Queue + Held Orders
  fiscal_bridge.py       - Bridge local (v3.0) cloud polling
  install_bridge.bat     - Script instalare
  start_bridge.bat       - Script pornire
  actualizeaza_bridge.bat - Script actualizare
/app/frontend/src/
  pages/POSPage.js       - POS cu hold orders backend, F-keys, offline mode, transaction ID
  pages/CashOperationsPage.js - Operatiuni casa
  pages/ProductsPage.js  - Gestiune produse
  pages/StockPage.js     - Stoc & Inventar cu alerte severity/deficit
  pages/ReportsPage.js   - Rapoarte
  components/Layout.js   - Layout cu sidebar si badge alerte stoc
```

## API Endpoints Principale
- `POST /api/auth/login` - Autentificare
- `GET/POST /api/products` - Produse CRUD
- `POST /api/sales` - Creare vanzare (cu transaction_id, idempotent)
- `POST /api/cash-operations` - Operatiuni casa
- `GET /api/cash-operations/daily-stats` - Statistici zilnice
- `POST /api/held-orders` - Creare comanda in asteptare (rezerva stoc)
- `GET /api/held-orders` - Lista comenzi active (expira automat >24h, stoc ramane dedus)
- `POST /api/held-orders/{id}/restore` - Restaureaza comanda (restaureaza stoc)
- `POST /api/held-orders/{id}/cancel` - Anuleaza comanda (restaureaza stoc)
- `GET /api/stock/alerts` - Alerte stoc cu severity si deficit
- `GET /api/stock/dashboard` - Dashboard stoc
- `POST /api/fiscal/queue` - Trimite comanda fiscala
- `GET /api/fiscal/pending` - Bridge poll-uieste joburi
- `GET /api/fiscal/bridge-status` - Status bridge
