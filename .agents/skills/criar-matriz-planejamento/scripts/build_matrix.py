#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Gera o DOCX da matriz usando apenas recursos empacotados nesta skill."""
from __future__ import annotations

import argparse
import copy
import re
import sys
from pathlib import Path
from xml.etree import ElementTree as ET
from zipfile import ZIP_DEFLATED, ZipFile

import matrix_engine as eng
import validate_matrix as validator

SKILL_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_TEMPLATE = SKILL_ROOT / "assets" / "matriz_planejamento_template.docx"
DEFAULT_OUTPUT_NAME = "matriz_planejamento.docx"


def parse_frontmatter(text: str) -> dict[str, str]:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}
    meta: dict[str, str] = {}
    for line in lines[1:]:
        if line.strip() == "---":
            break
        m = re.match(r"^([A-Za-z_][A-Za-z0-9_]*):\s*(.*)$", line)
        if not m:
            continue
        value = m.group(2).strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
            value = value[1:-1]
        meta[m.group(1).lower()] = value
    return meta


def update_header_xml(header_xml: bytes, replacements: dict[str, str]) -> bytes:
    if not replacements:
        return header_xml
    root = ET.fromstring(header_xml)
    W = f"{{{eng.W_NS}}}"
    found: set[str] = set()
    for paragraph in root.iter(f"{W}p"):
        current = eng.text_of(paragraph).strip()
        for label, value in replacements.items():
            if current.startswith(f"{label}:") or current.startswith(label):
                eng.set_labeled_paragraph_text(paragraph, label, value)
                found.add(label)
                break
    missing = sorted(set(replacements) - found)
    if missing:
        print(f"[AVISO] Rótulos não encontrados no cabeçalho: {', '.join(missing)}", file=sys.stderr)
    return ET.tostring(root, encoding="utf-8", xml_declaration=True)


def findings_clean(question: eng.Question, mapping: dict[str, str] | None = None):
    """Matriz de planejamento mostra hipótese e referências, não deliberação proposta."""
    display_mapping = mapping or {}
    lines: list[str | eng.CellParagraph] = []
    for finding in question.achados:
        if finding.title:
            lines.append(eng.CellParagraph(f"{finding.title.rstrip('.')}.", bold=True, spacing_after=80))
        for situation in finding.situacoes:
            refs = [eng.display_identifier(x, display_mapping) for x in dict.fromkeys(situation.referencias + situation.criterios)]
            desc = f"{situation.descricao.rstrip('.')}."
            if refs:
                desc += f" [{', '.join(refs)}];"
            lines.append(eng.CellParagraph(f"• {desc}", left_indent=240, spacing_after=60))
    if lines:
        return lines
    if not question.gera_achado or question.natureza:
        lines.append("Não se aplica: questão de levantamento, sem geração de achado individual.")
        if question.analise_permite_dizer:
            lines.append("O que a análise permite dizer:")
            lines.extend(eng.format_items(question.analise_permite_dizer, display_mapping))
        if question.limitacoes:
            lines.append("Limitações e cautelas:")
            lines.extend(eng.format_items(question.limitacoes, display_mapping))
        return lines
    return [eng.MISSING_MARKDOWN_PLACEHOLDER]


