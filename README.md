# RemoteConnect NT

A Streamlit tool for deciding **what to check next about remote NT connectivity**. It places the NT Government's 2022 source-location list beside ACCC operator-site observations from 31 January 2026. The experimental indicator helps select questions for follow-up; it does not confirm service gaps or recommend investment.

## Run locally

Tested with **Python 3.12 on Windows**. From the repository root in VS Code's terminal:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\run_app.bat
```

If the environment already exists, skip its creation. The batch launcher runs data preparation before starting Streamlit. It works with `data/processed/` absent and stops with an error if preparation fails. To prepare without launching:

```powershell
.\run_app.bat --prepare-only
```

Direct launch also prepares missing processed files automatically:

```powershell
.\.venv\Scripts\python.exe -m streamlit run app.py
```

After editing raw sources or calculation rules, rebuild explicitly (or relaunch using the batch file):

```powershell
.\.venv\Scripts\python.exe src\prepare_data.py
```

macOS/Linux equivalent (not tested in this review):

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python src/prepare_data.py
python -m streamlit run app.py
```

The included raw files are sufficient to run the app after dependency installation. No API key or live data download is needed. Use the virtual environment's Python explicitly if VS Code selects another interpreter. Missing dependency errors are resolved by installing `requirements.txt` in that same environment. Missing source errors name the required workbook or boundary; see [raw-data instructions](data/raw/README.txt).

## Six views, one investigation

1. **Overview:** three figures, an NT map and a featured location chosen from the current filtered view.
2. **Connectivity map:** fixed-size 2022 location circles; optional 2026 operator-site crosses. A table provides the same location evidence without requiring map interaction.
3. **Community explorer:** source flags, provider distances, actual listed site bands, effective score weights and practical verification steps.
4. **Digital inclusion:** a clear missing-data state and an explanation of why a regional average cannot fill a community profile.
5. **Data insights:** coverage composition, selected provider-distance dots and baseline/current score sensitivity. Each includes a calculated takeaway.
6. **Save snapshots:** a readable text snapshot and CSVs for the selected location or filtered set.

Sidebar filters and weights persist during in-app navigation. Explorer and snapshots use the filtered records; an empty selection stays empty. Infrastructure overlays and the labelled full-NT context table are independent of the location filters. Saved CSV/text snapshots can be read later without the app. **The interactive app needs a running Streamlit server**; device caching and synchronisation are not implemented. Maps draw locally without external tiles or topographic downloads.

## Included evidence and findings

The supplied files produce 188 source-location records and 419 NT operator-site records. These reduce to 405 distinct RFNSA/rounded-coordinate keys; that is not a verified physical-tower count.

- 98 locations have a positive proximity-to-cell flag; 96 of these are proximity-only.
- Seven locations have multiple YES flags. Profiles and exports preserve every original flag.
- No ADII or ABS observations are supplied. Their CSVs are blank templates, not evidence.
- ACCC TPG distances use its own listed sites. The separately published Optus–TPG shared-network file is excluded, so provider proximity does not measure retail choice.

The NT source lists **covered locations**, including communities, villages, tourism and highway sites. It is not a complete inventory of remote communities or unserved places. Nearby sites and listed bands do not prove local signal, reliability, capacity or affordability. The 2022 and 2026 files measure different things and must not be turned into a time series.

## Explainable indicator

Configured defaults are 40 coverage / 25 distance / 15 provider diversity / 20 context. With no context observations, actual default shares are **50%, 31.25%, 18.75%, 0%**. The context slider is disabled; missing components are omitted and the remaining positive weights are renormalised per record. Setting every usable weight to zero leaves records unscored.

For multiple coverage flags, the score explicitly uses the least limiting listed type (macro, then small, then proximity). This is a design assumption, not a measured quality judgement. The Insights sensitivity chart compares default and current weights on the same selected records. Read [METHODOLOGY.md](METHODOLOGY.md) for formulas, thresholds, exact deduplication and geography safeguards.

## Verification

```powershell
.\.venv\Scripts\python.exe src\prepare_data.py
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe scripts\check_first_launch.py
```

Optional browser checks require installed Chrome and the development dependencies:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
# Keep the app running at http://127.0.0.1:8501 in another terminal.
.\.venv\Scripts\python.exe scripts\browser_review.py --phase after
.\.venv\Scripts\python.exe scripts\browser_interactions.py
```

The first browser script captures all six pages at 1440×1000 and 390×844, including lower-page screenshots. The second checks real navigation, filters, score controls, map overlay, selection, downloads and mobile controls. The Windows first-launch script temporarily backs up only generated files under `.tmp/` and checks both batch and direct launch rebuilding. Screenshots and machine-readable results are in `artifacts/`. Browser checks are separate from Streamlit AppTest; a passing AppTest is not a visual review. [CHECKPOINT.md](CHECKPOINT.md) records the latest verification and any unfinished work.

## Files

| Path | Purpose |
|---|---|
| `app.py`, `.streamlit/config.toml` | Navigation, persistent controls, theme configuration |
| `pages/` | Six views |
| `assets/` | CSS and favicon |
| `src/dashboard.py` | Shared UI, filters, charts and local map |
| `src/prepare_data.py`, `src/priority.py` | Preparation, distances and explainable scoring |
| `src/exports.py` | Source-labelled CSV/text snapshot generation |
| `data/raw/` | Publisher files, optional empty templates and instructions |
| `data/processed/` | Generated files, excluded from Git |
| `tests/`, `scripts/` | Calculation, AppTest and real browser checks |
| `DATA_SOURCES.md`, `data_sources.csv` | Publisher links, licences, observation/access dates |

Raw files were accessed on 28 September 2026; publisher metadata was checked on 29 September. See [DATA_SOURCES.md](DATA_SOURCES.md) for links and verification limits. The project addresses the [CDU challenge's remote-connectivity theme](https://itcodefair.cdu.edu.au/data-innovation-challenge/). No community consultation or current field measurements are claimed.
