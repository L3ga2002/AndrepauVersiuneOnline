#!/bin/bash
cd /opt/andrepau
git stash 2>/dev/null
git pull origin main
source backend/venv/bin/activate
cd backend && pip install -r requirements.txt --quiet
cd ../frontend && yarn install --silent && yarn build
deactivate
systemctl restart andrepau-backend
echo "Update complet!"
