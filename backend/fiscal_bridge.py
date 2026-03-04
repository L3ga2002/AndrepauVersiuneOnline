#!/usr/bin/env python3
"""
ANDREPAU POS - Bridge Service pentru SuccesDrv (INCOTEX Succes M7)

Comunicare bazata pe fisiere:
  - Scrie comenzi in ONLINE.TXT
  - Citeste raspunsuri din ERROR.TXT

INSTALARE PE PC MAGAZIN:
  1. Instalati Python 3.x de pe https://www.python.org/downloads/
     (bifati "Add Python to PATH" la instalare!)
  2. Deschideti CMD si rulati:
       pip install flask flask-cors
  3. Copiati acest fisier pe desktop sau in folderul SuccesDrv
  4. Dublu-click pe fisier SAU rulati din CMD:
       python fiscal_bridge.py
  5. Deschideti in browser: http://localhost:5555/test
  6. IMPORTANT: Porniti SuccesDrv si apasati "Start procesare"!
"""

from flask import Flask, request, jsonify, make_response
from flask_cors import CORS
import os
import sys
import time
import glob
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
        'port_tcp': '',
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

# Calea poate fi setata ca argument: python fiscal_bridge.py "C:\cale\catre\SuccesDrv"
if len(sys.argv) > 1:
    SUCCESDRV_PATH = sys.argv[1]
else:
    SUCCESDRV_PATH = find_succesdrv_path() or r"C:\kit sistem\ANDREPAU\SuccesDrv_8_3"

# Citeste configurarea din INI
INI_PATH = os.path.join(SUCCESDRV_PATH, 'SuccesDRV.INI')
INI_CONFIG = parse_ini_file(INI_PATH)

# Construieste numele fisierelor - ONLINE.TXT si ERROR.TXT (standard SuccesDrv)
ONLINE_FILE = os.path.join(SUCCESDRV_PATH, "ONLINE.TXT")
ERROR_FILE = os.path.join(SUCCESDRV_PATH, "ERROR.TXT")

BRIDGE_PORT = 5555
RESPONSE_TIMEOUT = 30

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
CORS(app)

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
            # 1. Sterge ERROR.TXT vechi
            if os.path.exists(ERROR_FILE):
                try:
                    os.remove(ERROR_FILE)
                except:
                    pass
            
            # 2. Scrie comenzile in ONLINE.TXT
            command_text = '\n'.join(commands)
            logger.info(f"=== TRIMIT COMENZI ===\n{command_text}")
            
            with open(ONLINE_FILE, 'w', encoding='cp1250') as f:
                f.write(command_text)
            
            logger.info(f"Fisier ONLINE.TXT creat: {ONLINE_FILE}")
            
            # 3. Asteapta raspunsul in ERROR.TXT
            start_time = time.time()
            while time.time() - start_time < RESPONSE_TIMEOUT:
                if os.path.exists(ERROR_FILE):
                    time.sleep(0.3)  # Asteapta sa se scrie complet
                    try:
                        with open(ERROR_FILE, 'r', encoding='cp1250') as f:
                            response = f.read().strip()
                    except:
                        time.sleep(0.2)
                        continue
                    
                    logger.info(f"=== RASPUNS PRIMIT ===\n{response}")
                    
                    # Parseaza raspunsul
                    if response.startswith('0') and ('OK' in response.upper() or len(response.strip()) <= 5):
                        return {
                            'success': True,
                            'message': 'Comanda executata cu succes',
                            'raw_response': response,
                            'fiscal_number': extract_fiscal_number(response)
                        }
                    elif response.startswith('0'):
                        # Cod 0 = succes chiar daca nu scrie explicit OK
                        return {
                            'success': True,
                            'message': 'OK',
                            'raw_response': response,
                            'fiscal_number': extract_fiscal_number(response)
                        }
                    else:
                        return {
                            'success': False,
                            'message': f'Eroare casa de marcat: {response}',
                            'raw_response': response,
                            'error_code': extract_error_code(response)
                        }
                
                time.sleep(0.1)
            
            # Timeout - verifica daca ONLINE.TXT a fost preluat
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

def extract_fiscal_number(response: str) -> str:
    """Extrage numarul bonului fiscal din raspuns"""
    if not response:
        return None
    lines = response.split('\n')
    for line in lines:
        if line.startswith('#'):
            parts = line.replace('#', '').strip().split(',')
            if parts:
                return parts[0].strip()
    return None

