import copy
import json
from support import scratch_directory
import unittest
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch
from backend.config import settings
from backend.db.gateway import RegisteredGateway, checksum
from backend.errors import AuthorityError

class GatewayTests(unittest.TestCase):
    def setUp(self):
        self.tmp=scratch_directory()
        directory=self.tmp.__enter__()
        self.addCleanup(self.tmp.__exit__,None,None,None)
        self.g=RegisteredGateway(replace(settings,data_mode='local',audit_path=Path(directory)/'audit.jsonl'))

    def test_snapshot_is_projected_and_audited(self):
        result=self.g.execute('knowledge.snapshot',{},'case-1')
        self.assertEqual(len(result),45)
        self.assertNotIn('_id',result[0]);self.assertNotIn('embedding',result[0])
        audit=json.loads(self.g.audit_path.read_text().strip())
        self.assertEqual(audit['request_id'],'case-1');self.assertEqual(audit['outcome'],'allowed')

    def test_undeclared_parameter_denied_before_store(self):
        with patch.object(self.g.store,'read') as read:
            with self.assertRaises(Exception):self.g.execute('knowledge.snapshot',{'filter':{'$where':'evil'}})
            read.assert_not_called()

    def test_unknown_operation_denied(self):
        with self.assertRaises(AuthorityError):self.g.execute('../../anything',{})

    def test_tampered_authority_rejected(self):
        op=self.g.resolve('knowledge.snapshot');op['projection']['embedding']=1
        with patch('backend.db.gateway.json.loads',return_value=op):
            with self.assertRaises(AuthorityError):self.g.resolve('knowledge.snapshot')

    def test_version_status_type_collection_and_cost_rejected(self):
        for key,value in [('status','candidate'),('type','write'),('mutationMode','write'),('allowedCollections',['secrets']),('sourceCollection','secrets'),('limits',{'maxTimeMS':9000,'maxResults':100,'maxOutputBytes':524288})]:
            with self.subTest(key=key):
                op=self.g.resolve('knowledge.snapshot');op[key]=value;op['checksum']=checksum(op)
                old=copy.deepcopy(self.g.pins);self.g.pins['knowledge.snapshot']['checksum']=op['checksum']
                with patch('backend.db.gateway.json.loads',return_value=op):
                    with self.assertRaises(AuthorityError):self.g.resolve('knowledge.snapshot')
                self.g.pins=old

    def test_vectors_must_have_1024_finite_numbers_and_bounded_topk(self):
        for params in [{'QUERY_VECTOR':[0]*3,'TOP_K':5},{'QUERY_VECTOR':[0]*1024,'TOP_K':21},
                       {'QUERY_VECTOR':[0]*1024,'TOP_K':True},{'QUERY_VECTOR':[float('nan')]*1024,'TOP_K':5},
                       {'QUERY_VECTOR':['x']*1024,'TOP_K':5}, {'QUERY_VECTOR':[0]*1024,'TOP_K':5,'EXTRA':1}]:
            with self.subTest(params=str(params)[:80]),patch.object(self.g.store,'read') as read:
                with self.assertRaises(Exception):self.g.execute('knowledge.semantic',params)
                read.assert_not_called()

    def test_correct_vector_is_bound(self):
        with patch.object(self.g.store,'read',return_value=[]) as read:
            self.g.execute('knowledge.semantic',{'QUERY_VECTOR':[0.1]*1024,'TOP_K':5})
            self.assertEqual(read.call_args.args[1]['TOP_K'],5)

    def test_output_private_fields_types_count_bytes_and_time(self):
        valid=self.g.execute('knowledge.snapshot',{})[0]
        for output in [[{**valid,'_id':'private'}],[{**valid,'title':3}],[valid]*101,[{**valid,'text':'x'*600000}]]:
            with self.subTest(length=len(str(output))),patch.object(self.g.store,'read',return_value=output):
                with self.assertRaises(Exception):self.g.execute('knowledge.snapshot',{})
        with patch('backend.db.gateway.time.monotonic',side_effect=[0,9,9]),patch.object(self.g.store,'read',return_value=[]):
            with self.assertRaises(AuthorityError):self.g.execute('knowledge.snapshot',{})

    def test_audit_failure_is_fail_closed(self):
        with patch.object(self.g,'audit',side_effect=OSError('unwritable')):
            with self.assertRaises(OSError):self.g.execute('knowledge.snapshot',{})

    def test_mongo_mode_has_no_local_fallback(self):
        from backend.db.store import Store
        store=Store(replace(settings,data_mode='mongo',mongo_uri=''))
        with self.assertRaises(AuthorityError):store.read(self.g.resolve('knowledge.snapshot'),{})
