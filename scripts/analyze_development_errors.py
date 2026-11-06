"""Reproducible multi-metric error analysis of PR-03-v2 on the DEVELOPMENT set.

Reads only development data (evaluation/data/development_tickets.json,
evaluation/calibration/*, evaluation/results/development_* and
urgency_spectrum_development / urgency_pr03_v3_16). It never touches validation
files, makes no model calls and writes nothing except to stdout (markdown tables).

Usage:  .venv/bin/python scripts/analyze_development_errors.py [section ...]
Sections: data intent urgency joint scenarios routing probes labels   (default: all; add --show to labels to print the error sample)
"""

from __future__ import annotations

import collections as C
import hashlib
import json
import math
import random
import statistics as st
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.calibration import predict_isotonic  # noqa: E402
from src.routing import route_ticket  # noqa: E402

TICKETS = ROOT / "evaluation/data/development_tickets.json"
PREDS = ROOT / "evaluation/calibration/development_predictions.jsonl"
CALIB = ROOT / "evaluation/calibration/calibration-v1.json"
RES = ROOT / "evaluation/results"
U = ["low", "medium", "high"]
ORD = {u: i for i, u in enumerate(U)}

# ---------------------------------------------------------------- helpers

def tkey(t):
    return " ".join((t["subject"] + " " + t["body"]).casefold().split())


def split_of(k):
    return "fit" if int(hashlib.sha256(k.encode()).hexdigest()[:8], 16) / 0xFFFFFFFF < 0.7 else "holdout"


def wilson(k, n, z=1.96):
    if n == 0:
        return (float("nan"), float("nan"))
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return c - h, c + h


def fmt(k, n):
    if n == 0:
        return "n/a (n=0)"
    lo, hi = wilson(k, n)
    return f"{k / n:.1%} ({k}/{n}; {lo:.0%}-{hi:.0%})" + (" *" if n < 10 else "")


def pct(k, n):
    return "n/a" if n == 0 else f"{k / n:.1%}"


def table(header, rows):
    out = ["| " + " | ".join(str(h) for h in header) + " |", "|" + "|".join("---" for _ in header) + "|"]
    out += ["| " + " | ".join(str(c) for c in r) + " |" for r in rows]
    print("\n".join(out) + "\n")


def h(title):
    print(f"\n## {title}\n")


def auroc(scores, ok):
    """P(score_correct > score_wrong), ties 0.5."""
    pos = [s for s, o in zip(scores, ok) if o]
    neg = [s for s, o in zip(scores, ok) if not o]
    if not pos or not neg:
        return float("nan")
    tot = sum(1 if a > b else 0.5 if a == b else 0 for a in pos for b in neg)
    return tot / (len(pos) * len(neg))


def binom_two_sided(b, c):
    n = b + c
    if n == 0:
        return 1.0
    k = min(b, c)
    p = sum(math.comb(n, i) for i in range(0, k + 1)) / 2 ** n
    return min(1.0, 2 * p)


def majority(labels, default="medium"):
    if not labels:
        return default
    cnt = C.Counter(labels)
    best = max(cnt.values())
    return sorted(l for l, n in cnt.items() if n == best)[0]


# ---------------------------------------------------------------- data

T = json.load(open(TICKETS, encoding="utf-8"))
BYID = {t["ticket_id"]: t for t in T}
GRP = C.defaultdict(list)
for t in T:
    GRP[tkey(t)].append(t)
CONFLICT = {k: len({x["labels"]["urgency"] for x in v}) > 1 for k, v in GRP.items()}
PRED_ROWS = [json.loads(l) for l in open(PREDS, encoding="utf-8") if l.strip()]
R = []
for p in PRED_ROWS:
    if p.get("error"):
        continue
    t = BYID[p["ticket_id"]]
    k = tkey(t)
    assert split_of(k) == p["split"]
    R.append(dict(
        id=p["ticket_id"], t=t, key=k, split=p["split"], conflict=CONFLICT[k],
        gi=t["labels"]["intent"], gu=t["labels"]["urgency"], pi=p["intent"], pu=p["urgency"],
        ic=p["intent_confidence"], uc=p["urgency_confidence"], amb=p["urgency_ambiguous"],
        ev=p["urgency_evidence_valid"], words=len((t["subject"] + " " + t["body"]).split()),
    ))
for r in R:
    r["iok"] = r["gi"] == r["pi"]
    r["uok"] = r["gu"] == r["pu"]
CF = [r for r in R if not r["conflict"]]
HO = [r for r in R if r["split"] == "holdout"]
FIT = [r for r in R if r["split"] == "fit"]
CAL = json.load(open(CALIB, encoding="utf-8"))["calibrators"]


def acc(rows, f):
    return fmt(sum(r[f] for r in rows), len(rows))


# ---------------------------------------------------------------- 0 data

def sec_data():
    h("0. Data and sample description")
    nd = sum(len(v) > 1 for v in GRP.values())
    nc = sum(CONFLICT[k] for k, v in GRP.items() if len(v) > 1)
    table(["quantity", "value"], [
        ["dev tickets / unique texts", f"{len(T)} / {len(GRP)}"],
        ["repeated-text groups / with conflicting urgency", f"{nd} / {nc}"],
        ["tickets in conflicting groups (all dev)", sum(len(v) for k, v in GRP.items() if CONFLICT[k])],
        ["repeated-text groups with conflicting expected_route", sum(len({x['labels']['expected_route'] for x in v}) > 1 for v in GRP.values())],
        ["repeated-text groups with conflicting answerable_from_docs", sum(len({x['labels']['answerable_from_docs'] for x in v}) > 1 for v in GRP.values())],
        ["repeated-text groups with conflicting expected_route that also differ in answerable_from_docs / history.escalated",
         "{} / {}".format(sum(len({x['labels']['answerable_from_docs'] for x in v}) > 1 for v in GRP.values() if len({x['labels']['expected_route'] for x in v}) > 1),
                          sum(len({x['history']['escalated'] for x in v}) > 1 for v in GRP.values() if len({x['labels']['expected_route'] for x in v}) > 1))],
        ["repeated-text groups with conflicting intent", sum(len({x['labels']['intent'] for x in v}) > 1 for v in GRP.values())],
        ["prediction rows (attempted / classified / error)", f"{len(PRED_ROWS)} / {len(R)} / {len(PRED_ROWS) - len(R)}"],
        ["classified: fit / holdout", f"{len(FIT)} / {len(HO)}"],
        ["classified: unique texts", len({r['key'] for r in R})],
        ["classified in a conflicting-urgency text group", sum(r['conflict'] for r in R)],
        ["classified conflict-free", len(CF)],
    ])
    g = C.defaultdict(list)
    for r in R:
        g[r["key"]].append(r)
    incons = sum(len({(x["pi"], x["pu"], x["ic"], x["uc"]) for x in v}) > 1 for v in g.values())
    print(f"Repeated texts within the classified set: {sum(len(v) > 1 for v in g.values())} groups; "
          f"{incons} of them received non-identical outputs for identical text (temperature 0 but provider non-determinism).\n")
    # representativeness of classified subset vs all dev
    rows = []
    for u in U:
        rows.append([u, pct(sum(t['labels']['urgency'] == u for t in T), len(T)), pct(sum(r['gu'] == u for r in R), len(R)),
                     pct(sum(r['gu'] == u for r in HO), len(HO))])
    table(["gold urgency", "all 500 dev", "classified 341", "holdout 90"], rows)
    # ceiling
    ceil = 0
    for v in g.values():
        cnt = C.Counter(x["gu"] for x in v)
        ceil += max(cnt.values())
    print(f"Text-only ceiling: a deterministic function of the text can match at most {fmt(ceil, len(R))} of the 341 gold urgency labels "
          f"(best single label per distinct text; ignores that 13 text groups got inconsistent outputs).\n")


# ---------------------------------------------------------------- 1 intent

def prf(rows, gk, pk, classes):
    out = {}
    for c in classes:
        tp = sum(r[gk] == c and r[pk] == c for r in rows)
        fp = sum(r[gk] != c and r[pk] == c for r in rows)
        fn = sum(r[gk] == c and r[pk] != c for r in rows)
        p = tp / (tp + fp) if tp + fp else None
        if p is None and tp + fn:
            p = 0.0  # src/evaluation.py convention
        rc = tp / (tp + fn) if tp + fn else None
        f1 = 2 * p * rc / (p + rc) if p is not None and rc is not None and p + rc > 0 else (0.0 if p is not None and rc is not None else None)
        out[c] = dict(tp=tp, fp=fp, fn=fn, sup=tp + fn, npred=tp + fp, p=p, r=rc, f1=f1)
    return out


