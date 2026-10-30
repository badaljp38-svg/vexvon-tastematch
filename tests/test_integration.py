"""HTTP tests use test-only upstream fixtures; they are not evidence of live Qloo calls."""
import json, os, threading, unittest, urllib.request, urllib.error
from unittest.mock import patch
from http.server import ThreadingHTTPServer
from server import Handler
A='00000000-0000-4000-8000-000000000001'
B='00000000-0000-4000-8000-000000000002'
class HttpTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
        threading.Thread(target=cls.server.serve_forever,daemon=True).start()
        cls.base=f'http://127.0.0.1:{cls.server.server_address[1]}'
    @classmethod
    def tearDownClass(cls):cls.server.shutdown();cls.server.server_close()
    def post(self,path,data,headers=None):
        req=urllib.request.Request(self.base+path,data=json.dumps(data).encode(),headers=headers or {'Content-Type':'application/json'})
        try:
            with urllib.request.urlopen(req) as r:return r.status,json.load(r)
        except urllib.error.HTTPError as e:return e.code,json.load(e)
    def test_search_to_recommend_http_contract(self):
        fixture={'results':[{'entity_id':A,'name':'Test favorite'}]}
        with patch('server.qloo_request',return_value=(fixture,False)):
            status,result=self.post('/api/search',{'query':'Favorite','category':'urn:entity:movie'})
        self.assertEqual(status,200)
        with patch('server.qloo_request',return_value=({'results':{'entities':[{'entity_id':B,'name':'Test recommendation'}]}},False)):
            status,matches=self.post('/api/recommend',{'seeds':[result['results'][0]['id']],'category':'urn:entity:book'})
        self.assertEqual(status,200);self.assertEqual(matches['results'][0]['id'],B);self.assertEqual(len(matches['trace']),3)
    def test_missing_credential_never_substitutes_samples(self):
        with patch.dict(os.environ,{'QLOO_API_KEY':''}):
            status,obj=self.post('/api/recommend',{'seeds':[A]})
        self.assertEqual(status,503);self.assertEqual(obj['code'],'key_missing');self.assertNotIn('results',obj)
    def test_invalid_requests(self):
        for path,payload in (('/api/search',[]),('/api/search',{'query':'x'}),('/api/recommend',{'seeds':['fake']})):
            self.assertEqual(self.post(path,payload)[0],400)
    def test_cross_site_and_content_type_rejected(self):
        self.assertEqual(self.post('/api/search',{'query':'Test'},{'Content-Type':'text/plain'})[0],415)
        self.assertEqual(self.post('/api/search',{'query':'Test'},{'Content-Type':'application/json','Origin':'https://evil.example'})[0],403)
    def test_public_routes_and_security_headers(self):
        for path in ('/','/static/app.js','/static/style.css','/api/openapi.json','/api/status'):
            with urllib.request.urlopen(self.base+path) as r:
                self.assertEqual(r.status,200);self.assertEqual(r.headers['X-Content-Type-Options'],'nosniff');self.assertIn("frame-ancestors 'none'",r.headers['Content-Security-Policy'])
    def test_private_files_not_served(self):
        for path in ('/.env','/server.py','/README.md','/static/../server.py'):
            with self.assertRaises(urllib.error.HTTPError) as e:urllib.request.urlopen(self.base+path)
            self.assertEqual(e.exception.code,404)
    def test_status_does_not_claim_live_validation(self):
        with patch.dict(os.environ,{'QLOO_API_KEY':'test-only'}),urllib.request.urlopen(self.base+'/api/status') as r:
            d=json.load(r)
        self.assertTrue(d['api_key_configured']);self.assertEqual(d['live_validation'],'not asserted by configuration');self.assertNotIn('test-only',json.dumps(d))
if __name__=='__main__':unittest.main()
