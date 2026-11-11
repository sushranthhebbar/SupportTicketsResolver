"""Assemble the report HTML from sections/*.html and figures, then print it to PDF with Chrome."""

import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
OUT_PDF = HERE / "SushranthHebbar_Capstone_Report.pdf"

CSS = """
@page { size: A4; margin: 22mm 20mm 22mm 20mm; @bottom-center { content: counter(page); font: 9pt Helvetica, Arial, sans-serif; color: #6b7280; } }
body { font: 10.5pt/1.45 Georgia, 'Times New Roman', serif; color: #111827; }
h1 { font: bold 22pt Helvetica, Arial, sans-serif; margin: 0 0 4pt 0; }
h2 { font: bold 15pt Helvetica, Arial, sans-serif; margin: 0 0 8pt 0; padding-top: 4pt; border-top: 2px solid #2563eb; page-break-before: always; }
h2.nobreak { page-break-before: avoid; }
h3 { font: bold 11.5pt Helvetica, Arial, sans-serif; margin: 14pt 0 4pt 0; page-break-after: avoid; }
p { margin: 0 0 7pt 0; text-align: left; orphans: 3; widows: 3; }
table { border-collapse: collapse; width: 100%; margin: 6pt 0 4pt 0; font: 8.8pt/1.35 Helvetica, Arial, sans-serif; page-break-inside: auto; }
th, td { border: 1px solid #d1d5db; padding: 3pt 5pt; vertical-align: top; text-align: left; }
th { background: #f3f4f6; }
tr { page-break-inside: avoid; }
caption { caption-side: top; text-align: left; font: bold 9pt Helvetica, Arial, sans-serif; padding-bottom: 3pt; }
figure { margin: 8pt 0 10pt 0; page-break-inside: avoid; }
figcaption { font: italic 9pt Helvetica, Arial, sans-serif; color: #374151; margin-top: 3pt; }
.cover { text-align: left; padding-top: 70mm; }
.cover .sub { font: 13pt Helvetica, Arial, sans-serif; color: #374151; margin: 6pt 0 40pt 0; }
.cover .meta { font: 10.5pt Helvetica, Arial, sans-serif; line-height: 1.7; }
.toc { font: 10.5pt Helvetica, Arial, sans-serif; line-height: 1.9; }
.note { background: #fef3c7; border: 1px solid #d97706; padding: 5pt 8pt; font: 9pt Helvetica, Arial, sans-serif; margin: 6pt 0; }
.appendix h2 { border-top-color: #6b7280; }
"""

ORDER = [
    "00_cover", "01_summary", "02_problem", "03_discovery", "04_requirements", "05_architecture",
    "06_implementation", "07_evaluation", "08_governance", "09_revision", "10_conclusions",
    "11_declaration", "12_appendices",
]


def main() -> int:
    figs = {f"{{{{fig{i}}}}}": (HERE / "figures" / name).read_text(encoding="utf-8")
            for i, name in enumerate(["fig1_volume_vs_effort.svg", "fig2_architecture.svg", "fig3_accuracy.svg", "fig4_latency.svg"], 1)}
    import json
    pc = json.load(open(HERE.parents[1] / "evaluation/results/validation_final_pr03v4.report.json"))["technical"]["intent_classification"]["per_class"]
    rows = "".join(f"<tr><td>{k.replace('_', ' ')}</td><td>{v['support']}</td><td>{v['precision'] * 100:.0f}%</td><td>{v['recall'] * 100:.0f}%</td></tr>" for k, v in pc.items())
    figs["{{perclass}}"] = ("<table><caption>Table B1. Intent classification per class, validation set (80 tickets, final run)</caption>"
                            f"<tr><th>Intent</th><th>Tickets</th><th>Precision</th><th>Recall</th></tr>{rows}</table>")
    parts = []
    for name in ORDER:
        text = (HERE / "sections" / f"{name}.html").read_text(encoding="utf-8")
        for key, value in figs.items():
            text = text.replace(key, value)
        parts.append(text)
    html = f"<!doctype html><html><head><meta charset='utf-8'><title>CloudServe support assistant: capstone report</title><style>{CSS}</style></head><body>{''.join(parts)}</body></html>"
    html_path = HERE / "report.html"
    html_path.write_text(html, encoding="utf-8")
    subprocess.run([CHROME, "--headless", "--disable-gpu", "--no-pdf-header-footer", f"--print-to-pdf={OUT_PDF}", html_path.as_uri()],
                   check=True, capture_output=True)
    pages = len(re.findall(rb"/Type\s*/Page[^s]", OUT_PDF.read_bytes()))
    print(f"wrote {OUT_PDF.name}: {pages} pages, {len(re.sub('<[^>]+>', ' ', html).split())} words")
    return 0


if __name__ == "__main__":
    sys.exit(main())
