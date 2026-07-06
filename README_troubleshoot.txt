Error message in Textport says virtual environment 'TD_vEnv' not found:

[Is the main folder named exactly 'TD'?]
       │
       ├──► NO:  Rename the root directory to 'TD'.
       │
       └──► YES: [Are you running on macOS?]
                     │
                     └──► YES: Check path: TD ➔ TD_vEnv ➔ lib ➔ python3.x ➔ site-packages
                                   │
                                   └──► PATH IS MISSING: Fix the macOS folder structure:
                                         1. Open TD Textport (Cmd + T).
                                         2. Type: import sys
                                         3. Type: print(sys.version) to get your active version.
                                         4. Navigate to: TD/TD_vEnv/lib/
                                         5. Create a new folder named exactly 'python3.x' 
                                            (e.g., python3.11).
                                         6. Move the 'site-packages' folder inside it.


Robot operator isn't updating, or the physical robot is unresponsive.

[Is the 'robot' operator cooking/updating?]
       │
       └──► NO: Double-click the 'robot' operator to force it to compute.
       │
[Are the motor torques turned on?]
       │
       └──► NO: Select 'robot' ➔ Press 'P' to open parameters ➔ Enable Torques.
       │
[Is the serial/network data flowing?]
       │
       └──► NO: Refresh the connection ports in parameters ➔ Try selecting a different COM/Serial port.
       │
[Is the hardware physically locked or in an error state?]
       │
       └──► YES: Manually/physically move the robot slightly to clear dead zones or hardware limits.
       │
[Still completely unresponsive?]
       │
       └──► FIX: Power-cycle the system: Reconnect the main power supply and reseat the USB cable.