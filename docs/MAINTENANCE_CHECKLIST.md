# Project Maintenance Checklist (Windows)

**For humans:** This is an AI prompt for maintaining codebases. Use it every 5-10 changes or before releases to keep documentation synchronized with code.

**For AI:** Execute this checklist to update all project documentation and ensure production-readiness.

## REQUIRED FILES

### Root Directory

```
README.md                  - Project overview, features, quick start
INSTALL.md                 - Installation guide with troubleshooting
CHANGELOG.md               - Version history
LICENSE                    - Legal terms
VERSION                    - Current version (e.g., "1.2.0")
environment-win-gpu.yml    - Conda env (GPU/CUDA)
environment-win-cpu.yml    - Conda env (CPU)
environment.yml            - Alias for CPU env
.gitignore                 - Files to exclude from git
install.ps1                - Automated installation
create_shortcut.ps1        - Start Menu shortcut
start_dictate.ps1          - Application launcher
smoke_test.py              - Basic functionality tests
```

### docs/ Directory

```
ARCHITECTURE.md            - Code organization
DEVELOPMENT_GUIDELINES.md  - Developer setup and coding standards
```

## MAINTENANCE TASKS

### 1. Code Inventory

**Scan codebase:**
```powershell
Get-ChildItem -Recurse -Include *.py | Select-Object FullName
Get-ChildItem -Recurse -Include *.py | ForEach-Object { (Get-Content $_).Count } | Measure-Object -Sum
```

**Extract:**
- Entry points (files with `if __name__ == "__main__"`)
- Main classes/functions
- Dependencies (imports)
- Configuration files used

### 2. Dependency Check

**Conda environment:**
```powershell
conda list -n fasterwhisper
```

**Compare with documented versions:**
- Are versions in environment YML files current?
- Are versions pinned with `==`?
- Any new dependencies missing from docs?

### 3. Documentation Sync

**For each file, verify:**

| File | Must Match | Check |
|------|-----------|-------|
| README.md | Current features | Does example code work? |
| INSTALL.md | install.ps1 steps | Does it match actual script? |
| ARCHITECTURE.md | Code structure | Are module names current? |
| CHANGELOG.md | Git history | Last 5-10 commits documented? |
| VERSION | Latest tag/release | Matches CHANGELOG? |

### 4. Testing

**Run:**
```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\install.ps1
python smoke_test.py
```

**Verify:**
- Installation succeeds
- Smoke tests pass
- No errors in logs

### 5. Git Hygiene

**Check:**
```powershell
git status
git log --oneline -10
git tag
```

**Ensure:**
- No uncommitted changes in tracked files
- .gitignore covers secrets (*.env, config.yml, *.key)
- Latest changes have meaningful commit messages

### 6. Release Checklist (if applicable)

**Before release:**
- [ ] Update VERSION file
- [ ] Update CHANGELOG.md with changes since last release
- [ ] Update README.md if features changed
- [ ] Run full test suite
- [ ] Tag commit: `git tag vX.Y.Z`

## EXECUTION STEPS

1. **Scan:** Inventory code and dependencies
2. **Compare:** Check docs match reality
3. **Update:** Fix any mismatches
4. **Test:** Run install.ps1 + smoke tests
5. **Commit:** If releasing, tag version

**Frequency:** Every 5-10 commits, before releases, before deploying to new machines.
