#!/usr/bin/env python3
"""convert-doc.py — Stage 1 of the doc→ingest pipeline (agentic-knowledge-management).

Deterministic RAW conversion of a source document to Markdown via `markit`,
with format pre-handling for legacy/macro formats and an optional `pandoc`
reference output used by the QC stage to measure conversion fidelity.

This script does NO judgement work. It only produces bytes. All quality
control, annotation, and approval happen in later stages (see SKILL.md).

Usage:
  "$CLAUDE_PLUGIN_ROOT/skills/doc-pipeline/convert-doc.py" <source-file> [--out-dir DIR] [--no-ref] [--keep-images]

Output (relative to the current vault root):
  <out-dir>/<slug>.md             raw markdown (markit)
  <out-dir>/_ref/<slug>.ref.md    pandoc reference (docx/doc/html/epub only)

Defaults: out-dir = <vault>/.raw/_staging   (override with --out-dir for custom layouts,
          e.g. a vault that stages under .raw/training/_staging)

Format handling:
  .docx .pdf .pptx .xlsx .html .epub .csv ...  → markit directly
  .doc   (legacy OLE2)  → textutil → .docx → markit   (+ pandoc reference)
  .pptm  (macro PPTX)   → copied to .pptx            → markit
  .xls   (legacy)       → attempted directly, warns if unsupported
"""

import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

# ---- vault root via plugin-wide resolver (PR0): KM_VAULT_PATH env → cwd ----
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent / "lib"))
from vault_root import resolve_vault_root  # noqa: E402


def err(msg: str) -> None:
    print(msg, file=sys.stderr)


def derive_slug(stem: str) -> str:
    """Replicate the shell slug derivation:
      lowercase | ' '/'_' → '-' | strip non [a-z0-9äöüß-] | collapse '-' | trim '-'
    """
    slug = stem.lower()
    slug = slug.replace(" ", "-").replace("_", "-")
    slug = re.sub(r"[^a-z0-9äöüß-]+", "", slug)
    slug = re.sub(r"-+", "-", slug)
    slug = slug.strip("-")
    return slug or "doc"


def main(argv: list[str]) -> int:
    root = resolve_vault_root()

    # ---- args ----
    if not argv:
        err("usage: convert-doc.py <source-file> [--out-dir DIR] [--no-ref] [--keep-images]")
        return 2
    src = argv[0]
    rest = argv[1:]

    out_dir = str(root / ".raw" / "_staging")
    make_ref = True
    keep_images = False
    i = 0
    while i < len(rest):
        arg = rest[i]
        if arg == "--out-dir":
            out_dir = rest[i + 1]
            i += 2
        elif arg == "--no-ref":
            make_ref = False
            i += 1
        elif arg == "--keep-images":
            keep_images = True
            i += 1
        else:
            err(f"unknown arg: {arg}")
            return 2

    if not Path(src).is_file():
        err(f"ERROR: source not found: {src}")
        return 1
    if shutil.which("markit") is None:
        err("ERROR: markit not installed (npm i -g markit-ai / brew install markit?)")
        return 1

    # ---- derive a clean slug from the filename ----
    base = os.path.basename(src)
    stem, dot, ext_raw = base.rpartition(".")
    if not dot:
        # no extension: bash `${base%.*}` == base, `${base##*.}` == base
        stem = base
        ext = base.lower()
    else:
        ext = ext_raw.lower()
    slug = derive_slug(stem)

    out_path_dir = Path(out_dir)
    (out_path_dir / "_ref").mkdir(parents=True, exist_ok=True)
    out = out_path_dir / f"{slug}.md"
    ref = out_path_dir / "_ref" / f"{slug}.ref.md"

    tmp_base = os.environ.get("TMPDIR", "/tmp")
    work = Path(tempfile.mkdtemp(prefix="markit-conv.", dir=tmp_base))
    try:
        return _convert(
            src, base, stem, ext, slug, root, out, ref, work,
            make_ref, keep_images,
        )
    finally:
        shutil.rmtree(work, ignore_errors=True)


