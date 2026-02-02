# Multi-DPI Icon Generator - Quick Start Guide

## Problem
Windows Titlebar-Icons erscheinen unscharf auf High-DPI Bildschirmen, weil die `.ico`-Datei nicht alle benötigten Größen enthält.

## Lösung
Generiere eine neue `dictate.ico` mit **allen DPI-Größen** (16/20/24/28/32/40/48/64/96/128/256 px).

---

## Benötigte Größen für alle Bildschirme

| Größe | Verwendung |
|-------|-----------|
| **16×16** | Titlebar @ 100% DPI (96) |
| **20×20** | Titlebar @ 125% DPI (120) ⭐ Häufig |
| **24×24** | Titlebar @ 150% DPI (144) ⭐ Häufig |
| **28×28** | Titlebar @ 175% DPI (168) |
| **32×32** | Titlebar @ 200% DPI (192) ⭐ Häufig |
| **40×40** | Titlebar @ 250% DPI (240) |
| **48×48** | Titlebar @ 300% DPI (288) |
| **64×64** | Taskbar @ 100-150% |
| **96×96** | Taskbar @ 200-250% |
| **128×128** | Taskbar @ 300% |
| **256×256** | High-res displays |

---

## Voraussetzungen

```bash
# Install Pillow (Python image library)
pip install pillow

# Optional: Für SVG-Support
pip install cairosvg
```

---

## Option 1: Quick Rebuild (Empfohlen)

Wenn du bereits eine hochauflösende Version deines Icons hast:

```bash
# 1. Benenne dein Source-Image (mindestens 256×256 px)
#    Beispiel: dictate_source.png, logo.png, oder dictate.svg

# 2. Führe das Rebuild-Script aus
python rebuild_dictate_icon.py

# 3. Mit Preview (empfohlen zum Testen)
python rebuild_dictate_icon.py --preview
```

Das Script:
- ✅ Findet automatisch dein Source-Image
- ✅ Erstellt Backup von alter dictate.ico
- ✅ Generiert alle DPI-Größen
- ✅ Optimiert kleine Icons automatisch
- ✅ Optional: Erstellt Preview-Bild

---

## Option 2: Manuelle Kontrolle

Für volle Kontrolle über alle Parameter:

```bash
# Basic: Eine Source-Datei für alle Größen
python generate_ico.py logo.png dictate.ico

# Advanced: Separate vereinfachte Version für kleine Icons
python generate_ico.py logo_detailed.png dictate.ico --simplify logo_simple.png

# Mit Preview
python generate_ico.py logo.png dictate.ico --preview

# Von SVG (beste Qualität)
python generate_ico.py logo.svg dictate.ico --preview
```

---

## Tipps für optimale Ergebnisse

### 1. Source-Image Empfehlungen

**Beste Qualität:**
- ✅ SVG (Vektor) - skaliert perfekt auf jede Größe
- ✅ PNG mit mindestens 512×512 px
- ✅ Transparenter Hintergrund (RGBA)

**Akzeptabel:**
- ⚠️ PNG mit 256×256 px (Minimum)
- ⚠️ JPG funktioniert, aber kein Transparenz

**Problematisch:**
- ❌ PNG < 256×256 px - wird unscharf beim Hochskalieren
- ❌ Bereits als ICO - kann nicht gut hochskaliert werden

### 2. Design-Tipps für kleine Icons (16-32 px)

Bei **16×16 bis 32×32 px** ist Platz extrem begrenzt:

**❌ Schlecht:**
- Viele kleine Details (verschwimmen)
- Dünne Linien (verschwinden)
- Komplexe Farbverläufe (matschig)
- Text unter 8-10px Höhe (unleserlich)

**✅ Gut:**
- Einfache, klare Formen
- Dicke Linien (mindestens 2-3 px)
- Hoher Kontrast
- Flächige Farben
- Reduziertes Design

**Beispiel:**
```
Original (256px):     Simplified (16px):
[Complex Logo]    →   [Simple "D" Letter]
 + Subtitle           + Bold
 + Border             + High contrast
 + Gradient           + Solid colors
```

### 3. Zwei-Versionen-Strategie (Empfohlen)

Erstelle **zwei Versionen** deines Icons:

1. **Detailed Version** (für große Größen 64-256 px)
   - Volles Design
   - Alle Details
   - Farbverläufe OK

2. **Simplified Version** (für kleine Größen 16-48 px)
   - Reduziertes Design
   - Dickere Linien
   - Hoher Kontrast
   - Keine kleinen Details

**Verwendung:**
```bash
python generate_ico.py logo_detailed.png dictate.ico \
    --simplify logo_simple.png \
    --simplify-threshold 48
```

---

## Nach dem Generieren

### 1. Icon ersetzen
```bash
# Alte Icon wurde automatisch als dictate_backup_YYYYMMDD_HHMMSS.ico gesichert
# Die neue dictate.ico ist bereit
```

