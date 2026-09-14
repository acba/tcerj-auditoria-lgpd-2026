#!/usr/bin/env python3
"""Revisa SurveyMD e gera produtos LSS e DOCX para o LimeSurvey."""

from __future__ import annotations

import argparse
import json
import re
import sys
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import surveymd_to_lss as engine  # noqa: E402
import surveymd_to_docx as docx_engine  # noqa: E402
from survey_utils import (  # noqa: E402
    survey_targets,
    target_output_path,
    validate_visible_dependencies,
)


def _issue(level: str, code: str, message: str, location: str = "") -> dict[str, str]:
    return {
        "level": level,
        "code": code,
        "location": location,
        "message": message,
    }


def _source_question_blocks(text: str) -> list[tuple[str, str, str]]:
    pattern = re.compile(
        r"(?ms)^###\s+([A-Za-z0-9_]+)\s*\[([^]]+)\]\s*\n(.*?)(?=^###\s+|^##\s+Grupo:|\Z)"
    )
    return [(m.group(1), m.group(2).strip().lower(), m.group(3)) for m in pattern.finditer(text)]


def review_markdown(path: Path) -> dict[str, Any]:
    issues: list[dict[str, str]] = []
    result: dict[str, Any] = {
        "source": str(path),
        "valid": False,
        "summary": {},
        "issues": issues,
    }

    if not path.exists():
        issues.append(_issue("error", "file_not_found", "Arquivo SurveyMD não encontrado.", str(path)))
        return result

    try:
        source_text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        issues.append(_issue("error", "encoding", "O arquivo deve estar codificado em UTF-8.", str(path)))
        return result

    try:
        survey = engine.parse_markdown(path)
    except Exception as exc:
        issues.append(_issue("error", "parse", str(exc), str(path)))
        return result

    try:
        validate_visible_dependencies(survey)
    except Exception as exc:
        issues.append(_issue("error", "visible_dependency", str(exc), str(path)))
        return result

    meta = survey.meta
    for field, label in (
        ("title", "título"),
        ("language", "idioma"),
        ("admin", "responsável"),
        ("adminemail", "e-mail do responsável"),
    ):
        if not str(meta.get(field, "")).strip():
            issues.append(
                _issue("warning", f"missing_{field}", f"Front matter sem {label} explícito.", "front matter")
            )

    if not str(meta.get("welcome", "")).strip():
        issues.append(
            _issue(
                "warning",
                "missing_welcome",
                "Inclua abertura com finalidade, público, período de referência e canal de contato.",
                "front matter",
            )
        )
    if not str(meta.get("endtext", "")).strip():
        issues.append(
            _issue("warning", "missing_endtext", "Inclua texto de encerramento e próximos passos.", "front matter")
        )

    question_codes: list[str] = []
    type_counts: Counter[str] = Counter()
    for group in survey.groups:
        if not " ".join(group.description_lines).strip():
            issues.append(
                _issue(
                    "warning",
                    "group_without_description",
                    "O grupo não explica sua finalidade ou instruções.",
                    group.code,
                )
            )
        for question in group.questions:
            question_codes.append(question.code)
            type_counts[question.type] += 1
            if not question.text().strip():
                issues.append(_issue("error", "empty_question", "Pergunta sem enunciado.", question.code))
            if len(re.sub(r"<[^>]+>", "", question.text())) > 800:
                issues.append(
                    _issue(
                        "warning",
                        "long_question",
                        "Enunciado acima de 800 caracteres; avalie separar contexto, ajuda e pergunta.",
                        question.code,
                    )
                )
            option_codes = [item.code for item in question.alternatives + question.subquestions]
            duplicates = sorted(code for code, count in Counter(option_codes).items() if count > 1)
            if duplicates:
                issues.append(
                    _issue(
                        "error",
                        "duplicate_option_code",
                        f"Códigos de alternativa/subquestão duplicados: {', '.join(duplicates)}.",
                        question.code,
                    )
                )

    source_blocks = _source_question_blocks(source_text)
    for code, question_type, block in source_blocks:
        if question_type in engine.MACRO_TYPES:
            if not re.search(r"(?m)^evidence_text:\s*\S", block):
                issues.append(
                    _issue(
                        "warning",
                        "adoption_without_evidence",
                        "Questão de adoção sem pedido de evidência; confirme se a autodeclaração é suficiente.",
                        code,
                    )
                )
            if not re.search(r"(?m)^(subquestions|subquestões|rows|detail_options):\s*$", block):
                issues.append(
                    _issue(
                        "warning",
                        "adoption_without_detail",
                        "Questão de adoção sem detalhamento confirmatório.",
                        code,
                    )
                )

    levels = Counter(issue["level"] for issue in issues)
    result["summary"] = {
        "groups": len(survey.groups),
        "questions_after_expansion": len(question_codes),
        "question_types_after_expansion": dict(sorted(type_counts.items())),
        "targets": survey_targets(survey),
        "errors": levels["error"],
        "warnings": levels["warning"],
    }
    result["valid"] = levels["error"] == 0
    return result


