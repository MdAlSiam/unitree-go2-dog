# Python Activity Pipeline (Go2)

This folder provides a modular Python-first pipeline with a C++ bridge to Unitree SDK2 Go2 camera APIs.

This README is intended to be enough for a new developer to clone the repository on a fresh Ubuntu machine, fetch the external Unitree SDK dependency, build the bridge, connect a Go2 robot, and run the pipeline successfully.

## What is included (v1)

- Modular activity runner (`pipeline/runner.py`)
- Camera module abstraction + Go2 camera adapter (`modules/camera`)
- Speech module abstraction with pluggable backends (`modules/speech`)
- Demo activity that captures camera frames and plays startup/shutdown speech (`activities/see_and_say.py`)
- Main entrypoint (`main.py`)
- C++ shared-library bridge (`bridges/go2_cpp`) copied into `python_pipeline/bin`

## Repository requirements

This pipeline is not standalone.

You must have both of these directories in the same workspace:

- `python_pipeline`
- `unitree_sdk2`

Why this matters:

- `python_pipeline` contains the Python runtime, activities, and `ctypes` wrapper.
- `unitree_sdk2` contains the SDK source and build system used to compile the shared bridge library.

`unitree_sdk2` is a tracked git submodule:

- Remote: `https://github.com/unitreerobotics/unitree_sdk2.git`
- Managed as a git dependency of this repository

Standard clone and setup for new developers (replace `$REPO_URL` with your fork):

```bash
git clone --recurse-submodules $REPO_URL
cd unitree-go2-dog
./setup_sdk.sh
```

If you cloned without `--recurse-submodules`, initialize the submodule:

```bash
git submodule update --init --recursive
./setup_sdk.sh
```

## Fresh machine setup (Ubuntu)

These steps assume a new Ubuntu machine with this repository already cloned.

### 1. Install system dependencies

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

### 2. Create a Python virtual environment

The current Python pipeline uses only standard-library modules, so there is no `requirements.txt` at the moment.

