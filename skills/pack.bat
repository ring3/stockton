@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo =========================================
echo Stockton Skill - 打包工具
echo =========================================
echo.

REM 解析参数
set "INCLUDE_TESTS=0"
set "HELP=0"

:parse_args
if "%~1"=="" goto :done_parse
if "%~1"=="--include-tests" set "INCLUDE_TESTS=1" & shift & goto :parse_args
if "%~1"=="-t" set "INCLUDE_TESTS=1" & shift & goto :parse_args
if "%~1"=="--help" set "HELP=1" & shift & goto :parse_args
if "%~1"=="-h" set "HELP=1" & shift & goto :parse_args
shift
goto :parse_args
:done_parse

REM 显示帮助
if "%HELP%"=="1" (
    echo 用法: pack.bat [选项]
    echo.
    echo 选项:
    echo   --include-tests, -t    包含 tests 目录（默认不包含）
    echo   --help, -h            显示帮助
    echo.
    echo 示例:
    echo   pack.bat              ^(默认，不包含 tests^)
    echo   pack.bat -t           ^(包含 tests^)
    echo   pack.bat --include-tests  ^(包含 tests^)
    pause
    exit /b 0
)

REM 显示打包模式
echo [模式] %INCLUDE_TESTS%==1 (
    echo 包含 tests 目录
) else (
    echo 不包含 tests 目录（默认）
)
echo.

REM 清理旧的打包文件
echo [1/4] 清理旧的打包文件...
cd /d "%~dp0"
if exist "stockton.skill" del /f "stockton.skill" 2>nul
if exist "stockton.zip" del /f "stockton.zip" 2>nul
if exist "_pack_temp" rmdir /s /q "_pack_temp" 2>nul
echo [OK] 旧文件已清理

REM 创建临时目录
echo.
echo [2/4] 准备打包文件...
mkdir "_pack_temp\stockton" 2>nul

REM 复制主要文件
echo 复制 SKILL.md, README.md...
copy "stockton\SKILL.md" "_pack_temp\stockton\" >nul
copy "stockton\README.md" "_pack_temp\stockton\" >nul

echo 复制 scripts 目录...
xcopy "stockton\scripts" "_pack_temp\stockton\scripts\" /s /e /i /q >nul

echo 复制 references 目录...
xcopy "stockton\references" "_pack_temp\stockton\references\" /s /e /i /q >nul

REM 根据参数决定是否复制 tests
if "%INCLUDE_TESTS%"=="1" (
    echo 复制 tests 目录...
    xcopy "stockton\tests" "_pack_temp\stockton\tests\" /s /e /i /q >nul
) else (
    echo 跳过 tests 目录（使用 --include-tests 包含）
)

echo [OK] 文件准备完成

REM 清理缓存
echo.
echo [3/4] 清理缓存文件...
for /f "delims=" %%i in ('dir /s /b /ad "_pack_temp\__pycache__" 2^>nul') do (
    rmdir /s /q "%%i" 2>nul
)
for /f "delims=" %%i in ('dir /s /b "_pack_temp\*.pyc" 2^>nul') do (
    del /q "%%i" 2>nul
)
echo [OK] 缓存已清理

REM 创建压缩包
echo.
echo [4/4] 创建压缩包...
powershell -Command "Compress-Archive -Path '_pack_temp\stockton' -DestinationPath 'stockton.zip' -Force"
if errorlevel 1 (
    echo [FAIL] 压缩失败
    rmdir /s /q "_pack_temp" 2>nul
    pause
    exit /b 1
)

REM 重命名
rename stockton.zip stockton.skill
if errorlevel 1 (
    echo [FAIL] 重命名失败
    rmdir /s /q "_pack_temp" 2>nul
    pause
    exit /b 1
)

REM 清理临时目录
rmdir /s /q "_pack_temp" 2>nul

echo [OK] 打包完成

echo.
echo =========================================
dir /b "%~dp0stockton.skill"
echo =========================================
echo.

if "%INCLUDE_TESTS%"=="1" (
    echo 打包模式: 包含 tests 目录
) else (
    echo 打包模式: 不包含 tests 目录（使用 -t 参数包含）
)

echo.
echo 使用方法:
echo   1. 复制 stockton.skill 到目标位置
echo   2. 解压到 ~/.config/agents/skills/ (Linux/Mac)
echo   3. 或解压到 %%USERPROFILE%%\.config\agents\skills\ (Windows)
echo.
echo 提示: 运行 pack.bat --help 查看详细选项
echo.
pause
