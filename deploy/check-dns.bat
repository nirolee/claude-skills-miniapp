@echo off
echo ================================================
echo 检查 DNS 解析是否生效
echo ================================================
echo.

:check
echo [%date% %time%] 正在检查 api.liguoqi.site 的解析...
ping -n 1 api.liguoqi.site | findstr /C:"223.109.140.233" >nul
if %errorlevel%==0 (
    echo.
    echo ✅ DNS 解析已生效！
    echo    api.liguoqi.site -> 223.109.140.233
    echo.
    pause
    exit /b 0
) else (
    ping -n 1 api.liguoqi.site
    echo.
    echo ⏳ DNS 解析尚未生效，5秒后重试...
    echo    (通常需要等待 5-10 分钟)
    echo.
    timeout /t 5 /nobreak >nul
    goto check
)