def sec_intent():
    h("1. Intent")
    classes = sorted({r["gi"] for r in R} | {r["pi"] for r in R})
    for name, rows in (("all classified", R), ("fit", FIT), ("holdout", HO)):
        s = prf(rows, "gi", "pi", classes)
        mp = st.mean(v["p"] for v in s.values() if v["p"] is not None)
        mr = st.mean(v["r"] for v in s.values() if v["r"] is not None)
        mf = st.mean(v["f1"] for v in s.values() if v["f1"] is not None)
        print(f"- {name}: accuracy {acc(rows, 'iok')}; macro precision {mp:.3f}, macro recall {mr:.3f}, macro F1 {mf:.3f} (n={len(rows)})")
    print()
    s = prf(R, "gi", "pi", classes)
    s_ho = prf(HO, "gi", "pi", classes)
    rows = []
    for c in sorted(classes, key=lambda c: (s[c]["f1"] or 0)):
        v = s[c]
        rows.append([c, v["sup"], v["npred"], "n/a" if v["p"] is None else f"{v['p']:.2f}",
                     "n/a" if v["r"] is None else f"{v['r']:.2f}", f"{v['f1']:.2f}",
                     f"{s_ho[c]['tp']}/{s_ho[c]['sup']}" , "*" if v["sup"] < 10 else ""])
    print("Per-class (all 341 classified; sorted by F1; holdout column = correct/support on holdout; * = support < 10):\n")
    table(["intent", "support", "n predicted", "precision", "recall", "F1", "holdout hit", "n<10"], rows)
    cm = C.Counter((r["gi"], r["pi"]) for r in R if not r["iok"])
    print("Top confusion pairs (gold -> predicted), all classified:\n")
    table(["gold", "predicted", "n"], [[a, b, n] for (a, b), n in cm.most_common(15)])
    print(f"Errors: {sum(not r['iok'] for r in R)}; top-3 pairs cover {sum(n for _, n in cm.most_common(3))}.\n")
    # confidence
    print("Intent confidence vs accuracy (raw self-reported):\n")
    rows = []
    for v in sorted({r["ic"] for r in R}):
        m = [r for r in R if r["ic"] == v]
        rows.append([v, len(m), acc(m, "iok")])
    table(["raw intent_confidence", "n", "accuracy"], rows)
    print(f"AUROC of raw intent confidence for correctness: {auroc([r['ic'] for r in R], [r['iok'] for r in R]):.3f} "
          f"(holdout only: {auroc([r['ic'] for r in HO], [r['iok'] for r in HO]):.3f}, n={len(HO)}).\n")
    lo = [r for r in R if r["ic"] < 0.95]
    print(f"Confidence < 0.95: {acc(lo, 'iok')}; confidence >= 0.95: {acc([r for r in R if r['ic'] >= .95], 'iok')}.\n")
    # confusion-by-gold with errors only for weak classes
    print("Intent errors by weak class (misses of the three lowest-recall gold classes; false positives of the main 'sink' predictions):\n")
    err = [r for r in R if not r["iok"]]
    for c in ("integration_help", "api_key_issue", "compliance_request"):
        e = [r for r in err if r["gi"] == c]
        print(f"- gold {c}: {len(e)} errors -> {dict(C.Counter(r['pi'] for r in e))}")
    for c in ("configuration_help", "data_export", "webhook_issue", "performance_degradation", "security_incident"):
        e = [r for r in err if r["pi"] == c]
        print(f"- predicted {c}: {len(e)} false positives from {dict(C.Counter(r['gi'] for r in e))}")
    print()
    # intent accuracy on conflict-free vs conflicted -> no label conflict on intent
    print("Intent labels never conflict across identical texts in dev (see section 0), so intent is not affected by the duplicate-label problem.\n")
    # duplicated-text inflation: dedupe by text
    seen = {}
    for r in R:
        seen.setdefault(r["key"], r)
    d = list(seen.values())
    print(f"Distinct-text intent accuracy (first copy of each text): {acc(d, 'iok')}.\n")


# ---------------------------------------------------------------- 2 urgency

def confusion(rows):
    m = [[sum(r["gu"] == g and r["pu"] == p for r in rows) for p in U] for g in U]
    return m


def print_confusion(rows, title):
    m = confusion(rows)
    print(f"{title} (rows = gold, columns = predicted; n={len(rows)})\n")
    table(["gold \\ pred"] + U + ["total", "recall"],
          [[g] + m[i] + [sum(m[i]), pct(m[i][i], sum(m[i]))] for i, g in enumerate(U)]
          + [["precision"] + [pct(m[j][j], sum(m[i][j] for i in range(3))) for j in range(3)] + [sum(map(sum, m)), pct(sum(m[i][i] for i in range(3)), len(rows))]])


def baselines(train_pool, score_rows, label):
    """train_pool: list of (intent, urgency) used to fit; returns accuracy of constant & per-intent majority."""
    const = majority([u for _, u in train_pool])
    byint = C.defaultdict(list)
    for i, u in train_pool:
        byint[i].append(u)
    pm = {i: majority(v) for i, v in byint.items()}
    ok_c = sum(r["gu"] == const for r in score_rows)
    ok_g = sum(r["gu"] == pm.get(r["gi"], const) for r in score_rows)
    ok_p = sum(r["gu"] == pm.get(r["pi"], const) for r in score_rows)
    return const, ok_c, ok_g, ok_p