def generate(matrix_path: Path, template_path: Path, output_path: Path, headers: dict[str, str]) -> int:
    matrix = eng.parse_matrix(matrix_path.read_text(encoding="utf-8"))
    if not matrix.questions:
        raise ValueError("Nenhuma questão encontrada.")
    with ZipFile(template_path, "r") as zin:
        archive = [(copy.copy(item), zin.read(item.filename)) for item in zin.infolist()]
    files = {item.filename: data for item, data in archive}
    if "word/document.xml" not in files:
        raise ValueError("Template sem word/document.xml.")
    W = f"{{{eng.W_NS}}}"
    root = ET.fromstring(files["word/document.xml"])
    body = root.find(f"{W}body")
    if body is None:
        raise ValueError("Template sem word/body.")
    intro, table_template, signature_parts, sect_pr = eng.find_template_parts(body)
    for child in list(body):
        body.remove(child)
    for element in eng.replace_intro_text(intro, matrix):
        body.append(element)
    blank = ET.Element(f"{W}p")
    original_formatter = eng.format_findings_or_analysis
    eng.format_findings_or_analysis = findings_clean
    try:
        for index, question in enumerate(matrix.questions):
            summary, details = eng.build_question_tables(table_template, question)
            if index > 0:
                body.append(eng.page_break_paragraph())
            body.append(summary)
            body.append(details)
    finally:
        eng.format_findings_or_analysis = original_formatter
    for part in signature_parts:
        body.append(copy.deepcopy(blank))
        body.append(copy.deepcopy(part))
    body.append(copy.deepcopy(sect_pr))
    files["word/document.xml"] = ET.tostring(root, encoding="utf-8", xml_declaration=True)
    if "word/header1.xml" in files and headers:
        files["word/header1.xml"] = update_header_xml(files["word/header1.xml"], headers)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(output_path, "w", ZIP_DEFLATED) as zout:
        for item, _ in archive:
            zout.writestr(item, files[item.filename])
    return len(matrix.questions)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Valida e gera matriz_planejamento.docx.")
    p.add_argument("input", type=Path, help="matriz_planejamento.md/.md")
    p.add_argument("--template", type=Path, default=DEFAULT_TEMPLATE, help="template DOCX; por padrão usa o asset da skill")
    p.add_argument("--output", type=Path, help="DOCX de saída; padrão: ao lado da matriz")
    p.add_argument("--fiscalizacao")
    p.add_argument("--jurisdicionados")
    p.add_argument("--objetivo-auditoria")
    p.add_argument("--allow-warnings", action="store_true", help="gera mesmo quando houver avisos; erros continuam bloqueantes")
    args = p.parse_args(argv)
    if not args.input.exists():
        print(f"Matriz não encontrada: {args.input}", file=sys.stderr); return 2
    if not args.template.exists():
        print(f"Template não encontrado: {args.template}", file=sys.stderr); return 2
    try:
        questions, messages = validator.validate_file(args.input)
    except Exception as exc:
        print(f"[FATAL] validação estrutural: {exc}", file=sys.stderr); return 2
    errors = [m for m in messages if m.level == "ERROR"]
    warnings = [m for m in messages if m.level == "WARN"]
    for m in messages:
        loc = f" linha {m.line}" if m.line else ""
        print(f"[{m.level}] {m.question}{loc} {m.code}: {m.text}")
    if errors:
        print(f"Geração bloqueada: {len(errors)} erro(s) de matriz.", file=sys.stderr); return 1
    if warnings and not args.allow_warnings:
        print(f"Geração bloqueada por {len(warnings)} aviso(s). Revise-os ou use --allow-warnings conscientemente.", file=sys.stderr); return 1
    text = args.input.read_text(encoding="utf-8")
    meta = parse_frontmatter(text)
    headers = {
        "FISCALIZAÇÃO": args.fiscalizacao or meta.get("fiscalizacao", "[PREENCHER]"),
        "JURISDICIONADOS": args.jurisdicionados or meta.get("jurisdicionados", "[PREENCHER]"),
        "OBJETIVO DA AUDITORIA": args.objetivo_auditoria or meta.get("objetivo_auditoria", "[PREENCHER]"),
    }
    output = args.output or (args.input.parent / DEFAULT_OUTPUT_NAME)
    try:
        count = generate(args.input, args.template, output, headers)
    except Exception as exc:
        print(f"Erro ao gerar DOCX: {exc}", file=sys.stderr); return 2
    print(f"[OK] {count} questão(ões) renderizada(s).")
    print(f"[OK] DOCX: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
