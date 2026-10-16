from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from pathlib import Path

out=Path('docs/CIDS_Project_Page_Guide.docx')
out.parent.mkdir(parents=True,exist_ok=True)
doc=Document()
sec=doc.sections[0]
sec.top_margin=Inches(.68); sec.bottom_margin=Inches(.68); sec.left_margin=Inches(.78); sec.right_margin=Inches(.78)
styles=doc.styles
styles['Normal'].font.name='Aptos'; styles['Normal'].font.size=Pt(10); styles['Normal'].font.color.rgb=RGBColor(34,48,68)
styles['Normal'].paragraph_format.space_after=Pt(6)
for n,size,color in [('Title',28,'101828'),('Heading 1',19,'101828'),('Heading 2',14,'2563EB'),('Heading 3',11,'344054')]:
 s=styles[n]; s.font.name='Aptos Display'; s.font.size=Pt(size); s.font.bold=True; s.font.color.rgb=RGBColor.from_string(color)

# Header/footer
header=sec.header.paragraphs[0]; header.text='CIDS CONSOLE  /  PROJECT GUIDE'; header.style='Caption'; header.runs[0].font.color.rgb=RGBColor(102,112,133); header.runs[0].font.bold=True
footer=sec.footer.paragraphs[0]; footer.alignment=WD_ALIGN_PARAGRAPH.RIGHT
r=footer.add_run('Page-by-page reference  •  '); r.font.size=Pt(8); r.font.color.rgb=RGBColor(102,112,133)
fld=OxmlElement('w:fldSimple'); fld.set(qn('w:instr'),'PAGE'); footer._p.append(fld)

def shade(cell,fill):
 tcPr=cell._tc.get_or_add_tcPr(); shd=OxmlElement('w:shd'); shd.set(qn('w:fill'),fill); tcPr.append(shd)
def set_cell(cell,text,bold=False,color=None,size=9):
 cell.text=''; p=cell.paragraphs[0]; p.paragraph_format.space_after=Pt(0); r=p.add_run(str(text)); r.bold=bold; r.font.name='Aptos'; r.font.size=Pt(size)
 if color:r.font.color.rgb=RGBColor.from_string(color)
 cell.vertical_alignment=WD_CELL_VERTICAL_ALIGNMENT.CENTER
def table(headers,rows,widths=None):
 t=doc.add_table(rows=1, cols=len(headers)); t.alignment=WD_TABLE_ALIGNMENT.CENTER; t.style='Table Grid'
 for i,h in enumerate(headers):set_cell(t.rows[0].cells[i],h,True,'FFFFFF',9); shade(t.rows[0].cells[i],'2563EB')
 for ri,row in enumerate(rows):
  cells=t.add_row().cells
  for i,v in enumerate(row):set_cell(cells[i],v,False,None,8.5); shade(cells[i],'F7F8FA' if ri%2==0 else 'FFFFFF')
 if widths:
  for row in t.rows:
   for i,w in enumerate(widths):row.cells[i].width=Inches(w)
 doc.add_paragraph().paragraph_format.space_after=Pt(1)
 return t
def para(text,style=None): doc.add_paragraph(text,style)
def bullets(items):
 for x in items: doc.add_paragraph(x,style='List Bullet')
def code(text):
 p=doc.add_paragraph(); p.paragraph_format.left_indent=Inches(.18); p.paragraph_format.space_before=Pt(3); p.paragraph_format.space_after=Pt(8)
 r=p.add_run(text); r.font.name='Cascadia Code'; r.font.size=Pt(9); r.font.color.rgb=RGBColor(71,84,103)
def page(title,sub,sections):
 doc.add_heading(title,1); p=doc.add_paragraph(sub); p.runs[0].italic=True; p.runs[0].font.color.rgb=RGBColor(102,112,133)
 for head,body in sections:
  doc.add_heading(head,2)
  if isinstance(body,list):bullets(body)
  else:para(body)

# Cover
p=doc.add_paragraph(); p.paragraph_format.space_before=Pt(60)
r=p.add_run('CIDS Console'); r.bold=True; r.font.name='Aptos Display'; r.font.size=Pt(32); r.font.color.rgb=RGBColor(16,24,40)
p=doc.add_paragraph(); r=p.add_run('Page by page project guide'); r.font.size=Pt(21); r.font.color.rgb=RGBColor(37,99,235)
para('A practical walkthrough of the dashboard, its controls, the results it displays, and the Python code that produces them.')
para('Project: Collaborative Intrusion Detection Between Socket Nodes')
para('Dashboard URL when running locally: http://127.0.0.1:8507')
doc.add_heading('What this guide covers',2)
bullets(['All eight dashboard pages and what each section means.','Sidebar controls and the reference configuration.','Code map with file paths, line locations, functions, and the data flow between them.','How to run the dashboard and read exported results.'])
doc.add_heading('About the screenshots',2)
para('This guide describes each live dashboard page. The browser capture in this workspace is available only as an inline preview and does not expose an image file to the document builder, so screenshots could not be embedded into this Word file. To add them, open the local dashboard, visit each page listed below, and use Windows Snipping Tool (Win + Shift + S) to capture the page; the page descriptions identify the relevant view.')
para('The guide avoids presenting mockups as screenshots. The page layouts described here were checked against the running dashboard; results vary slightly between simulation runs because socket scheduling is real-time.')
doc.add_page_break()

