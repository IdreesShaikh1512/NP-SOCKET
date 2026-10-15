"""Seeded, partially visible synthetic workloads and their ground truth."""
import random
from .models import Event

SCENARIOS=("concentrated","coordinated","low_rate","benign_bait","duplicate_delayed","misleading_peer","offline_peer","replay","invalid_messages")
REFERENCE_DURATION=180.0

def _scale(duration_seconds):
    if duration_seconds<=0: raise ValueError("duration_seconds must be positive")
    return float(duration_seconds)/REFERENCE_DURATION

def generate(seed=7,node_count=4,scenario="all",duration_seconds=REFERENCE_DURATION):
    r=random.Random(seed); rows=[]; n=0; scale=_scale(duration_seconds)
    def add(t,target,kind,rate,owners,attack=False,incident="",label=None,spread=0.0):
        nonlocal n
        for i in owners:
            for j in range(rate):
                n+=1; offset=(spread*j/max(1,rate-1)) if rate>1 else 0.0
                rows.append(Event(f"e{n:05d}",(t+offset+r.random()*.04)*scale,f"node-{i}",target,kind,{"rate":1,"scenario":label or scenario},attack,incident))
    if scenario in ("all","concentrated"): add(1,"srv-A","login_fail",9,[0],True,"inc-concentrated","concentrated")
    if scenario in ("all","coordinated"): add(20,"srv-B","port_probe",3,[0,1,2][:node_count],True,"inc-coordinated","coordinated")
    # Three observations per sensor over eight seconds: reports suspicion at half
    # the local threshold but never reaches the local rate threshold of six.
    if scenario in ("all","low_rate"): add(40,"srv-C","login_fail",3,list(range(node_count)),True,"inc-lowrate","low_rate",spread=8)
    if scenario in ("all","benign_bait"): add(60,"srv-D","login_fail",5,[0],False,"inc-benign-bait","benign_bait")
    if scenario in ("all","duplicate_delayed"): add(80,"srv-E","http_request",4,[0,1],False,"inc-duplicate-delayed","duplicate_delayed")
    if scenario in ("all","misleading_peer"): add(100,"srv-F","port_probe",2,[0,1],True,"inc-misleading","misleading_peer")
    if scenario in ("all","offline_peer"): add(120,"srv-G","login_fail",8,[0],True,"inc-offline","offline_peer")
    if scenario in ("all","replay"): add(140,"srv-H","port_probe",8,[0],True,"inc-replay","replay")
    if scenario in ("all","invalid_messages"): add(160,"srv-I","login_fail",8,[0],True,"inc-invalid","invalid_messages")
    # Nodes 1 and 2 have recent benign visibility of the target later used by
    # the false-peer injection, allowing an evidence-based negative trust update.
    if scenario in ("all","misleading_peer"):
        add(169,"synthetic-fault-target","benign_observation",1,[i for i in (1,2) if i<node_count],False,"","watch")
    return sorted(rows,key=lambda e:e.timestamp)

def incidents(scenario="all",duration_seconds=REFERENCE_DURATION,include_fault=False):
    scale=_scale(duration_seconds)
    records=[
        ("concentrated","srv-A","login_fail",1,2,True),
        ("coordinated","srv-B","port_probe",20,22,True),
        ("lowrate","srv-C","login_fail",40,49,True),
        ("benign-bait","srv-D","login_fail",60,61,False),
        ("duplicate-delayed","srv-E","http_request",80,82,False),
        ("misleading","srv-F","port_probe",100,102,True),
        ("offline","srv-G","login_fail",120,122,True),
        ("replay","srv-H","port_probe",140,142,True),
        ("invalid_messages","srv-I","login_fail",160,162,True),
    ]
    aliases={"low_rate":"lowrate","benign_bait":"benign-bait","duplicate_delayed":"duplicate-delayed"}
    normalized=aliases.get(scenario,scenario)
    selected=records if scenario=="all" else [r for r in records if r[0]==normalized]
    output=[{"incident_id":"inc-"+key,"target_id":target,"event_type":kind,"start_time":start*scale,"end_time":end*scale,"is_attack":attack} for key,target,kind,start,end,attack in selected]
    if include_fault:
        output.append({"incident_id":"inc-false-peer-alert","target_id":"synthetic-fault-target","event_type":"port_probe","start_time":170*scale,"end_time":175*scale,"is_attack":False})
    return output
