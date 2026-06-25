# Python Pipeline Developer Guide

This document explains how the Go2 Python pipeline is structured, how data flows through it, and where to make changes safely.

It is also intended to help a new developer clone the repository (including the SDK submodule), build the required bridge library, and verify the full runtime path end to end.

## 0. New Developer Quick Start

If you are new to this repository, do these steps in order:

1. Confirm the repository includes `python_pipeline` and fetch `unitree_sdk2` with `./setup_sdk.sh` if it is missing.
2. Install Ubuntu build dependencies and Linux TTS packages.
3. Create and activate a Python virtual environment.
4. Build the shared C++ bridge from `unitree_sdk2`.
5. Verify local speech with `spd-say`.
6. Connect the robot and identify the correct network interface.
7. Run the pipeline from the repository root.
8. Verify that startup speech plays and `python_pipeline/output/frame_live.jpg` updates.

If any one of those steps fails, stop there and fix that layer before changing code.

## 0.1 Fresh machine prerequisites

This project assumes:

- Ubuntu or a compatible Linux environment
- `python3`
- `cmake`
- `g++`
- standard C++ build tooling
- local audio output configured on the machine

Recommended package install:

```bash
sudo apt-get update
sudo apt-get install -y \
  cmake \
  g++ \
  build-essential \
  libyaml-cpp-dev \
  libeigen3-dev \
  libboost-all-dev \
  libspdlog-dev \
  libfmt-dev \
  speech-dispatcher \
  espeak-ng
```

## 0.2 Repository layout assumption

The pipeline depends on both source trees being present:

- `python_pipeline`
- `unitree_sdk2`

This matters because the Python code does not contain a pure-Python camera implementation. It loads a shared library built from SDK-backed C++ code.

`unitree_sdk2` is tracked as a git submodule at:

- `https://github.com/unitreerobotics/unitree_sdk2.git`

Initialize it after cloning:

```bash
git clone --recurse-submodules <your-project-url>
cd unitree-go2-dog
git submodule update --init --recursive
```

## 0.3 First build on a new machine

Create a virtual environment:

```bash
cd /path/to/unitree-go2-dog
python3 -m venv .venv
source .venv/bin/activate
```

Ensure the submodule is initialized:

```bash
cd /path/to/unitree-go2-dog
git submodule update --init --recursive
```

Build the bridge:

```bash
cd /path/to/unitree-go2-dog/unitree_sdk2
cmake -S . -B build -DBUILD_PYTHON_PIPELINE_BRIDGE=ON -DBUILD_EXAMPLES=OFF
cmake --build build -j4
```

Expected output artifact:

- `python_pipeline/bin/libgo2_video_bridge.so`

## 0.4 First runtime verification on a new machine

Verify speech locally before involving the robot:

```bash
spd-say "System speech is working"
```

Then identify the robot NIC:

```bash
ip -br addr
```

Then run the pipeline:

```bash
cd /path/to/unitree-go2-dog
export PIPELINE_SPEECH_PROVIDER=system
export PIPELINE_TICK_HZ=1.0
export PIPELINE_MAX_TICKS=3600
export CAMERA_POLL_EVERY_TICKS=1
PYTHONPATH=. python3 -m python_pipeline.main
```

If explicit interface binding is necessary:

```bash
export GO2_NETWORK_INTERFACE=YOUR_INTERFACE_NAME
PYTHONPATH=. python3 -m python_pipeline.main
```

If explicit interface binding fails, unset it and let DDS auto-pick:

```bash
unset GO2_NETWORK_INTERFACE
PYTHONPATH=. python3 -m python_pipeline.main
```

## 1. What This Pipeline Does

The pipeline is a small activity runtime:

- It initializes providers (camera, speech).
- It runs one or more activities on a fixed tick loop.
- Activities decide what to do each tick (for example, capture a frame every N ticks).
- On shutdown, providers are stopped in reverse order.

Current default activity:

- `see_and_say`: captures camera images, announces startup/shutdown, and writes a live frame image.

## 2. Key Files and Their Roles