def _section_rows(root: ET.Element, section_name: str) -> list[ET.Element]:
    section = root.find(section_name)
    return section.findall("./rows/row") if section is not None else []


def _row_value(row: ET.Element, field: str) -> str:
    value = row.find(field)
    return (value.text or "").strip() if value is not None else ""


def validate_lss(path: Path) -> dict[str, Any]:
    errors: list[str] = []
    result: dict[str, Any] = {
        "source": str(path),
        "valid": False,
        "summary": {},
        "errors": errors,
    }
    if not path.exists():
        errors.append("Arquivo LSS não encontrado.")
        return result
    try:
        root = ET.parse(path).getroot()
    except ET.ParseError as exc:
        errors.append(f"XML inválido: {exc}")
        return result

    if root.tag != "document":
        errors.append(f"Elemento raiz inesperado: {root.tag!r}; esperado 'document'.")
    if (root.findtext("LimeSurveyDocType") or "").strip() != "Survey":
        errors.append("LimeSurveyDocType ausente ou diferente de 'Survey'.")

    groups = _section_rows(root, "groups")
    questions = _section_rows(root, "questions")
    subquestions = _section_rows(root, "subquestions")
    answers = _section_rows(root, "answers")
    surveys = _section_rows(root, "surveys")
    language_settings = _section_rows(root, "surveys_languagesettings")

    for name, rows in (
        ("groups", groups),
        ("questions", questions),
        ("surveys", surveys),
        ("surveys_languagesettings", language_settings),
    ):
        if not rows:
            errors.append(f"Seção obrigatória sem linhas: {name}.")

    group_ids = [_row_value(row, "gid") for row in groups]
    question_ids = [_row_value(row, "qid") for row in questions]
    question_codes = [_row_value(row, "title") for row in questions]
    duplicate_gids = sorted(key for key, count in Counter(group_ids).items() if key and count > 1)
    duplicate_qids = sorted(key for key, count in Counter(question_ids).items() if key and count > 1)
    duplicate_codes = sorted(key for key, count in Counter(question_codes).items() if key and count > 1)
    if duplicate_gids:
        errors.append(f"GIDs duplicados: {', '.join(duplicate_gids)}.")
    if duplicate_qids:
        errors.append(f"QIDs duplicados: {', '.join(duplicate_qids)}.")
    if duplicate_codes:
        errors.append(f"Códigos de pergunta duplicados: {', '.join(duplicate_codes)}.")

    gid_set = set(group_ids)
    qid_set = set(question_ids)
    for row in questions:
        qid = _row_value(row, "qid") or "?"
        gid = _row_value(row, "gid")
        if gid not in gid_set:
            errors.append(f"Pergunta QID {qid} referencia GID inexistente: {gid!r}.")
    for row in subquestions:
        parent = _row_value(row, "parent_qid")
        if parent not in qid_set:
            errors.append(f"Subquestão referencia parent_qid inexistente: {parent!r}.")
    for row in answers:
        qid = _row_value(row, "qid")
        if qid not in qid_set:
            errors.append(f"Alternativa referencia QID inexistente: {qid!r}.")

    result["summary"] = {
        "groups": len(groups),
        "questions": len(questions),
        "subquestions": len(subquestions),
        "answers": len(answers),
        "surveys": len(surveys),
        "language_settings": len(language_settings),
        "errors": len(errors),
    }
    result["valid"] = not errors
    return result


