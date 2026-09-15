# TD — Modular Mapping System for Expressive Robot Puppeteering

A TouchDesigner operator library for building reconfigurable mappings between
arbitrary control inputs (MIDI, gamepad, keyboard, leader arm) and the joints of
a robotic motion rig. Operators exchange a **joint-angle vector** as their common
data format, which keeps them independent of both the controller hardware and the
robot's kinematics, so mapping structures can be rewired without touching the rest
of the chain.

This is the software artifact for:

> TODO — paper title, authors, venue, year, DOI/arXiv link
> TODO — MSc thesis title and repository link

---

## Prerequisites

### Software
%to chech
| Requirement | Version | Notes |
|---|---|---|
| TouchDesigner | TODO — exact build, e.g. `2023.11xxx` | `.toe`/`.tox` files **cannot** be opened by a build older than the one that saved them. Non-commercial licence is sufficient. |
| Python | 3.11 | Must match the interpreter your TouchDesigner build ships with. Check with `import sys; print(sys.version)` in the Textport. |
| Git | any | Recommended over ZIP download — see the folder-name warning below. |

### Hardware

The system is robot-agnostic, but the operators in `own_comps/robots/` are written
for specific targets:

- **SO-101 arm** with Waveshare ST3215 servos — the primary platform used in the
  study. Connects over USB serial via `feetech-servo-sdk`.
%to check do we support Braccios? I think we did.
- **Arduino Braccio** — serial, via `robot_Braccio_serial.tox`.
- **Any OSC-capable target** — via `robot_so101_osc.tox` / `robot_manual_osc.tox`.

Controller inputs used during development: MIDI launchpad, gamepad, keyboard, and
a second SO-101 used as a teleoperation leader arm. None of these are required —
any TouchDesigner input source can be wired in.

You can open the project and explore the mapping chains without any robot
connected; only the `robot` operator needs hardware.

---

## Installation

### 1. Get the files

```bash
git clone https://github.com/ChrisHoltland/TD.git
cd TD
```

> **The root folder must be named exactly `TD`.** The project resolves the virtual
> environment relative to this name. If you downloaded a ZIP, it extracts as
> `TD-main` — rename it to `TD` before continuing, or nothing will initialise.

### 2. Create the virtual environment

**Windows**

```cmd
python -m venv TD_vEnv
TD_vEnv\Scripts\activate
pip install -r requirements.txt
```

(PowerShell: `.\TD_vEnv\Scripts\activate.ps1`)

**macOS**

```bash
python3 -m venv TD_vEnv
```

Before installing, apply the macOS path fix. TouchDesigner on macOS looks for
`site-packages` under a version-named folder, which `venv` does not create:

```bash
mkdir -p TD_vEnv/lib/python3.11
mv TD_vEnv/lib/site-packages TD_vEnv/lib/python3.11/
```

Replace `python3.11` with whatever `print(sys.version)` reports in your Textport.
Then:

```bash
source TD_vEnv/bin/activate
pip install -r requirements.txt
```

You'll know the environment is active when `(TD_vEnv)` appears at the front of your
terminal prompt.

### 3. Point TouchDesigner at it

1. Open `conference.toe`.
2. **Edit → Preferences → Python** — set the Python Module Path to your `TD` folder.
3. Open the Textport (`Alt+T` / `Cmd+T`). No initialisation errors means you're set.

> `TDPyEnvManagerContext.json` contains an absolute path from the original
> development machine. Edit `installPath` to your own `TD` directory if the
> environment manager doesn't pick up the venv.

### 4. Connect a robot

1. Select the `robot` operator and press `P` to open its parameters.
2. Choose the correct COM (Windows) or `/dev/tty.*` (macOS) serial port.
3. Enable **Torques**.
4. Double-click the operator to force it to cook.

---

## Repository structure

```
TD/
├── conference.toe              # main project file
├── demo.12.toe                 # TODO — appears identical to conference.toe; remove or document
├── requirements.txt
├── TDPyEnvManagerContext.json  # venv config (contains a machine-specific path)
├── own_comps/
│   ├── blocks/                 # the operator library — see below
│   ├── robots/                 # robot output operators (SO-101, Braccio, OSC)
│   ├── backup/                 # earlier operator versions + full_DMP.py
│   └── images/
├── TD_assets/
│   └── Keyframer.*.tox         # third-party keyframer component
├── TDImportCache/              # cached FBX geometry for the background robot view (~23 MB)
└── dataset/
    └── backaway_degrees.bclip  # example recorded movement clip
```

