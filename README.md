# AUDIO VISUALISER

Small audio visualiser panel.

Load a WAV file and it plays while two live graphs follow the music:

- **Waveform**: the shape of the sound wave at the current moment.
- **Spectrum**: how loud each frequency is.

## Requirements

- Python 3.9 or newer (developed with Python 3.14)
- Windows, macOS or Linux

## Installation

From the project folder, create a virtual environment and install the dependencies:

```bash
python -m venv .venv
```

Activate it:

```bash
# macOS / Linux
source .venv/bin/activate

# Windows
.venv\Scripts\activate
```

Then install the packages:

```bash
pip install -r requirements.txt
```

On some minimal Linux installs the window may fail to open with `Could not load the Qt platform plugin "xcb"`. Installing `libxcb-cursor0` (Debian/Ubuntu: `sudo apt install libxcb-cursor0`) fixes it.

## Running

With the virtual environment activated:

```bash
python main.py
```

## Usage

1. Click **Load Audio File** and choose a `.wav` file. It starts playing straight away (When a file is opened, every other WAV file in the same folder is added to a playlist, sorted alphanumericaly).
2. Use the controls below the graphs:

| Button      | Action                                                                                       |
| ----------- | -------------------------------------------------------------------------------------------- |
| ⏮          | Restart the current track, or go to the previous track if pressed within the first 3 seconds |
| ►           | Play                                                                                         |
| ❚❚          | Pause                                                                                        |
| ◼           | Stop                                                                                         |
| ⏭          | Next track                                                                                   |
| X / 🔁 / 🔂 | Repeat mode: off, repeat the whole playlist, or repeat the current track                     |
