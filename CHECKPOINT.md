# RemoteConnect NT checkpoint — 30 September 2026

## Scope and status

Dashboard and code-documentation improvements are complete and verified. No academic report, slides, presentation or submission ZIP was created. All changes are in the local repository; nothing was committed or pushed. User asked for this checkpoint to make interruption/resumption safe.

The first session stopped when automatic approval review hit the usage limit during a Chrome launch. Work resumed on 30 September; that block is resolved.

## Implemented

- Six-page visual system: warm neutral background, dark teal text, ochre accents, stronger caption contrast, compact headers, consistent charts/cards, responsive layout and current-page navigation.
- Overview: three figures, one local NT map, a featured location and a direct profile action. Map circles are fixed-size 2022 source locations; optional crosses are 2026 operator-site records.
- Explorer: respects filters; selected record carries between pages; source flags, provider distances, actual site band lists, effective weights and verification questions.
- Digital Inclusion: explicit missing-data state, geography explanation and ADII attribution; no developer import instructions in the main experience.
- Insights: 100% source-category composition, selected provider-distance dots, baseline/current score sensitivity; full NT infrastructure counts clearly separated.
- Downloads: CSV and readable text snapshots, including source URLs, dates, licences, original flags and effective weights. They are not an offline interactive client.
- Original coverage flags preserved for all seven named cases. Combined labels and an explicit least-limiting score basis. 98 any-proximity records, 96 proximity-only, 7 multiple-flag records.
- Context slider disabled with no usable observations. Default effective weights: 50% coverage, 31.25% distance, 18.75% diversity, 0% context.
- Shared RFNSA + five-decimal coordinate key: 419 operator records and 405 mapped-site keys. Replaces inconsistent 408 unrounded keys in old summary. Neither count is asserted to be verified physical towers.
- Batch launcher rebuilds processed data; direct app launch prepares missing outputs. Tested top-level dependency versions pinned. README, METHODOLOGY, DATA_SOURCES and CSV register updated.

## Verification

Commands use `.venv\Scripts\python.exe` (Python 3.12 on Windows):

| Command | Result |
|---|---|
| `src/prepare_data.py` | 188 locations, 419 operator records, 405 mapped-site keys, 0 ADII matches |
| `-m unittest discover -s tests -v` | 19 tests passed, including seven multiple-flag cases, missing/zero weights, filters, export metadata, map structure and page rendering |
| `scripts/check_first_launch.py` | Batch `--prepare-only` and direct AppTest launch each rebuilt all three absent processed files; generated-file backups under ignored `.tmp/` |
| `scripts/browser_review.py --phase after` | Final fresh-server run passed all 12 page/width combinations, with no application/browser exceptions or horizontal overflow. Includes top/bottom and profile/insights middle screenshots |
| `scripts/browser_interactions.py` | Passed on freshly restarted server: featured action, multi-flag filtering, selection persistence, actual downloads parsed, site overlay, score controls, disabled context, empty states, ADII state and 390px touch navigation |
| `-m pip check` | No broken requirements |
| `git -c core.safecrlf=false diff --check` | Passed |

Real Chrome screenshots were visually inspected before and after the redesign, including desktop, narrow and lower-page views. Streamlit AppTest alone is not treated as visual evidence. The interaction run recorded no external network requests. AppTest switched pages execute directly in this installed version; true navigation persistence was verified in Chrome.

Browser artifacts: `artifacts/before/`, `artifacts/after/`, `artifacts/interactions/`. Interaction screenshots include site overlay, changed-weight sensitivity and a Mutitjulu phone-width profile. Raw source files remain unchanged.

## Sources verified and limitations

- NT catalogue: 2022 workbook, last updated 4 July 2022, CC BY. No per-record observation dates.
- ACCC catalogue API: all three registered CSV URLs, modification timestamps and CC BY 2.5 AU licence verified 29 September. ACCC report confirms 31 January 2026 observations; publication page dated 22 September. Raw file access date remains 28 September.
- Separate Optus–TPG MOCN data are excluded. TPG distance/diversity are own-infrastructure measures, not retail service choice. Cross-border sites are also excluded.
- ADII: 2022/2024 observation options, 2025 report citation, CC BY-NC-SA 4.0. No matched ADII or ABS observations supplied.
- Natural Earth public-domain terms verified. Approximate admin boundary is not a legal survey.
- Normal ACCC catalogue pages returned HTTP 403 to the web reader; the public API worked. Local CSV contents were inspected but not hash-compared to redownloads. Interpretation guide v6 was identified via metadata; its PDF contents were not fetched.
- No current field service measurements, coverage validation or community consultation. No macOS/Linux, other browser or physical-phone test was performed; narrow Chrome viewport/touch emulation was used.

## Resume if needed

No required implementation or verification work remains. Final screenshots and machine-readable results are saved. Review this file and the working-tree diff before starting any new request; no further feature work is planned for this task.

App currently runs at http://127.0.0.1:8501 (server session 3371, may not survive interruption). Restart with `.venv\Scripts\python.exe -m streamlit run app.py --server.headless true --server.address 127.0.0.1 --server.port 8501`. Restart after shared Python module edits if the development watcher retains an old module.
