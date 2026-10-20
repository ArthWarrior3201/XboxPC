# XboxPC v1

An original research foundation for native Xbox/Windows interoperability.
**This release does not run or convert commercial Xbox, Steam, or Epic games.**
It is not derived from AnyPS5 source. No console firmware, SDK code, keys, or game assets are included.

## v1 installed-library launcher

On Windows, install Python 3.10+ with Tkinter (included in the normal python.org installer), then double-click **Start-XboxPC.cmd**, or run:

```powershell
python -m xboxpc gui
python -m xboxpc library
python -m xboxpc launch "steam:123"
```

Use a real key from `library` in place of the example. No login, account linking, passwords, browser cookies or account tokens are requested or read. Sign in to each store through its own app as usual.

The GUI scans at startup and has Refresh and Refresh & launch buttons. Every launch rescans all providers and resolves the selected identity again. Removed or unavailable records are refused. Steam and Epic launches are handed to their installed clients; registered Xbox/Store packages use Windows app activation. These are native PC launches, not Xbox binary translation. A handed-off request is not proof the game started or that an account owns it.

| Provider | Data source | Coverage |
|---|---|---|
| Steam | Current-user Steam registry path, libraryfolders.vdf, appmanifest files | Locally installed apps across discovered library drives |
| Epic | ProgramData Epic installation manifests | Complete installed applications with launch identities |
| Xbox / Microsoft Store | Current-user Windows package inventory, MicrosoftGame.config, Start-menu identities | A subset of registered game packages; inaccessible and legacy packages may be omitted |

This reads the clients' local installation metadata and queries Windows; it does **not** directly request a full online owned library from each app. Buying a new game without installing it will not add it here. Install/update it in its store app, then refresh. Store clients remain responsible for account access and game updates. Installing the Xbox app is not guaranteed on every Windows installation.

Steam/Epic local formats are version-dependent and may change. Xbox coverage is deliberately conservative so ordinary Windows applications are not mislabeled as Xbox games. Detection does not prove ownership, console availability, or translator compatibility.

For custom discovery paths (inspection only):

```powershell
python -m xboxpc library --steam-root "D:\Steam" --epic-manifests "C:\ProgramData\Epic\EpicGamesLauncher\Data\Manifests"
```

GUI and `launch` use automatic paths. The scanner does not force cloud synchronization. Warnings distinguish missing metadata and discovery failures. No permanent library cache is used.

## What works now

- Python CLI inspects unpacked AMD64 PE32+ sections and normal imports without executing them.
- A strict fixture relinker changes a self-authored test executable's imported DLL from `xboxpc_guest.dll` to `xboxpc_host.dll`. CPU instructions are unchanged.
- C++ host runtime implements the project's own XP* test ABI: monotonic clock, sleep, offset file reads, controller buttons, and a Windows D3D12 clear/present demo.
- Direction-specific blocker reports for future Xbox-to-Windows and Windows-to-Xbox work.
- Automated parser, relinker, runtime tests and Windows/Linux GitHub Actions build configuration.

**XP* functions are an invented test interface, not reverse-engineered Xbox exports.**
The executable fixture is a Windows program authored for this project. Relinking it proves an import-retargeting mechanism, not console compatibility. Runtime calls execute natively; this is not a CPU emulator. Relinking is performed ahead of execution, not a real-time binary recompiler.

## Quick start: inspect an executable

Install Python 3.10 or later. Open a terminal in this folder:

```powershell
python -m xboxpc inspect "C:\path\program.exe"
python -m xboxpc plan "C:\path\program.exe" --target windows
python -m xboxpc plan "C:\path\program.exe" --target xbox
python -m unittest discover -s tests -v
```

Inspection is limited to 128 MiB and ordinary, unpacked PE32+ images. It does not unpack XVC/disc/store containers, verify ownership, decrypt content, or determine whether an inspected binary is an Xbox title. A successful inspection is not a compatibility verdict. `plan` produces a blocker report and always marks execution unproven.

## Build the Windows runtime and native demonstration

Requires x64 Windows, Visual Studio C++ build tools, Windows SDK, CMake 3.20+, and Python. With Visual Studio's generator:

```powershell
cmake -S . -B build -A x64
cmake --build build --config Release
ctest --test-dir build -C Release --output-on-failure
New-Item -ItemType Directory -Path dist
python -m xboxpc relink-fixture build/Release/xboxpc_fixture.exe dist/xboxpc_demo.exe
Copy-Item build/Release/xboxpc_host.dll dist/
./dist/xboxpc_demo.exe
./dist/xboxpc_demo.exe --graphics
```

The destination must not exist. If repeating, choose another destination filename.
Keep `xboxpc_host.dll` next to the relinked executable. The guest DLL is a link-time stand-in and is deliberately omitted from `dist`. The normal demo checks clock/sleep and reports controller status. The optional graphics demo opens a green animated D3D12 window for 240 frames; controller buttons change its color. It is a host graphics smoke test, not a game or shader translator. Hardware D3D12 is required; no automatic software fallback is used. The demo waits once per frame for simplicity and makes no speed claim.

The runtime uses the normal C++ runtime supplied by the build toolchain. Install the corresponding x64 Visual C++ runtime if a build reports a missing runtime DLL.

## GitHub Actions

Copy this directory's **contents**, including `.github`, into a new repository. The included `Build and verify XboxPC` workflow:

1. Tests the parser/relinker on Windows and Linux.
2. Builds the native runtime and runs conformance tests.
3. On Windows, relinks the fixture and executes it from a folder containing only the host DLL.
4. Uploads `XboxPC-Windows-x64-research` containing the demo EXE, host DLL, CLI Python files and README.

This workflow has been authored but was **not run in GitHub during preparation**. No hosted build artifact or precompiled Windows EXE is included in this source archive. Graphical tests require a local Windows desktop and are not run in CI.

## Compatibility status

| Capability | Status |
|---|---|
| Normal AMD64 PE metadata and imports | Implemented and locally tested |
| Self-authored fixture import retargeting | Implemented and locally tested on synthetic metadata |
| Portable runtime clock/sleep/read tests | Compiled and tested on Linux |
| Native Windows fixture execution | Implemented; pending Windows build/run |
| Windows XInput and D3D12 backend | Implemented; pending Windows build/run |
| Xbox kernel / GameOS ABI | Not implemented |
| Xbox D3D12X / GPU packets / shaders | Not implemented |
| XAudio2 / DirectStorage compatibility | Not implemented |
| Xbox-to-Windows commercial titles | Unsupported |
| Steam/Epic/Windows-to-Xbox titles | Unsupported |
| Console packaging / installation | Not implemented |

## Constraints

The relinker intentionally only accepts the project's known fixture DLL and exports. It rejects signed images, bound imports, delay imports, CLR images, DLL inputs, ordinal fixture imports, unknown fixture symbols, and existing output files. It does not rewrite arbitrary Win32 or Xbox imports, repair signatures, or modify CPU code. Inspection is not a malware scanner or a sandbox. Only execute trusted self-authored test programs; the host runtime has ordinary process permissions, including file access.

See [architecture](docs/ARCHITECTURE.md), [research plan](docs/ROADMAP.md), and [validation](docs/VALIDATION.md).
