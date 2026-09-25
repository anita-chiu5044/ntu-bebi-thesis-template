#!/usr/bin/env python3
"""Compile disposable regression fixtures; never fills in the author's metadata.

Run with XeLaTeX, latexmk, the bibliography backend, and pypdf available:
    python -m pip install pypdf==6.10.0
    python scripts/check_template.py

All synthetic metadata, bibliographic records, and unsigned verification pages
exist only in a temporary directory by default. --preview-dir can preserve
explicitly named SYNTHETIC-TEST-ONLY PDFs for visual QA, never for submission.
"""

from pathlib import Path
import argparse
import re
import shutil
import subprocess
import tempfile

from pypdf import PdfReader, PdfWriter
from pypdf.generic import ContentStream, DecodedStreamObject


ROOT = Path(__file__).resolve().parents[1]
GENERATED = (
    ".git", ".github", "build", "__pycache__", "*.aux", "*.bbl", "*.bcf",
    "*.blg", "*.fdb_latexmk", "*.fls", "*.log", "*.run.xml", "*.synctex.gz",
    "*.toc", "*.lof", "*.lot", "*.out", "*.xdv", "main.pdf", "draft.pdf", "final.pdf",
)


def check(condition, message):
    if not condition:
        raise AssertionError(message)


def compile_tex(directory, entry, expected_error=None):
    command = ["latexmk", "-xelatex", "-halt-on-error", "-interaction=nonstopmode",
               "-file-line-error", entry]
    result = subprocess.run(command, cwd=directory, text=True,
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                            timeout=240)
    log = directory / (Path(entry).stem + ".log")
    details = result.stdout + (log.read_text(errors="replace") if log.exists() else "")
    if expected_error is not None:
        check(result.returncode != 0, f"{entry} unexpectedly compiled despite {expected_error}")
        check(expected_error in details,
              f"{entry} failed for the wrong reason; wanted {expected_error}:\n{details[-7000:]}")
        return details
    log_text = log.read_text(errors="replace") if log.exists() else ""
    check(result.returncode == 0,
          f"{entry} failed to compile:\n{result.stdout[-8000:]}\n{log_text[-4000:]}")
    check("Missing character:" not in details, "A required character is missing from the PDF font")
    check("undefined references" not in (log.read_text(errors="replace") if log.exists() else ""),
          "The final compiler pass has unresolved references")
    return details


def copy_fixture(parent, name):
    target = parent / name
    shutil.copytree(ROOT, target, ignore=shutil.ignore_patterns(*GENERATED))
    return target


def pdf(directory, name="main"):
    reader = PdfReader(directory / f"{name}.pdf")
    for page in reader.pages:
        check(abs(float(page.mediabox.width) - 595.28) < 1,
              "A page is not A4 width")
        check(abs(float(page.mediabox.height) - 841.89) < 1,
              "A page is not A4 height")
    return reader, "\n".join(page.extract_text() or "" for page in reader.pages)


def toc_page(directory, title, name="main"):
    content = (directory / f"{name}.toc").read_text()
    matches = re.findall(r"\\contentsline \{chapter\}\{" + re.escape(title)
                         + r"\}\{([^}]+)\}", content)
    check(len(matches) == 1, f"Expected exactly one TOC entry for {title}: {content}")
    return matches[0]


def roman(number):
    result = ""
    for value, token in ((1000, "m"), (900, "cm"), (500, "d"), (400, "cd"),
                         (100, "c"), (90, "xc"), (50, "l"), (40, "xl"),
                         (10, "x"), (9, "ix"), (5, "v"), (4, "iv"), (1, "i")):
        while number >= value:
            result += token
            number -= value
    return result


def configure_synthetic_fixture(directory):
    """Supply synthetic, isolated content solely to exercise successful final builds."""
    with (directory / "ntusetup.tex").open("a") as stream:
        stream.write(r"""
% SYNTHETIC REGRESSION FIXTURE ONLY. NOT A THESIS OR AN ASSIGNED DOI.
\ntusetup{
 title={排版回歸測試}, title*={Synthetic Layout Validation},
 author={測試作者}, author*={Synthetic Author}, ID={TEST-ONLY},
 advisor={測試指導者}, advisor*={Synthetic Advisor},
 date={2026-09-26}, oral-date={2026-09-25},
 DOI={10.0000/synthetic-unassigned-test-only},
 keywords={排版,測試,分頁,目次,引用},
 keywords*={layout,testing,pagination,contents,citations}}
""")
    (directory / "front/acknowledgement.tex").write_text(
        r"\begin{acknowledgement}排版測試。\end{acknowledgement}" + "\n")
    (directory / "front/abstract.tex").write_text(
        r"\begin{abstract}中文摘要排版測試。\end{abstract}" + "\n"
        r"\begin{abstract*}Synthetic abstract for layout validation.\end{abstract*}" + "\n")
    for number in range(1, 9):
        content = rf"\chapter{{Synthetic Chapter {number}}}" + "\n"
        if number == 1:
            content += (r"\typeout{BEBI-TEST-BASELINE=\the\baselineskip}" + "\n"
                        r"Synthetic body text with a citation~\cite{layoutFixture}." + "\n"
                        r"\textcolor{red}{Monochrome mode probe.}" + "\n")
        else:
            content += "Synthetic body text for pagination validation.\n"
        (directory / f"contents/chapter{number:02}.tex").write_text(content)
    (directory / "back/appendix01.tex").write_text(
        r"\chapter{Synthetic Appendix}Synthetic appendix content." + "\n")
    (directory / "back/references.bib").write_text("""@misc{layoutFixture,
  author = {{Template Regression Test}},
  title = {Synthetic bibliography retention check},
  year = {2026},
  note = {Synthetic test record, not a scientific source}
}
""")


