import io, json, os, unittest, urllib.error
from unittest.mock import patch, MagicMock
import server
A='00000000-0000-4000-8000-000000000001'
B='00000000-0000-4000-8000-000000000002'
C='00000000-0000-4000-8000-000000000003'
ENTITY={'entity_id':B,'name':'Fixture only','subtype':'urn:entity:movie','properties':{'description':'Fixture description','websites':['javascript:alert(1)','https://example.com']},'query':{'affinity':0.42}}
class AdapterTests(unittest.TestCase):
    def setUp(self):
        server._cache.clear();server._calls.clear()
    def test_response_variants_and_metadata(self):
        for body in ({'results':[ENTITY]},{'results':{'entities':[ENTITY]}},{'entities':[ENTITY]}):
            row=server.extract_results(body)[0]
            self.assertEqual(row['id'],B);self.assertEqual(row['description'],'Fixture description');self.assertEqual(row['website'],'https://example.com');self.assertEqual(row['affinity'],.42)
    def test_unverified_ids_and_missing_names_removed(self):
        self.assertEqual(server.extract_results({'results':[{'name':'Invalid','id':'made-up'},{'entity_id':A}]}),[])
    def test_deduplicates_and_does_not_invent_scores(self):
        e={**ENTITY,'query':{}}
        rows=server.extract_results({'results':[e,e]})
        self.assertEqual(len(rows),1);self.assertIsNone(rows[0]['affinity'])
    def test_nonfinite_scores_removed(self):
        self.assertIsNone(server.extract_results({'results':[{**ENTITY,'query':{'affinity':float('nan')}}]})[0]['affinity'])
    def test_search_uses_search_not_insights(self):
        with patch('server.qloo_request',return_value=({'results':[ENTITY]},False)) as call:
            result=server.search_entities({'query':'千と千尋の神隠し','category':'urn:entity:movie'})
        call.assert_called_once_with('/search',{'query':'千と千尋の神隠し','types':'urn:entity:movie','take':'6'})
        self.assertEqual(result['results'][0]['id'],B)
    def test_recommend_resolved_ids_location_and_exclusions(self):
        with patch('server.qloo_request',return_value=({'results':{'entities':[ENTITY]}},False)) as call:
            result=server.recommend({'seeds':[A],'exclude':[C],'category':'urn:entity:place','location':'Los Angeles'})
        path,params=call.call_args.args
        self.assertEqual(path,'/v2/insights/');self.assertEqual(params['signal.interests.entities'],A)
        self.assertEqual(params['filter.exclude.entities'],A+','+C);self.assertEqual(params['filter.location.query'],'Los Angeles')
        self.assertNotIn('signal.interests.tags',params);self.assertEqual(result['provenance']['seeds'],[A])
    def test_excluded_results_not_leaked(self):
        with patch('server.qloo_request',return_value=({'results':[ENTITY]},False)):
            self.assertEqual(server.recommend({'seeds':[A],'exclude':[B]})['results'],[])
    def test_no_location_parameter_for_nonplace(self):
        with patch('server.qloo_request',return_value=({'results':[]},False)) as call:
            server.recommend({'seeds':[A],'category':'urn:entity:book','location':'Boston'})
        self.assertNotIn('filter.location.query',call.call_args.args[1])
    def test_invalid_ids_and_limits_before_api(self):
        for payload in ({'seeds':[]},{'seeds':['fictional']},{'seeds':[A]*6},{'seeds':[A],'exclude':[B]*25},{'seeds':[A],'category':[]}):
            with patch('server.qloo_request') as call:
                with self.assertRaises(server.ApiError):server.recommend(payload)
                call.assert_not_called()
    def test_missing_key_and_host_guard(self):
        for env in ({'QLOO_API_KEY':''},{'QLOO_API_KEY':'test-only','QLOO_API_BASE':'https://example.com'}):
            with patch.dict(os.environ,env,clear=True),patch('urllib.request.build_opener') as op:
                with self.assertRaises(server.ApiError):server.qloo_request('/search',{'query':'test'})
                op.assert_not_called()
    def test_headers_timeout_cache_and_exact_endpoint(self):
        response=MagicMock();response.__enter__.return_value=response;response.read.return_value=json.dumps({'results':[ENTITY]}).encode()
        opener=MagicMock();opener.open.return_value=response
        with patch.dict(os.environ,{'QLOO_API_KEY':'test-only'},clear=True),patch('urllib.request.build_opener',return_value=opener):
            a=server.qloo_request('/search',{'query':'A & B','types':'urn:entity:movie','take':'6'})
            b=server.qloo_request('/search',{'query':'A & B','types':'urn:entity:movie','take':'6'})
        request=opener.open.call_args.args[0]
        self.assertTrue(request.full_url.startswith('https://hackathon.api.qloo.com/search?'));self.assertIn('query=A+%26+B',request.full_url)
        self.assertEqual(request.get_header('X-api-key'),'test-only');self.assertEqual(opener.open.call_args.kwargs['timeout'],12)
        self.assertFalse(a[1]);self.assertTrue(b[1]);self.assertEqual(opener.open.call_count,1)
    def test_upstream_errors_are_safe_and_not_retried(self):
        for status,expected in ((401,503),(403,503),(429,429),(500,502),(400,422)):
            with self.subTest(status=status),patch.dict(os.environ,{'QLOO_API_KEY':'test-only'},clear=True),patch('urllib.request.build_opener') as op:
                op.return_value.open.side_effect=urllib.error.HTTPError('https://hackathon.api.qloo.com/search',status,'secret upstream message',{},io.BytesIO(b'secret'))
                with self.assertRaises(server.ApiError) as err:server.qloo_request('/search',{'query':str(status)})
                self.assertEqual(err.exception.status,expected);self.assertNotIn('secret',str(err.exception));self.assertEqual(op.return_value.open.call_count,1)
    def test_no_redirect_credential_forwarding(self):
        self.assertIsNone(server.NoRedirect().redirect_request(None,None,302,'',{},'https://example.com'))
    def test_agent_schema_has_bounded_tools(self):
        paths=server.tool_schema()['paths'];self.assertEqual(len(paths),2)
        self.assertEqual(paths['/api/recommend']['post']['requestBody']['content']['application/json']['schema']['properties']['seeds']['maxItems'],5)
if __name__=='__main__':unittest.main()
