#define XP_EXPORT
#include "abi.h"
#include <chrono>
#include <thread>
#include <fstream>
#include <limits>
#ifdef _WIN32
#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <Xinput.h>
#endif
uint32_t XPVersion() { return 1; }
uint64_t XPTimeNs() {
    return static_cast<uint64_t>(std::chrono::duration_cast<std::chrono::nanoseconds>(
        std::chrono::steady_clock::now().time_since_epoch()).count());
}
void XPSleepMs(uint32_t ms) { std::this_thread::sleep_for(std::chrono::milliseconds(ms)); }
int64_t XPReadAt(const char* path, uint64_t offset, void* buffer, uint32_t size) {
    if (!path || (!buffer && size) || offset > static_cast<uint64_t>((std::numeric_limits<std::streamoff>::max)())) return -1;
    try {
        std::ifstream file(path, std::ios::binary);
        if (!file) return -1;
        file.seekg(static_cast<std::streamoff>(offset));
        if (!file) return -1;
        if (!size) return 0;
        file.read(static_cast<char*>(buffer), size);
        return file.bad() ? -1 : file.gcount();
    } catch (...) { return -1; }
}
int XPGetButtons(uint32_t controller, uint32_t* buttons) {
    if (!buttons) return -1;
    *buttons=0;
    if (controller>=4) return -1;
#ifdef _WIN32
    XINPUT_STATE state{};
    if (XInputGetState(controller,&state)!=ERROR_SUCCESS) return 1;
    *buttons=state.Gamepad.wButtons;
    return 0;
#else
    return -1;
#endif
}
#ifndef _WIN32
int XPClearDemo(uint32_t) { return -1; }
#endif
