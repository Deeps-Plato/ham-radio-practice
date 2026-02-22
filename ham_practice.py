#!/usr/bin/env python3
"""Ham radio question pool importer, CLI practice tests, and local web UI."""

from __future__ import annotations

import argparse
import json
import random
import re
import sys
import textwrap
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from pypdf import PdfReader


POOL_CONFIG = {
    2: {
        "name": "Technician",
        "element": 2,
        "pool_cycle": "2026-2030",
        "source_url": "http://ncvec.org/downloads/2026-2030 Technician Pool and Syllabus Public Release Feb 19 2026.pdf",
        "raw_pdf": "data/raw/technician_2026_2030.pdf",
        "first_question_id": "T1A01",
        "exam_questions": 35,
        "pass_score": 26,
        "blueprint": {
            "T1": 6,
            "T2": 3,
            "T3": 3,
            "T4": 2,
            "T5": 4,
            "T6": 4,
            "T7": 4,
            "T8": 4,
            "T9": 2,
            "T0": 3,
        },
    },
    3: {
        "name": "General",
        "element": 3,
        "pool_cycle": "2023-2027",
        "source_url": "http://ncvec.org/downloads/General Class Pool and Syllabus 2023-2027 Public Release with 6th Errata Feb 4 2026.pdf",
        "raw_pdf": "data/raw/general_2023_2027.pdf",
        "first_question_id": "G1A01",
        "exam_questions": 35,
        "pass_score": 26,
        "blueprint": {
            "G1": 5,
            "G2": 3,
            "G3": 3,
            "G4": 2,
            "G5": 2,
            "G6": 3,
            "G7": 3,
            "G8": 4,
            "G9": 2,
            "G0": 3,
        },
    },
    4: {
        "name": "Amateur Extra",
        "element": 4,
        "pool_cycle": "2024-2028",
        "source_url": "http://ncvec.org/downloads/2024-2028 Extra Class Question Pool and Syllabus Public Release with 4th Errata Feb 4 2026.pdf",
        "raw_pdf": "data/raw/extra_2024_2028.pdf",
        "first_question_id": "E1A01",
        "exam_questions": 50,
        "pass_score": 37,
        "blueprint": {
            "E1": 6,
            "E2": 5,
            "E3": 3,
            "E4": 5,
            "E5": 4,
            "E6": 6,
            "E7": 8,
            "E8": 4,
            "E9": 4,
            "E0": 5,
        },
    },
}

QUESTION_HEADER_RE = re.compile(r"^([TGE]\d[A-Z]\d{2})(?:\s+\(([ABCD])\))?(?:\s+\[([^\]]+)\])?\s*$")
OPTION_RE = re.compile(r"^([ABCD])\.\s*(.*)$")
SUBELEMENT_HEADER_RE = re.compile(
    r"^SUBELEMENT\s+([TGE]\d)\s*[-–—]\s*(.+?)\s+\[(\d+)\s+exam questions?\s*[-–—]\s*(\d+)\s+groups?\](?:\s+(\d+)\s+Questions)?$",
    flags=re.IGNORECASE,
)
GROUP_OBJECTIVE_RE = re.compile(r"^([TGE]\d[A-Z])\s+(.*)$")
MISSED_PATH = Path("data/progress/missed_questions.json")


@dataclass
class Question:
    question_id: str
    element: int
    license_class: str
    subelement: str
    group: str
    answer_key: str
    citation: Optional[str]
    question: str
    choices: Dict[str, str]

    def to_dict(self) -> Dict[str, object]:
        return {
            "question_id": self.question_id,
            "element": self.element,
            "license_class": self.license_class,
            "subelement": self.subelement,
            "group": self.group,
            "answer_key": self.answer_key,
            "citation": self.citation,
            "question": self.question,
            "choices": self.choices,
        }


def _clean_text(s: str) -> str:
    return re.sub(r"\s+", " ", s.strip())


def _normalize_source_url(url: str) -> str:
    parts = urllib.parse.urlsplit(url)
    return urllib.parse.urlunsplit(
        (parts.scheme, parts.netloc, urllib.parse.quote(parts.path), parts.query, parts.fragment)
    )


def default_missed_db() -> Dict[str, List[str]]:
    return {str(element): [] for element in sorted(POOL_CONFIG.keys())}


def normalize_missed_db(raw: object) -> Dict[str, List[str]]:
    normalized = default_missed_db()
    if not isinstance(raw, dict):
        return normalized

    for element in normalized:
        values = raw.get(element, [])
        if not isinstance(values, list):
            continue
        cleaned = sorted({str(v).strip() for v in values if isinstance(v, str) and str(v).strip()})
        normalized[element] = cleaned
    return normalized


