"""TasteMatch: bounded server-side Qloo tools; no external Python dependencies."""
import json, math, os, threading, time, urllib.error, urllib.parse, urllib.request, uuid
from collections import OrderedDict
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
ROOT = Path(__file__).resolve().parent
TYPES = {'urn:entity:' + n for n in ('place', 'movie', 'artist', 'book', 'destination')}
_cache, _calls, _lock = OrderedDict(), [], threading.Lock()

class ApiError(Exception):
    def __init__(self, message, status=400, code='invalid_request'):
        super().__init__(message)
        self.status, self.code = status, code

def plain_text(value, name, minimum=0, maximum=120):
    if not isinstance(value, str): raise ApiError(f'{name} must be text.')
    value = value.strip()
    if not minimum <= len(value) <= maximum or any(ord(c) < 32 for c in value):
        raise ApiError(f'{name} must contain {minimum}–{maximum} readable characters.')
    return value

def entity_ids(value, name, maximum, required=False):
    if not isinstance(value, list) or not (int(required) <= len(value) <= maximum):
        raise ApiError(f'{name} must contain {int(required)}–{maximum} Qloo entity IDs.')
    out = []
    for item in value:
        try:
            if not isinstance(item, str): raise ValueError()
            identifier = str(uuid.UUID(item)).upper()
        except (ValueError, AttributeError):
            raise ApiError(f'{name} requires valid entity IDs from a Qloo search.') from None
        if identifier not in out: out.append(identifier)
    return out

class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None  # Never forward the credential to a redirected host.

def qloo_request(path, params):
    token = os.environ.get('QLOO_API_KEY', '').strip()
    if not token:
        raise ApiError('Live discovery is awaiting the organizer-issued Qloo API key. Explore the clearly labeled sample meanwhile.', 503, 'key_missing')
    base = os.environ.get('QLOO_API_BASE', 'https://hackathon.api.qloo.com').rstrip('/')
    if base != 'https://hackathon.api.qloo.com':
        raise ApiError('The event API host is not configured correctly.', 503, 'configuration_error')
    cache_key, now = (path, tuple(sorted(params.items()))), time.monotonic()
    with _lock:
        cached = _cache.get(cache_key)
        if cached and now - cached[0] < 300:
            _cache.move_to_end(cache_key)
            return cached[1], True
        _calls[:] = [t for t in _calls if now - t < 60]
        if len(_calls) >= 30:
            raise ApiError('This demo is busy. Please wait a minute before trying again.', 429, 'demo_rate_limit')
        _calls.append(now)
    req = urllib.request.Request(base + path + '?' + urllib.parse.urlencode(params), headers={'X-Api-Key': token, 'Accept': 'application/json'})
    try:
        with urllib.request.build_opener(NoRedirect).open(req, timeout=12) as response:
            raw = response.read(2_000_001)
            if len(raw) > 2_000_000: raise ApiError('Qloo returned an oversized response.', 502, 'upstream_response')
            data = json.loads(raw)
    except urllib.error.HTTPError as exc:
        if exc.code == 404 and path == '/search': return {'results': []}, False
        if exc.code in (401, 403): raise ApiError('Qloo did not authorize this demo’s credential. The owner needs to check event access.', 503, 'qloo_auth') from None
        if exc.code == 429: raise ApiError('Qloo’s request limit was reached. Please wait before trying again.', 429, 'qloo_rate_limit') from None
        if exc.code in (400, 422): raise ApiError('Qloo could not match these filters. Check your selected favorites and city, then try again.', 422, 'qloo_query') from None
        raise ApiError('Qloo is unavailable. No substitute results were generated.', 502, 'qloo_unavailable') from None
    except (urllib.error.URLError, TimeoutError, OSError):
        raise ApiError('Qloo did not respond in time. Please try again later.', 504, 'qloo_timeout') from None
    except (ValueError, UnicodeDecodeError):
        raise ApiError('Qloo returned an unreadable response.', 502, 'upstream_response') from None
    if not isinstance(data, dict) or data.get('success') is False:
        raise ApiError('Qloo did not return a successful response.', 502, 'upstream_response')
    with _lock:
        _cache[cache_key] = (now, data)
        _cache.move_to_end(cache_key)
        while len(_cache) > 128: _cache.popitem(last=False)
    return data, False

