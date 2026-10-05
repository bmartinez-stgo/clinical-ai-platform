"""Renderiza las 4 plantillas con el caso de ejemplo, para revisión visual.

Uso: python3 render.py
Genera research/paper/datasets/samples/template_{1..4}_*.{html,pdf}
"""
import subprocess
import sys
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from sample_data import REPORT

BASE_DIR = Path(__file__).parent
TEMPLATES_DIR = BASE_DIR / "templates"
SAMPLES_DIR = BASE_DIR / "samples"

TEMPLATES = [
    "template_1_simple.html.j2",
    "template_2_letterhead.html.j2",
    "template_3_panel_grid.html.j2",
    "template_4_abbreviated.html.j2",
    "template_5_scanned.html.j2",
    "template_6_bilingual.html.j2",
    "template_7_stamped.html.j2",
    "template_8_narrative.html.j2",
    "template_9_portal.html.j2",
    "template_10_multipage.html.j2",
]


def render_pdf(html_path: Path, pdf_path: Path) -> None:
    result = subprocess.run(
        [
            "google-chrome",
            "--headless",
            "--disable-gpu",
            "--no-sandbox",
            f"--print-to-pdf={pdf_path}",
            "--print-to-pdf-no-header",
            "--no-pdf-header-footer",
            f"file://{html_path}",
        ],
        capture_output=True,
        text=True,
        timeout=30,
    )
    if result.returncode != 0:
        raise RuntimeError(f"chrome failed for {html_path}: {result.stderr}")


def main() -> None:
    SAMPLES_DIR.mkdir(exist_ok=True)
    env = Environment(loader=FileSystemLoader(str(TEMPLATES_DIR)))

    for tpl_name in TEMPLATES:
        template = env.get_template(tpl_name)
        html = template.render(**REPORT)

        stem = tpl_name.replace(".html.j2", "")
        html_path = SAMPLES_DIR / f"{stem}.html"
        pdf_path = SAMPLES_DIR / f"{stem}.pdf"
        html_path.write_text(html, encoding="utf-8")
        render_pdf(html_path, pdf_path)
        print(f"ok: {pdf_path}")


if __name__ == "__main__":
    main()
