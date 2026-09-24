@echo off
setlocal

if not exist ".venv\Scripts\python.exe" (
  echo [Docu Generator] Creando entorno Python...
  python -m venv .venv
  if errorlevel 1 exit /b 1
)

echo [Docu Generator] Actualizando backend...
".venv\Scripts\python.exe" -m pip install -e .
if errorlevel 1 exit /b 1

if not exist "frontend\node_modules" (
  echo [Docu Generator] Instalando frontend...
  pushd frontend
  call npm install
  if errorlevel 1 exit /b 1
  popd
)

echo [Docu Generator] Arrancando API en http://127.0.0.1:8000
start "Docu Generator API" cmd /k ".venv\Scripts\python.exe -m uvicorn docu_generator.api:app --reload --host 127.0.0.1 --port 8000"

echo [Docu Generator] Arrancando frontend en http://localhost:3000
pushd frontend
call npm run dev
popd
