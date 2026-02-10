# PFCV Project Cleanup Script
# Safely removes redundant and outdated files

Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host "PFCV PROJECT CLEANUP SCRIPT" -ForegroundColor Yellow
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host ""

# Step 0: Verify we're in the right directory
if (-not (Test-Path "pyproject.toml")) {
    Write-Host "ERROR: Must run from project root directory!" -ForegroundColor Red
    exit 1
}

# Step 1: Create backup commit
Write-Host "[1/5] Creating backup commit..." -ForegroundColor Cyan
git add .
git commit -m "Checkpoint before cleanup" 2>$null
if ($LASTEXITCODE -eq 0) {
    Write-Host "[OK] Backup commit created" -ForegroundColor Green
} else {
    Write-Host "[WARN] No changes to commit (or git not initialized)" -ForegroundColor Yellow
}

# Step 2: Run verification
Write-Host ""
Write-Host "[2/5] Running verification..." -ForegroundColor Cyan
python scripts/verify_before_cleanup.py
if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] Verification failed! Aborting cleanup." -ForegroundColor Red
    exit 1
}

# Step 3: Prompt for confirmation
Write-Host ""
Write-Host "[3/5] Confirming deletion..." -ForegroundColor Cyan
$confirmation = Read-Host "Proceed with file deletion? (yes/no)"
if ($confirmation -ne "yes") {
    Write-Host "Cleanup cancelled by user." -ForegroundColor Yellow
    exit 0
}

# Step 4: Delete files
Write-Host ""
Write-Host "[4/5] Deleting files..." -ForegroundColor Cyan

$deletedCount = 0
$failedCount = 0

# Function to safely delete
function Safe-Delete {
    param($Path)
    
    if (Test-Path $Path) {
        try {
            Remove-Item $Path -Recurse -Force
            Write-Host "  [OK] Deleted: $Path" -ForegroundColor Green
            return $true
        } catch {
            Write-Host "  [FAIL] Failed: $Path" -ForegroundColor Red
            return $false
        }
    } else {
        Write-Host "  [SKIP] Not found: $Path" -ForegroundColor Gray
        return $null
    }
}

# Category A: Duplicate Documentation
Write-Host ""
Write-Host "Category A: Duplicate Documentation" -ForegroundColor Yellow
$result = Safe-Delete "docs\CHANGELOG.md"
if ($result -eq $true) { $deletedCount++ } elseif ($result -eq $false) { $failedCount++ }

$result = Safe-Delete "docs\CONTRIBUTING.md"
if ($result -eq $true) { $deletedCount++ } elseif ($result -eq $false) { $failedCount++ }

$result = Safe-Delete "docs\api_reference.md"
if ($result -eq $true) { $deletedCount++ } elseif ($result -eq $false) { $failedCount++ }

# Category B: Outdated/Superseded Files
Write-Host ""
Write-Host "Category B: Outdated Specification Files" -ForegroundColor Yellow
$result = Safe-Delete "modules\module_01_ffi_verifier\SYSTEM_ARCHITECTURE.md"
if ($result -eq $true) { $deletedCount++ } elseif ($result -eq $false) { $failedCount++ }

$result = Safe-Delete "modules\module_02_verification_pipeline\VERIFICATION_PIPELINE.md"
if ($result -eq $true) { $deletedCount++ } elseif ($result -eq $false) { $failedCount++ }

$result = Safe-Delete "modules\module_03_build_process\BUILD_PROCESS.md"
if ($result -eq $true) { $deletedCount++ } elseif ($result -eq $false) { $failedCount++ }

$result = Safe-Delete "modules\module_04_native_interface_ingestion\NATIVE_INTERFACE_INGESTION.md"
if ($result -eq $true) { $deletedCount++ } elseif ($result -eq $false) { $failedCount++ }

$result = Safe-Delete "releases\MODULE_02_CERTIFICATION.md"
if ($result -eq $true) { $deletedCount++ } elseif ($result -eq $false) { $failedCount++ }

$result = Safe-Delete "releases\RELEASE_NOTES_v1.0.0.md"
if ($result -eq $true) { $deletedCount++ } elseif ($result -eq $false) { $failedCount++ }

