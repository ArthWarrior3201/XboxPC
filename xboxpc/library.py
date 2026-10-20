"""Local installation discovery, never an account-entitlement API.
Steam/Epic metadata formats are best-effort, version-dependent integrations.
"""
import json
import os
from pathlib import Path
import re
import subprocess
from datetime import datetime, timezone
from urllib.parse import quote

class LibraryError(ValueError): pass

def read_text(path):
    with Path(path).open('rb') as f: data=f.read(4*1024*1024+1)
    if len(data)>4*1024*1024: raise LibraryError('Manifest exceeds 4 MiB')
    return data.decode('utf-8-sig')

def vdf(text):
    # Strict subset used by appmanifest/libraryfolders: quoted strings and braces.
    tokens=[]; pos=0
    pattern=re.compile(r'\s+|//[^\n]*|"((?:\\.|[^"\\])*)"|([{}])')
    while pos<len(text):
        m=pattern.match(text,pos)
        if not m: raise LibraryError('Invalid VDF token')
        pos=m.end()
        if m.group(1) is not None:
            tokens.append(('s',re.sub(r'\\([\\"])',r'\1',m.group(1))))
        elif m.group(2): tokens.append((m.group(2),m.group(2)))
    at=0
    def obj(depth=0):
        nonlocal at
        if depth>32: raise LibraryError('VDF nesting too deep')
        result={}
        while at<len(tokens) and tokens[at][0]!='}':
            kind,key=tokens[at]; at+=1
            if kind!='s' or at==len(tokens): raise LibraryError('Invalid VDF key/value')
            kind,value=tokens[at]; at+=1
            if kind=='{':
                value=obj(depth+1)
                if at==len(tokens) or tokens[at][0]!='}': raise LibraryError('Unclosed VDF object')
                at+=1
            elif kind!='s': raise LibraryError('Invalid VDF value')
            if key in result: raise LibraryError('Duplicate VDF key')
            result[key]=value
        return result
    result=obj()
    if at!=len(tokens): raise LibraryError('Unexpected VDF close')
    return result

def record(store,id,name,location='',**extra):
    return dict(key=f'{store}:{id}',store=store,id=id,name=name,location=str(location),
                ownership='not_checked',execution='native_windows',**extra)

def steam_scan(root,warnings):
    if not root or not root.is_dir(): return []
    roots=[root]; folders=root/'steamapps/libraryfolders.vdf'
    if folders.exists():
        try:
            entries=vdf(read_text(folders)).get('libraryfolders',{})
            for key,value in entries.items():
                if key.isdigit():
                    path=value.get('path') if isinstance(value,dict) else value
                    if isinstance(path,str): roots.append(Path(path))
        except (OSError,ValueError,AttributeError) as e: warnings.append(f'Steam library folders: {e}')
    games=[]
    for base in dict.fromkeys(roots):
        for file in sorted((base/'steamapps').glob('appmanifest_*.acf')):
            try:
                a=vdf(read_text(file))['AppState']
                id=a['appid']; directory=a['installdir']
                if not re.fullmatch(r'[0-9]+',id) or file.name!=f'appmanifest_{id}.acf': raise LibraryError('Invalid Steam app ID')
                if not directory or '/' in directory or '\\' in directory or directory in ('.','..'): raise LibraryError('Invalid install directory')
                location=base/'steamapps/common'/directory
                # Fully-installed bit; client still decides whether updates/auth are needed.
                if int(a.get('StateFlags','0')) & 4 and location.is_dir():
                    games.append(record('steam',id,a.get('name',id),location))
            except (OSError,ValueError,KeyError,TypeError) as e: warnings.append(f'{file.name}: {e}')
    return games

def epic_scan(folder,warnings):
    if not folder or not folder.is_dir(): return []
    games=[]
    for file in sorted(folder.glob('*.item')):
        try:
            a=json.loads(read_text(file))
            if not isinstance(a,dict): raise LibraryError('Invalid Epic manifest')
            if a.get('bIsIncompleteInstall') or a.get('bIsApplication') is False: continue
            parts=[a.get(k) for k in ('CatalogNamespace','CatalogItemId','AppName')]
            if not all(isinstance(x,str) and x and len(x)<=256 for x in parts): raise LibraryError('Missing Epic launch identity')
            location=a.get('InstallLocation')
            if not isinstance(location,str) or not location or not Path(location).is_dir(): continue
            # DLC is not an independently launchable application.
            if a.get('MainGameAppName') and a['MainGameAppName']!=parts[2]: continue
            id=':'.join(quote(x,safe='') for x in parts)
            games.append(record('epic',id,a.get('DisplayName',parts[2]),location))
        except (OSError,ValueError,TypeError) as e: warnings.append(f'{file.name}: {e}')
    return games

