import importlib.util
import pathlib
from support import scratch_directory
import unittest
ROOT=pathlib.Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('checker',ROOT/'scripts/check_architecture.py')
checker=importlib.util.module_from_spec(spec);spec.loader.exec_module(checker)

class ArchitectureTests(unittest.TestCase):
    def test_current_boundaries(self):self.assertEqual(checker.violations(ROOT),[])

    def test_new_direct_transport_is_blocked(self):
        with scratch_directory() as directory:
            root=pathlib.Path(directory);(root/'static').mkdir();(root/'backend').mkdir()
            (root/'static/bad.view.js').write_text("window.fetch('/api/chat')")
            self.assertTrue(checker.violations(root))

    def test_new_database_reachthrough_is_blocked(self):
        with scratch_directory() as directory:
            root=pathlib.Path(directory);(root/'static').mkdir();(root/'backend/services').mkdir(parents=True)
            (root/'backend/services/bad.py').write_text('from backend.db.gateway import RegisteredGateway\nfrom pymongo import MongoClient\n')
            self.assertTrue(checker.violations(root))

    def test_nested_endpoints_cannot_move_into_view(self):
        for endpoint in ['/mambot/api/chat','../../../../api/health']:
            with scratch_directory() as directory:
                root=pathlib.Path(directory);(root/'static').mkdir();(root/'backend').mkdir()
                (root/'static/bad.view.js').write_text('const endpoint="'+endpoint+'";')
                self.assertTrue(checker.violations(root))
