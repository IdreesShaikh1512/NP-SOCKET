import pandas as pd
import plotly.express as px
import streamlit as st
from ui.context import page_start
from ui.components import card,dataframe

REASONS={"replay":"A previously accepted sender alert ID was received again.","freshness":"Authenticated alert timestamp fell outside the permitted freshness window.","signature":"HMAC signature did not match the configured sender key.","empty_frame":"Frame declared zero bytes.","truncated":"Frame ended before its declared payload length arrived.","oversized_frame":"Declared frame exceeded the configured maximum size.","non_utf8":"Payload was not valid UTF-8.","invalid_json":"Payload could not be decoded as JSON.","invalid_frame":"Malformed frame header or payload.","schema":"Message fields did not match the protocol schema.","types_ranges":"A field had an invalid type or value range.","sender":"Claimed identity did not match the authenticated channel identity.","protocol":"Protocol version was unsupported.","timeout":"Handshake or frame read exceeded its timeout."}

state,result=page_start("Security","Authentication, replay protection, and transport rejection evidence")
if result is not None:
    with card("Rejections by reason"):
        counts=result.get("rejection_counts",{})
        if counts:
            data=pd.DataFrame([{"Reason":k,"Count":v} for k,v in counts.items()])
            st.plotly_chart(px.bar(data,x="Reason",y="Count",color="Reason",title="Rejected messages and malformed frames"),width="stretch")
            data["Explanation"]=data.Reason.map(REASONS).fillna("Protocol or peer validation rejected the message.")
            dataframe(data,height=300)
        else: st.caption("No rejections recorded.")
    with card("Channel and peer rejection log"):
        rows=[]
        for key,count in result.get("rejections",{}).items():
            if ":" in key:
                parts=key.split(":",2)
                if len(parts)==3: rows.append({"Receiver":parts[0],"Connection peer":parts[1],"Reason":parts[2],"Count":count})
        if rows: dataframe(pd.DataFrame(rows),height=300)
        else: st.caption("No channel-scoped rejections recorded.")
        st.caption("Rejected or replayed payloads cannot change the trust score of the sender identity they claim. Those events are attributed to the transport channel.")
