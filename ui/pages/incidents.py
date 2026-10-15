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
        st.subheader("Ground truth × per-incident decisions")
        display=[]
        for row in rows:
            truth=bool(row["is_attack"])
            item={"incident_id":row["incident_id"],"is_attack":"Attack" if truth else "Benign",
                  "collaborative":"Detected" if row["collaborative"] else "No alert","local_only_any":"Detected" if row["local_only_any"] else "No alert",
                  "local_only_per_node_average":row["local_only_per_node_average"],
                  "majority_vote":"Detected" if row["majority_vote"] else "No alert","majority_vote_observers":"Detected" if row["majority_vote_observers"] else "No alert",
                  "weighted_support":row.get("weighted_support",0),"distinct_sources":row.get("distinct_sources",0),
                  "supporting_node_ids":row.get("supporting_node_ids",""),"explanation":row.get("explanation","")}
            display.append(item)
        table=pd.DataFrame(display).rename(columns={"incident_id":"Incident ID","is_attack":"Ground truth",
            **METHOD_LABELS,"weighted_support":"Weighted support",
            "distinct_sources":"Distinct sources","supporting_node_ids":"Supporting node IDs","explanation":"Explanation"})
        def result_style(row):
            styles=[]
            for column in (METHOD_LABELS["collaborative"],METHOD_LABELS["local_only_any"],METHOD_LABELS["majority_vote"],METHOD_LABELS["majority_vote_observers"]):
                correct=(row[column]=="Detected")==("Attack" in str(row["Ground truth"]))
                styles.append("background-color: #182B22; color: #86EFAC" if correct else "background-color: #2B2020; color: #FCA5A5")
            return [""]*2+[styles[0],styles[1],""]+[styles[2],styles[3]]+[""]*(len(row)-7)
        from ui.charts import METHOD_COLORS
        header_styles=[{"selector":f"th.col{idx}","props":[("color",METHOD_COLORS[key]),("font-weight","600")]} for idx,(col,key) in enumerate((("Collaborative (trust-weighted)","collaborative"),("Local only (any node)","local_only_any"),("Local only (per-node average)","local_only_per_node_average"),("Majority vote (all nodes)","majority_vote"),("Majority vote (observers)","majority_vote_observers")),start=2)]
        styled=table.style.format({"Local only (per-node average)":"{:.3f}","Weighted support":"{:.3f}"}).apply(result_style,axis=1).set_table_styles(header_styles,overwrite=False)
        dataframe(styled,height=340)
    selected=st.selectbox("Inspect incident",[x["incident_id"] for x in rows],key="incident_detail",help="Choose an evaluation incident to inspect its window, evidence, support, and explanation.")
    row=next(x for x in rows if x["incident_id"]==selected)
    truth=next(x for x in result["incidents"] if x["incident_id"]==selected)
    with card("Incident details"):
        st.subheader(selected)
        c1,c2,c3=st.columns(3)
        c1.metric("Truth", "Attack" if truth["is_attack"] else "Benign",help="Ground-truth label for this evaluation incident.")
        c2.metric("Incident window",f"{number(truth['start_time'])}–{number(truth['end_time'])} s",help="Simulation start and end times for this labeled incident.")
        c3.metric("Scoring grace",f"{number(result['grace_period_seconds'])} s",help="Time after the incident end allowed for scoring an attack decision.")
        support=row.get("peer_weighted_support",row.get("weighted_support",0)); threshold=result.get("decision_threshold",.5)
        fig=go.Figure(go.Bar(x=[support],y=["Weighted support"],orientation="h",marker_color="#3B82F6",text=[f"{support:.3f}"],textposition="outside"))
        fig.add_vline(x=threshold,line_dash="dash",line_color="#F59E0B",annotation_text=f"Decision threshold {threshold:.3f}")
        fig.update_layout(xaxis_title="Weighted support",yaxis_title="",height=180,margin={"l":5,"r":20,"t":20,"b":35})
        st.plotly_chart(fig,width="stretch")
        columns=st.columns(3)
        columns[0].metric("Distinct sources",row["distinct_sources"],help="Number of distinct authenticated peer senders supporting this incident.")
        columns[1].metric("Supporting node IDs",row["supporting_node_ids"] or "None",help="Node identities whose validated alerts contributed support.")
        columns[2].metric("Nodes observing target",row.get("observing_node_ids") or "None",help="Nodes with local observations of this incident target.")
        st.markdown("**Explanation**")
        st.write(row["explanation"])
