# ANDREPAU POS - Product Requirements Document

## Descriere Proiect
Aplicatie completa de gestiune magazin si POS (Point of Sale) pentru magazinul de materiale de constructii **ANDREPAU**. Aplicatie in limba romana, optimizata pentru Windows desktop si tablete.

## Arhitectura
- **Frontend**: React + Tailwind CSS + Shadcn UI (PWA)
- **Backend**: FastAPI + Python + MongoDB
- **Bridge Fiscal Local**: Python script (ruleaza pe PC-ul din magazin, polling cloud)
- **Comunicare Hardware**: Cloud Queue → Bridge polls → SuccesDrv → ONLINE.TXT → INCOTEX Succes M7
- **Desktop (Electron)**: Setup complet, comunica direct cu bridge-ul local (fara cloud) - permite bonuri offline

## Credentiale
- Admin: `admin` / `admin123`
- Casier: `casier` / `casier123`

## Ce s-a implementat

### Complet (Functional)
1. **Sistem de autentificare** - JWT, roluri admin/casier
2. **Gestiune produse** - CRUD complet, import Excel, categorii, cod bare
3. **Pagina POS** - Vanzare cu cos, cautare, categorii, discount, factura cu CUI
4. **Integrare Bridge Fiscal (Cloud Polling)** - PWA → Cloud API → Bridge polls → Printer
5. **Operatiuni Casa** - Raport X/Z, Intrare/Iesire numerar, Deschide sertar, Istoric
6. **Bridge Service v3.0** - Cloud polling, comenzi corecte din Manual SuccesDRV 8.5
7. **Descarcare Bridge ZIP** - Endpoint /api/bridge/download-direct
8. **Stoc & Inventar** - Dashboard, export Excel
9. **Rapoarte** - Vanzari pe zi/luna, top produse, profit
10. **Furnizori** - CRUD complet
11. **Cautare CUI (ANAF)** - Cache local + OpenAPI.ro
12. **NIR (Nota Intrare Receptie)** - Receptie marfa
13. **TVA actualizat** - Conform Legea 141/2025 (21%)
14. **Comenzi in Asteptare cu Rezervare Stoc** - Hold cu stoc dedus, restaurat la restore/cancel, RAMANE dedus la expirare 24h
15. **Mod Offline Baza** - Detectare, cache produse, coada vanzari, sync automata
16. **Shortcut-uri F-key** - F9=Numerar, F7=Card, F11=Anulare (etichete vizibile)
17. **Afisare produse imbunatatita** - 3 linii cu tooltip, stoc per produs
18. **Eliminare dialog bon** - Finalizare directa cu toast
19. **Prevenire Vanzari Duplicate** - Transaction ID unic, backend idempotent
20. **Alerte Stoc Minim** - Severitate (critical/warning), deficit, sortare, icoane, rezumat
21. **Logare Profesionala** - [SALE], [CASH], [FISCAL], [STOCK] cu detalii complete
22. **Dashboard Deschidere Zi** - Sold casa, status bridge, hold, alerte stoc, checklist, "INCEPE ZIUA"
23. **Setup Electron Desktop** - Config complet pentru build aplicatie nativa Windows cu bonuri offline
24. **Bridge v3.2 PRODUCTIE** - Eliminate butoanele de bon test, comanda manuala si endpoint /fiscal/test-command. Curatare ONLINE.TXT la pornire.

## Taskuri Viitoare

### P0: Build & Test Electron Desktop
- Utilizatorul trebuie sa ruleze `yarn electron-dev` pe PC-ul din magazin
- Testare comunicare directa cu bridge-ul local
- Build installer Windows (.exe)

### P1: Mod Offline Avansat
- Service Worker complet, IndexedDB, sync coada offline

### P2: Bridge Auto-Start
- Bridge sa porneasca automat cu Windows/Electron

### P3: Import NIR din PDF
- Parsare facturi furnizori din PDF

### P4: Integrare Verifone V200c
- Terminal POS card (blocat pe documentatie ECR)

## Structura Fisiere Cheie
```
/app/backend/
  server.py              - API principal + Fiscal Queue + Held Orders + Opening Summary
  fiscal_bridge.py       - Bridge local (v3.0) cloud polling
/app/frontend/
  electron/main.js       - Electron main process (comunica direct cu bridge)
  electron/preload.js    - Expune bridge API catre React
  electron-builder.json  - Config build installer Windows
  ELECTRON_README.md     - Documentatie Electron
  src/pages/
    StartDayPage.js      - Dashboard deschidere zi
    POSPage.js           - POS cu hold, F-keys, offline, transaction ID
    CashOperationsPage.js - Operatiuni casa
    StockPage.js         - Stoc cu alerte severity/deficit
```

## API Endpoints Principale
- `POST /api/auth/login` - Autentificare
- `GET /api/daily/opening-summary` - Dashboard deschidere zi
- `GET/POST /api/products` - Produse CRUD
- `POST /api/sales` - Creare vanzare (cu transaction_id, idempotent)
- `POST /api/held-orders` - Hold cu rezervare stoc
- `GET /api/held-orders` - Lista (auto-expira >24h, stoc ramane dedus)
- `POST /api/held-orders/{id}/restore` - Restaurare (stoc restaurat)
- `POST /api/held-orders/{id}/cancel` - Anulare (stoc restaurat)
- `GET /api/stock/alerts` - Alerte cu severity si deficit
- `POST /api/fiscal/queue` - Comanda fiscala
- `GET /api/fiscal/pending` - Bridge poll
