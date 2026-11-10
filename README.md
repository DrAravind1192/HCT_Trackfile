# Comet Trackfile Creator for the 2-m Himalayan Chandra Telescope (HCT)

A Python GUI application for automatically generating **trackfiles** required for tracking **comets and asteroids** with the **2-m Himalayan Chandra Telescope (HCT), Hanle, India**.

The program retrieves ephemerides from the **JPL Horizons** system, processes them into the format required by the HCT telescope control software, and optionally produces an elevation (visibility) plot for the observing night.

---

## Features

- Simple graphical user interface (GUI)
- Supports both **comets** and **asteroids**
- Generate trackfiles for up to **10 objects** simultaneously
- Automatically queries **JPL Horizons**
- Handles both normal and disintegrated comets
- Creates telescope-ready `.trk` files
- Generates visibility plots showing object elevation during the observing night
- Console window displaying processing status and errors
- Automatically organizes final trackfiles into a dedicated folder

---

## Requirements

### Operating System

The code has been developed and tested on **Linux**.

It should also work on macOS with minor modifications.

Windows users may need to modify a few Linux-specific shell commands (`mv`, `rm`, `awk`, `xdg-open`).

---

## Python Version

Use **Python 3.9 or later**.

To check your version,

```bash
python3 --version
```

Example

```text
Python 3.11.5
```

---

## Required Python Packages

The following packages are required.

| Package | Purpose |
|----------|---------|
| tkinter | GUI |
| astroquery | JPL Horizons interface |
| pandas | Table handling |
| numpy | Numerical calculations |
| matplotlib | Visibility plotting |
| smplotlib | Matplotlib styling |

Install them using

```bash
pip3 install astroquery pandas numpy matplotlib smplotlib
```

or

```bash
python3 -m pip install astroquery pandas numpy matplotlib smplotlib
```

The following modules are part of the Python standard library and do **not** require installation:

- csv
- os
- re
- time
- threading
- subprocess
- datetime
- sys

---

## Download

Clone the repository

```bash
git clone https://github.com/DrAravind1192/HCT_Trackfile.git
```

or download it as a ZIP from GitHub.

Move into the repository

```bash
cd HCT_Trackfile
```

---

## Running the Program

Run using Python 3

```bash
python3 comet_trackfile_gui.py
```

The GUI window will open.

---

# Input Parameters

The GUI requires the following inputs.

## 1. Observing Month

Choose the observing month from the drop-down list. 

_Make sure to change the selected month when changing the month in the observing date (to produce trackfile for multiple dates)_


---

## 2. Observation Date

Enter the UT observing date in

```
YYYY-MM-DD
```

Example

```
2026-08-15
```

---

## 3. Object Type

Choose

- Comet
- Asteroid

---

## 4. Number of Objects

Choose between

```
1–10
```

---

## 5. Object Names

Enter the object designation exactly as recognized by **JPL Horizons**.

Examples

```
3I/ATLAS

12P/Pons-Brooks

C/2023 A3

29P

99942 Apophis
```

---

## 6. Disintegrated Objects

Some disintegrated comets require a different Horizons query.

Tick

```
Disintegrated
```

only if the comet has disintegrated.

---

## 7. Visibility Plot

Tick

```
Generate Visibility Plot
```

to produce an elevation plot along with moon.

If unchecked, only the trackfiles are generated.

---

# Outputs

The program automatically creates

```
Final/
```

containing

```
*_observing_date.trk
```

These are the files required by the HCT telescope.

If requested, the program also produces

```
Visibility_observing_date.png
```

showing the elevation curves of all selected objects and moon throughout the observing night.

---

# Workflow

The program performs the following operations automatically.

1. Query JPL Horizons.
2. Retrieve ephemerides.
3. Compute telescope tracking rates.
4. Convert into HCT trackfile format.
5. Correct azimuth values crossing 360°.
6. Save final trackfiles.
7. Generate visibility curves (optional).

---

# JPL Horizons Naming

The software relies entirely on the naming conventions accepted by JPL Horizons.

If Horizons cannot uniquely identify an object, an error similar to

```
ValueError: Ambiguous target name; provide unique id
```

may appear. The specific error can be seen in a JPL errorlog file with the Final folder.

Simply use the unique identifier (Record #) suggested by Horizons and run the program again.

---

# Notes

- Internet access is required since ephemerides are downloaded from JPL Horizons.
- The software does **not** perform orbit calculations itself.
- All ephemerides originate directly from the JPL Horizons service.

---

# Citation

If this software contributes to published scientific work, please cite the corresponding publication (https://doi.org/10.1093/mnras/stae666) and acknowledge the use of this software.

---

# Author

**Aravind K.**

STAR Institute

University of Liège

Belgium

---

# Acknowledgements

This software makes use of

- NASA JPL Horizons
- Astroquery
- NumPy
- Pandas
- Matplotlib

---

# License


```
Copyright (c) 2026 Aravind K.

Permission is hereby granted, free of charge, to any person obtaining a copy...
```

---