def extract_error_code(response: str) -> str:
    """Extrage codul de eroare din raspuns"""
    if response:
        parts = response.split()
        if parts:
            return parts[0]
    return 'UNKNOWN'

# ===================== ENDPOINTS =====================

@app.route('/health', methods=['GET'])
def health_check():
    """Verifica daca bridge-ul functioneaza"""
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
        'timestamp': datetime.now().isoformat()
    })

@app.route('/diagnostic', methods=['GET'])
def diagnostic():
    """Diagnostic complet - verifica tot ce trebuie"""
    checks = []
    
    # 1. Verifica folderul SuccesDrv
    path_ok = os.path.isdir(SUCCESDRV_PATH)
    checks.append({
        'test': 'Folder SuccesDrv exista',
        'path': SUCCESDRV_PATH,
        'ok': path_ok
    })
    
    # 2. Verifica SuccesDrv exe
    exe_found = False
    exe_name = None
    for f in os.listdir(SUCCESDRV_PATH) if path_ok else []:
        if 'succesdrv' in f.lower() and f.lower().endswith('.exe'):
            exe_found = True
            exe_name = f
            break
    checks.append({
        'test': 'SuccesDrv.exe gasit',
        'ok': exe_found,
        'note': exe_name if exe_found else 'Nu s-a gasit niciun exe SuccesDrv'
    })
    
    # 3. Verifica daca putem scrie in folder
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
    checks.append({
        'test': 'Permisiuni scriere in folder',
        'ok': can_write
    })
    
    # 4. Verifica fisierele
    online_exists = os.path.exists(ONLINE_FILE)
    error_exists = os.path.exists(ERROR_FILE)
    checks.append({
        'test': 'ONLINE.TXT exista acum',
        'ok': not online_exists,  # Nu ar trebui sa existe (inseamna ca nu e nimic in asteptare)
        'note': 'OK - nu exista (normal)' if not online_exists else 'ATENTIE - fisierul exista, comanda anterioara nu a fost preluata!'
    })
    checks.append({
        'test': 'ERROR.TXT exista acum',
        'ok': True,  # Informational
        'note': f'Exista: {error_exists}'
    })
    
    # 5. Listeaza fisierele din folder
    files_in_dir = []
    if path_ok:
        try:
            files_in_dir = os.listdir(SUCCESDRV_PATH)[:30]
        except:
            pass
    checks.append({
        'test': 'Fisiere in folder SuccesDrv',
        'ok': True,
        'files': files_in_dir
    })
    
    # 6. Citeste INI daca exista
    ini_content = None
    ini_path = os.path.join(SUCCESDRV_PATH, 'SuccesDRV.INI')
    if os.path.exists(ini_path):
        try:
            with open(ini_path, 'r', encoding='cp1250') as f:
                ini_content = f.read()
        except:
            pass
    checks.append({
        'test': 'Continut SuccesDRV.INI',
        'ok': ini_content is not None,
        'content': ini_content
    })
    
    # 7. Configurare fisiere din INI
    checks.append({
        'test': 'Fisier comenzi',
        'ok': True,
        'note': f'ONLINE.TXT (citit din INI: Masca={INI_CONFIG["masca_bon"]})'
    })
    
    all_ok = all(c['ok'] for c in checks[:4])
    
    return jsonify({
        'status': 'OK' if all_ok else 'PROBLEME DETECTATE',
        'all_ok': all_ok,
        'checks': checks,
        'timestamp': datetime.now().isoformat()
    })