def _convert(src, base, stem, ext, slug, root, out, ref, work,
             make_ref, keep_images) -> int:
    # ---- normalize source into a markit-friendly file ----
    markit_src = src
    pre = ""
    if ext == "doc":
        # Legacy Word (OLE2): neither markit nor pandoc read it. textutil → docx (macOS).
        # Shell redirect (not -output) avoids the macOS provenance flag blocking textutil.
        if shutil.which("textutil") is not None:
            docx_path = work / f"{slug}.docx"
            with open(docx_path, "wb") as fh:
                subprocess.run(
                    ["textutil", "-convert", "docx", "-stdout", src],
                    stdout=fh, check=True,
                )
            markit_src = str(docx_path)
            pre = "textutil .doc→.docx"
        elif shutil.which("libreoffice") is not None:
            subprocess.run(
                ["libreoffice", "--headless", "--convert-to", "docx",
                 "--outdir", str(work), src],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            )
            markit_src = str(work / f"{stem}.docx")
            pre = "libreoffice .doc→.docx"
        else:
            err("ERROR: .doc needs textutil (macOS) or libreoffice.")
            return 1
    elif ext == "pptm":
        dest = work / f"{slug}.pptx"
        shutil.copy(src, dest)
        markit_src = str(dest)
        pre = "copy .pptm→.pptx"
    elif ext == "xls":
        err("WARN: legacy .xls may be unsupported by markit; attempting directly.")
        pre = "legacy .xls (best effort)"

    # ---- primary conversion (markit) ----
    # NOTE: markit's -q/-i/-o are GLOBAL options and must precede the source.
    # The `convert` subcommand form silently ignores -o, so we use the default command.
    print(f"→ markit convert: {base}" + (f"  [{pre}]" if pre else ""))
    result = subprocess.run(
        ["markit", "-q", "-i", str(work / "img"), "-o", str(out), markit_src]
    )
    if result.returncode != 0:
        err(f"ERROR: markit failed on {base}")
        return 1

    # ---- clean up broken/temporary local image links ----
    # markit extracts images to a temp dir we discard, leaving dead absolute paths.
    # Replace them with a REVIEW marker that preserves the alt text so the QC stage
    # can decide whether the image mattered.
    if not keep_images and out.exists() and out.stat().st_size > 0:
        text = out.read_text(encoding="utf-8")

        def _repl(m: "re.Match") -> str:
            alt = m.group(1)
            return (
                f'<!-- REVIEW[image|info]: Bild im Original entfernt '
                f'(alt: "{alt}") - bei Relevanz manuell ergaenzen -->'
            )

        text = re.sub(
            r"!\[([^\]]*)\]\((?!https?://)[^)]*\)",
            _repl,
            text,
        )
        out.write_text(text, encoding="utf-8")

    # ---- reference conversion (pandoc) for the fidelity diff ----
    if make_ref and shutil.which("pandoc") is not None:
        ref_src = ""
        ref_fmt = ""
        if ext == "docx":
            ref_src, ref_fmt = src, "docx"
        elif ext == "doc":
            ref_src, ref_fmt = markit_src, "docx"
        elif ext in ("html", "htm"):
            ref_src, ref_fmt = src, "html"
        elif ext == "epub":
            ref_src, ref_fmt = src, "epub"
        if ref_src:
            pandoc_res = subprocess.run(
                ["pandoc", "-f", ref_fmt, "-t", "markdown", ref_src, "-o", str(ref)],
                stderr=subprocess.DEVNULL,
            )
            if pandoc_res.returncode == 0:
                print(f"→ pandoc reference: {_relto(ref, root)}")
            else:
                err("WARN: pandoc reference failed (non-fatal)")
                try:
                    ref.unlink()
                except FileNotFoundError:
                    pass
        else:
            print(f"ℹ no pandoc reference for .{ext} — QC must compare raw MD vs. the original")

    # ---- summary ----
    out_text = out.read_text(encoding="utf-8")
    words = len(out_text.split())
    lines = out_text.count("\n")
    print(f"✓ raw markdown: {_relto(out, root)}  ({lines} lines, {words} words)")
    if ref.exists():
        print(f"  reference:    {_relto(ref, root)}")
    print()
    print("Next: QC stage annotates this file in place (see the doc-pipeline skill), then")
    print("      set 'status: approved' in its PIPELINE-REVIEW header and run finalize-md.py.")
    return 0


def _relto(path: Path, root: Path) -> str:
    """Mimic shell `${VAR#$ROOT/}` — strip a leading "<root>/" prefix if present."""
    prefix = f"{root}/"
    s = str(path)
    return s[len(prefix):] if s.startswith(prefix) else s


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
