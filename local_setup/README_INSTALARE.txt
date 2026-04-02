============================================================
     ANDREPAU POS - GHID COMPLET INSTALARE SI UTILIZARE
============================================================


============================================================
PARTEA 1: INSTALARE PE PC-UL DIN MAGAZIN (o singura data)
============================================================

PASUL 1: Deschide CMD
    - Apasa tasta Windows
    - Scrie: cmd
    - Click pe "Command Prompt"

PASUL 2: Scrie aceste 2 comenzi (una cate una):

    cd C:\
    git clone https://github.com/L3ga2002/AndrepauVersiuneOnline.git ANDREPAU

    NOTA: Daca apare eroare "git is not recognized":
    - Descarca Git de pe: https://git-scm.com/download/win
    - Instaleaza-l (Next, Next, Finish)
    - Inchide CMD si deschide altul nou
    - Repeta comenzile de mai sus

PASUL 3: Ruleaza instalarea automata:

    C:\ANDREPAU\INSTALEAZA_TOTUL.bat

    Scriptul face TOTUL singur:
    - Verifica daca Python e instalat, daca nu il descarca
      IMPORTANT: Cand se deschide installerul Python bifeaza:
      [x] Add Python to PATH (jos de tot!)
      Apoi click "Install Now" si asteapta
    - Verifica Node.js, daca nu il descarca
      Click: Next, Next, Next, Install, Finish
    - Verifica MongoDB (fisier mare ~500MB, asteapta 2-5 min)
      Click: Next, Accept, "Complete"
      IMPORTANT: Lasa bifat [x] Install MongoDB as a Service
      Next, Install, Finish
    - Verifica Git (daca nu e instalat deja)
    - Descarca aplicatia din GitHub
    - Instaleaza toate dependentele automat
    - Construieste aplicatia (dureaza 1-2 min)
    - Creeaza shortcut "ANDREPAU POS" pe Desktop
    - Porneste aplicatia prima data

PASUL 4: Gata! Aplicatia se deschide automat.
    - Cont admin:  admin / admin123
    - Cont casier: casier / casier123


============================================================
PARTEA 2: PRIMA CONFIGURARE (o singura data)
============================================================

