@echo off
echo ============================================================
echo    DYNASTY-AM - METRICS PM DASHBOARD LAUNCHER
echo ============================================================
echo.

REM Aller dans le bon dossier
cd /d "C:\Users\romain.mizrahi\OneDrive - Dynasty-AM\Python\Gestion\METRICS_DYN_CONV"

REM Activer l'environnement virtuel
call venv\Scripts\activate.bat

echo Lancement du dashboard Streamlit...
echo.
timeout /t 2 /nobreak > nul

start "" streamlit run metrics_pm_application.py

echo.
echo ============================================================
echo Dashboard lance avec succes!
echo Le navigateur devrait s'ouvrir automatiquement.
echo ============================================================
echo.
echo Vous pouvez fermer cette fenetre.
timeout /t 5
exit