@echo off
echo ========================================
echo  SETUP RAPIDO - Classroom Downloader
echo ========================================
echo.

cd /d D:\Users\vinic\PycharmProjects\MyEdools_Impacta\classroom-downloader-api

echo [1/5] Ativando ambiente virtual...
call .venv\Scripts\activate.bat
if %errorlevel% neq 0 (
    echo ERRO: Ambiente virtual nao encontrado!
    echo Criando ambiente virtual...
    python -m venv .venv
    call .venv\Scripts\activate.bat
)
echo OK!
echo.

echo [2/5] Instalando dependencias...
pip install -r requirements.txt -q
echo OK!
echo.

echo [3/5] Importando cookies...
python import_cookies.py
echo.

echo [4/5] Verificando cookies...
python check_cookies.py
echo.

echo [5/5] Criando banco de dados...
alembic upgrade head
echo OK!
echo.

echo ========================================
echo  SETUP COMPLETO!
echo ========================================
echo.
echo Agora execute:
echo   uvicorn app.main:app --reload
echo.
echo Depois acesse: http://localhost:8001/docs
echo ========================================
pause