PASUL 1: Import produse de pe VPS
    - Deschide VPS-ul in browser (https://andrepau.com)
    - Logheaza-te ca admin
    - Mergi la Setari > Backup
    - Click "Export Excel Produse" - descarca fisierul .xlsx
    - Pe aplicatia locala (localhost:8001)
    - Mergi la Produse > Import > alege fisierul .xlsx
    - Asteapta sa se importe (poate dura 1-2 min)

PASUL 2: Configurare sincronizare automata
    - Pe aplicatia locala, mergi la Setari > Sincronizare
    - La "Adresa VPS (URL)" scrie adresa site-ului:
      Exemplu: https://andrepau.com
    - La "Cheie Sincronizare" lasa: andrepau-sync-2026
    - Click "Salveaza Configurare"
    - De acum, produsele si vanzarile se sincronizeaza
      automat la fiecare 30 secunde cand ai internet

PASUL 3: Shortcut pe Desktop (daca nu s-a creat automat)
    - Deschide "Acest PC" sau "My Computer"
    - Navigheaza la C:\ANDREPAU\
    - Click dreapta pe ANDREPAU.bat
    - "Send to" > "Desktop (create shortcut)"


============================================================
PARTEA 3: UTILIZARE ZILNICA
============================================================

PORNIRE APLICATIE:
    - Dublu-click pe "ANDREPAU POS" de pe Desktop
    - Aplicatia se deschide ca un program normal
    - Nu apar ferestre CMD vizibile
    - Functioneaza cu sau fara internet

OPRIRE APLICATIE:
    - Dublu-click pe C:\ANDREPAU\OPRESTE_ANDREPAU.bat
    - Sau inchide browserul si serviciile se opresc singure
      la restart PC

CU INTERNET:
    - In sidebar scrie "MOD LOCAL (Offline)" dar
      vanzarile se sincronizeaza automat cu VPS-ul
    - Patronul vede totul actualizat pe VPS

FARA INTERNET:
    - Aplicatia merge la fel, fara intrerupere
    - Faci vanzari numerar + bonuri fiscale normal
    - Cand revine internetul, se sincronizeaza automat

CASA DE MARCAT (INCOTEX):
    - Bridge-ul porneste automat cu aplicatia
    - SuccesDrv trebuie sa fie pornit (Start procesare)
    - Verifica pe Deschidere Zi: "Casa de Marcat: Conectata"


============================================================
PARTEA 4: ACTUALIZARI
============================================================

CAND PRIMESTI O ACTUALIZARE NOUA:

PE VPS (serveru online):
    1. Pe Emergent: click "Save to Github"
    2. Conecteaza-te pe VPS prin SSH (PuTTY)
    3. Scrie:  /opt/update.sh
    4. Gata!

PE PC-UL LOCAL (din magazin sau de acasa):
    1. Asigura-te ca ai internet
    2. Deschide CMD
    3. Scrie aceste comenzi:

       cd C:\ANDREPAU
       git stash
       git pull origin main
       cd backend
       pip install -r requirements.txt
       cd ..\frontend
       yarn build

    4. Reporneste aplicatia (inchide si redeschide ANDREPAU POS)


============================================================
PARTEA 5: CE SE SINCRONIZEAZA AUTOMAT
============================================================

Intre PC-ul local si VPS se sincronizeaza:

    VANZARI:   Local --> VPS (la fiecare 30 sec)
    PRODUSE:   VPS <--> Local (in ambele directii)
    STOCURI:   Se actualizeaza automat cu vanzarile

Conditii:
    - PC-ul trebuie sa aiba internet
    - URL-ul VPS trebuie configurat in Setari > Sincronizare
    - Cheia de sincronizare trebuie sa fie aceeasi pe ambele


============================================================
PARTEA 6: PROBLEME FRECVENTE
============================================================

1. "Aplicatia nu porneste"
   - Verifica ca MongoDB ruleaza:
     Deschide CMD, scrie: sc query MongoDB
     Daca nu ruleaza: net start MongoDB

2. "Nu am produse pe local"
   - Import din Excel (vezi Partea 2, Pasul 1)
   - Sau asteapta sincronizarea automata (30 sec)

3. "Casa de marcat nu se conecteaza"
   - Verifica ca SuccesDrv e pornit (Start procesare)
   - Verifica cablul USB/COM
   - Testeaza: http://localhost:5555/test

4. "VPS nu se actualizeaza"
   - Verifica ca ai dat "Save to Github" pe Emergent
   - Pe VPS: /opt/update.sh
   - Daca eroare "git stash":
     cd /opt/andrepau && git stash && git pull origin main

5. "Eroare la pip install"
   - Pe VPS foloseste virtualenv:
     source backend/venv/bin/activate
     pip install -r requirements.txt
     deactivate

6. "Nu se sincronizeaza cu VPS"
   - Verifica Setari > Sincronizare > URL VPS
   - Verifica ca ai internet
   - Verifica ca pe VPS e actualizat codul


============================================================
INFORMATII UTILE
============================================================

Aplicatie locala:  http://localhost:8001
Bridge fiscal:    http://localhost:5555/test
Cont admin:       admin / admin123
Cont casier:      casier / casier123
Repo GitHub:      https://github.com/L3ga2002/AndrepauVersiuneOnline

Foldere:
    C:\ANDREPAU\                - folderul principal
    C:\ANDREPAU\ANDREPAU.bat    - pornire aplicatie
    C:\ANDREPAU\backend\        - serverul Python
    C:\ANDREPAU\frontend\       - interfata
    C:\ANDREPAU\local_setup\    - scripturi instalare

============================================================
