#!/usr/bin/env python3
"""Separate educational web app for learning ham radio physics and math."""

from __future__ import annotations

import argparse
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Dict, List
import urllib.parse

from ham_practice import POOL_CONFIG, load_pool_payload


LEARNING_ROADMAP: List[Dict[str, Any]] = [
    {
        "id": "m1",
        "title": "Signals As Waves",
        "goal": "Understand what a radio wave is and how frequency, period, and wavelength connect.",
        "key_points": [
            "Electromagnetic waves have electric and magnetic fields at right angles.",
            "Frequency (Hz) means cycles per second; period T = 1/f.",
            "Wavelength lambda = c/f, and for amateur work lambda(m) approx 300/f(MHz).",
            "Higher frequency means shorter wavelength and usually more line-of-sight behavior.",
        ],
        "math": [
            "T = 1 / f",
            "lambda = c / f",
            "lambda(m) ~= 300 / f(MHz)",
        ],
        "why_exam": "Band planning, antenna sizing, and propagation questions all depend on this.",
        "practice_bridge": [
            "T3B",
            "G3C",
            "E3A",
        ],
    },
    {
        "id": "m2",
        "title": "Units, Ratios, And dB",
        "goal": "Think in logarithms and ratio language used across RF systems.",
        "key_points": [
            "Decibels compare ratios; they do not represent absolute power by themselves.",
            "+3 dB is about 2x power, +10 dB is 10x power.",
            "Power in dBm references 1 milliwatt.",
            "Losses and gains in a link budget add and subtract in dB.",
        ],
        "math": [
            "dB = 10 * log10(P2 / P1)",
            "P2 / P1 = 10^(dB/10)",
            "dBm = 10 * log10(PmW)",
        ],
        "why_exam": "Amplifier gain, feedline loss, and system performance are frequently tested.",
        "practice_bridge": [
            "T5B",
            "G5B",
            "E4D",
        ],
    },
    {
        "id": "m3",
        "title": "DC Circuit Core",
        "goal": "Build intuition for voltage, current, resistance, and power relationships.",
        "key_points": [
            "Voltage drives current through resistance.",
            "Power is rate of energy use and sets thermal stress in components.",
            "Series and parallel structures change equivalent resistance and current sharing.",
            "The same formulas appear in power-supply and safety decisions.",
        ],
        "math": [
            "V = I * R",
            "P = V * I",
            "P = I^2 * R",
            "P = V^2 / R",
        ],
        "why_exam": "This is foundational for troubleshooting and electronics subelements.",
        "practice_bridge": [
            "T5D",
            "G5C",
            "E5B",
        ],
    },
    {
        "id": "m4",
        "title": "Reactance And Resonance",
        "goal": "Understand why RF circuits behave differently from simple DC circuits.",
        "key_points": [
            "Capacitors and inductors store energy and cause phase shift.",
            "Reactance changes with frequency: XL rises with f, XC falls with f.",
            "At resonance, reactive parts cancel and transfer can peak.",
            "Quality factor Q links selectivity to bandwidth.",
        ],
        "math": [
            "XL = 2 * pi * f * L",
            "XC = 1 / (2 * pi * f * C)",
            "f0 = 1 / (2 * pi * sqrt(LC))",
            "Q ~= f0 / BW",
        ],
        "why_exam": "Filter behavior, matching networks, and receiver selectivity rely on this.",
        "practice_bridge": [
            "T5C",
            "G7C",
            "E5A",
        ],
    },
    {
        "id": "m5",
        "title": "Modulation And Bandwidth",
        "goal": "Link signal type to occupied bandwidth and practical operating choices.",
        "key_points": [
            "Different modes use spectrum differently (CW, SSB, FM, digital modes).",
            "SSB improves efficiency by removing redundant carrier and sideband content.",
            "FM deviation and audio content shape occupied bandwidth.",
            "Band-edge operation requires awareness of transmitted signal width.",
        ],
        "math": [
            "BW and mode relationship is qualitative in many exam items",
            "For FM, occupied BW rises with deviation and modulating frequency",
        ],
        "why_exam": "Mode selection, band-edge compliance, and operating practice depend on this.",
        "practice_bridge": [
            "T8A",
            "G4D",
            "E8A",
        ],
    },
    {
        "id": "m6",
        "title": "Feed Lines, Matching, And SWR",
        "goal": "Understand reflections, mismatch, and practical transmission-line decisions.",
        "key_points": [
            "A mismatch causes reflected power and standing waves.",
            "SWR indicates match quality but does not directly tell line loss magnitude.",
            "Higher frequency and longer runs increase coax attenuation concerns.",
            "Tuners can transform impedance but do not magically remove feedline loss.",
        ],
        "math": [
            "SWR = (1 + |Gamma|) / (1 - |Gamma|)",
            "Gamma = (ZL - Z0) / (ZL + Z0)",
        ],
        "why_exam": "Antenna/feedline setup, troubleshooting, and station optimization require this.",
        "practice_bridge": [
            "T9B",
            "G9A",
            "E9F",
        ],
    },
    {
        "id": "m7",
        "title": "Antennas And Radiation",
        "goal": "Build a mental model of pattern, polarization, and gain tradeoffs.",
        "key_points": [
            "Antenna pattern shapes where energy goes.",
            "Gain concentrates energy; it is not free power generation.",
            "Polarization mismatch can cause major signal loss.",
            "Antenna height and surrounding environment strongly affect real performance.",
        ],
        "math": [
            "Effective radiated behavior is often reasoned in dB",
            "Free-space path and antenna gain combine in link budgets",
        ],
        "why_exam": "Portable/mobile setup and HF/VHF planning are antenna-driven.",
        "practice_bridge": [
            "T9A",
            "G9C",
            "E9A",
        ],
    },
    {
        "id": "m8",
        "title": "Propagation Physics",
        "goal": "Predict when and why a band opens or closes.",
        "key_points": [
            "HF propagation depends on ionospheric layers, solar cycle, and geometry.",
            "VHF/UHF often follows line-of-sight but can use tropospheric and sporadic-E enhancements.",
            "Space weather indicators correlate with path reliability and noise.",
            "Operating strategy changes with time of day, season, and solar conditions.",
        ],
        "math": [
            "Radio horizon and skip behavior are commonly reasoned conceptually",
            "MUF/LUF concepts inform practical band selection",
        ],
        "why_exam": "Finding working frequencies quickly is a core operator skill.",
        "practice_bridge": [
            "T3C",
            "G3A",
            "E3C",
        ],
    },
    {
        "id": "m9",
        "title": "Link Budget Thinking",
        "goal": "Estimate if a path works before transmitting.",
        "key_points": [
            "Start with transmit power in dBm and add gains/subtract losses.",
            "Compare received level with receiver sensitivity and required SNR.",
            "Distance, frequency, and antenna system dominate path viability.",
            "This framework explains why small improvements can matter a lot.",
        ],
        "math": [
            "FSPL(dB) = 32.44 + 20log10(fMHz) + 20log10(dkm)",
            "Prx(dBm) = Ptx + Gtx + Grx - losses - pathloss",
        ],
        "why_exam": "Important in Extra-level performance and weak-signal scenarios.",
        "practice_bridge": [
            "G8A",
            "E4D",
            "E9B",
        ],
    },
    {
        "id": "m10",
        "title": "RF Safety And Responsible Operation",
        "goal": "Operate safely and legally while protecting people and equipment.",
        "key_points": [
            "Evaluate exposure conditions and maintain compliance with FCC limits.",
            "Grounding, bonding, and lightning protection reduce risk.",
            "Battery chemistry, charging, and thermal events require discipline.",
            "Control operator responsibility and good engineering practice are essential.",
        ],
        "math": [
            "Inverse-square behavior: field strength and power density drop with distance",
            "Duty cycle and average power affect exposure assessments",
        ],
        "why_exam": "Safety and rules are high-value and high-frequency exam topics.",
        "practice_bridge": [
            "T0C",
            "G0A",
            "E0A",
        ],
    },
]