@app.route('/fiscal/receipt', methods=['POST'])
def print_receipt():
    """Printeaza bon fiscal - format SuccesM7"""
    try:
        data = request.json
        items = data.get('items', [])
        payment = data.get('payment', {})
        client = data.get('client', None)
        
        if not items:
            return jsonify({'success': False, 'message': 'Nu exista produse'}), 400
        
        commands = ['COM1']
        
        # Deschidere bon fiscal
        commands.append('2;1;')
        
        # Client/CUI pe bon (la inceput, inainte de articole)
        if client and client.get('cui'):
            cui = client.get('cui', '')
            nume = client.get('nume', '')[:38]
            adresa = client.get('adresa', '')[:38]
            commands.append(f'40;{nume};{cui};{adresa}')
        
        for item in items:
            name = item.get('name', 'Produs')[:38]
            qty = item.get('quantity', 1)
            price = item.get('price', 0)
            # Cota TVA: 1=Fara, 2=Alte taxe, 3=A(19%), 4=B(9%), 5=C(0%)
            vat = item.get('vat', '3')
            um = item.get('um', 'buc')[:5]
            
            # SuccesM7: 1;denumire;um;cota_tva;pret;cantitate;;grupa;
            cmd = f'1;{name};{um};{vat};{price:.2f};{qty};;1;'
            commands.append(cmd)
        
        # Plata - comanda 3;forma_plata;suma
        # Forme plata: 1=Numerar, 2=Card, 3=Tichet, 4=Credit
        method = payment.get('method', 'cash')
        total = payment.get('total', 0)
        if method == 'card':
            commands.append(f'3;2;{total:.2f}')
        elif method == 'voucher':
            commands.append(f'3;3;{total:.2f}')
        elif method == 'mixed':
            cash = payment.get('cash_amount', 0)
            card = payment.get('card_amount', 0)
            voucher = payment.get('voucher_amount', 0)
            if cash > 0:
                commands.append(f'3;1;{cash:.2f}')
            if card > 0:
                commands.append(f'3;2;{card:.2f}')
            if voucher > 0:
                commands.append(f'3;3;{voucher:.2f}')
        else:
            # Numerar
            commands.append(f'3;1;{total:.2f}')
        
        result = write_command(commands)
        log_transaction('RECEIPT', data, result)
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Eroare la printare bon: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/fiscal/cancel', methods=['POST'])
def cancel_receipt():
    """Anuleaza bonul curent"""
    commands = ['COM1', '60;1;']
    result = write_command(commands)
    log_transaction('CANCEL', {}, result)
    return jsonify(result)

@app.route('/fiscal/report/x', methods=['POST'])
def report_x():
    """Printeaza Raport X (fara inchidere zi)"""
    commands = ['COM1', '30;']
    result = write_command(commands)
    log_transaction('REPORT_X', {}, result)
    return jsonify(result)

@app.route('/fiscal/report/z', methods=['POST'])
def report_z():
    """Printeaza Raport Z (INCHIDE ZIUA FISCALA!)"""
    commands = ['COM1', '15;']
    result = write_command(commands)
    log_transaction('REPORT_Z', {}, result)
    return jsonify(result)

@app.route('/fiscal/cash/in', methods=['POST'])
def cash_in():
    """Intrare numerar in sertar"""
    try:
        data = request.json
        amount = data.get('amount', 0)
        if amount <= 0:
            return jsonify({'success': False, 'message': 'Suma trebuie sa fie pozitiva'}), 400
        
        reason = data.get('reason', 'Intrare numerar')
        # SuccesM7: 25;2;valoare
        commands = ['COM1', f'25;2;{amount:.2f}']
        result = write_command(commands)
        log_transaction('CASH_IN', data, result)
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/fiscal/cash/out', methods=['POST'])
def cash_out():
    """Extragere numerar din sertar"""
    try:
        data = request.json
        amount = data.get('amount', 0)
        if amount <= 0:
            return jsonify({'success': False, 'message': 'Suma trebuie sa fie pozitiva'}), 400
        
        reason = data.get('reason', 'Extragere numerar')
        # SuccesM7: 25;1;valoare
        commands = ['COM1', f'25;1;{amount:.2f}']
        result = write_command(commands)
        log_transaction('CASH_OUT', data, result)
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/fiscal/drawer/open', methods=['POST'])
def open_drawer():
    """Deschide sertarul de bani"""
    commands = ['COM1', '106;']
    result = write_command(commands)
    return jsonify(result)

@app.route('/fiscal/totals', methods=['GET'])
def read_totals():
    """Citeste totalurile zilnice"""
    commands = ['COM1', '67;']
    result = write_command(commands)
    return jsonify(result)

