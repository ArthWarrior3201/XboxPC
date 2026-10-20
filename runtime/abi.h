#pragma once
#include <cstdint>
#if defined(_WIN32)
# if defined(XP_EXPORT)
#  define XP_API extern "C" __declspec(dllexport)
# else
#  define XP_API extern "C" __declspec(dllimport)
# endif
#else
# define XP_API extern "C"
#endif
// Self-authored experimental ABI. No claim of compatibility with Xbox exports.
XP_API uint32_t XPVersion();
XP_API uint64_t XPTimeNs();
XP_API void XPSleepMs(uint32_t ms);
// Explicit offset, read-only. Returns bytes read; -1 on error. Caller owns buffer.
XP_API int64_t XPReadAt(const char* path, uint64_t offset, void* buffer, uint32_t size);
// Returns 0 when connected, 1 disconnected, -1 invalid/unsupported. Clears output.
XP_API int XPGetButtons(uint32_t controller, uint32_t* buttons);
// Windows hardware D3D12 clear/present demonstration. 0 success, -1 failure.
XP_API int XPClearDemo(uint32_t frames);
