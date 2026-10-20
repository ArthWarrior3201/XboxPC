# XboxPC architecture and boundaries

## Direction: console to Windows

The long-term design is an executable adapter plus user-mode compatibility libraries, with native execution of compatible CPU instructions and explicit translation of observable platform semantics. The current milestone only exercises DLL import retargeting on our own fixture. It does not map or execute console code.

Proposed layers, not all implemented:

1. Image/container identification. Ordinary PE metadata inspection exists. Console package extraction and loader variants do not.
2. ABI inventory. Collect exact module names, export versions, ordinals, structures, call conventions and error behavior from permitted samples. No invented Xbox function addresses or hypercall identifiers.
3. Runtime implementations. Memory reservations, page behavior, TLS, exceptions, threads, waits, files and services need verified contracts. The present XP* ABI establishes a test harness only.
4. Graphics translation. Translate supported console interfaces or command streams to host D3D12, preserving resource states, descriptors, fences and layout semantics. The current D3D12 demo does none of that translation.
5. Shader handling. Identify actual container and instruction formats. Recompile or translate where needed; fail explicitly when unsupported.

The Xbox hypervisor/System OS/Game OS separation is a relevant architectural boundary, not three Windows DLLs to rename. A user-mode compatibility layer should reproduce the interfaces actually observed by the title. It need not reproduce a dashboard just because a physical console has one. Kernel-driver requests, privileged instructions, hypercalls, direct GPU submissions and partition-specific services must each be characterized when encountered; this project currently handles none of them. It would be inaccurate to assume every game API call is a hypercall.

Shared x86-64 removes some instruction-set translation work, not process ABI, available instruction subsets, memory mapping, executable loading, synchronization or GPU differences. PS5 also uses x86-64 CPUs; that property is not unique to Xbox. Xbox One and Series must be investigated as separate target profiles rather than assumed interchangeable.

Shared HLSL source language does not establish binary shader compatibility. Microsoft distinguishes the Xbox graphics driver and DirectX shader compiler from the PC GDK. Console-native GPU code, memory layouts or extension semantics cannot simply be handed to arbitrary NVIDIA or AMD PC drivers. Related XAudio2, XInput/GameInput and streaming APIs likewise need version- and behavior-specific verification. No blanket claim is made that all games use the same APIs or DirectStorage.

## Direction: Windows to console

This is a separate backend, not the inverse of changing a DLL name. A PC title may depend on Win32 desktop features, store clients, online services, codecs, middleware, anti-cheat, device capabilities and shaders absent on the target. The target loader/package format, available execution environment, console generation and OS version must be specified and tested. A modified console alone does not supply those missing implementations.

XboxPC currently emits only a blocker report for this direction. There is no executable generation, package installer or console runtime. Source-level ports using an appropriate development environment and binary compatibility research are distinct paths. Purchasing a game through a store does not supply source code or missing platform libraries; this project includes no store-login, entitlement-transfer or DRM tooling. The v1 local-library launcher reads installation records and delegates native PC launches to existing clients; it is separate from binary translation.

## Current test path

`self-authored Windows fixture -> checked DLL import edit -> Windows loader -> xboxpc_host.dll -> host APIs`

The C++ demo imports XPVersion, XPTimeNs, XPSleepMs, XPGetButtons and XPClearDemo. XPReadAt is covered independently by runtime conformance tests. Original CPU code, sections and relocations are retained. No guest process, VM or instruction interpreter is used. Unsupported images fail before output creation.

## Sources consulted

- AnyPS5 README and architecture, inspected as architectural references; no code copied:
  https://github.com/boykopovar/AnyPS5
  https://github.com/boykopovar/AnyPS5/blob/main/docs/dev/ARCHITECTURE.md
- Microsoft PE format, used for normal PE parsing:
  https://learn.microsoft.com/en-us/windows/win32/debug/pe-format
- Microsoft GDK overview and distinctions between PC and console development:
  https://github.com/microsoft/GDK/blob/Main/README.MD
  https://learn.microsoft.com/en-us/gaming/gdk/docs/gdk-dev/intro/introduction

These sources are not a complete specification of proprietary console interfaces. Architecture decisions above distinguish verified host functionality from future research requirements.

## v1 library discovery references

- Windows current-user Start-menu inventory and its omissions:
  https://learn.microsoft.com/en-us/powershell/module/startlayout/get-startapps
  https://learn.microsoft.com/en-us/windows/configuration/store/find-aumid
- XPackage enumeration is scoped, not an arbitrary account library API:
  https://learn.microsoft.com/en-us/gaming/gdk/docs/reference/system/xpackage/functions/xpackageenumeratepackages
- Epic documents local manifests as installation metadata:
  https://dev.epicgames.com/documentation/unreal-engine/multiple-launcher-unreal-engine-installs

Steam VDF/Epic JSON parsing and URI routes are best-effort client integrations, not a vendor guarantee that an entire account library can be queried without authentication. Actual Windows integration validation remains pending.
