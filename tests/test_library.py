import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from types import SimpleNamespace
import subprocess
from xboxpc.library import LibraryError,vdf,steam_scan,epic_scan,xbox_scan,record,snapshot,launch,launch_target
class LibraryTests(unittest.TestCase):
    def steam(self,root,id='123',name='Example'):
        (root/'steamapps/common/Game').mkdir(parents=True,exist_ok=True)
        f=root/f'steamapps/appmanifest_{id}.acf'
        f.write_text(f'"AppState" {{ "appid" "{id}" "name" "{name}" "installdir" "Game" "StateFlags" "4" }}')
        return f
    def epic(self,root,**extra):
        root.mkdir(exist_ok=True); install=root/'Game'; install.mkdir(exist_ok=True)
        obj=dict(CatalogNamespace='ns',CatalogItemId='item',AppName='app',InstallLocation=str(install),DisplayName='Epic Test')
        obj.update(extra); (root/'game.item').write_text(json.dumps(obj));return root/'game.item'
    def test_steam_multidrive(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)/'Steam';other=Path(d)/'External';self.steam(root);self.steam(other,'456')
            # Escape Windows backslashes as the real VDF writer does.
            paths=[str(x).replace('\\','\\\\') for x in (root,other)]
            (root/'steamapps/libraryfolders.vdf').write_text('"libraryfolders" { "0" { "path" "'+paths[0]+'" } "1" { "path" "'+paths[1]+'" } }')
            rows=steam_scan(root,[]);self.assertEqual({x['id'] for x in rows},{'123','456'});self.assertEqual(len(rows),2)
    def test_steam_partial_deleted(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);f=self.steam(root);f.write_text(f.read_text().replace('"4"','"2"'))
            self.assertEqual(steam_scan(root,[]),[]);f.unlink();self.assertEqual(steam_scan(root,[]),[])
    def test_malformed_isolated(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);self.steam(root);(root/'steamapps/appmanifest_bad.acf').write_text('"bad" {')
            warnings=[];self.assertEqual(len(steam_scan(root,warnings)),1);self.assertTrue(warnings)
    def test_epic_launch_id(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);self.epic(root,AppName='app with space');game=epic_scan(root,[])[0]
            self.assertEqual(launch_target(game),'com.epicgames.launcher://apps/ns:item:app%20with%20space?action=launch&silent=true')
    def test_epic_partial_dlc(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);self.epic(root,bIsIncompleteInstall=True);self.assertEqual(epic_scan(root,[]),[])
            self.epic(root,MainGameAppName='other');self.assertEqual(epic_scan(root,[]),[])
    def test_epic_bad_manifest(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);self.epic(root).write_text('[]');w=[]
            self.assertEqual(epic_scan(root,w),[]);self.assertTrue(w)
    def test_refresh_every_launch_remove(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);f=self.steam(root);opened=[];calls=[]
            def scan():
                calls.append(True);return dict(games=steam_scan(root,[]),refreshed_at='now')
            for _ in range(2):self.assertEqual(launch('steam:123',scan,opened.append)['status'],'launch_requested')
            f.unlink()
            with self.assertRaises(LibraryError):launch('steam:123',scan,opened.append)
            self.assertEqual(len(calls),3);self.assertEqual(opened,['steam://rungameid/123']*2)
    def test_updates_visible(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);self.steam(root,name='Before');self.assertEqual(steam_scan(root,[])[0]['name'],'Before')
            self.steam(root,name='After');self.assertEqual(steam_scan(root,[])[0]['name'],'After')
    def test_unsafe_launch_id(self):
        for store in ('steam','epic','xbox'):
            with self.assertRaises(LibraryError):launch_target(record(store,'evil & command','x'))
    def test_vdf(self):
        self.assertEqual(vdf(r'"p" "C:\\Games\\Steam"')['p'],r'C:\Games\Steam')
        for t in ('"a" {','}','"a" "b" "a" "c"','garbage'):
            with self.assertRaises(LibraryError):vdf(t)
    def test_xbox_mock_response(self):
        def run(args,**kw):
            self.assertEqual(args[1:3],['-NoProfile','-NonInteractive']);self.assertTrue(kw['timeout'])
            return SimpleNamespace(stdout=json.dumps([dict(id='Game_pub!App',name='Test',location='C:/Game')]))
        with patch('xboxpc.library.os',SimpleNamespace(name='nt',environ={})):
            game=xbox_scan([],run)[0]
        self.assertEqual(launch_target(game),r'shell:AppsFolder\Game_pub!App')
    def test_xbox_timeout(self):
        def run(*a,**k):raise subprocess.TimeoutExpired('powershell',45)
        warnings=[]
        with patch('xboxpc.library.os',SimpleNamespace(name='nt',environ={})):
            self.assertEqual(xbox_scan(warnings,run),[])
        self.assertTrue(warnings)
    def test_scope(self):
        with tempfile.TemporaryDirectory() as d:
            with patch('xboxpc.library.xbox_scan',return_value=[]):s=snapshot(d,d)
        self.assertFalse(s['full_owned_library'])
    def test_failed_open(self):
        def scan():return dict(games=[record('steam','123','x')],refreshed_at='now')
        def fail(uri):raise OSError('No app registered')
        with self.assertRaises(OSError):launch('steam:123',scan,fail)