BEGINNER_EXPANSIONS: Dict[str, Dict[str, Any]] = {
    "m1": {
        "plain_english": "Radio is just a repeating wiggle moving through space. Faster wiggles mean higher frequency and shorter physical size.",
        "step_by_step": [
            "Start with frequency: how many wiggles happen each second.",
            "Convert to wavelength using 300/f(MHz).",
            "Use wavelength to estimate antenna size (half-wave and quarter-wave).",
            "Use that size intuition when picking bands and antennas.",
        ],
        "common_mistakes": [
            "Thinking higher frequency means farther range in all cases.",
            "Mixing up Hz, kHz, and MHz by factors of 1000.",
            "Using antenna lengths without matching units.",
        ],
    },
    "m2": {
        "plain_english": "dB is a compact way to talk about 'how many times bigger or smaller' something is.",
        "step_by_step": [
            "Treat dB like comparison points, not raw power.",
            "Memorize anchors: +3 dB about 2x, +10 dB = 10x.",
            "Convert when needed between dB and ratio.",
            "Add gains and subtract losses in a link budget.",
        ],
        "common_mistakes": [
            "Adding linear power and dB values together.",
            "Forgetting that negative dB means loss.",
            "Confusing dB (ratio) with dBm (absolute power reference).",
        ],
    },
    "m3": {
        "plain_english": "Voltage pushes, current flows, resistance resists, and power is how hard your circuit is working.",
        "step_by_step": [
            "Pick any two of V, I, and R.",
            "Solve the third with Ohm's law.",
            "Compute power to understand heating and stress.",
            "Use this to sanity-check your station wiring and loads.",
        ],
        "common_mistakes": [
            "Using volts when the formula needs current.",
            "Forgetting that power can rise quickly with current.",
            "Ignoring resistor watt ratings in real circuits.",
        ],
    },
    "m4": {
        "plain_english": "At RF, capacitors and inductors act like frequency-dependent resistors, so circuits change behavior with frequency.",
        "step_by_step": [
            "Learn that XL grows with frequency while XC shrinks.",
            "Find resonance where inductive and capacitive effects balance.",
            "Relate sharpness of peak to Q and bandwidth.",
            "Apply this to filters and tuning behavior.",
        ],
        "common_mistakes": [
            "Treating capacitor/inductor behavior as fixed like a resistor.",
            "Confusing high Q with 'always better' (it can be too narrow).",
            "Ignoring component tolerances and real losses.",
        ],
    },
    "m5": {
        "plain_english": "Different modulation modes package information differently, so they take different amounts of spectrum.",
        "step_by_step": [
            "Identify which mode you are using (CW, SSB, FM, digital).",
            "Estimate how wide that signal is.",
            "Check band edges so your signal stays legal.",
            "Pick the mode that best matches the communication goal.",
        ],
        "common_mistakes": [
            "Using FM where narrow modes are better for weak signals.",
            "Setting transmit audio too hot and splattering bandwidth.",
            "Operating near band edges without margin.",
        ],
    },
    "m6": {
        "plain_english": "When line and load do not match, part of your signal bounces back and creates standing waves.",
        "step_by_step": [
            "Measure SWR to estimate mismatch severity.",
            "Inspect feedline type, length, and frequency loss.",
            "Adjust antenna/feedpoint before relying on tuner fixes.",
            "Re-test after each change and compare results.",
        ],
        "common_mistakes": [
            "Believing tuner fixes all mismatch losses everywhere.",
            "Chasing perfect 1:1 SWR when 'good enough' is sufficient.",
            "Ignoring coax loss at higher frequencies.",
        ],
    },
    "m7": {
        "plain_english": "Antennas shape where your power goes; gain is focusing, not creating energy.",
        "step_by_step": [
            "Choose desired radiation direction and polarization.",
            "Select antenna type for that pattern.",
            "Install with height and surroundings in mind.",
            "Validate with on-air reports and measurements.",
        ],
        "common_mistakes": [
            "Confusing gain claims with guaranteed better coverage everywhere.",
            "Ignoring polarization mismatch penalties.",
            "Placing antennas too close to noisy structures.",
        ],
    },
    "m8": {
        "plain_english": "Propagation is the radio 'weather' between stations, and it changes by time, frequency, and solar conditions.",
        "step_by_step": [
            "Start with time of day and target distance.",
            "Choose likely bands based on current conditions.",
            "Use reports/spotting tools to confirm openings.",
            "Shift band or mode when conditions change.",
        ],
        "common_mistakes": [
            "Assuming one band works all day the same way.",
            "Ignoring solar/geomagnetic conditions.",
            "Not adapting quickly when a band closes.",
        ],
    },
    "m9": {
        "plain_english": "A link budget is a scoreboard: start with TX power, then add gains and subtract losses to see if the signal arrives strong enough.",
        "step_by_step": [
            "Convert transmit power to dBm.",
            "Add antenna gains and subtract line losses/path loss.",
            "Compare result to receiver sensitivity and SNR needs.",
            "Improve weakest points (antenna, feedline, noise floor).",
        ],
        "common_mistakes": [
            "Mixing linear units and dB in one equation.",
            "Ignoring receive-side noise and required SNR.",
            "Assuming more power always solves bad system design.",
        ],
    },
    "m10": {
        "plain_english": "Safe station design means controlling exposure distance, electrical risk, and operating responsibility.",
        "step_by_step": [
            "Identify possible RF and electrical hazards.",
            "Apply distance, power, and duty-cycle controls.",
            "Implement grounding, bonding, and lightning safety.",
            "Review station procedures regularly.",
        ],
        "common_mistakes": [
            "Treating RF safety as optional at low power.",
            "Skipping bonding/grounding checks.",
            "Underestimating battery failure risks.",
        ],
    },
}


KNOWLEDGE_CHECKS: Dict[str, List[Dict[str, Any]]] = {
    "m1": [
        {
            "q": "If frequency goes up, what happens to wavelength?",
            "choices": ["It gets longer", "It gets shorter", "It stays the same"],
            "answer": 1,
            "explain": "Wavelength and frequency move in opposite directions (lambda = c/f).",
        },
        {
            "q": "About how long is a 2 meter half-wave antenna?",
            "choices": ["About 1 meter", "About 2 meters", "About 4 meters"],
            "answer": 0,
            "explain": "A half-wave on the 2 meter band is around 1 meter.",
        },
        {
            "q": "What does MHz measure?",
            "choices": ["Power", "Frequency", "Resistance"],
            "answer": 1,
            "explain": "MHz is millions of cycles per second, a frequency unit.",
        },
    ],
    "m2": [
        {
            "q": "A +3 dB increase is closest to what power change?",
            "choices": ["About 2x", "About 5x", "About 10x"],
            "answer": 0,
            "explain": "+3 dB is approximately double power.",
        },
        {
            "q": "Is dB an absolute power unit?",
            "choices": ["Yes", "No"],
            "answer": 1,
            "explain": "dB is a ratio. dBm is an absolute reference to 1 mW.",
        },
        {
            "q": "In a link budget, how are losses handled in dB?",
            "choices": ["Added", "Subtracted", "Ignored"],
            "answer": 1,
            "explain": "You subtract losses and add gains in dB.",
        },
    ],
    "m3": [
        {
            "q": "Ohm's law is:",
            "choices": ["V = I * R", "P = V / I", "R = V * I"],
            "answer": 0,
            "explain": "Voltage equals current times resistance.",
        },
        {
            "q": "If V is fixed and R increases, current does what?",
            "choices": ["Increases", "Decreases", "Stays the same"],
            "answer": 1,
            "explain": "I = V/R, so higher R gives lower I for fixed V.",
        },
        {
            "q": "Power can be calculated as:",
            "choices": ["P = V * I", "P = V + I", "P = R / I"],
            "answer": 0,
            "explain": "Power in watts is voltage times current.",
        },
    ],
    "m4": [
        {
            "q": "Inductive reactance XL changes with frequency by:",
            "choices": ["Going up", "Going down", "Staying fixed"],
            "answer": 0,
            "explain": "XL = 2*pi*f*L, so it rises as frequency rises.",
        },
        {
            "q": "Capacitive reactance XC changes with frequency by:",
            "choices": ["Going up", "Going down", "Staying fixed"],
            "answer": 1,
            "explain": "XC = 1/(2*pi*f*C), so it falls as frequency rises.",
        },
        {
            "q": "At resonance, the circuit often has:",
            "choices": ["A clear peak response", "No response", "Infinite DC current"],
            "answer": 0,
            "explain": "Resonance is where reactive parts balance and response can peak.",
        },
    ],
    "m5": [
        {
            "q": "Which mode is usually narrower in bandwidth?",
            "choices": ["FM", "SSB", "Broadcast TV"],
            "answer": 1,
            "explain": "SSB generally occupies less bandwidth than FM voice.",
        },
        {
            "q": "Why care about bandwidth near band edges?",
            "choices": ["No reason", "To avoid out-of-band emissions", "Only for satellites"],
            "answer": 1,
            "explain": "Your occupied signal must stay inside legal band segments.",
        },
        {
            "q": "Overdriving audio in SSB often causes:",
            "choices": ["Cleaner signal", "Wider, dirtier signal", "No change"],
            "answer": 1,
            "explain": "Too much drive causes distortion and splatter.",
        },
    ],
    "m6": [
        {
            "q": "A high SWR usually indicates:",
            "choices": ["Good match", "Mismatch", "Low battery"],
            "answer": 1,
            "explain": "High SWR usually means line/load mismatch.",
        },
        {
            "q": "Can a tuner remove all feedline loss?",
            "choices": ["Yes", "No"],
            "answer": 1,
            "explain": "A tuner transforms impedance but cannot erase line loss already present.",
        },
        {
            "q": "At higher frequency, typical coax loss is usually:",
            "choices": ["Lower", "Higher", "Unchanged"],
            "answer": 1,
            "explain": "Loss generally increases as frequency increases.",
        },
    ],
    "m7": [
        {
            "q": "Antenna gain mostly means:",
            "choices": ["Creating extra power", "Focusing energy", "Cooling the radio"],
            "answer": 1,
            "explain": "Gain is directional concentration, not free energy.",
        },
        {
            "q": "Wrong polarization between two stations causes:",
            "choices": ["Potential signal loss", "Guaranteed stronger signal", "No effect"],
            "answer": 0,
            "explain": "Polarization mismatch can reduce received signal significantly.",
        },
        {
            "q": "Directional antennas are best when:",
            "choices": ["You need coverage in one main direction", "You need equal all-around coverage", "You never move"],
            "answer": 0,
            "explain": "Directional designs focus energy where you need it most.",
        },
    ],
    "m8": [
        {
            "q": "HF propagation often depends strongly on:",
            "choices": ["Moon phase only", "Ionosphere and solar conditions", "Cable color"],
            "answer": 1,
            "explain": "Ionospheric conditions drive many HF path behaviors.",
        },
        {
            "q": "VHF/UHF is commonly:",
            "choices": ["Line-of-sight dominated", "Always worldwide", "Always groundwave only"],
            "answer": 0,
            "explain": "Higher frequencies are often line-of-sight, with special enhancements.",
        },
        {
            "q": "When a band closes, a good operator should:",
            "choices": ["Keep calling forever", "Try another band/mode", "Increase power only"],
            "answer": 1,
            "explain": "Adapting bands and modes is core operating skill.",
        },
    ],
    "m9": [
        {
            "q": "A link budget starts with:",
            "choices": ["Random guess", "Transmit power reference", "Antenna color"],
            "answer": 1,
            "explain": "Start from known transmit power and track gains/losses.",
        },
        {
            "q": "If received level is below receiver needs, you should:",
            "choices": ["Improve gains/reduce losses/noise", "Do nothing", "Only change call sign"],
            "answer": 0,
            "explain": "Optimize system components and noise environment.",
        },
        {
            "q": "FSPL generally changes with distance by:",
            "choices": ["Increasing", "Decreasing", "Staying constant"],
            "answer": 0,
            "explain": "Free-space path loss grows with distance.",
        },
    ],
    "m10": [
        {
            "q": "Increasing distance from an antenna usually:",
            "choices": ["Raises exposure", "Lowers exposure", "Has no effect"],
            "answer": 1,
            "explain": "Field strength and density drop quickly with distance.",
        },
        {
            "q": "Good station safety includes:",
            "choices": ["Grounding and bonding", "Ignoring wiring", "No labels"],
            "answer": 0,
            "explain": "Grounding/bonding are core safety practices.",
        },
        {
            "q": "Battery safety is important because:",
            "choices": ["Batteries are always harmless", "Thermal and chemical hazards can occur", "Only FCC cares"],
            "answer": 1,
            "explain": "Improper charging/discharging can create serious hazards.",
        },
    ],
}