def check_pagination(directory, name="main", verification_pages=0):
    reader, text = pdf(directory, name)
    labels = reader.page_labels
    first_roman = labels.index("i")
    first_body = labels.index("1", first_roman + 1)
    front_labels = labels[first_roman:first_body]
    check(front_labels == [roman(n) for n in range(1, len(front_labels) + 1)],
          f"Roman front-matter numbering is not continuous: {front_labels}")
    check(labels[first_body:] == [str(n) for n in range(1, len(labels) - first_body + 1)],
          "Body, bibliography, and appendix must continue Arabic numbering from 1")
    check(toc_page(directory, "誌謝", name) == roman(verification_pages + 1),
          "Acknowledgements have the wrong Roman page number")
    check(toc_page(directory, "摘要", name) == roman(verification_pages + 2),
          "Chinese abstract has the wrong Roman page number")
    check(toc_page(directory, "ABSTRACT", name) == roman(verification_pages + 3),
          "English abstract has the wrong Roman page number")
    for title in ("目次", "圖次", "表次"):
        check(toc_page(directory, title, name) in front_labels,
              f"{title} is missing or has an invalid front-matter page")
    toc = (directory / f"{name}.toc").read_text()
    check(r"\numberline {1}Synthetic Chapter 1" in toc,
          "The optional verification letter changed the first body chapter number")
    if verification_pages:
        check(toc_page(directory, "口試委員審定書", name) == "i",
              "Included verification letter must appear once at Roman i")
    else:
        check("口試委員審定書" not in toc,
              "Omitted verification letter must also be omitted from the TOC")
    check("Synthetic bibliography retention check" in text,
          "The bibliography disappeared from the rendered document")
    return reader, text, first_roman


def override(directory, text):
    with (directory / "ntusetup.tex").open("a") as stream:
        stream.write("\n" + text + "\n")


def check_monochrome_text(reader):
    # Check page-level LaTeX colors, including a deliberately red test command.
    # External figures, PDFs, and the official watermark still need visual review.
    for page in reader.pages:
        contents = page.get_contents()
        if contents is None:
            continue
        for operands, operator in ContentStream(contents, reader).operations:
            if operator in (b"rg", b"RG"):
                values = [float(value) for value in operands]
                check(max(values) - min(values) < 0.0001,
                      "Final mode contains colored LaTeX text or rules")
            elif operator in (b"k", b"K"):
                check(all(abs(float(value)) < 0.0001 for value in operands[:3]),
                      "Final mode contains colored LaTeX text or rules")


def check_graphics_resources(reader):
    """Catch invalid first-page opacity resources even when TeX exits successfully."""
    def inspect(stream, resources, seen):
        resources = resources.get_object()
        states = resources.get("/ExtGState", {})
        states = states.get_object() if hasattr(states, "get_object") else states
        forms = resources.get("/XObject", {})
        forms = forms.get_object() if hasattr(forms, "get_object") else forms
        half_opacity = False
        for operands, operator in ContentStream(stream, reader).operations:
            if operator == b"gs":
                key = operands[0]
                check(key in states, f"PDF references an undefined graphics-state resource: {key}")
                state = states[key].get_object()
                half_opacity |= any(abs(float(state.get(key, 1)) - 0.5) < 0.0001
                                    for key in ("/ca", "/CA"))
            elif operator == b"Do":
                key = operands[0]
                check(key in forms, f"PDF references an undefined graphic resource: {key}")
                form = forms[key].get_object()
                if form.get("/Subtype") == "/Form" and id(form) not in seen:
                    seen.add(id(form))
                    half_opacity |= inspect(form, form.get("/Resources", resources), seen)
        return half_opacity

    return [inspect(page.get_contents(), page["/Resources"], set())
            if page.get_contents() is not None else False for page in reader.pages]


