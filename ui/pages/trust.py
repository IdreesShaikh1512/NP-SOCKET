import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st
from ui.context import page_start
from ui.components import card,dataframe

state,result=page_start("Trust","Trust is observer-specific and changes only on authenticated evidence")
if result is not None:
    with card("Observer × peer scores"):
        st.subheader("Observer × peer trust")
        nodes=result["nodes"]; trust=result["trust"]
        matrix=np.full((len(nodes),len(nodes)),np.nan)
        for i,observer in enumerate(nodes):
            for j,peer in enumerate(nodes):
                if observer!=peer: matrix[i,j]=trust.get(observer,{}).get(peer,np.nan)
        fig=px.imshow(matrix,x=nodes,y=nodes,color_continuous_scale=[[0,"#EF4444"],[.5,"#64748B"],[1,"#22C55E"]],zmin=0,zmax=1,text_auto=".3f",aspect="auto",labels={"x":"Peer","y":"Observer","color":"Trust score"},template="cids_dark")
        fig.update_layout(height=390)
        st.plotly_chart(fig,width="stretch")
    with card("Observer-specific trust history"):
        st.subheader("Trust history")
        history=pd.DataFrame(result.get("trust_history",[]))
        if history.empty: st.caption("No trust changes occurred in this run.")
        else:
            observers=sorted(history.observer_id.unique()); observer=st.selectbox("Observer",observers,key="trust_observer",help="Select which node's independent trust evidence to inspect.")
            focus=history[history.observer_id==observer]
            fig=px.line(focus,x="simulation_time",y="to",color="peer_id",markers=True,labels={"simulation_time":"Simulation time (s)","to":"Trust score","peer_id":"Peer"})
            fig.update_yaxes(title_text="Trust score",range=[0,1]); st.plotly_chart(fig,width="stretch")
            peer_options=["All"]+sorted(focus.peer_id.unique()); peer=st.selectbox("Filter update log by peer",peer_options,key="trust_peer_filter",help="Limit the trust update log to one peer identity.")
            log=focus if peer=="All" else focus[focus.peer_id==peer]
            log=log.rename(columns={"peer_id":"Peer ID","simulation_time":"Simulation time (s)","from":"Trust before","to":"Trust score","delta":"Change","reason":"Update reason","evidence":"Evidence"}).sort_values("Simulation time (s)")
            dataframe(log,height=320)
