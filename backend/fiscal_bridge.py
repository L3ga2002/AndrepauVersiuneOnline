#!/usr/bin/env python3
"""
ANDREPAU POS - Bridge Service pentru SuccesDrv (INCOTEX Succes M7)
Versiunea 3.0 - Bazat pe Manual utilizare SuccesDRV 8.5 (2023)

Comunicare bazata pe fisiere:
  - Scrie comenzi in ONLINE.TXT
  - Citeste raspunsuri din ERROR.TXT

FORMAT COMENZI (din manual oficial):
  - Command 0:  Deschidere bon fiscal - 0;NrOperator;Parola;1[;I]
  - Command 1:  Vanzare articol - 1;denumire;UM;CotaTVA;Pret_bani;Cantitate[;den_opt][;grupa]
  - Command 2:  Text aditional - 2;text(max 38 car)
  - Command 3:  Inchidere bon cu numerar (fara rest) - 3
  - Command 5:  Forme de plata - 5;Suma_bani;FormaPl(1-10);1;0[;Text1][;Text2]
  - Command 7:  Discount/Adaos - 7;Tip;Aplicare;Optiune;Procent;Valoare;Atribut[;CotaTVA]
  - Command 8:  Subtotal - 8
  - Command 14: Anulare bon - 14  (FARA punct-virgula!)
  - Command 15: Raport Z - 15  (FARA punct-virgula!)
  - Command 25: Sold initial/Sume retrase - 25;T(1=iesire,2=intrare);Valoare_bani;Motiv;NrOperator
  - Command 30: Raport X - 30  (FARA punct-virgula!)
  - Command 40: Info client - 40;Nume(max32);CodFiscal(max21);Adresa(max28) INAINTE de cmd 0!
  - Command 46: Copie ultimul bon - 46
  - Command 67: Citire totaluri zilnice - 67
  - Command 106: Deschidere sertar - 106

PRETURILE: se inmultesc cu 100 (in bani). Ex: 1.20 RON = 120
CANTITATILE: cu punct zecimal. Ex: 2.5 kg = 2.5
FORME PLATA: 1=Numerar, 2=Card, 3=Tichet masa, 4=Voucher, 5=Bon valoric, 6=Credit
  ATENTIE: Pentru CARD nu se introduce suma! Comanda CARD trebuie sa fie ULTIMA!

INSTALARE PE PC MAGAZIN:
  1. Instalati Python 3.x de pe https://www.python.org/downloads/
     (bifati "Add Python to PATH" la instalare!)
  2. Deschideti CMD si rulati:  pip install flask flask-cors
  3. Copiati acest fisier pe desktop sau in folderul SuccesDrv
  4. Dublu-click pe start_bridge.bat
  5. Deschideti in browser: http://localhost:5555/test
  6. IMPORTANT: Porniti SuccesDrv si apasati "Start procesare"!
"""

from flask import Flask, request, jsonify, make_response
from flask_cors import CORS
import os
import sys
import time
import threading
import logging
from datetime import datetime
import json

# ===================== AUTO-DETECTARE CALE =====================

def find_succesdrv_path():
    """Cauta automat folderul SuccesDrv pe disc"""
    known_paths = [
        r"C:\kit sistem\ANDREPAU\SuccesDrv_8_3",
        r"C:\kit sistem\ANDREPAU\SuccesDrv",
        r"C:\SuccesDrv",
        r"C:\SuccesM7",
        r"C:\Program Files\SuccesDrv",
        r"C:\Program Files (x86)\SuccesDrv",
    ]
    for p in known_paths:
        if os.path.isdir(p):
            return p
    for root_dir in [r"C:\kit sistem", r"C:\\"]:
        if os.path.isdir(root_dir):
            for dirpath, dirnames, filenames in os.walk(root_dir):
                for f in filenames:
                    if 'succesdrv' in f.lower() and f.lower().endswith('.exe'):
                        return dirpath
                if dirpath.count(os.sep) - root_dir.count(os.sep) > 4:
                    dirnames.clear()
    return None

def parse_ini_file(ini_path):
    """Citeste SuccesDRV.INI si extrage configurarile"""
    config = {
        'masca_bon': 'ONLINE',
        'extensie_bon': 'TXT',
        'port': '1',
        'tip_comunicatie': '0',
        'ip': '',
        'port_tcp': '9198',
    }
    if not os.path.exists(ini_path):
        return config
    try:
        with open(ini_path, 'r', encoding='cp1250') as f:
            for line in f:
                line = line.strip()
                if '=' in line:
                    key, val = line.split('=', 1)
                    key = key.strip().lower()
                    val = val.strip()
                    if key == 'masca_bon':
                        config['masca_bon'] = val
                    elif key == 'extensie_bon':
                        config['extensie_bon'] = val
                    elif key == 'port':
                        config['port'] = val
                    elif key == 'tipcomunicatie':
                        config['tip_comunicatie'] = val
                    elif key == 'ip':
                        config['ip'] = val
                    elif key == 'porttcp':
                        config['port_tcp'] = val
    except Exception as e:
        print(f"Eroare citire INI: {e}")
    return config

# ===================== CONFIGURARE =====================

if len(sys.argv) > 1 and not sys.argv[1].startswith('http'):
    SUCCESDRV_PATH = sys.argv[1]
else:
    SUCCESDRV_PATH = find_succesdrv_path() or r"C:\kit sistem\ANDREPAU\SuccesDrv_8_3"

INI_PATH = os.path.join(SUCCESDRV_PATH, 'SuccesDRV.INI')
INI_CONFIG = parse_ini_file(INI_PATH)

ONLINE_FILE = os.path.join(SUCCESDRV_PATH, "ONLINE.TXT")
ERROR_FILE = os.path.join(SUCCESDRV_PATH, "ERROR.TXT")

BRIDGE_PORT = 5555
RESPONSE_TIMEOUT = 30

# Operator implicit (1-10, programat in casa de marcat)
DEFAULT_OPERATOR = 1
DEFAULT_PAROLA = 0

# Mapare unitati de masura din aplicatie la coduri SuccesM7
# Coduri: 1=fara, 2=Buc, 3=Kg, 4=m, 5=L, 6=mp, 7=bax, 8=mc, 9=fara, 10=fara
# Sau text max 5 caractere
UM_MAP = {
    'buc': '2',
    'sac': 'Sac',
    'kg': '3',
    'metru': '4',
    'm': '4',
    'litru': '5',
    'l': '5',
    'rola': 'Rola',
    'mp': '6',
    'mc': '8',
    'bax': '7',
    'set': 'Set',
    'palet': 'Palet',
}

# Mapare cota TVA
# Cotele TVA Romania (actualizat august 2025, Legea 141/2025):
# 1 = TVA A (21% standard), 2 = TVA B (11% redusa), 3 = TVA C (0% scutit),
# 4 = TVA D (9% tranzitorie locuinte), 7 = SCUTIT TVA, 8 = ALTE TAXE
TVA_MAP = {
    21: '1',
    11: '2',
    0: '3',
    9: '4',
    5: '3',
}

# Valorile pentru programarea casei de marcat (comanda 60)
# Format: procent * 100 (ex: 21% = 2100)
DEFAULT_TVA_RATES = {
    'A': 2100,  # 21% standard
    'B': 1100,  # 11% redusa
    'C': 0,     # 0% scutit/export
    'D': 900,   # 9% tranzitorie
    'E': 0,
    'F': 0,
}

