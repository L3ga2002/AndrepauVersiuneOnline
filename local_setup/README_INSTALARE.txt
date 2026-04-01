================================================================
    ANDREPAU POS - GHID INSTALARE PE PC WINDOWS
    Aplicatie Offline pentru Magazin
================================================================

CERINTE MINIME:
  - Windows 10 sau 11 (64-bit)
  - 4 GB RAM minim
  - 2 GB spatiu pe disc
  - Conexiune internet (doar pentru instalare si actualizari)

================================================================
PASUL 1: INSTALARE PROGRAME NECESARE
================================================================

1.1. Python (necesar pentru backend si bridge)
     Descarcati de pe: https://www.python.org/downloads/
     La instalare BIFATI:
       [x] Add Python to PATH
       [x] Install for all users
     Restart PC dupa instalare.

1.2. Node.js (necesar pentru frontend)
     Descarcati versiunea LTS de pe: https://nodejs.org/
     Instalati cu setarile implicite.

1.3. MongoDB Community Server (baza de date)
     Descarcati de pe: https://www.mongodb.com/try/download/community
     La instalare alegeti:
       [x] Install MongoDB as a Service
       [x] Run service as Network Service user
     Aceasta face ca MongoDB sa porneasca automat cu Windows.

1.4. Git (necesar pentru actualizari)
     Descarcati de pe: https://git-scm.com/download/win
     Instalati cu setarile implicite.

================================================================
PASUL 2: DESCARCARE APLICATIE
================================================================

Deschideti CMD (Command Prompt) si rulati:

  cd C:\
  git clone https://github.com/CONTUL_GITHUB/andrepau-pos.git ANDREPAU

(Inlocuiti CONTUL_GITHUB cu contul real de GitHub)

================================================================
PASUL 3: INSTALARE APLICATIE
================================================================

Navigati in folder:
  C:\ANDREPAU\local_setup\

Dublu-click pe:
  install_andrepau.bat

Scriptul verifica automat:
  - Python instalat
  - Node.js instalat
  - MongoDB instalat
  - Instaleaza dependentele Python
  - Instaleaza dependentele frontend
  - Construieste aplicatia frontend

================================================================
PASUL 4: PORNIRE APLICATIE
================================================================

Dublu-click pe:
  C:\ANDREPAU\local_setup\start_andrepau.bat

Scriptul porneste automat:
  1. MongoDB (daca nu ruleaza deja)
  2. Backend FastAPI (port 8001)
  3. Bridge fiscal INCOTEX (port 5555)
  4. Deschide browserul la http://localhost:8001

Cont admin:  admin / admin123
Cont casier: casier / casier123

================================================================
PASUL 5: OPRIRE APLICATIE
================================================================

Dublu-click pe:
  C:\ANDREPAU\local_setup\stop_andrepau.bat

SAU inchideti ferestrele CMD cu titlul ANDREPAU.

================================================================
ACTUALIZARI
================================================================

Cand primiti o actualizare noua:

1. Asigurati-va ca aveti conexiune la internet
2. Dublu-click pe: update_local.bat

SAU manual:
  cd C:\ANDREPAU
  git pull origin main
  cd backend && pip install -r requirements.txt
  cd ..\frontend && yarn install && yarn build

Apoi reporniti aplicatia cu start_andrepau.bat.

================================================================
CUM FUNCTIONEAZA ONLINE / OFFLINE
================================================================

MODUL NORMAL (cu internet):
  - Deschideti browserul la adresa VPS: https://andrepau.com
  - Patronul poate accesa din birou
  - Bridge-ul trimite bonuri prin cloud

MODUL OFFLINE (fara internet):
  - Deschideti browserul la: http://localhost:8001
  - Aplicatia detecteaza automat ca e locala
  - Puteti face vanzari numerar + bonuri fiscale
  - Cand revine internetul, vanzarile se sincronizeaza

BRIDGE FISCAL:
  - Porneste automat cu start_andrepau.bat
  - In modul local, bridge-ul comunica direct cu backend-ul
  - SuccesDrv trebuie sa aiba "Start procesare" apasat!
  - Pagina control bridge: http://localhost:5555/test

================================================================
PROBLEME FRECVENTE
================================================================

1. "Python nu este recunoscut"
   → Reinstalati Python cu "Add to PATH" bifat
   → Restartati PC-ul

2. "MongoDB nu porneste"
   → Deschideti Services.msc si cautati "MongoDB"
   → Click dreapta → Start

3. "Eroare la pornire backend"
   → Deschideti CMD in folderul backend
   → Rulati: pip install -r requirements.txt
   → Apoi: python -m uvicorn server:app --port 8001

4. "Bridge nu se conecteaza la casa de marcat"
   → Verificati ca SuccesDrv este pornit si are "Start procesare"
   → Verificati conexiunea COM port/USB
   → Testati la: http://localhost:5555/test → "Diagnostic Complet"

5. "Aplicatia nu se deschide in browser"
   → Deschideti manual: http://localhost:8001
   → Asteptati 10-15 secunde dupa pornire

================================================================
CONTACT SUPORT: [adaugati informatiile de contact]
================================================================
