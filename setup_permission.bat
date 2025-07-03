@echo off
echo Setting up permissions for Xecura bot data...

:: Create data directory if it doesn't exist
if not exist data mkdir data

:: Set directory permissions
icacls data /grant Everyone:F

:: Create database file with proper permissions if it doesn't exist
type nul > data\data.db
icacls data\data.db /grant Everyone:F

echo.
echo Permissions set up successfully!
echo.

echo Data directory permissions:
icacls data

echo.
echo Database file permissions:
icacls data\data.db

pause