def load_missed_db() -> Dict[str, List[str]]:
    if not MISSED_PATH.exists():
        return default_missed_db()

    try:
        raw = json.loads(MISSED_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return default_missed_db()

    return normalize_missed_db(raw)


def save_missed_db(db: Dict[str, List[str]]) -> None:
    payload = normalize_missed_db(db)
    MISSED_PATH.parent.mkdir(parents=True, exist_ok=True)
    MISSED_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def mark_question_result(
    db: Dict[str, List[str]],
    element: int,
    question_id: str,
    correct: bool,
) -> None:
    key = str(element)
    current = set(db.get(key, []))
    if correct:
        current.discard(question_id)
    else:
        current.add(question_id)
    db[key] = sorted(current)


def download_pdf(url: str, out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    normalized = _normalize_source_url(url)
    with urllib.request.urlopen(normalized) as response, out_path.open("wb") as out_file:
        out_file.write(response.read())


def extract_pdf_text(pdf_path: Path) -> str:
    reader = PdfReader(str(pdf_path))
    return "\n".join((page.extract_text() or "") for page in reader.pages)


def parse_questions(text: str, element: int, class_name: str, first_question_id: str) -> List[Question]:
    start = text.find(first_question_id)
    if start < 0:
        raise ValueError(f"Could not find first question marker '{first_question_id}' in source text")
    text = text[start:]

    end_marker = "~~~~End of question pool text~~~~"
    end = text.find(end_marker)
    if end >= 0:
        text = text[:end]

    questions: List[Question] = []
    current_header: Optional[re.Match[str]] = None
    body_lines: List[str] = []

    def flush_current() -> None:
        nonlocal current_header, body_lines
        if current_header is None:
            return

        question_id = current_header.group(1)
        answer_key = current_header.group(2)
        citation = current_header.group(3)

        text_lines: List[str] = []
        choices: Dict[str, str] = {}
        current_choice: Optional[str] = None

        for raw_line in body_lines:
            line = _clean_text(raw_line)
            if not line:
                continue
            option_match = OPTION_RE.match(line)
            if option_match:
                current_choice = option_match.group(1)
                choices[current_choice] = option_match.group(2)
                continue
            if current_choice:
                choices[current_choice] = _clean_text(f"{choices[current_choice]} {line}")
            else:
                text_lines.append(line)

        question_text = _clean_text(" ".join(text_lines))

        # Deleted/withdrawn entries are represented without answer keys/options.
        if not answer_key or len(choices) != 4 or answer_key not in choices or not question_text:
            current_header = None
            body_lines = []
            return

        subelement = question_id[:2]
        group = question_id[:3]

        questions.append(
            Question(
                question_id=question_id,
                element=element,
                license_class=class_name,
                subelement=subelement,
                group=group,
                answer_key=answer_key,
                citation=citation,
                question=question_text,
                choices=choices,
            )
        )
        current_header = None
        body_lines = []

    for raw_line in text.splitlines():
        line = raw_line.strip()

        header_match = QUESTION_HEADER_RE.match(line)
        if header_match:
            flush_current()
            current_header = header_match
            body_lines = []
            continue

        if current_header:
            if line == "~~":
                flush_current()
            else:
                body_lines.append(raw_line)

    flush_current()
    return questions


def parse_syllabus(text: str, element_prefix: str) -> Dict[str, object]:
    subelements: Dict[str, Dict[str, object]] = {}
    current_subelement: Optional[str] = None
    current_group: Optional[str] = None

    for raw_line in text.splitlines():
        line = _clean_text(raw_line)
        if not line:
            continue

        if QUESTION_HEADER_RE.match(line):
            if subelements:
                break
            continue

        sub_match = SUBELEMENT_HEADER_RE.match(line)
        if sub_match:
            sub_id = sub_match.group(1)
            if not sub_id.startswith(element_prefix):
                current_subelement = None
                current_group = None
                continue

            pool_questions_raw = sub_match.group(5)
            next_entry: Dict[str, object] = {
                "title": sub_match.group(2),
                "exam_questions": int(sub_match.group(3)),
                "group_count": int(sub_match.group(4)),
                "pool_questions": int(pool_questions_raw) if pool_questions_raw else 0,
                "groups": {},
            }
            existing_entry = subelements.get(sub_id)
            if isinstance(existing_entry, dict) and existing_entry.get("groups"):
                if int(existing_entry.get("pool_questions", 0)) == 0 and int(next_entry["pool_questions"]) > 0:
                    existing_entry["pool_questions"] = int(next_entry["pool_questions"])
                current_subelement = sub_id
                current_group = None
                continue

            subelements[sub_id] = next_entry
            current_subelement = sub_id
            current_group = None
            continue

        if not current_subelement:
            continue

        group_match = GROUP_OBJECTIVE_RE.match(line)
        if group_match and group_match.group(1).startswith(current_subelement):
            group_id = group_match.group(1)
            subelements[current_subelement]["groups"][group_id] = group_match.group(2)
            current_group = group_id
            continue

        if current_group and not line.startswith("FCC Element"):
            if line.startswith("Effective "):
                continue
            if re.match(r"^\d{4}-\d{4}\s+.*Class", line):
                continue
            existing = str(subelements[current_subelement]["groups"][current_group])
            subelements[current_subelement]["groups"][current_group] = _clean_text(f"{existing} {line}")

    group_objectives: Dict[str, str] = {}
    for sub_id in sorted(subelements):
        groups = subelements[sub_id]["groups"]
        for group_id in sorted(groups):
            group_objectives[group_id] = str(groups[group_id])

    return {
        "subelements": subelements,
        "group_objectives": group_objectives,
    }


def write_pool_json(
    element: int, questions: List[Question], syllabus: Dict[str, object], output_path: Path
) -> None:
    config = POOL_CONFIG[element]
    payload = {
        "metadata": {
            "generated_at_utc": datetime.now(timezone.utc).isoformat(),
            "element": element,
            "license_class": config["name"],
            "pool_cycle": config["pool_cycle"],
            "source_url": config["source_url"],
            "question_count": len(questions),
            "exam_questions": config["exam_questions"],
            "pass_score": config["pass_score"],
            "blueprint": config["blueprint"],
            "syllabus": syllabus,
        },
        "questions": [q.to_dict() for q in questions],
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def load_pool_payload(element: int) -> Dict[str, object]:
    path = Path(f"data/pools/element{element}.json")
    if not path.exists():
        raise FileNotFoundError(
            f"Missing {path}. Run 'python ham_practice.py update-pools' first."
        )
    return json.loads(path.read_text(encoding="utf-8"))


def load_questions_from_json(element: int) -> List[Dict[str, object]]:
    payload = load_pool_payload(element)
    return payload["questions"]


def build_exam_questions(element: int, questions: List[Dict[str, object]], rng: random.Random) -> List[Dict[str, object]]:
    blueprint = POOL_CONFIG[element]["blueprint"]
    by_subelement: Dict[str, List[Dict[str, object]]] = {}
    for q in questions:
        by_subelement.setdefault(q["subelement"], []).append(q)

    selected: List[Dict[str, object]] = []
    for subelement, needed_count in blueprint.items():
        bucket = by_subelement.get(subelement, [])
        if len(bucket) < needed_count:
            raise ValueError(
                f"Not enough questions for {subelement}: need {needed_count}, found {len(bucket)}"
            )
        selected.extend(rng.sample(bucket, needed_count))

    rng.shuffle(selected)
    return selected


def build_random_questions(
    questions: List[Dict[str, object]], count: int, rng: random.Random
) -> List[Dict[str, object]]:
    count = max(1, min(count, len(questions)))
    return rng.sample(questions, count)


def build_missed_questions(
    element: int,
    questions: List[Dict[str, object]],
    missed_db: Dict[str, List[str]],
) -> List[Dict[str, object]]:
    missed_ids = set(missed_db.get(str(element), []))
    if not missed_ids:
        return []
    return [q for q in questions if q["question_id"] in missed_ids]


def build_teach_questions(
    element: int,
    questions: List[Dict[str, object]],
    syllabus: Dict[str, object],
    rng: random.Random,
    num_questions: Optional[int],
    questions_per_group: int,
    subelement_filter: Optional[str],
    group_filter: Optional[str],
) -> List[Dict[str, object]]:
    filtered = questions
    if subelement_filter:
        filtered = [q for q in filtered if str(q["subelement"]).upper() == subelement_filter.upper()]
    if group_filter:
        filtered = [q for q in filtered if str(q["group"]).upper() == group_filter.upper()]

    by_group: Dict[str, List[Dict[str, object]]] = {}
    for q in filtered:
        by_group.setdefault(str(q["group"]), []).append(q)

    selected: List[Dict[str, object]] = []
    for group_id in sorted(by_group):
        bucket = by_group[group_id]
        pick = min(len(bucket), max(1, questions_per_group))
        if num_questions is not None:
            remaining = num_questions - len(selected)
            if remaining <= 0:
                break
            pick = min(pick, remaining)
        selected.extend(rng.sample(bucket, pick))

    if num_questions is not None and len(selected) < num_questions and filtered:
        remaining = num_questions - len(selected)
        used_ids = {str(q["question_id"]) for q in selected}
        extras = [q for q in filtered if str(q["question_id"]) not in used_ids]
        if extras:
            selected.extend(rng.sample(extras, min(remaining, len(extras))))

    group_objectives = syllabus.get("group_objectives", {}) if isinstance(syllabus, dict) else {}
    subelements = syllabus.get("subelements", {}) if isinstance(syllabus, dict) else {}

    enriched: List[Dict[str, object]] = []
    for q in selected:
        q_copy = dict(q)
        group_id = str(q_copy["group"])
        sub_id = str(q_copy["subelement"])
        sub_meta = subelements.get(sub_id, {}) if isinstance(subelements, dict) else {}
        q_copy["teaching_focus"] = str(group_objectives.get(group_id, ""))
        q_copy["teaching_section_title"] = str(sub_meta.get("title", ""))
        enriched.append(q_copy)

    rng.shuffle(enriched)
    return enriched


def select_questions_for_mode(
    element: int,
    mode: str,
    num_questions: Optional[int],
    rng: random.Random,
    missed_db: Dict[str, List[str]],
    subelement_filter: Optional[str] = None,
    group_filter: Optional[str] = None,
    questions_per_group: int = 1,
) -> Tuple[List[Dict[str, object]], Optional[int], str]:
    config = POOL_CONFIG[element]
    payload = load_pool_payload(element)
    questions = payload["questions"]
    meta = payload.get("metadata", {})
    syllabus = meta.get("syllabus", {})

    if mode == "exam":
        selected = build_exam_questions(element, questions, rng)
        pass_score = int(config["pass_score"])
        label = f"Element {element} {config['name']} exam-style"
        return selected, pass_score, label

    if mode == "random":
        requested = num_questions or int(config["exam_questions"])
        selected = build_random_questions(questions, requested, rng)
        label = f"Element {element} {config['name']} random drill"
        return selected, None, label

    if mode == "missed":
        missed_questions = build_missed_questions(element, questions, missed_db)
        if not missed_questions:
            return [], None, f"Element {element} {config['name']} missed-questions review"

        requested = num_questions or len(missed_questions)
        selected = build_random_questions(missed_questions, requested, rng)
        label = f"Element {element} {config['name']} missed-questions review"
        return selected, None, label

    if mode == "teach":
        selected = build_teach_questions(
            element=element,
            questions=questions,
            syllabus=syllabus,
            rng=rng,
            num_questions=num_questions,
            questions_per_group=max(1, questions_per_group),
            subelement_filter=subelement_filter,
            group_filter=group_filter,
        )
        label = f"Element {element} {config['name']} guided teaching mode"
        return selected, None, label

    raise ValueError(f"Unsupported mode '{mode}'")


def ask_question(
    q: Dict[str, object],
    index: int,
    total: int,
    wrap_width: int,
    always_show_teaching: bool = False,
) -> Optional[bool]:
    print(f"\n[{index}/{total}] {q['question_id']} ({q['subelement']})")
    citation = q.get("citation")
    if citation:
        print(f"Rule ref: {citation}")
    print(textwrap.fill(str(q["question"]), width=wrap_width))

    choices = q["choices"]
    for key in ["A", "B", "C", "D"]:
        print(textwrap.fill(f"{key}. {choices[key]}", width=wrap_width, subsequent_indent="   "))

    while True:
        try:
            raw = input("Your answer [A-D, s=show, q=quit]: ").strip().upper()
        except EOFError:
            print("\nInput stream closed. Ending session.")
            return None

        if raw in {"A", "B", "C", "D"}:
            correct = raw == q["answer_key"]
            if correct:
                print("Correct")
            else:
                answer_key = q["answer_key"]
                print(f"Incorrect. Correct answer: {answer_key}. {choices[answer_key]}")

            if always_show_teaching:
                focus = str(q.get("teaching_focus", "")).strip()
                section = str(q.get("teaching_section_title", "")).strip()
                if section:
                    print(f"Section: {section}")
                if focus:
                    print(f"Teaching focus ({q['group']}): {focus}")
                answer_key = q["answer_key"]
                print(f"Knowledge point: {choices[answer_key]}")
            return correct

        if raw == "S":
            answer_key = q["answer_key"]
            print(f"Answer: {answer_key}. {choices[answer_key]}")
            if always_show_teaching:
                focus = str(q.get("teaching_focus", "")).strip()
                section = str(q.get("teaching_section_title", "")).strip()
                if section:
                    print(f"Section: {section}")
                if focus:
                    print(f"Teaching focus ({q['group']}): {focus}")
                print(f"Knowledge point: {choices[answer_key]}")
            return False

        if raw == "Q":
            return None

        print("Please enter A, B, C, D, s, or q.")


def run_session(
    element: int,
    mode: str,
    num_questions: Optional[int],
    rng: random.Random,
    wrap_width: int,
    missed_db: Dict[str, List[str]],
    subelement_filter: Optional[str] = None,
    group_filter: Optional[str] = None,
    questions_per_group: int = 1,
) -> Dict[str, object]:
    selected, pass_score, label = select_questions_for_mode(
        element=element,
        mode=mode,
        num_questions=num_questions,
        rng=rng,
        missed_db=missed_db,
        subelement_filter=subelement_filter,
        group_filter=group_filter,
        questions_per_group=questions_per_group,
    )

    print(f"\n=== {label} ===")
    if not selected:
        print("No questions available for this session. Add some misses first or choose another mode.")
        return {
            "element": element,
            "mode": mode,
            "asked": 0,
            "correct": 0,
            "total": 0,
            "pass_score": pass_score,
        }

    correct = 0
    asked = 0
    show_teaching = mode == "teach"
    for idx, q in enumerate(selected, start=1):
        result = ask_question(q, idx, len(selected), wrap_width, always_show_teaching=show_teaching)
        if result is None:
            break

        asked += 1
        if result:
            correct += 1

        mark_question_result(
            db=missed_db,
            element=element,
            question_id=str(q["question_id"]),
            correct=result,
        )

    print("\nSession complete")
    print(f"Score: {correct}/{asked} ({(100.0 * correct / asked) if asked else 0:.1f}%)")

    if pass_score is not None and mode == "exam":
        status = "PASS" if correct >= pass_score else "NOT PASS"
        print(f"Result: {status} (needs {pass_score}/{len(selected)})")

    return {
        "element": element,
        "mode": mode,
        "asked": asked,
        "correct": correct,
        "total": len(selected),
        "pass_score": pass_score,
    }


def command_update_pools(args: argparse.Namespace) -> int:
    all_counts = {}

    for element, config in POOL_CONFIG.items():
        raw_pdf_path = Path(config["raw_pdf"])
        source_url = str(config["source_url"])

        if args.download or not raw_pdf_path.exists():
            print(f"Downloading Element {element} source PDF...")
            download_pdf(source_url, raw_pdf_path)

        print(f"Parsing Element {element} question pool...")
        text = extract_pdf_text(raw_pdf_path)
        syllabus = parse_syllabus(text=text, element_prefix=str(config["first_question_id"])[0:1])
        questions = parse_questions(
            text=text,
            element=element,
            class_name=str(config["name"]),
            first_question_id=str(config["first_question_id"]),
        )

        if not questions:
            raise ValueError(f"No questions parsed for Element {element}")

        output = Path(f"data/pools/element{element}.json")
        write_pool_json(element, questions, syllabus, output)

        all_counts[element] = len(questions)
        print(f"Wrote {output} with {len(questions)} questions")

    combined = {
        "metadata": {
            "generated_at_utc": datetime.now(timezone.utc).isoformat(),
            "elements": sorted(POOL_CONFIG.keys()),
            "counts": all_counts,
        },
        "elements": {
            str(element): json.loads(Path(f"data/pools/element{element}.json").read_text(encoding="utf-8"))
            for element in sorted(POOL_CONFIG)
        },
    }

    combined_path = Path("data/pools/all_elements.json")
    combined_path.write_text(json.dumps(combined, indent=2), encoding="utf-8")
    print(f"Wrote {combined_path}")

    return 0


def command_practice(args: argparse.Namespace) -> int:
    rng = random.Random(args.seed)
    missed_db = load_missed_db()

    elements = [2, 3, 4] if args.element == "all" else [int(args.element)]
    summaries = []

    for element in elements:
        summary = run_session(
            element=element,
            mode=args.mode,
            num_questions=args.num_questions,
            rng=rng,
            wrap_width=args.width,
            missed_db=missed_db,
            subelement_filter=args.subelement,
            group_filter=args.group,
            questions_per_group=args.questions_per_group,
        )
        summaries.append(summary)

        save_missed_db(missed_db)

        if summary["asked"] < summary["total"]:
            print("Stopped early.")
            break

    if len(summaries) > 1:
        total_correct = sum(s["correct"] for s in summaries)
        total_asked = sum(s["asked"] for s in summaries)
        print("\n=== Combined summary ===")
        print(f"Overall score: {total_correct}/{total_asked} ({(100.0 * total_correct / total_asked) if total_asked else 0:.1f}%)")

    return 0


def command_stats(_args: argparse.Namespace) -> int:
    missed_db = load_missed_db()
    for element, config in POOL_CONFIG.items():
        questions = load_questions_from_json(element)
        by_subelement: Dict[str, int] = {}
        for q in questions:
            by_subelement[q["subelement"]] = by_subelement.get(q["subelement"], 0) + 1

        print(f"Element {element} {config['name']}: {len(questions)} questions")
        print(f"  missed currently tracked: {len(missed_db.get(str(element), []))}")
        for subelement in sorted(by_subelement):
            print(f"  {subelement}: {by_subelement[subelement]}")

    return 0


def command_syllabus(args: argparse.Namespace) -> int:
    elements = [2, 3, 4] if args.element == "all" else [int(args.element)]

    for idx, element in enumerate(elements, start=1):
        payload = load_pool_payload(element)
        meta = payload.get("metadata", {})
        syllabus = meta.get("syllabus", {})
        subelements = syllabus.get("subelements", {}) if isinstance(syllabus, dict) else {}
        config = POOL_CONFIG[element]

        print(
            f"Element {element} {config['name']} ({meta.get('pool_cycle', 'unknown cycle')})"
        )

        if not subelements:
            print("  No parsed syllabus metadata found. Re-run update-pools.")
            continue

        for sub_id in sorted(subelements):
            sub = subelements[sub_id]
            title = sub.get("title", "")
            exam_questions = sub.get("exam_questions", "?")
            pool_questions = sub.get("pool_questions", "?")
            print(f"  {sub_id} - {title}")
            print(f"    Exam questions: {exam_questions} | Pool questions: {pool_questions}")

            groups = sub.get("groups", {})
            for group_id in sorted(groups):
                print(f"    {group_id}: {groups[group_id]}")

        if idx < len(elements):
            print("")

    return 0


WEB_INDEX_HTML = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Ham Practice</title>
  <style>
    :root {
      --bg: #f6f4ef;
      --panel: #fffefc;
      --ink: #1d2d44;
      --muted: #556273;
      --accent: #0d6e6e;
      --accent-2: #f0a202;
      --ok: #1f8a4d;
      --bad: #b42318;
      --border: #d7d2c8;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      color: var(--ink);
      background:
        radial-gradient(circle at 0% 0%, #ffffff 0, #ffffff 18%, transparent 18%),
        radial-gradient(circle at 100% 100%, #e5f2f2 0, #e5f2f2 24%, transparent 24%),
        var(--bg);
      font-family: Georgia, "Times New Roman", serif;
    }
    .wrap {
      max-width: 980px;
      margin: 0 auto;
      padding: 20px;
    }
    h1 {
      margin: 0 0 10px;
      font-size: clamp(1.4rem, 2.5vw, 2rem);
      letter-spacing: 0.4px;
    }
    .subtitle {
      margin: 0 0 18px;
      color: var(--muted);
    }
    .card {
      background: var(--panel);
      border: 1px solid var(--border);
      border-radius: 12px;
      padding: 14px;
      box-shadow: 0 10px 24px rgba(22, 24, 30, 0.08);
      margin-bottom: 14px;
    }
    .row {
      display: flex;
      gap: 10px;
      flex-wrap: wrap;
      align-items: end;
    }
    label {
      display: grid;
      gap: 4px;
      font-size: 0.95rem;
      color: var(--muted);
    }
    select, input, button {
      font: inherit;
      border-radius: 8px;
      border: 1px solid var(--border);
      padding: 8px 10px;
      background: white;
      color: var(--ink);
    }
    button {
      background: var(--accent);
      border-color: var(--accent);
      color: white;
      cursor: pointer;
      transition: transform 100ms ease, opacity 100ms ease;
    }
    button:hover { transform: translateY(-1px); }
    button.secondary {
      background: white;
      color: var(--accent);
      border-color: var(--accent);
    }
    .pill {
      display: inline-block;
      padding: 3px 8px;
      border-radius: 999px;
      font-size: 0.8rem;
      border: 1px solid var(--border);
      color: var(--muted);
    }
    .question {
      font-size: 1.1rem;
      margin: 10px 0 14px;
      line-height: 1.45;
    }
    .choices {
      display: grid;
      gap: 8px;
    }
    .choice {
      text-align: left;
      white-space: normal;
      background: #ffffff;
      color: var(--ink);
      border-color: var(--border);
    }
    .choice.correct { border-color: var(--ok); background: #e8f7ee; }
    .choice.incorrect { border-color: var(--bad); background: #fdeceb; }
    .feedback { min-height: 22px; margin: 10px 0; font-weight: 600; }
    .feedback.ok { color: var(--ok); }
    .feedback.bad { color: var(--bad); }
    .meta {
      display: flex;
      gap: 10px;
      flex-wrap: wrap;
      color: var(--muted);
      font-size: 0.95rem;
    }
    .hidden { display: none; }
    .footer {
      color: var(--muted);
      font-size: 0.9rem;
      margin-top: 10px;
    }
    @media (max-width: 640px) {
      .row > * { width: 100%; }
      button { width: 100%; }
    }
  </style>
</head>
<body>
  <div class="wrap">
    <h1>Ham Radio Practice</h1>
    <p class="subtitle">Run exam-style, random drills, or missed-only review in your browser.</p>

    <section class="card">
      <div class="row">
        <label>
          Element
          <select id="element">
            <option value="2">Element 2 - Technician</option>
            <option value="3">Element 3 - General</option>
            <option value="4">Element 4 - Amateur Extra</option>
          </select>
        </label>
        <label>
          Mode
          <select id="mode">
            <option value="exam">Exam-style</option>
            <option value="random">Random drill</option>
            <option value="missed">Missed-only review</option>
            <option value="teach">Guided teaching</option>
          </select>
        </label>
        <label>
          Count (optional for random/missed/teach)
          <input id="count" type="number" min="1" placeholder="Default auto" />
        </label>
        <label>
          Teach Subelement (optional)
          <input id="teachSubelement" type="text" placeholder="e.g. T1, G4, E7" />
        </label>
        <label>
          Teach Group (optional)
          <input id="teachGroup" type="text" placeholder="e.g. T1A, G8D, E4C" />
        </label>
        <label>
          Questions / Group (teach)
          <input id="qpg" type="number" min="1" value="1" />
        </label>
        <button id="startBtn">Start Session</button>
      </div>
      <div class="footer">Missed questions are persisted to <code>data/progress/missed_questions.json</code>.</div>
    </section>

    <section id="sessionCard" class="card hidden">
      <div class="meta">
        <span id="progress" class="pill"></span>
        <span id="qid" class="pill"></span>
        <span id="subelementBadge" class="pill"></span>
        <span id="citation" class="pill hidden"></span>
      </div>
      <div id="questionText" class="question"></div>
      <div id="teachingFocus" class="footer hidden"></div>
      <div id="choices" class="choices"></div>
      <div id="feedback" class="feedback"></div>
      <div class="row">
        <button id="showAnswerBtn" class="secondary">Show Answer</button>
        <button id="nextBtn" class="hidden">Next</button>
      </div>
    </section>

    <section id="summaryCard" class="card hidden"></section>
  </div>

  <script>
    const state = {
      element: null,
      mode: null,
      passScore: null,
      questions: [],
      index: 0,
      asked: 0,
      correct: 0,
      locked: false,
    };

    const elementEl = document.getElementById('element');
    const modeEl = document.getElementById('mode');
    const countEl = document.getElementById('count');
    const subelementInput = document.getElementById('teachSubelement');
    const groupInput = document.getElementById('teachGroup');
    const qpgInput = document.getElementById('qpg');
    const startBtn = document.getElementById('startBtn');

    const sessionCard = document.getElementById('sessionCard');
    const summaryCard = document.getElementById('summaryCard');

    const progressEl = document.getElementById('progress');
    const qidEl = document.getElementById('qid');
    const subelementEl = document.getElementById('subelementBadge');
    const citationEl = document.getElementById('citation');
    const questionTextEl = document.getElementById('questionText');
    const teachingFocusEl = document.getElementById('teachingFocus');
    const choicesEl = document.getElementById('choices');
    const feedbackEl = document.getElementById('feedback');
    const showAnswerBtn = document.getElementById('showAnswerBtn');
    const nextBtn = document.getElementById('nextBtn');

    async function apiGet(url) {
      const res = await fetch(url);
      if (!res.ok) {
        const text = await res.text();
        throw new Error(text || `Request failed: ${res.status}`);
      }
      return await res.json();
    }

    async function apiPost(url, payload) {
      const res = await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      if (!res.ok) {
        const text = await res.text();
        throw new Error(text || `Request failed: ${res.status}`);
      }
      return await res.json();
    }

    function clearSessionUI() {
      feedbackEl.textContent = '';
      feedbackEl.className = 'feedback';
      nextBtn.classList.add('hidden');
      showAnswerBtn.classList.remove('hidden');
      choicesEl.innerHTML = '';
      teachingFocusEl.classList.add('hidden');
      teachingFocusEl.textContent = '';
      summaryCard.classList.add('hidden');
      summaryCard.innerHTML = '';
    }

    function currentQuestion() {
      return state.questions[state.index];
    }

    function renderQuestion() {
      clearSessionUI();
      const q = currentQuestion();
      if (!q) {
        renderSummary();
        return;
      }

      state.locked = false;

      sessionCard.classList.remove('hidden');
      progressEl.textContent = `${state.index + 1} / ${state.questions.length}`;
      qidEl.textContent = q.question_id;
      subelementEl.textContent = q.subelement;

      if (q.citation) {
        citationEl.textContent = q.citation;
        citationEl.classList.remove('hidden');
      } else {
        citationEl.classList.add('hidden');
      }

      questionTextEl.textContent = q.question;
      const section = q.teaching_section_title || '';
      const focus = q.teaching_focus || '';
      if (focus || section) {
        const parts = [];
        if (section) parts.push(`Section: ${section}`);
        if (focus) parts.push(`Teaching focus (${q.group}): ${focus}`);
        teachingFocusEl.textContent = parts.join(' | ');
        teachingFocusEl.classList.remove('hidden');
      }

      for (const key of ['A', 'B', 'C', 'D']) {
        const btn = document.createElement('button');
        btn.className = 'choice';
        btn.innerHTML = `<strong>${key}.</strong> ${q.choices[key]}`;
        btn.addEventListener('click', () => submitAnswer(key));
        choicesEl.appendChild(btn);
      }
    }

    async function persistResult(correct) {
      const q = currentQuestion();
      try {
        await apiPost('/api/answer', {
          element: Number(state.element),
          question_id: q.question_id,
          correct,
        });
      } catch (err) {
        console.error(err);
      }
    }

    async function submitAnswer(choice) {
      if (state.locked) return;
      state.locked = true;

      const q = currentQuestion();
      const isCorrect = choice === q.answer_key;

      state.asked += 1;
      if (isCorrect) state.correct += 1;

      await persistResult(isCorrect);

      for (const btn of choicesEl.querySelectorAll('.choice')) {
        const key = btn.textContent.trim().charAt(0);
        if (key === q.answer_key) btn.classList.add('correct');
        if (key === choice && !isCorrect) btn.classList.add('incorrect');
        btn.disabled = true;
      }

      if (isCorrect) {
        feedbackEl.textContent = 'Correct';
        feedbackEl.classList.add('ok');
      } else {
        feedbackEl.textContent = `Incorrect. Correct answer: ${q.answer_key}`;
        feedbackEl.classList.add('bad');
      }

      if (state.mode === 'teach') {
        const knowledge = q.choices[q.answer_key];
        feedbackEl.textContent += ` | Knowledge point: ${knowledge}`;
      }

      showAnswerBtn.classList.add('hidden');
      nextBtn.classList.remove('hidden');
    }

    async function showAnswer() {
      if (state.locked) return;
      state.locked = true;

      state.asked += 1;
      await persistResult(false);

      const q = currentQuestion();
      for (const btn of choicesEl.querySelectorAll('.choice')) {
        const key = btn.textContent.trim().charAt(0);
        if (key === q.answer_key) btn.classList.add('correct');
        btn.disabled = true;
      }

      feedbackEl.textContent = `Answer: ${q.answer_key}`;
      feedbackEl.classList.add('bad');

      if (state.mode === 'teach') {
        const knowledge = q.choices[q.answer_key];
        feedbackEl.textContent += ` | Knowledge point: ${knowledge}`;
      }

      showAnswerBtn.classList.add('hidden');
      nextBtn.classList.remove('hidden');
    }

    function renderSummary() {
      sessionCard.classList.add('hidden');
      summaryCard.classList.remove('hidden');

      const pct = state.asked ? ((state.correct / state.asked) * 100).toFixed(1) : '0.0';
      let resultHtml = `<h2>Session Complete</h2>
        <p><strong>Score:</strong> ${state.correct}/${state.asked} (${pct}%)</p>`;

      if (state.mode === 'exam' && Number.isInteger(state.passScore)) {
        const pass = state.correct >= state.passScore;
        resultHtml += `<p><strong>Result:</strong> ${pass ? 'PASS' : 'NOT PASS'} (needs ${state.passScore}/${state.questions.length})</p>`;
      }

      resultHtml += `<button id="restartBtn">Start Another Session</button>`;
      summaryCard.innerHTML = resultHtml;

      document.getElementById('restartBtn').addEventListener('click', () => {
        summaryCard.classList.add('hidden');
      });
    }

    async function startSession() {
      const element = elementEl.value;
      const mode = modeEl.value;
      const countRaw = countEl.value.trim();
      const subelement = subelementInput.value.trim().toUpperCase();
      const group = groupInput.value.trim().toUpperCase();
      const qpgRaw = qpgInput.value.trim();
      const count = countRaw ? Number(countRaw) : null;

      let url = `/api/session?element=${encodeURIComponent(element)}&mode=${encodeURIComponent(mode)}`;
      if (count && count > 0) {
        url += `&num_questions=${encodeURIComponent(String(count))}`;
      }
      if (mode === 'teach') {
        if (subelement) url += `&subelement=${encodeURIComponent(subelement)}`;
        if (group) url += `&group=${encodeURIComponent(group)}`;
        if (qpgRaw) url += `&questions_per_group=${encodeURIComponent(qpgRaw)}`;
      }

      try {
        const data = await apiGet(url);
        state.element = Number(element);
        state.mode = mode;
        state.passScore = data.pass_score;
        state.questions = data.questions || [];
        state.index = 0;
        state.asked = 0;
        state.correct = 0;

        if (!state.questions.length) {
          summaryCard.classList.remove('hidden');
          summaryCard.innerHTML = '<h2>No questions available</h2><p>This usually means there are no missed questions yet for this element.</p>';
          sessionCard.classList.add('hidden');
          return;
        }

        renderQuestion();
      } catch (err) {
        alert(`Unable to start session: ${err.message}`);
      }
    }

    nextBtn.addEventListener('click', () => {
      state.index += 1;
      if (state.index >= state.questions.length) {
        renderSummary();
      } else {
        renderQuestion();
      }
    });

    showAnswerBtn.addEventListener('click', showAnswer);
    startBtn.addEventListener('click', startSession);
  </script>
</body>
</html>
"""


class HamPracticeHandler(BaseHTTPRequestHandler):
    def _send_json(self, status: int, payload: Dict[str, object]) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_html(self, status: int, body: str) -> None:
        data = body.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _read_json(self) -> Dict[str, object]:
        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length).decode("utf-8") if length > 0 else "{}"
        parsed = json.loads(raw)
        if not isinstance(parsed, dict):
            raise ValueError("JSON body must be an object")
        return parsed

    def log_message(self, format: str, *args: object) -> None:
        return

    def do_GET(self) -> None:
        parsed = urllib.parse.urlsplit(self.path)

        if parsed.path == "/":
            self._send_html(200, WEB_INDEX_HTML)
            return

        if parsed.path == "/api/missed":
            self._send_json(200, {"missed": load_missed_db()})
            return

        if parsed.path == "/api/session":
            params = urllib.parse.parse_qs(parsed.query)
            element_str = params.get("element", ["2"])[0]
            mode = params.get("mode", ["exam"])[0]
            num_raw = params.get("num_questions", [""])[0]
            subelement = params.get("subelement", [""])[0].strip() or None
            group = params.get("group", [""])[0].strip() or None
            qpg_raw = params.get("questions_per_group", ["1"])[0]

            try:
                element = int(element_str)
            except ValueError:
                self._send_json(400, {"error": "Invalid element"})
                return

            if element not in POOL_CONFIG:
                self._send_json(400, {"error": "Unsupported element"})
                return

            if mode not in {"exam", "random", "missed", "teach"}:
                self._send_json(400, {"error": "Unsupported mode"})
                return

            num_questions: Optional[int] = None
            if num_raw:
                try:
                    num_questions = int(num_raw)
                except ValueError:
                    self._send_json(400, {"error": "num_questions must be an integer"})
                    return

            try:
                questions_per_group = int(qpg_raw)
            except ValueError:
                self._send_json(400, {"error": "questions_per_group must be an integer"})
                return

            try:
                selected, pass_score, label = select_questions_for_mode(
                    element=element,
                    mode=mode,
                    num_questions=num_questions,
                    rng=random.Random(),
                    missed_db=load_missed_db(),
                    subelement_filter=subelement,
                    group_filter=group,
                    questions_per_group=max(1, questions_per_group),
                )
            except FileNotFoundError as exc:
                self._send_json(400, {"error": str(exc)})
                return

            self._send_json(
                200,
                {
                    "label": label,
                    "element": element,
                    "mode": mode,
                    "pass_score": pass_score,
                    "total": len(selected),
                    "questions": selected,
                },
            )
            return

        self._send_json(404, {"error": "Not found"})

    def do_POST(self) -> None:
        parsed = urllib.parse.urlsplit(self.path)

        if parsed.path == "/api/answer":
            try:
                payload = self._read_json()
            except Exception as exc:
                self._send_json(400, {"error": f"Invalid JSON: {exc}"})
                return

            try:
                element = int(payload.get("element", 0))
            except ValueError:
                self._send_json(400, {"error": "element must be an integer"})
                return

            question_id = str(payload.get("question_id", "")).strip()
            correct = bool(payload.get("correct", False))

            if element not in POOL_CONFIG:
                self._send_json(400, {"error": "Unsupported element"})
                return
            if not question_id:
                self._send_json(400, {"error": "question_id is required"})
                return

            missed_db = load_missed_db()
            mark_question_result(missed_db, element, question_id, correct)
            save_missed_db(missed_db)
            self._send_json(200, {"ok": True, "missed_count": len(missed_db.get(str(element), []))})
            return

        self._send_json(404, {"error": "Not found"})


def command_web(args: argparse.Namespace) -> int:
    for element in sorted(POOL_CONFIG):
        load_questions_from_json(element)

    server = ThreadingHTTPServer((args.host, args.port), HamPracticeHandler)
    print(f"Web UI running at http://{args.host}:{args.port}")
    print("Press Ctrl+C to stop")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping web server")
        server.server_close()
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="NCVEC ham radio practice test utility")
    subparsers = parser.add_subparsers(dest="command", required=True)

    update = subparsers.add_parser("update-pools", help="Download/parse official question pools")
    update.add_argument(
        "--download",
        action="store_true",
        help="Force re-download of source PDFs even if local copies already exist",
    )
    update.set_defaults(func=command_update_pools)

    practice = subparsers.add_parser("practice", help="Run an interactive practice session")
    practice.add_argument(
        "--element",
        choices=["2", "3", "4", "all"],
        default="2",
        help="Element to practice (2=Technician, 3=General, 4=Extra, all=run all three)",
    )
    practice.add_argument(
        "--mode",
        choices=["exam", "random", "missed", "teach"],
        default="exam",
        help="exam uses official distribution; random samples pool; missed reviews wrong answers; teach is guided study by group",
    )
    practice.add_argument(
        "--num-questions",
        type=int,
        default=None,
        help="Question count for random/missed/teach (ignored in exam mode)",
    )
    practice.add_argument(
        "--subelement",
        type=str,
        default=None,
        help="Optional filter for teach mode, e.g. T1, G4, E7",
    )
    practice.add_argument(
        "--group",
        type=str,
        default=None,
        help="Optional filter for teach mode, e.g. T1A, G8D, E4C",
    )
    practice.add_argument(
        "--questions-per-group",
        type=int,
        default=1,
        help="Teach mode: number of sampled questions per group before moving to next",
    )
    practice.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Set RNG seed for reproducible sessions",
    )
    practice.add_argument(
        "--width",
        type=int,
        default=100,
        help="Output wrap width",
    )
    practice.set_defaults(func=command_practice)

    stats = subparsers.add_parser("stats", help="Show pool counts by element/subelement")
    stats.set_defaults(func=command_stats)

    syllabus_cmd = subparsers.add_parser("syllabus", help="Print full syllabus objectives by element")
    syllabus_cmd.add_argument(
        "--element",
        choices=["2", "3", "4", "all"],
        default="all",
        help="Element to print syllabus for",
    )
    syllabus_cmd.set_defaults(func=command_syllabus)

    web_cmd = subparsers.add_parser("web", help="Run a local web UI")
    web_cmd.add_argument("--host", default="127.0.0.1", help="Host bind address")
    web_cmd.add_argument("--port", type=int, default=8787, help="HTTP port")
    web_cmd.set_defaults(func=command_web)

    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        return int(args.func(args))
    except KeyboardInterrupt:
        print("\nInterrupted")
        return 130


if __name__ == "__main__":
    sys.exit(main())
