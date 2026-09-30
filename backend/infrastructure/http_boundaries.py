"""ASGI transport controls; no private Request._body mutation or business logic."""
import asyncio
import logging
import threading
import time
from collections import OrderedDict, deque
from uuid import uuid4
from starlette.datastructures import Headers, MutableHeaders, URL
from starlette.responses import JSONResponse

LOGGER = logging.getLogger('mambot.http')
MAX_BODY_BYTES = 49152
SECURITY_HEADERS = {
    'X-Content-Type-Options': 'nosniff',
    'X-Frame-Options': 'SAMEORIGIN',
    'Referrer-Policy': 'strict-origin-when-cross-origin',
    'Permissions-Policy': 'camera=(), microphone=(), geolocation=()',
    'Content-Security-Policy': "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self'; font-src 'self'; base-uri 'self'; form-action 'self'; frame-ancestors 'self'",
}

class RateLimiter:
    def __init__(self):
        self.windows = OrderedDict()
        self.lock = threading.Lock()

    def allow(self, ip):
        now = time.monotonic()
        with self.lock:
            bucket = self.windows.setdefault(ip, deque())
            self.windows.move_to_end(ip)
            while bucket and now - bucket[0] >= 60:
                bucket.popleft()
            allowed = len(bucket) < 60
            if allowed:
                bucket.append(now)
            while len(self.windows) > 4096:
                self.windows.popitem(last=False)
            return allowed

class HttpBoundaries:
    def __init__(self, app, limiter, body_timeout=10, max_chats=4):
        self.app = app
        self.limiter = limiter
        self.body_timeout = body_timeout
        self.chat_slots = threading.BoundedSemaphore(max_chats)

    async def __call__(self, scope, receive, send):
        if scope['type'] != 'http':
            return await self.app(scope, receive, send)
        request_id = str(uuid4())
        scope.setdefault('state', {})['request_id'] = request_id
        headers = Headers(scope=scope)
        started = False
        path = scope['path']
        root_path = scope.get('root_path', '').rstrip('/')
        if root_path and (path == root_path or path.startswith(root_path + '/')):
            path = path[len(root_path):]
        is_api = path.startswith(('/api/', '/mambot/api/'))
        is_chat = scope['method'] == 'POST' and path in (
            '/api/chat', '/api/chat-stream', '/mambot/api/chat', '/mambot/api/chat-stream')
        held_chat_slot = False

        async def protected_send(message):
            nonlocal started
            if message['type'] == 'http.response.start':
                started = True
                output = MutableHeaders(scope=message)
                output.update(SECURITY_HEADERS)
                output['X-Request-ID'] = request_id
                output['Cache-Control'] = 'no-store' if is_api else 'no-cache'
            await send(message)

        async def reject(status, detail, extra=None):
            result = JSONResponse({'detail': detail, 'request_id': request_id},
                                  status_code=status, headers=extra)
            await result(scope, receive, protected_send)

        try:
            if is_api:
                ip = (scope.get('client') or ('unknown', 0))[0]
                if not self.limiter.allow(ip):
                    return await reject(429, 'Bạn thao tác quá nhanh. Thử lại sau một phút.', {'Retry-After': '60'})
            app_receive = receive
            if scope['method'] == 'POST':
                origin = headers.get('origin')
                url = URL(scope=scope)
                expected_origin = f'{url.scheme}://{url.netloc}'
                if origin and origin != expected_origin:
                    return await reject(403, 'Nguồn yêu cầu không hợp lệ.')
                if headers.get('content-type', '').split(';')[0].strip().lower() != 'application/json':
                    return await reject(415, 'Yêu cầu phải dùng JSON.')
                length = headers.get('content-length')
                if length is not None:
                    if not length.isdecimal():
                        return await reject(400, 'Độ dài yêu cầu không hợp lệ.')
                    if len(length) > 10 or int(length) > MAX_BODY_BYTES:
                        return await reject(413, 'Yêu cầu quá lớn.')
                body = bytearray()
                async with asyncio.timeout(self.body_timeout):
                    while True:
                        message = await receive()
                        if message['type'] == 'http.disconnect':
                            return
                        if message['type'] != 'http.request':
                            return await reject(400, 'Yêu cầu không hợp lệ.')
                        chunk = message.get('body', b'')
                        if len(body) + len(chunk) > MAX_BODY_BYTES:
                            return await reject(413, 'Yêu cầu quá lớn.')
                        body.extend(chunk)
                        if not message.get('more_body', False):
                            break
                delivered = False
                async def replay_body():
                    nonlocal delivered
                    if not delivered:
                        delivered = True
                        return {'type': 'http.request', 'body': bytes(body), 'more_body': False}
                    return await receive()
                app_receive = replay_body
            if is_chat:
                held_chat_slot = self.chat_slots.acquire(blocking=False)
                if not held_chat_slot:
                    return await reject(503, 'Máy chủ đang bận xử lý câu hỏi. Vui lòng thử lại.', {'Retry-After': '2'})
            await self.app(scope, app_receive, protected_send)
        except TimeoutError:
            if not started:
                await reject(408, 'Quá thời gian gửi yêu cầu. Vui lòng thử lại.')
        except Exception as error:
            # Never log exception text, request bodies, provider credentials or DB URIs.
            LOGGER.error('request_failed request_id=%s error_type=%s', request_id, type(error).__name__)
            if not started:
                await reject(500, 'Máy chủ gặp lỗi khi xử lý. Vui lòng thử lại hoặc cung cấp mã yêu cầu để kiểm tra.')
            else:
                raise
        finally:
            if held_chat_slot:
                self.chat_slots.release()