# ===================== LOGGING =====================

log_handlers = [logging.StreamHandler()]
try:
    log_file = os.path.join(SUCCESDRV_PATH, "bridge_log.txt")
    log_handlers.append(logging.FileHandler(log_file, encoding='utf-8'))
except:
    pass

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=log_handlers
)
logger = logging.getLogger(__name__)

# ===================== FLASK APP =====================

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

@app.after_request
def add_cors_headers(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
    response.headers['Access-Control-Allow-Private-Network'] = 'true'
    return response

@app.before_request
def handle_preflight():
    """Handle CORS preflight for Private Network Access"""
    if request.method == 'OPTIONS':
        response = app.make_default_options_response()
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        response.headers['Access-Control-Allow-Private-Network'] = 'true'
        return response

fiscal_lock = threading.Lock()

def write_command(commands: list) -> dict:
    """
    Scrie comenzi in ONLINE.TXT si asteapta raspunsul din ERROR.TXT

    Flux:
      1. Sterge ERROR.TXT vechi (daca exista)
      2. Scrie comenzile in ONLINE.TXT
      3. SuccesDrv citeste ONLINE.TXT, il sterge, executa comenzile
      4. SuccesDrv scrie rezultatul in ERROR.TXT
      5. Bridge citeste ERROR.TXT si returneaza rezultatul
    """
    with fiscal_lock:
        try:
            if os.path.exists(ERROR_FILE):
                try:
                    os.remove(ERROR_FILE)
                except:
                    pass

            command_text = '\n'.join(commands)
            logger.info(f"=== TRIMIT COMENZI ===\n{command_text}")

            with open(ONLINE_FILE, 'w', encoding='cp1250') as f:
                f.write(command_text)

            logger.info(f"Fisier ONLINE.TXT creat: {ONLINE_FILE}")

            start_time = time.time()
            while time.time() - start_time < RESPONSE_TIMEOUT:
                if os.path.exists(ERROR_FILE):
                    time.sleep(0.3)
                    try:
                        with open(ERROR_FILE, 'r', encoding='cp1250') as f:
                            response = f.read().strip()
                    except:
                        time.sleep(0.2)
                        continue

                    logger.info(f"=== RASPUNS PRIMIT ===\n{response}")
                    return parse_response(response)

                time.sleep(0.1)

            online_still_exists = os.path.exists(ONLINE_FILE)
            return {
                'success': False,
                'message': 'Timeout - casa de marcat nu raspunde.' +
                           (' ONLINE.TXT inca exista - SuccesDrv NU proceseaza!' if online_still_exists else
                            ' ONLINE.TXT a fost preluat dar nu a venit raspuns.'),
                'raw_response': None,
                'error_code': 'TIMEOUT',
                'online_file_exists': online_still_exists
            }

        except PermissionError as e:
            logger.error(f"Eroare permisiuni: {str(e)}")
            return {
                'success': False,
                'message': f'Eroare permisiuni la scriere fisier: {str(e)}',
                'error_code': 'PERMISSION_ERROR'
            }
        except Exception as e:
            logger.error(f"Eroare: {str(e)}")
            return {
                'success': False,
                'message': f'Eroare interna: {str(e)}',
                'error_code': 'INTERNAL_ERROR'
            }

def parse_response(response: str) -> dict:
    """
    Parseaza raspunsul din ERROR.TXT conform manual SuccesDRV

    Format raspuns succes:
      0 OK
      # 13,7          (numar document, numar bon fiscal)
      19.00,09.00,-,-,-,-    (cotele TVA)

    Format raspuns eroare:
      1 ERROR
      Eroare Generala
      Nr. Eroare si descriere
    """
    if not response:
        return {'success': False, 'message': 'Raspuns gol', 'error_code': 'EMPTY'}

    lines = response.split('\n')
    first_line = lines[0].strip()

    if first_line.startswith('0'):
        result = {
            'success': True,
            'message': 'Comanda executata cu succes',
            'raw_response': response,
        }
        # Extrage numar document si numar bon fiscal
        for line in lines[1:]:
            line = line.strip()
            if line.startswith('#'):
                parts = line.replace('#', '').strip().split(',')
                if len(parts) >= 2:
                    result['document_number'] = parts[0].strip()
                    result['fiscal_number'] = parts[1].strip()
                elif len(parts) == 1:
                    result['fiscal_number'] = parts[0].strip()
            # Extrage info sold (pentru cmd 25)
            if line.startswith('P,') or line.startswith('F,'):
                result['cash_info'] = line
        return result
    else:
        error_msg = first_line
        if len(lines) > 1:
            error_msg = ' | '.join(l.strip() for l in lines if l.strip())
        return {
            'success': False,
            'message': f'Eroare casa de marcat: {error_msg}',
            'raw_response': response,
            'error_code': first_line.split()[0] if first_line.split() else 'UNKNOWN'
        }

def get_um_code(unitate: str) -> str:
    """Converteste unitatea de masura din aplicatie in cod SuccesM7"""
    if not unitate:
        return '2'
    return UM_MAP.get(unitate.lower().strip(), '2')

def get_tva_code(tva_percent) -> str:
    """Converteste procentul TVA in cod cota SuccesM7"""
    try:
        tva = int(float(tva_percent))
    except:
        return '1'
    return TVA_MAP.get(tva, '1')

def price_to_bani(price_ron) -> int:
    """Converteste pretul din RON in bani (centi). Ex: 35.50 RON = 3550"""
    return int(round(float(price_ron) * 100))

def format_quantity(qty) -> str:
    """Formateaza cantitatea cu punct zecimal conform manual.
    Ex: 1 -> '1', 2.5 -> '2.5', 0.500 -> '0.5'
    """
    q = float(qty)
    if q == int(q):
        return str(int(q))
    return f'{q:.3f}'.rstrip('0').rstrip('.')

# ===================== ENDPOINTS =====================

@app.route('/health', methods=['GET'])
def health_check():
    path_exists = os.path.isdir(SUCCESDRV_PATH)
    exe_found = False
    if path_exists:
        for f in os.listdir(SUCCESDRV_PATH):
            if 'succesdrv' in f.lower() and f.lower().endswith('.exe'):
                exe_found = True
                break
    return jsonify({
        'status': 'ok',
        'driver_path': SUCCESDRV_PATH,
        'driver_exists': path_exists,
        'exe_found': exe_found,
        'command_file': 'ONLINE.TXT',
        'version': '3.0',
        'timestamp': datetime.now().isoformat()
    })

@app.route('/diagnostic', methods=['GET'])
def diagnostic():
    checks = []
    path_ok = os.path.isdir(SUCCESDRV_PATH)
    checks.append({'test': 'Folder SuccesDrv exista', 'path': SUCCESDRV_PATH, 'ok': path_ok})

    exe_found = False
    exe_name = None
    for f in os.listdir(SUCCESDRV_PATH) if path_ok else []:
        if 'succesdrv' in f.lower() and f.lower().endswith('.exe'):
            exe_found = True
            exe_name = f
            break
    checks.append({'test': 'SuccesDrv.exe gasit', 'ok': exe_found, 'note': exe_name or 'Nu s-a gasit'})

    can_write = False
    if path_ok:
        try:
            test_file = os.path.join(SUCCESDRV_PATH, '_bridge_test.tmp')
            with open(test_file, 'w') as f:
                f.write('test')
            os.remove(test_file)
            can_write = True
        except:
            pass
    checks.append({'test': 'Permisiuni scriere in folder', 'ok': can_write})

    online_exists = os.path.exists(ONLINE_FILE)
    checks.append({
        'test': 'ONLINE.TXT',
        'ok': not online_exists,
        'note': 'OK - nu exista (normal)' if not online_exists else 'ATENTIE - comanda anterioara nu a fost preluata!'
    })

    ini_content = None
    if os.path.exists(INI_PATH):
        try:
            with open(INI_PATH, 'r', encoding='cp1250') as f:
                ini_content = f.read()
        except:
            pass
    checks.append({'test': 'SuccesDRV.INI', 'ok': ini_content is not None, 'content': ini_content})

    files_in_dir = []
    if path_ok:
        try:
            files_in_dir = os.listdir(SUCCESDRV_PATH)[:30]
        except:
            pass
    checks.append({'test': 'Fisiere in folder', 'ok': True, 'files': files_in_dir})

    all_ok = all(c['ok'] for c in checks[:3])
    return jsonify({
        'status': 'OK' if all_ok else 'PROBLEME DETECTATE',
        'all_ok': all_ok,
        'checks': checks,
        'timestamp': datetime.now().isoformat()
    })

# ---------- BON FISCAL ----------

@app.route('/fiscal/receipt', methods=['POST'])
def print_receipt():
    """
    Printeaza bon fiscal conform manual SuccesDRV 8.5

    Body JSON:
    {
      "items": [{"name": "Produs", "quantity": 2, "price": 35.50, "vat": 19, "um": "buc"}],
      "payment": {"method": "cash"|"card"|"mixed", "total": 71.00, "cash_amount": 50, "card_amount": 21},
      "client": {"cui": "RO12345", "nume": "Firma SRL", "adresa": "Bucuresti"}  // optional
    }
    """
    try:
        data = request.json
        items = data.get('items', [])
        payment = data.get('payment', {})
        client = data.get('client', None)

        if not items:
            return jsonify({'success': False, 'message': 'Nu exista produse'}), 400

        commands = []

        # Comanda 40 - Info client (INAINTE de deschidere bon!)
        if client and client.get('cui'):
            cui = str(client.get('cui', ''))[:21]
            nume = str(client.get('nume', ''))[:32]
            adresa = str(client.get('adresa', ''))[:28]
            commands.append(f'40;{nume};{cui};{adresa}')
            # Deschidere bon cu flag I (Invoice/Factura scurta)
            commands.append(f'0;{DEFAULT_OPERATOR};{DEFAULT_PAROLA};1;I')
        else:
            # Deschidere bon simplu
            commands.append(f'0;{DEFAULT_OPERATOR};{DEFAULT_PAROLA};1')

        # Comenzi articole
        for item in items:
            name = str(item.get('name', 'Produs'))[:38]
            qty = item.get('quantity', 1)
            price = item.get('price', 0)
            vat = item.get('vat', 19)
            um = item.get('um', 'buc')

            um_code = get_um_code(um)
            tva_code = get_tva_code(vat)
            pret_bani = price_to_bani(price)
            cantitate = format_quantity(qty)

            # Format: 1;denumire;UM;CotaTVA;Pret_bani;Cantitate
            commands.append(f'1;{name};{um_code};{tva_code};{pret_bani};{cantitate}')

        # Forme de plata
        method = payment.get('method', 'cash')
        total = payment.get('total', 0)
        total_bani = price_to_bani(total)

        if method == 'card':
            # CARD: fara suma, trebuie sa fie ULTIMA forma de plata
            # Conform manual: "5;;2;1;0" - suma lipseste, driver completeaza automat
            commands.append('5;;2;1;0')
        elif method == 'mixed':
            # Plata combinata - CARD trebuie sa fie ULTIMA!
            cash_amount = payment.get('cash_amount', 0)
            card_amount = payment.get('card_amount', 0)
            voucher_amount = payment.get('voucher_amount', 0)

            if voucher_amount > 0:
                commands.append(f'5;{price_to_bani(voucher_amount)};3;1;0')
            if cash_amount > 0:
                commands.append(f'5;{price_to_bani(cash_amount)};1;1;0')
            if card_amount > 0:
                # Card ULTIMA - fara suma, driver calculeaza restul
                commands.append('5;;2;1;0')
        else:
            # Numerar - cu suma pentru calcul rest
            commands.append(f'5;{total_bani};1;1;0')

        result = write_command(commands)
        log_transaction('RECEIPT', data, result)
        return jsonify(result)

    except Exception as e:
        logger.error(f"Eroare la printare bon: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

# ---------- ANULARE BON ----------

@app.route('/fiscal/cancel', methods=['POST'])
def cancel_receipt():
    """Anuleaza bonul curent - Comanda 14 (FARA punct-virgula!)"""
    commands = ['14']
    result = write_command(commands)
    log_transaction('CANCEL', {}, result)
    return jsonify(result)

# ---------- RAPOARTE ----------

@app.route('/fiscal/report/x', methods=['POST'])
def report_x():
    """Printeaza Raport X (fara inchidere zi) - Comanda 30"""
    commands = ['30']
    result = write_command(commands)
    log_transaction('REPORT_X', {}, result)
    return jsonify(result)

@app.route('/fiscal/report/z', methods=['POST'])
def report_z():
    """Printeaza Raport Z (INCHIDE ZIUA FISCALA!) - Comanda 15"""
    commands = ['15']
    result = write_command(commands)
    log_transaction('REPORT_Z', {}, result)
    return jsonify(result)

# ---------- NUMERAR IN/OUT ----------

@app.route('/fiscal/cash/in', methods=['POST'])
def cash_in():
    """
    Intrare numerar in sertar (Sold initial)
    Comanda 25: 25;2;valoare_bani;motiv;nr_operator
    """
    try:
        data = request.json
        amount = data.get('amount', 0)
        if amount <= 0:
            return jsonify({'success': False, 'message': 'Suma trebuie sa fie pozitiva'}), 400

        amount_bani = price_to_bani(amount)
        reason = str(data.get('reason', 'Intrare numerar'))[:32]
        operator = data.get('operator', DEFAULT_OPERATOR)

        commands = [f'25;2;{amount_bani};{reason};{operator}']
        result = write_command(commands)
        log_transaction('CASH_IN', data, result)
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/fiscal/cash/out', methods=['POST'])
def cash_out():
    """
    Extragere numerar din sertar (Sume retrase)
    Comanda 25: 25;1;valoare_bani;motiv;nr_operator
    """
    try:
        data = request.json
        amount = data.get('amount', 0)
        if amount <= 0:
            return jsonify({'success': False, 'message': 'Suma trebuie sa fie pozitiva'}), 400

        amount_bani = price_to_bani(amount)
        reason = str(data.get('reason', 'Extragere numerar'))[:32]
        operator = data.get('operator', DEFAULT_OPERATOR)

        commands = [f'25;1;{amount_bani};{reason};{operator}']
        result = write_command(commands)
        log_transaction('CASH_OUT', data, result)
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

# ---------- SERTAR ----------

@app.route('/fiscal/drawer/open', methods=['POST'])
def open_drawer():
    """Deschide sertarul de bani - Comanda 106 (FARA punct-virgula!)"""
    commands = ['106']
    result = write_command(commands)
    return jsonify(result)

# ---------- TOTALURI ----------

@app.route('/fiscal/totals', methods=['GET'])
def read_totals():
    """Citeste totalurile zilnice - Comanda 67"""
    commands = ['67']
    result = write_command(commands)
    return jsonify(result)

# ---------- COPIE BON ----------

@app.route('/fiscal/copy-receipt', methods=['POST'])
def copy_receipt():
    """Tipareste copie nefiscala a ultimului bon - Comanda 46"""
    commands = ['46']
    result = write_command(commands)
    log_transaction('COPY_RECEIPT', {}, result)
    return jsonify(result)

# ---------- CITIRE COTE TVA ----------

@app.route('/fiscal/read-vat', methods=['GET'])
def read_vat():
    """Citeste cotele TVA programate - Comanda 61"""
    commands = ['61']
    result = write_command(commands)
    return jsonify(result)

# ---------- PROGRAMARE COTE TVA ----------

@app.route('/fiscal/setup/vat', methods=['POST'])
def setup_vat():
    """
    Programeaza cotele TVA pe casa de marcat - Comanda 60
    Format: 60;cota_A;cota_B;cota_C;cota_D;cota_E;cota_F;N;T
    Cotele sunt in format XXYY = XX.YY% (ex: 2100 = 21.00%)
    Valori implicite: A=21%(standard), B=11%(redusa), C=0%(scutit), D=9%(tranzitorie)
    Conform Legea 141/2025, valabil de la 1 august 2025
    """
    try:
        data = request.json or {}
        cota_a = data.get('cota_a', DEFAULT_TVA_RATES['A'])
        cota_b = data.get('cota_b', DEFAULT_TVA_RATES['B'])
        cota_c = data.get('cota_c', DEFAULT_TVA_RATES['C'])
        cota_d = data.get('cota_d', DEFAULT_TVA_RATES['D'])
        cota_e = data.get('cota_e', DEFAULT_TVA_RATES['E'])
        cota_f = data.get('cota_f', DEFAULT_TVA_RATES['F'])
        commands = [f'60;{cota_a};{cota_b};{cota_c};{cota_d};{cota_e};{cota_f};0;0']
        result = write_command(commands)
        log_transaction('SETUP_VAT', {'command': commands[0]}, result)
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

# ---------- PROGRAMARE GRUPE ----------

@app.route('/fiscal/setup/group', methods=['POST'])
def setup_group():
    """
    Programeaza o grupa de articole - Comanda 65
    Format: 65;nr_grupa(1-100);denumire(max 18 car);cota_TVA(1-8)
    """
    try:
        data = request.json or {}
        nr = data.get('group_nr', 1)
        name = str(data.get('name', 'GENERAL'))[:18]
        vat_code = data.get('vat_code', 1)  # 1=A(19%), 2=B(9%), etc.
        commands = [f'65;{nr};{name};{vat_code}']
        result = write_command(commands)
        log_transaction('SETUP_GROUP', data, result)
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

# ---------- STATUS ----------

@app.route('/fiscal/status', methods=['GET'])
def get_status():
    """Verifica statusul casei de marcat"""
    try:
        status = {'connected': False, 'status': 'UNKNOWN'}
        if os.path.exists(INI_PATH):
            with open(INI_PATH, 'r', encoding='cp1250') as f:
                content = f.read()
                if 'START' in content.upper():
                    status['connected'] = True
                    status['status'] = 'RUNNING'
        return jsonify(status)
    except Exception as e:
        return jsonify({'connected': False, 'status': 'ERROR', 'message': str(e)})

# ---------- COMANDA MANUALA ----------

@app.route('/fiscal/test-command', methods=['POST'])
def test_command():
    """Trimite o comanda personalizata la SuccesDrv (pentru testare)"""
    try:
        data = request.json
        raw_command = data.get('command', '').strip()
        if not raw_command:
            return jsonify({'success': False, 'message': 'Comanda goala'}), 400

        lines = raw_command.replace('\\n', '\n').split('\n')
        lines = [l.strip() for l in lines if l.strip()]

        result = write_command(lines)
        log_transaction('TEST_COMMAND', {'command': raw_command}, result)
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

# ---------- LOGGING ----------

def log_transaction(trans_type: str, data: dict, result: dict):
    """Logheaza tranzactia intr-un fisier JSON zilnic"""
    try:
        log_dir = os.path.join(SUCCESDRV_PATH, 'logs')
        os.makedirs(log_dir, exist_ok=True)

        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'type': trans_type,
            'data': data,
            'result': result
        }

        date_str = datetime.now().strftime('%Y-%m-%d')
        log_file = os.path.join(log_dir, f'fiscal_{date_str}.json')

        logs = []
        if os.path.exists(log_file):
            with open(log_file, 'r', encoding='utf-8') as f:
                try:
                    logs = json.load(f)
                except:
                    logs = []
        logs.append(log_entry)
        with open(log_file, 'w', encoding='utf-8') as f:
            json.dump(logs, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"Eroare la logging: {str(e)}")

# ===================== PAGINA DE TEST =====================

TEST_PAGE_HTML = """<!DOCTYPE html>
<html lang="ro">
<head>
    <meta charset="UTF-8">
    <title>ANDREPAU - Test Casa de Marcat v3.0</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Segoe UI', Tahoma, sans-serif; background: #0a0a0b; color: #e5e5e5; min-height: 100vh; }
        .header { background: #111; border-bottom: 2px solid #f59e0b; padding: 16px 24px; }
        .header h1 { color: #f59e0b; font-size: 22px; }
        .header .sub { color: #888; font-size: 13px; margin-top: 4px; }
        .container { max-width: 960px; margin: 24px auto; padding: 0 16px; }
        .status-bar { display: flex; gap: 12px; margin-bottom: 20px; flex-wrap: wrap; }
        .status-item { padding: 12px 18px; border-radius: 8px; background: #161618; border: 1px solid #222; flex: 1; min-width: 180px; }
        .status-item .label { font-size: 12px; color: #888; margin-bottom: 4px; }
        .status-item .value { font-size: 16px; font-weight: 600; }
        .status-ok { border-color: #22c55e; }
        .status-ok .value { color: #22c55e; }
        .status-err { border-color: #ef4444; }
        .status-err .value { color: #ef4444; }
        .section { background: #161618; border: 1px solid #222; border-radius: 10px; margin-bottom: 16px; overflow: hidden; }
        .section-title { padding: 14px 18px; background: #1a1a1c; border-bottom: 1px solid #222; font-weight: 600; font-size: 15px; }
        .section-body { padding: 18px; }
        .btn-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(180px, 1fr)); gap: 10px; }
        .btn { padding: 14px 20px; border-radius: 8px; border: none; font-size: 14px; font-weight: 600; cursor: pointer; transition: all 0.15s; text-align: center; }
        .btn:hover { transform: translateY(-1px); }
        .btn:active { transform: translateY(0); }
        .btn:disabled { opacity: 0.5; cursor: not-allowed; transform: none; }
        .btn-blue { background: #2563eb; color: white; }
        .btn-blue:hover { background: #1d4ed8; }
        .btn-green { background: #16a34a; color: white; }
        .btn-green:hover { background: #15803d; }
        .btn-red { background: #dc2626; color: white; }
        .btn-red:hover { background: #b91c1c; }
        .btn-orange { background: #ea580c; color: white; }
        .btn-orange:hover { background: #c2410c; }
        .btn-gray { background: #333; color: white; }
        .btn-gray:hover { background: #444; }
        .log { background: #0d0d0e; border: 1px solid #222; border-radius: 8px; padding: 12px; font-family: 'Consolas', 'Courier New', monospace; font-size: 13px; max-height: 400px; overflow-y: auto; white-space: pre-wrap; line-height: 1.5; margin-top: 12px; }
        .log-entry { padding: 4px 0; border-bottom: 1px solid #1a1a1a; }
        .log-ok { color: #22c55e; }
        .log-err { color: #ef4444; }
        .log-info { color: #60a5fa; }
        .log-warn { color: #f59e0b; }
        .input-group { display: flex; gap: 8px; align-items: center; margin-bottom: 10px; }
        .input-group label { min-width: 100px; font-size: 13px; color: #888; }
        .input-group input, .input-group textarea { flex: 1; padding: 10px 14px; background: #0d0d0e; border: 1px solid #333; border-radius: 6px; color: white; font-size: 14px; font-family: monospace; }
        .input-group input:focus, .input-group textarea:focus { outline: none; border-color: #f59e0b; }
        .info-box { padding: 10px 14px; background: #1a1a0e; border: 1px solid #f59e0b30; border-radius: 6px; font-size: 12px; color: #ccc; margin-bottom: 12px; line-height: 1.5; }
        .info-box code { color: #f59e0b; background: #0005; padding: 1px 4px; border-radius: 3px; }
    </style>
</head>
<body>
    <div class="header">
        <h1>ANDREPAU - Test Casa de Marcat</h1>
        <div class="sub">Bridge Service v3.0 | INCOTEX Succes M7 via SuccesDrv | Format comenzi: Manual SuccesDRV 8.5</div>
    </div>
    <div class="container">
        <div class="status-bar">
            <div class="status-item" id="st-bridge"><div class="label">Bridge Service</div><div class="value">Verificare...</div></div>
            <div class="status-item" id="st-folder"><div class="label">Folder SuccesDrv</div><div class="value">Verificare...</div></div>
            <div class="status-item" id="st-exe"><div class="label">SuccesDrv.exe</div><div class="value">Verificare...</div></div>
        </div>

        <div class="section">
            <div class="section-title">Diagnostic</div>
            <div class="section-body">
                <div class="btn-grid">
                    <button class="btn btn-blue" onclick="runDiagnostic()">Diagnostic Complet</button>
                    <button class="btn btn-gray" onclick="checkHealth()">Health Check</button>
                    <button class="btn btn-gray" onclick="readVat()">Citeste Cote TVA</button>
                    <button class="btn btn-gray" onclick="readTotals()">Citeste Totaluri</button>
                </div>
            </div>
        </div>

        <div class="section">
            <div class="section-title">Rapoarte Fiscale</div>
            <div class="section-body">
                <div class="btn-grid">
                    <button class="btn btn-blue" onclick="reportX()">Raport X</button>
                    <button class="btn btn-red" onclick="if(confirm('ATENTIE! Raportul Z INCHIDE ziua fiscala si NU poate fi anulat! Continuati?')) reportZ()">Raport Z (Inchidere Zi)</button>
                    <button class="btn btn-gray" onclick="copyReceipt()">Copie Ultimul Bon</button>
                    <button class="btn btn-gray" onclick="openDrawer()">Deschide Sertar</button>
                </div>
            </div>
        </div>

        <div class="section">
            <div class="section-title">Operatiuni Numerar</div>
            <div class="section-body">
                <div class="input-group">
                    <label>Suma (RON):</label>
                    <input type="number" id="cashAmount" value="100" step="0.01" min="0.01">
                </div>
                <div class="input-group">
                    <label>Motiv:</label>
                    <input type="text" id="cashReason" value="Sold initial" maxlength="32">
                </div>
                <div class="btn-grid">
                    <button class="btn btn-green" onclick="cashIn()">Intrare Bani (Sold Initial)</button>
                    <button class="btn btn-orange" onclick="cashOut()">Extragere Bani (Sume Retrase)</button>
                </div>
            </div>
        </div>

        <div class="section" style="border-color: #f59e0b;">
            <div class="section-title" style="color: #f59e0b;">CONFIGURARE CASA DE MARCAT (Obligatoriu prima data!)</div>
            <div class="section-body">
                <div class="info-box" style="border-color: #ef444440; background: #1a0e0e;">
                    <strong style="color:#ef4444;">IMPORTANT!</strong> Inainte de a printa bonuri, trebuie programate cotele TVA si grupele pe casa.<br>
                    Conform <strong>Legea 141/2025</strong> (ANAF), de la 1 august 2025:<br>
                    <strong>A = 21%</strong> (standard) | <strong>B = 11%</strong> (redusa) | <strong>C = 0%</strong> (scutit/export) | <strong>D = 9%</strong> (tranzitorie locuinte)
                </div>
                <div style="display:grid; grid-template-columns:repeat(4,1fr); gap:8px; margin-bottom:12px;">
                    <div class="input-group" style="flex-direction:column; margin:0;">
                        <label style="min-width:auto; margin-bottom:4px;">Cota A (standard):</label>
                        <input type="number" id="vatA" value="21" step="0.01" min="0" max="50" style="text-align:center;">
                    </div>
                    <div class="input-group" style="flex-direction:column; margin:0;">
                        <label style="min-width:auto; margin-bottom:4px;">Cota B (redusa):</label>
                        <input type="number" id="vatB" value="11" step="0.01" min="0" max="50" style="text-align:center;">
                    </div>
                    <div class="input-group" style="flex-direction:column; margin:0;">
                        <label style="min-width:auto; margin-bottom:4px;">Cota C (scutit):</label>
                        <input type="number" id="vatC" value="0" step="0.01" min="0" max="50" style="text-align:center;">
                    </div>
                    <div class="input-group" style="flex-direction:column; margin:0;">
                        <label style="min-width:auto; margin-bottom:4px;">Cota D (tranzitorie):</label>
                        <input type="number" id="vatD" value="9" step="0.01" min="0" max="50" style="text-align:center;">
                    </div>
                </div>
                <div class="btn-grid">
                    <button class="btn btn-gray" onclick="readVat()">1. Citeste TVA curente</button>
                    <button class="btn btn-orange" onclick="setupVat()">2. Programeaza TVA pe casa</button>
                    <button class="btn btn-orange" onclick="setupGroup()">3. Programeaza Grupa 1</button>
                    <button class="btn btn-gray" onclick="readVat()">4. Verifica TVA</button>
                </div>
            </div>
        </div>

        <div class="section">
            <div class="section-title">Test Bon Fiscal</div>
            <div class="section-body">
                <div class="info-box">
                    <strong>Format articol:</strong> <code>1;Denumire;UM;CotaTVA;Pret_bani;Cantitate</code><br>
                    <strong>Preturi:</strong> in BANI (x100). Ex: 35.50 RON = <code>3550</code><br>
                    <strong>Cantitati:</strong> cu punct zecimal. Ex: 2.5 = <code>2.5</code><br>
                    <strong>UM:</strong> 1=fara, 2=Buc, 3=Kg, 4=m, 5=L, 6=mp, 7=bax, 8=mc<br>
                    <strong>TVA:</strong> 1=A(21%), 2=B(11%), 3=C(0%), 4=D(9%), 7=Scutit, 8=Alte taxe<br>
                    <strong>Plata:</strong> <code>5;suma_bani;1(numerar);1;0</code> | CARD: <code>5;;2;1;0</code> (fara suma!)
                </div>
                <div class="btn-grid">
                    <button class="btn btn-green" onclick="testReceiptCash()">Bon Test (Numerar)</button>
                    <button class="btn btn-blue" onclick="testReceiptCard()">Bon Test (Card)</button>
                    <button class="btn btn-blue" onclick="testReceiptCUI()">Bon Test cu CUI</button>
                    <button class="btn btn-orange" onclick="testReceiptMultiQty()">Bon Test (Cantitati)</button>
                    <button class="btn btn-red" onclick="cancelReceipt()">Anuleaza Bon Curent</button>
                </div>
            </div>
        </div>

        <div class="section" style="border-color: #f59e0b;">
            <div class="section-title" style="color: #f59e0b;">Comanda Manuala (Avansat)</div>
            <div class="section-body">
                <div class="info-box">
                    Trimite comenzi direct la SuccesDrv. Fiecare linie = o comanda. NU adauga COM1.<br>
                    Exemple rapide: <code>30</code> (Raport X) | <code>15</code> (Raport Z) | <code>14</code> (Anulare) | <code>67</code> (Totaluri) | <code>106</code> (Sertar)
                </div>
                <div class="input-group">
                    <label>Comenzi:</label>
                    <textarea id="customCmd" rows="4" placeholder="Ex:&#10;0;1;0;1&#10;1;Test Produs;2;1;500;1&#10;5;500;1;1;0"></textarea>
                </div>
                <div style="display:flex; gap:8px; flex-wrap:wrap;">
                    <button class="btn btn-orange" onclick="sendCustomCommand()">Trimite Comenzi</button>
                    <button class="btn btn-gray" onclick="setCmd('30')">Raport X</button>
                    <button class="btn btn-gray" onclick="setCmd('15')">Raport Z</button>
                    <button class="btn btn-gray" onclick="setCmd('14')">Anulare</button>
                    <button class="btn btn-gray" onclick="setCmd('67')">Totaluri</button>
                    <button class="btn btn-gray" onclick="setCmd('106')">Sertar</button>
                    <button class="btn btn-gray" onclick="setCmd('61')">Cote TVA</button>
                    <button class="btn btn-gray" onclick="setCmd('46')">Copie Bon</button>
                </div>
            </div>
        </div>

        <div class="section">
            <div class="section-title">
                Log Comunicare
                <button class="btn btn-gray" onclick="clearLog()" style="float:right; padding:4px 10px; font-size:12px;">Sterge</button>
            </div>
            <div class="section-body">
                <div class="log" id="logArea">Asteptare comenzi...\n</div>
            </div>
        </div>
    </div>

    <script>
        const BASE = '';

        function log(msg, type='info') {
            const el = document.getElementById('logArea');
            const time = new Date().toLocaleTimeString('ro-RO');
            const cls = type==='ok'?'log-ok':type==='err'?'log-err':type==='warn'?'log-warn':'log-info';
            el.innerHTML += '<div class="log-entry '+cls+'">['+time+'] '+msg+'</div>';
            el.scrollTop = el.scrollHeight;
        }
        function clearLog() { document.getElementById('logArea').innerHTML = ''; }
        function setStatus(id, text, ok) {
            const el = document.getElementById(id);
            el.querySelector('.value').textContent = text;
            el.className = 'status-item ' + (ok ? 'status-ok' : 'status-err');
        }
        function setCmd(cmd) { document.getElementById('customCmd').value = cmd; }

        async function api(method, url, body=null) {
            try {
                const opts = { method, headers: {'Content-Type':'application/json'} };
                if (body) opts.body = JSON.stringify(body);
                const resp = await fetch(BASE + url, opts);
                return await resp.json();
            } catch(e) {
                return { success:false, message:'Eroare conexiune: '+e.message, error:true };
            }
        }

        function showResult(label, data) {
            const ok = data.success;
            log(label + ': ' + (ok ? 'SUCCES' : 'EROARE') + ' - ' + (data.message || ''), ok ? 'ok' : 'err');
            if (data.fiscal_number) log('  Nr. bon fiscal: ' + data.fiscal_number, 'ok');
            if (data.document_number) log('  Nr. document: ' + data.document_number, 'info');
            if (data.cash_info) log('  Info numerar: ' + data.cash_info, 'info');
            if (data.raw_response) log('  Raspuns complet: ' + data.raw_response, 'info');
        }

        async function checkHealth() {
            log('Verificare health...');
            const data = await api('GET', '/health');
            if (data.error) { setStatus('st-bridge', 'EROARE', false); log('Bridge nu raspunde!', 'err'); return; }
            setStatus('st-bridge', 'CONECTAT v'+data.version, true);
            setStatus('st-folder', data.driver_exists ? 'GASIT' : 'NEGASIT', data.driver_exists);
            setStatus('st-exe', data.exe_found ? 'GASIT' : 'NEGASIT', data.exe_found);
            log('Health OK - Path: ' + data.driver_path, data.driver_exists ? 'ok' : 'warn');
        }

        async function runDiagnostic() {
            log('Rulare diagnostic complet...');
            const data = await api('GET', '/diagnostic');
            if (data.error) { log('Eroare: ' + data.message, 'err'); return; }
            log('=== DIAGNOSTIC: ' + data.status + ' ===', data.all_ok ? 'ok' : 'err');
            for (const c of data.checks) {
                log('  [' + (c.ok?'OK':'FAIL') + '] ' + c.test + (c.note ? ' - '+c.note : ''), c.ok ? 'ok' : 'err');
            }
        }

        async function reportX() { log('Raport X...'); showResult('Raport X', await api('POST', '/fiscal/report/x')); }
        async function reportZ() { log('Raport Z (INCHIDERE ZI)...'); showResult('Raport Z', await api('POST', '/fiscal/report/z')); }
        async function openDrawer() { log('Deschidere sertar...'); showResult('Sertar', await api('POST', '/fiscal/drawer/open')); }
        async function copyReceipt() { log('Copie ultimul bon...'); showResult('Copie', await api('POST', '/fiscal/copy-receipt')); }
        async function readVat() { log('Citire cote TVA...'); showResult('Cote TVA', await api('GET', '/fiscal/read-vat')); }
        async function readTotals() { log('Citire totaluri...'); showResult('Totaluri', await api('GET', '/fiscal/totals')); }

        async function setupVat() {
            const a = Math.round(parseFloat(document.getElementById('vatA').value) * 100);
            const b = Math.round(parseFloat(document.getElementById('vatB').value) * 100);
            const c = Math.round(parseFloat(document.getElementById('vatC').value) * 100);
            const d = Math.round(parseFloat(document.getElementById('vatD').value) * 100);
            log('PROGRAMARE COTE TVA: A=' + (a/100) + '%, B=' + (b/100) + '%, C=' + (c/100) + '%, D=' + (d/100) + '%');
            log('  Comanda: 60;' + a + ';' + b + ';' + c + ';' + d + ';0;0;0;0');
            showResult('Programare TVA', await api('POST', '/fiscal/setup/vat', {
                cota_a: a, cota_b: b, cota_c: c, cota_d: d
            }));
        }

        async function setupGroup() {
            log('PROGRAMARE GRUPA 1 = GENERAL, TVA A (19%)...');
            log('  Comanda: 65;1;GENERAL;1');
            showResult('Programare Grupa', await api('POST', '/fiscal/setup/group', {
                group_nr: 1, name: 'GENERAL', vat_code: 1
            }));
        }

        async function cashIn() {
            const amount = parseFloat(document.getElementById('cashAmount').value);
            const reason = document.getElementById('cashReason').value || 'Sold initial';
            if (!amount || amount <= 0) { log('Suma invalida!', 'err'); return; }
            log('Intrare numerar: ' + amount + ' RON (' + Math.round(amount*100) + ' bani)...');
            showResult('Intrare', await api('POST', '/fiscal/cash/in', { amount, reason }));
        }

        async function cashOut() {
            const amount = parseFloat(document.getElementById('cashAmount').value);
            const reason = document.getElementById('cashReason').value || 'Extragere numerar';
            if (!amount || amount <= 0) { log('Suma invalida!', 'err'); return; }
            log('Extragere numerar: ' + amount + ' RON (' + Math.round(amount*100) + ' bani)...');
            showResult('Extragere', await api('POST', '/fiscal/cash/out', { amount, reason }));
        }

        async function cancelReceipt() {
            log('Anulare bon curent (comanda 14)...');
            showResult('Anulare', await api('POST', '/fiscal/cancel'));
        }

        async function testReceiptCash() {
            log('BON TEST: 1 x Colier 1 RON, plata numerar...');
            log('  Comanda: 0;1;0;1 / 1;Colier metalic 20mm;2;1;100;1 / 5;100;1;1;0');
            showResult('Bon numerar', await api('POST', '/fiscal/receipt', {
                items: [
                    { name: 'Colier metalic 20mm', quantity: 1, price: 1.00, vat: 21, um: 'buc' }
                ],
                payment: { method: 'cash', total: 1.00 }
            }));
        }

        async function testReceiptCard() {
            log('BON TEST: 1 x Colier 1 RON, plata CARD...');
            log('  Comanda: 0;1;0;1 / 1;Colier metalic 20mm;2;1;100;1 / 5;;2;1;0');
            showResult('Bon card', await api('POST', '/fiscal/receipt', {
                items: [{ name: 'Colier metalic 20mm', quantity: 1, price: 1.00, vat: 21, um: 'buc' }],
                payment: { method: 'card', total: 1.00 }
            }));
        }

        async function testReceiptCUI() {
            log('BON TEST: 1 x Colier 1 RON cu CUI...');
            showResult('Bon CUI', await api('POST', '/fiscal/receipt', {
                client: { cui: 'RO4381714', nume: 'FIRMA TEST SRL', adresa: 'Bucuresti' },
                items: [{ name: 'Colier metalic 20mm', quantity: 1, price: 1.00, vat: 21, um: 'buc' }],
                payment: { method: 'cash', total: 1.00 }
            }));
        }

        async function testReceiptMultiQty() {
            log('BON TEST: 3 x Colier 1 RON = 3 RON...');
            showResult('Bon cantitati', await api('POST', '/fiscal/receipt', {
                items: [
                    { name: 'Colier metalic 20mm', quantity: 3, price: 1.00, vat: 21, um: 'buc' }
                ],
                payment: { method: 'cash', total: 3.00 }
            }));
        }

        async function sendCustomCommand() {
            const cmd = document.getElementById('customCmd').value.trim();
            if (!cmd) { log('Introduceti o comanda!', 'err'); return; }
            log('Trimit comenzi:\\n' + cmd);
            showResult('Comanda', await api('POST', '/fiscal/test-command', { command: cmd }));
        }

        checkHealth();
    </script>
</body>
</html>"""

@app.route('/test', methods=['GET'])
def test_page():
    resp = make_response(TEST_PAGE_HTML)
    resp.headers['Content-Type'] = 'text/html; charset=utf-8'
    return resp

# ===================== CLOUD POLLING MODE =====================

import urllib.request
import urllib.error

CLOUD_URL = None  # Set from command line or config

def cloud_get(url):
    """HTTP GET folosind urllib (fara requests)"""
    req = urllib.request.Request(url, headers={'User-Agent': 'ANDREPAU-Bridge/3.1'})
    resp = urllib.request.urlopen(req, timeout=10)
    return json.loads(resp.read().decode('utf-8'))

def cloud_post(url, data=None):
    """HTTP POST folosind urllib (fara requests)"""
    body = json.dumps(data or {}).encode('utf-8')
    req = urllib.request.Request(url, data=body, headers={
        'Content-Type': 'application/json',
        'User-Agent': 'ANDREPAU-Bridge/3.1'
    })
    resp = urllib.request.urlopen(req, timeout=10)
    return json.loads(resp.read().decode('utf-8'))

def poll_cloud_jobs():
    """Poll-uieste backend-ul cloud pentru joburi fiscale noi"""
    if not CLOUD_URL:
        logger.error("Cloud polling dezactivat - lipseste URL")
        return
    
    logger.info(f"Cloud polling pornit: {CLOUD_URL}")
    
    while True:
        try:
            # Ping - anunta ca bridge-ul e activ
            try:
                cloud_post(f"{CLOUD_URL}/api/fiscal/bridge-ping")
            except:
                pass
            
            # Poll pentru joburi
            try:
                data = cloud_get(f"{CLOUD_URL}/api/fiscal/pending")
                job = data.get("job")
                if job:
                    logger.info(f"Job primit: {job['job_id']} - {job['type']}")
                    result = execute_fiscal_job(job)
                    # Raporteaza rezultatul
                    try:
                        cloud_post(
                            f"{CLOUD_URL}/api/fiscal/result/{job['job_id']}",
                            result
                        )
                        logger.info(f"Rezultat raportat: {result.get('success')}")
                    except Exception as e:
                        logger.error(f"Eroare raportare rezultat: {e}")
            except urllib.error.URLError as e:
                logger.error(f"Eroare conexiune cloud: {e}")
        except Exception as e:
            logger.error(f"Eroare polling: {e}")
        
        time.sleep(2)  # Poll la fiecare 2 secunde

def execute_fiscal_job(job: dict) -> dict:
    """Executa un job fiscal primit de la cloud"""
    job_type = job.get("type", "")
    data = job.get("data", {})
    
    if job_type == "receipt":
        return execute_receipt(data)
    elif job_type == "cash_in":
        return execute_cash_in(data)
    elif job_type == "cash_out":
        return execute_cash_out(data)
    elif job_type == "report_x":
        return write_command(['30'])
    elif job_type == "report_z":
        return write_command(['15'])
    elif job_type == "cancel":
        return write_command(['14'])
    elif job_type == "copy":
        return write_command(['46'])
    elif job_type == "drawer":
        return write_command(['106'])
    elif job_type == "totals":
        return write_command(['67'])
    elif job_type == "setup_vat":
        cota_a = data.get('cota_a', DEFAULT_TVA_RATES['A'])
        cota_b = data.get('cota_b', DEFAULT_TVA_RATES['B'])
        cota_c = data.get('cota_c', DEFAULT_TVA_RATES['C'])
        cota_d = data.get('cota_d', DEFAULT_TVA_RATES['D'])
        return write_command([f'60;{cota_a};{cota_b};{cota_c};{cota_d};0;0;0;0'])
    elif job_type == "setup_group":
        nr = data.get('group_nr', 1)
        name = str(data.get('name', 'GENERAL'))[:18]
        vat_code = data.get('vat_code', 1)
        return write_command([f'65;{nr};{name};{vat_code}'])
    else:
        return {"success": False, "message": f"Tip job necunoscut: {job_type}"}

def execute_receipt(data: dict) -> dict:
    """Construieste si trimite comenzile pentru bon fiscal"""
    items = data.get('items', [])
    payment = data.get('payment', {})
    client = data.get('client', None)
    
    if not items:
        return {"success": False, "message": "Nu exista produse"}
    
    commands = []
    
    if client and client.get('cui'):
        cui = str(client.get('cui', ''))[:21]
        nume = str(client.get('nume', ''))[:32]
        adresa = str(client.get('adresa', ''))[:28]
        commands.append(f'40;{nume};{cui};{adresa}')
        commands.append(f'0;{DEFAULT_OPERATOR};{DEFAULT_PAROLA};1;I')
    else:
        commands.append(f'0;{DEFAULT_OPERATOR};{DEFAULT_PAROLA};1')
    
    for item in items:
        name = str(item.get('name', 'Produs'))[:38]
        qty = item.get('quantity', 1)
        price = item.get('price', 0)
        vat = item.get('vat', 21)
        um = item.get('um', 'buc')
        um_code = get_um_code(um)
        tva_code = get_tva_code(vat)
        pret_bani = price_to_bani(price)
        cantitate = format_quantity(qty)
        commands.append(f'1;{name};{um_code};{tva_code};{pret_bani};{cantitate}')
    
    method = payment.get('method', 'cash')
    total = payment.get('total', 0)
    total_bani = price_to_bani(total)
    
    if method == 'card':
        commands.append('5;;2;1;0')
    elif method == 'mixed':
        cash_amount = payment.get('cash_amount', 0)
        card_amount = payment.get('card_amount', 0)
        voucher_amount = payment.get('voucher_amount', 0)
        if voucher_amount > 0:
            commands.append(f'5;{price_to_bani(voucher_amount)};3;1;0')
        if cash_amount > 0:
            commands.append(f'5;{price_to_bani(cash_amount)};1;1;0')
        if card_amount > 0:
            commands.append('5;;2;1;0')
    else:
        commands.append(f'5;{total_bani};1;1;0')
    
    result = write_command(commands)
    log_transaction('RECEIPT_CLOUD', data, result)
    return result

def execute_cash_in(data: dict) -> dict:
    amount = data.get('amount', 0)
    if amount <= 0:
        return {"success": False, "message": "Suma trebuie sa fie pozitiva"}
    amount_bani = price_to_bani(amount)
    reason = str(data.get('reason', 'Intrare numerar'))[:32]
    operator = data.get('operator', DEFAULT_OPERATOR)
    result = write_command([f'25;2;{amount_bani};{reason};{operator}'])
    log_transaction('CASH_IN_CLOUD', data, result)
    return result

def execute_cash_out(data: dict) -> dict:
    amount = data.get('amount', 0)
    if amount <= 0:
        return {"success": False, "message": "Suma trebuie sa fie pozitiva"}
    amount_bani = price_to_bani(amount)
    reason = str(data.get('reason', 'Extragere numerar'))[:32]
    operator = data.get('operator', DEFAULT_OPERATOR)
    result = write_command([f'25;1;{amount_bani};{reason};{operator}'])
    log_transaction('CASH_OUT_CLOUD', data, result)
    return result

# ===================== MAIN =====================

if __name__ == '__main__':
    # Detect cloud URL from args or config
    cloud_url = None
    for arg in sys.argv[1:]:
        if arg.startswith('http'):
            cloud_url = arg.rstrip('/')
    
    # Try reading from config file
    if not cloud_url:
        config_path = os.path.join(SUCCESDRV_PATH, 'bridge_config.json')
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    cfg = json.load(f)
                    cloud_url = cfg.get('cloud_url', '').rstrip('/')
            except:
                pass
    
    CLOUD_URL = cloud_url
    
    print()
    print("=" * 64)
    print("  ANDREPAU POS - Bridge Service v3.1")
    print("  Casa de Marcat INCOTEX Succes M7 via SuccesDrv")
    print("  Format: Manual SuccesDRV 8.5 (2023)")
    print("=" * 64)
    print(f"  Cale SuccesDrv:  {SUCCESDRV_PATH}")
    print(f"  Folder exista:   {os.path.isdir(SUCCESDRV_PATH)}")
    print(f"  Fisier comenzi:  ONLINE.TXT")
    print(f"  Port COM:        {INI_CONFIG['port']}")
    print(f"  Bridge port:     {BRIDGE_PORT}")
    if CLOUD_URL:
        print(f"  Cloud URL:       {CLOUD_URL}")
        print(f"  Mod:             CLOUD POLLING (comenzi de la PWA)")
    else:
        print(f"  Cloud URL:       Nu este configurat")
        print(f"  Mod:             LOCAL ONLY (doar pagina de test)")
    print("-" * 64)
    print(f"  PAGINA TEST:     http://localhost:{BRIDGE_PORT}/test")
    print("-" * 64)
    print("  Endpoints locale:")
    print("    POST /fiscal/receipt       Bon fiscal")
    print("    POST /fiscal/cancel        Anulare bon (cmd 14)")
    print("    POST /fiscal/report/x      Raport X (cmd 30)")
    print("    POST /fiscal/report/z      Raport Z (cmd 15)")
    print("    POST /fiscal/cash/in       Intrare numerar")
    print("    POST /fiscal/cash/out      Extragere numerar")
    print("    POST /fiscal/drawer/open   Deschide sertar")
    print("    POST /fiscal/copy-receipt  Copie ultimul bon")
    print("    GET  /fiscal/totals        Totaluri zilnice")
    print("    GET  /test                 Pagina de test")
    print("=" * 64)
    print()
    print("  >>> Deschideti in browser: http://localhost:5555/test <<<")
    print("  >>> Asigurati-va ca SuccesDrv are 'Start procesare' apasat! <<<")
    print()
    
    if CLOUD_URL:
        print(f"  >>> CLOUD: Bridge-ul preia comenzi de la {CLOUD_URL} <<<")
        print()
        # Start cloud polling thread
        poll_thread = threading.Thread(target=poll_cloud_jobs, daemon=True)
        poll_thread.start()
    
    print("  Apasati Ctrl+C pentru a opri serviciul")
    print()

    app.run(host='0.0.0.0', port=BRIDGE_PORT, debug=False, threaded=True)