doc.add_heading('1. Start the project',1)
para('Open PowerShell in the project folder, activate the virtual environment, install dependencies, and launch the dashboard. The first page opens at Overview. Use the left navigation list to move between sections; the current run remains available while changing pages.')
code('python -m venv .venv\n.venv\\Scripts\\Activate.ps1\npython -m pip install -r requirements.txt\nstreamlit run app.py --server.address 127.0.0.1 --server.port 8507')
para('For the default reference scenario, keep Scenario = all and the default 4-node / seed-7 settings, then select Run simulation. The status pill changes from Idle to Running and then Finished. A multi-seed comparison is launched with Multi-seed; Stop requests a graceful stop.')
doc.add_heading('2. Sidebar controls',1)
table(['Control group','Control','What it changes'],[
('Network','Nodes (2–10)','Number of isolated simulated IDS peers.'),('Network','TLS','Whether local peer sockets use the configured lab TLS certificate.'),('Network','Simulation speed','Simulation-time scale relative to wall time.'),('Detection','Local threshold','Per-node event count needed for a full alert.'),('Detection','Reporting threshold','Normalized local score needed before suspicion is shared.'),('Detection','Correlation window','How long evidence can be combined for one target/event type.'),('Detection','Decision threshold','Minimum weighted peer support for peer-only decisions.'),('Detection','Minimum peer sources','Distinct validated peer senders required for a peer-only decision.'),('Run','Scenario / Duration','Synthetic workload and requested duration; schedule can extend short runs.'),('Run','Seed / Number of seeds','Reproducible seed and number of experiment runs.'),('Run','Reset / Run / Multi-seed / Stop','Restore reference settings, run once, run repeated seeds, or request stop.')])
para('The reference config is stored in configs/reference.json. It uses 4 nodes, scenario all, seed 7, five experiment seeds by default, 240 seconds, and the documented threshold values. Reset to reference restores these values.')
doc.add_page_break()

