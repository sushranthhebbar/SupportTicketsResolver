"""Assemble the report from sections/*.html, add a contents page with page numbers, print to PDF with Chrome."""

import json
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
PDF = HERE / "SushranthHebbar_Capstone_Report.pdf"
RESULTS = HERE.parents[1] / "evaluation" / "results" / "validation_final_pr03v4.report.json"

NAVY, BLUE, AMBER = "#1e3a5f", "#2563eb", "#d97706"

CSS = f"""
@page {{ size: A4; margin: 25mm 21mm 23mm 21mm;
  @top-left {{ content: "A support assistant for CloudServe Solutions"; font: 8pt 'Helvetica Neue', Helvetica, Arial, sans-serif; color: #8a94a6; }}
  @top-right {{ content: "Capstone project report"; font: 8pt 'Helvetica Neue', Helvetica, Arial, sans-serif; color: #8a94a6; }}
  @bottom-left {{ content: "Sushranth Hebbar  ·  Forward Deployed AI Engineering"; font: 8pt 'Helvetica Neue', Helvetica, Arial, sans-serif; color: #8a94a6; }}
  @bottom-right {{ content: counter(page); font: 8.5pt 'Helvetica Neue', Helvetica, Arial, sans-serif; color: {NAVY}; }} }}
@page cover {{ margin: 0; @top-left {{ content: none; }} @top-right {{ content: none; }} @bottom-left {{ content: none; }} @bottom-right {{ content: none; }} }}
* {{ -webkit-print-color-adjust: exact; print-color-adjust: exact; }}
body {{ margin: 0; font: 10.6pt/1.56 Charter, 'Iowan Old Style', Georgia, serif; color: #1c2430; }}
h2 {{ font: 700 23pt/1.15 'Helvetica Neue', Helvetica, Arial, sans-serif; color: {NAVY}; margin: 0 0 14pt 0; padding-bottom: 8pt; border-bottom: 2.5px solid {AMBER}; page-break-before: auto; }}
h2.pb {{ page-break-before: always; }}
h2.same {{ page-break-before: avoid; margin-top: 26pt; }}
.eyebrow {{ font: 600 8.5pt 'Helvetica Neue', Helvetica, Arial, sans-serif; letter-spacing: 1.6px; text-transform: uppercase; color: {AMBER}; margin: 0 0 3pt 0; page-break-before: always; page-break-after: avoid; }}
h3 {{ font: 700 12pt/1.25 'Helvetica Neue', Helvetica, Arial, sans-serif; color: {NAVY}; margin: 16pt 0 5pt 0; page-break-after: avoid; }}
p {{ margin: 0 0 8pt 0; orphans: 3; widows: 3; }}
ol, ul {{ margin: 0 0 8pt 0; padding-left: 18pt; }} li {{ margin-bottom: 4pt; }}
table {{ border-collapse: collapse; width: 100%; margin: 7pt 0 10pt 0; font: 8.5pt/1.38 'Helvetica Neue', Helvetica, Arial, sans-serif; }}
caption {{ caption-side: top; text-align: left; font: 600 8.8pt 'Helvetica Neue', Helvetica, Arial, sans-serif; color: {NAVY}; padding-bottom: 4pt; }}
th {{ background: {NAVY}; color: #fff; font-weight: 600; text-align: left; padding: 4.5pt 6pt; }}
td {{ padding: 4pt 6pt; vertical-align: top; border-bottom: 1px solid #e3e7ee; }}
tbody tr:nth-child(even) td {{ background: #f6f8fb; }}
tr {{ page-break-inside: avoid; }}
figure {{ margin: 10pt 0 12pt 0; page-break-inside: avoid; border: 1px solid #e3e7ee; border-radius: 4px; padding: 10pt 12pt 6pt 12pt; background: #fff; }}
figcaption {{ font: 8.8pt/1.4 'Helvetica Neue', Helvetica, Arial, sans-serif; color: #4b5565; margin-top: 6pt; }}
figcaption b {{ color: {NAVY}; }}
.callout {{ background: #eef3fb; border-left: 3.5px solid {BLUE}; padding: 8pt 11pt; margin: 10pt 0 12pt 0; font: 9.6pt/1.5 'Helvetica Neue', Helvetica, Arial, sans-serif; page-break-inside: avoid; }}
.callout b.t {{ display: block; color: {NAVY}; font-size: 8pt; letter-spacing: 1.2px; text-transform: uppercase; margin-bottom: 2pt; }}
.callout.warn {{ background: #fff6e8; border-left-color: {AMBER}; }}
.stats {{ display: flex; gap: 8pt; margin: 4pt 0 14pt 0; }}
.stat {{ flex: 1; border-top: 3px solid {BLUE}; background: #f6f8fb; padding: 7pt 8pt 8pt 8pt; font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; }}
.stat .n {{ font-size: 19pt; font-weight: 700; color: {NAVY}; line-height: 1.1; }}
.stat .l {{ font-size: 7.8pt; color: #4b5565; margin-top: 3pt; line-height: 1.3; }}
.stat.amber {{ border-top-color: {AMBER}; }}
.cover {{ page: cover; height: 280mm; position: relative; page-break-after: always; }}
.cover .band {{ background: {NAVY}; height: 118mm; padding: 34mm 24mm 0 24mm; color: #fff; box-sizing: border-box; }}
.cover .band .k {{ font: 600 9pt 'Helvetica Neue', Helvetica, Arial, sans-serif; letter-spacing: 2.4px; text-transform: uppercase; color: #f5c27a; }}
.cover h1 {{ font: 700 34pt/1.12 'Helvetica Neue', Helvetica, Arial, sans-serif; margin: 10pt 0 12pt 0; }}
.cover .sub {{ font: 13pt/1.45 'Helvetica Neue', Helvetica, Arial, sans-serif; color: #d6e0f0; max-width: 135mm; }}
.cover .rule {{ height: 5px; background: {AMBER}; }}
.cover .meta {{ padding: 14mm 24mm; font: 11pt/1.8 'Helvetica Neue', Helvetica, Arial, sans-serif; color: #1c2430; }}
.cover .meta .n {{ font-size: 17pt; font-weight: 700; color: {NAVY}; line-height: 1.3; }}
.cover .meta .role {{ font-size: 10.5pt; color: #4b5565; margin-bottom: 12mm; }}
.cover table.docmeta {{ width: 100%; font: 9.6pt/1.5 'Helvetica Neue', Helvetica, Arial, sans-serif; margin: 0; }}
.cover table.docmeta td {{ border-bottom: 1px solid #e3e7ee; padding: 5pt 0; background: none !important; }}
.cover table.docmeta td:first-child {{ width: 42mm; color: #8a94a6; font-weight: 600; text-transform: uppercase; font-size: 7.8pt; letter-spacing: 1px; }}
.cover .foot {{ position: absolute; bottom: 16mm; left: 24mm; right: 24mm; font: 8.6pt/1.5 'Helvetica Neue', Helvetica, Arial, sans-serif; color: #8a94a6; border-top: 1px solid #e3e7ee; padding-top: 6pt; }}
.toc h1 {{ font: 700 23pt 'Helvetica Neue', Helvetica, Arial, sans-serif; color: {NAVY}; margin: 0 0 14pt 0; padding-bottom: 8pt; border-bottom: 2.5px solid {AMBER}; }}
.toc .row {{ display: flex; align-items: baseline; font: 10.8pt/2.0 'Helvetica Neue', Helvetica, Arial, sans-serif; }}
.toc .row .t {{ flex: 0 1 auto; }} .toc .row .d {{ flex: 1; border-bottom: 1px dotted #9aa4b5; margin: 0 6pt; transform: translateY(-3pt); }} .toc .row .p {{ color: {NAVY}; font-weight: 600; }}
.toc .sec {{ font-weight: 600; color: {NAVY}; }}
.toc .sub .t {{ color: #4b5565; padding-left: 12pt; }}
.toc p.note {{ font: 9.2pt/1.5 'Helvetica Neue', Helvetica, Arial, sans-serif; color: #4b5565; margin-top: 18pt; border-top: 1px solid #e3e7ee; padding-top: 8pt; }}
.toc h1.lof {{ margin-top: 0; }}
.toc .grp {{ font: 600 8.5pt 'Helvetica Neue', Helvetica, Arial, sans-serif; letter-spacing: 1.6px; text-transform: uppercase; color: {AMBER}; margin: 12pt 0 2pt 0; }}
.toc .row.cap {{ font-size: 9.6pt; line-height: 1.75; }} .toc .row.cap .t {{ color: #1c2430; }} .toc .row.cap .t b {{ color: {NAVY}; font-weight: 600; display: inline-block; width: 19mm; }}
.appendix h2 {{ border-bottom-color: #8a94a6; }}
"""

