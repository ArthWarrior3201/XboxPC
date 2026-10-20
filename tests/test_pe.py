import struct
import unittest
from xboxpc.pe import PE, PEError
from xboxpc.relink import relink

# Synthetic metadata, not a real Xbox image; no executable code in this fixture.
def fixture():
    b=bytearray(0x600)
    def w(p,fmt,*v): struct.pack_into('<'+fmt,b,p,*v)
    b[:2]=b'MZ'; w(0x3c,'I',0x80); b[0x80:0x84]=b'PE\0\0'
    w(0x84,'HH',0x8664,1); w(0x94,'HH',240,0x22)
    o=0x98
    w(o,'H',0x20b); w(o+16,'I',0x1000); w(o+24,'Q',0x140000000)
    w(o+60,'I',0x200); w(o+68,'H',3); w(o+108,'I',16)
    w(o+120,'II',0x1000,40)
    s=o+240; b[s:s+8]=b'.rdata\0\0'; w(s+8,'IIII',0x400,0x1000,0x400,0x200)
    w(0x200,'IIIII',0x1040,0,0,0x1080,0x1060)
    w(0x240,'QQ',0x10a0,0); w(0x260,'QQ',0x10a0,0)
    b[0x280:0x291]=b'xboxpc_guest.dll\0'
    b[0x2a2:0x2ac]=b'XPVersion\0'
    return bytes(b)

class TestPE(unittest.TestCase):
    def test_inspect(self):
        p=PE(fixture()); self.assertEqual(p.imports[0]['symbols'],[{'name':'XPVersion'}])
    def test_relink(self):
        source=fixture(); output,report=relink(source)
        self.assertEqual(PE(output).imports[0]['dll'],'xboxpc_host.dll')
        self.assertEqual(len(output),len(source))
        self.assertFalse(report['commercial_game_support'])
        changes=[i for i,(a,b) in enumerate(zip(source,output)) if a!=b]
        self.assertTrue(changes); self.assertTrue(all(0x280<=i<0x291 for i in changes))
    def test_truncated(self):
        for n in range(len(fixture())):
            with self.assertRaises(PEError): PE(fixture()[:n])
    def test_bad_magic(self):
        with self.assertRaises(PEError): PE(b'not a package')
    def test_wrong_arch(self):
        b=bytearray(fixture()); struct.pack_into('<H',b,0x84,0x14c)
        with self.assertRaises(PEError): PE(b)
    def test_virtual_only_rva(self):
        p=PE(fixture())
        with self.assertRaises(PEError): p.offset(0x1400)
    def test_signed_and_special_directories(self):
        for directory in (4,11,13,14):
            b=bytearray(fixture()); struct.pack_into('<II',b,0x98+112+directory*8,0x1100,8)
            with self.assertRaises(PEError): relink(b)
    def test_ordinal_rejected(self):
        b=bytearray(fixture()); struct.pack_into('<Q',b,0x240,(1<<63)|3)
        self.assertEqual(PE(b).imports[0]['symbols'],[{'ordinal':3}])
        with self.assertRaises(PEError): relink(b)
    def test_unknown_symbol(self):
        b=bytearray(fixture()); b[0x2a2]=ord('Y')
        with self.assertRaises(PEError): relink(b)
    def test_unmapped_import(self):
        b=bytearray(fixture()); struct.pack_into('<I',b,0x20c,0xffff0000)
        with self.assertRaises(PEError): PE(b)
    def test_directory_not_terminated(self):
        b=bytearray(fixture()); struct.pack_into('<I',b,0x98+124,20)
        with self.assertRaises(PEError): PE(b)
    def test_relink_twice(self):
        b,_=relink(fixture())
        with self.assertRaises(PEError): relink(b)
    def test_bounded_mutations(self):
        import random
        r=random.Random(42)
        for _ in range(2000):
            b=bytearray(fixture())
            for _ in range(4): b[r.randrange(len(b))]=r.randrange(256)
            try: PE(b)
            except PEError: pass

if __name__=='__main__': unittest.main()
