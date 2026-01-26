@echo off
echo.
echo ===========================================
echo   Compilando HelpDeskApp com PyInstaller  
echo ===========================================
echo.

:: Verifica se o Python está no PATH
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERRO] Python não encontrado no PATH.
    pause
    exit /b
)

:: Instala dependências necessárias
echo [1/3] Instalando dependências do projeto...
pip install -r requirements.txt
pip install pyinstaller

:: Inicia a compilação via script Python
echo [2/3] Iniciando compilação...
python build_exe.py

echo.
echo [3/3] Processo concluído!
echo O executável estará na pasta 'dist'.
echo.
pause
