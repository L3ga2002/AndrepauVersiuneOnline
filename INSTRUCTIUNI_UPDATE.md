# INSTRUCTIUNI UPDATE ANDREPAU POS

## Ce s-a schimbat in aceasta actualizare

### 1. Bug critic fixat: Dublu-click pe "Genereaza Factura cu CUI"
**Problema**: Apasai de doua ori butonul si se printau DOUA bonuri fiscale.
**Fix**: Butoanele "Genereaza Factura", "Finalizeaza Plata", "Continua fara bon fiscal" si calculator-ul Numerar sunt ACUM DEZACTIVATE automat cat timp se proceseaza o plata. Cand butonul e dezactivat, se afiseaza "Se proceseaza..." si un spinner animat.

### 2. Sincronizare stocuri VPS <-> Local (REPARATA COMPLET)
**Problema**: Daca vindeai offline, stocul se decrementa doar local. Daca vindeai online, stocul se decrementa doar online. Niciodata nu se sincronizau intre ele.
**Fix complet**:
- Adaugat endpoint nou: `GET /api/sync/sales-since` - returneaza vanzarile create dupa un anumit timestamp
- Adaugat endpoint nou: `POST /api/sync/apply-remote-sales` - primeste vanzari de pe VPS si decrementeaza stocul local
- Layout.js (frontend) acum ruleaza FULL SYNC la fiecare 15 secunde (inainte era doar 30s si doar cand existau vanzari nesincronizate)
- Fluxul acum este bidirectional:
  - **Local -> VPS**: vanzarile locale urca la VPS care decrementeaza stocul VPS
  - **VPS -> Local**: vanzarile VPS coboara la Local care decrementeaza stocul local
- Produsul `updated_at` se actualizeaza acum si cand se decrementeaza stocul (fix pentru detectarea modificarilor in sync)
- IMPORTANT: `stoc` NU se mai copiaza prin `/sync/products/push` cand se actualizeaza produsele existente (doar la insert produs nou). Stocul este gestionat EXCLUSIV prin sincronizarea vanzarilor, ca sa nu apara conflicte.

### 3. Import NIR din PDF (REPARAT pentru formatul tau)
**Problema**: PDF-ul TOP_2026001074.pdf nu era citit - 0 produse extrase.
**Fix**:
- Rescris parser PDF pentru formatul multi-block (NIR generat de vechiul sistem cu coloane extinse: Nr | Denumire | UM | Cant | Pret furnizor | ... | Pret vanzare unitar | Valoare total)
- Parser-ul extrage acum pret VANZARE (nu pret achizitie), conform specificatiei tale
- Testat cu PDF-ul tau: **12/12 produse extrase** corect (25.00, 60.00, 41.00 RON etc.)
- La produse noi: pret_vanzare din PDF, fara markup *1.3
- La produse existente: se pastreaza denumirea din sistem, se actualizeaza pret_vanzare si se incrementeaza stocul

### 4. Dezduplicare automata prin cod de bare
**Problema**: Cand importi NIR PDF si creezi produs nou cu denumire usor diferita, apoi scanezi codul de bare care exista deja in sistem, aveai dubluri.
**Fix**: Cand salvezi un cod de bare care exista deja pe alt produs, sistemul face automat MERGE:
- Transfera stocul pe produsul existent
- Sterge produsul duplicat
- Pastreaza denumirea produsului ORIGINAL
- Actualizeaza pret_vanzare
- Mesajul de confirmare te informeaza cate au fost unificate automat

### 5. Intarziere bon INCOTEX (REDUSA)
**Problema**: Uneori bonul se printa instantaneu, alteori dura 1-3 secunde.
**Fix**: Bridge-ul fiscal face acum polling la fiecare **0.5 secunde** (inainte 2 secunde). Frontend-ul verifica rezultatul la fiecare **0.5 secunde** (inainte 1 secunda). Raspuns ~3-4x mai rapid. Va trebui sa instalezi bridge-ul nou pe PC-ul de la casa (vezi mai jos).

