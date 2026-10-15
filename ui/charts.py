"""Consistent chart styling and labels for all pages."""
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import plotly.io as pio

METHOD_COLORS={"collaborative":"#3B82F6","local_only_any":"#94A3B8","local_only_per_node_average":"#64748B","majority_vote":"#F59E0B","majority_vote_observers":"#A78BFA"}
METHOD_LABELS={"collaborative":"Collaborative (trust-weighted)","local_only_any":"Local only (any node)","local_only_per_node_average":"Local only (per-node average)","majority_vote":"Majority vote (all nodes)","majority_vote_observers":"Majority vote (observers)"}
DISPLAY={"tp":"True positives","tn":"True negatives","fp":"False positives","fn":"False negatives","precision":"Precision","recall":"Recall","f1":"F1 score","accuracy":"Accuracy","false_positive_rate":"False positive rate","mean":"Mean","std":"Standard deviation"}


def register_plotly_template():
    template=go.layout.Template(layout=go.Layout(
        paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)",
        font={"family":"Inter, Arial, sans-serif","color":"#E6EDF3","size":12},
        colorway=["#3B82F6","#94A3B8","#64748B","#F59E0B","#A78BFA"],
        margin={"l":18,"r":18,"t":42,"b":20},height=330,
        legend={"orientation":"h","yanchor":"bottom","y":1.02,"xanchor":"left","x":0},
        xaxis={"gridcolor":"#1F2A37","zerolinecolor":"#1F2A37","linecolor":"#1F2A37"},
        yaxis={"gridcolor":"#1F2A37","zerolinecolor":"#1F2A37","linecolor":"#1F2A37"},
    ))
    pio.templates["cids_dark"]=template
    pio.templates.default="cids_dark"


register_plotly_template()

def metric_frame(result):
    rows=[]
    for method,metrics in result["classification"].items():
        stds=result.get("classification_std",{}).get(method,{})
        row={"Method":METHOD_LABELS.get(method,method)}
        for key,value in metrics.items(): row[DISPLAY.get(key,key)]=value
        for key,value in stds.items(): row[f"{DISPLAY.get(key,key)} (across nodes std)"]=value
        rows.append(row)
    return pd.DataFrame(rows)

def comparison_chart(result,metrics=("f1","false_positive_rate"),title="Method comparison"):
    rows=[]
    for method,values in result["classification"].items():
        for metric in metrics:
            if metric in values: rows.append({"Method":METHOD_LABELS.get(method,method),"Metric":DISPLAY.get(metric,metric),"Value":values[metric]})
    fig=px.bar(pd.DataFrame(rows),x="Value",y="Method",color="Method",facet_col="Metric",color_discrete_map={METHOD_LABELS[k]:v for k,v in METHOD_COLORS.items()},title=title,orientation="h",text_auto=".3f")
    fig.update_layout(barmode="group",height=max(300,45*len(result["classification"]))); fig.update_traces(textposition="outside",cliponaxis=False)
    return fig

def summary_sentence(result):
    scores=result["classification"]
    collab=scores["collaborative"]; local=scores["local_only_any"]
    detected=collab["tp"]; total=collab["tp"]+collab["fn"]
    f1=collab["f1"]; fpr=collab["false_positive_rate"]
    better="higher" if collab["f1"]>local["f1"] else "lower" if collab["f1"]<local["f1"] else "equal"
    return (f"Collaborative detection found {detected:g} of {total:g} attack incidents (F1 {f1:.3f}, false-positive rate {fpr:.3f}). "
            f"Its F1 is {better} than local-only-any ({local['f1']:.3f}). "
            f"Peer-only decisions require {result.get('min_peer_sources',2)} sources; local threshold detections use self-evidence.")

def network_figure(result,at_time):
    nodes=result["nodes"]; count=max(1,len(nodes)); positions={n:(__import__("math").cos(2*__import__("math").pi*i/count),__import__("math").sin(2*__import__("math").pi*i/count)) for i,n in enumerate(nodes)}
    edges=[]
    for item in result.get("topology_history",result.get("topology",[])):
        start=item.get("start_time",0); end=item.get("end_time")
        if start<=at_time and (end is None or at_time<=end): edges.append(item)
    fig=go.Figure()
    for e in edges:
        x0,y0=positions[e["source"]]; x1,y1=positions[e["target"]]; reachable=e["status"]=="reachable"; color="#334155" if reachable else "#EF4444"
        fig.add_trace(go.Scatter(x=[x0,x1],y=[y0,y1],mode="lines",line={"color":color,"width":1.5,"dash":"solid" if reachable else "dash"},hovertemplate=f"{e['source']} ↔ {e['target']} · {e['status']}<extra></extra>",showlegend=False))
    offline={n for e in edges if e["status"]!="reachable" for n in (e["source"],e["target"])}
    labels=[]; colors=[]; symbols=[]
    for n in nodes:
        labels.append(n+ (" · misleading" if n==result.get("misleading_peer_id") else " · offline" if n in offline else ""))
        colors.append("#64748B" if n in offline else "#18202B")
        symbols.append("circle")
    outlines=["#F59E0B" if n==result.get("misleading_peer_id") else "#8B98A5" if n in offline else "#3B82F6" for n in nodes]
    fig.add_trace(go.Scatter(x=[positions[n][0] for n in nodes],y=[positions[n][1] for n in nodes],mode="markers+text",text=labels,textposition="bottom center",marker={"size":30,"color":colors,"symbol":symbols,"line":{"color":outlines,"width":2}},hovertemplate="%{text}<extra></extra>",showlegend=False))
    fig.update_layout(title=f"Network topology at simulation time {at_time:.2f}s",xaxis={"visible":False},yaxis={"visible":False,"scaleanchor":"x","scaleratio":1},height=400,margin={"l":10,"r":10,"t":50,"b":20},plot_bgcolor="rgba(0,0,0,0)",paper_bgcolor="rgba(0,0,0,0)",template="cids_dark",annotations=[{"x":0,"y":-0.12,"xref":"paper","yref":"paper","text":"Reachable — muted line   ·   Unreachable — dashed red   ·   Misleading peer — amber outline   ·   Offline — grey","showarrow":False,"font":{"size":10,"color":"#8B98A5"}}])
    return fig
