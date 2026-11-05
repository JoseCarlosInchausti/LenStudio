# LenStudio — Developer Reference

## What Is This

LenStudio is a PyQt6 desktop app for visually inspecting astronomical images from the [DESI Legacy Imaging Surveys](https://www.legacysurvey.org/). Astronomers load a CSV of targets (RA/Dec columns), step through each one, view RGB and GRZ cutouts, assign grades/comments, and export the annotated CSV. It also includes per-band contrast sliders, an Einstein Radius measurement tool, and VoiceOver mode for accessibility.

---

## How to Run

```bash
conda activate project1
cd /Users/joseinchausti/LenStudio
python Main.py
```

Runtime dependencies (all in `project1`): PyQt6, pyqtgraph, numpy, astropy, Pillow, requests, pytablericons, pandas.

---

## File Map

| File | Purpose |
|---|---|
| `Main.py` | Entry point — creates `QApplication`, `MainWindow`, switches screens |
| `LoadDataScreen.py` | Screen 1: CSV picker, column mapper, survey selector |
| `PreInspectionScreen.py` | Screen 2: grader name, additional column picker, settings |
| `StudioScreen.py` | Screen 3: main inspection UI |
| `InspectionEngine.py` | Image fetching, caching, prefetch thread |
| `Assets.py` | All shared widgets (ImageWidget, StyledInputBox, SystemJumpWidget, …) |
| `SettingsAssets.py` | Settings panel widgets |
| `Theme.py` | Color palette constants |
| `Icons.py` | Tabler icon helpers (`tabler_icon`, `tabler_pixmap`, `OutlineIcon`) |
| `VoiceOverEngine.py` | Text-to-speech for grade/metadata readout |

---

## Color Palette (`Theme.py`)

```python
BG       = "#0a1628"   # window background
SURFACE  = "#0d1a2e"   # header / toolbar strips
CARD     = "#152238"   # panel / card background
FIELD    = "#2e466c"   # input field background
BORDER   = "#27364d"
FIELD_BRD= "#4a6188"
ACCENT   = "#4A9EFF"   # primary / focus / active
ACCENT_HI= "#5fb0ff"   # hover
ACCENT_LO= "#3d8de0"   # pressed
TXT      = "#e8edf5"
TXT_SOFT = "#c3cde0"
TXT_MUTE = "#8a99b3"
```

---

## Survey Layers — Critical Detail

The Legacy Survey API requires exact layer names. Wrong names return 200 OK with all-zero data (no error).

```python
SURVEY_LAYERS = {
    'dr9':  'ls-dr9',        # NO -grz suffix
    'dr10': 'ls-dr10-grz',   # -grz required
    'dr11': 'ls-dr11',       # NO -grz suffix
}
```

**Do not add `-grz` to dr9 or dr11 layer names.**

---

## Image Orientation Transforms

Both transforms were determined programmatically via centroid matching against the RGB reference.

**RGB (JPEG):** `np.rot90(np.array(pil_image), k=-1)` — 90° clockwise

**GRZ (FITS):**
```python
data = fits.open(url)[0].data          # shape: (3, H, W)
data = np.flip(data, axis=2)           # flip left-right
data = np.rot90(data, k=1, axes=(1,2)) # 90° CCW per band
```

`flipLR + rot90CCW` scored 14.1 px total centroid residual vs 174 px for the runner-up.

---

## Architecture: Key Classes

### `InspectionEngine.Inspection`
- Holds the survey layer, cache, and coord validation
- `get_current_images(idx)` → `(status_dict, data_dict)` — returns `bad_coords: True` if RA/Dec are non-numeric or NaN
- `_is_valid_coord(val)` — uses `f == f` NaN check
- `add_to_cache(list_of_new_images, idx)` — use `idx` parameter, not `self.current_idx`
- `pixscale = 0.262` arcsec/pixel

### `InspectionEngine.PrefetchThread(QThread)`
- Fetches the next cutout in background
- Snapshots `inspection.layer` at construction — discards results if layer changed by the time it finishes
- Signal: `fetched = pyqtSignal(object, object, int, str)` → (rgb, grz, idx, layer)

### `Assets.ImageWidget(pg.GraphicsLayoutWidget)`
- Wraps a pyqtgraph ViewBox + ImageItem
- Grayscale (2D) arrays get percentile-based stretch (p2/p99) with adjustable contrast
- `set_contrast_scale(slider_value)`: maps slider 1–100 → `10**((50-val)/60)` — slider 50 = identity, 100 = bright/tight, 1 = dim/wide
- `update_image(arr)` recomputes base levels, preserves current contrast scale

### `Assets.SystemJumpWidget(QWidget)`
- Displays "Cutout **N** of M" with the number underlined/blue as a clickable link
- Clicking enters edit mode (QLineEdit with QIntValidator)
- Signal: `jump_requested = pyqtSignal(int)` — emits 0-based index
- `set_system(current_1based, total)`

### `Assets.StyledInputBox`
- Title bar is a QHBoxLayout: `title_label` (left) + `_lock_label` (right, hidden)
- `_lock_label`: amber lock icon (pytablericons, 11px, `#f59e0b`)
- `show_lock(visible: bool)` toggles visibility

### `StudioScreen.StudioScreenWidget`
Key state:
- `self._prefetch_threads = {}` — dict of `{idx: PrefetchThread}`
- `self._er_mode = False` — Einstein Radius measurement toggle
- `self._er_points = []` — 0, 1, or 2 `(x, y)` ViewBox-coord points
- `self._er_overlay_items = []` — pyqtgraph items added to RGB ViewBox

Key methods:
- `update_onscreen_data()` — main refresh after navigation; calls `_er_clear()` first
- `_jump_to_system(idx)` — saves grade/comment, updates nav, triggers autosave
- `set_up_inspection_layout()` — grid: col0=sliders, col1=GRZ, col2=RGB
- `_toggle_er_mode()` — toggles button style, clears ER state
- `_on_er_rgb_click(event)` — collects up to 2 points, calls `_er_draw_overlay()`
- `_er_draw_overlay()` — adds ScatterPlotItem, PlotDataItem (dashed), TextItem to RGB ViewBox
- `_start_prefetch(idx)` / `_on_prefetch_done(...)` / `_stop_all_prefetches()`

---

## GRZ Layout

Each of the 3 GRZ bands (g, r, z) is displayed with a vertical `QSlider` to its left:
- Range 1–100, default 50 (identity contrast)
- Size: 20×134 px
- Connected to `band_image.set_contrast_scale(slider_value)`

Grid columns: `[sliders (stretch 0)] [GRZ (stretch 1)] [RGB (stretch 3)]`

ImageWidgets are **always created** (blank `np.zeros` placeholder) so navigation never causes a KeyError. The `_update_blank_overlays` method overlays text on them if data is unavailable.

---

## Invalid / NaN Coordinates

`get_current_images` returns early with `{'bad_coords': True}` if either RA or Dec fails `_is_valid_coord`. `_update_blank_overlays` in StudioScreen shows:

```
"Invalid coordinates\nRA: {val}\nDEC: {val}"
```

on all image panels instead of "Not in footprint."

---

## Arrow Key Navigation

`eventFilter` in StudioScreenWidget handles Left/Right arrow keys for navigation:

```python
if obj not in (grade_field, comment_field) or obj.isReadOnly():
    # navigate
```

The `or obj.isReadOnly()` clause ensures locked (read-only) fields don't swallow arrow keys.

---

## Einstein Radius Estimator

User clicks two points on the RGB image. Distance is computed in ViewBox coords (pixels) and converted to arcseconds:

```python
d_arcsec = sqrt(dx**2 + dy**2) * pixscale  # pixscale = 0.262
```

Overlay items: red dots (ScatterPlotItem), dashed accent line (PlotDataItem), arcsecond label (TextItem at midpoint). All stored in `_er_overlay_items` and removed by `_er_clear_overlay()`. The button uses `ER_ACTIVE_BTN` style when active.

---

## Settings System

Settings are stored as JSON (see `JSON-for-settings-design-format.txt` and `settings-state.txt` for the schema). The `InspectionSettings` class in `Assets.py` manages read/write. Settings include: grader name, survey, RA/Dec column names, additional metadata columns, quick inspection mode, VoiceOver, lock grades, move-forward behavior.

---

## Security Note

The DESI `viewer-desi` endpoint requires credentials and is access-controlled. **Do not re-add it.** All fetches use the public `legacysurvey.org/viewer` endpoint only.

---

## Distribution (Deferred)

Plan is to ship via PyPI (`pip install lenstudio` / `pipx install lenstudio`). Packaging steps are deferred until feature work is complete.

---

## Pre-Public Checklist

Before making the repository public, complete the following:

**🔴 Blockers**
- [ ] Remove hardcoded DESI credential from `tests.py` line 78 (`auth=('desi', '[REDACTED]')`) **and rewrite git history** — the credential appears in two commits (`Initial commit`, `VoiceOver mode added`). Use BFG Repo Cleaner or `git filter-branch`. Simply deleting the line is not enough.

**🟡 Gitignore additions**
- [ ] Add `recent_files.json` — contains local filesystem paths
- [ ] Add `settings-state.txt` — user-specific runtime state
- [ ] Add `.claude/` — Claude Code project config

**🟠 Cleanup**
- [ ] Decide whether to include `Test catalogs/` as sample data (files contain personal inspection grades in `JI_grades`/`JI_comments` columns) or gitignore it
- [ ] Remove or gitignore `Main_temp.py` and `StudioScreen v1.py` (dead files)
- [ ] Review Jupyter notebooks (`notebook_tests.ipynb`, `GIF.ipynb`, `_VI_interface-true-grz_fits-zd+zs_hsc (1) (5).ipynb`) for internal data before publishing
- [ ] Review `VoiceOverTests/`

**✅ Dependencies — all clear**

PyQt6 (LGPL), pyqtgraph (MIT), numpy (BSD), astropy (BSD), Pillow (HPND), requests (Apache 2.0), pytablericons (MIT), pandas (BSD). No licensing conflicts.

**📣 Citation**
- [ ] Add `CITATION.cff` with author name, year, and software title
- [ ] Register repo on Zenodo for a citable DOI per release