### 2. Windows Icon Cache leeren

**Option A: Soft Reset (schnell)**
```powershell
ie4uinit.exe -show
```

**Option B: Hard Reset (bei hartnäckigen Problemen)**
```powershell
# Als Administrator:
cd %LOCALAPPDATA%\Microsoft\Windows\Explorer
del iconcache* /a
shutdown /r /t 0
```

### 3. App neustarten
```bash
# Dictate-App komplett beenden und neu starten
# Icon sollte jetzt auf allen DPI-Stufen scharf sein
```

---

## Testing auf verschiedenen DPI-Stufen

### DPI in Windows ändern:
1. **Settings** → **System** → **Display**
2. **Scale** ändern: 100%, 125%, 150%, 175%, 200%, 250%
3. Abmelden/Anmelden oder neu starten
4. Dictate starten und Titlebar-Icon prüfen

### Was testen:
- ✅ Titlebar-Icon (oben links im Fenster)
- ✅ Close-Dialog Icon (beim Fenster schließen)
- ✅ Taskbar-Icon
- ✅ Alt+Tab Icon
- ✅ Tray Icon (separate Datei, nicht betroffen)

---

## ICO-Datei analysieren

Um zu überprüfen, welche Größen in einer .ico enthalten sind:

```bash
python check_ico.py
```

**Erwartete Ausgabe:**
```
✅ Valid ICO file with 11 image(s)

Sizes found in ICO:
----------------------------------------
  • 16×16 px
  • 20×20 px
  • 24×24 px
  • 28×28 px
  • 32×32 px
  • 40×40 px
  • 48×48 px
  • 64×64 px
  • 96×96 px
  • 128×128 px
  • 256×256 px
```

---

## Troubleshooting

### Problem: Immer noch unscharf

**Mögliche Ursachen:**

1. **Windows Icon Cache nicht geleert**
   ```powershell
   ie4uinit.exe -show
   # oder Neustart
   ```

2. **App verwendet alte AppID**
   ```python
   # In config.py oder beim Start ändern:
   set DICTATE_APPID=Dictate_v2
   ```

3. **Source-Image zu klein**
   - Verwende mindestens 256×256 px
   - Besser: 512×512 px oder SVG

4. **Kleine Icons zu komplex**
   - Erstelle vereinfachte Version
   - Verwende `--simplify` Parameter

### Problem: Script findet kein Source-Image

```bash
# Explizit Source angeben:
python rebuild_dictate_icon.py --source /pfad/zu/logo.png

# Oder in aktuelles Verzeichnis kopieren als:
dictate_source.png
```

### Problem: Pillow nicht installiert

```bash
# Im Conda-Environment:
conda activate fasterwhisper
pip install pillow

# Oder system-weit:
python -m pip install pillow
```

---

## Beispiel-Workflow

### Szenario: Du hast nur dein aktuelles dictate.ico

```bash
# 1. Prüfe aktuelle ICO:
python check_ico.py
# → Zeigt: Nur 16×16 und 256×256 vorhanden

# 2. Extrahiere größte Variante als PNG:
python -c "from PIL import Image; img=Image.open('dictate.ico'); img.save('dictate_source.png')"

# 3. Optional: In Bildbearbeitung optimieren
#    - Auf 512×512 hochskalieren (z.B. mit waifu2x oder Photoshop Super Resolution)
#    - Vereinfachte Version für kleine Größen erstellen

# 4. Neue ICO generieren:
python rebuild_dictate_icon.py --source dictate_source.png --preview

# 5. Cache leeren & testen:
ie4uinit.exe -show
```

---

## Alternative Tools

Falls Python nicht funktioniert:

### IcoFX (Windows GUI)
- Download: https://icofx.ro/
- Importiere PNG/SVG
- Erstelle alle Größen manuell
- Export als ICO

### GIMP (Open Source)
- Mit ICO-Plugin
- Batch-resize möglich
- Export mit mehreren Größen

### Online Tools
- https://convertico.com/
- https://redketchup.io/icon-converter
- https://icoconvert.com/

**⚠️ Achtung:** Online-Tools erstellen oft nicht alle benötigten Größen!

---

## Weiterführende Links

- **Windows DPI Scaling**: https://docs.microsoft.com/en-us/windows/win32/hidpi/high-dpi-desktop-application-development-on-windows
- **ICO Format Spec**: https://en.wikipedia.org/wiki/ICO_(file_format)
- **Pillow Docs**: https://pillow.readthedocs.io/

---

## Zusammenfassung

```bash
# Quick Start (3 Schritte):

# 1. Prepare source image (min 256×256 px)
#    → dictate_source.png

# 2. Generate ICO
python rebuild_dictate_icon.py --preview

# 3. Clear cache & restart
ie4uinit.exe -show
```

**Ergebnis:** Gestochen scharfe Icons auf allen DPI-Stufen! ✨