- `main.py`
  - Application entrypoint.
  - Loads settings from environment.
  - Wires concrete providers + activity.
  - Starts `PipelineRunner`.

- `pipeline/runner.py`
  - Tick loop scheduler.
  - Calls activity lifecycle methods (`on_start`, `on_tick`, `on_stop`).

- `pipeline/contracts.py`
  - Core data contracts and protocols (`FrameSample`, `TickContext`, `Activity`, provider protocols).

- `activities/see_and_say.py`
  - Example activity using camera and speech providers.
  - Writes frames into `python_pipeline/output`.

- `modules/camera/go2_camera.py`
  - Python `ctypes` wrapper around the C++ bridge shared library.

- `bridges/go2_cpp/go2_video_bridge.cpp`
  - C ABI bridge that talks to Unitree SDK2 `VideoClient`.

- `config/settings.py`
  - Environment-variable based runtime settings.

- `modules/speech/system_speech.py`
  - Linux TTS backend using `spd-say`, `espeak-ng`, or `espeak`.

- `setup_sdk.sh`
  - Verifies `unitree_sdk2` is present and initialized.
  - Called after `git submodule update --init --recursive`.

## 3. Runtime Flow (End-to-End)

1. `python_pipeline.main` starts.
2. `load_settings()` reads env vars.
3. `Go2CameraProvider` loads `bin/libgo2_video_bridge.so`.
4. `PipelineRunner.run()` starts each activity.
5. Every tick:
   - A `TickContext` is created.
   - Each activity receives `on_tick(context)`.
   - Runner sleeps to maintain target tick frequency.
6. On exit/failure, activities are stopped in reverse order.

What a successful runtime looks like:

- Startup logs appear
- Speech backend starts successfully
- The startup phrase is audible
- `python_pipeline/output/frame_live.jpg` is created or refreshed
- The process remains alive until `max_ticks` is reached or interrupted

## 4. Lifecycle Contracts

### 4.1 Activity contract

Activities should implement:

- `name: str`
- `on_start()`: allocate/open resources
- `on_tick(context: TickContext)`: tick logic
- `on_stop()`: release resources

### 4.2 Camera provider contract

- `start()`
- `read() -> Optional[FrameSample]`
- `stop()`

`read()` should return `None` for "no frame available" and only raise for unrecoverable usage errors.

### 4.3 Speech provider contract

- `start()`
- `say(text: str)`
- `stop()`

Current speech backends:

- `SystemSpeechProvider`: default runtime backend; calls local Linux TTS commands (`spd-say`, `espeak-ng`, or `espeak`) when installed.
- `NullSpeechProvider`: log-only backend for silent/testing runs.

## 4.4 Available Control Surfaces

This section lists what can be controlled today from Python, and what control APIs are present in `unitree_sdk2` examples but not yet exposed through the Python pipeline.

### 4.4.1 Python control surfaces (available now)

| Surface | Python API | Location |
|---|---|---|
| Activity lifecycle | `on_start()`, `on_tick(context)`, `on_stop()` | `pipeline/contracts.py` (`Activity` protocol) |
| Camera provider contract | `start()`, `read()`, `stop()` | `modules/camera/base.py` (`CameraProviderBase`) |
| Speech provider contract | `start()`, `say(text)`, `stop()` | `modules/speech/base.py` (`SpeechProviderBase`) |
| Concrete Go2 camera provider | `start()`, `read()`, `stop()` | `modules/camera/go2_camera.py` (`Go2CameraProvider`) |
| Concrete system speech provider | `start()`, `say(text)`, `stop()` | `modules/speech/system_speech.py` (`SystemSpeechProvider`) |
| Current default activity | `SeeAndSayActivity` | `activities/see_and_say.py` |
| Entrypoint wiring | one activity instance passed to runner | `main.py` |

### 4.4.2 SDK control surfaces (available in C++ examples)

The following APIs are demonstrated under `unitree_sdk2/example/go2/`:

