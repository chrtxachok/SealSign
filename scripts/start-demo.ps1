param(
    [ValidateRange(1, 65535)]
    [int]$Port = 8765,
    [switch]$NoBrowser
)

$ErrorActionPreference = 'Stop'
$repo = Split-Path -Parent $PSScriptRoot
$localPackages = Join-Path $repo 'artifacts/s05-site-packages-verified'
$versionedPython = Join-Path $repo 'artifacts/.uv-python-s05/cpython-3.11.18-windows-x86_64-none'
$python = @(
    (Join-Path $versionedPython 'python.exe'),
    (Join-Path $versionedPython 'pythonw.exe'),
    (Join-Path $repo '.venv/Scripts/python.exe')
) | Where-Object { Test-Path -LiteralPath $_ -PathType Leaf } | Select-Object -First 1
if (!$python) {
    $available = Get-Command python -CommandType Application -ErrorAction SilentlyContinue
    if (!$available) { throw 'Install Python and the packages listed in requirements-s05.txt.' }
    $python = $available.Source
}

$paths = @((Join-Path $repo 'src'))
if (Test-Path -LiteralPath $localPackages -PathType Container) { $paths += $localPackages }
if ($env:PYTHONPATH) { $paths += $env:PYTHONPATH }
$previousPythonPath = $env:PYTHONPATH
$previousPythonUtf8 = $env:PYTHONUTF8
$logs = Join-Path $repo 'artifacts/demo'
New-Item -Path $logs -ItemType Directory -Force | Out-Null
$serverArgs = @('-u', '-m', 'sealsign', 'demo', '--port', $Port)
if (!$NoBrowser) { $serverArgs += '--open' }
try {
    $env:PYTHONPATH = $paths -join [IO.Path]::PathSeparator
    $env:PYTHONUTF8 = '1'
    $options = @{
        FilePath = $python
        ArgumentList = $serverArgs
        WorkingDirectory = $repo
        WindowStyle = 'Hidden'
        RedirectStandardOutput = Join-Path $logs "server-$Port.log"
        RedirectStandardError = Join-Path $logs "server-$Port-errors.log"
        PassThru = $true
    }
    $process = Start-Process @options
} finally {
    $env:PYTHONPATH = $previousPythonPath
    $env:PYTHONUTF8 = $previousPythonUtf8
}
Write-Output "SealSign PID $($process.Id) http://127.0.0.1:${Port}/"
