"""Portable entry point: validate installation and reserve the listening socket."""
import argparse
import importlib
import json
import os
from pathlib import Path
import socket
import sys
import threading
import urllib.request
import webbrowser

ROOT = Path(__file__).resolve().parent


class StartupError(Exception):
    """A diagnostic safe to show without printing configuration secrets."""


def check_installation(root=ROOT):
    if sys.version_info < (3, 11):
        raise StartupError('Can Python 3.11 tro len. Hay dung runtime di kem Mambot 1.1.zip.')
    required = ('backend/app.py', 'static/index.html', 'static/js/app.view.js',
                'static/style.css', 'static/student.css', 'static/huit-logo.jpg',
                'static/js/features/planner/planner.controller.js',
                'static/js/features/chat/chat.controller.js', 'static/js/features/chat/chat.api.js',
                'static/js/features/library/library.controller.js', 'static/js/features/library/library.api.js',
                'static/js/features/system/system.controller.js', 'static/js/features/system/system.api.js',
                'static/js/shared/http.js', 'data/knowledge.json', 'registry/lock.json')
    missing = [name for name in required if not (root / name).is_file()]
    if missing:
        raise StartupError('Giai nen chua day du. Thieu: ' + ', '.join(missing) +
                           '. Hay Extract All toan bo ZIP vao mot thu muc moi.')
    for name in ('fastapi', 'uvicorn', 'jsonschema', 'pymongo', 'httpx'):
        try:
            importlib.import_module(name)
        except (ImportError, OSError) as error:
            raise StartupError('Khong nap duoc thu vien ' + name +
                               '. Hay giai nen lai toan bo Mambot 1.1.zip (Windows 64-bit).') from error


def reserve_listener(host, port_value):
    """Keep the socket open to avoid a check-then-bind race."""
    explicit = port_value is not None
    if explicit:
        try:
            port = int(port_value)
        except (TypeError, ValueError):
            raise StartupError('PORT phai la so nguyen tu 1 den 65535.') from None
        if not 1 <= port <= 65535:
            raise StartupError('PORT phai nam trong khoang 1 den 65535.')
    else:
        port = 8000
    for candidate in range(port, port + (1 if explicit else 10)):
        listener = socket.socket(socket.AF_INET6 if ':' in host else socket.AF_INET, socket.SOCK_STREAM)
        try:
            if os.name == 'nt':
                listener.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
            listener.bind((host, candidate))
            listener.listen(128)
            return listener
        except OSError:
            listener.close()
    raise StartupError('Khong mo duoc cong ' + (str(port) if explicit else '8000-8009') +
                       '. Kiem tra MAMBOT_HOST/PORT hoac dung mot cong khac.')


def browser_when_ready(url, stopped):
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    for _ in range(60):
        if stopped.is_set():
            return
        try:
            with opener.open(url + 'api/health', timeout=1) as response:
                body = json.loads(response.read(16384))
            if body.get('name') == 'Mambot' and body.get('status') == 'ok':
                webbrowser.open(url)
                return
        except Exception:
            pass
        stopped.wait(.5)


def main(argv=None):
    parser = argparse.ArgumentParser(description='Mambot 1.1')
    parser.add_argument('--check', action='store_true')
    parser.add_argument('--open-browser', action='store_true')
    parser.add_argument('--no-browser', action='store_true')
    args = parser.parse_args(argv)
    os.chdir(ROOT)
    try:
        check_installation()
        if args.check:
            from backend.config import settings
            from backend.operations.knowledge import KnowledgeOperations
            from backend.services.library import LibraryService
            operations = KnowledgeOperations(settings)
            try:
                status = LibraryService(operations, settings).health('startup-check')
            finally:
                operations.close()
            if status['status'] != 'ok':
                raise StartupError('Kho tri thuc chua co du lieu.')
            print('PASS: Mambot 1.1 - runtime, tep ung dung, authority va ' + str(status['records']) + ' tai lieu.')
            return 0
        import uvicorn
        host = os.getenv('MAMBOT_HOST', '127.0.0.1')
        listener = reserve_listener(host, os.getenv('PORT'))
        port = listener.getsockname()[1]
        display_host = '127.0.0.1' if host == '0.0.0.0' else ('[::1]' if host == '::' else ('['+host+']' if ':' in host else host))
        url = f'http://{display_host}:{port}/mambot/'
        stopped = threading.Event()
        try:
            trusted = os.getenv('MAMBOT_TRUSTED_PROXIES', '')
            config = uvicorn.Config('backend.app:app', host=host, port=port,
                                    proxy_headers=bool(trusted), forwarded_allow_ips=trusted)
            print('Mambot 1.1: ' + url, flush=True)
            print('Giu cua so nay mo. Nhan Ctrl+C de dung.', flush=True)
            if args.open_browser and not args.no_browser:
                threading.Thread(target=browser_when_ready, args=(url, stopped), daemon=True).start()
            server = uvicorn.Server(config)
            server.run(sockets=[listener])
            return 0 if server.started else 1
        finally:
            stopped.set()
            listener.close()
    except KeyboardInterrupt:
        return 0
    except Exception as error:
        message = str(error) if isinstance(error, StartupError) else 'Kiem tra goi giai nen va cau hinh may chu; chay KIEM_TRA_MAMBOT.cmd.'
        print('LOI KHOI DONG: ' + message, file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