| SDK client | APIs seen in examples | Example file |
|---|---|---|
| `SportClient` | `StandUp()`, `StandDown()`, `BalanceStand()`, `Move(vx, vy, vyaw)`, `Damp()`, `RecoveryStand()`, `Sit()`, `RiseSit()`, `StopMove()` | `go2_sport_client.cpp` |
| `SportClient` (trajectory) | `TrajectoryFollow(path)` | `go2_trajectory_follow.cpp` |
| `RobotStateClient` | `GetApiVersion()`, `GetServerApiVersion()`, `SetReportFreq(...)`, `ServiceSwitch(...)`, `ServiceList(...)` | `go2_robot_state_client.cpp` |
| `MotionSwitcherClient` | `CheckMode(...)`, `ReleaseMode()` | `go2_stand_example.cpp` |
| `VideoClient` | `GetImageSample(...)` | `go2_video_client.cpp` |
| `VuiClient` | `SetBrightness(...)`, `GetBrightness(...)` | `go2_vui_client.cpp` |

### 4.4.3 Current gap and extension path

- Current Python pipeline wiring in `main.py` exposes camera and speech, and ships one activity (`see_and_say`).
- A Python-accessible Go2 sport provider is now available (`modules/sport/go2_sport.py`) via `libgo2_sport_bridge.so`.
- To use motion in activities, instantiate `Go2SportProvider`, call `start()`, and inject it into your activity alongside camera/speech providers.
- `Go2SportProvider` can optionally take a speech provider and announce actions such as standing up, moving, and stopping move.
- `move()` now clamps out-of-range velocity inputs to conservative values before forwarding them to the SDK.

### 4.4.4 Exposure matrix (quick scan)

| Control surface | Exposed in Python pipeline | Source |
|---|---|---|
| Activity lifecycle (`Activity`) | Yes | `pipeline/contracts.py` |
| Camera provider (`CameraProviderBase`) | Yes | `modules/camera/base.py` |
| Speech provider (`SpeechProviderBase`) | Yes | `modules/speech/base.py` |
| Sport provider (`SportProviderBase`) | Yes | `modules/sport/base.py` |
| `SeeAndSayActivity` | Yes | `activities/see_and_say.py` |
| `VideoClient::GetImageSample(...)` | Yes (indirect via bridge) | `bridges/go2_cpp/go2_video_bridge.cpp`, `modules/camera/go2_camera.py` |
| `SportClient` motion controls | Yes (indirect via bridge) | `bridges/go2_cpp/go2_sport_bridge.cpp`, `modules/sport/go2_sport.py` |
| Sport action notifications | Yes, optional | `modules/sport/go2_sport.py` |
| `move()` velocity clamping | Yes | `modules/sport/go2_sport.py` |
| `SportClient::TrajectoryFollow(path)` | Partial (`go2_sport_trajectory_follow` currently returns unsupported) | `bridges/go2_cpp/go2_sport_bridge.cpp`, `modules/sport/go2_sport.py` |
| `VuiClient` controls | No | `unitree_sdk2/example/go2/go2_vui_client.cpp` |
| `RobotStateClient` service/state controls | No | `unitree_sdk2/example/go2/go2_robot_state_client.cpp` |
| `MotionSwitcherClient` mode controls | No | `unitree_sdk2/example/go2/go2_stand_example.cpp` |

## 5. Tick Timing Model

`PipelineRunner` computes:

- `tick_period = 1.0 / tick_hz`

For each tick:

- `elapsed = time spent running all activities`
- `remaining = tick_period - elapsed`
- If `remaining > 0`, it sleeps for `remaining`.

Implications:

- If activity work is too slow (`elapsed > tick_period`), ticks run late.
- There is currently no drift correction, skipped ticks, or per-activity timeout.

## 6. Camera Bridge Details

The Python camera provider calls these C functions from the shared library:

- `go2_video_init(const char* network_interface)`
- `go2_video_get_frame(void** out_data, int* out_size)`
- `go2_video_free_frame(uint8_t* data)`
- `go2_video_shutdown()`

### 6.1 Memory ownership

