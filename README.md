# Ham Radio Practice Test (US FCC / NCVEC)

This project downloads/parses official NCVEC question pools and gives you:

- CLI exam practice for Element 2, 3, and 4
- Random drilling mode
- Missed-questions-only review mode
- Guided teaching mode (objective-based learning by syllabus group)
- Full syllabus outline command (all subelements and group objectives)
- Local browser web UI
- Separate learning website focused on radio math/physics with graphs and calculators

## Current project path

- `/home/amandeep_chadda/codex/ham-practice`

## Setup

```bash
cd /home/amandeep_chadda/codex/ham-practice
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

## Build/Refresh Question Bank

```bash
.venv/bin/python ham_practice.py update-pools
```

Generated question-bank files:

- `data/pools/element2.json`
- `data/pools/element3.json`
- `data/pools/element4.json`
- `data/pools/all_elements.json`

Missed-question tracking file:

- `data/progress/missed_questions.json`

Syllabus metadata is stored inside each pool JSON under `metadata.syllabus`.

## CLI Usage

Exam-style (official blueprint):

```bash
.venv/bin/python ham_practice.py practice --element 2 --mode exam
```

Random drill:

```bash
.venv/bin/python ham_practice.py practice --element 4 --mode random --num-questions 25
```

Missed-only review:

```bash
.venv/bin/python ham_practice.py practice --element 3 --mode missed
```

Guided teaching mode (one question per group by default):

```bash
.venv/bin/python ham_practice.py practice --element 2 --mode teach
```

Teach only one subelement:

```bash
.venv/bin/python ham_practice.py practice --element 2 --mode teach --subelement T1
```

Teach one specific group:

```bash
.venv/bin/python ham_practice.py practice --element 3 --mode teach --group G8D --questions-per-group 3
```

Run all elements in sequence:

```bash
.venv/bin/python ham_practice.py practice --element all --mode exam
```

Stats (includes missed counts):

```bash
.venv/bin/python ham_practice.py stats
```

Print full syllabus objectives:

```bash
.venv/bin/python ham_practice.py syllabus --element all
```

## Web UI

Start local web app:

```bash
.venv/bin/python ham_practice.py web --host 127.0.0.1 --port 8787
```

Then open:

- `http://127.0.0.1:8787`

The web app supports exam/random/missed modes and updates your missed-question tracker automatically.
The web app also supports guided teaching mode with syllabus focus and knowledge-point feedback.

## Separate Learning Website

This is a separate interface from quiz practice, designed for conceptual learning.

Start it directly:

```bash
.venv/bin/python ham_learning.py web --host 127.0.0.1 --port 8788
```

Or use launcher script:

```bash
./start_ham_learning.sh 8788 127.0.0.1
```

Open:

- `http://127.0.0.1:8788`

What it includes:

- Step-by-step curriculum for radio physics and math fundamentals
- Beginner-friendly plain-English explanations and common-mistake callouts for each module
- Per-concept visuals: each module now has its own picture and graph
- Interactive graphs (wave behavior, resonance/Q, inverse-square intuition, dB ladder)
- Calculators (wavelength, Ohm's law/power, dB and FSPL)
- Full official syllabus explorer by element/group objective
- Direct bridge commands back into practice mode (`practice --mode teach --group ...`)

## Refresh Source PDFs

```bash
.venv/bin/python ham_practice.py update-pools --download
```

## Source PDFs Used

- `http://ncvec.org/downloads/2026-2030 Technician Pool and Syllabus Public Release Feb 19 2026.pdf`
- `http://ncvec.org/downloads/General Class Pool and Syllabus 2023-2027 Public Release with 6th Errata Feb 4 2026.pdf`
- `http://ncvec.org/downloads/2024-2028 Extra Class Question Pool and Syllabus Public Release with 4th Errata Feb 4 2026.pdf`
