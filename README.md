# IT--bung

## Beschreibung

Dieses Projekt enthält drei Streamlit-Apps zur Anzeige von **Lastprofilen aus SMARD** (offizielle Strommarktdaten der Bundesnetzagentur). Die Apps laden die stündliche Netzlast und stellen sie als interaktive Diagramme dar.

Die empfohlene App ist **`app_multi_view.py`** – sie vereint vier Ansichten:

- **Standard-Ansicht:** Lastprofil von einem wählbaren Start- bis Enddatum
- **Kalenderwochen-Overlay:** Wochenverlauf pro Wochentag, mehrere Kalenderwochen überlagert
- **Tage vergleichen:** bis zu 7 einzelne Tage direkt nebeneinander
- **Boxplot: Lastverteilung:** zeigt die Streuung der Last (Median, Quartile, Ausreißer) – wahlweise pro Stunde des Tages (über bis zu 7 gewählte Tage) oder pro Wochentag (über einen gewählten Zeitraum)

Die beiden anderen Apps sind Einzelansichten: `app.py` (einfaches Lastprofil) und `app_weekly_overlay.py` (nur Wochenvergleich).

> **Hinweis:** Die Apps laden die Daten live von SMARD. Du brauchst also eine Internetverbindung, und der erste Ladevorgang kann ein paar Sekunden dauern.

---

## Voraussetzungen

- **Python 3.10 oder neuer** muss installiert sein.
  - Prüfen (siehe Schritt 1). Falls nicht vorhanden: von [python.org](https://www.python.org/downloads/) herunterladen.
  - **Windows:** Beim Installieren unbedingt das Häkchen **„Add Python to PATH"** setzen.
- Internetverbindung (die Apps laden Daten von SMARD).

---

## Setup – Schritt für Schritt

Die Befehle gibt es jeweils für **Windows (PowerShell)** und **macOS / Linux (Terminal)**. Nimm die Spalte, die zu deinem System passt. Am einfachsten geht alles direkt im **VS-Code-Terminal** (Menü *Terminal → New Terminal*).

### Schritt 1 – Python prüfen

**Windows (PowerShell):**
```powershell
python --version
```

**macOS / Linux:**
```bash
python3 --version
```

Es sollte z. B. `Python 3.12.x` erscheinen. Kommt ein Fehler oder öffnet sich ein Store/Installationsfenster, ist Python noch nicht (richtig) installiert → siehe Voraussetzungen.

### Schritt 2 – Code herunterladen

1. Auf der GitHub-Seite oben rechts auf den grünen Button **`< > Code`** → **Download ZIP**.
2. ZIP entpacken (Windows: Rechtsklick → „Alle extrahieren"; Mac: Doppelklick). Du erhältst den Ordner **`IT--bung-main`**.

Alternativ mit Git:
```bash
git clone https://github.com/lukasroehl107/IT--bung.git
```

### Schritt 3 – In den Projektordner wechseln

Wechsle in den entpackten Ordner. **Passe den Pfad an den Ort an, wo der Ordner bei dir liegt** (z. B. im Downloads-Ordner).

**Windows (PowerShell):**
```powershell
cd "$HOME\Downloads\IT--bung-main"
```

**macOS / Linux:**
```bash
cd ~/Downloads/IT--bung-main
```

> **Tipp:** In VS Code kannst du dir das sparen: *File → Open Folder…* → den Ordner `IT--bung-main` auswählen, dann ist das Terminal automatisch im richtigen Ordner. Prüfen mit `ls` (Mac/Linux) bzw. `dir` (Windows) – die Datei `app_multi_view.py` sollte in der Liste auftauchen.

### Schritt 4 – Virtuelle Umgebung anlegen und aktivieren

Eine virtuelle Umgebung (`venv`) hält die Pakete dieses Projekts getrennt von deinem System.

**Windows (PowerShell):**
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

> **Falls auf Windows ein roter Fehler kommt** („… die Ausführung von Skripts ist deaktiviert"): einmalig diesen Befehl ausführen und dann die Aktivierung erneut versuchen:
> ```powershell
> Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
> ```

**macOS / Linux:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

Danach steht **`(.venv)`** vorne in der Terminalzeile – die Umgebung ist aktiv.

### Schritt 5 – Abhängigkeiten installieren

**Windows (PowerShell):**
```powershell
python -m pip install --upgrade pip
python -m pip install streamlit pandas plotly requests
```

**macOS / Linux:**
```bash
python3 -m pip install --upgrade pip
python3 -m pip install streamlit pandas plotly requests
```

Das dauert ein bis zwei Minuten und es rauscht viel Text durch – das ist normal.

### Schritt 6 – App starten

**Empfohlene App (Multi-View, alle drei Ansichten):**

Windows:
```powershell
python -m streamlit run app_multi_view.py
```
macOS / Linux:
```bash
python3 -m streamlit run app_multi_view.py
```

Beim allerersten Start fragt Streamlit eventuell nach einer E-Mail-Adresse → einfach mit **Enter** überspringen. Danach öffnet sich der Browser mit dem Dashboard „SMARD Lastprofil Explorer". Falls nicht, kopiere die im Terminal angezeigte Adresse (`Local URL: http://localhost:8501`) in deinen Browser.

Die beiden Einzel-Apps startest du analog:
```bash
# einfaches Lastprofil
python -m streamlit run app.py          # Windows
python3 -m streamlit run app.py         # macOS / Linux

# nur Wochenvergleich
python -m streamlit run app_weekly_overlay.py     # Windows
python3 -m streamlit run app_weekly_overlay.py    # macOS / Linux
```

### Schritt 7 – App beenden

Im Terminal **Strg + C** (Windows) bzw. **Ctrl + C** (Mac) drücken. Die virtuelle Umgebung verlässt du anschließend mit:
```bash
deactivate
```

---

## Optional: Conda statt venv

Falls du **Conda** verwendest und bereits eine passende Umgebung hast, kannst du statt der venv-Schritte (Schritt 4) diese aktivieren:

```bash
conda activate environment_it_energy
```

Danach weiter mit Schritt 5 (Abhängigkeiten installieren) und Schritt 6 (App starten). **Wenn du kein Conda nutzt, ignoriere diesen Abschnitt einfach** – der venv-Weg oben reicht vollständig.

---

## Hinweis

Wenn im Terminal **`(.venv)`** vor dem Prompt steht, bedeutet das nur, dass die virtuelle Python-Umgebung aktiviert ist. Das ist normal und gewünscht, wenn du die App aus dieser Umgebung startest.

---

**Datenquelle:** [SMARD – Strommarktdaten der Bundesnetzagentur](https://www.smard.de)
 
