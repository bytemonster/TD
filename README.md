# TD
Expressive Puppeteering System Materials - MSc Robotics 07/26

-------------------------------------------

How to Set Up the Project Environment

Follow these steps to recreate the exact Python virtual environment required for this project.


Step 1: 
-Open Your Terminal
-Open your computer's command-line interface and navigate to your project directory.
 -Windows: Open Command Prompt or PowerShell, then type: cd "C:\path\to\your\TD"
 -macOS: Open Terminal, then type: cd "/path/to/your/TD"


Step 2: Create the Environment (TD_vEnv)
Run the command for your specific operating system to create a clean, isolated Python environment.

1.Initialize the Virtual Environment:
Run the creation command:
-Windows: python -m venv TD_vEnv
-macOS: python3 -m venv TD_vEnv

2. macOS ONLY: Apply TouchDesigner Folder Fix (Skip if on Windows)
Because macOS TouchDesigner looks for a highly specific path structure, you must adjust the folder layout inside the newly created environment:
-Open your file finder and navigate into TD/TD_vEnv/lib/.Check which Python version your TouchDesigner uses (e.g., python3.11).
-Create a new folder inside lib/ named exactly after that version (e.g., python3.11).
-Drag and move the existing site-packages folder inside that new python3.11 folder.

3.Activate the Environment (Tells your system to use TD_vEnv)
Activate the environment via your terminal so your computer knows where to install the packages:
-Windows (Command Prompt): TD_vEnv\Scripts\activate
-Windows (PowerShell): .\TD_vEnv\Scripts\activate.ps1
-macOS: source TD_vEnv/bin/activate (Note: If you performed the macOS folder fix in Step 2, run source TD_vEnv/lib/python3.x/site-packages if standard activation gives path errors, though standard terminal activation usually handles installation fine).
-You will know it worked because (TD_vEnv) will now appear at the very front of your terminal line.

4.Install the Dependencies:
Run the following command to automatically download and install the exact cross-platform binaries required for your specific machine: pip install -r requirements.txt


Step 3: Verify in TouchDesigner
-Launch your TouchDesigner project.
-Go to Edit > Preferences > Python.
-Ensure your Python Module Path points directly to your main TD folder.
-Open the Textport (Alt+T or Cmd+T). If there are no initialization errors, your environment is perfectly paired and ready to rock!

--------------------------------------------------------

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