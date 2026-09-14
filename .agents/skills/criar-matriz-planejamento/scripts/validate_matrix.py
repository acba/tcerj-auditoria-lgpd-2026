#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Valida estrutura, rastreabilidade e heurísticas de qualidade da matriz."""
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

import matrix_engine as eng

QUESTION_HEADING = re.compile(r"^##\s+Quest[aã]o\s+(?:\d+|Transversal)\b", re.I)
FIELD = re.compile(r"^([a-z_]+):\s*(.*)$")
ITEM = re.compile(r"^\s*-\s+((?:R|F|IR|P|E|A)\w*(?:\.\d+)?)\s*:\s*(.*)$", re.I)
CRITERION_ID = re.compile(r"^\s*-\s+id:\s*(C[\w.\-]+)\s*$", re.I)
SITUATION_ID = re.compile(r"^\s*-\s+(S[\w.\-]+)\s*:\s*$", re.I)
QID = re.compile(r"\b((?:QT|Q)\d+)\s*\.", re.I)
REF_TOKEN = re.compile(r"\b(?:IR\d+(?:\.\d+)?|R\d+(?:\.\d+)?|F\d+(?:\.\d+)?|P\d+(?:\.\d+)?|E\d+(?:\.\d+)?|C\d+(?:\.\d+)?|A\d+(?:\.\d+)?|S\d+(?:\.\d+)?)\b", re.I)

SECTION_NAMES = {
    "subquestoes", "riscos", "fontes_de_informacao", "informacoes_requeridas",
    "criterios", "procedimentos", "evidencias", "variaveis_derivadas",
    "possiveis_achados", "o_que_a_analise_permite_dizer", "limitacoes_e_cautelas",
}

SPECIFIC_LOCATOR = re.compile(
    r"(?:\bart\.?\s*\d|\barts\.?\s*\d|§\s*\d|\binciso\b|\bal[ií]nea\b|"
    r"\bitem\s+[A-Z0-9]|\bitens\s+[A-Z0-9]|\bcl[aá]usula\s+[A-Z0-9]|"
    r"\bcontrole\s+[A-Z0-9]|\bpr[aá]tica\s+[A-Z0-9]|\bprocesso\s+[A-Z]{2,}[0-9]|"
    r"\bobjetivo\s+[A-Z0-9]|\b[A-Z]{2}\.[A-Z]{2}-\d{2}\b|"
    r"\b(?:EDM|APO|BAI|DSS|MEA)\d{2}(?:\.\d{2})?\b)", re.I,
)
REFERENCE_FAMILY = re.compile(
    r"\b(?:ISO|IEC|ABNT|COBIT|NIST|ITIL|ISSAI|INTOSAI|Lei|Decreto|Resolu[cç][aã]o|"
    r"Ac[oó]rd[aã]o|Delibera[cç][aã]o|Portaria|Instru[cç][aã]o Normativa)\b", re.I,
)
SOURCE_PRODUCT_ONLY = re.compile(
    r"^\s*(?:respostas?|documentos?|evid[eê]ncias?|relat[oó]rios?|anexos?|informa[cç][oõ]es?|question[aá]rio)\b", re.I,
)
SOURCE_ORIGIN_HINT = re.compile(
    r"\b(?:gestor|respons[aá]vel|unidade|secretaria|órg[aã]o|orgao|sistema|base|portal|processo|"
    r"reposit[oó]rio|fornecedor|operador|comiss[aã]o|comit[eê]|diretoria|coordena[cç][aã]o|"
    r"tribunal|prefeitura|minist[eé]rio|autarquia|empresa|servidor|administra[cç][aã]o)\b", re.I,
)
GENERIC_PROCEDURE = re.compile(
    r"^\s*(?:avaliar|verificar|analisar)\s+(?:a|o|as|os)?\s*(?:governan[cç]a|conformidade|"
    r"documenta[cç][aã]o|documentos?|processo|controle)s?\s*[.;]?$", re.I,
)

