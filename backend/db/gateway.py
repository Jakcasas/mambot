"""Fail-closed operation authority, pinned independently of request data."""
import hashlib
import json
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4
from jsonschema import Draft202012Validator
from backend.config import ROOT
from backend.errors import AuthorityError
from backend.db.store import Store

def checksum(authority):
    payload = {k: v for k, v in authority.items() if k != 'checksum'}
    return 'sha256:' + hashlib.sha256(json.dumps(payload, ensure_ascii=False, sort_keys=True,
                                              separators=(',', ':'), allow_nan=False).encode()).hexdigest()

class RegisteredGateway:
    def __init__(self, settings, registry=None, store=None):
        self.directory = Path(registry or ROOT / 'registry')
        self.pins = json.loads((self.directory / 'lock.json').read_text(encoding='utf-8'))
        self.store = store or Store(settings)
        self.audit_path = settings.audit_path
        self.audit_lock = threading.Lock()

    def close(self):
        self.store.close()

    def resolve(self, key):
        if key not in self.pins:
            raise AuthorityError('Unknown operation')
        pin = self.pins[key]
        op = json.loads((self.directory / f"{key}@{pin['version']}.json").read_text(encoding='utf-8'))
        if op['operationKey'] != key or op['version'] != pin['version']:
            raise AuthorityError('Identity mismatch')
        if op.get('checksum') != pin['checksum'] or checksum(op) != pin['checksum']:
            raise AuthorityError('Checksum mismatch')
        if op.get('status') != 'active' or op.get('type') != 'read' or op.get('mutationMode') != 'readOnly':
            raise AuthorityError('Authority is not active read-only')
        if op.get('allowedCollections') != ['huit_kb'] or op.get('sourceCollection') != 'huit_kb':
            raise AuthorityError('Collection denied')
        limits = op['limits']
        if not (0 < limits['maxTimeMS'] <= 8000 and 0 < limits['maxResults'] <= 100
                and 0 < limits['maxOutputBytes'] <= 524288):
            raise AuthorityError('Cost policy violation')
        return op

    def audit(self, record):
        self.audit_path.parent.mkdir(parents=True, exist_ok=True)
        with self.audit_lock, self.audit_path.open('a', encoding='utf-8') as out:
            out.write(json.dumps(record, ensure_ascii=False, allow_nan=False) + '\n')

    def execute(self, key, params, request_id=None):
        start = time.monotonic(); outcome = 'denied'; count = 0
        try:
            op = self.resolve(key)
            # JSON Schema considers NaN a number in Python; reject it explicitly.
            json.dumps(params, allow_nan=False)
            Draft202012Validator(op['parameters']).validate(params)
            result = self.store.read(op, params)
            if (time.monotonic() - start) * 1000 > op['limits']['maxTimeMS']:
                raise AuthorityError('Time budget exceeded')
            if len(result) > op['limits']['maxResults']:
                raise AuthorityError('Result count exceeded')
            if len(json.dumps(result, ensure_ascii=False, allow_nan=False).encode()) > op['limits']['maxOutputBytes']:
                raise AuthorityError('Output byte budget exceeded')
            Draft202012Validator(op['outputSchema']).validate(result)
            count = len(result); outcome = 'allowed'
            return result
        finally:
            # Fail closed if audit storage is unavailable; no question, vector or secret is logged.
            self.audit({'at': datetime.now(timezone.utc).isoformat(), 'request_id': request_id or str(uuid4()),
                        'principal': 'public-reader', 'operation': key, 'authority': self.pins.get(key),
                        'outcome': outcome, 'result_count': count,
                        'duration_ms': round((time.monotonic() - start) * 1000, 2)})
