"""Deterministic response adapters; no model calls, fabricated sources, or scores."""
import json
import math
import pandas as pd
from paf_client import field


def decode(value):
    if isinstance(value,str):
        candidate=value.strip()
        if candidate.startswith('```json') and candidate.endswith('```'):
            candidate=candidate[7:-3].strip()
        if candidate.startswith(('{','[')):
            try: return json.loads(candidate)
            except ValueError: pass
    return value


def envelopes(raw):
    pending=[decode(raw)]; result=[]
    for _ in range(12):
        if not pending: break
        item=decode(pending.pop(0))
        if not isinstance(item,dict): continue
        result.append(item)
        for key in ('message','response','result','output','data'):
            child=decode(item.get(key))
            if isinstance(child,dict): pending.append(child)
    return result


def mapped(raw,path):
    value=decode(raw)
    for name in path.split('.'):
        value=decode(value)
        if not isinstance(value,dict): return None
        value=value.get(name)
    return decode(value)


def records(value):
    value=decode(value)
    if isinstance(value,list) and all(isinstance(x,dict) for x in value): return value
    return []


def parse_response(raw,answer_path='',rows_path='',sources_path='',room_path='roomId'):
    nodes=envelopes(raw)
    text=''; query=''; rows=[]; sources=[]
    explicit=mapped(raw,answer_path) if answer_path else None
    if isinstance(explicit,str): text=explicit.strip()
    # Prefer text on the deepest recognized envelope, including message.text.
    if not text:
        for node in reversed(nodes):
            for key in ('text','answer','content','message','response','output'):
                value=decode(node.get(key))
                if isinstance(value,str) and value.strip():
                    text=value.strip(); break
            if text: break
    if not text and isinstance(decode(raw),str): text=decode(raw)
    if rows_path: rows=records(mapped(raw,rows_path))
    else:
        for node in nodes:
            for key in ('data','rows','records'):
                rows=records(node.get(key))
                if rows: break
            if rows: break
    if sources_path:
        sources=mapped(raw,sources_path)
    else:
        for node in nodes:
            for key in ('citations','sources','references','sourceDocuments','source_documents','retrievedDocuments'):
                if node.get(key): sources=decode(node[key]); break
            if sources: break
    if not isinstance(sources,list): sources=[sources] if sources else []
    for node in nodes:
        value=node.get('query') or node.get('sql')
        if isinstance(value,str): query=value; break
    room=mapped(raw,room_path)
    if room is None and room_path=='roomId':
        room=next((n['roomId'] for n in nodes if n.get('roomId') is not None),None)
    metadata = {}
    for node in nodes:
        for key in ('metadata', 'similarity_score', 'similarityScore', 'score', 'distance', 'responseTime', 'response_time', 'usage'):
            if key in node and key not in metadata: metadata[key] = node[key]
    return {'metadata':metadata, 'text':text,'rows':rows,'sources':sources,'query':query,'room_id':room,
            'failed':any(n.get('status') is False or n.get('success') is False or bool(n.get('error')) for n in nodes)}


def chart_frame(rows,x,y):
    if not rows or any(x not in r or y not in r for r in rows): return None
    if any(not isinstance(r[y],(int,float)) or isinstance(r[y],bool) or not math.isfinite(r[y]) for r in rows): return None
    if any(not isinstance(r[x],(str,int,float)) or isinstance(r[x],bool) for r in rows): return None
    return pd.DataFrame([{x:r[x],y:r[y]} if x!=y else {x:r[x]} for r in rows])