@dataclass
class Message:
    level: str
    question: str
    code: str
    text: str
    line: int | None = None

@dataclass
class Element:
    id: str
    text: str
    line: int
    section: str
    refs: set[str] = field(default_factory=set)

@dataclass
class Criterion:
    id: str
    text: str
    line: int

@dataclass
class Situation:
    id: str
    line: int
    text: str = ""
    refs_matrix: set[str] = field(default_factory=set)
    criteria: set[str] = field(default_factory=set)

@dataclass
class Question:
    label: str
    start_line: int
    end_line: int
    nature: str = ""
    gera_achado: bool = True
    sections: dict[str, list[tuple[int, str]]] = field(default_factory=dict)
    elements: dict[str, Element] = field(default_factory=dict)
    criteria: dict[str, Criterion] = field(default_factory=dict)
    situations: dict[str, Situation] = field(default_factory=dict)

    @property
    def descriptive(self) -> bool:
        return self.nature.strip().lower() == "levantamento" or not self.gera_achado


def normalize_ref(ref: str) -> str:
    return ref.upper()


def refs_from(text: str) -> set[str]:
    return {normalize_ref(x) for x in REF_TOKEN.findall(text)}


def split_questions(lines: list[str]) -> list[tuple[int, int]]:
    starts = [i for i, line in enumerate(lines) if QUESTION_HEADING.search(line)]
    return [(start, starts[idx + 1] if idx + 1 < len(starts) else len(lines)) for idx, start in enumerate(starts)]


def parse_question(lines: list[str], start: int, end: int) -> Question:
    block = lines[start:end]
    qid = None
    nature = ""
    gera_achado = True
    for line in block:
        m = FIELD.match(line.strip())
        if not m:
            continue
        key, value = m.group(1), m.group(2)
        if key == "questao":
            q = QID.search(value)
            if q:
                qid = q.group(1).upper()
        elif key == "natureza":
            nature = value.strip()
        elif key == "gera_achado":
            gera_achado = value.strip().lower() not in {"false", "nao", "não", "0"}
    q = Question(qid or f"linha-{start + 1}", start + 1, end, nature, gera_achado)
    current_section: str | None = None
    current_criterion: Criterion | None = None
    current_situation: Situation | None = None
    for idx in range(start, end):
        raw = lines[idx]
        stripped = raw.strip()
        fm = FIELD.match(stripped)
        if fm and fm.group(1) in SECTION_NAMES and raw == raw.lstrip():
            current_section = fm.group(1)
            q.sections.setdefault(current_section, [])
            current_criterion = None
            current_situation = None
            continue
        if current_section:
            q.sections.setdefault(current_section, []).append((idx + 1, raw))
        if current_section == "criterios":
            cm = CRITERION_ID.match(raw)
            if cm:
                cid = normalize_ref(cm.group(1))
                current_criterion = Criterion(cid, "", idx + 1)
                q.criteria[cid] = current_criterion
                continue
            if current_criterion and stripped.startswith("descricao:"):
                value = stripped.split(":", 1)[1].strip()
                if value and value not in {">-", ">", "|", "|-"}:
                    current_criterion.text = value
                continue
            if current_criterion and raw.startswith("    ") and not stripped.startswith(("natureza_fundamento:", "apto_a_fundamentar_determinacao:", "publico:", "aplica_se:")):
                if stripped and not re.match(r"^[a-z_]+:", stripped):
                    current_criterion.text = (current_criterion.text + " " + stripped).strip()
        im = ITEM.match(raw)
        if im and current_section in {"riscos", "fontes_de_informacao", "informacoes_requeridas", "procedimentos", "evidencias", "possiveis_achados"}:
            eid = normalize_ref(im.group(1))
            q.elements[eid] = Element(eid, im.group(2).strip(), idx + 1, current_section, refs_from(im.group(2)))
        if current_section == "possiveis_achados":
            sm = SITUATION_ID.match(raw)
            if sm:
                sid = normalize_ref(sm.group(1))
                current_situation = Situation(sid, idx + 1)
                q.situations[sid] = current_situation
                continue
            if current_situation:
                if stripped.startswith("descricao:"):
                    current_situation.text = stripped.split(":", 1)[1].strip()
                elif stripped.startswith("referencias_matriz:"):
                    current_situation.refs_matrix |= refs_from(stripped)
                elif stripped.startswith("criterios:"):
                    current_situation.criteria |= {x for x in refs_from(stripped) if x.startswith("C")}
    return q