### 6. Ecran alb pe offline (FIXAT)
**Problema**: Aplicatia offline dadea ecran alb aleatoriu si trebuia sa o repornesti.
**Fix**: Adaugat React ErrorBoundary care intercepteaza erorile si:
- Afiseaza un mesaj clar in loc de ecran alb
- Auto-reincarca aplicatia dupa 3 secunde (daca e prima eroare in ultima ora)
- Ofera butoane "Reincarca aplicatia" si "Reset complet" pentru cazuri severe

### 7. Ferestre CMD ascunse pe offline (FIXAT)
**Problema**: Cand porneai ANDREPAU.bat, apareau 2 ferestre CMD enervante.
**Fix**: Inlocuit cu `ANDREPAU_START.vbs` care porneste totul ASCUNS folosind `pythonw.exe` (Python fara consola). Acum `ANDREPAU.bat` cheama acest VBS. Nu mai vezi nicio fereastra CMD, doar browserul in mod aplicatie (Chrome --app).

---

# UPDATE PE VARIANTA ONLINE (VPS)

Pasii pentru a aplica update-urile pe VPS:

## Pas 1: Conecteaza-te la VPS prin SSH
```bash
ssh root@<IP-VPS>
```

## Pas 2: Du-te in folderul aplicatiei
```bash
cd /app   # sau unde ai aplicatia (de obicei /var/www/andrepau sau /app)
```

## Pas 3: Pull modificarile din Git
```bash
git pull origin main
```
(daca folosesti alt branch, inlocuieste `main` cu numele lui)

## Pas 4: Reporneste serviciile
Daca folosesti supervisor (cazul default pe Emergent):
```bash
sudo supervisorctl restart backend
sudo supervisorctl restart frontend
```

Sau daca folosesti systemd:
```bash
sudo systemctl restart andrepau-backend
sudo systemctl restart andrepau-frontend
```

## Pas 5: Verifica ca merge
Deschide in browser: `https://<domeniul-tau-vps>` si logheaza-te cu admin/admin123.
Verifica ca vezi "ONLINE (VPS)" in bara stanga sus.

---

# UPDATE PE VARIANTA OFFLINE (PC-ul din magazin)

## Metoda recomandata: ACTUALIZEAZA_BRIDGE.bat