`go2_video_get_frame` allocates a heap buffer (`new[]`) and returns pointer + size.
Python copies bytes with `ctypes.string_at(...)` and then must free using `go2_video_free_frame(...)`.

If you add new bridge APIs, keep ownership rules explicit and symmetrical.

### 6.2 Threading

The C++ bridge protects global state with a `std::mutex`.
Current design is process-global singleton style for one camera client.

### 6.3 Error codes currently used

- `0`: success
- `-1`: init exception
- `-2`: invalid output pointers passed to `go2_video_get_frame`
- `-3`: get frame called before successful init
- `-4`: allocation failure
- positive/non-zero values: propagated Unitree SDK return codes

Python side logs frame-read errors and returns `None` for non-zero frame read codes.

## 7. Configuration Reference

Environment variables consumed by `config/settings.py`:

- `GO2_NETWORK_INTERFACE`: network interface name for SDK channel init
- `PIPELINE_TICK_HZ` (float, default `0.5`)
- `PIPELINE_MAX_TICKS` (int, default `10`)
- `CAMERA_POLL_EVERY_TICKS` (int, default `1`, clamped to min `1`)
- `PIPELINE_SPEECH_PROVIDER` (`system` or `null`, default `system`)

Recommended values for a first successful run:

- `PIPELINE_SPEECH_PROVIDER=system`
- `PIPELINE_TICK_HZ=1.0`
- `PIPELINE_MAX_TICKS=3600`
- `CAMERA_POLL_EVERY_TICKS=1`

Common examples:

```bash
export GO2_NETWORK_INTERFACE=enx00e04c6806b0
export PIPELINE_TICK_HZ=2.0
export PIPELINE_MAX_TICKS=30
export CAMERA_POLL_EVERY_TICKS=2
export PIPELINE_SPEECH_PROVIDER=system
PYTHONPATH=. python3 -m python_pipeline.main
```

## 8. How To Add a New Activity

1. Create a file in `activities/`, for example `activities/patrol.py`.
2. Implement `name`, `on_start`, `on_tick`, and `on_stop`.
3. Keep `on_tick` fast; move heavy work to background workers if needed.
4. Wire it in `main.py` by adding to the `PipelineRunner(activities=[...])` list.

Recommended pattern:

- Validate dependencies in `on_start`.
- Treat missing sensor data as normal (`None`) rather than fatal.
- Use structured logging (include tick index and key IDs).

## 8.1 Current Activity Behavior (Beginner Reference)

`activities/see_and_say.py` currently does the following:

- `on_start`: starts camera/speech and says `Now I can see you.`
- `on_tick`: reads camera frames and writes `python_pipeline/output/frame_live.jpg`
- `on_stop`: says `See you again later.` and shuts down providers

This is intentionally simple and beginner-friendly so new developers can verify camera and speech quickly.

Why it writes a single file:

- `frame_live.jpg` is easier for beginners to inspect live because it is replaced continuously.
- It avoids filling the output directory with thousands of files during long runs.

## 9. How To Replace Null Speech

1. Create new provider under `modules/speech/`, for example `go2_vui_speech.py` or `remote_tts.py`.
2. Implement `SpeechProviderBase` methods.
3. Switch provider construction in `main.py`.

Important: Go2 SDK2 exposes VUI controls (volume/brightness/switch), but not native text-to-speech in this pipeline.

Practical implication:

- The current audible voice comes from the developer machine speakers, not from a native Go2 onboard TTS API.

## 10. How To Extend the C++ Bridge

When adding bridge functions:

1. Add declarations in `go2_video_bridge.hpp` using `extern "C"`.
2. Implement in `go2_video_bridge.cpp` with explicit error codes.
3. Update bridge `CMakeLists.txt` only if new source files are added.
4. Expose new signatures in Python `ctypes` (`argtypes` + `restype`).
5. Keep pointer ownership and free routines unambiguous.

Rebuild from `unitree_sdk2`:

```bash
cmake -S . -B build -DBUILD_PYTHON_PIPELINE_BRIDGE=ON -DBUILD_EXAMPLES=OFF
cmake --build build -j4
```

If `unitree_sdk2` is missing, initialize the submodule:

