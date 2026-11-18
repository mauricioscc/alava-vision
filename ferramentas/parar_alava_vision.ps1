# =============================================================================
#  Alava Vision - fecha servidor, player e o Chrome da TV
#  (ferramentas/parar_alava_vision.ps1) - versao 0.7.0
#
#  Usado pelo atualizar.bat antes do git pull. Pode ser rodado sozinho:
#    powershell -ExecutionPolicy Bypass -File ferramentas\parar_alava_vision.ps1 -Dir "C:\Alava Vision" -Port 8080
#  -Simular: so lista o que seria fechado, sem fechar nada (diagnostico).
#
#  Fecha SO o que pertence a esta instalacao (pasta -Dir):
#    - janelas cmd dos iniciar_*.bat desta pasta
#    - python rodando o player.py ou o uvicorn (servidor) desta pasta
#    - Chrome/Edge aberto com o perfil data\browser-profile desta pasta (a tela da TV)
#    - python escutando na porta do .env (servidor aberto por versoes antigas dos .bat)
#    - python rodando "player.py" sem caminho (player aberto por versoes antigas dos .bat)
#  Outros programas Python e outras janelas do Chrome nao sao tocados.
#
#  Este arquivo fica sem acentos de proposito: o PowerShell 5 le .ps1 sem BOM como ANSI.
#
#  COMO REVERTER: git checkout <commit> -- ferramentas/parar_alava_vision.ps1
# =============================================================================
param(
    [Parameter(Mandatory = $true)][string]$Dir,
    [int]$Port = 8080,
    [switch]$Simular
)

$d = (Resolve-Path -LiteralPath $Dir).Path.TrimEnd('\').ToLower()
$profileDir = "$d\data\browser-profile"
$procs = @(Get-CimInstance Win32_Process | Where-Object { $_.CommandLine })
$ids = New-Object System.Collections.Generic.HashSet[int]

foreach ($p in $procs) {
    $c = $p.CommandLine.ToLower()
    $n = $p.Name.ToLower()
    $isPython = $n -like 'python*.exe'
    if ($n -eq 'cmd.exe' -and $c.Contains($d) -and $c.Contains('iniciar_')) { [void]$ids.Add($p.ProcessId) }
    elseif ($isPython -and $c.Contains($d) -and ($c.Contains('player.py') -or $c.Contains('uvicorn'))) { [void]$ids.Add($p.ProcessId) }
    elseif ($isPython -and $c -match '(^|[\s"])player\.py("|\s|$)') { [void]$ids.Add($p.ProcessId) }
    elseif (($n -eq 'chrome.exe' -or $n -eq 'msedge.exe') -and $c.Contains($profileDir)) { [void]$ids.Add($p.ProcessId) }
}

try {
    foreach ($conn in @(Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction Stop)) {
        $owner = $procs | Where-Object { $_.ProcessId -eq $conn.OwningProcess }
        if ($owner -and $owner.Name -like 'python*.exe') { [void]$ids.Add($owner.ProcessId) }
    }
} catch {}

[void]$ids.Remove($PID)
if ($ids.Count -eq 0) {
    Write-Host "  Nada do Alava Vision estava aberto."
    exit 0
}
if ($Simular) {
    foreach ($id in $ids) {
        $p = $procs | Where-Object { $_.ProcessId -eq $id }
        $c = $p.CommandLine
        Write-Host ("  fecharia PID {0} {1}: {2}" -f $id, $p.Name, $c.Substring(0, [Math]::Min(110, $c.Length)))
    }
    exit 0
}
foreach ($id in $ids) { & taskkill.exe /T /F /PID $id 2>&1 | Out-Null }
Start-Sleep -Seconds 2
Write-Host "  Alava Vision fechado ($($ids.Count) processo(s))."
exit 0