def build_surveys(source: Path, output: Path, sid: int | None = None) -> tuple[list[Path], dict[str, Any]]:
    survey = engine.parse_markdown(source)
    sid_base = sid if sid is not None else int(survey.meta.get("sid", "900001"))
    targets = survey_targets(survey)
    outputs: list[Path] = []
    validations: list[dict[str, Any]] = []
    variants = targets or [""]
    for index, target in enumerate(variants):
        current = engine.filter_survey_by_target(survey, target) if target else survey
        current_output = target_output_path(output, target) if len(targets) > 1 else output
        current_output.parent.mkdir(parents=True, exist_ok=True)
        xml = engine.build_lss(current, sid=sid_base + index, first_gid=1000, first_qid=10000)
        current_output.write_text(xml, encoding="utf-8")
        outputs.append(current_output)
        validations.append(validate_lss(current_output))
    return outputs, {
        "valid": all(item["valid"] for item in validations),
        "outputs": validations,
    }


def _print_review(result: dict[str, Any]) -> None:
    summary = result.get("summary", {})
    print(f"Fonte: {result['source']}")
    if summary:
        print(
            "Resumo: "
            f"grupos={summary.get('groups', 0)}, "
            f"perguntas={summary.get('questions_after_expansion', 0)}, "
            f"erros={summary.get('errors', 0)}, "
            f"avisos={summary.get('warnings', 0)}"
        )
    for item in result.get("issues", []):
        location = f" [{item['location']}]" if item.get("location") else ""
        print(f"{item['level'].upper()}{location} {item['code']}: {item['message']}")