```bash
git submodule update --init --recursive
```

## 11. Troubleshooting Checklist

### No audible speech output

- Ensure `PIPELINE_SPEECH_PROVIDER=system`.
- Install Linux speech packages:

```bash
sudo apt-get update
sudo apt-get install -y speech-dispatcher espeak-ng
```

- Verify local TTS manually:

```bash
spd-say "System speech is working"
```

- If no TTS command is installed, the provider falls back to log-only speech messages.

### A new developer wants to know whether setup succeeded

Use this checklist:

- `unitree_sdk2` submodule is initialized: `git submodule status unitree_sdk2` shows no leading `-`
- `python_pipeline/bin/libgo2_video_bridge.so` exists
- `spd-say "System speech is working"` works locally
- startup log shows camera provider started
- startup log shows system speech provider started
- audible phrase `Now I can see you.` is heard
- `python_pipeline/output/frame_live.jpg` exists and changes during runtime

If one of these is missing, debug that layer before continuing.

### Bridge library not found

- Symptom: `FileNotFoundError` from `Go2CameraProvider`.
- Initialize the `unitree_sdk2` submodule: `git submodule update --init --recursive`
- Check that `python_pipeline/bin/libgo2_video_bridge.so` exists.
- Rebuild bridge and verify post-build copy step.

### Cannot initialize camera bridge

- Symptom: `RuntimeError` with init failure code.
- Verify robot/network reachability.
- Set `GO2_NETWORK_INTERFACE` explicitly.
- If explicit interface selection fails, try `unset GO2_NETWORK_INTERFACE`.
- Confirm SDK dependencies are available on runtime linker path.

### Frequent "No frame available"

- Verify robot video service state and network quality.
- Reduce `PIPELINE_TICK_HZ` to lower polling pressure.
- Confirm `CAMERA_POLL_EVERY_TICKS` is not too sparse for your expectation.

### The pipeline exits earlier than expected

- Check `PIPELINE_MAX_TICKS`.
- Remember runtime length is roughly `PIPELINE_MAX_TICKS / PIPELINE_TICK_HZ` seconds.
- For long demonstrations, values like `3600` or `100000` are reasonable.

### Output images not appearing

- Confirm activity `see_and_say` is wired into runner.
- Check write permissions for `python_pipeline/output`.
- Look at logs for frame read warnings and tick numbers.

## 12. Known Design Limits (Current Version)

- Single-process, single-thread tick loop.
- No built-in retry/backoff policy in providers.
- No metrics endpoint.
- No persistent state/checkpointing.
- Camera bridge uses global singleton state (single camera client).

These are good areas for future hardening if you move beyond demos.

## 13. Suggested Onboarding Path For New Developers

1. Complete the fresh-machine setup and build steps in section 0.
2. Run the pipeline once and verify speech plus live frame output.
3. Read `main.py` and `pipeline/runner.py` first.
4. Follow one frame path: `see_and_say -> go2_camera -> C++ bridge`.
5. Change one setting (`PIPELINE_TICK_HZ`) and observe behavior.
6. Add a minimal second activity that only logs ticks.

This sequence gives the fastest understanding of control flow, timing, and extension seams.

## 13.1 Updating the SDK Version

Since `unitree_sdk2` is a tracked submodule, SDK version updates must be committed to the root repository.

Update to a new SDK version:

```bash
cd /path/to/unitree-go2-dog
git submodule update --remote unitree_sdk2
cd unitree_sdk2
git checkout <desired-tag-or-branch>
cd ..
git add unitree_sdk2
git commit -m "Update SDK to [version]"
git push
```

Clone and check out that version:

```bash
git clone --recurse-submodules <your-project-url>
cd unitree-go2-dog
./setup_sdk.sh
```

## 13.2 How To Run The Sport Provider

The default `python_pipeline.main` entrypoint still runs the camera + speech demo activity. The sport API is exposed as a Python provider and is meant to be imported from your own script or activity.

Build the bridge first:

