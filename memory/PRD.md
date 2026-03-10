# ANDREPAU POS - Product Requirements Document

## Descriere Proiect
Aplicatie completa de gestiune magazin si POS (Point of Sale) pentru magazinul de materiale de constructii **ANDREPAU**. Aplicatie in limba romana, optimizata pentru Windows desktop si tablete.

## Arhitectura
- **Frontend**: React + Tailwind CSS + Shadcn UI (PWA)
- **Backend**: FastAPI + Python + MongoDB
- **Bridge Fiscal Local**: Python/Flask (ruleaza pe PC-ul din magazin)
- **Comunicare Hardware**: SuccesDrv → ONLINE.TXT/ERROR.TXT → INCOTEX Succes M7

## Credentiale
- Admin: `admin` / `admin123`
- Casier: `casier` / `casier123`

## Ce s-a implementat

### Complet (Functional)
1. **Sistem de autentificare** - JWT, roluri admin/casier
2. **Gestiune produse** - CRUD complet, import Excel, categorii, cod bare
3. **Pagina POS** - Vanzare cu cos, cautare produse, categorii, discount, hold orders, factura cu CUI
4. **Integrare Bridge Fiscal** - POS-ul comunica cu bridge-ul local pentru a printa bonul fiscal INAINTE de a salva vanzarea
5. **Operatiuni Casa** - Pagina dedicata: Raport X/Z, Intrare/Iesire numerar, Deschide sertar, Istoric, Status bridge
6. **Bridge Service v3.0** (`fiscal_bridge.py`) - Complet rescris cu formatul corect din Manual SuccesDRV 8.5 (2023):
   - Comenzi: 0 (deschidere bon), 1 (articol), 5 (plata), 14 (anulare), 15 (Raport Z), 25 (numerar in/out), 30 (Raport X), 40 (info client), 46 (copie bon), 67 (totaluri), 106 (sertar)
   - Preturi in BANI (x100), Cantitati cu punct zecimal
   - CARD fara suma (5;;2;1;0), trebuie sa fie ULTIMA forma de plata
   - Pagina de test la http://localhost:5555/test
7. **Descărcare Bridge ZIP** - Endpoint /api/bridge/download (fiscal_bridge.py + .bat scripts)
8. **Stoc & Inventar** - Dashboard, alerte stoc scazut, export Excel
9. **Rapoarte** - Vanzari pe zi/luna, top produse
10. **Furnizori** - CRUD complet
11. **Cautare CUI (ANAF)** - Cache local cu 3.7M firme romanesti
12. **NIR (Nota Intrare Receptie)** - Receptie marfa

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

### P2: Deducere Atomica Stoc
- Stocul se deduce DOAR dupa confirmarea tiparirii bonului fiscal
- Flux anulare cu restaurarea stocului

### P3: Fix badge "100" alerta stoc
- Badge "100 produse cu stoc scazut" in sidebar

### P4: Alerte Stoc Minim
- Sistem robust de notificari pentru produse sub pragul minim

### P5: Prevenire Vanzari Duplicate
- ID tranzactie unic in fluxul de vanzare

### P6: Logare Profesionala
- Log detaliat pentru operatiuni fiscale, POS, stoc, erori

### P7: Import NIR din PDF
- Parsare facturi furnizori din PDF

### P8: Integrare Verifone V200c
- Terminal POS card (blocat pana la obtinerea documentatiei ECR)

## Structura Fisiere Cheie
```
/app/backend/
  server.py              - API principal FastAPI
  fiscal_bridge.py       - Bridge local (v3.0) pentru casa de marcat
  install_bridge.bat     - Script instalare
  start_bridge.bat       - Script pornire
/app/frontend/src/
  pages/POSPage.js       - Pagina POS cu integrare bridge
  pages/CashOperationsPage.js - Operatiuni casa
  pages/ProductsPage.js  - Gestiune produse
  pages/StockPage.js     - Stoc & Inventar
  pages/ReportsPage.js   - Rapoarte
  components/Layout.js   - Layout cu sidebar si alerte stoc
```

## API Endpoints Principale
- `POST /api/auth/login` - Autentificare
- `GET/POST /api/products` - Produse CRUD
- `POST /api/sales` - Creare vanzare (cu fiscal_number, fiscal_status)
- `POST /api/cash-operations` - Inregistrare operatiuni casa
- `GET /api/cash-operations/daily-stats` - Statistici zilnice
- `GET /api/bridge/download` - Descarca ZIP bridge service
- `POST /api/anaf/search-cui` - Cautare firma

## Integrari
- **INCOTEX Succes M7**: IN PROGRESS (bridge complet, testare hardware necesara)
- **Verifone V200c**: NOT STARTED (asteptam documentatie ECR)
