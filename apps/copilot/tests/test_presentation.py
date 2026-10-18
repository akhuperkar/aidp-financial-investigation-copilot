import json
import unittest
from response_view import parse_response, chart_frame

class ResponseTests(unittest.TestCase):
    def test_screenshot_data_analysis_envelope(self):
        payload={'message':{'data':[{'MONTH':'March','MEDIAN_CONSUMPTION':1088.955,'DEVIATION':230.685}],
                            'query':'SELECT ... FETCH FIRST 1 ROW ONLY','status':True,'text':'In **March**, consumption was highest.'},'roomId':'r1'}
        for source in [payload, json.dumps(payload), {'response':json.dumps(payload)}]:
            parsed=parse_response(source)
            self.assertEqual(parsed['text'],'In **March**, consumption was highest.')
            self.assertEqual(len(parsed['rows']),1)
            self.assertIn('FETCH FIRST',parsed['query'])
            self.assertEqual(parsed['room_id'],'r1')

    def test_metadata_scores_unchanged_and_missing_not_invented(self):
        source={'message':'Answer','sources':[{'filename':'Guidelines.pdf','page':4,'similarity_score':0.87,'distance':0.13}]}
        parsed=parse_response(source)
        self.assertEqual(parsed['sources'][0]['similarity_score'],0.87)
        self.assertEqual(parsed['sources'][0]['distance'],0.13)
        self.assertEqual(parse_response({'message':'No metadata'})['sources'],[])

    def test_custom_paths_and_unknown_fallback(self):
        parsed=parse_response({'custom':{'answer':'Hello','records':[{'n':1}],'refs':['doc1']}},answer_path='custom.answer',rows_path='custom.records',sources_path='custom.refs')
        self.assertEqual(parsed['text'],'Hello')
        self.assertEqual(parsed['rows'],[{'n':1}])
        self.assertEqual(parsed['sources'],['doc1'])
        self.assertEqual(parse_response({'unknown':123})['text'],'')

    def test_false_status_not_presented_as_success(self):
        parsed=parse_response({'message':{'status':False,'text':'Query failed','data':[]}})
        self.assertTrue(parsed['failed'])

    def test_chart_no_aggregation_no_numeric_coercion(self):
        rows=[{'MONTH':'March','VALUE':1},{'MONTH':'March','VALUE':2}]
        frame=chart_frame(rows,'MONTH','VALUE')
        self.assertEqual(len(frame),2)
        self.assertEqual(frame['VALUE'].tolist(),[1,2])
        self.assertIsNone(chart_frame([{'MONTH':'March','VALUE':'not numeric'}],'MONTH','VALUE'))

if __name__=='__main__': unittest.main()
