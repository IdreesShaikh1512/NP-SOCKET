import asyncio

from cids.baselines import majority_peer_vote
from cids.clock import SimulationClock
from cids.config import Settings
from cids.evaluation import evaluate_incidents
from cids.event_generator import generate, incidents
from cids.event_generator import REFERENCE_DURATION
from cids.experiments import summarize_runs
from cids.metrics import classification
from cids.models import Alert, Event
from cids.node import IDSNode
from cids.message_security import sign
from cids.simulation import run
from cids.consensus_engine import ConsensusEngine
from cids import experiments


def test_latency_is_measured_from_each_incident_start():
    truth = [{"incident_id":"i1", "target_id":"host", "event_type":"login", "start_time":10, "end_time":11, "is_attack":True}]
    evaluated = evaluate_incidents(truth, [{"target_id":"host", "event_type":"login", "timestamp":13, "is_attack":True, "weighted_support":1, "sources":["n0"]}], {}, [], ["n0"], grace=5)
    assert evaluated["latency_table"][0]["latency_seconds"] == 3


def test_forged_claim_does_not_change_honest_peers_trust():
    async def case():
        settings = Settings(node_count=2)
        keys = {"node-0":b"0"*32, "node-1":b"1"*32}
        node = IDSNode("node-1", {"node-0":0}, keys, settings, SimulationClock())
        forged = Alert(1,"forged","e1","node-0",0,"login_fail","host",4,.9,"forged evidence", "0"*64)
        before = node.trust.get("node-0")
        await node.handle("node-0", __import__("json").dumps(forged.__dict__).encode())
        assert node.trust.get("node-0") == before
        assert node.validator.rejections["signature"] == 1
        assert node.transport.rejections[("node-0", "signature")] == 1
    asyncio.run(case())


def test_trust_uses_each_observers_own_authenticated_evidence():
    async def case():
        keys = {"node-0":b"0"*32,"node-1":b"1"*32,"node-2":b"2"*32}
        observers = [IDSNode(f"node-{i}", {f"node-{j}":0 for j in range(3) if i != j}, keys, Settings(node_count=3), SimulationClock()) for i in (1,2)]
        event = Event("local", 0, "node-1", "host", "login_fail", {})
        observers[0].local_events[("host","login_fail")].append(event)
        alert = Alert(1,"a1","e1","node-0",0,"login_fail","host",4,.9,"authenticated report")
        sign(alert,keys["node-0"])
        for observer in observers:
            await observer.handle("node-0", __import__("json").dumps(alert.__dict__).encode())
        assert observers[0].trust.get("node-0") == .55
        assert observers[1].trust.get("node-0") == .5
    asyncio.run(case())


def test_majority_vote_counts_distinct_validated_alert_sources():
    incident = {"target_id":"host","event_type":"probe","start_time":1,"end_time":2}
    alerts = [Alert(1,f"a{i}",f"e{i}",f"node-{i}",1.5,"probe","host",4,.9,"valid") for i in range(3)]
    assert not majority_peer_vote(incident, alerts[:1], [f"node-{i}" for i in range(4)], 1)["decision"]
    assert majority_peer_vote(incident, alerts[:3], [f"node-{i}" for i in range(4)], 1)["decision"]
    local = {"node-0":[{"target_id":"host","event_type":"probe","timestamp":1.5}]}
    score = evaluate_incidents([dict(incident,incident_id="i",is_attack=True)], [], local, alerts[:1], [f"node-{i}" for i in range(4)], 1)
    row = score["decision_table"][0]
    assert row["local_only_any"] is True and row["majority_vote"] is False


def test_ground_truth_has_benign_evaluation_units_and_confusion_counts_reconcile():
    truth = incidents("all", include_fault=True)
    assert any(not row["is_attack"] for row in truth)
    assert any(row["incident_id"] == "inc-false-peer-alert" for row in truth)
    result = evaluate_incidents(truth, [], {}, [], ["node-0","node-1"], grace=5)
    for method, metrics in result["classification"].items():
        if method=="local_only_per_node_average":
            assert not {"tp","tn","fp","fn"} & set(metrics)
        else:
            assert len(result["decision_table"]) == metrics["tp"] + metrics["tn"] + metrics["fp"] + metrics["fn"]
    low = next(row for row in truth if row["incident_id"] == "inc-lowrate")
    assert low["end_time"] - low["start_time"] == 9


