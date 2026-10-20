import argparse
import json
import sys
from pathlib import Path
from .pe import PE, PEError
from .relink import relink

def main():
    p=argparse.ArgumentParser(description='XboxPC v1 research tools — no commercial game support')
    sub=p.add_subparsers(dest='command',required=True)
    inspect=sub.add_parser('inspect',help='Inspect an unpacked AMD64 PE without executing it')
    inspect.add_argument('input',type=Path)
    plan=sub.add_parser('plan',help='Report direction-specific research blockers; does not convert')
    plan.add_argument('input',type=Path)
    plan.add_argument('--target',choices=['windows','xbox'],required=True)
    patch=sub.add_parser('relink-fixture',help='Retarget only the self-authored XP* fixture ABI')
    patch.add_argument('input',type=Path)
    patch.add_argument('output',type=Path)
    sub.add_parser('gui',help='Open the installed-library launcher')
    library=sub.add_parser('library',help='Refresh local installed titles; no account linking')
    library.add_argument('--steam-root',type=Path)
    library.add_argument('--epic-manifests',type=Path)
    launch_parser=sub.add_parser('launch',help='Refresh then request a native store launch')
    launch_parser.add_argument('key',help='Exact key returned by library')
    args=p.parse_args()
    try:
        if args.command=='gui':
            from .gui import main as gui_main
            gui_main()
            return 0
        if args.command in ('library','launch'):
            from .library import snapshot, launch
            report=snapshot(args.steam_root,args.epic_manifests) if args.command=='library' else launch(args.key)
            print(json.dumps(report,indent=2))
            return 0
        # Inspection intentionally bounded: avoid accidentally loading multi-GB packages.
        with args.input.open('rb') as f:
            data=f.read(128*1024*1024+1)
        if len(data)>128*1024*1024: raise PEError('Image exceeds 128 MiB inspection limit')
        if args.command=='relink-fixture':
            output,report=relink(data)
            # Never replace input, existing files, or follow an existing destination symlink.
            with args.output.open('xb') as f: f.write(output)
        else:
            pe=PE(data)
            report=pe.report()
            if args.command=='plan':
                report.update(target=args.target,runnable=False,compatibility='unproven',
                    blockers=(['Xbox ABI identification and import implementations',
                    'Console graphics/shader translation', 'Memory, synchronization and service semantics']
                    if args.target=='windows' else ['Windows API and store-service implementations on Xbox',
                    'Console graphics backend and memory constraints',
                    'Target-specific executable loading and packaging; no console backend exists']))
        print(json.dumps(report,indent=2))
        return 0
    except (OSError,ValueError) as exc:
        print(f'XboxPC: {exc}',file=sys.stderr)
        return 2

if __name__=='__main__': raise SystemExit(main())
