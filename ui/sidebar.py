"""Persistent navigation controls and run buttons shared by every page."""
import streamlit as st
from cids.config import Settings
from cids.event_generator import SCENARIOS
from cids.experiments import run_experiments
from cids.simulation import run
from .context import controller


def render_sidebar():
    state=controller()
    with st.sidebar:
        color={"Idle":"#8B98A5","Running":"#3B82F6","Finished":"#22C55E","Error":"#EF4444"}.get(state.status,"#8B98A5")
        st.markdown(f"<span style='color:{color};font-size:12px;font-weight:600'>● {state.status} · run {state.run_number}</span>",unsafe_allow_html=True)
        with st.expander("Network",expanded=False):
            nodes=st.slider("Nodes",2,10,4,key="ctl_nodes",help="Number of isolated localhost IDS observers.")
            tls=st.toggle("TLS",value=False,key="ctl_tls",help="Encrypt local peer sockets; generate the lab certificate first.")
            speed=st.slider("Simulation speed",10,500,100,key="ctl_speed",help="Simulation seconds advanced per wall-clock second.")
        max_sources=max(1,nodes-1)
        if st.session_state.get("ctl_min_sources",2)>max_sources: st.session_state.ctl_min_sources=max_sources
        with st.expander("Detection",expanded=False):
            local_threshold=st.slider("Local threshold",2,20,6,key="ctl_local_threshold",help="Events from one source in the detector window needed for a local alert.")
            reporting=st.slider("Reporting threshold",0.1,1.0,.5,.1,key="ctl_reporting_threshold",help="Normalized local score at which a suspicion is shared; 0.5 equals half the local event threshold.")
            correlation=st.slider("Correlation window (s)",1,60,15,key="ctl_corr",help="Simulation seconds during which evidence for the same target and event type is combined.")
            decision=st.slider("Decision threshold",.3,.9,.5,.05,key="ctl_decision",help="Minimum trust-weighted peer support for a peer-only decision.")
            min_peers=st.slider("Minimum peer sources",1,max_sources,min(2,max_sources),key="ctl_min_sources",help="Distinct authenticated peer senders required; local self-evidence is exempt.")
        with st.expander("Run",expanded=True):
            scenario=st.selectbox("Scenario",("all",)+SCENARIOS,key="ctl_scenario",help="Seeded synthetic event and fault-injection workload.")
            duration=st.slider("Duration (s)",30,600,180,30,key="ctl_duration",help="Scale the synthetic incident schedule to this simulation duration.")
            seed=st.number_input("Starting seed",0,100000,7,key="ctl_seed",help="Seed used for a single run or first experiment run.")
            seeds=st.number_input("Number of seeds",1,50,5,key="ctl_seed_count",help="How many independently seeded runs to include in a multi-seed experiment.")
        running=state.status=="Running"
        run_single=st.button("Run simulation",type="primary",width="stretch",disabled=running,help="Run the selected scenario once with the configured settings.")
        col1,col2=st.columns(2)
        run_multi=col1.button("Multi-seed",width="stretch",disabled=running,help="Run independent seeded repetitions and summarize mean ± standard deviation.")
        stop=col2.button("Stop",width="stretch",disabled=not running,help="Request a graceful stop at the next simulation checkpoint.")
        snapshot={"nodes":nodes,"tls":tls,"speedup":float(speed),"rate_threshold":int(local_threshold),"reporting_threshold":float(reporting),"correlation_window":float(correlation),"decision_threshold":float(decision),"min_peer_sources":int(min_peers),"scenario":scenario,"duration_seconds":float(duration),"seed":int(seed),"seed_count":int(seeds)}
        st.session_state.cids_settings_snapshot=snapshot
    if stop: state.stop()
    options={k:v for k,v in snapshot.items() if k in {"tls","speedup","rate_threshold","reporting_threshold","correlation_window","quorum_weight","min_peer_sources","duration_seconds"}}
    options["quorum_weight"]=snapshot["decision_threshold"]
    if run_single:
        try:
            settings=Settings(node_count=nodes,seed=int(seed),**options).validate()
            started=state.start("single",lambda event,sink:run(settings,scenario,event,sink))
            if started: st.rerun()
        except Exception as exc: state.error=f"{type(exc).__name__}: {exc}"; state.status="Error"
    if run_multi:
        try:
            Settings(node_count=nodes,seed=int(seed),**options).validate()
            started=state.start("multi_seed",lambda event,sink:run_experiments(count=int(seeds),start_seed=int(seed),scenario=scenario,nodes=nodes,settings_options=options,stop_event=event))
            if started: st.rerun()
        except Exception as exc: state.error=f"{type(exc).__name__}: {exc}"; state.status="Error"
    state.poll()