def test_low_rate_has_three_subthreshold_observations_within_reporting_window():
    events = generate(7, 4, "low_rate", REFERENCE_DURATION)
    assert len(events) == 12
    for node in {e.source_id for e in events}:
        local = [e for e in events if e.source_id == node]
        assert len(local) == 3 and local[-1].timestamp-local[0].timestamp < 10
        assert len(local) < Settings().rate_threshold


def test_false_positive_rate_is_reported():
    assert classification([True,False],[True,True])["false_positive_rate"] == 1


def test_multi_seed_summary_reports_mean_and_sample_std():
    runs = [{"classification":{"m":{"tp":i,"tn":0,"fp":0,"fn":0,"precision":i,"recall":0,"f1":0,"accuracy":0,"false_positive_rate":0}}} for i in (1,3)]
    row = next(r for r in summarize_runs(runs) if r["method"] == "m" and r["metric"] == "tp")
    assert row["mean"] == 2 and row["std"] == 2**.5


def test_simulation_evaluates_duplicate_alert_unit_once_and_reconciles_delivery():
    async def case():
        result = await run(Settings(node_count=4, speedup=500), "all")
        ids = [row["incident_id"] for row in result["incidents"]]
        assert ids.count("inc-false-peer-alert") == 1
        delivery = result["alert_delivery"]
        assert delivery["unaccounted"] == 0
        assert delivery["alerts_transmitted"] == delivery["validated_alerts_received"] + sum(delivery["rejected_by_reason"].values())
        assert result["operational"]["bytes_received"] > 0
        assert {"empty_frame","truncated","oversized_frame","non_utf8","invalid_json"} <= set(result["rejection_counts"])
        assert all(x["delta"]>=0 or x["reason"]=="authenticated_alert_uncorroborated_while_target_observed" for x in result["trust_history"])
        false_peer=next(x for x in result["decision_table"] if x["incident_id"]=="inc-false-peer-alert")
        assert not false_peer["collaborative"]
        assert all(not x["local_only_any"] or x["collaborative"] for x in result["decision_table"])
    asyncio.run(case())


def test_peer_quorum_requires_two_sources_but_local_detection_overrides_it():
    engine=ConsensusEngine(threshold=.5,min_peer_sources=2)
    alert=Alert(1,"a","e","node-0",1,"probe","host",3,.8,"evidence")
    one=[(1,alert,.8)]
    assert not engine.decide(("host","probe"),one,2,observer_id="node-1")["is_attack"]
    assert engine.decide(("host","probe"),one,2,observer_id="node-0",local_detected=True)["is_attack"]


def test_subthreshold_suspicion_confidence_tracks_local_score():
    async def case():
        settings=Settings(node_count=2); keys={"node-0":b"0"*32,"node-1":b"1"*32}; node=IDSNode("node-0",{},keys,settings,SimulationClock())
        events=[Event(str(i),float(i),"node-0","host","login_fail",{}) for i in (1,2,3)]
        result=None
        for event in events: result=node.detector.observe(event)
        await node.publish(events[-1],result)
        assert not result["decision"] and result["score"]==.5
        assert node.local[-1].confidence==.5 and node.local[-1].severity==2
    asyncio.run(case())


def test_per_node_average_averages_metrics_and_reports_cross_node_std():
    truth=[True,False]
    local={"node-0":[{"target_id":"a","event_type":"probe","timestamp":1}],
           "node-1":[{"target_id":"b","event_type":"probe","timestamp":1}]}
    incidents_=[{"incident_id":"a","target_id":"a","event_type":"probe","start_time":0,"end_time":2,"is_attack":True},
                {"incident_id":"b","target_id":"b","event_type":"probe","start_time":0,"end_time":2,"is_attack":False}]
    result=evaluate_incidents(incidents_,[],local,[],["node-0","node-1"],0)
    avg=result["classification"]["local_only_per_node_average"]
    assert avg["precision"] == .5
    assert avg["f1"] == .5
    assert not {"tp","tn","fp","fn"} & set(avg)
    assert result["classification_std"]["local_only_per_node_average"]["precision"] > .7


