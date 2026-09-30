"""Driver boundary. Only RegisteredGateway imports this module."""
import copy
import json
import os
import threading
from datetime import datetime, timezone
from backend.config import ROOT
from backend.errors import AuthorityError

FIELDS = ('title','text','source_url','category','year','major_code','retrieved_at')

class Store:
    def __init__(self, settings):
        self.settings = settings
        self.client = None
        self.local = None
        self.local_signature = None
        self.init_lock = threading.Lock()
        if settings.data_mode not in ('local', 'mongo'):
            raise AuthorityError('Unknown data mode')

    def read(self, authority, params):
        collection = authority['sourceCollection']
        if collection not in authority['allowedCollections'] or collection != 'huit_kb':
            raise AuthorityError('Collection denied')
        maximum = authority['limits']['maxResults']
        if self.settings.data_mode == 'local':
            if authority['strategy'] != 'snapshot':
                raise AuthorityError('Local mode has no dense vectors')
            with self.init_lock:
                path = ROOT / 'data' / 'knowledge.json'
                stat = path.stat()
                # ctime differs between stat/fstat on supported Windows runtimes.
                signature = (stat.st_mtime_ns, stat.st_size, stat.st_ino)
                if self.local is None or signature != self.local_signature:
                    with path.open('rb') as source:
                        before = os.fstat(source.fileno())
                        raw = source.read(2 * 1024 * 1024 + 1)
                        after = os.fstat(source.fileno())
                    if len(raw) > 2 * 1024 * 1024:
                        raise AuthorityError('Local knowledge file is too large')
                    if ((before.st_mtime_ns, before.st_size, before.st_ino) != signature or
                        (after.st_mtime_ns, after.st_size, after.st_ino) != signature):
                        raise AuthorityError('Knowledge changed during read; retry')
                    fresh = json.loads(raw)
                    if not isinstance(fresh, list):
                        raise AuthorityError('Knowledge must be an array')
                    # Commit together only after a complete read; the gateway still validates every result.
                    self.local = fresh
                    self.local_signature = signature
                return copy.deepcopy(self.local[:maximum + 1])
        if not self.settings.mongo_uri:
            raise AuthorityError('Database is not configured')
        with self.init_lock:
            if self.client is None:
                from pymongo import MongoClient
                self.client = MongoClient(self.settings.mongo_uri, serverSelectionTimeoutMS=3000,
                                         connectTimeoutMS=3000, socketTimeoutMS=8500)
        target = self.client[self.settings.mongo_database][collection]
        if authority['strategy'] == 'snapshot':
            cursor = target.find({}, authority['projection']).limit(maximum + 1).max_time_ms(authority['limits']['maxTimeMS'])
        elif authority['strategy'] == 'vector':
            cursor = target.aggregate([
                {'$vectorSearch': {'index': authority['vectorIndex'], 'path': authority['vectorPath'],
                                  'queryVector': params['QUERY_VECTOR'], 'limit': params['TOP_K'],
                                  'numCandidates': authority['numCandidates']}},
                {'$project': {**authority['projection'], 'score': {'$meta': 'vectorSearchScore'}}}
            ], maxTimeMS=authority['limits']['maxTimeMS'])
        else:
            raise AuthorityError('Unregistered strategy')
        # Bound memory as records arrive; do not first materialize an unbounded cursor.
        result = []
        size = 2
        try:
            for raw in cursor:
                record = {k: (raw.get(k) if k == 'year' else raw.get(k, '') if raw.get(k) is not None else '') for k in FIELDS}
                if isinstance(record['retrieved_at'], datetime):
                    date = record['retrieved_at']
                    record['retrieved_at'] = (date.replace(tzinfo=timezone.utc) if date.tzinfo is None else date).isoformat()
                if 'score' in raw:
                    record['score'] = raw['score']
                size += len(json.dumps(record, ensure_ascii=False, allow_nan=False).encode()) + (2 if result else 0)
                if len(result) >= maximum or size > authority['limits']['maxOutputBytes']:
                    raise AuthorityError('Driver output budget exceeded')
                result.append(record)
        finally:
            cursor.close()
        return result

    def close(self):
        with self.init_lock:
            if self.client is not None:
                self.client.close()
                self.client = None
