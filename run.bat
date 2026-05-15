@echo off
chcp 65001 >nul
cd /d "%~dp0"
set "LOG=%~dp0ultimo_erro.log"
set "VENV_PY=%~dp0.venv\Scripts\python.exe"

echo [%date% %time%] Iniciando... > "%LOG%"

REM --- Se o venv ja existe, usa direto (nao depende do PATH) ---
if exist "%VENV_PY%" goto :run

REM --- Primeira vez: localizar Python instalado ---
set "PY="
if exist "%LocalAppData%\Programs\Python\Python312\python.exe" set "PY=%LocalAppData%\Programs\Python\Python312\python.exe"
if not defined PY if exist "%LocalAppData%\Programs\Python\Python313\python.exe" set "PY=%LocalAppData%\Programs\Python\Python313\python.exe"
if not defined PY if exist "%LocalAppData%\Programs\Python\Python311\python.exe" set "PY=%LocalAppData%\Programs\Python\Python311\python.exe"

if not defined PY (
  where python >nul 2>&1
  if not errorlevel 1 (
    for /f "delims=" %%P in ('where python 2^>nul ^| findstr /i "Programs\\Python"') do set "PY=%%P"
  )
)

if not defined PY (
  echo ERRO: Python nao encontrado. >> "%LOG%"
  echo.
  echo [ERRO] Python nao encontrado.
  echo Instale em https://www.python.org/downloads/
  echo Marque "Add Python to PATH" na instalacao.
  echo.
  echo Detalhes em: %LOG%
  pause
  exit /b 1
)

echo Criando ambiente virtual com: %PY% >> "%LOG%"
echo Criando ambiente virtual (primeira vez)...
"%PY%" -m venv .venv
if errorlevel 1 (
  echo Falha ao criar venv. >> "%LOG%"
  pause
  exit /b 1
)

echo Instalando dependencias...
"%VENV_PY%" -m pip install -r requirements.txt >> "%LOG%" 2>&1
if errorlevel 1 (
  echo Falha no pip install. Veja %LOG%
  pause
  exit /b 1
)

:run
echo Usando: %VENV_PY% >> "%LOG%"

where ffmpeg >nul 2>&1
if errorlevel 1 (
  echo AVISO: FFmpeg nao no PATH. Videos podem falhar. >> "%LOG%"
  echo.
  echo [AVISO] FFmpeg nao encontrado. Necessario para arquivos de video.
  echo.
)

echo.
echo ========================================
echo   Transcricao de Video
echo   http://127.0.0.1:8000
echo ========================================
echo.
echo Abrindo o navegador...
start "" "http://127.0.0.1:8000"

"%VENV_PY%" -m uvicorn main:app --host 127.0.0.1 --port 8000
if errorlevel 1 (
  echo Servidor encerrou com erro. >> "%LOG%"
  echo.
  echo [ERRO] O servidor nao iniciou. Veja: %LOG%
  pause
)