def add(messages: list[Message], level: str, q: Question, code: str, text: str, line: int | None = None) -> None:
    messages.append(Message(level, q.label, code, text, line))


def validate_traceability(q: Question, messages: list[Message]) -> None:
    known = set(q.elements) | set(q.criteria) | set(q.situations)
    for element in q.elements.values():
        for ref in element.refs:
            if ref.startswith(("R", "F", "IR", "P", "E", "C", "A", "S")) and ref not in known:
                add(messages, "ERROR", q, "REF_INEXISTENTE", f"{element.id} referencia {ref}, que não existe na questão.", element.line)
        if element.section == "informacoes_requeridas" and not any(r.startswith("F") for r in element.refs):
            add(messages, "ERROR", q, "IR_SEM_FONTE", f"{element.id} não referencia fonte F#.", element.line)
        if element.section == "procedimentos" and not any(r.startswith("IR") for r in element.refs):
            add(messages, "ERROR", q, "P_SEM_IR", f"{element.id} não referencia informação requerida IR#.", element.line)
        if element.section == "evidencias" and not any(r.startswith("P") for r in element.refs):
            add(messages, "ERROR", q, "E_SEM_P", f"{element.id} não referencia procedimento P#.", element.line)
    for s in q.situations.values():
        for ref in s.refs_matrix | s.criteria:
            if ref not in known:
                add(messages, "ERROR", q, "REF_INEXISTENTE", f"{s.id} referencia {ref}, que não existe na questão.", s.line)

    # Cobertura reversa da cadeia F <- IR <- P <- E.
    irs = {e.id for e in q.elements.values() if e.section == "informacoes_requeridas"}
    ps = {e.id for e in q.elements.values() if e.section == "procedimentos"}
    es = {e.id for e in q.elements.values() if e.section == "evidencias"}
    used_ir = {r for e in q.elements.values() if e.section == "procedimentos" for r in e.refs if r.startswith("IR")}
    used_p = {r for e in q.elements.values() if e.section == "evidencias" for r in e.refs if r.startswith("P")}
    for iid in sorted(irs - used_ir):
        add(messages, "WARN", q, "IR_ORFA", f"{iid} não é testada por nenhum procedimento.", q.elements[iid].line)
    for pid in sorted(ps - used_p):
        add(messages, "WARN", q, "P_SEM_EVIDENCIA", f"{pid} não produz nenhuma evidência E# explícita.", q.elements[pid].line)
    if q.descriptive:
        if q.situations or any(e.section == "possiveis_achados" for e in q.elements.values()):
            add(messages, "ERROR", q, "LEVANTAMENTO_COM_ACHADO", "Questão de levantamento contém possíveis achados/situações de desconformidade.", q.start_line)
        if not ps:
            add(messages, "ERROR", q, "LEVANTAMENTO_SEM_P", "Questão de levantamento não contém procedimentos.", q.start_line)
        if not es:
            add(messages, "ERROR", q, "LEVANTAMENTO_SEM_E", "Questão de levantamento não contém evidências/saídas analíticas.", q.start_line)
        if "o_que_a_analise_permite_dizer" not in q.sections:
            add(messages, "WARN", q, "LEVANTAMENTO_SEM_SAIDA", "Considere declarar o_que_a_analise_permite_dizer.", q.start_line)
        return
    if not q.criteria:
        add(messages, "ERROR", q, "NORMATIVA_SEM_CRITERIO", "Questão normativa não possui critérios de auditoria.", q.start_line)
    if not q.situations:
        add(messages, "ERROR", q, "NORMATIVA_SEM_ACHADO", "Questão normativa deve prever ao menos um possível achado/situação.", q.start_line)
    for s in q.situations.values():
        needed = {
            "R": any(r.startswith("R") and not r.startswith("IR") for r in s.refs_matrix),
            "P": any(r.startswith("P") for r in s.refs_matrix),
            "E": any(r.startswith("E") for r in s.refs_matrix),
            "C": bool(s.criteria),
        }
        missing = [k for k, ok in needed.items() if not ok]
        if missing:
            add(messages, "ERROR", q, "SITUACAO_SEM_RASTRO", f"{s.id} não possui rastreabilidade mínima para: {', '.join(missing)}.", s.line)


