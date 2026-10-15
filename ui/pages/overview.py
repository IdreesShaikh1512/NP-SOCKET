import pandas as pd
import streamlit as st
from ui.context import page_start,number
from ui.charts import METHOD_LABELS,comparison_chart,summary_sentence
from ui.components import card

state,result=page_start("Overview","CIDS multi-observer intrusion-detection simulation")
if result is not None:
    scores=result["classification"]; rows=result["decision_table"]; methods=[(key,METHOD_LABELS[key]) for key in METHOD_LABELS]
    cards=st.columns(5)
    for col,(method,label) in zip(cards,methods):
        if method=="local_only_per_node_average":
            value=sum(row[method] for row in rows)*len(result["nodes"])
            label="Per-node detections"
        else: value=sum(bool(row.get(method,False)) for row in rows)
        suffix=f" / {len(rows)}" if method!="local_only_per_node_average" else " total"
        help_text="Mean local detections accumulated across nodes and evaluation incidents." if method=="local_only_per_node_average" else "Incident decisions for this method; denominator is all labeled evaluation incidents."
        col.metric(label,f"{number(value,1)}{suffix}",help=help_text)
    summary=st.columns(4)
    summary[0].metric("Collaborative F1",number(scores["collaborative"]["f1"]),help="Harmonic mean of collaborative precision and recall over incident units.")
    summary[1].metric("Collaborative FPR",f"{scores['collaborative']['false_positive_rate']:.1%}",help="False positive rate among benign evaluation incidents.")
    summary[2].metric("Alerts sent / validated",f"{result['alert_delivery']['alerts_transmitted']:,} / {result['alert_delivery']['validated_alerts_received']:,}",help="Alerts transmitted and authenticated/accepted by receiving nodes.")
    summary[3].metric("Total rejections",f"{sum(result.get('rejection_counts',{}).values()):,}",help="Rejected messages and malformed frames by reason.")
    with card("Baseline comparison"):
        st.plotly_chart(comparison_chart(result,("f1",),"F1 by evaluation method"),width="stretch")
        st.write(summary_sentence(result))