1. Pe PC-ul din magazin, **inchide aplicatia** folosind `OPRESTE_ANDREPAU.bat` (sau dublu-click pe el)
2. Deschide browserul si mergi pe varianta online (pe VPS): `https://<domeniul-tau-vps>`
3. Logheaza-te ca admin si mergi la **Setari -> Bridge Fiscal -> Descarca Bridge Service**
4. Se descarca un `.zip` cu toate fisierele actualizate
5. Dezarhiveaza `.zip`-ul peste folderul tau de instalare (suprascrie fisierele)
   - Folderul tipic: `C:\ANDREPAU-POS\` sau unde l-ai instalat
6. Ruleaza `update_local.bat` (din `C:\ANDREPAU-POS\local_setup\`) - face `git pull` automat
7. Porneste din nou aplicatia: dublu-click pe `ANDREPAU.bat`
8. Ar trebui sa apara **doar browserul**, fara ferestre CMD.

## Metoda manuala: Git pull pe PC-ul local
Daca ai instalat prin git direct:
1. Inchide aplicatia: dublu-click `OPRESTE_ANDREPAU.bat`
2. Deschide Command Prompt si navigheaza la folderul aplicatiei:
   ```cmd
   cd C:\ANDREPAU-POS
   git pull origin main
   cd backend
   pip install -r requirements.txt
   cd ..\frontend
   yarn install
   yarn build
   ```
3. Reporneste aplicatia: dublu-click `ANDREPAU.bat`

---

# VERIFICARI DUPA UPDATE

Dupa ce ai actualizat AMBELE variante (online si offline), verifica:

## 1. Test double-click (CRITIC)
- Mergi la POS pe oricare din variante
- Pune un produs in cos, apasa "FACT" (Factura)
- Introdu un CUI valid (ex: RO14586700), apasa Cauta
- Dupa ce se completeaza automat, da **DUBLU-CLICK RAPID** pe "Genereaza Factura"
- **Trebuie sa se printeze UN SINGUR bon**. Butonul va arata "Se proceseaza..." imediat dupa primul click.

## 2. Test sincronizare stocuri
- **Test A**: Vinde un produs pe VPS (online). Asteapta 30 secunde. Verifica pe instanta locala ca stocul s-a decrementat. ✓
- **Test B**: Vinde un produs pe local (offline, cu VPS pornit). Asteapta 30 secunde. Verifica pe VPS ca stocul s-a decrementat. ✓
- **Test C**: Adauga un produs nou pe VPS. Asteapta 30 secunde. Verifica pe local ca apare produsul nou. ✓

## 3. Test NIR PDF
- Mergi pe **Stoc & Inventar -> Import din PDF**
- Selecteaza fisierul tau `TOP_2026001074.pdf`
- Ar trebui sa vezi **12 produse** in tabel cu preturi corecte: 25.00, 60.00, 41.00, 29.00, 33.00...
- Selecteaza furnizorul, pune numarul facturii, apasa "Salveaza NIR"
- Se deschide dialog pentru scanare coduri de bare - scaneaza cate un produs
- Daca scanezi un cod care exista deja pe alt produs, vei primi mesaj: "X produse duplicate unificate automat (stoc transferat)"

## 4. Test bridge fiscal (INCOTEX)
- Pe varianta pe care ai conectata casa de marcat, fa o vanzare simpla
- Bonul trebuie sa se printeze in maxim 1-2 secunde (nu 3-5 cum era inainte)

## 5. Test offline - ecran alb
- Pe varianta locala (offline), lasa aplicatia deschisa cateva ore / inchide internetul si foloseste-o intens
- Daca apare o eroare, acum vezi un mesaj clar cu buton "Reincarca aplicatia" in loc de ecran alb
- Aplicatia se auto-reincarca dupa 3 secunde

## 6. Test lansare offline fara CMD
- Porneste `ANDREPAU.bat`
- Asteapta 5-7 secunde
- Ar trebui sa se deschida **doar browserul** (Chrome in mod aplicatie, fara bara de adresa)
- **NU** trebuie sa mai vezi ferestre CMD pe taskbar

---

# TROUBLESHOOTING

## "Imi apar tot CMD-urile dupa update"
- Verifica ca ai `ANDREPAU_START.vbs` in folderul de instalare (alaturi de `ANDREPAU.bat`)
- Deschide `ANDREPAU.bat` cu Notepad - ar trebui sa contina 7 linii scurte
- Daca tot nu merge, instaleaza Python cu optiunea "Add to PATH" bifata
- Verifica ca ai `pythonw.exe` (nu doar `python.exe`): `where pythonw`

## "Stocurile tot nu se sincronizeaza"
- Verifica URL-ul VPS setat: in browser deschide consola (F12) si scrie:
  ```javascript
  localStorage.getItem('andrepau_vps_url')
  ```
- Daca e gol sau gresit, seteaza-l corect in **Setari -> Sincronizare VPS**
- Verifica ca vezi badge-ul verde "Sincronizat cu VPS" in bara stanga
- Intervalul de sincronizare este 15 secunde - poate dura pana la 15s pentru a vedea modificarea

## "NIR-ul tot nu citeste produsele din PDF"
- Verifica ca PDF-ul contine text real (nu e scanat ca imagine)
- Deschide PDF-ul, selecteaza text cu mouse-ul - daca poti copia text, merge
- Daca e PDF scanat, trebuie OCR (nu suportat momentan)
- Trimite-mi PDF-ul si pot adapta parser-ul pentru un nou format

## "Bonul tot vine cu intarziere"
- Verifica ca ai actualizat `fiscal_bridge.py` pe PC-ul cu casa de marcat
- Restart la bridge: `OPRESTE_ANDREPAU.bat` apoi `ANDREPAU.bat`
- Verifica ca vezi "Casa conectata" (verde) in POS, nu "Casa deconectata" (rosu)

---

# CONCLUZIE

Toate task-urile P0 si P1 au fost rezolvate si testate (16/16 teste backend trecute). Pentru probleme sau intrebari, contacteaza-ma direct.
