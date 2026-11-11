"""Draw the report figures as SVG from the repository's own result files (no plotting library)."""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent / "figures"
INK, GREY, BLUE, ORANGE, LIGHT = "#1f2937", "#9ca3af", "#2563eb", "#d97706", "#e5e7eb"
FONT = "font-family='Helvetica, Arial, sans-serif'"


def svg(width, height, body):
    return (f"<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 {width} {height}' width='100%' {FONT} "
            f"font-size='12' fill='{INK}'>{body}</svg>")


def text(x, y, s, anchor="start", size=12, weight="normal", fill=INK):
    return f"<text x='{x}' y='{y}' text-anchor='{anchor}' font-size='{size}' font-weight='{weight}' fill='{fill}'>{s}</text>"


def volume_vs_effort():
    rows = [("Security incident", 5.2, 9.7), ("Compliance request", 5.2, 8.4), ("Feature request", 4.0, 6.9),
            ("Data residency", 5.8, 7.1), ("Deployment failure", 5.4, 6.2), ("Data export", 5.8, 4.0),
            ("SSO configuration", 5.2, 2.4), ("Onboarding", 4.4, 2.1), ("Rate limit", 2.6, 0.8)]
    w, h, left, scale = 720, 40 + 34 * len(rows), 170, 40
    b = [text(left, 20, "Share of tickets", fill=BLUE, weight="bold"), text(left + 150, 20, "Share of resolution minutes", fill=ORANGE, weight="bold")]
    for i, (name, vol, eff) in enumerate(rows):
        y = 40 + i * 34
        b.append(text(left - 8, y + 18, name, anchor="end"))
        b.append(f"<rect x='{left}' y='{y}' width='{vol * scale}' height='12' fill='{BLUE}'/>")
        b.append(text(left + vol * scale + 5, y + 10, f"{vol}%", size=11))
        b.append(f"<rect x='{left}' y='{y + 14}' width='{eff * scale}' height='12' fill='{ORANGE}'/>")
        b.append(text(left + eff * scale + 5, y + 24, f"{eff}%", size=11))
    return svg(w, h, "".join(b))


def architecture():
    def box(x, y, w, h, title, sub="", fill="#eff6ff", stroke=BLUE):
        s = f"<rect x='{x}' y='{y}' width='{w}' height='{h}' rx='6' fill='{fill}' stroke='{stroke}'/>"
        s += text(x + w / 2, y + 20, title, anchor="middle", weight="bold")
        for i, line in enumerate(sub.split("|")):
            if line:
                s += text(x + w / 2, y + 37 + i * 14, line, anchor="middle", size=11)
        return s

    def arrow(x1, y1, x2, y2):
        return (f"<line x1='{x1}' y1='{y1}' x2='{x2}' y2='{y2}' stroke='{INK}' stroke-width='1.5' marker-end='url(#a)'/>")

    b = ["<defs><marker id='a' markerWidth='8' markerHeight='8' refX='7' refY='4' orient='auto'><path d='M0,0 L8,4 L0,8 z' fill='#1f2937'/></marker></defs>"]
    b.append(box(10, 20, 110, 60, "Ticket", "email, chat,|docs, forum"))
    b.append(box(150, 20, 130, 60, "Normalise", "one shared format|labels kept apart"))
    b.append(box(310, 20, 140, 60, "Classify", "intent + urgency|(language model)"))
    b.append(box(480, 20, 130, 60, "Route", "router-v4 rules", fill="#fef3c7", stroke=ORANGE))
    b.append(arrow(120, 50, 150, 50)); b.append(arrow(280, 50, 310, 50)); b.append(arrow(450, 50, 480, 50))
    b.append(box(480, 130, 130, 60, "Escalate", "specialist; summary|prepared", fill="#fee2e2", stroke="#dc2626"))
    b.append(arrow(545, 80, 545, 130))
    b.append(box(300, 130, 150, 60, "Retrieve", "29 articles, passages|vector index"))
    b.append(arrow(480, 62, 450, 150))
    b.append(box(300, 230, 150, 60, "Draft with citations", "language model;|sources only"))
    b.append(arrow(375, 190, 375, 230))
    b.append(box(120, 230, 150, 60, "Guardrails", "ticket and draft checks|block or pass", fill="#fef3c7", stroke=ORANGE))
    b.append(arrow(300, 260, 270, 260))
    b.append(box(120, 130, 150, 60, "Agent review", "read, edit, approve,|reject or escalate", fill="#dcfce7", stroke="#16a34a"))
    b.append(arrow(195, 230, 195, 190))
    b.append(box(480, 230, 130, 60, "Decision log", "every step recorded|(SQLite)", fill=LIGHT, stroke=GREY))
    b.append(arrow(450, 260, 480, 260))
    b.append(text(10, 320, "Nothing is sent to a customer: the system ends at the agent's review screen.", size=12))
    return svg(640, 335, "".join(b))