def get_learning_roadmap() -> List[Dict[str, Any]]:
    merged: List[Dict[str, Any]] = []
    for module in LEARNING_ROADMAP:
        item = dict(module)
        item.update(BEGINNER_EXPANSIONS.get(str(module.get("id")), {}))
        item["knowledge_checks"] = KNOWLEDGE_CHECKS.get(str(module.get("id")), [])
        merged.append(item)
    return merged


def load_syllabus_snapshot() -> Dict[str, Any]:
    snapshot: Dict[str, Any] = {}
    for element, config in POOL_CONFIG.items():
        payload = load_pool_payload(element)
        metadata = payload.get("metadata", {})
        syllabus = metadata.get("syllabus", {})
        snapshot[str(element)] = {
            "element": element,
            "license_class": config["name"],
            "pool_cycle": metadata.get("pool_cycle", ""),
            "subelements": syllabus.get("subelements", {}),
            "group_objectives": syllabus.get("group_objectives", {}),
            "question_count": metadata.get("question_count", 0),
            "exam_questions": metadata.get("exam_questions", 0),
            "pass_score": metadata.get("pass_score", 0),
        }
    return snapshot


WEB_TEMPLATE = """<!doctype html>
<html lang=\"en\">
<head>
  <meta charset=\"utf-8\" />
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
  <title>Ham Radio Learning Studio</title>
  <style>
    :root {
      --ink: #1e2a2f;
      --muted: #4c5c63;
      --paper: #fcfbf7;
      --panel: #ffffff;
      --line: #d9d3c5;
      --accent: #0f766e;
      --accent-2: #b45309;
      --ok: #0b7d3e;
      --bad: #b91c1c;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      color: var(--ink);
      background:
        radial-gradient(1200px 500px at 8% -10%, #d2f3ee 0, transparent 60%),
        radial-gradient(1000px 500px at 100% -8%, #f7e9d3 0, transparent 55%),
        var(--paper);
      font-family: \"Palatino Linotype\", \"Book Antiqua\", Palatino, serif;
      line-height: 1.45;
    }
    .wrap {
      max-width: 1200px;
      margin: 0 auto;
      padding: 22px 18px 40px;
    }
    h1 {
      margin: 0 0 6px;
      font-size: clamp(1.5rem, 3vw, 2.3rem);
      letter-spacing: 0.4px;
    }
    .sub {
      margin: 0 0 16px;
      color: var(--muted);
      max-width: 920px;
    }
    .layout {
      display: grid;
      grid-template-columns: 300px 1fr;
      gap: 14px;
    }
    .card {
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 12px;
      box-shadow: 0 12px 28px rgba(28, 35, 36, 0.08);
      padding: 14px;
    }
    .sticky {
      position: sticky;
      top: 14px;
      height: fit-content;
      max-height: calc(100vh - 28px);
      overflow: auto;
    }
    .module-btn {
      display: block;
      width: 100%;
      text-align: left;
      margin: 0 0 8px;
      border: 1px solid var(--line);
      border-radius: 10px;
      background: #fff;
      padding: 9px 10px;
      color: var(--ink);
      cursor: pointer;
      font: inherit;
    }
    .module-btn.active {
      border-color: var(--accent);
      background: #effcf9;
    }
    .module-kicker {
      font-size: 0.78rem;
      color: var(--muted);
      margin-bottom: 2px;
      letter-spacing: 0.2px;
      text-transform: uppercase;
    }
    .module-title {
      margin: 0;
      font-size: 1.1rem;
    }
    .chip {
      display: inline-block;
      padding: 3px 8px;
      border-radius: 999px;
      border: 1px solid var(--line);
      color: var(--muted);
      font-size: 0.84rem;
      margin: 2px 6px 2px 0;
      background: #fff;
    }
    .eq {
      font-family: \"Lucida Console\", Monaco, monospace;
      font-size: 0.9rem;
      background: #f7f6f3;
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 6px 8px;
      margin: 4px 0;
      display: inline-block;
    }
    h2, h3 {
      margin: 0 0 8px;
    }
    ul {
      margin: 6px 0 12px 18px;
      padding: 0;
    }
    .grid2 {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 12px;
    }
    .graph-card canvas {
      width: 100%;
      height: 220px;
      background: #fff;
      border: 1px solid var(--line);
      border-radius: 10px;
    }
    .control-row {
      display: grid;
      grid-template-columns: 1fr 120px;
      gap: 8px;
      align-items: center;
      margin-top: 8px;
    }
    .calc-grid {
      display: grid;
      grid-template-columns: repeat(3, minmax(220px, 1fr));
      gap: 12px;
    }
    label {
      display: grid;
      gap: 4px;
      color: var(--muted);
      font-size: 0.9rem;
    }
    input, select, button {
      font: inherit;
      padding: 8px 9px;
      border-radius: 8px;
      border: 1px solid var(--line);
      background: #fff;
      color: var(--ink);
    }
    button {
      background: var(--accent);
      color: #fff;
      border-color: var(--accent);
      cursor: pointer;
    }
    .secondary {
      background: #fff;
      color: var(--accent);
    }
    .result {
      margin-top: 8px;
      padding: 8px;
      border: 1px solid var(--line);
      border-radius: 8px;
      background: #f9faf9;
      min-height: 36px;
      font-size: 0.92rem;
    }
    .small {
      color: var(--muted);
      font-size: 0.88rem;
    }
    .roadmap-practice {
      margin-top: 10px;
      padding: 10px;
      border: 1px dashed var(--line);
      border-radius: 10px;
      background: #f8fbfb;
    }
    .plain-box {
      border: 1px solid var(--line);
      border-radius: 10px;
      padding: 10px;
      background: #fffdf7;
      margin-bottom: 10px;
    }
    .beginner-grid {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 12px;
    }
    .lesson-visual canvas {
      width: 100%;
      height: 240px;
      background: #fff;
      border: 1px solid var(--line);
      border-radius: 10px;
    }
    .caption {
      margin-top: 6px;
      font-size: 0.86rem;
      color: var(--muted);
    }
    .toggle-row {
      display: flex;
      align-items: center;
      gap: 10px;
      margin-bottom: 10px;
      padding: 10px;
      border: 1px solid var(--line);
      border-radius: 10px;
      background: #f7fbff;
    }
    .hint-box {
      margin-top: 8px;
      padding: 8px 10px;
      border-radius: 8px;
      border: 1px dashed var(--line);
      background: #fdfcf8;
      color: var(--muted);
      font-size: 0.88rem;
    }
    .hidden { display: none; }
    .quiz-wrap {
      margin-top: 12px;
      border: 1px solid var(--line);
      border-radius: 10px;
      padding: 10px;
      background: #fbfdfb;
    }
    .quiz-q {
      font-weight: 600;
      margin-bottom: 8px;
    }
    .quiz-choice {
      display: block;
      width: 100%;
      text-align: left;
      margin: 6px 0;
      background: #fff;
      color: var(--ink);
      border: 1px solid var(--line);
    }
    .quiz-choice.correct { border-color: var(--ok); background: #ebf8ef; }
    .quiz-choice.incorrect { border-color: var(--bad); background: #fceceb; }
    .quiz-meta {
      margin-top: 8px;
      color: var(--muted);
      font-size: 0.88rem;
    }
    .cmd {
      font-family: \"Lucida Console\", Monaco, monospace;
      font-size: 0.82rem;
      background: #f0f5f5;
      border: 1px solid #d5dfdf;
      padding: 5px 7px;
      border-radius: 7px;
      display: block;
      margin: 4px 0;
      overflow: auto;
      white-space: nowrap;
    }
    table {
      width: 100%;
      border-collapse: collapse;
      font-size: 0.92rem;
    }
    th, td {
      text-align: left;
      border-bottom: 1px solid var(--line);
      padding: 7px 6px;
      vertical-align: top;
    }
    th {
      color: var(--muted);
      font-weight: 600;
      font-size: 0.85rem;
      text-transform: uppercase;
      letter-spacing: 0.2px;
    }
    .foot {
      margin-top: 10px;
      color: var(--muted);
      font-size: 0.85rem;
    }
    .source-jump {
      color: var(--ink);
      font-weight: 600;
      text-decoration: underline;
      text-underline-offset: 2px;
    }
    .source-list {
      margin: 8px 0 0;
      padding-left: 18px;
    }
    .source-list li {
      margin: 6px 0;
    }
    .source-list a {
      color: #0f4a69;
    }
    @media (max-width: 980px) {
      .layout { grid-template-columns: 1fr; }
      .sticky { position: static; max-height: none; }
      .grid2 { grid-template-columns: 1fr; }
      .beginner-grid { grid-template-columns: 1fr; }
      .calc-grid { grid-template-columns: 1fr; }
    }
  </style>
</head>
<body>
  <div class=\"wrap\">
    <h1>Ham Radio Learning Studio</h1>
    <p class=\"sub\">A separate learning interface for people starting from zero physics background. Each lesson explains the idea in plain language, then adds equations, visuals, and practice bridges.</p>
    <p class=\"small\"><a class=\"source-jump\" href=\"#sources\">Sources</a></p>

    <div class=\"layout\">
      <aside class=\"card sticky\">
        <h2>Step-By-Step Roadmap</h2>
        <div id=\"moduleList\"></div>
      </aside>

      <main>
        <section class=\"card\" id=\"lessonCard\">
          <div class=\"module-kicker\" id=\"moduleKicker\"></div>
          <h2 id=\"moduleTitle\"></h2>
          <p id=\"moduleGoal\"></p>
          <div class=\"toggle-row\">
            <label style=\"display:flex;align-items:center;gap:8px;color:var(--ink);font-size:0.92rem;\">
              <input id=\"superBeginnerToggle\" type=\"checkbox\" />
              Super Beginner Mode (start simple, reveal details step-by-step)
            </label>
            <button id=\"revealDetailBtn\" class=\"secondary hidden\" style=\"margin-left:auto;\">Reveal Next Detail</button>
          </div>
          <div id=\"superHint\" class=\"hint-box hidden\"></div>
          <div class=\"plain-box\">
            <h3>In Plain English</h3>
            <p id=\"modulePlain\"></p>
          </div>
          <div class=\"beginner-grid\">
            <div>
              <h3>Beginner Step-By-Step</h3>
              <ol id=\"moduleSteps\"></ol>
            </div>
            <div>
              <h3>Common Mistakes To Avoid</h3>
              <ul id=\"moduleMistakes\"></ul>
            </div>
          </div>
          <div id=\"detailBlock\">
            <h3 id=\"keyConceptsTitle\">Key Concepts</h3>
            <ul id=\"modulePoints\"></ul>
            <h3 id=\"equationTitle\">Core Equations</h3>
            <div id=\"moduleMath\"></div>
            <h3 id=\"visualTitle\">Concept Picture And Graph</h3>
            <div class=\"beginner-grid lesson-visual\" id=\"visualBlock\">
              <div>
                <canvas id=\"moduleSketchCanvas\" width=\"520\" height=\"240\"></canvas>
                <div class=\"caption\" id=\"moduleSketchCaption\"></div>
              </div>
              <div>
                <canvas id=\"moduleGraphCanvas\" width=\"520\" height=\"240\"></canvas>
                <div class=\"caption\" id=\"moduleGraphCaption\"></div>
              </div>
            </div>
          </div>
          <h3>Why This Matters On Exam Day</h3>
          <p id=\"moduleExam\"></p>
          <div class=\"roadmap-practice\">
            <strong>Bridge To Practice Mode</strong>
            <p class=\"small\">Use these group IDs in your existing quiz app to reinforce this lesson:</p>
            <div id=\"modulePractice\"></div>
          </div>
          <div class=\"quiz-wrap\">
            <h3 style=\"margin-bottom:6px;\">Quick Knowledge Check</h3>
            <div id=\"quizQuestion\" class=\"quiz-q\"></div>
            <div id=\"quizChoices\"></div>
            <div id=\"quizExplain\" class=\"hint-box hidden\"></div>
            <div class=\"quiz-meta\" id=\"quizMeta\"></div>
            <div style=\"margin-top:8px;display:flex;gap:8px;flex-wrap:wrap;\">
              <button id=\"quizNextBtn\" class=\"secondary hidden\">Next Question</button>
              <button id=\"quizResetBtn\" class=\"secondary\">Restart Quiz</button>
            </div>
          </div>
        </section>

        <section class=\"card\">
          <h2>Visual Intuition Lab</h2>
          <p class=\"small\">Interactive graphs to make abstract RF math concrete.</p>
          <div class=\"grid2\">
            <div class=\"graph-card\">
              <h3>Waveform vs Frequency</h3>
              <canvas id=\"waveCanvas\" width=\"520\" height=\"220\"></canvas>
              <div class=\"control-row\">
                <input id=\"waveFreq\" type=\"range\" min=\"1\" max=\"30\" value=\"7\" />
                <span id=\"waveInfo\" class=\"small\"></span>
              </div>
            </div>
            <div class=\"graph-card\">
              <h3>Resonance And Q</h3>
              <canvas id=\"resCanvas\" width=\"520\" height=\"220\"></canvas>
              <div class=\"control-row\">
                <input id=\"qFactor\" type=\"range\" min=\"5\" max=\"60\" value=\"20\" />
                <span id=\"qInfo\" class=\"small\"></span>
              </div>
            </div>
            <div class=\"graph-card\">
              <h3>Inverse Square Path Loss Intuition</h3>
              <canvas id=\"invCanvas\" width=\"520\" height=\"220\"></canvas>
              <div class=\"control-row\">
                <input id=\"distPick\" type=\"range\" min=\"1\" max=\"40\" value=\"10\" />
                <span id=\"distInfo\" class=\"small\"></span>
              </div>
            </div>
            <div class=\"graph-card\">
              <h3>dB Ladder</h3>
              <canvas id=\"dbCanvas\" width=\"520\" height=\"220\"></canvas>
              <div class=\"small\">Visual reference: power ratio grows exponentially with linear dB increases.</div>
            </div>
          </div>
        </section>

        <section class=\"card\">
          <h2>Math Toolbox</h2>
          <div class=\"calc-grid\">
            <div>
              <h3>Wavelength Calculator</h3>
              <label>Frequency (MHz)
                <input id=\"wlFreq\" type=\"number\" step=\"0.001\" value=\"146.52\" />
              </label>
              <button id=\"wlBtn\">Compute</button>
              <div id=\"wlOut\" class=\"result\"></div>
            </div>
            <div>
              <h3>Ohm's Law + Power</h3>
              <label>Voltage V (volts)
                <input id=\"ohmV\" type=\"number\" step=\"0.01\" />
              </label>
              <label>Current I (amps)
                <input id=\"ohmI\" type=\"number\" step=\"0.001\" />
              </label>
              <label>Resistance R (ohms)
                <input id=\"ohmR\" type=\"number\" step=\"0.01\" />
              </label>
              <button id=\"ohmBtn\">Solve</button>
              <div id=\"ohmOut\" class=\"result\"></div>
            </div>
            <div>
              <h3>dB + FSPL</h3>
              <label>dB value
                <input id=\"dbVal\" type=\"number\" step=\"0.01\" value=\"6\" />
              </label>
              <label>Frequency (MHz)
                <input id=\"fsplF\" type=\"number\" step=\"0.01\" value=\"146.52\" />
              </label>
              <label>Distance (km)
                <input id=\"fsplD\" type=\"number\" step=\"0.01\" value=\"20\" />
              </label>
              <button id=\"dbBtn\">Compute</button>
              <div id=\"dbOut\" class=\"result\"></div>
            </div>
          </div>
        </section>

        <section class=\"card\">
          <h2>Syllabus Explorer (Official Objectives)</h2>
          <div class=\"control-row\">
            <select id=\"elementSelect\">
              <option value=\"2\">Element 2 - Technician</option>
              <option value=\"3\">Element 3 - General</option>
              <option value=\"4\">Element 4 - Amateur Extra</option>
            </select>
            <span id=\"elementMeta\" class=\"small\"></span>
          </div>
          <table>
            <thead>
              <tr>
                <th style=\"width: 72px\">Group</th>
                <th style=\"width: 180px\">Subelement</th>
                <th>Learning Objective</th>
              </tr>
            </thead>
            <tbody id=\"objectiveBody\"></tbody>
          </table>
          <div class=\"foot\">After each objective, reinforce with: <span class=\"cmd\">.venv/bin/python ham_practice.py practice --mode teach --group &lt;GROUP_ID&gt;</span></div>
        </section>

        <section class=\"card\" id=\"sources\">
          <h2>Sources</h2>
          <p class=\"small\">This learning studio references official amateur exam pools/syllabi and standard RF/communications references used for formulas and regulatory context.</p>
          <ul class=\"source-list\">
            <li><a href=\"http://ncvec.org/downloads/2026-2030%20Technician%20Pool%20and%20Syllabus%20Public%20Release%20Feb%2019%202026.pdf\" target=\"_blank\" rel=\"noopener noreferrer\">NCVEC Technician Class Pool and Syllabus (2026-2030)</a></li>
            <li><a href=\"http://ncvec.org/downloads/General%20Class%20Pool%20and%20Syllabus%202023-2027%20Public%20Release%20with%206th%20Errata%20Feb%204%202026.pdf\" target=\"_blank\" rel=\"noopener noreferrer\">NCVEC General Class Pool and Syllabus (2023-2027, 6th Errata)</a></li>
            <li><a href=\"http://ncvec.org/downloads/2024-2028%20Extra%20Class%20Question%20Pool%20and%20Syllabus%20Public%20Release%20with%204th%20Errata%20Feb%204%202026.pdf\" target=\"_blank\" rel=\"noopener noreferrer\">NCVEC Amateur Extra Class Pool and Syllabus (2024-2028, 4th Errata)</a></li>
            <li><a href=\"https://www.ecfr.gov/current/title-47/chapter-I/subchapter-D/part-97\" target=\"_blank\" rel=\"noopener noreferrer\">FCC 47 CFR Part 97 (Amateur Radio Service Rules)</a></li>
            <li><a href=\"https://physics.nist.gov/cgi-bin/cuu/Value?c\" target=\"_blank\" rel=\"noopener noreferrer\">NIST Fundamental Physical Constants: Speed of Light</a></li>
            <li><a href=\"https://www.itu.int/rec/R-REC-P.525/en\" target=\"_blank\" rel=\"noopener noreferrer\">ITU-R P.525: Free-Space Attenuation (FSPL) Reference</a></li>
          </ul>
        </section>
      </main>
    </div>
  </div>

  <script>
    const roadmap = __ROADMAP_JSON__;
    let syllabusCache = null;
    let activeModule = 0;
    let superBeginner = false;
    let superRevealStage = 3;
    let quizIndex = 0;
    let quizScore = 0;
    let quizAnswered = false;

    const moduleList = document.getElementById('moduleList');
    const moduleKicker = document.getElementById('moduleKicker');
    const moduleTitle = document.getElementById('moduleTitle');
    const moduleGoal = document.getElementById('moduleGoal');
    const modulePlain = document.getElementById('modulePlain');
    const moduleSteps = document.getElementById('moduleSteps');
    const moduleMistakes = document.getElementById('moduleMistakes');
    const modulePoints = document.getElementById('modulePoints');
    const moduleMath = document.getElementById('moduleMath');
    const moduleExam = document.getElementById('moduleExam');
    const modulePractice = document.getElementById('modulePractice');
    const moduleSketchCanvas = document.getElementById('moduleSketchCanvas');
    const moduleGraphCanvas = document.getElementById('moduleGraphCanvas');
    const moduleSketchCaption = document.getElementById('moduleSketchCaption');
    const moduleGraphCaption = document.getElementById('moduleGraphCaption');
    const superBeginnerToggle = document.getElementById('superBeginnerToggle');
    const revealDetailBtn = document.getElementById('revealDetailBtn');
    const superHint = document.getElementById('superHint');
    const detailBlock = document.getElementById('detailBlock');
    const keyConceptsTitle = document.getElementById('keyConceptsTitle');
    const equationTitle = document.getElementById('equationTitle');
    const visualTitle = document.getElementById('visualTitle');
    const visualBlock = document.getElementById('visualBlock');
    const quizQuestion = document.getElementById('quizQuestion');
    const quizChoices = document.getElementById('quizChoices');
    const quizExplain = document.getElementById('quizExplain');
    const quizMeta = document.getElementById('quizMeta');
    const quizNextBtn = document.getElementById('quizNextBtn');
    const quizResetBtn = document.getElementById('quizResetBtn');

    function safeNum(v) {
      const n = Number(v);
      return Number.isFinite(n) ? n : null;
    }

    function renderModuleList() {
      moduleList.innerHTML = '';
      roadmap.forEach((m, idx) => {
        const b = document.createElement('button');
        b.className = 'module-btn' + (idx === activeModule ? ' active' : '');
        b.innerHTML = `<div class=\"module-kicker\">Step ${idx + 1}</div><div class=\"module-title\">${m.title}</div>`;
        b.addEventListener('click', () => {
          activeModule = idx;
          renderModuleList();
          renderModule();
        });
        moduleList.appendChild(b);
      });
    }

    function renderModule() {
      const m = roadmap[activeModule];
      moduleKicker.textContent = `Step ${activeModule + 1} of ${roadmap.length}`;
      moduleTitle.textContent = m.title;
      moduleGoal.textContent = m.goal;
      modulePlain.textContent = m.plain_english || m.goal;

      moduleSteps.innerHTML = '';
      (m.step_by_step || []).forEach((s) => {
        const li = document.createElement('li');
        li.textContent = s;
        moduleSteps.appendChild(li);
      });

      moduleMistakes.innerHTML = '';
      (m.common_mistakes || []).forEach((s) => {
        const li = document.createElement('li');
        li.textContent = s;
        moduleMistakes.appendChild(li);
      });

      modulePoints.innerHTML = '';
      m.key_points.forEach((p) => {
        const li = document.createElement('li');
        li.textContent = p;
        modulePoints.appendChild(li);
      });

      moduleMath.innerHTML = '';
      m.math.forEach((eq) => {
        const div = document.createElement('div');
        div.className = 'eq';
        div.textContent = eq;
        moduleMath.appendChild(div);
      });

      moduleExam.textContent = m.why_exam;

      modulePractice.innerHTML = '';
      m.practice_bridge.forEach((g) => {
        const chip = document.createElement('span');
        chip.className = 'chip';
        chip.textContent = g;
        modulePractice.appendChild(chip);

        const cmd = document.createElement('code');
        cmd.className = 'cmd';
        cmd.textContent = `.venv/bin/python ham_practice.py practice --mode teach --group ${g}`;
        modulePractice.appendChild(cmd);
      });

      drawModuleVisuals(m);
      superRevealStage = superBeginner ? 0 : 3;
      applySuperBeginnerVisibility();
      resetQuizForModule(m);
    }

    function applySuperBeginnerVisibility() {
      const showAll = !superBeginner;

      if (showAll) {
        detailBlock.classList.remove('hidden');
        revealDetailBtn.classList.add('hidden');
        superHint.classList.add('hidden');
        keyConceptsTitle.classList.remove('hidden');
        modulePoints.classList.remove('hidden');
        equationTitle.classList.remove('hidden');
        moduleMath.classList.remove('hidden');
        visualTitle.classList.remove('hidden');
        visualBlock.classList.remove('hidden');
        return;
      }

      revealDetailBtn.classList.remove('hidden');
      superHint.classList.remove('hidden');

      if (superRevealStage <= 0) {
        detailBlock.classList.add('hidden');
        superHint.textContent = 'Level 1: start with plain-English overview and steps only. Click "Reveal Next Detail" when ready.';
        keyConceptsTitle.classList.add('hidden');
        modulePoints.classList.add('hidden');
        equationTitle.classList.add('hidden');
        moduleMath.classList.add('hidden');
        visualTitle.classList.add('hidden');
        visualBlock.classList.add('hidden');
        return;
      }

      if (superRevealStage === 1) {
        detailBlock.classList.remove('hidden');
        superHint.textContent = 'Level 2: key concepts are now visible. Equations and visuals remain hidden.';
        keyConceptsTitle.classList.remove('hidden');
        modulePoints.classList.remove('hidden');
        equationTitle.classList.add('hidden');
        moduleMath.classList.add('hidden');
        visualTitle.classList.add('hidden');
        visualBlock.classList.add('hidden');
        return;
      }

      if (superRevealStage === 2) {
        detailBlock.classList.remove('hidden');
        superHint.textContent = 'Level 3: equations are now visible. Visual diagrams are still hidden.';
        keyConceptsTitle.classList.remove('hidden');
        modulePoints.classList.remove('hidden');
        equationTitle.classList.remove('hidden');
        moduleMath.classList.remove('hidden');
        visualTitle.classList.add('hidden');
        visualBlock.classList.add('hidden');
        return;
      }

      detailBlock.classList.remove('hidden');
      superHint.textContent = 'Level 4: full detail shown, including concept picture and graph.';
      keyConceptsTitle.classList.remove('hidden');
      modulePoints.classList.remove('hidden');
      equationTitle.classList.remove('hidden');
      moduleMath.classList.remove('hidden');
      visualTitle.classList.remove('hidden');
      visualBlock.classList.remove('hidden');
    }

    function resetQuizForModule(moduleObj) {
      quizIndex = 0;
      quizScore = 0;
      quizAnswered = false;
      quizExplain.classList.add('hidden');
      quizExplain.textContent = '';
      quizNextBtn.classList.add('hidden');
      renderQuizQuestion(moduleObj);
    }

    function renderQuizQuestion(moduleObj) {
      const checks = moduleObj.knowledge_checks || [];
      if (!checks.length) {
        quizQuestion.textContent = 'No quiz questions for this module yet.';
        quizChoices.innerHTML = '';
        quizMeta.textContent = '';
        quizNextBtn.classList.add('hidden');
        return;
      }

      if (quizIndex >= checks.length) {
        quizQuestion.textContent = `Quiz complete. Final score: ${quizScore}/${checks.length}`;
        quizChoices.innerHTML = '';
        quizMeta.textContent = 'Press Restart Quiz to try again.';
        quizNextBtn.classList.add('hidden');
        quizExplain.classList.remove('hidden');
        quizExplain.textContent = 'Great work. Re-run the module quiz to reinforce memory.';
        return;
      }

      const q = checks[quizIndex];
      quizQuestion.textContent = `Q${quizIndex + 1}. ${q.q}`;
      quizChoices.innerHTML = '';
      quizExplain.classList.add('hidden');
      quizExplain.textContent = '';
      quizNextBtn.classList.add('hidden');
      quizAnswered = false;

      q.choices.forEach((choice, idx) => {
        const btn = document.createElement('button');
        btn.className = 'quiz-choice';
        btn.textContent = choice;
        btn.addEventListener('click', () => submitQuizChoice(moduleObj, idx));
        quizChoices.appendChild(btn);
      });

      quizMeta.textContent = `Question ${quizIndex + 1}/${checks.length} | Score ${quizScore}/${checks.length}`;
    }

    function submitQuizChoice(moduleObj, choiceIdx) {
      if (quizAnswered) return;
      const checks = moduleObj.knowledge_checks || [];
      if (!checks.length || quizIndex >= checks.length) return;

      const q = checks[quizIndex];
      const correctIdx = Number(q.answer);
      const correct = choiceIdx === correctIdx;
      quizAnswered = true;
      if (correct) quizScore += 1;

      const buttons = Array.from(quizChoices.querySelectorAll('.quiz-choice'));
      buttons.forEach((btn, idx) => {
        if (idx === correctIdx) btn.classList.add('correct');
        if (idx === choiceIdx && !correct) btn.classList.add('incorrect');
        btn.disabled = true;
      });

      const correctText = q.choices[correctIdx];
      quizExplain.classList.remove('hidden');
      quizExplain.textContent = `${correct ? 'Correct.' : 'Not quite.'} ${q.explain} Correct answer: ${correctText}`;

      quizMeta.textContent = `Question ${quizIndex + 1}/${checks.length} | Score ${quizScore}/${checks.length}`;
      if (quizIndex < checks.length - 1) {
        quizNextBtn.classList.remove('hidden');
      } else {
        quizIndex = checks.length;
        renderQuizQuestion(moduleObj);
      }
    }

    function clearCanvas(canvas) {
      const ctx = canvas.getContext('2d');
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      return ctx;
    }

    function drawArrow(ctx, x1, y1, x2, y2, color) {
      const angle = Math.atan2(y2 - y1, x2 - x1);
      ctx.strokeStyle = color;
      ctx.fillStyle = color;
      ctx.lineWidth = 2;
      ctx.beginPath();
      ctx.moveTo(x1, y1);
      ctx.lineTo(x2, y2);
      ctx.stroke();
      ctx.beginPath();
      ctx.moveTo(x2, y2);
      ctx.lineTo(x2 - 8 * Math.cos(angle - Math.PI / 6), y2 - 8 * Math.sin(angle - Math.PI / 6));
      ctx.lineTo(x2 - 8 * Math.cos(angle + Math.PI / 6), y2 - 8 * Math.sin(angle + Math.PI / 6));
      ctx.closePath();
      ctx.fill();
    }

    function drawModuleVisuals(m) {
      const sctx = clearCanvas(moduleSketchCanvas);
      const gctx = clearCanvas(moduleGraphCanvas);
      const sw = moduleSketchCanvas.width;
      const sh = moduleSketchCanvas.height;
      const gw = moduleGraphCanvas.width;
      const gh = moduleGraphCanvas.height;

      sctx.font = '13px \"Trebuchet MS\", sans-serif';
      gctx.font = '12px \"Trebuchet MS\", sans-serif';

      if (m.id === 'm1') {
        sctx.fillStyle = '#334155';
        sctx.fillRect(70, 170, 28, 40);
        sctx.fillRect(420, 170, 28, 40);
        sctx.strokeStyle = '#0f766e';
        sctx.lineWidth = 3;
        sctx.beginPath();
        sctx.moveTo(84, 170);
        sctx.lineTo(84, 90);
        sctx.moveTo(434, 170);
        sctx.lineTo(434, 90);
        sctx.stroke();
        for (let i = 0; i < 4; i++) {
          sctx.beginPath();
          sctx.strokeStyle = '#0f766e';
          sctx.arc(255, 130, 30 + i * 16, Math.PI * 1.15, Math.PI * 1.85);
          sctx.stroke();
        }
        sctx.fillStyle = '#334155';
        sctx.fillText('TX antenna', 52, 224);
        sctx.fillText('RX antenna', 400, 224);

        drawAxes(gctx, gw, gh);
        gctx.strokeStyle = '#b45309';
        gctx.lineWidth = 2;
        gctx.beginPath();
        for (let x = 0; x <= gw - 48; x++) {
          const f = 1 + (x / (gw - 48)) * 29;
          const lam = 300 / f;
          const yN = Math.min(1, lam / 300);
          const px = 36 + x;
          const py = (gh - 26) - yN * (gh - 54);
          if (x === 0) gctx.moveTo(px, py);
          else gctx.lineTo(px, py);
        }
        gctx.stroke();
        moduleSketchCaption.textContent = 'Picture: radio energy leaving one antenna and arriving at another.';
        moduleGraphCaption.textContent = 'Graph: as frequency goes up, wavelength goes down.';
        return;
      }

      if (m.id === 'm2') {
        sctx.fillStyle = '#334155';
        sctx.fillRect(40, 90, 90, 50);
        sctx.fillStyle = '#fff';
        sctx.fillText('1 mW ref', 57, 120);
        sctx.fillStyle = '#334155';
        sctx.fillRect(220, 80, 90, 35);
        sctx.fillRect(220, 130, 90, 35);
        sctx.fillStyle = '#fff';
        sctx.fillText('+6 dB', 248, 103);
        sctx.fillText('-3 dB', 248, 153);
        drawArrow(sctx, 130, 115, 220, 97, '#0f766e');
        drawArrow(sctx, 130, 115, 220, 147, '#b45309');
        sctx.fillStyle = '#334155';
        sctx.fillText('dB is a ratio label', 340, 120);

        drawAxes(gctx, gw, gh);
        gctx.strokeStyle = '#0f766e';
        gctx.lineWidth = 2;
        gctx.beginPath();
        for (let x = 0; x <= gw - 48; x++) {
          const db = -20 + (x / (gw - 48)) * 40;
          const r = Math.pow(10, db / 10);
          const yN = Math.log10(r + 1) / Math.log10(101);
          const px = 36 + x;
          const py = (gh - 26) - yN * (gh - 54);
          if (x === 0) gctx.moveTo(px, py);
          else gctx.lineTo(px, py);
        }
        gctx.stroke();
        moduleSketchCaption.textContent = 'Picture: one reference power can map to many ratio changes in dB.';
        moduleGraphCaption.textContent = 'Graph: power ratio grows exponentially as dB increases linearly.';
        return;
      }

      if (m.id === 'm3') {
        sctx.strokeStyle = '#334155';
        sctx.lineWidth = 3;
        sctx.strokeRect(90, 70, 330, 130);
        sctx.fillStyle = '#0f766e';
        sctx.fillRect(90, 114, 42, 42);
        sctx.fillStyle = '#fff';
        sctx.fillText('V', 106, 141);
        sctx.fillStyle = '#b45309';
        sctx.fillRect(248, 70, 52, 34);
        sctx.fillStyle = '#fff';
        sctx.fillText('R', 268, 92);
        drawArrow(sctx, 138, 135, 238, 135, '#0f766e');
        sctx.fillStyle = '#334155';
        sctx.fillText('I', 186, 125);
        sctx.fillText('Simple loop: source, load, current flow', 130, 224);

        drawAxes(gctx, gw, gh);
        gctx.strokeStyle = '#0f766e';
        gctx.lineWidth = 2;
        gctx.beginPath();
        for (let x = 0; x <= gw - 48; x++) {
          const v = (x / (gw - 48)) * 12;
          const i = v / 6;
          const yN = Math.min(1, i / 2);
          const px = 36 + x;
          const py = (gh - 26) - yN * (gh - 54);
          if (x === 0) gctx.moveTo(px, py);
          else gctx.lineTo(px, py);
        }
        gctx.stroke();
        moduleSketchCaption.textContent = 'Picture: battery pushes current through resistance.';
        moduleGraphCaption.textContent = 'Graph: for fixed resistance, current rises linearly with voltage.';
        return;
      }

      if (m.id === 'm4') {
        sctx.strokeStyle = '#334155';
        sctx.lineWidth = 3;
        sctx.beginPath();
        sctx.moveTo(70, 120);
        sctx.lineTo(150, 120);
        sctx.lineTo(180, 80);
        sctx.lineTo(210, 160);
        sctx.lineTo(240, 80);
        sctx.lineTo(270, 160);
        sctx.lineTo(300, 120);
        sctx.lineTo(360, 120);
        sctx.stroke();
        sctx.beginPath();
        sctx.moveTo(300, 120);
        sctx.lineTo(300, 95);
        sctx.lineTo(340, 95);
        sctx.lineTo(340, 145);
        sctx.lineTo(300, 145);
        sctx.lineTo(300, 120);
        sctx.stroke();
        sctx.fillStyle = '#334155';
        sctx.fillText('L', 225, 74);
        sctx.fillText('C', 345, 122);
        sctx.fillText('LC tank resonates at one center frequency', 115, 224);

        drawAxes(gctx, gw, gh);
        gctx.strokeStyle = '#b45309';
        gctx.lineWidth = 2;
        gctx.beginPath();
        const f0 = 0.5;
        const bw = 0.06;
        for (let x = 0; x <= gw - 48; x++) {
          const fn = x / (gw - 48);
          const den = Math.sqrt(1 + Math.pow((fn - f0) / bw, 2));
          const amp = 1 / den;
          const px = 36 + x;
          const py = (gh - 26) - amp * (gh - 54) * 0.9;
          if (x === 0) gctx.moveTo(px, py);
          else gctx.lineTo(px, py);
        }
        gctx.stroke();
        moduleSketchCaption.textContent = 'Picture: inductor + capacitor network stores and exchanges energy.';
        moduleGraphCaption.textContent = 'Graph: resonance peak around center frequency.';
        return;
      }

      if (m.id === 'm5') {
        sctx.fillStyle = '#334155';
        sctx.fillText('AM/SSB/FM occupy different widths', 150, 26);
        sctx.fillStyle = '#0f766e';
        sctx.fillRect(90, 110, 24, 70);
        sctx.fillStyle = '#b45309';
        sctx.fillRect(180, 80, 50, 100);
        sctx.fillStyle = '#334155';
        sctx.fillRect(300, 50, 110, 130);
        sctx.fillStyle = '#334155';
        sctx.fillText('CW', 92, 200);
        sctx.fillText('SSB', 188, 200);
        sctx.fillText('FM', 345, 200);

        drawAxes(gctx, gw, gh);
        const bars = [
          {name: 'CW', bw: 1, color: '#0f766e'},
          {name: 'SSB', bw: 3, color: '#b45309'},
          {name: 'FM', bw: 10, color: '#334155'},
        ];
        bars.forEach((b, i) => {
          const x = 90 + i * 120;
          const hBar = b.bw * 14;
          gctx.fillStyle = b.color;
          gctx.fillRect(x, (gh - 26) - hBar, 70, hBar);
          gctx.fillStyle = '#334155';
          gctx.fillText(b.name, x + 18, gh - 8);
        });
        moduleSketchCaption.textContent = 'Picture: each mode uses a different slice of spectrum.';
        moduleGraphCaption.textContent = 'Graph: approximate relative bandwidth by mode.';
        return;
      }

      if (m.id === 'm6') {
        sctx.strokeStyle = '#334155';
        sctx.lineWidth = 4;
        sctx.beginPath();
        sctx.moveTo(60, 120);
        sctx.lineTo(460, 120);
        sctx.stroke();
        sctx.fillStyle = '#334155';
        sctx.fillRect(460, 92, 26, 56);
        drawArrow(sctx, 90, 108, 430, 108, '#0f766e');
        drawArrow(sctx, 430, 132, 160, 132, '#b91c1c');
        sctx.fillStyle = '#0f766e';
        sctx.fillText('Forward wave', 150, 96);
        sctx.fillStyle = '#b91c1c';
        sctx.fillText('Reflected wave', 220, 152);

        drawAxes(gctx, gw, gh);
        gctx.strokeStyle = '#0f766e';
        gctx.lineWidth = 2;
        gctx.beginPath();
        for (let x = 0; x <= gw - 48; x++) {
          const gamma = x / (gw - 48) * 0.95;
          const swr = (1 + gamma) / (1 - gamma);
          const yN = Math.min(1, swr / 20);
          const px = 36 + x;
          const py = (gh - 26) - yN * (gh - 54);
          if (x === 0) gctx.moveTo(px, py);
          else gctx.lineTo(px, py);
        }
        gctx.stroke();
        moduleSketchCaption.textContent = 'Picture: mismatch causes some energy to bounce back on the feed line.';
        moduleGraphCaption.textContent = 'Graph: SWR rises quickly as reflection coefficient approaches 1.';
        return;
      }

      if (m.id === 'm7') {
        sctx.strokeStyle = '#334155';
        sctx.lineWidth = 2;
        sctx.beginPath();
        sctx.moveTo(110, 190);
        sctx.lineTo(110, 80);
        sctx.stroke();
        sctx.strokeStyle = '#0f766e';
        sctx.beginPath();
        sctx.arc(110, 135, 55, 0, Math.PI * 2);
        sctx.stroke();
        sctx.strokeStyle = '#b45309';
        sctx.beginPath();
        sctx.ellipse(350, 135, 95, 35, 0, 0, Math.PI * 2);
        sctx.stroke();
        sctx.fillStyle = '#334155';
        sctx.fillText('Omni-like', 78, 216);
        sctx.fillText('Directional beam', 300, 216);

        drawAxes(gctx, gw, gh);
        gctx.strokeStyle = '#0f766e';
        gctx.lineWidth = 2;
        gctx.beginPath();
        for (let x = 0; x <= gw - 48; x++) {
          const d = 1 + (x / (gw - 48)) * 50;
          const loss = 20 * Math.log10(d);
          const yN = Math.min(1, loss / 40);
          const px = 36 + x;
          const py = (gh - 26) - yN * (gh - 54);
          if (x === 0) gctx.moveTo(px, py);
          else gctx.lineTo(px, py);
        }
        gctx.stroke();
        moduleSketchCaption.textContent = 'Picture: omni and directional patterns place energy differently.';
        moduleGraphCaption.textContent = 'Graph: path loss generally increases with distance.';
        return;
      }

      if (m.id === 'm8') {
        sctx.strokeStyle = '#334155';
        sctx.lineWidth = 2;
        sctx.beginPath();
        sctx.arc(260, 230, 220, Math.PI, Math.PI * 2);
        sctx.stroke();
        sctx.fillStyle = '#e5eef6';
        sctx.fillRect(30, 65, 460, 25);
        sctx.fillStyle = '#334155';
        sctx.fillText('Ionosphere', 225, 82);
        drawArrow(sctx, 90, 190, 250, 88, '#0f766e');
        drawArrow(sctx, 250, 88, 420, 190, '#0f766e');
        sctx.fillText('Skywave path', 215, 160);

        drawAxes(gctx, gw, gh);
        gctx.strokeStyle = '#b45309';
        gctx.lineWidth = 2;
        gctx.beginPath();
        for (let x = 0; x <= gw - 48; x++) {
          const t = x / (gw - 48);
          const y = 0.45 + 0.3 * Math.sin(t * Math.PI * 2 - 0.8);
          const px = 36 + x;
          const py = (gh - 26) - y * (gh - 54);
          if (x === 0) gctx.moveTo(px, py);
          else gctx.lineTo(px, py);
        }
        gctx.stroke();
        moduleSketchCaption.textContent = 'Picture: HF can refract from ionosphere and return to Earth.';
        moduleGraphCaption.textContent = 'Graph: propagation quality can vary over time.';
        return;
      }

      if (m.id === 'm9') {
        sctx.fillStyle = '#334155';
        sctx.fillRect(40, 100, 90, 46);
        sctx.fillRect(180, 100, 90, 46);
        sctx.fillRect(320, 100, 90, 46);
        sctx.fillStyle = '#fff';
        sctx.fillText('TX', 74, 128);
        sctx.fillText('Path', 208, 128);
        sctx.fillText('RX', 350, 128);
        drawArrow(sctx, 130, 123, 180, 123, '#0f766e');
        drawArrow(sctx, 270, 123, 320, 123, '#0f766e');
        sctx.fillStyle = '#334155';
        sctx.fillText('Add gains, subtract losses', 155, 186);

        drawAxes(gctx, gw, gh);
        gctx.strokeStyle = '#0f766e';
        gctx.lineWidth = 2;
        gctx.beginPath();
        for (let x = 0; x <= gw - 48; x++) {
          const d = 1 + (x / (gw - 48)) * 60;
          const pr = -40 - 20 * Math.log10(d);
          const yN = (pr + 90) / 50;
          const px = 36 + x;
          const py = (gh - 26) - Math.max(0, Math.min(1, yN)) * (gh - 54);
          if (x === 0) gctx.moveTo(px, py);
          else gctx.lineTo(px, py);
        }
        gctx.stroke();
        moduleSketchCaption.textContent = 'Picture: link budget is a chain from transmitter to receiver.';
        moduleGraphCaption.textContent = 'Graph: received level usually drops as distance increases.';
        return;
      }

      if (m.id === 'm10') {
        sctx.fillStyle = '#334155';
        sctx.fillRect(250, 150, 20, 60);
        sctx.strokeStyle = '#0f766e';
        sctx.lineWidth = 2;
        sctx.beginPath();
        sctx.arc(260, 145, 28, 0, Math.PI * 2);
        sctx.arc(260, 145, 58, 0, Math.PI * 2);
        sctx.arc(260, 145, 90, 0, Math.PI * 2);
        sctx.stroke();
        sctx.fillStyle = '#334155';
        sctx.fillText('Keep people outside higher-field zones', 150, 224);

        drawAxes(gctx, gw, gh);
        gctx.strokeStyle = '#b91c1c';
        gctx.lineWidth = 2;
        gctx.beginPath();
        for (let x = 1; x <= gw - 48; x++) {
          const d = 1 + (x / (gw - 48)) * 40;
          const e = 1 / (d * d);
          const px = 36 + x;
          const py = (gh - 26) - e * (gh - 54) * 45;
          if (x === 1) gctx.moveTo(px, py);
          else gctx.lineTo(px, py);
        }
        gctx.stroke();
        moduleSketchCaption.textContent = 'Picture: define safe operating distance around antennas.';
        moduleGraphCaption.textContent = 'Graph: RF field strength and power density drop quickly with distance.';
        return;
      }

      moduleSketchCaption.textContent = '';
      moduleGraphCaption.textContent = '';
    }

    function drawAxes(ctx, w, h) {
      ctx.strokeStyle = '#9aa6a8';
      ctx.lineWidth = 1;
      ctx.beginPath();
      ctx.moveTo(36, 12);
      ctx.lineTo(36, h - 26);
      ctx.lineTo(w - 12, h - 26);
      ctx.stroke();
    }

    function drawWave() {
      const canvas = document.getElementById('waveCanvas');
      const ctx = canvas.getContext('2d');
      const w = canvas.width;
      const h = canvas.height;
      const fMHz = Number(document.getElementById('waveFreq').value);
      document.getElementById('waveInfo').textContent = `${fMHz.toFixed(1)} MHz | wavelength ~ ${(300 / fMHz).toFixed(2)} m`;

      ctx.clearRect(0, 0, w, h);
      drawAxes(ctx, w, h);

      ctx.strokeStyle = '#0f766e';
      ctx.lineWidth = 2;
      ctx.beginPath();
      const cycles = Math.max(1, Math.min(10, Math.round(fMHz / 3)));
      for (let x = 0; x <= w - 48; x++) {
        const t = x / (w - 48);
        const y = Math.sin(t * Math.PI * 2 * cycles);
        const px = 36 + x;
        const py = (h - 26) - ((h - 54) / 2 + y * ((h - 54) / 2) * 0.85);
        if (x === 0) ctx.moveTo(px, py);
        else ctx.lineTo(px, py);
      }
      ctx.stroke();
    }

    function drawResonance() {
      const canvas = document.getElementById('resCanvas');
      const ctx = canvas.getContext('2d');
      const w = canvas.width;
      const h = canvas.height;
      const q = Number(document.getElementById('qFactor').value);
      document.getElementById('qInfo').textContent = `Q = ${q}`;

      ctx.clearRect(0, 0, w, h);
      drawAxes(ctx, w, h);

      const f0 = 0.5;
      const bw = f0 / q;

      ctx.strokeStyle = '#b45309';
      ctx.lineWidth = 2;
      ctx.beginPath();
      for (let x = 0; x <= w - 48; x++) {
        const fn = x / (w - 48);
        const den = Math.sqrt(1 + Math.pow((fn - f0) / Math.max(0.001, bw), 2));
        const amp = 1 / den;
        const px = 36 + x;
        const py = (h - 26) - amp * (h - 54) * 0.9;
        if (x === 0) ctx.moveTo(px, py);
        else ctx.lineTo(px, py);
      }
      ctx.stroke();

      const xPeak = 36 + f0 * (w - 48);
      ctx.strokeStyle = '#6b7280';
      ctx.setLineDash([4, 4]);
      ctx.beginPath();
      ctx.moveTo(xPeak, 14);
      ctx.lineTo(xPeak, h - 26);
      ctx.stroke();
      ctx.setLineDash([]);
    }

    function drawInverseSquare() {
      const canvas = document.getElementById('invCanvas');
      const ctx = canvas.getContext('2d');
      const w = canvas.width;
      const h = canvas.height;
      const dPick = Number(document.getElementById('distPick').value);

      ctx.clearRect(0, 0, w, h);
      drawAxes(ctx, w, h);

      ctx.strokeStyle = '#0f766e';
      ctx.lineWidth = 2;
      ctx.beginPath();
      for (let x = 1; x <= w - 48; x++) {
        const d = 1 + (x / (w - 48)) * 40;
        const p = 1 / (d * d);
        const px = 36 + x;
        const py = (h - 26) - p * (h - 54) * 45;
        if (x === 1) ctx.moveTo(px, py);
        else ctx.lineTo(px, py);
      }
      ctx.stroke();

      const xPick = 36 + ((dPick - 1) / 40) * (w - 48);
      const pPick = 1 / (dPick * dPick);
      const yPick = (h - 26) - pPick * (h - 54) * 45;

      ctx.fillStyle = '#b91c1c';
      ctx.beginPath();
      ctx.arc(xPick, yPick, 4, 0, Math.PI * 2);
      ctx.fill();

      document.getElementById('distInfo').textContent = `d = ${dPick} m | relative density = ${(pPick * 100).toFixed(3)}% of 1 m`;
    }

    function drawDbLadder() {
      const canvas = document.getElementById('dbCanvas');
      const ctx = canvas.getContext('2d');
      const w = canvas.width;
      const h = canvas.height;
      ctx.clearRect(0, 0, w, h);

      const dbVals = [-20, -10, -6, -3, 0, 3, 6, 10, 20];
      const ratios = dbVals.map((d) => Math.pow(10, d / 10));
      const maxR = Math.max(...ratios);

      const left = 42;
      const baseY = h - 28;
      const plotW = w - left - 14;
      const barW = plotW / dbVals.length - 6;

      ctx.strokeStyle = '#9aa6a8';
      ctx.beginPath();
      ctx.moveTo(left, 12);
      ctx.lineTo(left, baseY);
      ctx.lineTo(w - 12, baseY);
      ctx.stroke();

      dbVals.forEach((d, i) => {
        const r = ratios[i];
        const bh = (Math.log10(r + 1) / Math.log10(maxR + 1)) * (h - 54);
        const x = left + i * (barW + 6) + 4;
        const y = baseY - bh;
        ctx.fillStyle = d >= 0 ? '#0f766e' : '#b45309';
        ctx.fillRect(x, y, barW, bh);
        ctx.fillStyle = '#334155';
        ctx.font = '11px "Trebuchet MS", sans-serif';
        ctx.fillText(`${d}`, x + 1, baseY + 12);
      });
    }

    function setupGraphs() {
      drawWave();
      drawResonance();
      drawInverseSquare();
      drawDbLadder();

      document.getElementById('waveFreq').addEventListener('input', drawWave);
      document.getElementById('qFactor').addEventListener('input', drawResonance);
      document.getElementById('distPick').addEventListener('input', drawInverseSquare);
    }

    function runWavelengthCalc() {
      const f = safeNum(document.getElementById('wlFreq').value);
      const out = document.getElementById('wlOut');
      if (!f || f <= 0) {
        out.textContent = 'Enter a positive frequency in MHz.';
        return;
      }
      const lambdaM = 300 / f;
      out.innerHTML = `lambda ~ <strong>${lambdaM.toFixed(3)} m</strong><br/>Half-wave ~ ${(lambdaM / 2).toFixed(3)} m | Quarter-wave ~ ${(lambdaM / 4).toFixed(3)} m`;
    }

    function runOhmCalc() {
      const v = safeNum(document.getElementById('ohmV').value);
      const i = safeNum(document.getElementById('ohmI').value);
      const r = safeNum(document.getElementById('ohmR').value);
      const out = document.getElementById('ohmOut');

      const known = [v, i, r].filter((x) => x !== null).length;
      if (known < 2) {
        out.textContent = 'Enter any two of V, I, and R.';
        return;
      }

      let V = v;
      let I = i;
      let R = r;

      if (V !== null && I !== null) R = V / I;
      else if (V !== null && R !== null) I = V / R;
      else if (I !== null && R !== null) V = I * R;

      if (V === null || I === null || R === null || !Number.isFinite(V) || !Number.isFinite(I) || !Number.isFinite(R)) {
        out.textContent = 'Unable to solve with the provided values.';
        return;
      }

      const P = V * I;
      out.innerHTML = `V=${V.toFixed(3)} V | I=${I.toFixed(3)} A | R=${R.toFixed(3)} ohm<br/>P=${P.toFixed(3)} W`;
    }

    function runDbCalc() {
      const dB = safeNum(document.getElementById('dbVal').value);
      const f = safeNum(document.getElementById('fsplF').value);
      const d = safeNum(document.getElementById('fsplD').value);
      const out = document.getElementById('dbOut');

      if (dB === null || f === null || d === null || f <= 0 || d <= 0) {
        out.textContent = 'Enter valid dB, frequency (MHz), and distance (km).';
        return;
      }

      const pRatio = Math.pow(10, dB / 10);
      const fspl = 32.44 + 20 * Math.log10(f) + 20 * Math.log10(d);
      out.innerHTML = `Power ratio for ${dB.toFixed(2)} dB = <strong>${pRatio.toFixed(4)}x</strong><br/>FSPL(${f.toFixed(2)} MHz, ${d.toFixed(2)} km) = <strong>${fspl.toFixed(2)} dB</strong>`;
    }

    async function loadSyllabus() {
      const res = await fetch('/api/syllabus');
      if (!res.ok) {
        throw new Error('Unable to load syllabus metadata');
      }
      syllabusCache = await res.json();
      renderObjectives();
    }

    function renderObjectives() {
      if (!syllabusCache) return;
      const element = document.getElementById('elementSelect').value;
      const obj = syllabusCache[element];
      const body = document.getElementById('objectiveBody');
      const meta = document.getElementById('elementMeta');

      meta.textContent = `${obj.license_class} | Pool cycle ${obj.pool_cycle} | ${obj.question_count} pool questions`;

      const groups = obj.group_objectives || {};
      const subs = obj.subelements || {};
      const rows = [];
      Object.keys(subs).sort().forEach((subId) => {
        const sub = subs[subId];
        const title = sub.title || '';
        const subGroups = sub.groups || {};
        Object.keys(subGroups).sort().forEach((g) => {
          rows.push({ group: g, sub: `${subId} - ${title}`, objective: subGroups[g] });
        });
      });

      if (!rows.length && Object.keys(groups).length) {
        Object.keys(groups).sort().forEach((g) => rows.push({ group: g, sub: g.slice(0, 2), objective: groups[g] }));
      }

      body.innerHTML = '';
      rows.forEach((row) => {
        const tr = document.createElement('tr');
        tr.innerHTML = `<td><strong>${row.group}</strong></td><td>${row.sub}</td><td>${row.objective}</td>`;
        body.appendChild(tr);
      });
    }

    function boot() {
      renderModuleList();
      renderModule();
      setupGraphs();
      runWavelengthCalc();
      runDbCalc();

      document.getElementById('wlBtn').addEventListener('click', runWavelengthCalc);
      document.getElementById('ohmBtn').addEventListener('click', runOhmCalc);
      document.getElementById('dbBtn').addEventListener('click', runDbCalc);
      document.getElementById('elementSelect').addEventListener('change', renderObjectives);
      superBeginnerToggle.addEventListener('change', () => {
        superBeginner = superBeginnerToggle.checked;
        superRevealStage = superBeginner ? 0 : 3;
        applySuperBeginnerVisibility();
      });
      revealDetailBtn.addEventListener('click', () => {
        if (!superBeginner) return;
        superRevealStage = Math.min(3, superRevealStage + 1);
        applySuperBeginnerVisibility();
      });
      quizNextBtn.addEventListener('click', () => {
        if (!quizAnswered) return;
        quizIndex += 1;
        renderQuizQuestion(roadmap[activeModule]);
      });
      quizResetBtn.addEventListener('click', () => {
        resetQuizForModule(roadmap[activeModule]);
      });

      loadSyllabus().catch((err) => {
        document.getElementById('objectiveBody').innerHTML = `<tr><td colspan=\"3\">${err.message}</td></tr>`;
      });
    }

    boot();
  </script>
</body>
</html>
"""


