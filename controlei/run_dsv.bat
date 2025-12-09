@echo off
echo ---------------------------------------
echo Ativando ambiente virtual...
echo ---------------------------------------
call .venv\Scripts\activate

echo ---------------------------------------
echo Configurando variáveis Flask...
echo ---------------------------------------
set FLASK_APP=wsgi.py
set FLASK_ENV=development
set FLASK_DEBUG=1

echo ---------------------------------------
echo Iniciando servidor Flask...
echo ---------------------------------------
flask run --host=0.0.0.0 --port=5000

pause