```bash
cd /path/to/unitree-go2-dog
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Initialize `unitree_sdk2` submodule

If you cloned without submodules, initialize it now:

```bash
cd /path/to/unitree-go2-dog
git submodule update --init --recursive
./setup_sdk.sh
```

If you cloned with `--recurse-submodules`, it is already available:

```bash
cd /path/to/unitree-go2-dog
./setup_sdk.sh
```

### 4. Build the camera bridge

From the SDK folder:

```bash
cd /path/to/unitree-go2-dog/unitree_sdk2
cmake -S . -B build -DBUILD_PYTHON_PIPELINE_BRIDGE=ON -DBUILD_EXAMPLES=OFF
cmake --build build -j4
```

This creates and copies:

- `python_pipeline/bin/libgo2_video_bridge.so`

### 5. Verify system speech locally

The default speech backend uses local Linux TTS.

```bash
spd-say "System speech is working"
```

If `spd-say` is unavailable, the pipeline also supports `espeak-ng` and `espeak`.

### 6. Connect the robot

Attach the robot to the new machine and confirm the NIC that is on the robot subnet:

```bash
ip -br addr
```

Look for the interface that has the robot-facing IP address, typically on a `192.168.x.x` subnet.

### 7. Run the pipeline from the repository root

```bash
cd /path/to/unitree-go2-dog
export PIPELINE_SPEECH_PROVIDER=system
export PIPELINE_TICK_HZ=1.0
export PIPELINE_MAX_TICKS=3600
export CAMERA_POLL_EVERY_TICKS=1
PYTHONPATH=. python3 -m python_pipeline.main
```

If explicit NIC binding is needed:

```bash
export GO2_NETWORK_INTERFACE=YOUR_INTERFACE_NAME
PYTHONPATH=. python3 -m python_pipeline.main
```

If explicit NIC binding fails, try auto-selection:

```bash
unset GO2_NETWORK_INTERFACE
PYTHONPATH=. python3 -m python_pipeline.main
```

## Build the bridge

From the SDK folder:

```bash
cd unitree_sdk2
cmake -S . -B build -DBUILD_PYTHON_PIPELINE_BRIDGE=ON -DBUILD_EXAMPLES=OFF
cmake --build build -j4
```

This creates and copies `python_pipeline/bin/libgo2_video_bridge.so`.

If `unitree_sdk2` is missing, run `./setup_sdk.sh` first.

## Run the pipeline

From workspace root (folder containing `python_pipeline` and `unitree_sdk2`):

```bash
PYTHONPATH=. python3 -m python_pipeline.main
```

For a long live session, use something like:

```bash
export PIPELINE_TICK_HZ=1.0
export PIPELINE_MAX_TICKS=100000
PYTHONPATH=. python3 -m python_pipeline.main
```

## SDK dependency (git submodule)

`unitree_sdk2` is managed as a git submodule for reproducible builds.

### Clone with submodule (recommended)

```bash
git clone --recurse-submodules $REPO_URL
cd unitree-go2-dog
./setup_sdk.sh
```

### Initialize submodule if cloned without it

```bash
git clone $REPO_URL
cd unitree-go2-dog
git submodule update --init --recursive
./setup_sdk.sh
```

### Update SDK version

To update to a newer SDK version:

```bash
git submodule update --remote unitree_sdk2
cd unitree_sdk2
git checkout <desired-branch-or-tag>
cd ..
git add unitree_sdk2
git commit -m "Update SDK to [version]"
```

Optional environment variables:

- `GO2_NETWORK_INTERFACE`: network adapter name (example: `enx00e04c6806b0`)
- `PIPELINE_TICK_HZ`: activity tick frequency (default: `0.5`)
- `PIPELINE_MAX_TICKS`: max loop ticks (default: `10`)
- `CAMERA_POLL_EVERY_TICKS`: camera poll interval in ticks (default: `1`)
- `PIPELINE_SPEECH_PROVIDER`: speech backend (`system` or `null`, default: `system`)

## Install system speech (Linux)

The default speech backend is `system`, which calls local Linux TTS commands.

Install one of the supported TTS tools:

```bash
sudo apt-get update
sudo apt-get install -y speech-dispatcher espeak-ng
```

Quick local test:

```bash
spd-say "System speech is working"
```

If `spd-say` is unavailable, the provider also supports `espeak-ng` and `espeak`.

To disable real speech and use log-only mode:

```bash
export PIPELINE_SPEECH_PROVIDER=null
```

## What success looks like

When the pipeline is working correctly, a new developer should observe all of the following:

- Startup logs from `PipelineRunner`, `Go2CameraProvider`, and the speech provider
- Audible startup phrase: `Now I can see you.`
- A live image file written to `python_pipeline/output/frame_live.jpg`
- No crash during activity startup
- Audible shutdown phrase: `See you again later.` when the process is stopped cleanly

## Activities (current)

Current default activity: `see_and_say`

- On start: initializes camera/speech and says `Now I can see you.`
- On each poll tick: reads a frame and writes `python_pipeline/output/frame_live.jpg`
- On stop: says `See you again later.` and shuts down providers

## Common command sequences

### Rebuild bridge after C++ changes

```bash
cd /path/to/unitree-go2-dog/unitree_sdk2
cmake --build build -j4
```

### Run silently without spoken audio

```bash
cd /path/to/unitree-go2-dog
export PIPELINE_SPEECH_PROVIDER=null
PYTHONPATH=. python3 -m python_pipeline.main
```

### Run with one-hour duration at 1 Hz

```bash
cd /path/to/unitree-go2-dog
export PIPELINE_TICK_HZ=1.0
export PIPELINE_MAX_TICKS=3600
export CAMERA_POLL_EVERY_TICKS=1
PYTHONPATH=. python3 -m python_pipeline.main
```

## Troubleshooting for new developers

### `libgo2_video_bridge.so` not found

- Ensure `unitree_sdk2` submodule is initialized: `git submodule update --init --recursive`
- Build the bridge from `unitree_sdk2`.
- Confirm `python_pipeline/bin/libgo2_video_bridge.so` exists.

### Speech works in logs but no audible voice

- Run `spd-say "System speech is working"` directly.
- Check the system speaker/audio output on the new machine.
- Set `PIPELINE_SPEECH_PROVIDER=system`.

### Camera provider starts but frames time out

- Verify the robot is connected and reachable on the expected NIC.
- Try `unset GO2_NETWORK_INTERFACE` so DDS can auto-select the interface.
- Reduce `PIPELINE_TICK_HZ` if needed.

### The pipeline exits too soon

- Increase `PIPELINE_MAX_TICKS`.
- For a long session, `PIPELINE_MAX_TICKS=100000` is acceptable.

## Notes

- Go2 in SDK2 currently exposes VUI controls and camera capture; no native Go2 TTS API is used in v1.
- Speech is modularized. `SystemSpeechProvider` uses local Linux TTS tools (`spd-say`, `espeak-ng`, or `espeak`) when available.

## Further reading

- `python_pipeline/PIPELINE_DEVELOPER_GUIDE.md`
