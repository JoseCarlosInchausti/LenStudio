# LenStudio

A desktop application for visually inspecting gravitational lens candidates from the [DESI Legacy Imaging Surveys](https://www.legacysurvey.org/). Load a CSV catalog of targets, step through RGB and GRZ cutouts, assign grades and comments, and export an annotated CSV — all from a single window.

---

## Features

- **RGB and GRZ cutouts** fetched live from the Legacy Survey viewer (DR9, DR10, DR11)
- **Per-band contrast sliders** for independent brightness control of each GRZ channel
- **Quick Inspection mode** — keyboard-driven grading with configurable advance keys
- **VoiceOver mode** — spoken readout of grades and metadata for accessibility
- **Einstein Radius estimator** — click two points on the RGB image to measure arc separation
- **Mark Center tool** — record the true lens center RA/Dec from the cutout
- **Summary tab** — grade distribution, histogram, and thumbnail grid of graded systems
- **Autosave** — grades and comments are written to CSV automatically as you inspect

---

## Requirements

- Python 3.11 or later
- The packages listed in `requirements.txt`

---

## Installation

```bash
# 1. Clone the repository
git clone https://github.com/JoseCarlosInchausti/LenStudio.git
cd LenStudio

# 2. Create and activate a virtual environment (or conda environment)
python -m venv venv
source venv/bin/activate        # macOS / Linux
# venv\Scripts\activate         # Windows

# 3. Install dependencies
pip install -r requirements.txt
```

**Using conda:**

```bash
conda create -n lenstudio python=3.13
conda activate lenstudio
pip install -r requirements.txt
```

---

## Running the app

```bash
python Main.py
```

---

## Usage

1. **Load a CSV** — the file must contain columns with RA and Dec coordinates in decimal degrees.
2. **Configure the inspection** — select which columns hold RA/Dec, choose a grader name, pick any extra metadata columns to display, and set a save location.
3. **Inspect** — use the Previous / Next buttons or the Left / Right arrow keys to navigate. Enter grades and comments in the input panel on the right.
4. **Export** — grades and comments are appended to your CSV automatically. The output file is saved to the location chosen in step 2.

---

## Citation

If you use LenStudio in published research, please cite:

> Inchausti, J. C. (2026). *LenStudio: A visual inspection tool for the DESI Legacy Imaging Surveys.*

---

## Image attribution

Cutout images are served by the [DESI Legacy Imaging Surveys](https://www.legacysurvey.org/) viewer, courtesy of D. Lang (Perimeter Institute), and are made available under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).
