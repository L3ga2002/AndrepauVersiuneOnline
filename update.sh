#!/bin/bash
echo "=== ANDREPAU POS - Actualizare ==="

cd /root/app || cd /app || { echo "EROARE: Nu am gasit directorul aplicatiei!"; exit 1; }

echo "[1/5] Descarc ultimele modificari din GitHub..."
git pull origin main

echo "[2/5] Instalez dependente backend..."
cd backend
pip install -r requirements.txt --quiet

echo "[3/5] Instalez dependente frontend..."
cd ../frontend
yarn install --silent

echo "[4/5] Construiesc frontend-ul..."
yarn build

echo "[5/5] Restartez serviciile..."
sudo supervisorctl restart backend
sudo supervisorctl restart frontend

echo ""
echo "=== Actualizare completa! ==="
sudo supervisorctl status
