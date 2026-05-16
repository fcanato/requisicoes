#!/bin/bash
# Script de inicialização em produção
# Uso: ./iniciar.sh

DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$DIR"

echo "Iniciando painel principal (porta 8501)..."
nohup streamlit run app.py \
    --server.port 8501 \
    --server.headless true \
    --server.enableCORS false \
    > logs_app.txt 2>&1 &
echo "App PID: $!"

echo "Iniciando painel admin (porta 8502)..."
nohup streamlit run admin_usuarios.py \
    --server.port 8502 \
    --server.headless true \
    --server.enableCORS false \
    > logs_admin.txt 2>&1 &
echo "Admin PID: $!"

echo ""
echo "Apps rodando:"
echo "  Principal: http://localhost:8501"
echo "  Admin:     http://localhost:8502"
echo ""
echo "Para parar: kill \$(lsof -t -i:8501) \$(lsof -t -i:8502)"