---

## Operator reference

> TODO — verify and expand these one-line descriptions; parameters are not
> documented here.

**Joint grouping**
%to check plz!
| Operator | Purpose |
|---|---|
| `add_overlapping` | Sums two channel groups; surplus channels are concatenated. |
| `fan_out` | Distributes one channel across multiple outputs. |
| `fan_robot_angles` | Splits a joint-angle vector into per-joint channels. |
| `scale` | Scales channel values. |
| `ref_clamp` | Clamps values against a reference. |

**Kinematics**
%to check plz!
| Operator | Purpose |
|---|---|
| `FK` | Forward kinematics. |
| `IK` | Inverse kinematics — end-effector control grouping. |
| `end_wrench` | End-effector wrench/orientation handling. |
| `retarget_movement` | Maps a movement from one rig onto another. |

**Expressive and animation layers**
%to check plz!
| Operator | Purpose |
|---|---|
| `expressive_overlay` | Second-order system exposing *anticipation* and *hold* as input ports, plus natural frequency and damping. |
| `animation` | Generative animation layer (DMP-based — see `backup/full_DMP.py`). |
| `recorder` | Records joint trajectories to `.bclip`. |
| `trigger_play` | Triggers playback of recorded movements. |
| `toggle` | Boolean switching within a chain. |
| `render` | Visual feedback of the control state. |

All angles are in **degrees** and joints are **1-indexed**.

### `full_DMP.py`

A self-contained Dynamic Movement Primitive implementation (6 DOF, 50 Gaussian
basis functions) wrapped as a Script CHOP. `imitate()` fits forcing-term weights
from a recorded trajectory by least squares; `roll_out()` regenerates it from new
start and goal states. Forcing terms are scaled by learned per-DOF amplitude
(`max(y) − min(y)`) rather than `(goal − start)`, which avoids the usual DMP
instability when start and goal coincide. The feature-extraction path is currently
commented out.

---
---

## Operator reference

Generated from the components themselves with `generate_operator_table.py`.
All inputs and outputs are CHOPs unless noted. Angles are in **degrees**.
The recurring `Robot` parameter takes a reference to a robot component from
`own_comps/robots/`, which is how operators stay kinematics-agnostic.

### `own_comps/blocks`

| Operator | Inputs | Outputs | Custom parameters |
|---|---|---|---|
| `FK` | `angles` | `FK` | `Robot` - robot (COMP) |
| `IK` | `setpoint_pos`<br>`setpoint_orient` | `angles`<br>`brake` | `Endeff` - End Effector Joint (Int, `0`)<br>`Baseidx` - Base Joint (Int, `0`)<br>`Robot` - robot (COMP)<br>`Resetrest` - Reset Rest Pose (Pulse)<br>`Gain` - Gain (Int, `10`)<br>`Speedlimit` - Speed Limit (norm) (Int, `10`)<br>`Nullgain` - Null Gain (Float, `0.2`) |
| `add_overlapping` | `channels1`<br>`channels2` | `channels_out` | - |
| `animation` | `in` | `out` | - |
| `end_wrench` | `angles`<br>`loads` | `wrench` | `Endeff` - End Effector (Int, `0`)<br>`Robot` - robot (COMP) |
| `expressive_overlay` | `channels`<br>`anticipation`<br>`hold`<br>`natural_freq`<br>`damping` | `expressive_channels` | `Damping` - Damping (Float, `0.5`)<br>`Natfreq` - Natural Frequency (Float, `2.0`) |
| `fan_out` | `in` | `out0_xaxis`, `out1_yaxis`, `out2_zaxis`<br>`out3_xrot`, `out4_yrot`, `out5_zrot`<br>`out6_slider1`, `out7_slider2`<br>`out8_b1` ... `out13_b6`<br>`out14_p1_X`, `out15_p1_Y` | - |
| `fan_robot_angles` | `channel1` ... `channel6` | `angles` | `Robot` - robot (COMP) |
| `recorder` | none (see note) | none (see note) | `Newsession` - New Session (Pulse) |
| `ref_clamp` | `in`<br>`clamp_vals` | `out` | - |
| `render` | `angles`<br>`setpoint_pos`<br>`setpoint_orient`<br>`wrench` | `render` (TOP) | `Robot` - robot (COMP) |
| `retarget_movement` | `current_channels`<br>`channels_recording`<br>`trigger` | `channels` | `Speedmultiplier` - Speed Multiplier (Float, `1.0`) |
| `scale` | `channels`<br>`scale` | `channels_scaled` | `Scale` - Scale (Float, `0.0`) |
| `toggle` | `button_channel` | `logic` | - |
| `trigger_play` | `full_range_channels`<br>`trigger` | `channels`<br>`running_flag` | - |