page('3. Overview','Screenshot target: Overview, after a completed single simulation.',[
('Purpose','This page gives a compact summary of the current single run: incident outcomes, collaboration and baseline metrics, message delivery, and comparison charts.'),
('Incident outcomes','Rows compare collaborative, local-only any-node, local-only per-node-average, majority across all nodes, and majority across observers. Attacks detected is TP / attack incidents; false alarms is FP / benign incidents. The per-node-average method shows a dash for aggregate counts because it averages node rates.'),
('Summary cards','Collaborative F1 and false-positive rate summarize detection quality. Alerts sent / validated separates transmissions from accepted messages. Rejected messages and frames counts transport/security validation failures.'),
('Baseline comparison','The grouped comparison chart shows precision, recall, F1, and false-positive rate using fixed method colors. Read the short summary below it as a comparison of this run only; use Experiments for multi-seed averages.'),
('Code path','ui/pages/overview.py, lines 1–31, builds the table and metrics. ui/charts.py, lines 44–71, prepares metric series and summary text. cids/evaluation.py, lines 9–69, produces incident-level decisions and scores.')])
page('4. Live Network','Screenshot target: Live Network, after a completed single simulation.',[
('Peer topology','The time slider moves through simulation seconds. Node color and edge style indicate availability and the fault state; start times are listed beneath the slider. The initial slider position targets the first relevant fault.'),
('Node activity','The chart compares events and alerts per node. Event counts describe generated events delivered to a node; alert counts show local alert production.'),
('Live alert feed','During a run this feed refreshes every second. Filters narrow messages by node, target, event type, or kind. After completion, it shows the recorded feed; rows include simulation time and message identity fields.'),
('Code path','ui/pages/live_network.py, lines 1–51, builds the topology, activity, and fragment feed. ui/charts.py, lines 22–27, selects the initial timeline position; lines 73 onward construct topology data. ui/context.py, lines 6–39, shares controller and run state.')])
page('5. Incidents','Screenshot target: Incidents, after a completed single simulation.',[
('Ground truth and method decisions','Every evaluation unit appears, including benign decoys. Attack/Benign is the label; each method shows Detected or Missed. Cell tint marks whether that method was correct for that incident.'),
('Evidence columns','Weighted support, distinct sources, supporting node IDs, and local detection nodes explain the evidence. The per-node-average column is a share, not an aggregate incident decision.'),
('Incident details','Choose an incident to see its attack/benign label, start/end window, grace period, decision path, support, quorum, and evidence explanation. Latency is measured from that incident’s own start time.'),
('Code path','ui/pages/incidents.py, lines 8–55, builds the ground-truth decision table and detail panel. cids/evaluation.py, lines 9 onward, centralizes incident evaluation. ui/components.py, lines 32 onward, applies readable table formatting.')])
page('6. Trust','Screenshot target: Trust, after a completed single simulation.',[
('Trust history','Each observer has an independent history for each peer. Lines start at the initial trust value at time zero and step at update times. The observer selector filters the displayed history.'),
('Update reasons','Positive authenticated corroboration raises the score in bounded steps. Authenticated claims that remain unsupported can lower it when the observer saw the target. Invalid signatures and replayed claims affect channel rejection statistics, not trust assigned to a claimed identity.'),
('Trust matrix','The heatmap summarizes final observer-to-peer trust. The diagonal is self and is marked separately; red/neutral/green indicates low/initial/high trust.'),
('Code path','ui/pages/trust.py, lines 1 onward, selects observer histories and renders the history and matrix. ui/charts.py, lines 11–20, inserts the initial value and step points. cids/trust_manager.py contains trust update rules; cids/models.py defines trust state.')])
page('7. Security','Screenshot target: Security, after a completed single simulation.',[
('Security rejection chart','Counts authentication, freshness, replay, malformed, and frame-size failures. Categories are grouped so an alert rejection can be distinguished from a malformed transport frame.'),
('Delivery and bytes','The page compares transmitted and validated alerts and reports bytes sent/received and message size. A sent message can be rejected after arrival; transport failures and validation rejections are separate explanations.'),
('Security interpretation','A replay or invalid signature is not evidence that the claimed peer sent the payload. Attribution stays with the receiving connection/channel until identity is authenticated.'),
('Code path','ui/pages/security.py contains the security breakdown and transport measurements. cids/message_security.py handles canonical encoding and signatures. cids/socket_transport.py handles message delivery; validation and rejection counters are assembled by cids/simulation.py.')])
page('8. Evaluation','Screenshot target: Evaluation, after a completed single simulation.',[
('Classification metrics','Per-method precision, recall, F1, accuracy, and false-positive rate are calculated over incident units. The page keeps attack and benign counts distinct.'),
('Latency table','Each attack incident has its own latency: first correct detection simulation time minus that incident’s start. Undetected attacks and benign incidents do not receive an attack latency value.'),
('Operational metrics','Events, alert counts, byte totals, average message size, CPU, and memory describe the simulation run. CPU and memory are environment-dependent; dashboard measurements include Streamlit overhead.'),
('Code path','ui/pages/evaluation.py renders score, latency, and operational sections. cids/metrics.py, lines 2–5, defines classification and operational metrics. cids/evaluation.py defines scoring windows and per-incident latency.')])
page('9. Experiments and Export','Screenshot target: Experiments & Export, after a single or multi-seed run.',[
('Run controls','The page can launch a single scenario, a multi-seed comparison, or a threshold sweep. Multi-seed reports mean and sample standard deviation; individual seed rows remain downloadable.'),
('Results tables','Single-run results show per-incident decisions. Multi-seed results show each method/metric summary. Threshold sweeps are separate so parameter-selection results are not confused with reference comparisons.'),
('Exports','Download controls produce decision CSV, per-incident latency CSV, experiment summary CSV, per-seed CSV, threshold sweep CSV, and complete JSON for the latest run.'),
('Code path','ui/pages/experiments.py builds the experiment actions and export buttons. cids/experiments.py, lines 9–72, summarizes runs; lines 73 onward implements CLI execution. cids/simulation.py contains the underlying single-run simulation.')])
page('10. About','Screenshot target: About.',[
('Decision and trust rules','The page explains the collaborative decision rule and trust semantics in readable text and math. Local detection can decide directly; otherwise peer support must meet the weighted threshold and distinct-source quorum.'),
('Evaluation and limitations','Ground truth uses one row per labeled incident, including benign decoys. Attack scoring includes the configured grace period. The lab uses synthetic events and loopback-only sockets; it is not a production IDS.'),
('Reference settings','A settings table shows the configuration currently used as the reproducible baseline, plus threshold provenance.'),
('Code path','ui/pages/about.py, lines 1 onward, reads the relevant README sections and reference JSON. README.md contains the project design and limitations. configs/reference.json contains the defaults.')])

