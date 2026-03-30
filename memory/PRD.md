# ANDREPAU POS - Product Requirements Document

## Descriere Proiect
Aplicatie completa de gestiune magazin si POS (Point of Sale) pentru magazinul de materiale de constructii **ANDREPAU**. Aplicatie in limba romana, optimizata pentru Windows desktop si tablete.

## Arhitectura
- **Frontend**: React + Tailwind CSS + Shadcn UI (PWA)
- **Backend**: FastAPI + Python + MongoDB
- **Bridge Fiscal Local**: Python script (v3.2 PRODUCTIE)
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
10. Cautare CUI (ANAF)
11. NIR (Nota Intrare Receptie) - Manual + Import PDF
12. Comenzi in Asteptare cu Rezervare Stoc
13. Mod Offline Baza
14. Shortcut-uri F-key
15. Prevenire Vanzari Duplicate
16. Alerte Stoc Minim
17. Dashboard Deschidere Zi
18. **Import NIR din PDF** - PyMuPDF blocks, creare automata produse noi, detectare furnizor
19. **Import CSV Produse** - Preview, template, Nou/Actualizare
20. **Post-NIR Coduri de Bare** - Dialog scanare coduri dupa orice NIR
21. **Cautare cu Filtru Pret Separat** - Camp denumire (stanga) + Camp pret optional (dreapta), ex: "pompa" + "620 RON" → gaseste pompa cu pret ~620
22. **Cautare Fuzzy Multi-cuvant** - Orice cuvant din orice pozitie
23. **3 Facturi PDF Test** - DEDEMAN (8 prod), HORNBACH (6 prod), LEROY MERLIN (9 prod)
24. **Cautare CUI via Bridge Local** - Fallback ANAF prin bridge (IP rezidential) cand VPS-ul e blocat
25. **Bridge URL actualizat** - start_bridge.bat + actualizeaza_bridge.bat → andrepau.com
26. **ANAF v9 Endpoint** - Cautare CUI functioneaza de pe VPS/server (v8 era blocat)
27. **Import NIR - Potrivire Exacta** - Doar cuvant cu cuvant; produs NOU daca nu se gaseste identic
28. **Buton Sterge Toate Produsele** - Cu dublu warning (trebuie scris "STERGE TOATE")
29. **Deschidere Zi - Sold Manual Optional** - Camp optional pentru soldul de inceput de zi
30. **TVA Bulk Update** - Schimbare cota TVA la toate produsele (preset 9/19/21/25%)
31. **Comenzi in Asteptare 12h** - Expira la 12 ore (nu 24)
32. **Login fara Demo** - Conturile demo nu mai sunt afisate
33. **Import .xls (Excel vechi)** - Suport format .xls via xlrd + normalizare coloane (PretAchizitie, CotaTVA, StocInitial, UM=M→metru)

## Taskuri Viitoare
- P1: Mod Offline Avansat
- P2: Calculator rest + configurare sertar (ca la supermarket)
- P2: Raport Z (End of Day) - DOAR dashboard vizualizare, fara comenzi fiscale
- P2: Sectiune Update-uri ANAF
- P2: Optimizare mobila (responsive)
- P3: Refactoring server.py (separare rute)
- P3: Bridge Auto-Start
- P4: Verifone V200c (blocat pe documentatie)
- P4: Import NIR din Excel
- P4: Istoric Preturi / Comparator preturi pe furnizor
- Electron (PAUZA)
