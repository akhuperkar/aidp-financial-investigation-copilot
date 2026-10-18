import tempfile
import unittest
from pathlib import Path
from history_store import HistoryStore, history_scope

class HistoryTests(unittest.TestCase):
    def test_roundtrip_scope_and_deletion_resets_room(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'history.sqlite3'
            store=HistoryStore(path)
            scope=history_scope('https://localhost/run/A','user','alice')
            doc={'id':'chat1','title':'First question','room_id':'r1','turns':[{'id':'t1','prompt':'one'},{'id':'t2','prompt':'two'}]}
            store.save(scope,doc)
            self.assertEqual(HistoryStore(path).load(scope)[0]['room_id'],'r1')
            other=history_scope('https://localhost/run/B','user','alice')
            self.assertEqual(store.load(other),[])
            self.assertFalse(store.delete_turn(other,'chat1','t1'))
            self.assertTrue(store.delete_turn(scope,'chat1','t1'))
            loaded=store.load(scope)[0]
            self.assertEqual([t['id'] for t in loaded['turns']],['t2'])
            self.assertIsNone(loaded['room_id'])
            self.assertTrue(loaded['context_reset'])
            store.delete(scope,'chat1')
            self.assertEqual(store.load(scope),[])

    def test_credentials_not_stored_in_scope(self):
        result=history_scope('https://host/run','api_key','secret-token')
        self.assertNotIn('secret-token',result)
        self.assertNotEqual(result,history_scope('https://host/run','api_key','other'))

if __name__=='__main__': unittest.main()
