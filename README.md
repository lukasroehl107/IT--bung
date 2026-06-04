# IT--bung

## Beschreibung
Dieses Projekt enthält zwei Streamlit-Apps zur Anzeige von Lastprofilen aus SMARD.

## Voraussetzungen
- Python 3.10 oder neuer
- Streamlit und weitere Bibliotheken installiert
- Terminal in `C:\Github\IT--bung`

## Empfohlene Befehle

1. Projektordner öffnen

```powershell
cd C:\Github\IT--bung
```

2. Kompletter Setup-Block (kopieren und einfügen)

```powershell
cd C:\Github\IT--bung
python -m venv .venv
& .\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install streamlit pandas plotly requests
python -m streamlit run app_multi_view.py
```

3. Falls du die Umgebung manuell nutzen möchtest:

Falls du eine Conda-Umgebung nutzt:

```powershell
conda activate environment_it_energy
```

Alternativ, falls du eine virtuelle Umgebung (`venv`) im Projektordner verwendest:

```powershell
.\.venv\Scripts\Activate.ps1
```

4. Abhängigkeiten installieren

```powershell
python -m pip install --upgrade pip
python -m pip install streamlit pandas plotly requests
```

Alternativ kannst du die Module einzeln installieren:

```powershell
python -m pip install streamlit
python -m pip install pandas
python -m pip install plotly
python -m pip install requests
```

4. App starten

Für die erste App:

```powershell
python -m streamlit run app.py
```

Für die Wochenvergleichs-App:

```powershell
python -m streamlit run app_weekly_overlay.py
```

## Hinweis
Wenn im Terminal `venv` vor dem Prompt steht, bedeutet das nur, dass eine virtuelle Python-Umgebung aktiviert ist. Das ist normal und gewünscht, wenn du die App aus dieser Umgebung startest.

