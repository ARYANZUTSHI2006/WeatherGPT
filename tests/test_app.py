import unittest, json
from types import SimpleNamespace
from urllib.parse import urlsplit
from unittest.mock import patch
from app import app

class WeatherTests(unittest.TestCase):
    def setUp(self): self.client=self
    def get(self,url):
        u=urlsplit(url); state={}
        def start(status,headers): state['status']=int(status.split()[0]); state['headers']=dict(headers)
        data=b''.join(app({'PATH_INFO':u.path,'QUERY_STRING':u.query,'REQUEST_METHOD':'GET'},start))
        return SimpleNamespace(status_code=state['status'],data=data,json=json.loads(data) if state['headers']['Content-Type'].startswith('application/json') else None)
    def test_home(self):
        r=self.client.get('/'); self.assertEqual(r.status_code,200); self.assertIn(b'Atmos',r.data)
    def test_health(self): self.assertEqual(self.client.get('/api/health').json['status'],'ok')
    def test_search_empty(self): self.assertEqual(self.client.get('/api/search?q=a').json,{'results':[]})
    @patch('app.fetch',return_value={'results':[{'name':'Delhi'}]})
    def test_search(self,m): self.assertEqual(self.client.get('/api/search?q=Delhi').json['results'][0]['name'],'Delhi')
    def test_invalid(self):
        for path in ['weather','air','alerts']:
            self.assertEqual(self.client.get('/api/'+path+'?lat=100&lon=0').status_code,400)
    @patch('app.fetch',return_value={'current':{'temperature_2m':24}})
    def test_weather(self,m): self.assertEqual(self.client.get('/api/weather?lat=28&lon=77').json['current']['temperature_2m'],24)
    @patch('app.fetch',return_value={'current':{'us_aqi':45}})
    def test_air(self,m): self.assertEqual(self.client.get('/api/air?lat=28&lon=77').json['current']['us_aqi'],45)
    def test_non_us_alerts(self): self.assertEqual(self.client.get('/api/alerts?lat=28&lon=77&country=IN').json['status'],'unknown')
    @patch('app.fetch',return_value={'features':[{'properties':{'event':'Flood Warning','instruction':'Follow officials'}}]})
    def test_us_alerts(self,m): self.assertEqual(self.client.get('/api/alerts?lat=40&lon=-74&country=US').json['alerts'][0]['event'],'Flood Warning')
    @patch('app.fetch',side_effect=TimeoutError)
    def test_provider_failure(self,m):
        for path in ['search?q=Delhi','weather?lat=28&lon=77','air?lat=28&lon=77','alerts?lat=40&lon=-74&country=US']:
            self.assertEqual(self.client.get('/api/'+path).status_code,502)

if __name__=='__main__': unittest.main()
