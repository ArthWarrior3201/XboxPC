#define XP_EXPORT
#include "abi.h"
// Link-time stand-in only. CI deliberately does not ship this DLL with the demo.
uint32_t XPVersion() { return 0; }
uint64_t XPTimeNs() { return 0; }
void XPSleepMs(uint32_t) {}
int64_t XPReadAt(const char*,uint64_t,void*,uint32_t) { return -1; }
int XPGetButtons(uint32_t,uint32_t*) { return -1; }
int XPClearDemo(uint32_t) { return -1; }