def sec_urgency():
    h("2. Urgency")
    print(f"- All classified: {acc(R, 'uok')}\n- Conflict-free: {acc(CF, 'uok')}\n- Conflicting-text tickets only: {acc([r for r in R if r['conflict']], 'uok')}\n"
          f"- Fit split: {acc(FIT, 'uok')}; holdout split: {acc(HO, 'uok')}; holdout conflict-free: {acc([r for r in HO if not r['conflict']], 'uok')}\n")
    print_confusion(R, "Confusion, all classified")
    print_confusion(CF, "Confusion, conflict-free")
    print_confusion([r for r in R if r["conflict"]], "Confusion, conflicting-text tickets only")
    # macro metrics as src/evaluation.py defines them
    for name, rs in (("all", R), ("conflict-free", CF), ("holdout", HO)):
        sc = prf(rs, "gu", "pu", U)
        print(f"- urgency macro precision / recall / F1, {name} (n={len(rs)}): {st.mean(v['p'] for v in sc.values()):.3f} / {st.mean(v['r'] for v in sc.values()):.3f} / {st.mean(v['f1'] for v in sc.values()):.3f}; "
              f"classes meeting the project 85% per-class precision and recall target: {sum(1 for v in sc.values() if v['p'] >= .85 and v['r'] >= .85)}/3")
    print()
    # ordinal
    rows = []
    for name, rs in (("all", R), ("conflict-free", CF)):
        d = C.Counter(ORD[r["pu"]] - ORD[r["gu"]] for r in rs)
        n = len(rs)
        rows.append([name, n, pct(d[0], n), pct(d[1] + d[-1], n), pct(d[2] + d[-2], n),
                     f"under-call {pct(d[-1] + d[-2], n)} / over-call {pct(d[1] + d[2], n)}",
                     f"{st.mean(ORD[r['pu']] - ORD[r['gu']] for r in rs):+.2f}"])
    print("Ordinal error (levels off; low=0, medium=1, high=2):\n")
    table(["set", "n", "exact", "off by 1", "off by 2", "direction", "mean signed error"], rows)
    print("Predicted vs gold distribution (all classified):\n")
    table(["level", "gold", "predicted"], [[u, pct(sum(r['gu'] == u for r in R), len(R)), pct(sum(r['pu'] == u for r in R), len(R))] for u in U])

    # baselines
    print("### Baselines vs model (majority classes broken alphabetically; 'oracle intent' uses the GOLD intent as a feature, which a real system does not have; 'predicted intent' uses PR-03-v2's intent)\n")
    allpool = [(r["gi"], r["gu"]) for r in R]
    fitpool = [(r["gi"], r["gu"]) for r in FIT]
    fit500 = [(t["labels"]["intent"], t["labels"]["urgency"]) for t in T if split_of(tkey(t)) == "fit"]
    rows = []
    c, a, g, p = baselines(allpool, R, "in")
    rows.append(["IN-SAMPLE (fit and score on all 341)", len(R), fmt(sum(r['uok'] for r in R), len(R)), f"{fmt(a, len(R))} [{c}]", fmt(g, len(R)), fmt(p, len(R))])
    c, a, g, p = baselines(allpool, CF, "in")
    rows.append(["IN-SAMPLE, conflict-free scored", len(CF), fmt(sum(r['uok'] for r in CF), len(CF)), f"{fmt(a, len(CF))} [{c}]", fmt(g, len(CF)), fmt(p, len(CF))])
    c, a, g, p = baselines(fitpool, HO, "ho")
    rows.append(["HELD-OUT: fit on 251 fit-split preds, score 90 holdout", len(HO), fmt(sum(r['uok'] for r in HO), len(HO)), f"{fmt(a, len(HO))} [{c}]", fmt(g, len(HO)), fmt(p, len(HO))])
    c, a, g, p = baselines(fit500, HO, "ho500")
    rows.append([f"HELD-OUT: fit on all {len(fit500)} dev tickets in fit split, score 90 holdout", len(HO), fmt(sum(r['uok'] for r in HO), len(HO)), f"{fmt(a, len(HO))} [{c}]", fmt(g, len(HO)), fmt(p, len(HO))])
    hocf = [r for r in HO if not r["conflict"]]
    c, a, g, p = baselines(fit500, hocf, "ho500cf")
    rows.append(["HELD-OUT (fit-500), holdout conflict-free only", len(hocf), fmt(sum(r['uok'] for r in hocf), len(hocf)), f"{fmt(a, len(hocf))} [{c}]", fmt(g, len(hocf)), fmt(p, len(hocf))])
    table(["protocol", "n scored", "PR-03-v2 model", "constant majority [label]", "per-intent majority (oracle intent)", "per-intent majority (predicted intent)"], rows)
    # paired on holdout
    c, a, g, p = baselines(fit500, HO, "")
    byint = C.defaultdict(list)
    for i, u in fit500:
        byint[i].append(u)
    pm = {i: majority(v) for i, v in byint.items()}
    b = sum(r["uok"] and r["gu"] != pm[r["gi"]] for r in HO)
    cc = sum((not r["uok"]) and r["gu"] == pm[r["gi"]] for r in HO)
    print(f"Paired on holdout (n=90): model right & per-intent baseline wrong = {b}; baseline right & model wrong = {cc}; exact sign-test p = {binom_two_sided(b, cc):.2f}.\n")
    # in-sample optimism of per-intent: leave-one-text-out
    loo = 0
    for r in R:
        pool = [x for x in R if x["key"] != r["key"]]
        bi = C.defaultdict(list)
        for x in pool:
            bi[x["gi"]].append(x["gu"])
        loo += r["gu"] == majority(bi.get(r["gi"], []), majority([x["gu"] for x in pool]))
    print(f"Leave-one-text-out per-intent majority (oracle intent), n=341: {fmt(loo, len(R))} -- a less noisy optimism check than the single 90-ticket holdout.\n")
    # per-intent baseline per-urgency recall
    print("Per-intent majority (oracle intent, fit on fit-500) predicted-level distribution on holdout: "
          + str(dict(C.Counter(pm.get(r['gi'], 'medium') for r in HO))) + "\n")

    # per segment
    def seg(name, f, rows_=R):
        d = C.defaultdict(list)
        for r in rows_:
            d[f(r)].append(r)
        out = []
        for k in sorted(d, key=str):
            m = d[k]
            out.append([k, len(m), acc(m, "uok"), pct(sum(x['pu'] == 'high' for x in m), len(m)), pct(sum(x['gu'] == 'high' for x in m), len(m))])
        print(f"By {name}:\n")
        table([name, "n", "urgency accuracy", "pred high share", "gold high share"], out)

    seg("gold intent", lambda r: r["gi"])
    seg("channel", lambda r: r["t"]["channel"])
    seg("customer_tier", lambda r: r["t"]["customer_tier"])
    seg("language_fluency", lambda r: r["t"]["language_fluency"])
    ws = sorted(r["words"] for r in R)
    q1, q2 = ws[len(ws) // 3], ws[2 * len(ws) // 3]
    seg(f"text length (words; tertile cuts {q1}/{q2})", lambda r: "short" if r["words"] <= q1 else "medium" if r["words"] <= q2 else "long")
    print("Conflict-free repeat of the channel/tier/fluency/length cuts (accuracy only):\n")
    for name, f in (("channel", lambda r: r["t"]["channel"]), ("tier", lambda r: r["t"]["customer_tier"]), ("fluency", lambda r: r["t"]["language_fluency"])):
        d = C.defaultdict(list)
        for r in CF:
            d[f(r)].append(r)
        print(f"- {name}: " + "; ".join(f"{k} {acc(v, 'uok')}" for k, v in sorted(d.items())))
    print()

    # ambiguity / evidence
    print("### Ambiguity flag and evidence validity\n")
    rows = []
    for name, f in (("urgency_ambiguous = true", lambda r: r["amb"]), ("urgency_ambiguous = false", lambda r: not r["amb"]),
                    ("evidence valid", lambda r: r["ev"]), ("evidence invalid", lambda r: not r["ev"])):
        m = [r for r in R if f(r)]
        mc = [r for r in CF if f(r)]
        rows.append([name, len(m), pct(len(m), len(R)), acc(m, "uok"), acc(mc, "uok"), pct(sum(x['conflict'] for x in m), len(m))])
    table(["group", "n", "share", "urgency acc (all)", "urgency acc (conflict-free)", "share in conflict groups"], rows)
    amb_c = sum(r["amb"] for r in R if r["conflict"])
    print(f"Ambiguity rate on conflicting-label texts {pct(amb_c, sum(r['conflict'] for r in R))} vs conflict-free {pct(sum(r['amb'] for r in CF), len(CF))}. "
          f"AUROC of the ambiguity flag (not-ambiguous) for urgency correctness: {auroc([0 if r['amb'] else 1 for r in R], [r['uok'] for r in R]):.3f}.\n")
    rows = []
    for u in U:
        m = [r for r in R if r["pu"] == u]
        rows.append([f"predicted {u}", len(m), pct(sum(r['amb'] for r in m), len(m))])
    table(["group", "n", "ambiguous rate"], rows)

    # confidence
    print("### Urgency confidence vs accuracy\n")
    rows = []
    for v in sorted({r["uc"] for r in R}):
        m = [r for r in R if r["uc"] == v]
        rows.append([v, len(m), acc(m, "uok"), acc([x for x in m if not x['conflict']], "uok")])
    table(["raw urgency_confidence", "n", "accuracy (all)", "accuracy (conflict-free)"], rows)
    for name, rs in (("all", R), ("conflict-free", CF), ("holdout", HO)):
        print(f"- AUROC raw urgency confidence -> correct, {name} (n={len(rs)}): {auroc([r['uc'] for r in rs], [r['uok'] for r in rs]):.3f}")
    bands = [("<0.70", lambda v: v < .7), ("0.70-0.85", lambda v: .7 <= v < .85), (">=0.90", lambda v: v >= .9)]
    print()
    rows = []
    for nm, f in bands:
        m = [r for r in R if f(r["uc"])]
        rows.append([nm, len(m), acc(m, "uok")])
    table(["band", "n", "accuracy"], rows)
    cb = CAL["urgency"]["blocks"]
    cal = [predict_isotonic(cb, r["uc"]) for r in R]
    print(f"Calibrated urgency scores take values {sorted(set(round(c, 3) for c in cal))}; max {max(cal):.3f} (< 0.80 so urgency can never clear the auto-respond bar).\n")
    # high-urgency under-call
    hi = [r for r in R if r["gu"] == "high"]
    print("### High urgency\n")
    d = C.Counter(r["pu"] for r in hi)
    print(f"Gold high n={len(hi)}: predicted high {fmt(d['high'], len(hi))}, medium {d['medium']}, low {d['low']}. "
          f"Predicted high n={sum(r['pu'] == 'high' for r in R)}, precision {fmt(sum(r['pu'] == 'high' and r['gu'] == 'high' for r in R), sum(r['pu'] == 'high' for r in R))}.\n")
    hic = [r for r in CF if r["gu"] == "high"]
    d = C.Counter(r["pu"] for r in hic)
    print(f"Conflict-free gold high n={len(hic)}: recall {fmt(d['high'], len(hic))}.\n")
    # high recall by intent
    rows = []
    for c in sorted({r["gi"] for r in hi}):
        m = [r for r in hi if r["gi"] == c]
        rows.append([c, len(m), fmt(sum(r['pu'] == 'high' for r in m), len(m))])
    table(["gold intent (gold-high tickets)", "n", "predicted-high recall"], rows)
    print("Where the model says high but gold is not high (false highs), by gold intent:\n")
    fh = [r for r in R if r["pu"] == "high" and r["gu"] != "high"]
    table(["gold intent", "n"], [[a, n] for a, n in C.Counter(r['gi'] for r in fh).most_common(8)])
    # accuracy decomposition: the two intents where urgency is nearly deterministic in the labels
    sr = [r for r in R if r["gi"] in ("security_incident", "rollback_request")]
    rest = [r for r in R if r["gi"] not in ("security_incident", "rollback_request")]
    loo_rest = sum(r["gu"] == majority([x["gu"] for x in R if x["key"] != r["key"] and x["gi"] == r["gi"]]) for r in rest)
    print("### Where the accuracy comes from\n")
    table(["subset", "n", "PR-03-v2", "always medium", "leave-one-text-out per-intent majority (oracle intent)"],
          [["security_incident + rollback_request", len(sr), acc(sr, "uok"), fmt(sum(r['gu'] == 'medium' for r in sr), len(sr)),
            fmt(sum(r["gu"] == majority([x["gu"] for x in R if x["key"] != r["key"] and x["gi"] == r["gi"]]) for r in sr), len(sr))],
           ["all other 20 intents", len(rest), acc(rest, "uok"), fmt(sum(r['gu'] == 'medium' for r in rest), len(rest)), fmt(loo_rest, len(rest))]])
    # gold-high recall excluding security/rollback
    easy = {"security_incident", "rollback_request"}
    m1 = [r for r in hi if r["gi"] in easy]
    m2 = [r for r in hi if r["gi"] not in easy]
    print(f"Gold-high recall within security_incident/rollback_request: {fmt(sum(r['pu']=='high' for r in m1), len(m1))}; within all other intents: {fmt(sum(r['pu']=='high' for r in m2), len(m2))}.\n")


# ---------------------------------------------------------------- 3 joint

def sec_joint():
    h("3. Joint intent / urgency view")
    for name, rs in (("all classified", R), ("conflict-free", CF)):
        n = len(rs)
        a = sum(r["iok"] and r["uok"] for r in rs)
        b = sum(r["iok"] and not r["uok"] for r in rs)
        c = sum((not r["iok"]) and r["uok"] for r in rs)
        d = sum((not r["iok"]) and (not r["uok"]) for r in rs)
        print(f"{name} (n={n})\n")
        table(["", "urgency right", "urgency wrong", "total"],
              [["intent right", a, b, a + b], ["intent wrong", c, d, c + d], ["total", a + c, b + d, n]])
        print(f"Both right {fmt(a, n)}; urgency acc given intent right {fmt(a, a + b)}, given intent wrong {fmt(c, c + d)}. "
              f"Odds ratio (intent right x urgency right) = {(a * d) / (b * c) if b * c else float('nan'):.2f}.\n")
    ie = [r for r in R if not r["iok"]]
    print(f"Of {len(ie)} intent errors, {sum(r['uok'] for r in ie)} still have correct urgency. Urgency errors per intent-correct ticket: {sum((not r['uok']) for r in R if r['iok'])}/{sum(r['iok'] for r in R)}.\n")
    print("Mean signed urgency error by whether intent was right: "
          f"right {st.mean(ORD[r['pu']] - ORD[r['gu']] for r in R if r['iok']):+.2f}, wrong {st.mean(ORD[r['pu']] - ORD[r['gu']] for r in ie):+.2f}.\n")


# ---------------------------------------------------------------- 4 routing

def must_not(t):
    return t["labels"]["must_not_auto_respond"]


def route_stats(rows, routes):
    """rows: list of R dicts; routes: list of route strings aligned."""
    n = len(rows)
    exp = [r["t"]["labels"]["expected_route"] for r in rows]
    dist = C.Counter(routes)
    match = sum(e == g for e, g in zip(exp, routes))
    viol = sum(must_not(r["t"]) and g == "auto_respond" for r, g in zip(rows, routes))
    n_mn = sum(must_not(r["t"]) for r in rows)
    esc_exp = sum(e == "escalate" for e in exp)
    nonauto_on_esc = sum(e == "escalate" and g != "auto_respond" for e, g in zip(exp, routes))
    esc_on_esc = sum(e == "escalate" and g == "escalate" for e, g in zip(exp, routes))
    auto_n = dist["auto_respond"]
    auto_good = sum(e == "auto_respond" and g == "auto_respond" for e, g in zip(exp, routes))
    return [n, f"{dist['auto_respond']}/{dist['review']}/{dist['escalate']}", fmt(match, n), f"{viol}/{n_mn}",
            fmt(nonauto_on_esc, esc_exp), fmt(esc_on_esc, esc_exp),
            "n/a" if auto_n == 0 else fmt(auto_good, auto_n)]


def sec_routing():
    h("4. Routing")
    labs = {t["labels"]["expected_route"] for t in T}
    print(f"expected_route values present in dev labels: {sorted(labs)}. `src/evaluation.py` scores routing as exact string equality of the route/action with expected_route, so the router's `review` outcome can never match a label: "
          f"every review-routed ticket counts as a routing miss, whatever its true merit.\n")
    art = CAL
    ib, ub = art["intent"]["blocks"], art["urgency"]["blocks"]
    hdr = ["policy simulated", "n", "auto/review/escalate", "routing acc (exact match)", "must_not violations (auto on must_not / n must_not)",
           "expected-escalate not auto-responded (handoff recall)", "expected-escalate routed 'escalate' (exact)", "precision of auto_respond"]

    def cls(r):
        return dict(intent=r["pi"], urgency=r["pu"], urgency_ambiguous=r["amb"], urgency_evidence_valid=r["ev"])

    def run(rows, mode):
        out = []
        for r in rows:
            c = cls(r)
            if mode == "none":
                cb = None
            elif mode == "calibrated":
                cb = dict(intent=predict_isotonic(ib, r["ic"]), urgency=predict_isotonic(ub, r["uc"]))
            elif mode == "raw":
                cb = dict(intent=r["ic"], urgency=r["uc"])
            elif mode == "raw_noamb":
                cb = dict(intent=r["ic"], urgency=r["uc"])
                c["urgency_ambiguous"] = False
                c["urgency_evidence_valid"] = True
            elif mode == "cal_noamb":
                cb = dict(intent=predict_isotonic(ib, r["ic"]), urgency=predict_isotonic(ub, r["uc"]))
                c["urgency_ambiguous"] = False
                c["urgency_evidence_valid"] = True
            out.append(route_ticket(c, calibrated_confidence=cb)["route"])
        return out

    modes = [("A. current deployment: no calibration artifact", "none"),
             ("B. calibration-v1 scores (urgency max 0.66)", "calibrated"),
             ("C. what-if: RAW confidences treated as calibrated @0.80", "raw"),
             ("D. what-if C with ambiguity/evidence gate disabled", "raw_noamb"),
             ("E. what-if B with ambiguity/evidence gate disabled", "cal_noamb")]
    for title, rows in (("All 341 classified (calibration was fitted on 251 of these; B/E are in-sample for the fit part)", R), ("Holdout 90 only (clean for B/E)", HO)):
        print(f"{title}\n")
        tab = []
        for name, m in modes:
            tab.append([name] + route_stats(rows, run(rows, m)))
        base_exp = C.Counter(r["t"]["labels"]["expected_route"] for r in rows)
        tab.append(["reference: always auto_respond"] + route_stats(rows, ["auto_respond"] * len(rows)))
        tab.append(["reference: always escalate"] + route_stats(rows, ["escalate"] * len(rows)))
        table(hdr, tab)
        print(f"Expected-route mix here: {dict(base_exp)}; must_not_auto_respond true: {sum(must_not(r['t']) for r in rows)}.\n")
    # what drives escalate in the current simulated policy
    ra = run(R, "none")
    print("Policy A route reasons (n=341): " + str(dict(C.Counter(
        "ambiguous/evidence" if (r['amb'] or not r['ev']) else "security_incident" if r['pi'] == 'security_incident' else "high urgency" if r['pu'] == 'high' else "no calibration" for r in R))) + "\n")
    # escalate calls vs gold
    esc = [(r, g) for r, g in zip(R, ra) if g == "escalate"]
    print(f"Policy A: {len(esc)} escalations; expected_route=escalate for {fmt(sum(r['t']['labels']['expected_route']=='escalate' for r, _ in esc), len(esc))}; "
          f"of the {sum(r['t']['labels']['expected_route']=='escalate' for r in R)} expected-escalate tickets, {sum(r['t']['labels']['expected_route']=='escalate' for r, _ in esc)} are escalated, "
          f"{sum(r['t']['labels']['expected_route']=='escalate' and g=='review' for r, g in zip(R, ra))} go to review.\n")
    # must_not tickets coverage by router rules
    mn = [r for r in R if must_not(r["t"])]
    print("must_not_auto_respond tickets (gold) by *predicted* intent and the rule that would catch them:\n")
    table(["gold intent", "n", "pred intent=security_incident", "pred urgency=high", "ambiguous/evidence-invalid", "caught by A (not auto and not needing calibration)"],
          [[c, len(m := [r for r in mn if r['gi'] == c]), sum(r['pi'] == 'security_incident' for r in m), sum(r['pu'] == 'high' for r in m),
            sum(r['amb'] or not r['ev'] for r in m),
            sum(g != 'auto_respond' for r, g in zip(R, ra) if r['gi'] == c and must_not(r['t']))] for c in sorted({r['gi'] for r in mn})])
    print("If a calibrated policy ever did auto-respond (mode C), these must_not tickets would be auto-responded, by gold intent:\n")
    rc = run(R, "raw")
    table(["gold intent", "n must_not", "auto-responded under C"],
          [[c, sum(r['gi'] == c for r in mn), sum(g == 'auto_respond' and r['gi'] == c for r, g in zip(R, rc) if must_not(r['t']))] for c in sorted({r['gi'] for r in mn})])

    # ---- label structure of expected_route (all 500 dev, hash split)
    print("### What determines expected_route in the dev labels (all 500 tickets; hash split fit/holdout by text)\n")
    print(f"must_not_auto_respond == (gold intent in security_incident/compliance_request/feature_request/unclear_request): "
          f"{all(must_not(t) == (t['labels']['intent'] in MN_INTENTS) for t in T)}; every must_not ticket has expected_route=escalate: "
          f"{all(t['labels']['expected_route']=='escalate' for t in T if must_not(t))}.\n")
    for name, f in (("urgency (gold)", lambda t: t["labels"]["urgency"]), ("answerable_from_docs", lambda t: t["labels"]["answerable_from_docs"]),
                    ("must_not_auto_respond", must_not), ("history.escalated", lambda t: t["history"]["escalated"]),
                    ("history.first_contact_resolution", lambda t: t["history"]["first_contact_resolution"]),
                    ("history.repeat_contact", lambda t: t["history"]["repeat_contact"]), ("history.csat_rating", lambda t: t["history"]["csat_rating"]),
                    ("customer_tier", lambda t: t["customer_tier"]), ("channel", lambda t: t["channel"])):
        d = C.defaultdict(C.Counter)
        for t in T:
            d[f(t)][t["labels"]["expected_route"]] += 1
        print(f"- {name}: " + "; ".join(f"{k}: {d[k]['escalate']}/{sum(d[k].values())} escalate" for k in sorted(d, key=str)))
    print()
    tr = [t for t in T if split_of(tkey(t)) == "fit"]
    te = [t for t in T if split_of(tkey(t)) == "holdout"]
    feats = {
        "constant (always auto_respond)": lambda t: 0,
        "urgency (gold)": lambda t: t["labels"]["urgency"],
        "intent (gold)": lambda t: t["labels"]["intent"],
        "intent x urgency (gold)": lambda t: (t["labels"]["intent"], t["labels"]["urgency"]),
        "customer_tier + channel": lambda t: (t["customer_tier"], t["channel"]),
        "history.csat_rating": lambda t: t["history"]["csat_rating"],
        "history.repeat_contact": lambda t: t["history"]["repeat_contact"],
        "answerable_from_docs": lambda t: t["labels"]["answerable_from_docs"],
        "must_not_auto_respond": must_not,
        "must_not OR not answerable": lambda t: must_not(t) or not t["labels"]["answerable_from_docs"],
        "history.escalated": lambda t: t["history"]["escalated"],
        "must_not x answerable x history.escalated": lambda t: (must_not(t), t["labels"]["answerable_from_docs"], t["history"]["escalated"]),
        "(must_not OR not answerable) x history.escalated": lambda t: (must_not(t) or not t["labels"]["answerable_from_docs"], t["history"]["escalated"]),
        "(must_not OR not answerable) x intent": lambda t: (must_not(t) or not t["labels"]["answerable_from_docs"], t["labels"]["intent"]),
    }
    rows = []
    for name, f in feats.items():
        mp = C.defaultdict(list)
        for t in tr:
            mp[f(t)].append(t["labels"]["expected_route"])
        glob = majority([t["labels"]["expected_route"] for t in tr], "auto_respond")
        pm = {k: majority(v) for k, v in mp.items()}
        pred = [pm.get(f(t), glob) for t in te]
        gold = [t["labels"]["expected_route"] for t in te]
        okn = sum(a == b for a, b in zip(pred, gold))
        tp = sum(a == b == "escalate" for a, b in zip(pred, gold))
        pp = sum(a == "escalate" for a in pred)
        pn = sum(b == "escalate" for b in gold)
        rows.append([name, fmt(okn, len(te)), fmt(tp, pp) if pp else "n/a (never predicts escalate)", fmt(tp, pn)])
    print(f"Single-lookup predictors of expected_route: majority class per feature value fitted on {len(tr)} fit-split tickets, scored on {len(te)} holdout tickets "
          f"(holdout escalate share {pct(sum(t['labels']['expected_route']=='escalate' for t in te), len(te))}). Features marked (gold) or label fields are NOT available to the classifier at run time.\n")
    table(["feature(s)", "holdout accuracy", "escalate precision", "escalate recall"], rows)
    res = [t for t in T if t["labels"]["expected_route"] == "escalate" and not must_not(t) and t["labels"]["answerable_from_docs"]]
    print(f"Escalations not explained by must_not or not-answerable: {len(res)} (intents {dict(C.Counter(t['labels']['intent'] for t in res))}; all history.escalated=True: {all(t['history']['escalated'] for t in res)}). "
          f"Among answerable, non-must_not database_issue/performance_degradation tickets with history.escalated=True: "
          f"{sum(t['labels']['expected_route']=='escalate' for t in T if t['labels']['intent'] in ('database_issue','performance_degradation') and t['labels']['answerable_from_docs'] and t['history']['escalated'])}/"
          f"{sum(1 for t in T if t['labels']['intent'] in ('database_issue','performance_degradation') and t['labels']['answerable_from_docs'] and t['history']['escalated'])} escalate.\n")
    print(f"history.escalated=False => expected_route=auto_respond in {sum(t['labels']['expected_route']=='auto_respond' for t in T if not t['history']['escalated'])}/{sum(not t['history']['escalated'] for t in T)} tickets. "
          f"Conflicting expected_route across identical texts: {sum(len({x['labels']['expected_route'] for x in v}) > 1 for v in GRP.values())} of {sum(len(v) > 1 for v in GRP.values())} repeated groups.\n")
    # runtime-available predictors, scored on the 90 classified holdout tickets, fitted on the 251 classified fit tickets
    def er(r):
        return r["t"]["labels"]["expected_route"]

    rt_feats = {
        "constant (always auto_respond)": lambda r: 0,
        "predicted urgency": lambda r: r["pu"],
        "predicted intent": lambda r: r["pi"],
        "predicted intent in {security, compliance, feature_request, unclear} (fixed rule, no fitting)": lambda r: r["pi"] in MN_INTENTS,
        "predicted intent x predicted urgency": lambda r: (r["pi"], r["pu"]),
        "gold intent (not runtime; ceiling of intent info)": lambda r: r["gi"],
    }
    rows = []
    for name, f in rt_feats.items():
        mp = C.defaultdict(list)
        for r in FIT:
            mp[f(r)].append(er(r))
        glob = majority([er(r) for r in FIT], "auto_respond")
        pm = {k: majority(v) for k, v in mp.items()}
        pred = [pm.get(f(r), glob) for r in HO]
        if "fixed rule" in name:
            pred = ["escalate" if f(r) else "auto_respond" for r in HO]
        gold = [er(r) for r in HO]
        okn = sum(a == b for a, b in zip(pred, gold))
        tp = sum(a == b == "escalate" for a, b in zip(pred, gold))
        pp = sum(a == "escalate" for a in pred)
        pn = sum(b == "escalate" for b in gold)
        rows.append([name, fmt(okn, len(HO)), fmt(tp, pp) if pp else "n/a", fmt(tp, pn)])
    print("Runtime-available predictors only (fit on the 251 classified fit tickets, score the 90 classified holdout; same data the classifier produced):\n")
    table(["predictor", "holdout accuracy", "escalate precision", "escalate recall"], rows)
    fixed = [("escalate" if r["pi"] in MN_INTENTS else "auto_respond") for r in R]
    print(f"The fixed 'predicted intent in the four must_not intents -> escalate' rule on all 341: accuracy {fmt(sum(a == er(r) for a, r in zip(fixed, R)), len(R))}.\n")
    # urgency's role: route by urgency high
    for lv in U:
        m = [t for t in T if t["labels"]["urgency"] == lv]
        print(f"- gold urgency={lv}: expected escalate {fmt(sum(t['labels']['expected_route']=='escalate' for t in m), len(m))}")
    print()
    # within non-must_not & answerable only
    m = [t for t in T if not must_not(t) and t["labels"]["answerable_from_docs"]]
    print(f"Within the {len(m)} answerable, non-must_not tickets (where routing is not forced by must_not/answerability), expected escalate share by gold urgency: "
          + "; ".join(f"{lv} {fmt(sum(t['labels']['expected_route']=='escalate' for t in m if t['labels']['urgency']==lv), sum(t['labels']['urgency']==lv for t in m))}" for lv in U) + "\n")


MN_INTENTS = {"security_incident", "compliance_request", "feature_request", "unclear_request"}


# ---------------------------------------------------------------- 5 probes

def sec_probes():
    h("5. Retrieval, citations and answerability (small probe files only)")
    pred_ids = {r["id"] for r in R}

    def load(name):
        return [json.loads(l) for l in open(RES / f"{name}.jsonl", encoding="utf-8") if l.strip()]

    tot_rows = []
    allids = {}
    for name in ("development_citation_probe", "development_citation_probe_v2", "development_citation_probe_v2_16"):
        rows = load(name)
        ids = [r["ticket_id"] for r in rows]
        allids[name] = ids
        elig = hits = cit_n = cit_ok = 0
        status = C.Counter()
        routes = C.Counter()
        ans_status = C.defaultdict(C.Counter)
        for r in rows:
            res = r["result"] or {}
            exp = r["expected"]
            docs = set(exp["expected_doc_ids"])
            retr = {s["doc_id"] for s in res.get("retrieved_sources", [])}
            cits = set(res.get("citations") or [])
            if exp["answerable_from_docs"] and docs:
                elig += 1
                hits += bool(docs & retr)
            cit_n += len(cits)
            cit_ok += len(cits & docs)
            status[res.get("answer_status")] += 1
            routes[res.get("route")] += 1
            ans_status[(exp["answerable_from_docs"], bool(exp["must_not_auto_respond"]))][res.get("answer_status")] += 1
        tot_rows.append([name, len(rows), f"{hits}/{elig}", f"{cit_ok}/{cit_n}", dict(status), dict(routes)])
    table(["file", "tickets", "retrieval hit (answerable)", "citation doc-ID matches / cited", "answer_status", "route"], tot_rows)
    print("Overlap of probe tickets with the 341-ticket calibration prediction set: "
          + ", ".join(f"{k}: {len(set(v) & pred_ids)}/{len(v)}" for k, v in allids.items()) + ".\n")
    # detailed per-ticket for union of v2 and v2_16
    rows = load("development_citation_probe_v2") + load("development_citation_probe_v2_16")
    print(f"Pooled latest-version probes (12 + 16 = {len(rows)} distinct tickets, all PR-03-v2 / qwen3.8-27b):\n")
    out = []
    elig = hits = 0
    first_doc_hit = 0
    for r in rows:
        res = r["result"] or {}
        exp = r["expected"]
        docs = exp["expected_doc_ids"]
        retr = [s["doc_id"] for s in res.get("retrieved_sources", [])]
        top = retr[0] if retr else None
        hit = bool(set(docs) & set(retr))
        if exp["answerable_from_docs"] and docs:
            elig += 1
            hits += hit
            first_doc_hit += top in docs
        out.append([r["ticket_id"], exp["answerable_from_docs"], ",".join(docs) or "-", "yes" if hit else "no", top, ",".join(res.get("citations") or []) or "-",
                    res.get("answer_status"), res.get("route"), exp["expected_route"], res.get("recommended_next_step") or "-"])
    table(["ticket", "answerable", "expected docs", "retrieval hit", "top-1 doc", "cited", "answer_status", "route", "expected_route", "next_step"], out)
    print(f"Pooled retrieval hit among answerable tickets with expected docs: {fmt(hits, elig)}; top-1 retrieved doc is an expected doc: {fmt(first_doc_hit, elig)}.\n")
    # status vs answerable
    d = C.defaultdict(C.Counter)
    for r in rows:
        res = r["result"] or {}
        d[r["expected"]["answerable_from_docs"]][res.get("answer_status")] += 1
    for k, v in d.items():
        print(f"- answerable_from_docs={k}: answer_status {dict(v)}")
    print()
    cit_ok = cit_n = 0
    drafted_unanswerable = 0
    for r in rows:
        res = r["result"] or {}
        cits = set(res.get("citations") or [])
        docs = set(r["expected"]["expected_doc_ids"])
        cit_n += len(cits)
        cit_ok += len(cits & docs)
        if res.get("answer_status") == "draft_ready" and not r["expected"]["answerable_from_docs"]:
            drafted_unanswerable += 1
    print(f"Pooled citation doc-ID match: {fmt(cit_ok, cit_n)} cited IDs equal an expected doc; drafts produced for tickets labelled not answerable: {drafted_unanswerable}.\n")
    # classification in probes
    ok_i = sum(r["result"]["intent"] == r["expected"]["intent"] for r in rows if r["result"])
    ok_u = sum(r["result"]["urgency"] == r["expected"]["urgency"] for r in rows if r["result"])
    print(f"Classification in the same 28 probes: intent {fmt(ok_i, len(rows))}, urgency {fmt(ok_u, len(rows))}.\n")
    # v3 comparison
    v3 = load("urgency_pr03_v3_16")
    v2 = {r["ticket_id"]: r for r in load("development_citation_probe_v2_16")}
    pair = [(v2[r["ticket_id"]]["result"], r["result"], r["expected"]) for r in v3 if r["result"]]
    a = sum(x["urgency"] == e["urgency"] for x, _, e in pair)
    b = sum(y["urgency"] == e["urgency"] for _, y, e in pair)
    print(f"PR-03-v3 vs v2 on the same {len(pair)} paired tickets (one v3 row failed validation): v2 urgency {a}/{len(pair)}, v3 {b}/{len(pair)}; both samples are far too small to distinguish prompts.\n")
    sp = load("urgency_spectrum_development")
    ok = sum(r["urgency"] == r["reference_urgency_offline_only"] for r in sp)
    print(f"urgency_spectrum_development: {len(sp)} tickets across {len({r['model'] for r in sp})} different free models (not a controlled run): urgency {ok}/{len(sp)} match; "
          f"ambiguous {sum(r['urgency_ambiguous'] for r in sp)}, evidence invalid {sum(not r['urgency_evidence_valid'] for r in sp)}. Excluded from quantitative conclusions.\n")

def label_sample(seed=17):
    """Stratified sample of urgency errors: all of the small off-diagonal cells, 14 from each large one
    (conflict-free tickets), plus one error per off-diagonal cell from conflicting-text tickets."""
    rng = random.Random(seed)
    cells = C.defaultdict(list)
    for r in sorted(CF, key=lambda r: r["id"]):
        if not r["uok"]:
            cells[(r["gu"], r["pu"])].append(r)
    out = []
    for key in sorted(cells):
        v = cells[key]
        out += v if len(v) <= 14 else rng.sample(v, 14)
    cc = C.defaultdict(list)
    for r in sorted(R, key=lambda r: r["id"]):
        if r["conflict"] and not r["uok"]:
            cc[(r["gu"], r["pu"])].append(r)
    for key in sorted(cc):
        out.append(rng.choice(cc[key]))
    return out


def sec_labels():
    h("6. Label quality")
    sample = label_sample()
    print(f"Sampled {len(sample)} urgency errors ({sum(not r['conflict'] for r in sample)} conflict-free, {sum(r['conflict'] for r in sample)} from conflicting-text groups).\n")
    if "--show" in sys.argv:
        for r in sample:
            t = r["t"]
            print(f"[{r['id']}] gold={r['gu']} pred={r['pu']} amb={r['amb']} conf={r['uc']} intent_gold={r['gi']} intent_pred={r['pi']} conflict={r['conflict']} copies={len(GRP[r['key']])} labels_in_group={sorted(x['labels']['urgency'] for x in GRP[r['key']])}")
            print(f"    subj: {t['subject']!r}\n    body: {t['body']!r}")
        return
    J = JUDGMENTS
    missing = [r["id"] for r in sample if r["id"] not in J]
    if missing:
        print("UNJUDGED:", missing)
    cnt = C.Counter(J[r["id"]][0] for r in sample if r["id"] in J)
    table(["judgment", "n (all)", "n (conflict-free)", "n (conflict group)"],
          [[k, cnt[k], sum(1 for r in sample if r["id"] in J and J[r["id"]][0] == k and not r["conflict"]),
            sum(1 for r in sample if r["id"] in J and J[r["id"]][0] == k and r["conflict"])] for k in "abc"])
    print("(a) gold consistent with the rubric, model wrong; (b) rubric-ambiguous / defensible either way; (c) gold contradicts the rubric.\n")
    rows = []
    for key in sorted({(r["gu"], r["pu"]) for r in sample}):
        m = [r for r in sample if (r["gu"], r["pu"]) == key and r["id"] in J]
        c = C.Counter(J[r["id"]][0] for r in m)
        rows.append([f"{key[0]} -> {key[1]}", len(m), c["a"], c["b"], c["c"]])
    table(["gold -> predicted", "n sampled", "a", "b", "c"], rows)
    cfs = [r for r in sample if not r["conflict"] and r["id"] in J]
    pop = C.Counter((r["gu"], r["pu"]) for r in CF if not r["uok"])
    tot_pop = sum(pop.values())
    est = {}
    for k in "abc":
        e = 0.0
        for key, npop in pop.items():
            m = [r for r in cfs if (r["gu"], r["pu"]) == key]
            e += npop * (sum(J[r["id"]][0] == k for r in m) / len(m)) if m else 0
        est[k] = e / tot_pop
    print(f"Stratum-weighted extrapolation to all {tot_pop} conflict-free urgency errors (error-cell sizes as weights; sample is {len(cfs)} tickets judged by a single reader, so treat as rough): "
          f"(a) {est['a']:.0%}, (b) {est['b']:.0%}, (c) {est['c']:.0%}.\n")
    for k in "abc":
        print(f"Examples ({k}):\n")
        by_id = {r["id"]: r for r in sample}
        for r in [by_id[i] for i in J if i in by_id and J[i][0] == k][:3]:
            t = r["t"]
            print(f"- {r['id']} gold={r['gu']} pred={r['pu']}: \"{(t['subject'] + ' ' + t['body']).strip()}\" -- {J[r['id']][1]}")
        print()
    # history vs urgency labels (observation only)
    print("### History fields vs gold urgency (observation only; all 500 dev tickets)\n")
    rows = []
    for u in U:
        m = [t for t in T if t["labels"]["urgency"] == u]
        rt = sorted(t["history"]["resolution_time_minutes"] for t in m)
        rows.append([u, len(m), f"{st.median(rt):.0f}", f"{rt[len(rt) // 4]}-{rt[3 * len(rt) // 4]}", f"{st.mean(t['history']['csat_rating'] for t in m):.2f}",
                     pct(sum(t['history']['escalated'] for t in m), len(m)), pct(sum(t['history']['first_contact_resolution'] for t in m), len(m)),
                     pct(sum(t['history']['repeat_contact'] for t in m), len(m))])
    table(["gold urgency", "n", "median resolution min", "IQR", "mean csat", "escalated", "first-contact resolved", "repeat contact"], rows)
    def auc(a, b):
        return sum(1 if x > y else .5 if x == y else 0 for x in a for y in b) / (len(a) * len(b))
    rt = lambda t: t["history"]["resolution_time_minutes"]
    out = []
    for a, b in (("high", "low"), ("high", "medium"), ("medium", "low")):
        out.append([f"{a} vs {b}", f"{auc([rt(t) for t in T if t['labels']['urgency'] == a], [rt(t) for t in T if t['labels']['urgency'] == b]):.3f}",
                    f"{auc([rt(t) for t in T if t['labels']['urgency'] == a and t['history']['escalated']], [rt(t) for t in T if t['labels']['urgency'] == b and t['history']['escalated']]):.3f}",
                    f"{auc([rt(t) for t in T if t['labels']['urgency'] == a and not t['history']['escalated']], [rt(t) for t in T if t['labels']['urgency'] == b and not t['history']['escalated']]):.3f}"])
    print("AUC of resolution_time_minutes separating urgency classes (0.5 = no relationship), overall and within escalated / non-escalated:\n")
    table(["pair", "all", "escalated only", "not escalated only"], out)
    print("Resolution time by history.escalated: median "
          f"{st.median(rt(t) for t in T if t['history']['escalated']):.0f} min (escalated, n={sum(t['history']['escalated'] for t in T)}) vs {st.median(rt(t) for t in T if not t['history']['escalated']):.0f} min (not escalated); "
          f"max non-escalated {max(rt(t) for t in T if not t['history']['escalated'])} min, min escalated {min(rt(t) for t in T if t['history']['escalated'])} min (disjoint ranges).\n")
    # urgency vs intent-only explained
    d = C.defaultdict(C.Counter)
    for t in T:
        d[t["labels"]["intent"]][t["labels"]["urgency"]] += 1
    ent = sum(max(v.values()) for v in d.values())
    print(f"Gold urgency is strongly tied to intent for a few intents (security_incident 92% high, rollback_request 82% high, api_usage_question 4% high) -- "
          f"predicting the majority urgency of the gold intent matches {fmt(ent, len(T))} of all 500 labels in-sample.\n")
    # same-text conflicts: do history/customer fields differ?
    n_diff = 0
    n_tot = 0
    for k, v in GRP.items():
        if CONFLICT[k]:
            n_tot += 1
            hi = [x for x in v if x["labels"]["urgency"] == "high"]
            lo = [x for x in v if x["labels"]["urgency"] == "low"]
            if hi and lo:
                n_diff += 1
    tiers = sum(1 for k, v in GRP.items() if CONFLICT[k] and len({x['customer_tier'] for x in v}) > 1)
    print(f"Conflicting-text groups: {n_tot}; {n_diff} contain both a high and a low label (two-level disagreement); {tiers} of {n_tot} have differing customer_tier across copies. "
          "Resolution-time AUC above is weak, so copies are not separable by an obvious history signal.\n")

# Single-reader judgments (author of this analysis) of 64 sampled urgency errors against the rubric in src/classification.py.
# a = gold consistent with rubric, model wrong; b = rubric-ambiguous / defensible either way; c = gold contradicts the rubric.
# Order matters: the first three ids per category are used as the representative examples in the report.
JUDGMENTS = {
    # --- c: gold contradicts the rubric
    "DEV-0044": ("c", "spend cap stopped a production workload overnight, 'raised immediately' = critical production unavailability, gold is low"),
    "DEV-0050": ("c", "plain billing question (service we do not use) with no harm or deadline, gold is high"),
    "DEV-0273": ("c", "'point me at the right starting place' is a routine onboarding question, gold is high"),
    "DEV-0211": ("c", "unrecognised activity and resources nobody created = active compromise, gold is medium"),
    "DEV-0092": ("c", "same spend-cap production stop as DEV-0044, gold is low (copy of the text is labelled medium)"),
    "DEV-0126": ("c", "all automated jobs failing to authenticate and 'help fast', gold is low"),
    "DEV-0206": ("c", "same scenario as DEV-0126, gold is low"),
    "DEV-0303": ("c", "production key returning 401 for two days, gold is low"),
    "DEV-0439": ("c", "connection pool exhausting under load, gold is low"),
    "DEV-0379": ("c", "webhook endpoint received no events since earlier today and 'urgent', gold is low"),
    "DEV-0425": ("c", "env var not visible to the app, no outage or deadline, gold is high"),
    "DEV-0165": ("c", "audit-log evidence request with no stated deadline, gold is high"),
    "DEV-0267": ("c", "latency climbing gradually, memory not at limit, gold is high"),
    "DEV-0095": ("c", "slow only at afternoon peak, fine otherwise, gold is high"),
    "DEV-0479": ("c", "single user locked out while colleague is fine (limited scope), gold is high"),
    "DEV-0471": ("c", "SSO auto-provisioning not working for new starters (limited), gold is high"),
    "DEV-0485": ("c", "one developer lacks project access, gold is high"),
    "DEV-0448": ("c", "question about retention options, gold is high"),
    "DEV-0174": ("c", "just signed up, where to start: routine question, gold is medium"),
    "DEV-0238": ("c", "which key type to use for CI: routine question, gold is medium"),
    "DEV-0233": ("c", "planned migration question, gold is medium"),
    "DEV-0226": ("c", "'point me at the right starting place', gold is medium"),
    "DEV-0296": ("c", "same as DEV-0226, gold is medium"),
    # --- b: rubric-ambiguous
    "DEV-0349": ("b", "'no connection available' errors after scale-up; production impact not stated, high or medium"),
    "DEV-0322": ("b", "identical text to DEV-0349"),
    "DEV-0472": ("b", "400 GB restore running since Friday, may be stalled; medium or high"),
    "DEV-0373": ("b", "'nothing loading properly today' has no scope; model flagged ambiguous and chose medium as the rubric directs"),
    "DEV-0149": ("b", "single-user lockout since Friday, 'blocking my work'; medium or high"),
    "DEV-0075": ("b", "all builds failing at dependency resolution, no code change; medium or high"),
    "DEV-0054": ("b", "all automated jobs failing to authenticate after password change; medium or high"),
    "DEV-0130": ("b", "every deployment fails health check; medium or high"),
    "DEV-0110": ("b", "EU residency for a contract being signed; deadline unstated"),
    "DEV-0445": ("b", "same text as DEV-0110, gold low in this copy"),
    "DEV-0219": ("b", "log forwarding stopped overnight; low or medium"),
    "DEV-0341": ("b", "same scenario as DEV-0219"),
    "DEV-0451": ("b", "restore running for hours, may be normal; low or medium"),
    "DEV-0336": ("b", "latency climbing over hours; low or medium"),
    "DEV-0438": ("b", "SSO provisioning 'have we missed a setting?'; low or medium (same scenario as DEV-0471 gold high)"),
    "DEV-0020": ("b", "same as DEV-0438"),
    "DEV-0285": ("b", "single-user console lockout; low or medium"),
    "DEV-0385": ("b", "past throttling incident, forward-looking config question; low or medium"),
    "DEV-0393": ("b", "offboarding access check; low or medium"),
    "DEV-0067": ("b", "webhook signature verification failing for every delivery; low or medium"),
    "DEV-0418": ("b", "'need someone to call us urgently' with no impact; rubric says urgent alone is not enough and unclear defaults to medium, low also defensible"),
    "DEV-0098": ("b", "release broke checkout for 'a portion' of customers; high or medium"),
    "DEV-0222": ("b", "key pushed to a public repo, careful replacement requested; high or medium"),
    "DEV-0269": ("b", "identical text to DEV-0222"),
    "DEV-0378": ("b", "connection-not-available errors after scale-up (gold medium here, high for DEV-0349)"),
    "DEV-0173": ("b", "billing period vs calendar month reconciliation; low or medium"),
    "DEV-0407": ("b", "invoice higher than usual, asks for explanation; low or medium"),
    "DEV-0415": ("b", "unexplained charges, asks for explanation; low or medium"),
    "DEV-0284": ("b", "same as DEV-0415"),
    "DEV-0034": ("b", "same as DEV-0407"),
    "DEV-0441": ("b", "expired export link, no way to regenerate; low or medium"),
    "DEV-0329": ("b", "same as DEV-0441"),
    "DEV-0123": ("b", "customer wants written confirmation of data location; deadline unstated"),
    "DEV-0058": ("b", "identical text to DEV-0123"),
    # --- a: gold consistent with the rubric, model wrong
    "DEV-0002": ("a", "one production key 401, other keys still work (workaround): medium; model said high"),
    "DEV-0397": ("a", "same as DEV-0002"),
    "DEV-0476": ("a", "same as DEV-0002 (copy of the text is labelled high)"),
    "DEV-0025": ("a", "health-check timeout, works in staging, production impact not stated: medium; model said high"),
    "DEV-0081": ("a", "identical text to DEV-0025"),
    "DEV-0136": ("a", "env var invisible to the app is a real current problem: medium; model said low"),
    "DEV-0295": ("a", "routine onboarding question with 'urgent' wording; low per rubric ('urgent alone is not enough'); model said medium with low confidence"),
}


def scenario_clusters(th=0.5):
    """Group tickets into paraphrase 'scenarios': same gold intent and content-word Jaccard >= th (union-find).
    Gold intent is used only as an analysis constraint (results are identical without it at th=0.5)."""
    import re
    stop = set("the a an and or to of in on is are was were we our i my it this that for with as at be by not no have has had can you please do does did "
               "from so if but will would could me us your their its they them there then than into out up about".split())

    def toks(t):
        return frozenset(w for w in re.findall(r"[a-z0-9]+", (t["subject"] + " " + t["body"]).lower()) if w not in stop and len(w) > 2)

    ids = [t["ticket_id"] for t in T]
    tk = {i: toks(BYID[i]) for i in ids}
    par = {i: i for i in ids}

    def find(x):
        while par[x] != x:
            par[x] = par[par[x]]
            x = par[x]
        return x

    for n, a in enumerate(ids):
        for b in ids[n + 1:]:
            if BYID[a]["labels"]["intent"] == BYID[b]["labels"]["intent"] and len(tk[a] & tk[b]) / len(tk[a] | tk[b]) >= th:
                par[find(a)] = find(b)
    cl = C.defaultdict(list)
    for i in ids:
        cl[find(i)].append(i)
    return list(cl.values())


def sec_scenarios():
    h("2b. Near-duplicate scenarios (paraphrase clusters) and the label ceiling")
    cl = scenario_clusters()
    big = [v for v in cl if len(v) > 1]
    ag = tot = 0
    for v in big:
        for x in range(len(v)):
            for y in range(x + 1, len(v)):
                tot += 1
                ag += BYID[v[x]]["labels"]["urgency"] == BYID[v[y]]["labels"]["urgency"]
    pr = {u: sum(t["labels"]["urgency"] == u for t in T) / len(T) for u in U}
    chance = sum(p * p for p in pr.values())
    cid = {i: n for n, v in enumerate(cl) for i in v}
    lab = lambda i: BYID[i]["labels"]["urgency"]

    def loo(i, pool_ids):
        pool = [lab(j) for j in pool_ids if j != i]
        return majority(pool) if pool else "medium"

    ceil = sum(max(C.Counter(lab(i) for i in v).values()) for v in cl)
    loo_ok = sum(lab(i) == loo(i, cl[cid[i]]) for i in (t["ticket_id"] for t in T))
    rm = [r for r in R]
    loo_r = sum(r["gu"] == loo(r["id"], cl[cid[r["id"]]]) for r in rm)
    loo_cf = sum(r["gu"] == loo(r["id"], cl[cid[r["id"]]]) for r in CF)
    table(["quantity", "value"], [
        ["scenario clusters among 500 dev tickets (Jaccard >= 0.5 on content words, same intent)", len(cl)],
        ["cluster size min / median / max", f"{min(map(len, cl))} / {st.median(map(len, cl))} / {max(map(len, cl))}"],
        ["clusters of size >1 containing more than one urgency label", f"{sum(len({lab(i) for i in v}) > 1 for v in big)}/{len(big)}"],
        ["pairwise urgency agreement of tickets in the same cluster", f"{ag / tot:.1%} ({ag}/{tot} pairs)"],
        ["agreement expected for two random tickets (sum p_i^2)", f"{chance:.1%}"],
        ["in-sample ceiling: predict each cluster's majority urgency (500 tickets)", fmt(ceil, len(T))],
        ["leave-one-out cluster-majority urgency, all 500 labels", fmt(loo_ok, len(T))],
        ["leave-one-out cluster-majority, the 341 classified tickets", fmt(loo_r, len(R))],
        ["leave-one-out cluster-majority, the 236 conflict-free classified tickets", fmt(loo_cf, len(CF))],
        ["PR-03-v2 on the same 341 / 236", f"{acc(R, 'uok')} / {acc(CF, 'uok')}"],
    ])
    print("Reading: clusters are paraphrase/noise variants of one scenario (typos, 'sorry for my english', changed durations). Two tickets in the same cluster agree on urgency barely more often than two random tickets, "
          "so the supplied urgency labels carry little scenario-level signal. A classifier that treats paraphrases alike cannot exceed roughly the in-sample ceiling and realistically sits near the leave-one-out figure.\n")
    # cluster-level table for biggest/most informative
    rows = []
    for v in sorted(big, key=len, reverse=True)[:12]:
        c = C.Counter(lab(i) for i in v)
        sample = BYID[v[0]]
        rows.append([len(v), sample["labels"]["intent"], f"{c['low']}/{c['medium']}/{c['high']}", (sample["subject"] + " " + sample["body"]).strip()[:70]])
    print("Twelve largest scenarios (labels shown as low/medium/high counts):\n")
    table(["size", "intent", "low/med/high", "text start"], rows)
    # model within-cluster behaviour
    cm = C.defaultdict(list)
    for r in R:
        cm[cid[r["id"]]].append(r)
    consistent = sum(len({r["pu"] for r in v}) == 1 for v in cm.values() if len(v) > 1)
    print(f"Model consistency across paraphrases: in {consistent}/{sum(len(v) > 1 for v in cm.values())} multi-ticket scenarios (among classified tickets) the model gives the same urgency to every variant.\n")
    g = C.defaultdict(list)
    for r in R:
        g[cid[r["id"]]].append(r)
    ierr = [v for v in g.values() if any(not r["iok"] for r in v)]
    allwrong = [v for v in ierr if all(not r["iok"] for r in v)]
    print(f"Intent errors are scenario-level: the 341 classified tickets span {len(g)} scenarios; all {sum(not r['iok'] for r in R)} intent errors fall in {len(ierr)} of them, "
          f"and {len(allwrong)} scenarios ({sum(len(v) for v in allwrong)} tickets) are wrong on every variant. Effective sample size for intent is therefore nearer 76 than 341.\n")
    rows = []
    for v in sorted(ierr, key=lambda v: -sum(not r["iok"] for r in v))[:10]:
        rows.append([len(v), sum(not r["iok"] for r in v), v[0]["gi"], dict(C.Counter(r["pi"] for r in v)), (v[0]["t"]["subject"] + " " + v[0]["t"]["body"]).strip()[:70]])
    table(["tickets", "intent errors", "gold intent", "predicted (counts)", "text start"], rows)
    fit_clusters = {cid[r["id"]] for r in FIT}
    leak = sum(cid[r["id"]] in fit_clusters for r in HO)
    print(f"Split leakage: {leak}/{len(HO)} holdout tickets belong to a scenario cluster that also has classified tickets in the fit split "
          f"({len({cid[r['id']] for r in HO} & fit_clusters)} of {len({cid[r['id']] for r in HO})} holdout scenarios). The hash split separates identical texts only, not paraphrases, "
          f"so anything fitted on `fit` (few-shot examples, per-intent/per-scenario priors, thresholds) is evaluated on paraphrases of its own training material.\n")
    n1, n2 = len(FIT), len(HO)
    p1, p2 = sum(r["uok"] for r in FIT) / n1, sum(r["uok"] for r in HO) / n2
    pp = (sum(r["uok"] for r in FIT) + sum(r["uok"] for r in HO)) / (n1 + n2)
    z = (p2 - p1) / math.sqrt(pp * (1 - pp) * (1 / n1 + 1 / n2))
    print(f"The model itself is never fitted, yet its urgency accuracy is {p1:.1%} on the fit split and {p2:.1%} on the holdout (z = {z:.2f}): the 90-ticket holdout is a noisy, somewhat easier slice, "
          f"so 55.6% should not be read as the expected accuracy.\n")
    # feature conditioning inside clusters (negative result)
    def loo_cond(keyf):
        ok = 0
        for t in T:
            i = t["ticket_id"]
            pool = [j for j in cl[cid[i]] if j != i and keyf(BYID[j]) == keyf(t)] or [j for j in cl[cid[i]] if j != i]
            ok += lab(i) == (majority([lab(j) for j in pool]) if pool else "medium")
        return ok
    rows = [["cluster only", fmt(loo_ok, len(T))]]
    for name, f in (("+ history.escalated", lambda t: t["history"]["escalated"]), ("+ customer_tier", lambda t: t["customer_tier"]), ("+ channel", lambda t: t["channel"]),
                    ("+ language_fluency", lambda t: t["language_fluency"]), ("+ subject line", lambda t: t["subject"]), ("+ csat_rating", lambda t: t["history"]["csat_rating"]),
                    ("+ repeat_contact", lambda t: t["history"]["repeat_contact"])):
        rows.append([name, fmt(loo_cond(f), len(T))])
    print("Does any other field explain urgency *within* a scenario? Leave-one-out majority using same-cluster tickets that also share the field value (fallback: whole cluster):\n")
    table(["conditioning", "LOO accuracy (500)"], rows)
    print("No field improves on the cluster alone (splitting small pools mostly adds noise), so within-scenario label variation is not explained by anything observed here. This is observation only, not proof the labels are random.\n")


def main():
    secs = {"data": sec_data, "intent": sec_intent, "urgency": sec_urgency, "joint": sec_joint, "routing": sec_routing, "probes": sec_probes,
            "scenarios": sec_scenarios, "labels": sec_labels}
    want = [a for a in sys.argv[1:] if not a.startswith('--')] or list(secs)
    for w in want:
        secs[w]()


if __name__ == "__main__":
    main()
