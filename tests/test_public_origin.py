import unittest

from backend.infrastructure.http_boundaries import HttpBoundaries, RateLimiter, parse_allowed_origins


class AllowedOriginTests(unittest.TestCase):
    def test_config_accepts_only_explicit_https_origins(self):
        self.assertEqual(parse_allowed_origins('https://mambot.netlify.app, https://preview.netlify.app'),
                         {'https://mambot.netlify.app', 'https://preview.netlify.app'})
        for value in ('*', 'http://mambot.netlify.app', 'https://evil.example/path',
                      'https://user:pass@evil.example', 'https://evil.example?x=1',
                      'https://evil.example:443', 'https://[',
                      ','.join(f'https://site{i}.example' for i in range(9))):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    parse_allowed_origins(value)


class AllowedOriginTransportTests(unittest.IsolatedAsyncioTestCase):
    async def exercise(self, origin, allowed):
        output = []
        calls = []

        async def endpoint(scope, receive, send):
            calls.append((await receive())['body'])
            await send({'type': 'http.response.start', 'status': 200, 'headers': []})
            await send({'type': 'http.response.body', 'body': b'ok'})

        async def receive():
            return {'type': 'http.request', 'body': b'{}', 'more_body': False}

        async def send(message):
            output.append(message)

        scope = {'type': 'http', 'method': 'POST', 'path': '/mambot/api/chat',
                 'scheme': 'https', 'server': ('mambot-api.onrender.com', 443),
                 'client': ('visitor', 1), 'query_string': b'',
                 'headers': [(b'host', b'mambot-api.onrender.com'),
                             (b'origin', origin.encode()),
                             (b'content-type', b'application/json')]}
        await HttpBoundaries(endpoint, RateLimiter(), allowed_origins=allowed)(scope, receive, send)
        return output[0]['status'], calls

    async def test_netlify_origin_is_allowed_when_configured(self):
        status, calls = await self.exercise('https://mambot.netlify.app', ['https://mambot.netlify.app'])
        self.assertEqual((status, calls), (200, [b'{}']))

    async def test_other_origin_remains_forbidden(self):
        status, calls = await self.exercise('https://evil.example', ['https://mambot.netlify.app'])
        self.assertEqual((status, calls), (403, []))

    async def test_backend_same_origin_is_still_allowed(self):
        status, calls = await self.exercise('https://mambot-api.onrender.com', [])
        self.assertEqual((status, calls), (200, [b'{}']))
