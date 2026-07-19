#!/usr/bin/env python3
"""Parse hey output files and generate a load-test chart for CentralImmo."""

import json
import re
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).parent
IMAGES = ROOT.parent / "ressources" / "images"

ENDPOINTS = {
    "health": ("GET /health", 100, 10),
    "neighborhoods": ("GET /neighborhoods", 200, 20),
    "annonces": ("GET /annonces?limit=100", 100, 10),
    "search": ("GET /search?q=studio Bonamoussadi", 20, 2),
}


def parse_hey(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    data = {}

    # Summary block
    m_total = re.search(r"Total:\s+([0-9.]+)\s+secs", text)
    m_slow = re.search(r"Slowest:\s+([0-9.]+)\s+secs", text)
    m_fast = re.search(r"Fastest:\s+([0-9.]+)\s+secs", text)
    m_avg = re.search(r"Average:\s+([0-9.]+)\s+secs", text)
    m_rps = re.search(r"Requests/sec:\s+([0-9.]+)", text)

    if m_total:
        data["total_seconds"] = float(m_total.group(1))
    if m_slow:
        data["slowest_ms"] = float(m_slow.group(1)) * 1000
    if m_fast:
        data["fastest_ms"] = float(m_fast.group(1)) * 1000
    if m_avg:
        data["avg_ms"] = float(m_avg.group(1)) * 1000
    if m_rps:
        data["rps"] = float(m_rps.group(1))

    # Percentiles
    for p in [10, 25, 50, 75, 90, 95, 99]:
        pat = rf"{p}%\% in\s+([0-9.]+)\s+secs"
        m = re.search(pat, text)
        if m:
            data[f"p{p}_ms"] = float(m.group(1)) * 1000

    # Status codes
    m_status = re.search(r"\[(\d+)\]\s+(\d+) responses", text)
    if m_status:
        data["status_code"] = int(m_status.group(1))
        data["responses"] = int(m_status.group(2))

    return data


def main():
    results = {}
    for key, (label, n, c) in ENDPOINTS.items():
        path = ROOT / f"{key}.txt"
        parsed = parse_hey(path)
        parsed["label"] = label
        parsed["n"] = n
        parsed["c"] = c
        results[key] = parsed

    json_path = ROOT / "hey_results.json"
    json_path.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")

    # Chart: latency percentiles per endpoint
    endpoints_order = ["health", "neighborhoods", "annonces", "search"]
    labels = [results[k]["label"] for k in endpoints_order]
    percentiles = [50, 75, 90, 95, 99]

    x = np.arange(len(endpoints_order))
    width = 0.15
    palette = ["#00695C", "#1976D2", "#D4AF37", "#C62828", "#5D4037"]

    fig, ax = plt.subplots(figsize=(10, 6))
    for i, p in enumerate(percentiles):
        vals = [results[k].get(f"p{p}_ms", 0) for k in endpoints_order]
        ax.bar(x + (i - 2) * width, vals, width, label=f"P{p}", color=palette[i])

    ax.set_ylabel("Latence (ms)")
    ax.set_title("Tests de charge avec hey — percentiles de latence par endpoint")
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=15, ha="right")
    ax.legend(title="Percentile")
    ax.set_yscale("log")
    ax.grid(axis="y", linestyle="--", alpha=0.4)
    fig.tight_layout()

    chart_path = IMAGES / "chart_hey_load_test.png"
    fig.savefig(chart_path, dpi=150)
    print(f"Saved chart to {chart_path}")

    # Chart: requests/sec
    fig2, ax2 = plt.subplots(figsize=(8, 5))
    rps_vals = [results[k].get("rps", 0) for k in endpoints_order]
    bars = ax2.bar(labels, rps_vals, color=["#00695C", "#1976D2", "#D4AF37", "#C62828"])
    ax2.set_ylabel("Requêtes / seconde")
    ax2.set_title("Débit mesuré par endpoint (hey)")
    ax2.set_xticklabels(labels, rotation=15, ha="right")
    ax2.grid(axis="y", linestyle="--", alpha=0.4)
    for bar in bars:
        height = bar.get_height()
        ax2.annotate(f"{height:.1f}", xy=(bar.get_x() + bar.get_width() / 2, height),
                     xytext=(0, 3), textcoords="offset points", ha="center", va="bottom", fontsize=9)
    fig2.tight_layout()
    chart_path2 = IMAGES / "chart_hey_throughput.png"
    fig2.savefig(chart_path2, dpi=150)
    print(f"Saved chart to {chart_path2}")


if __name__ == "__main__":
    main()
