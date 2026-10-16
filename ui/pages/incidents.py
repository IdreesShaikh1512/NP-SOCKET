import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from ui.context import page_start,number
from ui.components import card,dataframe
from ui.charts import METHOD_LABELS

state,result=page_start("Incidents","Ground truth and method decisions scored per incident")
if result is not None:
    rows=result["decision_table"]
    with card("Ground truth and method decisions"):
        display=[]
        for row in rows:
            truth=bool(row["is_attack"])
            item={"incident_id":row["incident_id"],"is_attack":"Attack" if truth else "Benign",
                  "collaborative":"Detected" if row["collaborative"] else "Missed","local_only_any":"Detected" if row["local_only_any"] else "Missed",
                  "local_only_per_node_average":row["local_only_per_node_average"],
                  "majority_vote":"Detected" if row["majority_vote"] else "Missed","majority_vote_observers":"Detected" if row["majority_vote_observers"] else "Missed",
                  "weighted_support":row.get("weighted_support",0),"distinct_sources":row.get("distinct_sources",0),
                  "supporting_node_ids":row.get("supporting_node_ids",""),"local_detection_nodes":row.get("local_detection_nodes",""),
                  "decision_path":row.get("decision_path",""),"explanation":row.get("explanation","")}
            display.append(item)
        table=pd.DataFrame(display).rename(columns={"incident_id":"Incident ID","is_attack":"Ground truth",
            **METHOD_LABELS,"local_only_per_node_average":"Local only (per-node average share)",
            "weighted_support":"Weighted support","distinct_sources":"Distinct sources","supporting_node_ids":"Supporting node IDs",
            "local_detection_nodes":"Local detection nodes","decision_path":"Decision path","explanation":"Evidence explanation"})
        method_columns=[METHOD_LABELS[k] for k in ("collaborative","local_only_any","majority_vote","majority_vote_observers")]
        average_column="Local only (per-node average share)"
        def result_style(row):
            attack=row["Ground truth"]=="Attack"; styles=[]
            for column in method_columns:
                correct=(row[column]=="Detected")==attack
                styles.append("background-color: #ECFDF3" if correct else "background-color: #FEF2F2")
            share=float(row[average_column]); share_correct=(share>0) if attack else (share==0)
            return [""]*2+styles[:2]+["background-color: #ECFDF3" if share_correct else "background-color: #FEF2F2"]+styles[2:]+[""]*(len(row)-7)
        styled=table.drop(columns=["Decision path","Evidence explanation"]).style.format({average_column:"{:.3f}","Weighted support":"{:.3f}"}).apply(result_style,axis=1)
        dataframe(styled,height=440)
    selected=st.selectbox("Inspect incident",[x["incident_id"] for x in rows],key="incident_detail",help="Choose an evaluation incident to inspect its window, evidence, support, and explanation.")
    row=next(x for x in rows if x["incident_id"]==selected)
    truth=next(x for x in result["incidents"] if x["incident_id"]==selected)
    with card("Incident details"):
        st.subheader(selected)
        c1,c2,c3=st.columns(3)
        c1.metric("Truth", "Attack" if truth["is_attack"] else "Benign",help="Ground-truth label for this evaluation incident.")
        c2.metric("Window",f"{number(truth['start_time'])}–{number(truth['end_time'])} s",help="Simulation start and end times for this labeled incident.")
        c3.metric("Grace period",f"{number(result['grace_period_seconds'])} s",help="Time after the incident end allowed for scoring an attack decision.")
        support=row.get("peer_weighted_support",row.get("weighted_support",0)); threshold=result.get("decision_threshold",.5)
        fig=go.Figure(go.Bar(x=[support],y=["Weighted support"],orientation="h",marker_color="#3B82F6",text=[f"{support:.3f}"],textposition="outside"))
        fig.add_vline(x=threshold,line_dash="dash",line_color="#D97706",annotation_text=f"Decision threshold {threshold:.3f}")
        fig.update_layout(xaxis_title="Weighted support",yaxis_title="",height=180,margin={"l":5,"r":20,"t":20,"b":35})
        st.plotly_chart(fig,width="stretch")
        columns=st.columns(3)
        columns[0].metric("Distinct sources",row["distinct_sources"],help="Number of distinct authenticated peer senders supporting this incident.")
        columns[1].metric("Supporting node IDs",row["supporting_node_ids"] or "None",help="Node identities whose validated alerts contributed support.")
        columns[2].metric("Nodes observing target",row.get("observing_node_ids") or "None",help="Nodes with local observations of this incident target.")
        st.markdown("**Explanation**")
        st.write(row["decision_path"])
        st.write(row["explanation"])
