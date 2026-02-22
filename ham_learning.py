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
    @media (max-width: 980px) {
      .layout { grid-template-columns: 1fr; }
      .sticky { position: static; max-height: none; }
      .grid2 { grid-template-columns: 1fr; }
      .calc-grid { grid-template-columns: 1fr; }
    }
  </style>
</head>
<body>
  <div class=\"wrap\">
    <h1>Ham Radio Learning Studio</h1>
    <p class=\"sub\">A separate learning interface focused on physics, math, and radio-system intuition. Use this before or alongside the question practice app.</p>

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
          <h3>Key Concepts</h3>
          <ul id=\"modulePoints\"></ul>
          <h3>Core Equations</h3>
          <div id=\"moduleMath\"></div>
          <h3>Why This Matters On Exam Day</h3>
          <p id=\"moduleExam\"></p>
          <div class=\"roadmap-practice\">
            <strong>Bridge To Practice Mode</strong>
            <p class=\"small\">Use these group IDs in your existing quiz app to reinforce this lesson:</p>
            <div id=\"modulePractice\"></div>
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
      </main>
    </div>
  </div>

  <script>
    const roadmap = __ROADMAP_JSON__;
    let syllabusCache = null;
    let activeModule = 0;

    const moduleList = document.getElementById('moduleList');
    const moduleKicker = document.getElementById('moduleKicker');
    const moduleTitle = document.getElementById('moduleTitle');
    const moduleGoal = document.getElementById('moduleGoal');
    const modulePoints = document.getElementById('modulePoints');
    const moduleMath = document.getElementById('moduleMath');
    const moduleExam = document.getElementById('moduleExam');
    const modulePractice = document.getElementById('modulePractice');

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
            html = WEB_TEMPLATE.replace("__ROADMAP_JSON__", json.dumps(LEARNING_ROADMAP))
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
