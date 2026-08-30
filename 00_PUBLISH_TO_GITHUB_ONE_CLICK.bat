@echo off
setlocal EnableExtensions
cd /d "%~dp0"
title Publish TamaPoke Cardputer ADV to GitHub
color 0A

echo ============================================================
echo      TamaPoke Cardputer ADV v0.7 - GITHUB PUBLISH
echo ============================================================
echo.
echo Original project credit:
echo   socquique/TamaPoke
echo   https://github.com/socquique/TamaPoke
echo.
echo This publishes THIS Cardputer ADV port to:
echo   https://github.com/petecolon1985/TamaPoke-CardputerADV
echo.

where git.exe >nul 2>nul
if errorlevel 1 (
  color 0C
  echo ERROR: Git for Windows was not found.
  echo.
  echo Install Git for Windows or GitHub Desktop, then run this file again.
  echo.
  pause
  exit /b 1
)

if not exist ".git" (
  git init
  if errorlevel 1 goto :failed
)

git config user.name "petecolon1985"
git config user.email "petecolon1985@users.noreply.github.com"

git branch -M main

git remote get-url origin >nul 2>nul
if errorlevel 1 (
  git remote add origin "https://github.com/petecolon1985/TamaPoke-CardputerADV.git"
) else (
  git remote set-url origin "https://github.com/petecolon1985/TamaPoke-CardputerADV.git"
)

git add .
if errorlevel 1 goto :failed

git diff --cached --quiet
if not errorlevel 1 (
  echo No new source changes to commit.
) else (
  git commit -m "Publish TamaPoke Cardputer ADV port v0.7"
  if errorlevel 1 goto :failed
)

echo.
echo Publishing to GitHub...
echo A GitHub sign-in window may open. Sign into the petecolon1985 account.
echo.

git push -u origin main
if errorlevel 1 goto :failed

echo.
echo ============================================================
echo                    PUBLISH SUCCESSFUL
echo ============================================================
echo.
echo Repository:
echo https://github.com/petecolon1985/TamaPoke-CardputerADV
echo.
start "" "https://github.com/petecolon1985/TamaPoke-CardputerADV"
pause
exit /b 0

:failed
color 0C
echo.
echo ============================================================
echo                    PUBLISH FAILED
echo ============================================================
echo.
echo Send a screenshot of this window to ChatGPT and do not change files.
echo.
pause
exit /b 1