```bash
cd /path/to/unitree-go2-dog/unitree_sdk2
cmake -S . -B build -DBUILD_PYTHON_PIPELINE_BRIDGE=ON -DBUILD_EXAMPLES=OFF
cmake --build build -j4 --target go2_sport_bridge
```

Then use it from Python:

```python
from python_pipeline.modules.sport.go2_sport import Go2SportProvider

sport = Go2SportProvider(network_interface="")
sport.start()
sport.stand_up()
sport.balance_stand()
sport.start_stand_guard(interval_s=1.0)

# Long stand / idle section
# Keep your script alive while the guard thread refreshes balance stand.
# ...

sport.stop_stand_guard()
sport.move(0.2, 0.0, 0.0)
sport.stop_move()
sport.stand_down()
sport.stop()
```

If you want to call it from a file, run it from the repository root so `python_pipeline` is on `PYTHONPATH`:

```bash
PYTHONPATH=. python3 your_script.py
```

Important:

- `main.py` does not automatically use `Go2SportProvider` yet.
- The sport provider is a control surface, not a standalone app.
- For long standing sessions, prefer `balance_stand()` and `start_stand_guard(...)` to reduce unstable idle behavior.
- `move(vx, vy, vyaw)` clamps out-of-range inputs to conservative limits before sending commands.
- `move(...)` sends a short burst of velocity commands for better command latching; call it repeatedly for continuous travel.
- `stop_move()` also sends a short stop-command burst for reliable halt behavior.
- You should keep the robot in a safe state and verify the target motion call before expanding the sequence.

## 14. Comprehensive Flowchart

```mermaid
flowchart TD
  A[Start: python -m python_pipeline.main] --> B[configure_logging]
  B --> C[load_settings from environment]
  C --> D[Resolve bridge path: python_pipeline/bin/libgo2_video_bridge.so]
  D --> E[Construct Go2CameraProvider]
  E --> F[Load shared library with ctypes]
  F --> G[Bind C symbols and signatures]
  G --> H[Construct speech provider from setting]
  H --> I[Construct SeeAndSayActivity]
  I --> J[Construct PipelineRunner]
  J --> K[runner.run max_ticks]

  K --> L[Log pipeline start]
  L --> M[For each activity: on_start]

  M --> N[SeeAndSayActivity.on_start]
  N --> O[Create output directory]
  O --> P[camera.start]
  P --> Q[go2_video_init]
  Q --> R{network interface set?}
  R -->|yes| S[ChannelFactory.Init 0, interface]
  R -->|no| T[ChannelFactory.Init 0]
  S --> U[Create Unitree VideoClient]
  T --> U
  U --> V[Set timeout and Init client]
  V --> W[speech.start]
  W --> W1[speech.say Now I can see you]
  W1 --> X[Enter tick loop]

  X --> Y[Create TickContext tick_index and now]
  Y --> Z[For each activity: on_tick]

  Z --> AA[SeeAndSayActivity.on_tick]
  AA --> AB{tick_index mod poll_every_ticks == 0?}
  AB -->|no| AC[Skip work for this tick]
  AB -->|yes| AD[camera.read]

  AD --> AE[go2_video_get_frame out_data out_size]
  AE --> AF{bridge initialized?}
  AF -->|no| AG[Return error code]
  AF -->|yes| AH[VideoClient.GetImageSample]
  AH --> AI{SDK returns frame bytes?}
  AI -->|no| AJ[Return non-zero code or empty frame]
  AI -->|yes| AK[Allocate heap buffer and copy frame bytes]
  AK --> AL[Return pointer and size to Python]

  AG --> AM[Python logs warning and returns None]
  AJ --> AM
  AL --> AN[Python copies bytes into FrameSample]
  AN --> AO[Python frees bridge buffer]
  AO --> AP{FrameSample exists?}
  AM --> AP

  AP -->|no| AQ[Log no frame available]
  AP -->|yes| AR[Write JPEG to python_pipeline/output]
  AR --> AS[Log saved frame path and size]
  AS --> AT[Continue without per-frame speech]

  AC --> AU[Tick work complete]
  AQ --> AU
  AT --> AU
  AU --> AV[Compute elapsed time]
  AV --> AW[remaining = tick_period - elapsed]
  AW --> AX{remaining > 0?}
  AX -->|yes| AY[sleep remaining]
  AX -->|no| AZ[Continue immediately, tick overran budget]
  AY --> BA{max_ticks reached?}
  AZ --> BA
  BA -->|no| Y
  BA -->|yes| BB[Begin shutdown]

  BB --> BC[Stop activities in reverse order]
  BC --> BD[SeeAndSayActivity.on_stop]
  BD --> BE0[speech.say See you again later]
  BE0 --> BE[speech.stop]
  BE --> BF[camera.stop]
  BF --> BG[go2_video_shutdown]
  BG --> BH[Reset global VideoClient state]
  BH --> BI[Log pipeline finished]
  BI --> BJ[Return 0]

  Q --> BK{init exception?}
  BK -->|yes| BL[Return -1]
  BL --> BM[Go2CameraProvider.start raises RuntimeError]
  BM --> BB
```