def run_checks(preview_dir=None):
    def preserve_preview(directory, label):
        if preview_dir is not None:
            target = Path(preview_dir).resolve()
            target.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(directory / "final.pdf", target / f"SYNTHETIC-TEST-ONLY-{label}-visual.pdf")

    for executable in ("latexmk", "xelatex", "biber"):
        check(shutil.which(executable), f"Required compiler tool is unavailable: {executable}")
    with tempfile.TemporaryDirectory(prefix="bebi-template-test-") as temporary:
        parent = Path(temporary)
        draft = copy_fixture(parent, "draft")
        compile_tex(draft, "main.tex")
        _, draft_text = pdf(draft)
        check("Draft" in draft_text, "Draft mode must clearly label its preview")
        check("Biomedical" in draft_text or "biomedical" in draft_text,
              "The biomedical thesis skeleton is absent")
        print("PASS: shipped draft compiles with its visible placeholders", flush=True)

        clean = copy_fixture(parent, "synthetic-final")
        configure_synthetic_fixture(clean)
        log = compile_tex(clean, "final.tex")
        baseline = re.search(r"BEBI-TEST-BASELINE=([0-9.]+)pt", log)
        check(baseline and 23.0 <= float(baseline[1]) <= 25.0,
              "English body text is not double spaced at 12pt")
        reader, text, first_roman = check_pagination(clean, "final")
        check_monochrome_text(reader)
        check(all(check_graphics_resources(reader)),
              "Every electronic final page needs a valid 50-percent-opacity watermark")
        check("Draft" not in text and "TODO" not in text and "初稿" not in text,
              "A final PDF still contains draft markers")
        for page in reader.pages:
            check("10.0000/synthetic-unassigned-test-only" in (page.extract_text() or ""),
                  "A non-verification page is missing the final DOI overlay")
        preserve_preview(clean, "final")
        print("PASS: final layout, Roman/Arabic sequence, TOC, double spacing and bibliography", flush=True)

        letter = copy_fixture(parent, "synthetic-letter")
        configure_synthetic_fixture(letter)
        writer = PdfWriter()
        for _ in range(2):
            page = writer.add_blank_page(width=595.276, height=841.89)
            content = DecodedStreamObject()
            content.set_data(b"q Q\n")
            page.replace_contents(content)
        with (letter / "front/verification.pdf").open("wb") as stream:
            writer.write(stream)
        override(letter, r"\bebisetup{verification=true}")
        compile_tex(letter, "final.tex")
        reader, _, first_roman = check_pagination(letter, "final", verification_pages=2)
        opacity = check_graphics_resources(reader)
        for index, page in enumerate(reader.pages):
            has_doi = "10.0000/synthetic-unassigned-test-only" in (page.extract_text() or "")
            check(has_doi == (index not in (first_roman, first_roman + 1)),
                  "DOI overlays must skip every included signed-verification page")
            check(opacity[index] == has_doi, "Watermark must skip only the verification pages")
        for offset in range(2):
            visible = (reader.pages[first_roman + offset].extract_text() or "").strip()
            check(visible == roman(offset + 1),
                  "Included verification pages must visibly print their Roman page numbers")
        print("PASS: optional two-page letter, TOC consistency and overlay exclusion", flush=True)

        paper = copy_fixture(parent, "synthetic-paper")
        configure_synthetic_fixture(paper)
        shutil.copyfile(letter / "front/verification.pdf", paper / "front/verification.pdf")
        override(paper, r"\bebisetup{print=true,verification=true}")
        compile_tex(paper, "final.tex")
        reader, _, first_roman = check_pagination(paper, "final", verification_pages=2)
        opacity = check_graphics_resources(reader)
        check(first_roman == 2, "Paper mode must include an outer cover and inner title page")
        for index, page in enumerate(reader.pages):
            has_doi = "10.0000/synthetic-unassigned-test-only" in (page.extract_text() or "")
            check(has_doi == (index not in (0, first_roman, first_roman + 1)),
                  "Paper overlays must skip the outer cover and signed letter, but include the title page")
            check(opacity[index] == has_doi,
                  "Paper watermark must skip the outer cover and signed letter only")
        print("PASS: paper cover/title page and verification-letter ordering", flush=True)
        preserve_preview(paper, "paper")

        for name, change, error in (
            ("missing-doi", r"\ntusetup{DOI={}}", "Required metadata is empty: doi"),
            ("metadata-placeholder", r"\ntusetup{author={\thesisplaceholder{Author}}}",
             "Unresolved metadata placeholder: author"),
            ("keyword-count", r"\ntusetup{keywords*={one,two}}", "At least 5 keywords required"),
            ("paper-without-letter", r"\bebisetup{print=true,verification=false}",
             "Final paper copy requires the signed verification letter"),
        ):
            bad = copy_fixture(parent, name)
            configure_synthetic_fixture(bad)
            override(bad, change)
            compile_tex(bad, "final.tex", error)
            print(f"PASS: final rejects {name}", flush=True)

        todo = copy_fixture(parent, "body-todo")
        configure_synthetic_fixture(todo)
        with (todo / "contents/chapter01.tex").open("a") as stream:
            stream.write(r"\todomark{Unresolved research task}" + "\n")
        compile_tex(todo, "final.tex", "Unresolved thesis placeholder")
        print("PASS: final rejects unresolved manuscript TODO", flush=True)

    print("All template checks passed. Temporary fixture files were deleted.")
    if preview_dir is not None:
        print(f"Synthetic visual-QA previews retained in {Path(preview_dir).resolve()}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--preview-dir", help="Keep SYNTHETIC-TEST-ONLY PDFs for visual QA")
    run_checks(parser.parse_args().preview_dir)