# Fixed script, no user-supplied code interpolated. Only positively identified game packages.
XBOX_SCRIPT=r'''
$ErrorActionPreference='Stop'
[Console]::OutputEncoding = New-Object System.Text.UTF8Encoding
$apps=@(Get-StartApps)
$result=@(foreach($p in Get-AppxPackage) {
  if(-not $p.InstallLocation) { continue }
  $config=Join-Path $p.InstallLocation 'MicrosoftGame.config'
  $content=Join-Path $p.InstallLocation 'Content\MicrosoftGame.config'
  if((Test-Path -LiteralPath $config) -or (Test-Path -LiteralPath $content)) {
    foreach($a in $apps) {
      if($a.AppID.StartsWith($p.PackageFamilyName+'!', [System.StringComparison]::OrdinalIgnoreCase)) {
        [PSCustomObject]@{id=$a.AppID;name=$a.Name;location=$p.InstallLocation}
      }
    }
  }
})
ConvertTo-Json -InputObject $result -Compress
'''

def xbox_scan(warnings,runner=subprocess.run):
    if os.name!='nt':
        warnings.append('Xbox package discovery requires Windows.'); return []
    try:
        ps=Path(os.environ.get('SystemRoot',r'C:\Windows'))/'System32/WindowsPowerShell/v1.0/powershell.exe'
        proc=runner([str(ps),'-NoProfile','-NonInteractive','-Command',XBOX_SCRIPT],
                    capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=45,check=True)
        rows=json.loads(proc.stdout.lstrip('\ufeff'))
        if not isinstance(rows,list): raise LibraryError('Invalid Windows package response')
        games=[]
        for a in rows:
            if not isinstance(a,dict) or not re.fullmatch(r'[A-Za-z0-9._-]+![A-Za-z0-9._-]+',a.get('id','')):
                raise LibraryError('Invalid Windows app identity')
            games.append(record('xbox',a['id'],a.get('name',a['id']),a.get('location','')))
        return games
    except (OSError,ValueError,subprocess.SubprocessError) as e:
        warnings.append(f'Xbox discovery unavailable: {e}'); return []

def steam_root():
    if os.name=='nt':
        import winreg
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER,r'Software\Valve\Steam') as key:
                return Path(winreg.QueryValueEx(key,'SteamPath')[0])
        except OSError: pass
    return None

def snapshot(steam=None,epic=None):
    warnings=[]
    steam=Path(steam) if steam is not None else steam_root()
    epic=Path(epic) if epic is not None else Path(os.environ.get('ProgramData',r'C:\ProgramData'))/'Epic/EpicGamesLauncher/Data/Manifests'
    if steam is None or not steam.is_dir(): warnings.append('Steam installation not detected; install/open Steam or specify --steam-root.')
    if not epic.is_dir(): warnings.append('Epic installed-title manifests not found; install a title through Epic first.')
    games=steam_scan(steam,warnings)+epic_scan(epic,warnings)+xbox_scan(warnings)
    unique={g['key']:g for g in games}
    warnings.append('Xbox discovery covers registered packages with MicrosoftGame.config and Start-menu entries only; legacy or inaccessible games may be missing.')
    return dict(version='1',refreshed_at=datetime.now(timezone.utc).isoformat(),scope='local_installed_only',
                full_owned_library=False,games=sorted(unique.values(),key=lambda g:(str(g['name']).casefold(),g['key'])),warnings=warnings)

def launch_target(game):
    store=game['store']; id=game['id']
    if store=='steam' and re.fullmatch(r'[0-9]+',id): return f'steam://rungameid/{id}'
    if store=='epic' and re.fullmatch(r'(?:[A-Za-z0-9_.~%-]+:){2}[A-Za-z0-9_.~%-]+',id):
        return f'com.epicgames.launcher://apps/{id}?action=launch&silent=true'
    if store=='xbox' and re.fullmatch(r'[A-Za-z0-9._-]+![A-Za-z0-9._-]+',id): return f'shell:AppsFolder\\{id}'
    raise LibraryError('Invalid store launch identity')

def launch(key,scan=snapshot,opener=None):
    # Never launch from a cached UI record: reread all providers on every click.
    fresh=scan()
    game=next((g for g in fresh['games'] if g['key']==key),None)
    if game is None: raise LibraryError('Title no longer appears in the fresh installed library. Refresh the list or open its store app.')
    target=launch_target(game)
    if opener is None:
        if os.name!='nt': raise LibraryError('Native store launching requires Windows')
        opener=os.startfile
    opener(target)
    return dict(status='launch_requested',key=key,target=target,refreshed_at=fresh['refreshed_at'],
                note='Request handed to the installed client/Windows; game startup and entitlement are not confirmed.')