def _print_lss_validation(result: dict[str, Any]) -> None:
    summary = result.get("summary", {})
    print(f"LSS: {result['source']}")
    if summary:
        print(
            "Resumo: "
            f"grupos={summary.get('groups', 0)}, perguntas={summary.get('questions', 0)}, "
            f"subquestões={summary.get('subquestions', 0)}, alternativas={summary.get('answers', 0)}, "
            f"erros={summary.get('errors', 0)}"
        )
    for error in result.get("errors", []):
        print(f"ERROR: {error}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    review_parser = subparsers.add_parser("review", help="Revisa um SurveyMD.")
    review_parser.add_argument("source", type=Path)
    review_parser.add_argument("--json", action="store_true", dest="as_json")
    review_parser.add_argument("--strict", action="store_true")

    build_parser = subparsers.add_parser("build", help="Revisa, gera e valida o LSS.")
    build_parser.add_argument("source", type=Path)
    build_parser.add_argument("output", type=Path)
    build_parser.add_argument("--sid", type=int)
    build_parser.add_argument("--json", action="store_true", dest="as_json")
    build_parser.add_argument("--strict", action="store_true")

    docx_parser = subparsers.add_parser(
        "build-docx",
        help="Gera e valida o guia DOCX destinado aos respondentes.",
    )
    docx_parser.add_argument("source", type=Path)
    docx_parser.add_argument("output", type=Path)
    docx_parser.add_argument("--reference-docx", type=Path, default=docx_engine.DEFAULT_REFERENCE_DOCX)
    docx_parser.add_argument("--resource-files", nargs="*", type=Path, default=[])
    docx_parser.add_argument("--show-logic", action="store_true")
    docx_parser.add_argument("--engine", choices=["auto", "pandoc", "python-docx"], default="auto")
    docx_parser.add_argument("--target", default="")
    docx_parser.add_argument("--json", action="store_true", dest="as_json")
    docx_parser.add_argument("--strict", action="store_true")

    all_parser = subparsers.add_parser(
        "build-all",
        help="Gera e valida conjuntamente o LSS e o guia DOCX.",
    )
    all_parser.add_argument("source", type=Path)
    all_parser.add_argument("output_base", type=Path)
    all_parser.add_argument("--sid", type=int)
    all_parser.add_argument("--reference-docx", type=Path, default=docx_engine.DEFAULT_REFERENCE_DOCX)
    all_parser.add_argument("--resource-files", nargs="*", type=Path, default=[])
    all_parser.add_argument("--show-logic", action="store_true")
    all_parser.add_argument("--engine", choices=["auto", "pandoc", "python-docx"], default="auto")
    all_parser.add_argument("--json", action="store_true", dest="as_json")
    all_parser.add_argument("--strict", action="store_true")

    lss_parser = subparsers.add_parser("validate-lss", help="Valida a estrutura de um LSS.")
    lss_parser.add_argument("source", type=Path)
    lss_parser.add_argument("--json", action="store_true", dest="as_json")

    args = parser.parse_args(argv)

    if args.command == "review":
        result = review_markdown(args.source)
        if args.as_json:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            _print_review(result)
        warnings = result.get("summary", {}).get("warnings", 0)
        return 0 if result["valid"] and not (args.strict and warnings) else 1

    if args.command == "validate-lss":
        result = validate_lss(args.source)
        if args.as_json:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            _print_lss_validation(result)
        return 0 if result["valid"] else 1

    review = review_markdown(args.source)
    warnings = review.get("summary", {}).get("warnings", 0)
    if not review["valid"] or (args.strict and warnings):
        if args.as_json:
            print(json.dumps({"review": review, "built": False}, ensure_ascii=False, indent=2))
        else:
            _print_review(review)
            print("LSS não gerado devido à revisão bloqueante.")
        return 1

    if args.command == "build-docx":
        try:
            result = docx_engine.build_docx(
                args.source,
                args.output,
                reference_docx=args.reference_docx,
                resource_paths=args.resource_files,
                show_logic=args.show_logic,
                conversion_engine=args.engine,
                target=args.target,
            )
        except Exception as exc:
            if args.as_json:
                print(json.dumps({"review": review, "built": False, "error": str(exc)}, ensure_ascii=False, indent=2))
            else:
                _print_review(review)
                print(f"ERROR: {exc}")
            return 1
        payload = {"review": review, "built": result["validation"]["valid"], "docx": result}
        if args.as_json:
            print(json.dumps(payload, ensure_ascii=False, indent=2))
        else:
            _print_review(review)
            print(f"DOCX: {result['output']} ({result['engine']})")
            print(f"Resumo: grupos={result['groups']}, perguntas={result['questions']}")
            for error in result["validation"]["errors"]:
                print(f"ERROR: {error}")
        return 0 if result["validation"]["valid"] else 1

    if args.command == "build-all":
        lss_output = args.output_base.with_suffix(".lss")
        docx_output = args.output_base.with_suffix(".docx")
        try:
            lss_files, lss_validation = build_surveys(args.source, lss_output, args.sid)
            survey = engine.parse_markdown(args.source)
            targets = survey_targets(survey)
            variants = targets or [""]
            docx_results = []
            for target in variants:
                current_output = target_output_path(docx_output, target) if len(targets) > 1 else docx_output
                docx_results.append(
                    docx_engine.build_docx(
                        args.source,
                        current_output,
                        reference_docx=args.reference_docx,
                        resource_paths=args.resource_files,
                        show_logic=args.show_logic,
                        conversion_engine=args.engine,
                        target=target,
                    )
                )
        except Exception as exc:
            if args.as_json:
                print(json.dumps({"review": review, "built": False, "error": str(exc)}, ensure_ascii=False, indent=2))
            else:
                _print_review(review)
                print(f"ERROR: {exc}")
            return 1
        valid = lss_validation["valid"] and all(item["validation"]["valid"] for item in docx_results)
        payload = {
            "review": review,
            "built": valid,
            "lss_files": [str(path) for path in lss_files],
            "lss_validation": lss_validation,
            "docx": docx_results,
        }
        if args.as_json:
            print(json.dumps(payload, ensure_ascii=False, indent=2))
        else:
            _print_review(review)
            for path in lss_files:
                print(f"LSS: {path}")
            for item in docx_results:
                print(f"DOCX: {item['output']} ({item['engine']})")
        return 0 if valid else 1

    try:
        outputs, validation = build_surveys(args.source, args.output, args.sid)
    except Exception as exc:
        if args.as_json:
            print(json.dumps({"review": review, "built": False, "error": str(exc)}, ensure_ascii=False, indent=2))
        else:
            _print_review(review)
            print(f"ERROR: {exc}")
        return 1

    payload = {
        "review": review,
        "built": validation["valid"],
        "files": [str(path) for path in outputs],
        "validation": validation,
    }
    if args.as_json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        _print_review(review)
        for item in validation["outputs"]:
            _print_lss_validation(item)
        for path in outputs:
            print(f"OK: arquivo gerado em {path}")
    return 0 if validation["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
