import json
import ssl
from urllib.error import HTTPError
from urllib.parse import urlparse
from urllib.request import Request, HTTPRedirectHandler, HTTPSHandler, ProxyHandler, build_opener

class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, message, headers, newurl):
        return None

class CentralClient:
    def __init__(self, base_url, agent, token, allow_loopback_http=False):
        parsed = urlparse(base_url)
        if parsed.username or parsed.password or parsed.query or parsed.fragment:
            raise ValueError('URL central inválida.')
        if parsed.scheme != 'https' and not (allow_loopback_http and parsed.scheme == 'http' and parsed.hostname in ('127.0.0.1', 'localhost', '::1')):
            raise ValueError('HTTPS obligatorio; HTTP solo se permite en loopback local explícito.')
        self.base_url, self.agent, self.token = base_url.rstrip('/'), agent, token
        self.context = ssl.create_default_context()
        self.opener = build_opener(ProxyHandler({}), HTTPSHandler(context=self.context), NoRedirect())

    def call(self, endpoint, body):
        request = Request(self.base_url + '/api/agent/' + endpoint + '/',
            data=json.dumps(body).encode(), headers={'Content-Type': 'application/json',
                'Authorization': 'Bearer ' + self.token, 'X-Agent-ID': self.agent}, method='POST')
        try:
            with self.opener.open(request, timeout=10) as response:
                return json.load(response)
        except HTTPError as exc:
            if exc.code == 409: return {'conflict': True}
            raise RuntimeError('La API central rechazó la solicitud.') from None

    def claim(self): return self.call('claim', {})['task']
    def validate(self, item):
        return self.call('validate', {'task': item['task'], 'attempt': item['attempt']})
    def report(self, item, report):
        return self.call('report', {'task': item['task'], 'attempt': item['attempt'], 'report': report})