def test_observer_majority_can_detect_when_all_node_majority_cannot():
    incident={"incident_id":"i","target_id":"host","event_type":"probe","start_time":1,"end_time":2,"is_attack":True}
    alert=Alert(1,"a","e","node-0",1.5,"probe","host",3,.8,"validated")
    event=Event("e",1.5,"node-0","host","probe",{})
    result=evaluate_incidents([incident],[],{},[alert],[f"node-{i}" for i in range(4)],0,
                              {"node-0":[event],"node-1":[],"node-2":[],"node-3":[]})
    row=result["decision_table"][0]
    assert row["majority_vote"] is False
    assert row["majority_vote_observers"] is True


def test_authenticated_unconfirmed_alert_decreases_trust_after_window():
    async def case():
        settings=Settings(node_count=2,correlation_window=1,speedup=1000)
        keys={"node-0":b"0"*32,"node-1":b"1"*32}; clock=SimulationClock(settings.speedup)
        node=IDSNode("node-1",{"node-0":0},keys,settings,clock)
        now=clock.now(); node.local_events[("host","benign_observation")].append(Event("watch",now,"node-1","host","benign_observation",{}))
        alert=Alert(1,"auth-false","e1","node-0",now,"probe","host",3,.8,"authenticated report"); sign(alert,keys["node-0"])
        await node.handle("node-0",__import__("json").dumps(alert.__dict__).encode())
        await node.drain_trust_audits()
        assert node.trust.get("node-0")==.4
        update=node.trust.states["node-0"].history[-1]
        assert update["reason"]=="authenticated_alert_uncorroborated_while_target_observed"
        assert "no independent probe observation" in update["evidence"]
    asyncio.run(case())


def test_replay_does_not_change_sender_trust():
    async def case():
        settings=Settings(node_count=2); keys={"node-0":b"0"*32,"node-1":b"1"*32}; node=IDSNode("node-1",{"node-0":0},keys,settings,SimulationClock())
        now=node.clock.now(); alert=Alert(1,"repeat","e1","node-0",now,"probe","host",3,.8,"report"); sign(alert,keys["node-0"]); payload=__import__("json").dumps(alert.__dict__).encode()
        await node.handle("node-0",payload); before=node.trust.get("node-0"); await node.handle("node-0",payload)
        assert node.trust.get("node-0")==before==.5
        assert node.validator.rejections["replay"]==1
    asyncio.run(case())


def test_e2e_self_detection_and_lowrate_collaboration():
    async def case():
        concentrated=await run(Settings(node_count=4,speedup=100),"concentrated")
        concentrated_row=next(x for x in concentrated["decision_table"] if x["incident_id"]=="inc-concentrated")
        assert concentrated_row["local_only_any"] and concentrated_row["collaborative"]
        assert all(item["status"]=="reachable" for item in concentrated["warmup"])
        lowrate=await run(Settings(node_count=4,speedup=100),"low_rate")
        row=next(x for x in lowrate["decision_table"] if x["incident_id"]=="inc-lowrate")
        assert row["collaborative"] and not row["local_only_any"]
    asyncio.run(case())


def test_offline_peer_topology_is_timed_and_recovers():
    async def case():
        result=await run(Settings(node_count=4,speedup=100),"offline_peer")
        edge=next(x for x in result["topology_history"] if x["target"]=="node-3" and x["status"]=="offline")
        assert edge["start_time"]<=122 and edge["end_time"]>=125
        assert any(x["target"]=="node-3" and x["status"]=="reachable" and abs(x["start_time"]-edge["end_time"])<.01 for x in result["topology_history"])
    asyncio.run(case())


def test_threshold_sweep_writes_f1_and_fpr_for_each_setting(tmp_path,monkeypatch):
    async def fake_run(settings,scenario):
        return {"classification":{"collaborative":{"f1":settings.quorum_weight,"false_positive_rate":settings.min_peer_sources/10}},"misleading_peer_weighted_support":.6}
    monkeypatch.setattr(experiments,"run",fake_run)
    async def case():
        result=await experiments.run_threshold_sweep(seeds=[7,17],thresholds=[.4,.6],min_peer_sources=[1,2],out=tmp_path,nodes=4)
        assert result["count"]==4
        rows=result["rows"]
        assert rows[0]["collaborative_f1_mean"]==.4 and rows[0]["collaborative_fpr_mean"]==.1
        assert (tmp_path/"threshold_sweep.csv").exists()
    asyncio.run(case())
