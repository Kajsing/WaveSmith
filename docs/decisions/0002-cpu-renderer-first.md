# 0002 - CPU Renderer First

WaveSmith v1 uses a CPU renderer because it is easier to inspect, debug, and run locally.

A GPU or shader backend can be added later behind a render backend interface.

Future GPU work should not replace the CPU renderer. The CPU path remains the reference
implementation and fallback. A later GPU milestone should add a backend interface first, then add a
ModernGL or shader implementation behind that interface.