class LearningHandler(BaseHTTPRequestHandler):
    def _send_json(self, status: int, payload: Dict[str, Any]) -> None:
        data = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _send_html(self, status: int, body: str) -> None:
        data = body.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, fmt: str, *args: object) -> None:
        return

    def do_GET(self) -> None:
        parsed = urllib.parse.urlsplit(self.path)

        if parsed.path == "/":
            html = WEB_TEMPLATE.replace("__ROADMAP_JSON__", json.dumps(get_learning_roadmap()))
            self._send_html(200, html)
            return

        if parsed.path == "/api/syllabus":
            try:
                snapshot = load_syllabus_snapshot()
            except FileNotFoundError as exc:
                self._send_json(400, {"error": str(exc)})
                return
            self._send_json(200, snapshot)
            return

        self._send_json(404, {"error": "Not found"})


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Ham radio learning web studio")
    sub = parser.add_subparsers(dest="command", required=True)

    web_cmd = sub.add_parser("web", help="Run the learning website")
    web_cmd.add_argument("--host", default="127.0.0.1", help="Host bind address")
    web_cmd.add_argument("--port", type=int, default=8788, help="HTTP port")

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "web":
        for element in sorted(POOL_CONFIG.keys()):
            load_pool_payload(element)

        server = ThreadingHTTPServer((args.host, args.port), LearningHandler)
        print(f"Learning studio running at http://{args.host}:{args.port}")
        print("Press Ctrl+C to stop")
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            print("\nStopping learning studio")
            server.server_close()
        return 0

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