If your Mermaid renderer does not open links inside nodes, use this clickable map:

| Flow Node | Link |
|---|---|
| A | [main.py:24](./main.py#L24) |
| B | [main.py:16](./main.py#L16) |
| C | [config/settings.py:17](./config/settings.py#L17) |
| D | [main.py:29](./main.py#L29) |
| E | [modules/camera/go2_camera.py:14](./modules/camera/go2_camera.py#L14) |
| F | [modules/camera/go2_camera.py:20](./modules/camera/go2_camera.py#L20) |
| G | [modules/camera/go2_camera.py:34](./modules/camera/go2_camera.py#L34) |
| H | [main.py:34](./main.py#L34) |
| I | [activities/see_and_say.py:11](./activities/see_and_say.py#L11) |
| J | [pipeline/runner.py:10](./pipeline/runner.py#L10) |
| K | [pipeline/runner.py:19](./pipeline/runner.py#L19) |
| L | [pipeline/runner.py:22](./pipeline/runner.py#L22) |
| M | [pipeline/runner.py:23](./pipeline/runner.py#L23) |
| N | [activities/see_and_say.py:27](./activities/see_and_say.py#L27) |
| O | [activities/see_and_say.py:28](./activities/see_and_say.py#L28) |
| P | [modules/camera/go2_camera.py:48](./modules/camera/go2_camera.py#L48) |
| Q | [bridges/go2_cpp/go2_video_bridge.cpp:20](./bridges/go2_cpp/go2_video_bridge.cpp#L20) |
| R | [bridges/go2_cpp/go2_video_bridge.cpp:26](./bridges/go2_cpp/go2_video_bridge.cpp#L26) |
| S | [bridges/go2_cpp/go2_video_bridge.cpp:27](./bridges/go2_cpp/go2_video_bridge.cpp#L27) |
| T | [bridges/go2_cpp/go2_video_bridge.cpp:29](./bridges/go2_cpp/go2_video_bridge.cpp#L29) |
| U | [bridges/go2_cpp/go2_video_bridge.cpp:34](./bridges/go2_cpp/go2_video_bridge.cpp#L34) |
| V | [bridges/go2_cpp/go2_video_bridge.cpp:35](./bridges/go2_cpp/go2_video_bridge.cpp#L35) |
| W | [modules/speech/system_speech.py:17](./modules/speech/system_speech.py#L17) |
| W1 | [modules/speech/system_speech.py:29](./modules/speech/system_speech.py#L29) |
| X | [pipeline/runner.py:27](./pipeline/runner.py#L27) |
| Y | [pipeline/contracts.py:14](./pipeline/contracts.py#L14) |
| Z | [pipeline/runner.py:30](./pipeline/runner.py#L30) |
| AA | [activities/see_and_say.py:33](./activities/see_and_say.py#L33) |
| AB | [activities/see_and_say.py:34](./activities/see_and_say.py#L34) |
| AC | [activities/see_and_say.py:35](./activities/see_and_say.py#L35) |
| AD | [modules/camera/go2_camera.py:58](./modules/camera/go2_camera.py#L58) |
| AE | [bridges/go2_cpp/go2_video_bridge.cpp:46](./bridges/go2_cpp/go2_video_bridge.cpp#L46) |
| AF | [bridges/go2_cpp/go2_video_bridge.cpp:51](./bridges/go2_cpp/go2_video_bridge.cpp#L51) |
| AG | [bridges/go2_cpp/go2_video_bridge.cpp:52](./bridges/go2_cpp/go2_video_bridge.cpp#L52) |
| AH | [bridges/go2_cpp/go2_video_bridge.cpp:57](./bridges/go2_cpp/go2_video_bridge.cpp#L57) |
| AI | [bridges/go2_cpp/go2_video_bridge.cpp:58](./bridges/go2_cpp/go2_video_bridge.cpp#L58) |
| AJ | [bridges/go2_cpp/go2_video_bridge.cpp:59](./bridges/go2_cpp/go2_video_bridge.cpp#L59) |
| AK | [bridges/go2_cpp/go2_video_bridge.cpp:67](./bridges/go2_cpp/go2_video_bridge.cpp#L67) |
| AL | [bridges/go2_cpp/go2_video_bridge.cpp:74](./bridges/go2_cpp/go2_video_bridge.cpp#L74) |
| AM | [modules/camera/go2_camera.py:64](./modules/camera/go2_camera.py#L64) |
| AN | [modules/camera/go2_camera.py:76](./modules/camera/go2_camera.py#L76) |
| AO | [modules/camera/go2_camera.py:74](./modules/camera/go2_camera.py#L74) |
| AP | [activities/see_and_say.py:37](./activities/see_and_say.py#L37) |
| AQ | [activities/see_and_say.py:38](./activities/see_and_say.py#L38) |
| AR | [activities/see_and_say.py:42](./activities/see_and_say.py#L42) |
| AS | [activities/see_and_say.py:43](./activities/see_and_say.py#L43) |
| AT | [activities/see_and_say.py:33](./activities/see_and_say.py#L33) |
| AU | [pipeline/runner.py:30](./pipeline/runner.py#L30) |
| AV | [pipeline/runner.py:31](./pipeline/runner.py#L31) |
| AW | [pipeline/runner.py:32](./pipeline/runner.py#L32) |
| AX | [pipeline/runner.py:33](./pipeline/runner.py#L33) |
| AY | [pipeline/runner.py:34](./pipeline/runner.py#L34) |
| AZ | [pipeline/runner.py:27](./pipeline/runner.py#L27) |
| BA | [pipeline/runner.py:27](./pipeline/runner.py#L27) |
| BB | [pipeline/runner.py:36](./pipeline/runner.py#L36) |
| BC | [pipeline/runner.py:36](./pipeline/runner.py#L36) |
| BD | [activities/see_and_say.py:53](./activities/see_and_say.py#L53) |
| BE0 | [modules/speech/system_speech.py:29](./modules/speech/system_speech.py#L29) |
| BE | [modules/speech/system_speech.py:44](./modules/speech/system_speech.py#L44) |
| BF | [modules/camera/go2_camera.py:80](./modules/camera/go2_camera.py#L80) |
| BG | [bridges/go2_cpp/go2_video_bridge.cpp:83](./bridges/go2_cpp/go2_video_bridge.cpp#L83) |
| BH | [bridges/go2_cpp/go2_video_bridge.cpp:85](./bridges/go2_cpp/go2_video_bridge.cpp#L85) |
| BI | [pipeline/runner.py:39](./pipeline/runner.py#L39) |
| BJ | [main.py:46](./main.py#L46) |
| BK | [bridges/go2_cpp/go2_video_bridge.cpp:38](./bridges/go2_cpp/go2_video_bridge.cpp#L38) |
| BL | [bridges/go2_cpp/go2_video_bridge.cpp:41](./bridges/go2_cpp/go2_video_bridge.cpp#L41) |
| BM | [modules/camera/go2_camera.py:53](./modules/camera/go2_camera.py#L53) |