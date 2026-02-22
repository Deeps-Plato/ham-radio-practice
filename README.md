# Ham Radio Practice Test (US FCC / NCVEC)

This project downloads/parses official NCVEC question pools and gives you:

- CLI exam practice for Element 2, 3, and 4
- Random drilling mode
- Missed-questions-only review mode
- Local browser web UI

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

Run all elements in sequence:

```bash
.venv/bin/python ham_practice.py practice --element all --mode exam
```

Stats (includes missed counts):

```bash
.venv/bin/python ham_practice.py stats
```

## Web UI

Start local web app:

```bash
.venv/bin/python ham_practice.py web --host 127.0.0.1 --port 8787
```

Then open:

- `http://127.0.0.1:8787`

The web app supports exam/random/missed modes and updates your missed-question tracker automatically.

## Refresh Source PDFs

```bash
.venv/bin/python ham_practice.py update-pools --download
```

## Source PDFs Used

- `http://ncvec.org/downloads/2026-2030 Technician Pool and Syllabus Public Release Feb 19 2026.pdf`
- `http://ncvec.org/downloads/General Class Pool and Syllabus 2023-2027 Public Release with 6th Errata Feb 4 2026.pdf`
- `http://ncvec.org/downloads/2024-2028 Extra Class Question Pool and Syllabus Public Release with 4th Errata Feb 4 2026.pdf`