# Category C: Stub Files
Write-Host ""
Write-Host "Category C: Stub Python Files" -ForegroundColor Yellow
$result = Safe-Delete "modules\module_01_ffi_verifier\system_architecture.py"
if ($result -eq $true) { $deletedCount++ } elseif ($result -eq $false) { $failedCount++ }

$result = Safe-Delete "modules\module_02_verification_pipeline\verification_pipeline.py"
if ($result -eq $true) { $deletedCount++ } elseif ($result -eq $false) { $failedCount++ }

$result = Safe-Delete "modules\module_03_build_process\build_process.py"
if ($result -eq $true) { $deletedCount++ } elseif ($result -eq $false) { $failedCount++ }

$result = Safe-Delete "modules\module_04_native_interface_ingestion\native_interface_ingestion.py"
if ($result -eq $true) { $deletedCount++ } elseif ($result -eq $false) { $failedCount++ }

# Category E: Config Redundancy
Write-Host ""
Write-Host "Category E: Redundant Config Files" -ForegroundColor Yellow
$result = Safe-Delete "config\pytest.ini"
if ($result -eq $true) { $deletedCount++ } elseif ($result -eq $false) { $failedCount++ }

$result = Safe-Delete "config\requirements-dev.txt"
if ($result -eq $true) { $deletedCount++ } elseif ($result -eq $false) { $failedCount++ }

$result = Safe-Delete "config\requirements.txt"
if ($result -eq $true) { $deletedCount++ } elseif ($result -eq $false) { $failedCount++ }

# Category F: Development Tracking
Write-Host ""
Write-Host "Category F: Development Tracking Files" -ForegroundColor Yellow
$result = Safe-Delete "docs\module_06_completion_summary.md"
if ($result -eq $true) { $deletedCount++ } elseif ($result -eq $false) { $failedCount++ }

# Category G: Cleanup Scripts Directory
Write-Host ""
Write-Host "Category G: CLEANUPAI Directory" -ForegroundColor Yellow
$result = Safe-Delete "CLEANUPAI"
if ($result -eq $true) { $deletedCount++ } elseif ($result -eq $false) { $failedCount++ }

# Clean up empty directories
Write-Host ""
Write-Host "Cleaning up empty directories..." -ForegroundColor Yellow
if ((Test-Path "config") -and ((Get-ChildItem "config" | Measure-Object).Count -eq 0)) {
    $result = Safe-Delete "config"
    if ($result -eq $true) { $deletedCount++ }
}
if ((Test-Path "releases") -and ((Get-ChildItem "releases" | Measure-Object).Count -eq 0)) {
    $result = Safe-Delete "releases"
    if ($result -eq $true) { $deletedCount++ }
}

# Step 5: Verification
Write-Host ""
Write-Host "[5/5] Running post-cleanup tests..." -ForegroundColor Cyan
Write-Host "Testing package imports..." -ForegroundColor Gray
python -c "import module_05_ir_normalization; import module_06_contract_schema; print('[OK] Imports successful')"
if ($LASTEXITCODE -eq 0) {
    Write-Host "[OK] Package imports working" -ForegroundColor Green
} else {
    Write-Host "[ERROR] Import test failed!" -ForegroundColor Red
    Write-Host "[WARN] You may need to restore from git" -ForegroundColor Yellow
}

# Final summary
Write-Host ""
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host "CLEANUP COMPLETE" -ForegroundColor Yellow
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Files deleted: $deletedCount" -ForegroundColor Green
if ($failedCount -gt 0) {
    Write-Host "Files failed: $failedCount" -ForegroundColor Red
} else {
    Write-Host "Files failed: $failedCount" -ForegroundColor Gray
}
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "  1. Review changes: git status" -ForegroundColor White
Write-Host "  2. Run tests: pytest tests/ -v" -ForegroundColor White
Write-Host "  3. Commit cleanup: git add . ; git commit -m 'Cleanup: Remove redundant files'" -ForegroundColor White
Write-Host ""

if ($failedCount -eq 0 -and $deletedCount -gt 0) {
    Write-Host "[SUCCESS] Cleanup successful!" -ForegroundColor Green
} elseif ($failedCount -gt 0) {
    Write-Host "[WARN] Cleanup completed with errors" -ForegroundColor Yellow
} else {
    Write-Host "[INFO] No files were deleted" -ForegroundColor Gray
}
