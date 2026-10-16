import pandas as pd
import plotly.express as px
import streamlit as st

from ui.charts import METHOD_COLORS, METHOD_LABELS, DISPLAY, comparison_chart, metric_frame
from ui.components import card, dataframe, method_color_table
from ui.context import controller, number, page_start

state,result=page_start("Evaluation","Incident-level scoring, seeded comparisons, latency, and communication")
tabs=st.tabs(["Single run","Multi-seed (mean ± std)","Threshold sweep","Latency","Communication overhead"])
with tabs[0]:
    if result is not None:
        with card("Single-run metrics"):
            frame=metric_frame(result)
            dataframe(frame.style.format(lambda v:number(v) if isinstance(v,(float,int)) else v),height=300)
            st.plotly_chart(comparison_chart(result,("precision","recall","f1","false_positive_rate"),"Classification metrics"),width="stretch")
            macro_std=result.get("classification_std",{}).get("local_only_per_node_average")
            if macro_std:
                st.caption("Local-only per-node metrics are averaged across nodes; across-node standard deviations: "+" · ".join(f"{k.replace('_',' ')} {number(v)}" for k,v in macro_std.items()))
    else: st.caption("Run a simulation to populate single-run metrics.")
with tabs[1]:
    full=state.result if state.result_kind=="multi_seed" else None
    if full and full.get("summary"):
        with card("Across-seed summary"):
            st.caption(f"{full['count']} seeded runs · mean ± sample standard deviation")
            frame=pd.DataFrame(full["summary"]); shown=frame.copy(); shown["method"]=shown.method.map(METHOD_LABELS); shown["metric"]=shown.metric.map(DISPLAY)
            shown=shown.rename(columns={"method":"Method","metric":"Metric","mean":"Mean","std":"Standard deviation","mean_plus_minus_std":"Mean ± standard deviation"})
            dataframe(method_color_table(shown,column="Method").format({"Mean":"{:.3f}","Standard deviation":"{:.3f}"}),height=380)
            score=frame[frame.metric.isin(["f1","false_positive_rate","recall","precision"])].copy()
            score["method_label"]=score.method.map(METHOD_LABELS)
            color_map={METHOD_LABELS[k]:v for k,v in METHOD_COLORS.items()}
            score["metric_label"]=score.metric.map(DISPLAY)
            fig=px.bar(score,x="mean",y="metric_label",color="method_label",error_x="std",orientation="h",text_auto=".3f",color_discrete_map=color_map,template="cids_light",barmode="group")
            fig.update_layout(title=None,height=360,xaxis_title="Mean score",yaxis_title="",legend_title_text="",margin={"l":18,"r":50,"t":15,"b":55}); fig.update_traces(textposition="outside",cliponaxis=False)
            st.plotly_chart(fig,width="stretch")
    else: st.caption("Run a multi-seed experiment from the sidebar to populate this tab.")
with tabs[2]:
    sweep=state.result if state.result_kind=="threshold_sweep" else None
    if sweep and sweep.get("rows"):
        data=pd.DataFrame(sweep["rows"])
        with card("Decision threshold × peer source quorum"):
            names={"decision_threshold":"Decision threshold","min_peer_sources":"Minimum peer sources","seed_count":"Seed count","collaborative_f1_mean":"Collaborative F1 mean","collaborative_f1_std":"Collaborative F1 standard deviation","collaborative_fpr_mean":"Collaborative FPR mean","collaborative_fpr_std":"Collaborative FPR standard deviation","misleading_peer_weighted_support_mean":"Misleading peer weighted support mean"}
            data=data.rename(columns=names)
            dataframe(data.style.format({c:"{:.3f}" for c in data.select_dtypes("number").columns}),height=380)
            palette=["#2563EB","#64748B","#94A3B8"]
            fig=px.line(data,x="Decision threshold",y="Collaborative F1 mean",color="Minimum peer sources",markers=True,error_y="Collaborative F1 standard deviation",template="cids_light",color_discrete_sequence=palette)
            st.plotly_chart(fig,width="stretch")
            fpr=px.line(data,x="Decision threshold",y="Collaborative FPR mean",color="Minimum peer sources",markers=True,error_y="Collaborative FPR standard deviation",template="cids_light",color_discrete_sequence=palette)
            st.plotly_chart(fpr,width="stretch")
    else: st.caption("Run the threshold sweep from Experiments & Export to populate this tab.")
with tabs[3]:
    if result is not None:
        latency=pd.DataFrame(result.get("latency_table",[]))
        if not latency.empty:
            latency["is_attack"]=latency["is_attack"].map({True:"Attack",False:"Benign"})
            latency["detected_within_grace"]=latency["detected_within_grace"].map({True:"Detected",False:"Missed"})
            latency=latency.rename(columns={"incident_id":"Incident ID","is_attack":"Ground truth","start_time":"Incident start (s)","end_time":"Incident end (s)","grace_period_seconds":"Scoring grace (s)","first_correct_detection_time":"First correct detection (s)","latency_seconds":"Detection latency (s)","detected_within_grace":"Attack decision"})
            with card("Per-incident latency"):
                st.caption("First correct detection time minus that incident's own start time; grace period is shown per row.")
                numeric=[c for c in ("Incident start (s)","Incident end (s)","Scoring grace (s)","First correct detection (s)","Detection latency (s)") if c in latency]
                dataframe(latency.style.format({c:"{:.3f}" for c in numeric}),height=380)
                values=latency["Detection latency (s)"].dropna()
                if not values.empty: st.metric("Mean collaborative latency",f"{number(values.mean())} s",help="Mean latency across detected attack incidents, relative to each incident's own start.")
    else: st.caption("Run a simulation to populate incident latency.")
with tabs[4]:
    if result is not None:
        ops=result["operational"]
        with card("Communication and process measurements"):
            c=st.columns(4)
            c[0].metric("Bytes sent",f"{ops['bytes_sent']:,}",help="Total message payload bytes sent during the simulation.")
            c[1].metric("Bytes received",f"{ops['bytes_received']:,}",help="Total message payload bytes received during the simulation.")
            c[2].metric("Average message size",f"{number(ops['average_message_size_bytes'])} bytes",help="Mean size of transmitted messages in bytes.")
            c[3].metric("Messages sent / received",f"{ops['alerts_sent']:,} / {ops['alerts_received']:,}",help="Alert transmissions and validated alert receipts.")
            c=st.columns(3)
            c[0].metric("Mean memory",f"{ops['memory_bytes']/1024/1024:,.2f} MiB" if ops.get("memory_bytes") else "n/a",help="Average process memory sampled during simulation.")
            c[1].metric("Peak memory",f"{ops['peak_memory_bytes']/1024/1024:,.2f} MiB" if ops.get("peak_memory_bytes") else "n/a",help="Peak process memory sampled during simulation.")
            c[2].metric("Process CPU",f"{number(ops.get('cpu_percent'))}%" if ops.get("cpu_percent") is not None else "n/a",help="Process CPU use sampled during simulation.")
            st.caption("CPU and memory are environment-dependent, includes Streamlit overhead. Samples cover the simulation window.")
    else: st.caption("Run a simulation to populate communication measurements.")