def safe_url(value):
    if not isinstance(value, str) or len(value) > 1500: return ''
    try:
        p = urllib.parse.urlsplit(value)
        return value if p.scheme == 'https' and p.hostname and not p.username and not p.password else ''
    except ValueError: return ''

def extract_results(data):
    arr = data.get('results', data.get('entities', []))
    if isinstance(arr, dict): arr = arr.get('entities', [])
    if not isinstance(arr, list): return []
    result, seen = [], set()
    for item in arr:
        if not isinstance(item, dict) or not isinstance(item.get('name'), str): continue
        try: identifier = str(uuid.UUID(str(item.get('entity_id') or item.get('id')))).upper()
        except ValueError: continue
        if identifier in seen or not item['name'].strip(): continue
        seen.add(identifier)
        props = item.get('properties') if isinstance(item.get('properties'), dict) else {}
        query = item.get('query') if isinstance(item.get('query'), dict) else {}
        websites = props.get('websites', [])
        website = next((safe_url(v) for v in websites if safe_url(v)), '') if isinstance(websites, list) else ''
        affinity = query.get('affinity')
        if type(affinity) not in (int, float) or not math.isfinite(affinity): affinity = None
        tags = item.get('tags', [])
        result.append({'id': identifier, 'name': item['name'][:180], 'type': str(item.get('subtype', ''))[:60],
            'description': str(props.get('description') or item.get('description') or '')[:600],
            'detail': str(item.get('disambiguation') or props.get('address') or '')[:240],
            'website': website, 'affinity': affinity,
            'tags': [str(t['name'])[:60] for t in tags if isinstance(t, dict) and isinstance(t.get('name'), str)][:4] if isinstance(tags, list) else []})
        if len(result) == 8: break
    return result

def search_entities(payload):
    query = plain_text(payload.get('query'), 'Favorite', 2)
    category = payload.get('category', 'urn:entity:movie')
    if not isinstance(category, str) or category not in TYPES: raise ApiError('Choose a supported category.')
    data, cached = qloo_request('/search', {'query': query, 'types': category, 'take': '6'})
    return {'source': 'qloo', 'cached': cached, 'results': extract_results(data), 'query': query}

def recommend(payload):
    seeds = entity_ids(payload.get('seeds'), 'Favorites', 5, True)
    excluded = entity_ids(payload.get('exclude', []), 'Skipped items', 24)
    category = payload.get('category', 'urn:entity:place')
    if not isinstance(category, str) or category not in TYPES: raise ApiError('Choose a supported category.')
    location = plain_text(payload.get('location', ''), 'City', 0, 100)
    params = {'filter.type': category, 'signal.interests.entities': ','.join(seeds),
        'filter.exclude.entities': ','.join(dict.fromkeys(seeds + excluded)), 'take': '8'}
    if category == 'urn:entity:place' and location: params['filter.location.query'] = location
    data, cached = qloo_request('/v2/insights/', params)
    results = [r for r in extract_results(data) if r['id'] not in seeds + excluded]
    return {'source': 'qloo', 'cached': cached, 'results': results,
        'trace': [{'step': 'Resolve', 'detail': f'{len(seeds)} confirmed Qloo entity ID(s).'},
                  {'step': 'Discover', 'detail': f'Qloo Insights → {category.rsplit(":", 1)[-1]}.'},
                  {'step': 'Refine', 'detail': f'Excluded {len(excluded)} skipped items and your favorites.'}],
        'provenance': {'provider': 'Qloo', 'endpoint': '/v2/insights/', 'seeds': seeds, 'category': category, 'location': location if category == 'urn:entity:place' else '', 'exclude': excluded},
        'note': 'Ranked by Qloo using aggregate cultural affinities. Discovery suggestions are not guarantees about an individual.'}

