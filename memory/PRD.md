# ANDREPAU POS - Product Requirements Document

## Descriere Proiect
Aplicatie completa de gestiune magazin si POS (Point of Sale) pentru magazinul de materiale de constructii **ANDREPAU**. Aplicatie in limba romana, optimizata pentru Windows desktop si tablete. APLICATIE LIVE IN PRODUCTIE.

## Arhitectura
- **Frontend**: React + Tailwind CSS + Shadcn UI (PWA)
- **Backend**: FastAPI + Python + MongoDB
- **Bridge Fiscal Local**: Python script (v3.2 PRODUCTIE)
- **VPS**: Hostinger Ubuntu 24.04, deploy via /opt/update.sh
- **Desktop (Electron)**: PAUZA

## Credentiale
- Admin: `admin` / `admin123`
- Casier: `casier` / `casier123`

## Ce s-a implementat

### Complet (Functional)
1. Sistem de autentificare - JWT, roluri admin/casier
2. Gestiune produse - CRUD, import Excel, categorii, cod bare
3. Pagina POS - Vanzare cu cos, cautare, categorii, discount, factura CUI
4. Integrare Bridge Fiscal (Cloud Polling)
5. Operatiuni Casa - Raport X/Z, Intrare/Iesire numerar, Sertar, Istoric
6. Bridge Service v3.2 PRODUCTIE
7. Stoc & Inventar - Dashboard, export Excel
8. Rapoarte - Vanzari pe zi/luna, top produse, profit
9. Furnizori - CRUD complet
10. Cautare CUI (ANAF v9)
11. NIR (Nota Intrare Receptie) - Manual + Import PDF
12. Comenzi in Asteptare cu Rezervare Stoc (12h expirare)
13. Mod Offline Baza
14. Shortcut-uri F-key (F7=Card, F9=Numerar, F11=Anulare) - FIXED stale closure cu refs
15. Prevenire Vanzari Duplicate
16. Alerte Stoc Minim
17. Dashboard Deschidere Zi
18. Import NIR din PDF - PyMuPDF blocks, creare automata produse noi
19. Import CSV/XLS Produse - Preview paginat (100/pag), bulk write MongoDB, import in loturi 500, pret 0 permis
20. Post-NIR Coduri de Bare
21. Cautare cu Filtru Pret Separat
22. Cautare Fuzzy Multi-cuvant
23. Cautare CUI via Bridge Local (fallback ANAF)
24. Import NIR - Potrivire Exacta
25. Buton Sterge Toate Produsele (cu dublu warning)
26. Deschidere Zi - Sold Manual Optional
27. TVA Bulk Update
28. Login fara Demo credentials
29. Fix bon dublu la factura CUI (skipFiscal=true)
30. NGINX client_max_body_size 20M pe VPS

## Taskuri de facut

### P1 - Urgente / Bug-uri
- [ ] **TVA implicit 21%** la adaugare produs manual (nu 19%) - FIX RAPID
- [ ] **Sold Deschidere Zi nu se salveaza** - buton Enter/Salveaza lipsa
- [ ] **Cosul POS se goleste** cand navighezi la Produse/alta pagina - persistenta cos

### P1 - Functionalitati cerute
- [ ] **Calculator Rest + Deschidere Sertar** - Modal in POS: suma primita → rest de dat + comanda hardware sertar
- [ ] **Detalii bon** - click pe bon in istoric → vezi produsele
- [ ] **Copiere/Reprint bon** - doar daca INCOTEX suporta functia COPIE (nu bon fiscal nou!)
- [ ] **Light Mode** - tema cu fundal deschis (nu doar dark mode)
- [ ] **Sold casa la Operatiuni Casa** - nu doar la Deschidere Zi
- [ ] **Suma card la Deschidere Zi** - total bonuri card printate cu succes

### P2 - Planificate
- [ ] Raport Z Dashboard (DOAR vizualizare, fara comenzi fiscale)
- [ ] Sectiune Update-uri ANAF
- [ ] Optimizare Mobila (responsive)

### P3 - Tehnice
- [ ] Refactoring server.py (separare rute in fisiere)
- [ ] Bridge Auto-Start pe Windows

### P4 - Viitor
- [ ] **Integrare Verifone V200c ECR** - BLOCAT pe parola admin de la Raiffeisen/Printec (IP + port ECR necesare). DLL disponibil: ecr_to_pos_v3_RZB.dll, parola arhiva: ecrdevelopmentsuite2020. Comunicare prin Ethernet, functii: Sale(suma), WaitForResponse(), GetLastErrorCode(). Suma in bani (2500=25.00 RON).
- [ ] Import NIR din Excel dedicat
- [ ] Istoric Preturi / Comparator preturi pe furnizor
- [ ] Electron Desktop App (PAUZA)

## Note VPS
- Update: `bash /opt/update.sh`
- Backend venv: `/opt/andrepau/backend/venv/`
- Install deps: `/opt/andrepau/backend/venv/bin/pip install <pachet>`
- NGINX config: `/etc/nginx/sites-available/andrepau` (client_max_body_size 20M)
- Restart backend: `systemctl restart andrepau-backend`
