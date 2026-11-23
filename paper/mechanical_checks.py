#!/usr/bin/env python3
"""Mechanical checks for the SagarVaani IEEE manuscript (master-prompt section 12).
Run:  python -I mechanical_checks.py
Validates citation/bib consistency, label/ref resolution, brace and environment
balance, placeholder residue, DOI verification, and empirical-number traceability.
Exits non-zero if any hard check fails.
"""
import re, sys, pathlib

ROOT = pathlib.Path(__file__).resolve().parent
TEX  = ROOT / "templates/ieee_conference/template.tex"
BIB  = ROOT / "templates/ieee_conference/references.bib"
LOG  = ROOT / "raw_materials/experimental_log.md"
CVL  = ROOT / "raw_materials/citation_verification_log.md"

tex = TEX.read_text(encoding="utf-8")
bib = BIB.read_text(encoding="utf-8")
log = LOG.read_text(encoding="utf-8")
cvl = CVL.read_text(encoding="utf-8")

fails, warns, oks = [], [], []
def ok(m): oks.append(m)
def fail(m): fails.append(m)
def warn(m): warns.append(m)

# strip comment lines for text-level checks (keep % that is escaped \%)
def strip_comments(s):
    out = []
    for line in s.splitlines():
        # remove unescaped % to end of line
        line = re.sub(r'(?<!\\)%.*$', '', line)
        out.append(line)
    return "\n".join(out)
tex_nc = strip_comments(tex)

# 1. Citations vs bibliography
cite_keys = set()
for m in re.finditer(r'\\cite\{([^}]*)\}', tex_nc):
    for k in m.group(1).split(','):
        if k.strip(): cite_keys.add(k.strip())
bib_keys = set(re.findall(r'@\w+\{\s*([^,\s]+)\s*,', bib))
missing = cite_keys - bib_keys
uncited = bib_keys - cite_keys
if missing: fail(f"\\cite keys with no bib entry: {sorted(missing)}")
else: ok(f"all {len(cite_keys)} cited keys exist in references.bib")
if uncited: fail(f"bib entries never cited: {sorted(uncited)}")
else: ok(f"all {len(bib_keys)} bib entries are cited")

# 2. Labels vs references
labels = set(re.findall(r'\\label\{([^}]*)\}', tex_nc))
refs = set()
for pat in (r'\\ref\{([^}]*)\}', r'\\eqref\{([^}]*)\}'):
    refs |= set(re.findall(pat, tex_nc))
unresolved = refs - labels
if unresolved: fail(f"\\ref/\\eqref to missing label: {sorted(unresolved)}")
else: ok(f"all {len(refs)} refs resolve to one of {len(labels)} labels")
unused_lbl = labels - refs
if unused_lbl: warn(f"labels never referenced: {sorted(unused_lbl)}")

# 3. External figure files exist (TikZ is inline -> expect none)
gfx = re.findall(r'\\includegraphics(?:\[[^\]]*\])?\{([^}]*)\}', tex_nc)
missing_gfx = [g for g in gfx if not (TEX.parent / g).exists() and not (TEX.parent / (g + '.pdf')).exists()]
if missing_gfx: fail(f"\\includegraphics missing files: {missing_gfx}")
else: ok(f"figures: {len(gfx)} external image(s); inline TikZ figures used otherwise")

# 4. Brace balance (ignore escaped \{ \})
no_esc = re.sub(r'\\[{}]', '', tex)
nopen, nclose = no_esc.count('{'), no_esc.count('}')
if nopen != nclose: fail(f"unbalanced braces: {{={nopen}  }}={nclose}")
else: ok(f"braces balanced ({nopen} pairs)")

# 5. Environment matching
stack, env_err = [], False
for m in re.finditer(r'\\(begin|end)\{([^}]*)\}', tex_nc):
    kind, env = m.group(1), m.group(2)
    if kind == 'begin': stack.append(env)
    else:
        if not stack or stack[-1] != env:
            fail(f"environment mismatch at \\end{{{env}}} (stack top: {stack[-1] if stack else 'empty'})")
            env_err = True; break
        stack.pop()
if not env_err:
    if stack: fail(f"unclosed environments: {stack}")
    else: ok("all LaTeX environments open/close correctly")

# 6. Placeholder residue (non-comment text only)
placeholders = re.findall(r'(TODO|TBD|XXX|\[AUTHORS[^\]]*\]|\[CONFERENCE[^\]]*\]|DRAFT PENDING|FIXME|PLACEHOLDER)', tex_nc)
if placeholders: fail(f"placeholder tokens remain in body: {sorted(set(placeholders))}")
else: ok("no author/affiliation/placeholder residue in body text")

# 7. DOI verification: every bib DOI must be in the verified-log set
bib_dois = set(d.strip().lower() for d in re.findall(r'doi\s*=\s*\{([^}]*)\}', bib))
verified = set(d.lower() for d in re.findall(r'10\.\d{4,9}/[^\s|)\]]+', cvl))
unverified = {d for d in bib_dois if d not in verified}
if unverified: fail(f"bib DOIs not present in citation_verification_log: {sorted(unverified)}")
else: ok(f"all {len(bib_dois)} bib DOIs appear in the Crossref-verified log")

# 8. Empirical-number traceability (key numbers must appear in experimental_log)
numbers = ["62", "85", "23", "820", "3.13.6", "8.3", "8354"]
present = [n for n in numbers if n in log]
# only flag numbers that are actually used in the tex
used = [n for n in numbers if n in tex_nc]
untraced = [n for n in used if n not in log]
if untraced: fail(f"numbers used in tex but absent from experimental_log.md: {untraced}")
else: ok(f"empirical numbers used in tex ({', '.join(used)}) all trace to experimental_log.md")

# 9. Honesty guard: no 'outperform/state-of-the-art/superior' claims
banned = re.findall(r'\b(outperform\w*|state-of-the-art|superior to|beats the baseline)\b', tex_nc, re.I)
if banned: fail(f"unsupported comparative claim(s): {sorted(set(x.lower() for x in banned))}")
else: ok("no 'outperforms/SOTA' comparative claims present")

# --- report ---
print("="*64)
print("SagarVaani manuscript — mechanical checks")
print("="*64)
for m in oks:  print(f"  PASS  {m}")
for m in warns:print(f"  WARN  {m}")
for m in fails:print(f"  FAIL  {m}")
print("-"*64)
print(f"  {len(oks)} passed, {len(warns)} warnings, {len(fails)} failures")
sys.exit(1 if fails else 0)
