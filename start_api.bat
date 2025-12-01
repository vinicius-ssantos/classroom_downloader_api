@echo off
echo ========================================
echo  Iniciando Classroom Downloader API
echo ========================================
echo.

cd /d D:\Users\vinic\PycharmProjects\MyEdools_Impacta\classroom-downloader-api

echo Ativando ambiente virtual...
call .venv\Scripts\activate.bat

echo.
echo API iniciando em http://localhost:8001
echo Documentacao em http://localhost:8001/docs
echo.
echo Pressione CTRL+C para parar
echo ========================================
echo.

uvicorn app.main:app --reload
