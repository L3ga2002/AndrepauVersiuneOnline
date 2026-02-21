#!/usr/bin/env python3
"""
ANDREPAU POS - Bridge Service pentru SuccesDrv
Acest serviciu face legătura între PWA și casa de marcat INCOTEX Succes M7

Instalare pe PC magazin:
1. Instalează Python 3.x de pe python.org
2. Rulează: pip install flask flask-cors
3. Rulează: python fiscal_bridge.py
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import time
import threading
import logging
from datetime import datetime
import json

# ===================== CONFIGURARE =====================
# MODIFICĂ ACEASTĂ CALE PENTRU PC-UL DIN MAGAZIN!
SUCCESDRV_PATH = r"C:\kit sistem\ANDREPAU\SuccesDrv_8_3"
ONLINE_FILE = os.path.join(SUCCESDRV_PATH, "ONLINE.TXT")
ERROR_FILE = os.path.join(SUCCESDRV_PATH, "ERROR.TXT")
LOG_FILE = os.path.join(SUCCESDRV_PATH, "bridge_log.txt")

# Port pentru Bridge Service
BRIDGE_PORT = 5555

# Timeout pentru așteptare răspuns (secunde)
RESPONSE_TIMEOUT = 30

# ===================== LOGGING =====================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE, encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ===================== FLASK APP =====================
app = Flask(__name__)
CORS(app)  # Permite cereri din PWA

# Lock pentru a preveni comenzi simultane
fiscal_lock = threading.Lock()

def write_command(commands: list) -> dict:
    """
    Scrie comenzi în ONLINE.TXT și așteaptă răspunsul din ERROR.TXT
    
    Args:
        commands: Lista de comenzi de trimis (ex: ['COM1', 'R_TRP "Test"1*10V3', 'R_PM1'])
    
    Returns:
        dict cu status și mesaj
    """
    with fiscal_lock:
        try:
            # Șterge fișierul ERROR.TXT existent
            if os.path.exists(ERROR_FILE):
                os.remove(ERROR_FILE)
            
            # Scrie comenzile în ONLINE.TXT
            command_text = '\n'.join(commands)
            logger.info(f"Trimit comenzi:\n{command_text}")
            
            with open(ONLINE_FILE, 'w', encoding='cp1250') as f:
                f.write(command_text)
            
            # Așteaptă răspunsul în ERROR.TXT
            start_time = time.time()
            while time.time() - start_time < RESPONSE_TIMEOUT:
                if os.path.exists(ERROR_FILE):
                    time.sleep(0.2)  # Așteaptă puțin să se scrie complet
                    with open(ERROR_FILE, 'r', encoding='cp1250') as f:
                        response = f.read().strip()
                    
                    logger.info(f"Răspuns primit: {response}")
                    
                    # Parsează răspunsul
                    if response.startswith('0 OK') or response.startswith('0OK'):
                        return {
                            'success': True,
                            'message': 'OK',
                            'raw_response': response,
                            'fiscal_number': extract_fiscal_number(response)
                        }
                    else:
                        return {
                            'success': False,
                            'message': f'Eroare casă de marcat: {response}',
                            'raw_response': response,
                            'error_code': extract_error_code(response)
                        }
                
                time.sleep(0.1)
            
            # Timeout
            return {
                'success': False,
                'message': 'Timeout - casa de marcat nu răspunde',
                'raw_response': None,
                'error_code': 'TIMEOUT'
            }
            
        except Exception as e:
            logger.error(f"Eroare: {str(e)}")
            return {
                'success': False,
                'message': f'Eroare internă: {str(e)}',
                'raw_response': None,
                'error_code': 'INTERNAL_ERROR'
            }

def extract_fiscal_number(response: str) -> str:
    """Extrage numărul bonului fiscal din răspuns"""
    # Formatul poate fi "0 OK\n# 9,8" unde 9 e numărul bonului
    lines = response.split('\n')
    for line in lines:
        if line.startswith('#'):
            parts = line.replace('#', '').strip().split(',')
            if parts:
                return parts[0].strip()
    return None

def extract_error_code(response: str) -> str:
    """Extrage codul de eroare din răspuns"""
    if response:
        parts = response.split()
        if parts:
            return parts[0]
    return 'UNKNOWN'

# ===================== ENDPOINTS =====================

@app.route('/health', methods=['GET'])
def health_check():
    """Verifică dacă bridge-ul funcționează"""
    driver_running = os.path.exists(SUCCESDRV_PATH)
    return jsonify({
        'status': 'ok',
        'driver_path': SUCCESDRV_PATH,
        'driver_exists': driver_running,
        'timestamp': datetime.now().isoformat()
    })

@app.route('/fiscal/receipt', methods=['POST'])
def print_receipt():
    """
    Printează bon fiscal
    
    Body JSON:
    {
        "items": [
            {"name": "Produs 1", "quantity": 2, "price": 10.50, "vat": "V3"},
            {"name": "Produs 2", "quantity": 1, "price": 25.00, "vat": "V3"}
        ],
        "payment": {
            "method": "cash",  // "cash", "card", "voucher", "mixed"
            "cash_amount": 50.00,
            "card_amount": 0,
            "voucher_amount": 0
        },
        "operator": "Admin"
    }
    """
    try:
        data = request.json
        items = data.get('items', [])
        payment = data.get('payment', {})
        
        if not items:
            return jsonify({'success': False, 'message': 'Nu există produse'}), 400
        
        # Construiește comenzile
        commands = ['COM1']  # Prima linie = interfața
        
        # Adaugă articolele
        for item in items:
            name = item.get('name', 'Produs')[:28]  # Max 28 caractere
            qty = item.get('quantity', 1)
            price = item.get('price', 0)
            vat = item.get('vat', 'V3')
            unit = item.get('unit', 'buc')[:4]
            
            # Format: R_TRP "Denumire"[Cantitate][UM]*[Pret]V[TVA]
            cmd = f'R_TRP "{name}"{qty}{unit}*{price:.2f}{vat}'
            commands.append(cmd)
        
        # Adaugă plata
        method = payment.get('method', 'cash')
        
        if method == 'cash':
            cash_amount = payment.get('cash_amount', 0)
            if cash_amount > 0:
                commands.append(f'R_PM1 {cash_amount:.2f}')
            else:
                commands.append('R_PM1')
                
        elif method == 'card':
            card_amount = payment.get('card_amount', 0)
            if card_amount > 0:
                commands.append(f'R_PM3 {card_amount:.2f}')
            else:
                commands.append('R_PM3')
                
        elif method == 'voucher':
            voucher_amount = payment.get('voucher_amount', 0)
            if voucher_amount > 0:
                commands.append(f'R_PM4 {voucher_amount:.2f}')
            else:
                commands.append('R_PM4')
                
        elif method == 'mixed':
            cash = payment.get('cash_amount', 0)
            card = payment.get('card_amount', 0)
            voucher = payment.get('voucher_amount', 0)
            
            if cash > 0:
                commands.append(f'R_PM1 {cash:.2f}')
            if card > 0:
                commands.append(f'R_PM3 {card:.2f}')
            if voucher > 0:
                commands.append(f'R_PM4 {voucher:.2f}')
        
        # Trimite comenzile
        result = write_command(commands)
        
        # Loghează tranzacția
        log_transaction('RECEIPT', data, result)
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Eroare la printare bon: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/fiscal/cancel', methods=['POST'])
def cancel_receipt():
    """Anulează bonul curent"""
    commands = ['COM1', 'C_VALL']
    result = write_command(commands)
    log_transaction('CANCEL', {}, result)
    return jsonify(result)

@app.route('/fiscal/report/x', methods=['POST'])
def report_x():
    """Printează Raport X (fără închidere zi)"""
    commands = ['COM1', 'C_DYX']
    result = write_command(commands)
    log_transaction('REPORT_X', {}, result)
    return jsonify(result)

@app.route('/fiscal/report/z', methods=['POST'])
def report_z():
    """Printează Raport Z (ÎNCHIDE ZIUA FISCALĂ!)"""
    commands = ['COM1', 'C_DYZ']
    result = write_command(commands)
    log_transaction('REPORT_Z', {}, result)
    return jsonify(result)

@app.route('/fiscal/cash/in', methods=['POST'])
def cash_in():
    """
    Intrare numerar în sertar
    
    Body JSON:
    {
        "amount": 100.00,
        "reason": "Sold inițial"
    }
    """
    try:
        data = request.json
        amount = data.get('amount', 0)
        reason = data.get('reason', 'Intrare numerar')[:28]
        
        if amount <= 0:
            return jsonify({'success': False, 'message': 'Suma trebuie să fie pozitivă'}), 400
        
        # Comanda pentru intrare numerar (bon nefiscal)
        commands = [
            'COM1',
            f'R_TXT "{reason}"',
            f'C_CIN {amount:.2f}'  # Cash In
        ]
        
        result = write_command(commands)
        log_transaction('CASH_IN', data, result)
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Eroare la cash in: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/fiscal/cash/out', methods=['POST'])
def cash_out():
    """
    Extragere numerar din sertar
    
    Body JSON:
    {
        "amount": 50.00,
        "reason": "Depunere bancă"
    }
    """
    try:
        data = request.json
        amount = data.get('amount', 0)
        reason = data.get('reason', 'Extragere numerar')[:28]
        
        if amount <= 0:
            return jsonify({'success': False, 'message': 'Suma trebuie să fie pozitivă'}), 400
        
        # Comanda pentru extragere numerar (bon nefiscal)
        commands = [
            'COM1',
            f'R_TXT "{reason}"',
            f'C_COUT {amount:.2f}'  # Cash Out
        ]
        
        result = write_command(commands)
        log_transaction('CASH_OUT', data, result)
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Eroare la cash out: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/fiscal/drawer/open', methods=['POST'])
def open_drawer():
    """Deschide sertarul de bani"""
    commands = ['COM1', 'C_OD']  # Open Drawer
    result = write_command(commands)
    return jsonify(result)

@app.route('/fiscal/status', methods=['GET'])
def get_status():
    """Verifică statusul casei de marcat"""
    try:
        # Citește fișierul INI pentru status
        ini_file = os.path.join(SUCCESDRV_PATH, 'SuccesDRV.INI')
        status = {'connected': False, 'status': 'UNKNOWN'}
        
        if os.path.exists(ini_file):
            with open(ini_file, 'r', encoding='cp1250') as f:
                content = f.read()
                if 'START PROCESARE' in content:
                    status['connected'] = True
                    status['status'] = 'RUNNING'
                elif 'STOP' in content:
                    status['connected'] = False
                    status['status'] = 'STOPPED'
        
        return jsonify(status)
        
    except Exception as e:
        return jsonify({'connected': False, 'status': 'ERROR', 'message': str(e)})

def log_transaction(trans_type: str, data: dict, result: dict):
    """Loghează tranzacția într-un fișier JSON"""
    try:
        log_dir = os.path.join(SUCCESDRV_PATH, 'logs')
        os.makedirs(log_dir, exist_ok=True)
        
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'type': trans_type,
            'data': data,
            'result': result
        }
        
        # Fișier zilnic
        date_str = datetime.now().strftime('%Y-%m-%d')
        log_file = os.path.join(log_dir, f'fiscal_{date_str}.json')
        
        # Citește logurile existente
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

# ===================== MAIN =====================
if __name__ == '__main__':
    print("=" * 60)
    print("  ANDREPAU POS - Bridge Service pentru Casa de Marcat")
    print("=" * 60)
    print(f"  Cale SuccesDrv: {SUCCESDRV_PATH}")
    print(f"  Port: {BRIDGE_PORT}")
    print(f"  URL: http://localhost:{BRIDGE_PORT}")
    print("=" * 60)
    print("  Endpoints disponibile:")
    print("    POST /fiscal/receipt     - Printează bon fiscal")
    print("    POST /fiscal/cancel      - Anulează bon curent")
    print("    POST /fiscal/report/x    - Raport X")
    print("    POST /fiscal/report/z    - Raport Z")
    print("    POST /fiscal/cash/in     - Intrare numerar")
    print("    POST /fiscal/cash/out    - Extragere numerar")
    print("    GET  /fiscal/status      - Status casă")
    print("    GET  /health             - Health check")
    print("=" * 60)
    print("\n  Apasă Ctrl+C pentru a opri serviciul\n")
    
    app.run(host='127.0.0.1', port=BRIDGE_PORT, debug=False, threaded=True)
