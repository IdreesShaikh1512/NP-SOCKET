from pathlib import Path

import streamlit as st

from ui.components import card
from ui.context import page_start

page_start("About", "Decision rules, scoring units, and simulation boundaries")
text=(Path(__file__).resolve().parents[2]/"README.md").read_text(encoding="utf-8")
sections={}; current=None
for line in text.splitlines():
    if line.startswith("#"):
        title=line.lstrip("# ")
        current=title if title in {"Decision and trust rules","Evaluation units and timing","Design and measurements","Scope note"} else None
        if current: sections[current]=[]
    elif current is not None:
        sections[current].append(line)

for title in ("Decision and trust rules","Evaluation units and timing","Scope note"):
    body=sections.get(title,[])
    if not body: continue
    with card(title):
        chunks=[]; text_lines=[]; formula=[]; in_formula=False
        for line in body:
            if line.strip()=="$$":
                in_formula=not in_formula
                if in_formula and text_lines:
                    chunks.append(("text","\n".join(text_lines))); text_lines=[]
                elif not in_formula and formula:
                    chunks.append(("math"," ".join(formula))); formula=[]
                continue
            if in_formula: formula.append(line.strip()); continue
            if line.strip(): text_lines.append(line)
        if text_lines: chunks.append(("text","\n".join(text_lines)))
        for kind,value in chunks:
            st.latex(value) if kind=="math" else st.markdown(value)