The `expressive_overlay` exposes anticipation, hold, natural frequency and
damping as **both** CHOP inputs and custom parameters, so they can be either
set statically or modulated live from a controller.

`recorder` has no in/out operators; it reads and writes through internal
references rather than the connector interface. TODO - document how it is wired.

`fan_out` is hardwired to a 16-output layout matching a specific controller
(3 axes, 3 rotations, 2 sliders, 6 buttons, 2 pad axes). TODO - note which
controller, since remapping to another device means editing the component.

### `own_comps/robots`

| Operator | Inputs | Outputs | Custom parameters |
|---|---|---|---|
| `robot_so101` | `angles`<br>`p_gain`<br>`d_gain` | `angles_out`<br>`loads_out` | `Nrjoints` (Int)<br>`Enabletorque` - Enable Torques (Toggle, `True`)<br>`Com` - COM (Int, `7`)<br>`Resetport` (Pulse)<br>`Positionpgain` (Int, `32`)<br>`Positiondgain` (Int, `32`)<br>`Acc` (Int, `50`)<br>`Speed` (Int, `2400`)<br>`Baud` (Int, `1000000`) |
| `robot_so101_MACOS_compatible` | `angles` | `angles_out` | as above, but `Comport` is a **menu** with `Refreshports` (Pulse) instead of a numeric COM index. No `loads_out`, so no force feedback. |
| `robot_so101_osc` | `angles` | - | `Nrjoints` (Int) |
| `robot_manual_osc` | `q_in` | - | `Nrjoints` (Int) |
| `robot_Braccio_serial` | `angles` | - | `Nrjoints` (Int)<br>`Com` - COM (Int, `8`) |

Only `robot_so101` returns `loads_out`, which `end_wrench` needs. The macOS
variant and the OSC variants are output-only, so wrench-based feedback chains
will not work with them.

### `full_DMP.py`

A self-contained Dynamic Movement Primitive implementation (6 DOF, 50 Gaussian
basis functions) wrapped as a Script CHOP. `imitate()` fits forcing-term weights
from a recorded trajectory by least squares; `roll_out()` regenerates it from new
start and goal states. Forcing terms are scaled by learned per-DOF amplitude
(`max(y) − min(y)`) rather than `(goal − start)`, which avoids the usual DMP
instability when start and goal coincide. The feature-extraction path is currently
commented out.

---


---

## Troubleshooting

**Textport says virtual environment `TD_vEnv` not found**

- Is the root folder named exactly `TD`? Rename it if not.
- On macOS, confirm the path `TD/TD_vEnv/lib/python3.x/site-packages` exists. If
  not, apply the folder fix in step 2 above using the version reported by
  `print(sys.version)`.

**Robot operator isn't updating**

- Double-click the `robot` operator to force a cook.

**Physical robot unresponsive**

- Torques enabled? Select `robot` → `P` → enable Torques.
- Correct serial port? Refresh the port list in the parameters and try another.
- Hardware locked or in an error state? Physically nudge the robot to clear dead
  zones and joint limits.
- Still nothing? Power-cycle: reconnect the supply and reseat the USB cable.

---

## Known limitations

- Runs at ~20 fps, capped by the robot operator's communication protocol. Adequate
  for real-time control but not for high-bandwidth teleoperation.
- `.toe` and `.tox` files are compressed binaries: they cannot be diffed in Git,
  and the saving build cannot be read without opening them in TouchDesigner.
- Large mapping structures become visually hard to manage in a node-based editor.
- Only one example movement clip is included.

## Workshop material

TODO — the graduated manual and routing/puppeteering assignments used in the
evaluation study are not included in this repository. Add them here or link out.

## Licence

TODO — no licence file is present. Without one, default copyright applies and
others cannot legally reuse the code.

## Citation

TODO — BibTeX entry.
