import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from test_pe import fixture
class TestCLI(unittest.TestCase):
    def invoke(self,*args):
        return subprocess.run([sys.executable,'-m','xboxpc',*map(str,args)],capture_output=True,text=True)
    def test_readonly_plan(self):
        with tempfile.TemporaryDirectory() as d:
            f=Path(d)/'input.exe'; f.write_bytes(fixture())
            for target in ('windows','xbox'):
                r=self.invoke('plan',f,'--target',target)
                self.assertEqual(r.returncode,0,r.stderr)
                self.assertFalse(json.loads(r.stdout)['runnable'])
            self.assertEqual(f.read_bytes(),fixture())
    def test_output_protection(self):
        with tempfile.TemporaryDirectory() as d:
            f=Path(d)/'in.exe'; f.write_bytes(fixture())
            self.assertEqual(self.invoke('relink-fixture',f,f).returncode,2)
            out=Path(d)/'out.exe'
            self.assertEqual(self.invoke('relink-fixture',f,out).returncode,0)
            before=out.read_bytes()
            self.assertEqual(self.invoke('relink-fixture',f,out).returncode,2)
            self.assertEqual(out.read_bytes(),before)
    def test_invalid_input_no_output(self):
        with tempfile.TemporaryDirectory() as d:
            f=Path(d)/'bad'; f.write_bytes(b'bad')
            out=Path(d)/'out'
            self.assertEqual(self.invoke('relink-fixture',f,out).returncode,2)
            self.assertFalse(out.exists())