TOC = [
    ("s1", "1", "Executive summary", False), ("s2", "2", "The problem", False), ("s3", "3", "Discovery findings", False),
    ("s4", "4", "Requirements", False), ("s5", "5", "Architecture and design", False), ("s6", "6", "Implementation", False),
    ("s7", "7", "Evaluation", False), ("s8", "8", "Governance and risk", False), ("s9", "9", "The requirements revision", False),
    ("s10", "10", "Conclusions", False), ("decl", "", "Declaration of AI tool use", False),
    ("aA", "", "Appendix A. Prompt register", True), ("aB", "", "Appendix B. Full result tables", True),
    ("aC", "", "Appendix C. Requirement traceability", True), ("aD", "", "Appendix D. Workbooks and reproduction", True),
    ("aE", "", "Appendix E. Open items and uncertainties", True),
]
ORDER = ["cover", "toc", "lof", "s01", "s02", "s03", "s04", "s05", "s06", "s07", "s08", "s09", "s10", "s11", "s12"]


def toc_html(pages):
    rows = []
    for sid, num, title, sub in TOC:
        label = f"{num}&nbsp;&nbsp;{title}" if num else title
        cls = "row sub" if sub else "row sec"
        rows.append(f"<div class='{cls}'><span class='t'>{label}</span><span class='d'></span><span class='p'>{pages.get(sid, '')}</span></div>")
    note = ("<p class='note'>Every performance figure states the data it was measured on. Three sets of tickets are used: "
            "500 development tickets (analysis and design decisions), 80 validation tickets (final comparison, never used for tuning), "
            "and a hidden set of 120 tickets that I was not given. Appendix E lists what is unmeasured or not yet checked.</p>")
    return f"<div class='toc' style='page-break-after: always'><h1>Contents</h1>{''.join(rows)}{note}</div>"


