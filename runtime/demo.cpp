#include "abi.h"
#include <cstdio>
#include <cstring>
int main(int argc,char** argv) {
    if (XPVersion()!=1) { std::fputs("Relink to the host runtime first.\n",stderr); return 2; }
    auto before=XPTimeNs();
    XPSleepMs(10);
    if (XPTimeNs()<=before) return 3;
    uint32_t buttons=0;
    const int input=XPGetButtons(0,&buttons);
    std::printf("XboxPC fixture: native clock/sleep passed; controller status=%d buttons=%u\n",input,buttons);
    if (argc>1 && std::strcmp(argv[1],"--graphics")==0) return XPClearDemo(240)==0 ? 0 : 4;
    return 0;
}