@app.route('/fiscal/test-command', methods=['POST'])
def test_command():
    """Trimite o comanda personalizata (pentru testare)"""
    try:
        data = request.json
        raw_command = data.get('command', '').strip()
        if not raw_command:
            return jsonify({'success': False, 'message': 'Comanda goala'}), 400
        
        # Adauga COM1 daca nu exista
        lines = raw_command.split('\\n')
        if not lines[0].upper().startswith('COM'):
            lines.insert(0, 'COM1')
        
        result = write_command(lines)
        log_transaction('TEST_COMMAND', {'command': raw_command}, result)
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/fiscal/scan-commands', methods=['POST'])
def scan_commands():
    """Scaneaza comenzi de la start la end si raporteaza care sunt valide"""
    try:
        data = request.json
        start = data.get('start', 1)
        end = data.get('end', 200)
        
        results = []
        for cmd_num in range(start, end + 1):
            cmd = f'{cmd_num};'
            result = write_command(['COM1', cmd])
            raw = result.get('raw_response', '') or ''
            
            status = 'UNKNOWN'
            if result.get('success'):
                status = 'OK_EXECUTED'
            elif '8007' in raw:
                status = 'VALID_NEEDS_PARAMS'
            elif '8006' in raw:
                status = 'UNKNOWN'
            else:
                status = 'OTHER_ERROR'
            
            if status != 'UNKNOWN':
                results.append({
                    'cmd': cmd_num,
                    'status': status,
                    'response': raw[:100]
                })
                logger.info(f"SCAN: {cmd_num}; -> {status}")
        
        return jsonify({'success': True, 'commands': results})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/fiscal/status', methods=['GET'])
