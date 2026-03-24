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

### Complet (Functional)
1. **Sistem de autentificare** - JWT, roluri admin/casier
2. **Gestiune produse** - CRUD complet, import Excel, categorii, cod bare
3. **Pagina POS** - Vanzare cu cos, cautare produse, categorii, discount, hold orders, factura cu CUI
4. **Integrare Bridge Fiscal (Cloud Polling)** - PWA → Cloud API → Bridge polls → Printer
5. **Operatiuni Casa** - Raport X/Z, Intrare/Iesire numerar, Deschide sertar, Istoric, Status bridge
6. **Bridge Service v3.0** - Cloud polling, comenzi corecte din Manual SuccesDRV 8.5
7. **Descarcare Bridge ZIP** - Endpoint /api/bridge/download-direct
8. **Stoc & Inventar** - Dashboard, alerte stoc scazut, export Excel
9. **Rapoarte** - Vanzari pe zi/luna, top produse, profit
10. **Furnizori** - CRUD complet
11. **Cautare CUI (ANAF)** - Cache local cu firme romanesti + OpenAPI.ro
12. **NIR (Nota Intrare Receptie)** - Receptie marfa
13. **Comenzi in Asteptare cu Rezervare Stoc** - Hold orders salvate in backend, stoc dedus la hold, restaurat la restore/cancel/expirare 24h
14. **Mod Offline Baza** - Detectare offline, cache produse in localStorage, coada vanzari offline, sincronizare automata
15. **Shortcut-uri F-key** - F9=Numerar, F7=Card, F11=Anulare cos
16. **Afisare produse imbunatatita** - Nume pe 3 linii, stoc vizibil, tooltip pe hover
17. **TVA actualizat** - Conform Legea 141/2025 (21% standard)

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

### P0: Deducere Atomica Stoc
- Stocul se deduce DOAR dupa confirmarea tiparirii bonului fiscal
- Flux anulare cu restaurarea stocului

### P1: Alerte Stoc Minim
- Sistem robust de notificari pentru produse sub pragul minim
- Badge 100 in sidebar sa fie functional si clar

### P2: Prevenire Vanzari Duplicate
- ID tranzactie unic in fluxul de vanzare

### P3: Logare Profesionala
- Log detaliat pentru operatiuni fiscale, POS, stoc, erori

### P4: Mod Offline Avansat
- Service Worker complet, IndexedDB, sync coadă offline

### P5: Bridge Auto-Start
- Bridge sa porneasca automat cu Windows/PWA

### P6: Import NIR din PDF
- Parsare facturi furnizori din PDF

### P7: Integrare Verifone V200c
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
  pages/POSPage.js       - POS cu hold orders backend, F-keys, offline mode
  pages/CashOperationsPage.js - Operatiuni casa
  pages/ProductsPage.js  - Gestiune produse
  pages/StockPage.js     - Stoc & Inventar
  pages/ReportsPage.js   - Rapoarte
  components/Layout.js   - Layout cu sidebar si alerte stoc
```

## API Endpoints Principale
- `POST /api/auth/login` - Autentificare
- `GET/POST /api/products` - Produse CRUD
- `POST /api/sales` - Creare vanzare
- `POST /api/cash-operations` - Operatiuni casa
- `GET /api/cash-operations/daily-stats` - Statistici zilnice
- `POST /api/held-orders` - Creare comanda in asteptare (rezerva stoc)
- `GET /api/held-orders` - Lista comenzi active (expira automat >24h)
- `POST /api/held-orders/{id}/restore` - Restaureaza comanda (restaureaza stoc)
- `POST /api/held-orders/{id}/cancel` - Anuleaza comanda (restaureaza stoc)
- `POST /api/fiscal/queue` - Trimite comanda fiscala
- `GET /api/fiscal/pending` - Bridge poll-uieste joburi
- `GET /api/fiscal/bridge-status` - Status bridge
- `GET /api/bridge/download-direct` - Descarca ZIP bridge

## Integrari
- **INCOTEX Succes M7**: FUNCTIONAL via cloud polling
- **Verifone V200c**: NOT STARTED (asteptam documentatie ECR)