def captions():
    """(label, short title) for every numbered table and figure, in document order."""
    caps = []
    for name in ORDER:
        f = HERE / "sections" / f"{name}.html"
        if not f.exists():
            continue
        text = f.read_text(encoding="utf-8").replace("{{perclass}}", "<caption>Table B1. Intent classification per class, validation set (80 tickets, final run)</caption>")
        for m in re.finditer(r"<caption>((?:Table) [A-Z]?\d+)\. (.*?)</caption>|<figcaption><b>(Figure \d+)\.</b> (.*?)</figcaption>", text, re.S):
            label, title = (m.group(1), m.group(2)) if m.group(1) else (m.group(3), m.group(4))
            title = re.sub(r"<[^>]+>", "", title).strip()
            if m.group(3):
                title = title.split(". ")[0].split(" (")[0].rstrip(".")
            caps.append((label, title))
    return caps


def lof_html(pages):
    caps = captions()
    def rows(kind):
        return "".join(f"<div class='row cap'><span class='t'><b>{l}</b>{t}</span><span class='d'></span><span class='p'>{pages.get(l, '')}</span></div>"
                       for l, t in caps if l.startswith(kind))
    return (f"<div class='toc' style='page-break-after: always'><h1 class='lof'>Figures and tables</h1>"
            f"<div class='grp'>Figures</div>{rows('Figure')}<div class='grp'>Tables</div>{rows('Table')}</div>")


def find_pages(pdf_path):
    try:
        import fitz
    except ImportError:
        return {}
    doc = fitz.open(pdf_path)
    lines_by_page = [[ln.strip() for ln in page.get_text().splitlines() if ln.strip()] for page in doc]
    start = next((i + 1 for i, ls in enumerate(lines_by_page) if "Contents" in ls), 2)
    pages = {}
    for sid, num, title, sub in TOC:
        for i in range(start, len(doc)):
            ls = lines_by_page[i]
            if sub:
                hit = title in ls
            elif num:
                hit = any(ls[j].lower() == f"section {num}" and ls[j + 1] == title for j in range(len(ls) - 1))
            else:
                hit = title in ls
            if hit:
                pages[sid] = i + 1
                break
    for label, _ in captions():
        for i in range(start, len(doc)):
            if any(ln.startswith(label + ". ") for ln in lines_by_page[i]):
                pages[label] = i + 1
                break
    return pages


def build(pages):
    per_class = json.load(open(RESULTS))["technical"]["intent_classification"]["per_class"]
    rows = "".join(f"<tr><td>{k.replace('_', ' ')}</td><td>{v['support']}</td><td>{v['precision'] * 100:.0f}%</td><td>{v['recall'] * 100:.0f}%</td></tr>" for k, v in per_class.items())
    subs = {f"{{{{fig{i}}}}}": (HERE / "figures" / n).read_text(encoding="utf-8")
            for i, n in enumerate(["fig1_volume_vs_effort.svg", "fig2_architecture.svg", "fig3_accuracy.svg", "fig4_latency.svg"], 1)}
    subs["{{perclass}}"] = ("<table><caption>Table B1. Intent classification per class, validation set (80 tickets, final run)</caption>"
                            f"<thead><tr><th>Intent</th><th>Tickets</th><th>Precision</th><th>Recall</th></tr></thead><tbody>{rows}</tbody></table>")
    parts = []
    for name in ORDER:
        if name == "toc":
            parts.append(toc_html(pages)); continue
        if name == "lof":
            parts.append(lof_html(pages)); continue
        text = (HERE / "sections" / f"{name}.html").read_text(encoding="utf-8")
        for k, v in subs.items():
            text = text.replace(k, v)
        parts.append(text)
    html = (f"<!doctype html><html><head><meta charset='utf-8'><title>A support assistant for CloudServe: capstone report</title>"
            f"<style>{CSS}</style></head><body>{''.join(parts)}</body></html>")
    out = HERE / "report.html"
    out.write_text(html, encoding="utf-8")
    subprocess.run([CHROME, "--headless", "--disable-gpu", "--no-pdf-header-footer", f"--print-to-pdf={PDF}", out.as_uri()],
                   check=True, capture_output=True)
    return len(html)


def main():
    build({})
    pages = find_pages(PDF)
    build(pages)
    n = len(re.findall(rb"/Type\s*/Page[^s]", PDF.read_bytes()))
    print(f"{PDF.name}: {n} pages; contents pages found: {pages}")


if __name__ == "__main__":
    sys.exit(main())
