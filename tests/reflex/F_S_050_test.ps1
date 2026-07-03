# ══════════════════════════════════════════════════════════════════════════════
# F-S-050 响应式布局与网络韧性 — VS Code 终端一键测试脚本 (PowerShell)
#
# 使用方式（在 VS Code 终端中执行）：
#   .\tests\reflex\F_S_050_test.ps1
#
# 如果遇到执行策略限制，先执行：
#   Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
#   然后再运行脚本
# ══════════════════════════════════════════════════════════════════════════════

$ErrorActionPreference = "Continue"

# ── 定位项目根目录 ────────────────────────────────────────────────────────
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Resolve-Path "$ScriptDir\..\.."

Write-Host ""
Write-Host "╔══════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║   F-S-050  响应式布局 & 网络韧性 — 自动化测试             ║" -ForegroundColor Cyan
Write-Host "║   分支: F_S_050  关联: #19                                  ║" -ForegroundColor Cyan
Write-Host "╚══════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# ── Step 1: 定位 Python ──────────────────────────────────────────────────
Write-Host "[1/4] 检测 Python 环境..." -ForegroundColor White

$Python = $null
$Candidates = @(
    "python",
    "python3",
    "py",
    "C:\Users\admin\AppData\Local\Programs\Python\Python312\python.exe",
    "C:\Program Files\Python312\python.exe"
)

foreach ($c in $Candidates) {
    try {
        $ver = & $c --version 2>&1
        if ($LASTEXITCODE -eq 0) {
            $Python = $c
            Write-Host "  √ 找到: $Python  ($ver)" -ForegroundColor Green
            break
        }
    } catch {
        # 继续尝试下一个
    }
}

if (-not $Python) {
    Write-Host "  × 未找到 Python，请先安装 Python 3.10+" -ForegroundColor Red
    Write-Host "    安装方式: winget install Python.Python.3.12" -ForegroundColor Yellow
    exit 1
}

# ── Step 2: 安装依赖 ────────────────────────────────────────────────────
Write-Host ""
Write-Host "[2/4] 检查依赖..." -ForegroundColor White

$RequiredPkgs = @("pytest", "pytest-asyncio", "reflex", "sqlmodel", "aiomysql", "pymysql", "bcrypt")
$Missing = @()

foreach ($pkg in $RequiredPkgs) {
    $check = & $Python -c "import $($pkg -replace '-','_')" 2>&1
    if ($LASTEXITCODE -ne 0) {
        $Missing += $pkg
    }
}

if ($Missing.Count -gt 0) {
    Write-Host "  ⚠ 安装缺失依赖: $($Missing -join ' ')" -ForegroundColor Yellow
    & $Python -m pip install --quiet $Missing 2>&1 | Select-Object -Last 3
    Write-Host "  √ 依赖安装完成" -ForegroundColor Green
} else {
    Write-Host "  √ 所有依赖已就绪" -ForegroundColor Green
}

# ── Step 3: 环境变量 ────────────────────────────────────────────────────
Write-Host ""
Write-Host "[3/4] 配置测试环境变量..." -ForegroundColor White

# 从 .env 加载（如果存在）
$EnvFile = Join-Path $ProjectRoot ".env"
if (Test-Path $EnvFile) {
    Get-Content $EnvFile | ForEach-Object {
        $line = $_.Trim()
        if ($line -and -not $line.StartsWith("#") -and $line.Contains("=")) {
            $parts = $line.Split("=", 2)
            $key = $parts[0].Trim()
            $val = $parts[1].Trim()
            [Environment]::SetEnvironmentVariable($key, $val, "Process")
        }
    }
}
# 测试环境覆盖
$env:REFLEX_DB_URL = "sqlite:///:memory:"
$env:PYTHONPATH = $ProjectRoot

Write-Host "  √ 环境变量已设置" -ForegroundColor Green

# ── Step 4: 运行测试 ────────────────────────────────────────────────────
Write-Host ""
Write-Host "[4/4] 运行 TDD 测试..." -ForegroundColor White
Write-Host ""
Write-Host "  ────────────────────────────────────────────" -ForegroundColor Cyan

Set-Location $ProjectRoot

$PassCount = 0
$FailCount = 0
$TestRoot = "$ProjectRoot\tests\reflex"

# 测试 1: F_S_050 响应式布局
Write-Host ""
Write-Host "  测试组 1: F_S_050 响应式布局" -ForegroundColor White
Write-Host ""
& $Python -m pytest "$TestRoot\test_F_S_050_responsive.py" -v --tb=short --no-header --rootdir="$TestRoot" 2>&1
if ($LASTEXITCODE -eq 0) {
    $PassCount += 3
    Write-Host ""
    Write-Host "    🟢 F_S_050 全部通过 (3/3)" -ForegroundColor Green
} else {
    $FailCount += 1
}

# 测试 2: F_S_051 异常提示/网络韧性
Write-Host ""
Write-Host "  测试组 2: F_S_051 异常提示 & 网络韧性" -ForegroundColor White
Write-Host ""
& $Python -m pytest "$TestRoot\test_F_S_051_error.py" -v --tb=short --no-header --rootdir="$TestRoot" 2>&1
if ($LASTEXITCODE -eq 0) {
    $PassCount += 4
    Write-Host ""
    Write-Host "    🟢 F_S_051 全部通过 (4/4)" -ForegroundColor Green
} else {
    $FailCount += 1
}

# 测试 3: F_S_022 回归验证
Write-Host ""
Write-Host "  测试组 3: F_S_022 截止规则（回归验证）" -ForegroundColor White
Write-Host ""
& $Python -m pytest "$TestRoot\test_F_S_022_deadline.py" -v --tb=short --no-header --rootdir="$TestRoot" 2>&1
if ($LASTEXITCODE -eq 0) {
    $PassCount += 4
    Write-Host ""
    Write-Host "    🟢 F_S_022 全部通过 (4/4) — 无回归" -ForegroundColor Green
} else {
    $FailCount += 1
}

Write-Host ""
Write-Host "  ────────────────────────────────────────────" -ForegroundColor Cyan

# ── 结果汇总 ────────────────────────────────────────────────────────────
Write-Host ""
Write-Host "╔══════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║              测 试 结 果 汇 总                              ║" -ForegroundColor Cyan
Write-Host "╚══════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

if ($FailCount -eq 0) {
    Write-Host "  ✅ 全部通过 — $PassCount 个测试" -ForegroundColor Green
    Write-Host ""
    Write-Host "  自动化测试已通过，请继续执行手动测试：" -ForegroundColor Green
    Write-Host "    1. 响应式布局测试（见测试指南）" -ForegroundColor Green
    Write-Host "    2. 网络韧性测试（见测试指南）" -ForegroundColor Green
    Write-Host ""
    Write-Host "  手动测试步骤:" -ForegroundColor White
    Write-Host "    cd oaepp" -ForegroundColor Cyan
    Write-Host "    reflex run" -ForegroundColor Cyan
    Write-Host "    然后按 tests/reflex/F_S_050_测试指南.md 逐项验证" -ForegroundColor Cyan
} else {
    Write-Host "  ❌ $FailCount 组测试失败" -ForegroundColor Red
}

Write-Host ""
exit $FailCount
