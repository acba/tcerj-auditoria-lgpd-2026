#!/usr/bin/env python3
"""Executa testes determinísticos dos recursos autocontidos da skill."""

from __future__ import annotations

import tempfile
from pathlib import Path

from survey_tool import build_surveys, review_markdown, validate_lss
from surveymd_to_docx import build_docx


ROOT = Path(__file__).resolve().parents[1]
FILES = ROOT / "evals" / "files"


def main() -> int:
    basic_review = review_markdown(FILES / "survey-basico.md")
    assert basic_review["valid"], basic_review

    adoption_review = review_markdown(FILES / "survey-adocao.md")
    assert adoption_review["valid"], adoption_review

    invalid_review = review_markdown(FILES / "survey-invalido.md")
    assert not invalid_review["valid"], invalid_review
    assert any("q9999" in issue["message"] for issue in invalid_review["issues"]), invalid_review

    with tempfile.TemporaryDirectory(prefix="survey-skill-test-") as temp_dir:
        temp = Path(temp_dir)
        basic_outputs, basic_validation = build_surveys(
            FILES / "survey-basico.md", temp / "basico.lss"
        )
        assert basic_validation["valid"], basic_validation
        assert validate_lss(basic_outputs[0])["valid"]

        adoption_outputs, adoption_validation = build_surveys(
            FILES / "survey-adocao.md", temp / "adocao.lss"
        )
        assert adoption_validation["valid"], adoption_validation
        xml = adoption_outputs[0].read_text(encoding="utf-8")
        for code in ("q0201", "q0201nsa", "q0201ext", "q0201evi"):
            assert f"<![CDATA[{code}]]>" in xml, code
        for filetype in ("pdf", "docx", "zip"):
            assert filetype in xml

        docx_result = build_docx(
            FILES / "survey-adocao.md",
            temp / "adocao.docx",
            conversion_engine="python-docx",
        )
        assert docx_result["validation"]["valid"], docx_result
        assert docx_result["groups"] == 1
        assert docx_result["questions"] >= 4

    print("OK: 3 cenários SurveyMD, 2 arquivos LSS e 1 guia DOCX validados.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