def validate_criteria(q: Question, messages: list[Message]) -> None:
    for c in q.criteria.values():
        text = re.sub(r"\s+", " ", c.text).strip()
        if not text:
            add(messages, "ERROR", q, "CRITERIO_VAZIO", f"{c.id} não possui descrição.", c.line)
            continue
        if REFERENCE_FAMILY.search(text) and not SPECIFIC_LOCATOR.search(text):
            add(messages, "ERROR", q, "CRITERIO_GENERICO", f"{c.id} cita referência sem dispositivo/item/prática específico: {text[:180]}", c.line)
        if "ISO" in text.upper() and not re.search(r"cl[aá]usula|controle\s+[A-Z0-9]|item\s+[A-Z0-9]|Anexo\s+[A-Z]", text, re.I):
            add(messages, "ERROR", q, "ISO_SEM_ITEM", f"{c.id} cita ISO/IEC sem cláusula, controle, item ou anexo específico.", c.line)
        if "COBIT" in text.upper() and not re.search(r"\b(?:EDM|APO|BAI|DSS|MEA)\d{2}(?:\.\d{2})?\b", text, re.I):
            add(messages, "ERROR", q, "COBIT_SEM_PRATICA", f"{c.id} cita COBIT sem objetivo/prática específica.", c.line)
        if re.search(r"\b(?:itens?|arts?\.)\s+[\d.]+\s+(?:a|até)\s+[\d.]+", text, re.I):
            add(messages, "WARN", q, "CRITERIO_INTERVALO_AMPLO", f"{c.id} usa intervalo amplo; prefira separar obrigações testáveis quando distintas.", c.line)
        # Duas normas ISO na mesma descrição costuma esconder critérios diferentes.
        if len(re.findall(r"ISO/IEC\s*\d{4,5}", text, re.I)) > 1:
            add(messages, "WARN", q, "CRITERIO_MULTIPLAS_NORMAS", f"{c.id} combina mais de uma norma; confirme se deve ser desdobrado.", c.line)


def validate_sources_and_procedures(q: Question, messages: list[Message]) -> None:
    for e in q.elements.values():
        if e.section == "fontes_de_informacao":
            if SOURCE_PRODUCT_ONLY.search(e.text) and not SOURCE_ORIGIN_HINT.search(e.text):
                add(messages, "ERROR", q, "FONTE_COMO_PRODUTO", f"{e.id} descreve produto informacional, não origem/ator/sistema: {e.text}", e.line)
        elif e.section == "procedimentos":
            main = e.text.split(";", 1)[0].strip()
            if GENERIC_PROCEDURE.match(main) or len(main.split()) < 10:
                add(messages, "ERROR", q, "PROCEDIMENTO_GENERICO", f"{e.id} é genérico; explicite objeto, ação, atributos/teste e, quando relevante, universo/amostra/período: {main}", e.line)
            if not q.descriptive and re.search(r"por meio da resposta|resposta à quest[aã]o|respostas aos itens", main, re.I) and not re.search(r"anexo|document|registro|sistema|inspec|confront|amostr|extrair|recalcular|observar", main, re.I):
                add(messages, "WARN", q, "PROCEDIMENTO_DECLARATORIO", f"{e.id} depende principalmente de resposta declaratória; avalie confirmação documental, sistêmica ou amostral.", e.line)


