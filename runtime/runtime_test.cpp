#include "abi.h"
#include <fstream>
#include <cstdio>
#include <cstring>
#define CHECK(x) do { if (!(x)) { std::fprintf(stderr,"Failed line %d: %s\n",__LINE__,#x); return 1; } } while(0)
int main() {
    CHECK(XPVersion()==1);
    auto start=XPTimeNs(); XPSleepMs(2); CHECK(XPTimeNs()>start);
    { std::ofstream f("runtime-test.bin",std::ios::binary); f<<"abcdef"; }
    char b[5]{};
    CHECK(XPReadAt("runtime-test.bin",2,b,3)==3);
    CHECK(std::memcmp(b,"cde",3)==0);
    CHECK(XPReadAt("runtime-test.bin",5,b,5)==1);
    CHECK(XPReadAt("runtime-test.bin",100,b,5)==0);
    CHECK(XPReadAt(nullptr,0,b,1)==-1);
    CHECK(XPReadAt("runtime-test.bin",0,nullptr,1)==-1);
    CHECK(XPReadAt("runtime-test.bin",UINT64_MAX,b,1)==-1);
    uint32_t buttons=99;
    CHECK(XPGetButtons(9,&buttons)==-1 && buttons==0);
    CHECK(XPGetButtons(0,nullptr)==-1);
    std::remove("runtime-test.bin");
    std::puts("Runtime conformance passed");
}