doc.add_page_break()
doc.add_heading('11. Source map by execution flow',1)
para('The UI and simulation are separated. Streamlit pages read one controller result; the simulation produces events, messages, trust histories, incidents, and metrics; export views serialize those same records.')
table(['Order','File and line focus','Role'],[
('1. App startup','app.py: 1–22','Defines eight pages, installs shared styles/charts, renders the sidebar, and dispatches navigation.'),
('2. Shared controls','ui/sidebar.py: 12 onward','Loads reference defaults, renders controls, validates settings, starts/stops single and multi-seed runs.'),
('3. Page state','ui/context.py: 6–41','Returns current controller/result to pages and formats numbers.'),
('4. Workload','cids/event_generator.py: 21–110','Creates seeded events and fixed incident windows with scenario-specific node visibility.'),
('5. Simulation','cids/simulation.py: main run function and CLI','Runs peer nodes and sockets, tracks fault injections, gathers alerts, and produces the run record.'),
('6. Peer transport','cids/node.py and cids/socket_transport.py','Processes local events and transmits alerts to peers; delivery is concurrent.'),
('7. Authentication','cids/message_security.py: 6–8; cids/socket_transport.py','Signs and validates messages and records replay/freshness/signature failures.'),
('8. Trust and consensus','cids/trust_manager.py; cids/consensus_engine.py','Maintains observer-specific trust and computes support/source quorum.'),
('9. Baselines/evaluation','cids/baselines.py: 4–39; cids/evaluation.py: 6 onward','Counts full-alert votes, defines observer set, and evaluates each labeled incident.'),
('10. Metrics/experiments','cids/metrics.py: 2–5; cids/experiments.py: 9 onward','Calculates classification/operational metrics and multi-seed summaries.'),
('11. Rendering/exports','ui/charts.py; ui/components.py; ui/pages/*.py','Converts results into charts, readable tables, and downloads.')])
para('Line numbers can shift as the project changes. Search by the function names listed in the source map when reading a newer checkout. Use `rg -n "def |page_start|st.navigation" app.py ui cids` from the project root to re-find them.')

doc.add_heading('12. Reading the main outputs',1)
table(['Output','What it contains','When to use it'],[
('experiment_summary.csv','Method × metric mean and standard deviation across seeds.','Compare methods across repeated runs.'),('experiment.csv','Raw method metrics for each individual seed.','Inspect variation and reproduce reported averages.'),('incident_decisions.csv','Truth label, decisions, support, sources, and explanation per incident.','Explain why one incident was detected or missed.'),('incident_latency.csv','Per-incident first-correct-detection latency from incident start.','Check detection delay without mixing unrelated incident windows.'),('cids_results.json','Complete structured result for one run.','Inspect detailed event, trust, delivery, and evaluation data.'),('threshold_sweep.csv/json','Metrics by tested thresholds and peer-source settings.','Examine the predeclared parameter grid; keep distinct from reference results.')])
para('Do not compare a single-run value with a five-seed mean as though they were the same statistic. The “any node” local baseline is a network-level incident decision. The per-node-average baseline is a macro average of local node rates, so it does not have a meaningful aggregate TP/TN/FP/FN count.')

doc.add_heading('13. Reference results snapshot',1)
para('The latest 5-seed reference comparison is stored in results/reference-comparison.csv. Collaborative F1 was 0.891 ± 0.053 at 4 nodes, 0.667 ± 0.149 at 6 nodes, and 0.527 ± 0.185 at 8 nodes. At 6 nodes the collaborative false-positive rate was 0.067 ± 0.149 and recall was 0.543 ± 0.256. Use the CSV as the precise source for all method-level values; run-to-run socket scheduling can change single-run details.')

doc.add_heading('Appendix A. Screenshot capture checklist',1)
para('For a visual appendix, capture one full browser viewport per page with the sidebar visible and a finished reference run. Use the page list below to keep screenshots in navigation order.')
bullets(['01 Overview — incident outcomes and baseline comparison.','02 Live Network — topology, node activity, and alert feed.','03 Incidents — ground truth, method decisions, and incident detail.','04 Trust — observer history and trust matrix.','05 Security — rejection reasons and traffic measurements.','06 Evaluation — metrics, per-incident latency, and runtime resources.','07 Experiments & Export — multi-seed summaries and export controls.','08 About — rules, reference configuration, and limitations.'])
para('Recommended procedure: press Win + Shift + S, select the browser window area, save each capture under docs/screenshots using the matching numbered name, then insert each image beneath its page heading. Keep one page screenshot per image so text remains readable.')

# Core properties
doc.core_properties.title='CIDS Console Page by Page Project Guide'
doc.core_properties.subject='Dashboard walkthrough, controls, source map, and result interpretation'
doc.core_properties.author='CIDS Project'
doc.save(out)
print(out.resolve())
print('paragraphs',len(doc.paragraphs),'tables',len(doc.tables))
