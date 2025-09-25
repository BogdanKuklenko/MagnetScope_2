@echo off
setlocal

rem --- Переходим в директорию, где находится батник ---
pushd "%~dp0"

echo ---
echo Starting MagnetScope...
echo ---
echo If the program crashes, make sure you have installed the required packages:
echo pip install -r requirements.txt
echo ---

rem --- Запускаем приложение ---
python src/magnetscope/main.py %*

set "ERR=%ERRORLEVEL%"

if not "%ERR%"=="0" (
  echo.
  echo ---
  echo [ERROR] The program exited with an error.
  echo ---
) else (
  echo.
  echo ---
  echo Program finished.
  echo ---
)

pause
popd
endlocal