def get_status():
    """Verifica statusul casei de marcat"""
    try:
        ini_file = os.path.join(SUCCESDRV_PATH, 'SuccesDRV.INI')
        status = {'connected': False, 'status': 'UNKNOWN'}
        
        if os.path.exists(ini_file):
            with open(ini_file, 'r', encoding='cp1250') as f:
                content = f.read()
                if 'START' in content.upper():
                    status['connected'] = True
                    status['status'] = 'RUNNING'
        
        return jsonify(status)
    except Exception as e:
        return jsonify({'connected': False, 'status': 'ERROR', 'message': str(e)})

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
    <title>ANDREPAU - Test Casa de Marcat</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Segoe UI', Tahoma, sans-serif; background: #0a0a0b; color: #e5e5e5; min-height: 100vh; }
        .header { background: #111; border-bottom: 2px solid #f59e0b; padding: 16px 24px; display: flex; align-items: center; gap: 12px; }
        .header h1 { color: #f59e0b; font-size: 22px; }
        .header .sub { color: #888; font-size: 13px; }
        .container { max-width: 900px; margin: 24px auto; padding: 0 16px; }
        
        .status-bar { display: flex; gap: 12px; margin-bottom: 20px; flex-wrap: wrap; }
        .status-item { padding: 12px 18px; border-radius: 8px; background: #161618; border: 1px solid #222; flex: 1; min-width: 200px; }
        .status-item .label { font-size: 12px; color: #888; margin-bottom: 4px; }
        .status-item .value { font-size: 16px; font-weight: 600; }
        .status-ok { border-color: #22c55e; }
        .status-ok .value { color: #22c55e; }
        .status-err { border-color: #ef4444; }
        .status-err .value { color: #ef4444; }
        
        .section { background: #161618; border: 1px solid #222; border-radius: 10px; margin-bottom: 16px; overflow: hidden; }
        .section-title { padding: 14px 18px; background: #1a1a1c; border-bottom: 1px solid #222; font-weight: 600; font-size: 15px; display: flex; align-items: center; gap: 8px; }
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
        
        .log { background: #0d0d0e; border: 1px solid #222; border-radius: 8px; padding: 12px; font-family: 'Consolas', 'Courier New', monospace; font-size: 13px; max-height: 350px; overflow-y: auto; white-space: pre-wrap; line-height: 1.5; margin-top: 12px; }
        .log-entry { padding: 4px 0; border-bottom: 1px solid #1a1a1a; }
        .log-ok { color: #22c55e; }
        .log-err { color: #ef4444; }
        .log-info { color: #60a5fa; }
        .log-warn { color: #f59e0b; }
        
        .input-group { display: flex; gap: 8px; align-items: center; margin-bottom: 10px; }
        .input-group label { min-width: 80px; font-size: 13px; color: #888; }
        .input-group input { flex: 1; padding: 10px 14px; background: #0d0d0e; border: 1px solid #333; border-radius: 6px; color: white; font-size: 14px; font-family: monospace; }
        .input-group input:focus { outline: none; border-color: #f59e0b; }
        
        .spinner { display: inline-block; width: 16px; height: 16px; border: 2px solid #444; border-top-color: #f59e0b; border-radius: 50%; animation: spin 0.6s linear infinite; margin-right: 6px; vertical-align: middle; }
        @keyframes spin { to { transform: rotate(360deg); } }
    </style>
</head>
<body>
    <div class="header">
        <div>
            <h1>ANDREPAU - Test Casa de Marcat</h1>
            <div class="sub">Bridge Service v2.0 | INCOTEX Succes M7 via SuccesDrv | Sintaxa: """ + INI_CONFIG.get('sintaxa', '?') + """</div>
        </div>
    </div>
    
    <div class="container">
        <!-- Status -->
        <div class="status-bar">
            <div class="status-item" id="st-bridge">
                <div class="label">Bridge Service</div>
                <div class="value">Verificare...</div>
            </div>
            <div class="status-item" id="st-folder">
                <div class="label">Folder SuccesDrv</div>
                <div class="value">Verificare...</div>
            </div>
            <div class="status-item" id="st-exe">
                <div class="label">SuccesDrv.exe</div>
                <div class="value">Verificare...</div>
            </div>
        </div>
        
        <!-- Diagnostic -->
        <div class="section">
            <div class="section-title">Diagnostic</div>
            <div class="section-body">
                <div class="btn-grid">
                    <button class="btn btn-blue" onclick="runDiagnostic()">Ruleaza Diagnostic</button>
                    <button class="btn btn-gray" onclick="checkHealth()">Health Check</button>
                </div>
            </div>
        </div>
        
        <!-- Operatiuni Fiscale -->
        <div class="section">
            <div class="section-title">Operatiuni Fiscale</div>
            <div class="section-body">
                <div class="btn-grid">
                    <button class="btn btn-blue" onclick="reportX()">Raport X</button>
                    <button class="btn btn-red" onclick="if(confirm('ATENTIE! Raportul Z inchide ziua fiscala. Continuati?')) reportZ()">Raport Z</button>
                    <button class="btn btn-gray" onclick="openDrawer()">Deschide Sertar</button>
                </div>
            </div>
        </div>
        
        <!-- Cash In/Out -->
        <div class="section">
            <div class="section-title">Numerar</div>
            <div class="section-body">
                <div class="input-group">
                    <label>Suma (RON):</label>
                    <input type="number" id="cashAmount" value="100" step="0.01" min="0.01">
                </div>
                <div class="btn-grid">
                    <button class="btn btn-green" onclick="cashIn()">Intrare Bani</button>
                    <button class="btn btn-orange" onclick="cashOut()">Extragere Bani</button>
                </div>
            </div>
        </div>
        
        <!-- Test Bon -->
        <div class="section">
            <div class="section-title">Test Bon Fiscal</div>
            <div class="section-body">
                <p style="color:#888; font-size:13px; margin-bottom:12px;">Printeaza un bon fiscal de test cu 2 articole (1 RON fiecare, plata numerar)</p>
                <div class="btn-grid">
                    <button class="btn btn-green" onclick="testReceipt()">Bon Fiscal Normal</button>
                    <button class="btn btn-blue" onclick="testReceiptCUI()">Bon Fiscal cu CUI</button>
                    <button class="btn btn-red" onclick="cancelReceipt()">Anuleaza Bon Curent</button>
                </div>
            </div>
        </div>
        
        <!-- Tester Comenzi -->
        <div class="section" style="border-color: #f59e0b;">
            <div class="section-title" style="color: #f59e0b;">Tester Comenzi Manual (AVANSAT)</div>
            <div class="section-body">
                <p style="color:#888; font-size:13px; margin-bottom:12px;">Trimite orice comanda la SuccesDrv. COM1 se adauga automat pe prima linie. Separati comenzile cu Enter.</p>
                <div class="input-group">
                    <label>Comanda:</label>
                    <input type="text" id="customCmd" placeholder="Ex: 69; sau 106; sau 67;" style="font-size:16px; padding:12px;">
                </div>
                <div style="display:flex; gap:8px; flex-wrap:wrap; margin-top:8px;">
                    <button class="btn btn-orange" onclick="sendCustomCommand()">Trimite Comanda</button>
                    <button class="btn btn-gray" onclick="document.getElementById('customCmd').value='69;'">69; (Raport X?)</button>
                    <button class="btn btn-gray" onclick="document.getElementById('customCmd').value='70;'">70; (Raport Z?)</button>
                    <button class="btn btn-gray" onclick="document.getElementById('customCmd').value='106;'">106; (Sertar)</button>
                    <button class="btn btn-gray" onclick="document.getElementById('customCmd').value='67;'">67; (Totaluri)</button>
                    <button class="btn btn-gray" onclick="document.getElementById('customCmd').value='60;'">60; (Anulare?)</button>
                </div>
                <div style="margin-top:16px; padding-top:12px; border-top:1px solid #333;">
                    <p style="color:#f59e0b; font-size:13px; margin-bottom:8px;">SCANNER: Testeaza automat comenzile de la X la Y si afiseaza care sunt valide</p>
                    <div style="display:flex; gap:8px; align-items:center; flex-wrap:wrap;">
                        <label style="color:#888; font-size:13px;">De la:</label>
                        <input type="number" id="scanStart" value="1" style="width:70px; padding:8px; background:#0d0d0e; border:1px solid #333; border-radius:6px; color:white; font-family:monospace;">
                        <label style="color:#888; font-size:13px;">Pana la:</label>
                        <input type="number" id="scanEnd" value="50" style="width:70px; padding:8px; background:#0d0d0e; border:1px solid #333; border-radius:6px; color:white; font-family:monospace;">
                        <button class="btn btn-blue" onclick="scanCommands()">Scaneaza Comenzi</button>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- Log -->
        <div class="section">
            <div class="section-title">
                Log Comunicare
                <button class="btn btn-gray" onclick="clearLog()" style="margin-left:auto; padding:6px 12px; font-size:12px;">Sterge Log</button>
            </div>
            <div class="section-body">
                <div class="log" id="logArea">Asteptare comenzi...\n</div>
            </div>
        </div>
    </div>
    
    <script>
        const BASE = '';  // Same origin (servit de bridge)
        
        function log(msg, type = 'info') {
            const el = document.getElementById('logArea');
            const time = new Date().toLocaleTimeString('ro-RO');
            const cls = type === 'ok' ? 'log-ok' : type === 'err' ? 'log-err' : type === 'warn' ? 'log-warn' : 'log-info';
            el.innerHTML += `<div class="log-entry ${cls}">[${time}] ${msg}</div>`;
            el.scrollTop = el.scrollHeight;
        }
        
        function clearLog() {
            document.getElementById('logArea').innerHTML = '';
        }
        
        function setStatus(id, text, ok) {
            const el = document.getElementById(id);
            el.querySelector('.value').textContent = text;
            el.className = 'status-item ' + (ok ? 'status-ok' : 'status-err');
        }
        
        async function api(method, url, body = null) {
            try {
                const opts = { method, headers: { 'Content-Type': 'application/json' } };
                if (body) opts.body = JSON.stringify(body);
                const resp = await fetch(BASE + url, opts);
                return await resp.json();
            } catch (e) {
                return { success: false, message: 'Eroare conexiune: ' + e.message, error: true };
            }
        }
        
        async function checkHealth() {
            log('Verificare health...');
            const data = await api('GET', '/health');
            if (data.error) {
                setStatus('st-bridge', 'EROARE', false);
                log('Bridge nu raspunde!', 'err');
                return;
            }
            setStatus('st-bridge', 'CONECTAT', true);
            setStatus('st-folder', data.driver_exists ? 'GASIT' : 'NEGASIT', data.driver_exists);
            setStatus('st-exe', data.exe_found ? 'GASIT' : 'NEGASIT', data.exe_found);
            log('Health OK - Path: ' + data.driver_path, data.driver_exists ? 'ok' : 'warn');
        }
        
        async function runDiagnostic() {
            log('Rulare diagnostic complet...');
            const data = await api('GET', '/diagnostic');
            if (data.error) { log('Eroare diagnostic: ' + data.message, 'err'); return; }
            
            log('=== DIAGNOSTIC ===', data.all_ok ? 'ok' : 'err');
            for (const c of data.checks) {
                const icon = c.ok ? 'OK' : 'FAIL';
                log(`  [${icon}] ${c.test}${c.note ? ' - ' + c.note : ''}`, c.ok ? 'ok' : 'err');
                if (c.files) log('  Fisiere: ' + c.files.join(', '), 'info');
                if (c.content) log('  INI: ' + c.content.substring(0, 200), 'info');
            }
            log('==================', data.all_ok ? 'ok' : 'err');
        }
        
        async function reportX() {
            log('Trimit comanda Raport X...');
            const data = await api('POST', '/fiscal/report/x');
            log('Raport X: ' + (data.success ? 'SUCCES' : 'EROARE') + ' - ' + (data.message || data.raw_response || ''), data.success ? 'ok' : 'err');
        }
        
        async function reportZ() {
            log('Trimit comanda Raport Z (INCHIDERE ZI)...');
            const data = await api('POST', '/fiscal/report/z');
            log('Raport Z: ' + (data.success ? 'SUCCES' : 'EROARE') + ' - ' + (data.message || data.raw_response || ''), data.success ? 'ok' : 'err');
        }
        
        async function openDrawer() {
            log('Trimit comanda deschidere sertar...');
            const data = await api('POST', '/fiscal/drawer/open');
            log('Sertar: ' + (data.success ? 'DESCHIS' : 'EROARE') + ' - ' + (data.message || ''), data.success ? 'ok' : 'err');
        }
        
        async function cashIn() {
            const amount = parseFloat(document.getElementById('cashAmount').value);
            if (!amount || amount <= 0) { log('Suma invalida!', 'err'); return; }
            log('Intrare numerar: ' + amount + ' RON...');
            const data = await api('POST', '/fiscal/cash/in', { amount });
            log('Cash In: ' + (data.success ? 'SUCCES' : 'EROARE') + ' - ' + (data.message || ''), data.success ? 'ok' : 'err');
        }
        
        async function cashOut() {
            const amount = parseFloat(document.getElementById('cashAmount').value);
            if (!amount || amount <= 0) { log('Suma invalida!', 'err'); return; }
            log('Extragere numerar: ' + amount + ' RON...');
            const data = await api('POST', '/fiscal/cash/out', { amount });
            log('Cash Out: ' + (data.success ? 'SUCCES' : 'EROARE') + ' - ' + (data.message || ''), data.success ? 'ok' : 'err');
        }
        
        async function testReceipt() {
            log('Printare bon fiscal test (2 articole x 1 RON, numerar)...');
            const data = await api('POST', '/fiscal/receipt', {
                items: [
                    { name: 'Articol Test 1', quantity: 1, price: 1.00, vat: '3', um: 'buc' },
                    { name: 'Articol Test 2', quantity: 1, price: 1.00, vat: '3', um: 'buc' }
                ],
                payment: { method: 'cash', total: 2.00 }
            });
            log('Bon: ' + (data.success ? 'PRINTAT' : 'EROARE') + ' - ' + (data.message || ''), data.success ? 'ok' : 'err');
            if (data.fiscal_number) log('Nr. fiscal: ' + data.fiscal_number, 'ok');
            if (data.raw_response) log('Raspuns brut: ' + data.raw_response, 'info');
        }
        
        async function testReceiptCUI() {
            log('Printare bon fiscal cu CUI (test)...');
            const data = await api('POST', '/fiscal/receipt', {
                client: { cui: 'RO4381714', nume: 'FIRMA TEST SRL', adresa: 'Bucuresti' },
                items: [
                    { name: 'Articol Test CUI', quantity: 1, price: 1.00, vat: '3', um: 'buc' }
                ],
                payment: { method: 'cash', total: 1.00 }
            });
            log('Bon CUI: ' + (data.success ? 'PRINTAT' : 'EROARE') + ' - ' + (data.message || ''), data.success ? 'ok' : 'err');
            if (data.raw_response) log('Raspuns brut: ' + data.raw_response, 'info');
        }
        
        async function cancelReceipt() {
            log('Anulare bon curent...');
            const data = await api('POST', '/fiscal/cancel');
            log('Anulare: ' + (data.success ? 'SUCCES' : 'EROARE') + ' - ' + (data.message || ''), data.success ? 'ok' : 'err');
        }
        
        async function sendCustomCommand() {
            const cmd = document.getElementById('customCmd').value.trim();
            if (!cmd) { log('Introduceti o comanda!', 'err'); return; }
            log('Trimit comanda: ' + cmd + ' ...');
            const data = await api('POST', '/fiscal/test-command', { command: cmd });
            log('Rezultat: ' + (data.success ? 'SUCCES' : 'EROARE') + ' - ' + (data.message || ''), data.success ? 'ok' : 'err');
            if (data.raw_response) log('Raspuns brut: ' + data.raw_response, 'info');
        }
        
        async function scanCommands() {
            const start = parseInt(document.getElementById('scanStart').value) || 1;
            const end = parseInt(document.getElementById('scanEnd').value) || 50;
            log('=== SCANNER: Testez comenzile ' + start + ' - ' + end + ' ===', 'warn');
            log('Asteptati... poate dura cateva minute...', 'warn');
            
            const data = await api('POST', '/fiscal/scan-commands', { start, end });
            if (data.success && data.commands) {
                log('=== REZULTATE SCANNER ===', 'ok');
                if (data.commands.length === 0) {
                    log('Nicio comanda valida gasita in intervalul ' + start + '-' + end, 'err');
                } else {
                    for (const cmd of data.commands) {
                        const icon = cmd.status === 'OK_EXECUTED' ? 'EXECUTAT' : 'NECESITA PARAMETRI';
                        const type = cmd.status === 'OK_EXECUTED' ? 'ok' : 'warn';
                        log('  Comanda ' + cmd.cmd + ': ' + icon + ' | ' + cmd.response, type);
                    }
                }
                log('=========================', 'ok');
            } else {
                log('Eroare scanner: ' + (data.message || 'necunoscuta'), 'err');
            }
        }
        
        // Auto health check la incarcare
        checkHealth();
    </script>
</body>
</html>"""

@app.route('/test', methods=['GET'])
def test_page():
    """Pagina de test pentru casa de marcat - se deschide in browser"""
    resp = make_response(TEST_PAGE_HTML)
    resp.headers['Content-Type'] = 'text/html; charset=utf-8'
    return resp

# ===================== MAIN =====================

if __name__ == '__main__':
    print()
    print("=" * 62)
    print("  ANDREPAU POS - Bridge Service v2.0")
    print("  Casa de Marcat INCOTEX Succes M7 via SuccesDrv")
    print("=" * 62)
    print(f"  Cale SuccesDrv: {SUCCESDRV_PATH}")
    print(f"  Folder exista:  {os.path.isdir(SUCCESDRV_PATH)}")
    print(f"  Fisier comenzi: ONLINE.TXT")
    print(f"  Port COM:       {INI_CONFIG['port']}")
    print(f"  Port:           {BRIDGE_PORT}")
    print("-" * 62)
    print(f"  PAGINA TEST:    http://localhost:{BRIDGE_PORT}/test")
    print(f"  DIAGNOSTIC:     http://localhost:{BRIDGE_PORT}/diagnostic")
    print("-" * 62)
    print("  Endpoints:")
    print("    POST /fiscal/receipt     Printeaza bon fiscal")
    print("    POST /fiscal/cancel      Anuleaza bon curent")
    print("    POST /fiscal/report/x    Raport X")
    print("    POST /fiscal/report/z    Raport Z (inchide ziua!)")
    print("    POST /fiscal/cash/in     Intrare numerar")
    print("    POST /fiscal/cash/out    Extragere numerar")
    print("    POST /fiscal/drawer/open Deschide sertar")
    print("    GET  /fiscal/status      Status casa")
    print("    GET  /health             Health check")
    print("    GET  /diagnostic         Diagnostic complet")
    print("    GET  /test               Pagina de test (browser)")
    print("=" * 62)
    print()
    print("  >>> Deschideti in browser: http://localhost:5555/test <<<")
    print("  >>> Asigurati-va ca SuccesDrv are 'Start procesare' apasat! <<<")
    print()
    print("  Apasati Ctrl+C pentru a opri serviciul")
    print()
    
    app.run(host='127.0.0.1', port=BRIDGE_PORT, debug=False, threaded=True)
