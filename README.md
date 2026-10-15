# Collaborative Intrusion Detection Between Socket Nodes

Runnable, defensive academic simulation: independent IDS nodes observe deterministic synthetic events, apply transparent local rate rules, exchange HMAC-signed alerts over real TCP sockets bound to loopback, validate incoming evidence, correlate distinct reporters, update explainable trust scores, and make trust-weighted decisions. It creates no real attack traffic, scans no networks, and contacts no external hosts.

## Requirements and setup

Python 3.11 or newer. In PowerShell, from this directory:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

On Linux/macOS activate with `source .venv/bin/activate`. Required libraries: Streamlit, pandas, Plotly, pytest, pytest-asyncio, psutil, cryptography. `cryptography` is used only for generating a self-signed localhost lab certificate. No other dependencies are used.

## Run

```powershell
python -m cids.simulation --nodes 4 --seed 7 --speedup 100
python -m cids.simulation --scenario low_rate
python -m cids.simulation --experiments --scenario all
python -m cids.experiments --threshold-sweep --scenario all --nodes 4 --seeds 5 --speedup 500
streamlit run app.py --server.address 127.0.0.1
pytest -q
```

The CLI prints a JSON run summary. `--port` selects the base listener port; zero requests OS-assigned ephemeral ports. Set `tls=true` on `Settings` only after generating the lab certificate with `python scripts/gen_lab_cert.py`. Missing TLS files fail clearly during configuration validation. The threshold sweep runs the seven decision thresholds from 0.3 to 0.9 and peer source counts 1 through 3 over five seeds, writing `results/threshold_sweep.csv` and `.json`.

## Design and measurements

See [docs/EXPLAINED.md](docs/EXPLAINED.md). Scenario names cover concentrated, coordinated, low-rate distributed and benign-bait events, duplicate/delayed messages, a misleading correctly signed peer, an unavailable peer, replay, invalid signatures and malformed frames. Incidents are labeled and assigned partial visibility. `--experiments` runs five seeds by default. Locally detected attacks contribute self-evidence with configurable trust 1.0; sub-threshold suspicion reports at a normalized score of 0.5 (half of the local count threshold). Peer-only decisions require weighted support at the configured decision threshold and at least two distinct peer sources by default. This prevents a lone peer from triggering a decision without suppressing an observer's own local detection. Trust increases only after authenticated corroboration; when a target was recently observed but an authenticated report remains uncorroborated through its correlation window, trust decreases by a bounded step. Rejected/forged/replayed claims never change trust. The strict majority over all nodes is structurally poor under partial visibility: a concentrated incident may be visible to only one node, which cannot form a majority of the full network. `majority_vote_observers` compares validated reporters with the nodes that observed the target during that incident.

The dashboard lets you choose seed count and exposes duration, correlation window, local threshold, reporting threshold, decision threshold, minimum peer sources, TLS, and Stop controls. It shows ground truth and per-incident decisions, latency from each incident's own start, observer-specific trust history, topology, live alerts, transport rejections/bytes, and mean ± sample standard deviation across seeds. JSON and CSV exports include summaries, decisions, latencies, and threshold sweeps under `results/`. CPU and memory are environment-dependent, sampled during simulation, and include Streamlit overhead when launched in the dashboard. Scheduling and socket timing can cause small run-to-run differences; event generation for a fixed seed is deterministic.

The redesigned dashboard has persistent session-scoped runs across eight pages: Overview, Live Network, Incidents, Trust, Security, Evaluation, Experiments & Export, and About. Navigation does not restart a run; Stop requests graceful shutdown. Each page displays an explicit empty state until results exist. Method colors and labels are shared across charts. The About page reads these project notes directly from this README.

### Decision and trust rules

For observer *i* and incident *j*, collaborative decisions follow this rule:

$$
D_{i,j} = L_{i,j} \lor (W_{i,j} \geq \theta \land S_{i,j} \geq q)
$$

where \(L\) is local detection, \(W\) is authenticated trust-weighted peer support, \(S\) is distinct authenticated peer sources, \(\theta\) is the decision threshold, and \(q\) is minimum peer sources.

- Peer support excludes the observer's own report. Self-trust defaults to 1.0 and is configurable; peer-only quorum defaults to two distinct senders.
- Authenticated corroborated evidence raises observer-specific peer trust by a bounded step. An authenticated alert that remains uncorroborated through its correlation window lowers trust only when the observer recently observed that target.
- Invalid signatures, replays, and other unauthenticated claims affect channel rejection counters, never the unproven claimed peer's trust.

### Evaluation units and timing

- One evaluation unit is one labeled incident, including benign decoy/fault incidents.
- An attack decision is correct through the incident's end plus the configured grace period. A benign unit is positive only if a decision occurs in its scoring window.
- Confusion counts are calculated once per incident and sum to the number of evaluation units. The default scoring grace period is five simulation seconds.
- Per-incident latency is `first correct detection simulation time - that incident's start_time`. Undetected incidents and benign units have no attack latency.

### Results summary

Five-seed corrected comparison (seeds 7, 17, 27, 37, 47; default scenario `all`; four nodes; 100x simulation speed) is exported at `results/experiment_summary.csv`. In counts TP/TN/FP/FN, collaborative is 6/3/0/1; local-only any-node is 4/3/0/3; strict majority is 2/3/0/5; and majority among target observers is 6/2/1/1. The per-node-average baseline reports per-node averaged rates, so it intentionally has no aggregate confusion-count fields. Reproducible timing can vary slightly with socket scheduling.

## Scope note

The source request available to this project ends mid-sentence at “Correlation key: (target_id, event_type) within a”. That missing remainder cannot be recovered from the attachment. The implementation uses an explicit configurable 15 simulation-second correlation window and documents defaults for unspecified details. This is an academic simulation, not a production IDS.
