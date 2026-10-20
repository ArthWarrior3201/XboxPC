# Validation of v1

Executed in a Linux environment during preparation:

- `python3 -m unittest discover -s tests -v`: **30 tests passed**.
- Tests include full truncation coverage for the synthetic PE, wrong architecture, malformed import directories, out-of-range RVAs, ordinal and unknown-symbol rejection, special-directory rejection, repeat relinking, output overwrite protection, direction reports, and 2,000 deterministically mutated inputs.
- `g++ -std=c++17 -Wall -Wextra -Werror -fsanitize=address,undefined -g runtime/host.cpp runtime/runtime_test.cpp`: compiled successfully.
- `ASAN_OPTIONS=detect_leaks=0 ./runtime_test`: **passed**, testing clock/sleep, read offsets, EOF, invalid parameters, and invalid controller indexes.

LeakSanitizer could not operate inside the execution environment, so leak detection was disabled for that run. AddressSanitizer and UndefinedBehaviorSanitizer remained enabled.

Not verified here:

- Windows C++ compilation, PE output from MSVC, native relinked execution, XInput devices, hardware D3D12 rendering.
- CMake configuration (CMake was not installed locally); runtime compilation used g++ directly.
- GitHub Actions execution (no destination repository exists).
- Any Xbox binary, commercial game, reverse conversion, or console hardware.

The CI workflow provides the next Windows build and native-execution checks. A passing future CI run will still not validate commercial game compatibility or graphical correctness.

## v1 library validation

14 added automated tests passed, for 30 total. Tests use temporary Steam/Epic manifest fixtures and mocked Windows package responses: multiple library drives, changed metadata, malformed records, partial installations, DLC exclusion, launch identity encoding, refresh on every launch, removal refusal, timeout handling, failed opener propagation, and honest installed-only scope.

Real Steam, Epic and Xbox clients were not available in this Linux environment. Windows package enumeration, actual store URI handling, real account changes and the Tkinter GUI have not been end-to-end tested. These fixture tests must not be described as proof of live account-library synchronization. No game was launched during preparation.
