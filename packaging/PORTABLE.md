# Portable Build (Windows)

Ziel: `Dictate.exe` als portable Ordner-App (ZIP) ohne Conda/Installer auf Zielmaschinen.

## Grundidee

- Build-Maschine: einmaliges Build-Environment (Conda/Miniforge ok).
- Ergebnis: `release/DictatePortable_<version>_win64.zip`
  - entpacken
  - `Dictate/Dictate.exe` starten
  - nutzt GPU, wenn vorhanden (sonst CPU-Fallback)

## Voraussetzungen (Build-Maschine)

- Windows 10/11
- Python 3.10 (oder das Repo-Conda env)
- GPU-Build empfohlen: `environment-win-gpu.yml` (enthaelt CUDA Runtime)
- Modelle vorher herunterladen: `download_models.ps1`

## Schritte (empfohlen: GPU-Build + Modelle im Paket)

```powershell
cd C:\path\to\_AA_DICTATE_WIN

# 1) Build-Env erstellen (einmalig) – empfohlen GPU-Env
conda env create -f environment-win-gpu.yml
conda activate fasterwhisper

# 2) PyInstaller installieren (nur Build-Maschine)
python -m pip install --upgrade pip
python -m pip install pyinstaller

# 3) Modelle lokal ins Repo laden (werden in das ZIP kopiert)
Set-ExecutionPolicy -Scope Process Bypass
.\download_models.ps1 -Models @("base","small","large-v3-turbo")

# 4) Portable ZIP bauen
.\packaging\build_portable.ps1 -IncludeModels
```

Ergebnis: `release/DictatePortable_<version>_win64.zip`

## Optional: Modelle separat ausliefern

```powershell
.\packaging\build_portable.ps1 -SplitModels
```

- App: `release/DictatePortable_<version>_win64_nomodels.zip`
- Modelle: `release/DictateModels_<version>.zip`
- Entpacken der Modelle in den App-Ordner per `packaging/extract_models.ps1`

## Testplan (Clean Windows)

1. Auf einem frischen Windows 10/11 (ohne Conda/Python) `DictatePortable_*.zip` entpacken.
2. `Dictate/Dictate.exe` starten.
3. Tray-Icon erscheint, Window laesst sich anzeigen/ausblenden.
4. GPU-Fall: in der Konsole/Logs muss GPU als verfuegbar erkannt werden (und `use_gpu=True`).
5. CPU-Fall: App startet trotzdem, waehlt automatisch CPU-Fallback (langsamer).
6. Modell-Fund: `Dictate/models/<model>` oder `~/Music/dictate/models/<model>` wird verwendet (kein Online-Download noetig).