def tool_schema():
    category = {'type': 'string', 'enum': sorted(TYPES)}
    ids = {'type': 'array', 'items': {'type': 'string', 'format': 'uuid'}}
    schemas = {
      '/api/search': ('searchTasteEntity', 'Resolve a favorite to Qloo entities. Ask the user to confirm ambiguous matches.', ['query', 'category'], {'query': {'type': 'string', 'minLength': 2, 'maxLength': 120}, 'category': category}),
      '/api/recommend': ('discoverTasteMatches', 'Use confirmed Qloo IDs. Refine by excluding skipped IDs. Never invent IDs or results. Maximum one upstream call per invocation.', ['seeds', 'category'], {'seeds': dict(ids, minItems=1, maxItems=5), 'exclude': dict(ids, maxItems=24), 'category': category, 'location': {'type': 'string', 'maxLength': 100}})}
    paths = {}
    for path, (name, description, required, properties) in schemas.items():
        paths[path] = {'post': {'operationId': name, 'description': description,
            'requestBody': {'required': True, 'content': {'application/json': {'schema': {'type': 'object', 'required': required, 'properties': properties, 'additionalProperties': False}}}},
            'responses': {'200': {'description': 'Qloo data with provenance; results may be empty.'}, '400': {'description': 'Invalid input.'}, '429': {'description': 'Rate limited. Do not retry automatically.'}, '503': {'description': 'Event credential unavailable. Stop and inform the user.'}}}}
    return {'openapi': '3.1.0', 'info': {'title': 'Vexvon TasteMatch agent tools', 'version': '0.6.0', 'description': 'Cultural grounding tools. No autonomous LLM is bundled. Never send personal records or credentials.'}, 'paths': paths}

class Handler(BaseHTTPRequestHandler):
    def send_bytes(self, status, body, content_type):
        self.send_response(status)
        for key, value in {'Content-Type': content_type, 'Content-Length': str(len(body)), 'Cache-Control': 'no-store', 'X-Content-Type-Options': 'nosniff', 'Referrer-Policy': 'no-referrer', 'Content-Security-Policy': "default-src 'self'; script-src 'self'; style-src 'self'; connect-src 'self'; img-src 'self' data:; object-src 'none'; base-uri 'none'; frame-ancestors 'none'; form-action 'self'"}.items(): self.send_header(key, value)
        self.end_headers()
        self.wfile.write(body)
    def reply(self, status, data):
        self.send_bytes(status, json.dumps(data, allow_nan=False).encode(), 'application/json; charset=utf-8')
    def do_GET(self):
        path = urllib.parse.urlsplit(self.path).path
        if path == '/api/status': return self.reply(200, {'project': 'Vexvon TasteMatch', 'version': '0.6.0', 'api_key_configured': bool(os.environ.get('QLOO_API_KEY', '').strip()), 'integration': 'search-then-insights', 'live_validation': 'not asserted by configuration'})
        if path == '/api/openapi.json': return self.reply(200, tool_schema())
        routes = {'/': ('static/index.html', 'text/html'), '/static/app.js': ('static/app.js', 'text/javascript'), '/static/style.css': ('static/style.css', 'text/css')}
        if path not in routes: return self.reply(404, {'error': 'Not found'})
        file, kind = routes[path]
        self.send_bytes(200, (ROOT / file).read_bytes(), kind + '; charset=utf-8')
    def do_POST(self):
        path = urllib.parse.urlsplit(self.path).path
        if path not in ('/api/search', '/api/recommend'): return self.reply(404, {'error': 'Not found'})
        if self.headers.get('Content-Type', '').split(';')[0].strip() != 'application/json': return self.reply(415, {'error': 'Send application/json.'})
        origin = self.headers.get('Origin')
        if origin and urllib.parse.urlsplit(origin).netloc != self.headers.get('Host'): return self.reply(403, {'error': 'Cross-site browser requests are not supported.'})
        try:
            length = int(self.headers.get('Content-Length', '0'))
            if not 1 <= length <= 8192: return self.reply(413, {'error': 'Request is empty or too large.'})
            payload = json.loads(self.rfile.read(length))
            if not isinstance(payload, dict): raise ApiError('Expected a JSON object.')
            self.reply(200, search_entities(payload) if path == '/api/search' else recommend(payload))
        except ApiError as exc: self.reply(exc.status, {'error': str(exc), 'code': exc.code})
        except (ValueError, UnicodeDecodeError): self.reply(400, {'error': 'Invalid JSON request.'})
        except Exception: self.reply(500, {'error': 'The request could not be completed. Please try again.'})
    def log_message(self, format, *args): pass

if __name__ == '__main__':
    ThreadingHTTPServer((os.environ.get('BIND_HOST', '127.0.0.1'), int(os.environ.get('PORT', '8000'))), Handler).serve_forever()
