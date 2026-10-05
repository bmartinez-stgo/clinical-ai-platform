"""Genera el corpus completo: 150 PDFs + su ground truth JSON.

Uso: python3 generate_corpus.py
Salida:
  corpus/<report_id>.pdf
  ground_truth/<report_id>.json
"""
import json
import subprocess
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from case_generator import generate_cases

BASE_DIR = Path(__file__).parent
TEMPLATES_DIR = BASE_DIR / "templates"
CORPUS_DIR = BASE_DIR / "corpus"
GT_DIR = BASE_DIR / "ground_truth"
TMP_HTML = BASE_DIR / "_tmp_render.html"


def render_pdf(html_path: Path, pdf_path: Path) -> None:
    result = subprocess.run(
        [
            "google-chrome", "--headless", "--disable-gpu", "--no-sandbox",
            f"--print-to-pdf={pdf_path}", "--print-to-pdf-no-header",
            "--no-pdf-header-footer", f"file://{html_path}",
        ],
        capture_output=True, text=True, timeout=30,
    )
    if result.returncode != 0:
        raise RuntimeError(f"chrome failed for {html_path}: {result.stderr}")


def main() -> None:
    CORPUS_DIR.mkdir(exist_ok=True)
    GT_DIR.mkdir(exist_ok=True)

    env = Environment(loader=FileSystemLoader(str(TEMPLATES_DIR)))
    cases = generate_cases()

    failures = []
    for case in cases:
        report_id = case["report_id"]
        template_file = f"{case['template']}.html.j2"
        try:
            template = env.get_template(template_file)
            html = template.render(**case["report"])
            TMP_HTML.write_text(html, encoding="utf-8")

            pdf_path = CORPUS_DIR / f"{report_id}.pdf"
            render_pdf(TMP_HTML, pdf_path)

            gt = {
                "report_id": report_id,
                "template": case["template"],
                "folio": case["report"]["folio"],
                "patient": case["report"]["patient"],
                "fecha_toma": case["report"]["fecha_toma"],
                "fecha_reporte": case["report"]["fecha_reporte"],
                "medico_solicitante": case["report"]["medico_solicitante"],
                "expected": case["expected"],
            }
            (GT_DIR / f"{report_id}.json").write_text(
                json.dumps(gt, ensure_ascii=False, indent=2), encoding="utf-8"
            )
            print(f"ok  {report_id} ({case['template']}, {len(case['expected'])} analitos)")
        except Exception as e:
            failures.append((report_id, str(e)))
            print(f"FAIL {report_id}: {e}")

    TMP_HTML.unlink(missing_ok=True)

    print(f"\n{len(cases) - len(failures)}/{len(cases)} generados correctamente")
    if failures:
        print("Fallos:", failures)


if __name__ == "__main__":
    main()
