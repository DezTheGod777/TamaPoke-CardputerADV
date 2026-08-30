@echo off
setlocal EnableExtensions EnableDelayedExpansion
cd /d "%~dp0"
title TamaPoke Cardputer ADV - GitHub Updater
color 0A

echo ============================================================
echo      TamaPoke Cardputer ADV - ONE CLICK GITHUB UPDATE
echo ============================================================
echo.
echo This updates your existing GitHub repository.
echo It does NOT delete the repository and does NOT delete old Releases.
echo.
echo Original project credit:
echo   socquique/TamaPoke
echo   https://github.com/socquique/TamaPoke
echo.

set "STABLEBIN=%~dp0TamaPoke-CardputerADV.bin"

if not exist "%STABLEBIN%" (
  color 0E
  echo IMPORTANT:
  echo TamaPoke-CardputerADV.bin is not in this folder yet.
  echo.
  echo First run:
  echo   00_BUILD_BIN_ONE_CLICK.bat
  echo.
  echo Then run this GitHub updater again.
  echo.
  pause
  exit /b 1
)

where git.exe >nul 2>nul
if errorlevel 1 (
  color 0C
  echo ERROR: Git for Windows was not found.
  echo Install Git for Windows or GitHub Desktop, then run this again.
  pause
  exit /b 1
)

where gh.exe >nul 2>nul
if errorlevel 1 (
  where winget.exe >nul 2>nul
  if errorlevel 1 (
    color 0C
    echo ERROR: GitHub CLI was not found.
    echo Install GitHub CLI from https://cli.github.com/
    pause
    exit /b 1
  )
  echo Installing GitHub CLI...
  winget install --id GitHub.cli -e --accept-source-agreements --accept-package-agreements
  if errorlevel 1 goto :failed
  set "PATH=%PATH%;%ProgramFiles%\GitHub CLI"
)

gh auth status >nul 2>nul
if errorlevel 1 (
  echo.
  echo GitHub sign-in will open now.
  gh auth login --hostname github.com --git-protocol https --web
  if errorlevel 1 goto :failed
)

for /f "delims=" %%U in ('gh api user --jq ".login"') do set "GHUSER=%%U"
if "%GHUSER%"=="" goto :failed

set "REPO=TamaPoke-CardputerADV"

echo.
echo Signed in as: %GHUSER%
echo Repository: %GHUSER%/%REPO%
echo.

gh repo view "%GHUSER%/%REPO%" >nul 2>nul
if errorlevel 1 (
  color 0C
  echo ERROR: Repository %GHUSER%/%REPO% was not found.
  pause
  exit /b 1
)

if exist "_github_update_work" rmdir /s /q "_github_update_work"

echo Cloning current repository...
git clone "https://github.com/%GHUSER%/%REPO%.git" "_github_update_work"
if errorlevel 1 goto :failed

echo Updating source files...
robocopy "%~dp0." "%~dp0_github_update_work" /MIR ^
  /XD ".git" ".pio" "_github_update_work" ^
  /XF "*.pyc" >nul
if errorlevel 8 goto :failed

cd /d "%~dp0_github_update_work"

REM Remove old public firmware names such as:
REM TamaPoke-CardputerADV-v0.7-MERGED.bin
REM TamaPoke-CardputerADV-v0.8.5-MERGED.bin
REM The only public BIN kept in main should be TamaPoke-CardputerADV.bin.
for %%F in (TamaPoke-CardputerADV-v*-MERGED.bin) do (
  if exist "%%F" (
    echo Removing old versioned firmware: %%F
    del /q "%%F"
  )
)

REM Do not publish PlatformIO temporary build data.
if exist ".pio" rmdir /s /q ".pio"

REM Confirm the new stable firmware survived the overlay.
if not exist "TamaPoke-CardputerADV.bin" (
  color 0C
  echo ERROR: TamaPoke-CardputerADV.bin was not copied into the update.
  pause
  exit /b 1
)

git config user.name "%GHUSER%"
git config user.email "%GHUSER%@users.noreply.github.com"

git add -A

git diff --cached --quiet
if not errorlevel 1 (
  echo.
  echo No changes found. GitHub is already up to date.
  goto :success
)

echo.
set /p "VER=Enter version label for this update (example v0.8.5.3): "
if "%VER%"=="" set "VER=update"

git commit -m "Update TamaPoke Cardputer ADV %VER%" -m "Unofficial Cardputer ADV port of socquique/TamaPoke. Original TamaPoke credit remains with socquique."
if errorlevel 1 goto :failed

echo.
echo Pushing update to GitHub...
git push origin HEAD:main
if errorlevel 1 goto :failed

:success
echo.
echo ============================================================
echo                    GITHUB UPDATE SUCCESSFUL
echo ============================================================
echo.
echo Public firmware filename:
echo   TamaPoke-CardputerADV.bin
echo.
echo Old versioned *-MERGED.bin files have been removed from main.
echo Old GitHub Releases remain untouched.
echo.
echo https://github.com/%GHUSER%/%REPO%
echo.
start "" "https://github.com/%GHUSER%/%REPO%"
pause
exit /b 0

:failed
color 0C
echo.
echo ============================================================
echo                     GITHUB UPDATE FAILED
echo ============================================================
echo.
echo Send a screenshot of this window to ChatGPT.
pause
exit /b 1
