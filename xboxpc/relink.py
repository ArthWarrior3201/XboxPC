"""Strict fixture-only relinker. The XP* ABI is ours, NOT an Xbox ABI."""
import hashlib
import struct
from .pe import PE, PEError

GUEST='xboxpc_guest.dll'
HOST='xboxpc_host.dll'
EXPORTS={'XPVersion','XPTimeNs','XPSleepMs','XPReadAt','XPGetButtons','XPClearDemo'}

def relink(data):
    pe=PE(data)
    for index,label in [(4,'certificate'),(11,'bound import'),(13,'delay import'),(14,'CLR')]:
        if any(pe.directory(index)):
            raise PEError(f'Fixture relinker does not support {label} tables')
    if pe.subsystem != 3:
        raise PEError('Only console-subsystem test executables are supported')
    if pe.u16(pe.pe+22) & 0x2000:
        raise PEError('DLL input is unsupported')
    matches=[x for x in pe.imports if x['dll'].lower()==GUEST]
    if len(matches)!=1:
        raise PEError('Requires exactly one XboxPC self-authored fixture import; retail games are unsupported')
    module=matches[0]
    if module['timestamp'] or not module['lookup']:
        raise PEError('An unbound import lookup table is required')
    if not module['symbols']:
        raise PEError('Fixture has no imports')
    if any(s.get('name') not in EXPORTS for s in module['symbols']):
        raise PEError('Unknown fixture ABI symbol or ordinal')
    if any(x['dll'].lower()==HOST for x in pe.imports):
        raise PEError('Host module already imported')
    start=pe.offset(module['name_rva'],len(GUEST)+1)
    output=bytearray(data)
    replacement=HOST.encode()+b'\0'*(len(GUEST)+1-len(HOST))
    output[start:start+len(replacement)]=replacement
    # User-mode unsigned sample: zero old checksum after modifying import metadata.
    struct.pack_into('<I',output,pe.opt+64,0)
    check=PE(output)
    expected=[dict(x,dll=HOST) if x is module else x for x in pe.imports]
    if check.imports != expected:
        raise PEError('Revalidation detected aliased/corrupted import metadata')
    return bytes(output),dict(mode='fixture-only',source_sha256=hashlib.sha256(data).hexdigest(),
        output_sha256=hashlib.sha256(output).hexdigest(),dll_from=GUEST,dll_to=HOST,
        cpu_instructions_changed=False,commercial_game_support=False)