def accuracy():
    rows = [("Development, first prompt (PR-03-v2), 340 tickets", 85.6, 77.2, 92.8),
            ("Development, revised prompt (PR-03-v4), 340 tickets", 93.2, None, None),
            ("Validation, first prompt (PR-03-v2), 80 tickets", 88.8, None, None),
            ("Validation, revised prompt (PR-03-v4), 80 tickets", 91.3, 83.3, 97.5)]
    w, left, scale = 760, 330, 4.0
    h = 60 + 40 * len(rows)
    b = []
    for pct in (70, 80, 90, 100):
        x = left + (pct - 60) * scale * 1.5
        b.append(f"<line x1='{x}' y1='30' x2='{x}' y2='{h - 20}' stroke='{LIGHT}'/>")
        b.append(text(x, h - 6, f"{pct}%", anchor="middle", size=11))
    for i, (name, v, lo, hi) in enumerate(rows):
        y = 50 + i * 40
        x = left + (v - 60) * scale * 1.5
        b.append(text(left - 10, y + 4, name, anchor="end", size=11))
        if lo is not None:
            b.append(f"<line x1='{left + (lo - 60) * scale * 1.5}' y1='{y}' x2='{left + (hi - 60) * scale * 1.5}' y2='{y}' stroke='{GREY}' stroke-width='3'/>")
        b.append(f"<circle cx='{x}' cy='{y}' r='6' fill='{BLUE if 'v4' in name else ORANGE}'/>")
        b.append(text(x + 10, y - 8, f"{v}%", size=11, weight="bold"))
    b.append(text(left, 18, "Intent accuracy (grey line = 95% interval where one was computed)", size=11))
    return svg(w, h, "".join(b))


def latency():
    vals = []
    for line in open(ROOT / "evaluation/results/validation_final_pr03v4.jsonl"):
        vals.append(json.loads(line)["latency_seconds"])
    bins = [(0, 5), (5, 10), (10, 20), (20, 30), (30, 40), (40, 50), (50, 60), (60, 70)]
    counts = [sum(1 for v in vals if lo <= v < hi) for lo, hi in bins]
    w, h, left, base, bw = 640, 240, 50, 190, 62
    top = max(counts)
    b = [text(left, 16, "Tickets per time band (seconds, 80 tickets)", size=11)]
    for i, ((lo, hi), c) in enumerate(zip(bins, counts)):
        x = left + i * (bw + 8)
        ht = c / top * 150
        b.append(f"<rect x='{x}' y='{base - ht}' width='{bw}' height='{ht}' fill='{BLUE if lo < 10 else ORANGE}'/>")
        b.append(text(x + bw / 2, base - ht - 5, str(c), anchor="middle", size=11))
        b.append(text(x + bw / 2, base + 16, f"{lo}-{hi}", anchor="middle", size=11))
    b.append(text(left, 226, "Median 6.3 s, 95th percentile 55.8 s. Two clusters: about 6 s, and 42 to 62 s (rate-limit waits).", size=11))
    return svg(w, h, "".join(b))


if __name__ == "__main__":
    for name, fn in (("fig1_volume_vs_effort", volume_vs_effort), ("fig2_architecture", architecture),
                     ("fig3_accuracy", accuracy), ("fig4_latency", latency)):
        (OUT / f"{name}.svg").write_text(fn(), encoding="utf-8")
    print("figures written")
