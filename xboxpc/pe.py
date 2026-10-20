"""Bounded, read-only PE32+ inspection. No code execution or package decryption."""
import struct

class PEError(ValueError):
    pass

class PE:
    def __init__(self, data):
        self.data = bytes(data)
        if self.read(0, 2) != b'MZ':
            raise PEError('Expected an unpacked PE image (MZ); packages are unsupported')
        self.pe = self.u32(0x3c)
        if self.read(self.pe, 4) != b'PE\0\0':
            raise PEError('Invalid PE signature')
        self.machine = self.u16(self.pe + 4)
        if self.machine != 0x8664:
            raise PEError('Only AMD64 images are supported')
        count = self.u16(self.pe + 6)
        if not 1 <= count <= 96:
            raise PEError('Invalid section count')
        opt_size = self.u16(self.pe + 20)
        self.opt = self.pe + 24
        self.read(self.opt, opt_size)
        if opt_size < 112 or self.u16(self.opt) != 0x20b:
            raise PEError('Expected PE32+ optional header')
        self.entry = self.u32(self.opt + 16)
        self.image_base = self.u64(self.opt + 24)
        self.header_size = self.u32(self.opt + 60)
        self.read(0, self.header_size)
        self.subsystem = self.u16(self.opt + 68)
        ndirs = self.u32(self.opt + 108)
        if ndirs > 16 or 112 + ndirs * 8 > opt_size:
            raise PEError('Invalid data directory count')
        self.dirs = [(self.u32(self.opt+112+i*8), self.u32(self.opt+116+i*8)) for i in range(ndirs)]
        self.sections = []
        table = self.opt + opt_size
        if table + count * 40 > self.header_size:
            raise PEError('Section table exceeds headers')
        for i in range(count):
            p = table + i*40
            name = self.read(p, 8).rstrip(b'\0').decode('ascii', errors='replace')
            virtual_size, rva, size, raw = struct.unpack('<IIII', self.read(p+8, 16))
            if size:
                self.read(raw, size)
                if raw < self.header_size:
                    raise PEError('Section overlaps headers')
            span = max(size, virtual_size)
            if rva < self.header_size or rva + span > 0x100000000:
                raise PEError('Invalid section RVA')
            for s in self.sections:
                if rva < s['rva']+s['span'] and s['rva'] < rva+span:
                    raise PEError('Overlapping virtual sections')
                if size and s['size'] and raw < s['raw']+s['size'] and s['raw'] < raw+size:
                    raise PEError('Overlapping raw sections')
            self.sections.append(dict(name=name,rva=rva,span=span,size=size,raw=raw))
        self.imports = self.parse_imports()

    def read(self, offset, size):
        if offset < 0 or size < 0 or offset > len(self.data)-size:
            raise PEError('Truncated image or out-of-bounds offset')
        return self.data[offset:offset+size]

    def u16(self,p): return struct.unpack('<H',self.read(p,2))[0]
    def u32(self,p): return struct.unpack('<I',self.read(p,4))[0]
    def u64(self,p): return struct.unpack('<Q',self.read(p,8))[0]
    def directory(self,n): return self.dirs[n] if n<len(self.dirs) else (0,0)

    def offset(self,rva,size=1):
        if rva < self.header_size and rva+size <= self.header_size:
            self.read(rva,size)
            return rva
        for s in self.sections:
            delta = rva-s['rva']
            if 0 <= delta and delta+size <= s['size']:
                self.read(s['raw']+delta,size)
                return s['raw']+delta
        raise PEError('RVA has no file-backed bytes')

    def string(self,rva):
        result=bytearray()
        for i in range(4096):
            c=self.data[self.offset(rva+i)]
            if not c:
                try: return result.decode('ascii')
                except UnicodeDecodeError as exc: raise PEError('Non-ASCII import name') from exc
            result.append(c)
        raise PEError('Unterminated import name')

    def parse_imports(self):
        rva,size=self.directory(1)
        if not rva and not size: return []
        if not rva or size<20: raise PEError('Invalid import directory')
        result=[]
        budget=65536
        for i in range(min(size//20,4096)):
            p=self.offset(rva+i*20,20)
            lookup,stamp,chain,name,iat=struct.unpack('<IIIII',self.read(p,20))
            if not any((lookup,stamp,chain,name,iat)): return result
            if not name or not iat: raise PEError('Incomplete import descriptor')
            dll=self.string(name)
            if not dll: raise PEError('Empty DLL name')
            symbols=[]
            for j in range(budget):
                value=self.u64(self.offset((lookup or iat)+j*8,8))
                self.offset(iat+j*8,8)
                budget-=1
                if not value: break
                if value & (1<<63):
                    if value & 0x7fffffffffff0000: raise PEError('Invalid ordinal thunk')
                    symbols.append({'ordinal':value & 0xffff})
                else:
                    if value>0xffffffff: raise PEError('Invalid name RVA (possibly bound IAT)')
                    self.offset(value,2)
                    symbols.append({'name':self.string(value+2)})
            else: raise PEError('Unterminated or excessive import thunks')
            result.append(dict(dll=dll,name_rva=name,symbols=symbols,timestamp=stamp,lookup=lookup))
        raise PEError('Unterminated import directory')

    def report(self):
        return dict(format='PE32+',architecture='x86-64',entry_rva=self.entry,
                    image_base=self.image_base,subsystem=self.subsystem,
                    sections=self.sections,imports=self.imports,
                    certificate_table=bool(any(self.directory(4))),
                    delayed_imports=bool(any(self.directory(13))),
                    managed_image=bool(any(self.directory(14))))