def validate_orphans(q: Question, messages: list[Message]) -> None:
    if q.descriptive or not q.situations:
        return
    used_criteria = set().union(*(s.criteria for s in q.situations.values()))
    for cid, c in q.criteria.items():
        if cid not in used_criteria:
            add(messages, "WARN", q, "CRITERIO_ORFAO", f"{cid} não é referenciado por nenhuma situação.", c.line)
    used_refs = set().union(*(s.refs_matrix for s in q.situations.values()))
    for eid, e in q.elements.items():
        if e.section == "procedimentos" and eid not in used_refs:
            add(messages, "WARN", q, "PROCEDIMENTO_ORFAO", f"{eid} não é referenciado por nenhuma situação; confirme sua contribuição.", e.line)


def validate_file(path: Path) -> tuple[list[Question], list[Message]]:
    text = path.read_text(encoding="utf-8")
    # Parser oficial da própria skill: qualquer erro aqui é estrutural e bloqueante.
    eng.parse_matrix(text)
    lines = text.splitlines()
    ranges = split_questions(lines)
    if not ranges:
        raise ValueError("Nenhuma seção '## Questão' encontrada.")
    questions = [parse_question(lines, a, b) for a, b in ranges]
    messages: list[Message] = []
    labels = [q.label for q in questions]
    for q in questions:
        validate_traceability(q, messages)
        validate_criteria(q, messages)
        validate_sources_and_procedures(q, messages)
        validate_orphans(q, messages)
    if len(set(labels)) != len(labels):
        dupes = sorted({x for x in labels if labels.count(x) > 1})
        add(messages, "ERROR", questions[0], "QUESTAO_DUPLICADA", f"IDs duplicados: {', '.join(dupes)}.")
    return questions, messages


def print_text(path: Path, questions: list[Question], messages: list[Message]) -> None:
    errors = [m for m in messages if m.level == "ERROR"]
    warns = [m for m in messages if m.level == "WARN"]
    print(f"Matriz: {path}")
    print(f"Questões: {len(questions)} | normativas: {sum(not q.descriptive for q in questions)} | levantamento: {sum(q.descriptive for q in questions)}")
    print(f"Erros: {len(errors)} | Avisos: {len(warns)}")
    for m in messages:
        loc = f" linha {m.line}" if m.line else ""
        print(f"[{m.level}] {m.question}{loc} {m.code}: {m.text}")


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Valida matriz de planejamento de auditoria governamental.")
    p.add_argument("matrix", type=Path)
    p.add_argument("--json", action="store_true", dest="as_json")
    p.add_argument("--strict", action="store_true", help="retorna erro também quando houver avisos")
    args = p.parse_args(argv)
    try:
        questions, messages = validate_file(args.matrix)
    except Exception as exc:
        print(f"[FATAL] {exc}", file=sys.stderr)
        return 2
    if args.as_json:
        print(json.dumps({
            "file": str(args.matrix),
            "questions": [{"id": q.label, "descriptive": q.descriptive} for q in questions],
            "summary": {"errors": sum(m.level == "ERROR" for m in messages), "warnings": sum(m.level == "WARN" for m in messages)},
            "messages": [m.__dict__ for m in messages],
        }, ensure_ascii=False, indent=2))
    else:
        print_text(args.matrix, questions, messages)
    return 1 if any(m.level == "ERROR" for m in messages) or (args.strict and messages) else 0


if __name__ == "__main__":
    raise SystemExit(main())
