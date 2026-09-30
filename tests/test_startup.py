import contextlib
import io
import json
import os
import shutil
import subprocess
import uuid
from pathlib import Path
import socket
import threading
import unittest
from unittest.mock import MagicMock, patch
import run


@contextlib.contextmanager
def launcher_scratch():
    # Inherit workspace ACLs; Windows restricted tokens cannot reopen mode-0700 temp dirs.
    base=run.ROOT/'var'
    folder=base/('Mambot launcher '+uuid.uuid4().hex)
    folder.mkdir(parents=True)
    try:yield folder
    finally:
        assert folder.resolve().is_relative_to(base.resolve())
        shutil.rmtree(folder)


class StartupTests(unittest.TestCase):
    def test_missing_planner_styles_are_reported_before_server_start(self):
        actual=Path.is_file
        with patch.object(Path,'is_file',lambda path: False if path.name=='student.css' else actual(path)):
            with self.assertRaisesRegex(run.StartupError,'student.css'):run.check_installation()

    @unittest.skipUnless(os.name=='nt','Windows launcher')
    def test_launcher_alone_explains_exact_missing_runtime_and_extraction(self):
        with launcher_scratch() as folder:
            launcher=Path(folder)/'START_MAMBOT.cmd'
            shutil.copy2(run.ROOT/'START_MAMBOT.cmd',launcher)
            result=subprocess.run(['cmd.exe','/d','/c',str(launcher),'--check'],cwd=run.ROOT,capture_output=True,text=True,timeout=20)
            self.assertEqual(result.returncode,1)
            for text in ('THIEU FILE:', 'run.py', 'runtime\\python\\python.exe', 'Extract All', 'THU MUC DANG CHAY:'):
                self.assertIn(text,result.stdout)

    @unittest.skipUnless(os.name=='nt','Windows launcher')
    def test_launcher_from_unrelated_directory_succeeds_without_browser(self):
        if not (run.ROOT/'runtime/python/python.exe').is_file():self.skipTest('Portable runtime not in source-only checkout')
        with launcher_scratch() as folder:
            result=subprocess.run(['cmd.exe','/d','/c',str(run.ROOT/'START_MAMBOT.cmd'),'--check'],cwd=folder,capture_output=True,text=True,timeout=30)
            self.assertEqual(result.returncode,0,result.stdout+result.stderr)
            self.assertIn('PASS: Mambot 1.1',result.stdout)

    def test_incomplete_extraction_explains_missing_files(self):
        with patch.object(Path,'is_file',return_value=False):
            with self.assertRaisesRegex(run.StartupError, 'Giai nen chua day du.*backend/app.py'):
                run.check_installation(Path('missing-extraction'))

    def test_old_python_is_rejected_before_dependency_import(self):
        with patch.object(run.sys,'version_info',(3,10)),self.assertRaisesRegex(run.StartupError,'3.11'):
            run.check_installation()

    def test_dependency_error_is_actionable_without_leaking_original_exception(self):
        with patch.object(run.importlib,'import_module',side_effect=ImportError('private path')):
            with self.assertRaises(run.StartupError) as error:run.check_installation()
        self.assertIn('fastapi',str(error.exception));self.assertNotIn('private path',str(error.exception))

    def test_invalid_port_is_not_silently_replaced(self):
        for value in ('','abc','0','65536','-1','3.5'):
            with self.subTest(value=value),self.assertRaises(run.StartupError):
                run.reserve_listener('127.0.0.1',value)

    def test_default_busy_port_falls_back_and_closes_failed_socket(self):
        first=MagicMock();second=MagicMock();first.bind.side_effect=OSError('busy')
        with patch.object(run.socket,'socket',side_effect=[first,second]):
            self.assertIs(run.reserve_listener('127.0.0.1',None),second)
        first.close.assert_called_once();second.bind.assert_called_once_with(('127.0.0.1',8001))
        second.listen.assert_called_once()

    def test_explicit_busy_port_fails_without_changing_user_configuration(self):
        sock=MagicMock();sock.bind.side_effect=OSError('busy')
        with patch.object(run.socket,'socket',return_value=sock) as factory:
            with self.assertRaisesRegex(run.StartupError,'8765'):run.reserve_listener('127.0.0.1','8765')
            self.assertEqual(factory.call_count,1)
        sock.close.assert_called_once()

    def test_selected_port_is_reserved_until_socket_is_closed(self):
        probe=socket.socket();probe.bind(('127.0.0.1',0));port=probe.getsockname()[1];probe.close()
        listener=run.reserve_listener('127.0.0.1',str(port))
        try:
            with self.assertRaises(run.StartupError):run.reserve_listener('127.0.0.1',str(port))
        finally:listener.close()

    def test_check_mode_verifies_local_authority_without_opening_browser(self):
        with contextlib.redirect_stdout(io.StringIO()) as out,patch.object(run.webbrowser,'open') as browser:
            self.assertEqual(run.main(['--check']),0)
            self.assertIn('45 tai lieu',out.getvalue());browser.assert_not_called()

    def test_browser_opens_only_after_healthy_mambot_response(self):
        opener=MagicMock()
        opener.open.return_value.__enter__.return_value.read.return_value=json.dumps({'name':'Mambot','status':'ok'}).encode()
        with patch.object(run.urllib.request,'build_opener',return_value=opener),patch.object(run.webbrowser,'open') as browser:
            run.browser_when_ready('http://127.0.0.1:8000/mambot/',threading.Event())
            browser.assert_called_once_with('http://127.0.0.1:8000/mambot/')

    def test_stopped_startup_never_opens_browser(self):
        stopped=threading.Event();stopped.set()
        with patch.object(run.webbrowser,'open') as browser:
            run.browser_when_ready('http://127.0.0.1:8000/mambot/',stopped)
            browser.assert_not_called()
