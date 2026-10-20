# Evidence-driven milestones

## M0 — current foundation

PE inspection; self-authored ABI; import patching; native host primitives; Windows D3D12 smoke-test source; CI definition. Finish validation by building on Windows and testing the graphical path on actual hardware.

## M1 — first real platform contract

Select one console generation, OS/build version, and legally usable unpacked self-authored/homebrew sample. Record the sample hash, original imports, initialization behavior, expected output and observed failures. Establish its actual ABI before implementing any mappings. Exit criterion: one real target ABI function implemented with differential evidence, not a function with an Xbox-like name.

## M2 — non-graphical executable bring-up

Support verified loader metadata, address layout, relocations, TLS, exception behavior, thread synchronization and required imports. Test representative cancellation, timeouts, failures and concurrent execution. Exit criterion: a small target-compiled non-graphical test runs correctly through the compatibility layer.

## M3 — graphics semantics

Document one minimal console rendering path, resource layouts, supported shader forms, descriptors and synchronization. Add a host D3D12 translator for only that measured subset. Compare output images and traces; reject unknown packets/operations. Exit criterion: an actual console-targeted triangle/sample works correctly. A native Windows clear screen does not count.

## M4 — small playable homebrew

Input, audio, filesystem namespaces, asynchronous IO and robust diagnostics. Test on multiple CPU/GPU vendors. Measure CPU time, GPU time, frame pacing, compilation time and memory use separately. No arbitrary speedup promises.

## M5 — reverse backend

Specify the Xbox execution environment and available loader; inventory a simple self-authored Windows title's dependencies. Implement a console backend and missing Win32 contracts. Validate on the actual console. This cannot be certified from Windows-only tests.

## M6 — title-specific compatibility

Only claim support for measured titles, versions and reproducible test scenarios. Compatibility entries should include evidence, crashes, visual differences and unfinished services. No commercial title is supported by the current release.
