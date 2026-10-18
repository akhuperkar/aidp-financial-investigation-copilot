"""Local single-presenter history. No PAF deletion calls; no login secrets saved."""
import hashlib
import json
import os
from pathlib import Path
import sqlite3
from datetime import datetime, timezone


def history_scope(endpoint,mode,identity):
    return hashlib.sha256(json.dumps([endpoint,mode,identity]).encode()).hexdigest()


class HistoryStore:
    def __init__(self,path):
        self.path=Path(path).expanduser()
        self.path.parent.mkdir(parents=True,exist_ok=True)
        with self.connect() as db:
            db.execute('CREATE TABLE IF NOT EXISTS conversations (scope TEXT NOT NULL, id TEXT NOT NULL, updated TEXT NOT NULL, document TEXT NOT NULL, PRIMARY KEY(scope,id))')
            db.execute('PRAGMA secure_delete=ON')
        os.chmod(self.path,0o600)

    def connect(self):
        db=sqlite3.connect(self.path,timeout=10)
        db.execute('PRAGMA secure_delete=ON')
        return db

    def load(self,scope):
        with self.connect() as db:
            rows=db.execute('SELECT document FROM conversations WHERE scope=? ORDER BY updated DESC',(scope,)).fetchall()
        return [json.loads(row[0]) for row in rows]

    def save(self,scope,document):
        # Whitelist conversation fields: never serialize the Streamlit state/client.
        clean={k:document[k] for k in ('id','title','room_id','turns','context_reset','assistant_title') if k in document}
        with self.connect() as db:
            db.execute('INSERT OR REPLACE INTO conversations VALUES (?,?,?,?)',
                       (scope,clean['id'],datetime.now(timezone.utc).isoformat(),json.dumps(clean,ensure_ascii=False)))

    def delete(self,scope,conversation_id):
        with self.connect() as db:
            db.execute('DELETE FROM conversations WHERE scope=? AND id=?',(scope,conversation_id))

    def delete_turn(self,scope,conversation_id,turn_id):
        with self.connect() as db:
            row=db.execute('SELECT document FROM conversations WHERE scope=? AND id=?',(scope,conversation_id)).fetchone()
            if not row: return False
            doc=json.loads(row[0]); before=len(doc['turns'])
            doc['turns']=[t for t in doc['turns'] if t['id']!=turn_id]
            if before==len(doc['turns']): return False
            doc['room_id']=None; doc['context_reset']=True
            doc['title']=doc['turns'][0]['prompt'][:70] if doc['turns'] else 'Empty conversation'
            db.execute('UPDATE conversations SET document=? WHERE scope=? AND id=?',(json.dumps(doc,ensure_ascii=False),scope,conversation_id))
        return True
