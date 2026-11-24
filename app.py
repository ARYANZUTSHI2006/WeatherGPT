import json, os, time, threading
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from pathlib import Path
from urllib.parse import parse_qs
from wsgiref.simple_server import make_server, WSGIServer
from socketserver import ThreadingMixIn

ROOT = Path(__file__).resolve().parent
ROUTES = {}
def route(path):
    def register(fn):
        ROUTES[path] = fn
        return fn
    return register
def jsonify(**kwargs): return kwargs

class ThreadedServer(ThreadingMixIn, WSGIServer):
    daemon_threads = True

CACHE = {}; LOCK = threading.Lock()

def fetch(url, params=None, ttl=300):
    url += ('?' + urlencode(params)) if params else ''
    with LOCK:
        old = CACHE.get(url)
        if old and time.monotonic()-old[0]<ttl: return old[1]
    with urlopen(Request(url, headers={'User-Agent':'AtmosWeather/1.0 (student weather dashboard)','Accept':'application/json'}), timeout=12) as response:
        data=json.load(response)
    with LOCK:
        if len(CACHE)>512: CACHE.clear()
        CACHE[url]=(time.monotonic(),data)
    return data

def coordinates(args):
    lat=float(args['lat']); lon=float(args['lon'])
    if not (-90<=lat<=90 and -180<=lon<=180): raise ValueError('Invalid coordinates')
    return round(lat,4),round(lon,4)

@route('/')
def home(args): return (ROOT/'templates/index.html').read_bytes(),200,'text/html; charset=utf-8'

@route('/api/search')
def search(args):
    q=args.get('q','').strip()[:100]
    if len(q)<2: return jsonify(results=[])
    try: return jsonify(results=fetch('https://geocoding-api.open-meteo.com/v1/search',{'name':q,'count':8,'language':'en','format':'json'},3600).get('results',[]))
    except Exception: return jsonify(error='City search provider unavailable. Try again.'),502

@route('/api/weather')
def weather(args):
    try: lat,lon=coordinates(args)
    except (ValueError,KeyError): return jsonify(error='Valid latitude and longitude required.'),400
    params={'latitude':lat,'longitude':lon,'timezone':'auto','forecast_days':7,'current':'temperature_2m,relative_humidity_2m,apparent_temperature,is_day,precipitation,weather_code,wind_speed_10m,wind_direction_10m','hourly':'temperature_2m,precipitation_probability,weather_code','daily':'weather_code,temperature_2m_max,temperature_2m_min,sunrise,sunset,uv_index_max,precipitation_probability_max,wind_speed_10m_max'}
    try: return fetch('https://api.open-meteo.com/v1/forecast',params)
    except Exception: return jsonify(error='Weather provider unavailable. Refresh to try again.'),502

@route('/api/air')
def air(args):
    try: lat,lon=coordinates(args)
    except (ValueError,KeyError): return jsonify(error='Invalid coordinates.'),400
    try: return fetch('https://air-quality-api.open-meteo.com/v1/air-quality',{'latitude':lat,'longitude':lon,'current':'us_aqi,pm2_5,pm10','timezone':'auto'})
    except Exception: return jsonify(error='Air quality data unavailable.'),502

@route('/api/alerts')
def alerts(args):
    try: lat,lon=coordinates(args)
    except (ValueError,KeyError): return jsonify(error='Invalid coordinates.'),400
    country=args.get('country','').upper()
    if country!='US': return jsonify(status='unknown',alerts=[],message='Official alert feed not integrated for this location. Check your local weather authority.')
    try:
        data=fetch('https://api.weather.gov/alerts/active',{'point':f'{lat},{lon}'},60)
        return jsonify(status='available',alerts=[{k:f.get('properties',{}).get(k) for k in ('event','headline','severity','description','instruction','expires')} for f in data.get('features',[])])
    except Exception: return jsonify(status='unknown',alerts=[],message='Official alert feed unavailable. Check the weather authority.'),502

@route('/api/health')
def health(args): return jsonify(status='ok')

def app(environ, start_response):
    path=environ.get('PATH_INFO','/')
    args={k:v[0] for k,v in parse_qs(environ.get('QUERY_STRING','')).items()}
    if environ.get('REQUEST_METHOD')!='GET': result=({'error':'Method not allowed'},405)
    elif path in ROUTES: result=ROUTES[path](args)
    elif path in ('/static/style.css','/static/app.js'):
        result=((ROOT/path.lstrip('/')).read_bytes(),200,'text/css; charset=utf-8' if path.endswith('.css') else 'application/javascript; charset=utf-8')
    else: result=({'error':'Not found'},404)
    if isinstance(result,tuple):
        body,status,*types=result
    else: body,status,types=result,200,[]
    if not isinstance(body,bytes): body=json.dumps(body,ensure_ascii=False).encode('utf-8')
    from http import HTTPStatus
    start_response(f'{status} {HTTPStatus(status).phrase}', [('Content-Type',types[0] if types else 'application/json; charset=utf-8'),('Content-Length',str(len(body))),('X-Content-Type-Options','nosniff')])
    return [body]

if __name__=='__main__':
    port=int(os.getenv('PORT','5000'))
    print(f'Atmos running on http://localhost:{port}',flush=True)
    with make_server('0.0.0.0',port,app,server_class=ThreadedServer) as server: server.serve_forever()
