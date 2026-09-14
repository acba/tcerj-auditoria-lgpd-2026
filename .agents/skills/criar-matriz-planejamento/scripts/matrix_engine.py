#!/usr/bin/env python3
"""Motor autocontido de parsing e geração de matriz de planejamento.

Usado apenas pelos scripts desta skill. Não depende de módulos do projeto do usuário.
"""

from __future__ import annotations

import copy
import ast
import re
import textwrap
import unicodedata
from dataclasses import dataclass, field
from typing import Iterable
from xml.etree import ElementTree as ET


MISSING_MARKDOWN_PLACEHOLDER = "[NÃO LOCALIZADO NO MARKDOWN]"

W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
R_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
XML_NS = "http://www.w3.org/XML/1998/namespace"
W = f"{{{W_NS}}}"
R = f"{{{R_NS}}}"
XML = f"{{{XML_NS}}}"

ET.register_namespace("w", W_NS)
ET.register_namespace("r", R_NS)
ET.register_namespace("xml", XML_NS)


FIELDS = [
    "natureza",
    "gera_achado",
    "questao",
    "subquestoes",
    "riscos",
    "fontes_de_informacao",
    "informacoes_requeridas",
    "criterios",
    # Mantidos apenas como delimitadores para que o parser possa rejeitar o
    # formato legado com uma mensagem específica.
    "metadados_criterios",
    "criterios_especificos",
    "criterios_de_comparabilidade",
    "procedimentos",
    "evidencias",
    "variaveis_derivadas",
    "possiveis_achados",
    "variantes_especificas",
    "o_que_a_analise_permite_dizer",
    "limitacoes_e_cautelas",
]


@dataclass
class ListItem:
    id: str
    text: str
    raw: str
    refs: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class Criterion:
    id: str
    descricao: str
    natureza_fundamento: str = ""
    apto_a_fundamentar_determinacao: bool = False
    publico: str = ""
    aplica_se: dict[str, list[str]] = field(default_factory=dict)

    @property
    def especifico(self) -> bool:
        return bool(self.aplica_se)


@dataclass
class CellParagraph:
    text: str
    bold: bool | None = None
    left_indent: int = 0
    spacing_after: int = 120


@dataclass(frozen=True)
class SituationVariant:
    publico: str
    aplica_se: dict[str, list[str]]
    criterios: list[str] | None = None
    tipo_encaminhamento: str | None = None
    fundamentacao_encaminhamento: str | None = None
    encaminhamento: str | None = None


@dataclass
class Situation:
    id: str
    descricao: str = ""
    severidade: str = ""
    itens: list[str] = field(default_factory=list)
    regra: list[str] = field(default_factory=list)
    referencias: list[str] = field(default_factory=list)
    criterios: list[str] = field(default_factory=list)
    tipo_encaminhamento: str = ""
    fundamentacao_encaminhamento: str = ""
    encaminhamento: str = ""
    variantes: list[SituationVariant] = field(default_factory=list)


@dataclass
class Finding:
    id: str
    title: str
    situacoes: list[Situation] = field(default_factory=list)


@dataclass
class Question:
    id: str
    title: str
    question: str
    natureza: str = ""
    gera_achado: bool = True
    subquestoes: list[ListItem] = field(default_factory=list)
    riscos: list[ListItem] = field(default_factory=list)
    fontes: list[ListItem] = field(default_factory=list)
    informacoes: list[ListItem] = field(default_factory=list)
    criterios: list[Criterion] = field(default_factory=list)
    criterios_comparabilidade: list[ListItem] = field(default_factory=list)
    procedimentos: list[ListItem] = field(default_factory=list)
    evidencias: list[ListItem] = field(default_factory=list)
    achados: list[Finding] = field(default_factory=list)
    analise_permite_dizer: list[ListItem] = field(default_factory=list)
    limitacoes: list[ListItem] = field(default_factory=list)


@dataclass
class Matrix:
    title: str
    questao_geral: str
    questions: list[Question]


def normalize_text(text: str) -> str:
    return text.replace("\r\n", "\n").replace("\r", "\n")


def split_csv_list(value: str) -> list[str]:
    value = value.strip()
    if value.startswith("[") and value.endswith("]"):
        value = value[1:-1]
    return [part.strip() for part in value.split(",") if part.strip()]


def get_single_line(content: str, key: str) -> str:
    match = re.search(rf"^{re.escape(key)}:\s*(.+)$", content, flags=re.M)
    return match.group(1).strip() if match else ""


def get_section_block(content: str, field_name: str) -> str:
    match = re.search(rf"^{re.escape(field_name)}:\s*$", content, flags=re.M)
    if not match:
        return ""
    start = match.end()
    rest = content[start:]
    next_match = re.search(
        r"\n(?:" + "|".join(re.escape(field) for field in FIELDS) + r"):\s*$|\n---\s*$",
        rest,
        flags=re.M,
    )
    return (rest[: next_match.start()] if next_match else rest).strip()


def parse_bool(value: str, default: bool = True) -> bool:
    if not value:
        return default
    return value.strip().lower() in {"true", "sim", "yes", "1"}


def _parse_scalar(value: str):
    value = value.strip()
    if not value:
        return ""
    low = value.lower()
    if low in {"true", "false"}:
        return low == "true"
    if value.startswith("[") and value.endswith("]"):
        inner = value[1:-1].strip()
        if not inner:
            return []
        parts = []
        current = ""
        quote = None
        for ch in inner:
            if ch in {"'", '"'}:
                if quote == ch:
                    quote = None
                elif quote is None:
                    quote = ch
                current += ch
            elif ch == "," and quote is None:
                parts.append(current.strip())
                current = ""
            else:
                current += ch
        if current.strip():
            parts.append(current.strip())
        result = []
        for item in parts:
            item = item.strip()
            if len(item) >= 2 and item[0] == item[-1] and item[0] in {"'", '"'}:
                try:
                    item = ast.literal_eval(item)
                except Exception:
                    item = item[1:-1]
            result.append(str(item))
        return result
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        try:
            return ast.literal_eval(value)
        except Exception:
            return value[1:-1]
    return value


def parse_structured_list(block: str, field_name: str) -> list[dict]:
    """Parseia o subconjunto YAML usado pela matriz sem depender de PyYAML.

    Suporta lista de objetos, escalares, booleanos, listas inline, bloco dobrado
    (>-) e um nível de objeto aninhado (usado por aplica_se).
    """
    if not block.strip():
        return []
    lines = textwrap.dedent(block).splitlines()
    items: list[dict] = []
    current: dict | None = None
    i = 0

    def indentation(line: str) -> int:
        return len(line) - len(line.lstrip(" "))

    while i < len(lines):
        line = lines[i]
        if not line.strip():
            i += 1
            continue
        m_item = re.match(r"^-\s+([A-Za-z_][A-Za-z0-9_]*):\s*(.*)$", line)
        if m_item:
            current = {}
            items.append(current)
            key, raw = m_item.group(1), m_item.group(2).strip()
            current[key] = _parse_scalar(raw)
            i += 1
            continue
        if current is None:
            raise ValueError(f"Bloco {field_name} inválido próximo de: {line.strip()}")
        m_prop = re.match(r"^(\s+)([A-Za-z_][A-Za-z0-9_]*):\s*(.*)$", line)
        if not m_prop:
            raise ValueError(f"Bloco {field_name} inválido próximo de: {line.strip()}")
        indent = len(m_prop.group(1))
        key, raw = m_prop.group(2), m_prop.group(3).strip()
        if raw in {">-", ">", "|-", "|"}:
            folded = raw.startswith(">")
            i += 1
            parts: list[str] = []
            while i < len(lines) and (not lines[i].strip() or indentation(lines[i]) > indent):
                if lines[i].strip():
                    parts.append(lines[i].strip())
                elif not folded:
                    parts.append("")
                i += 1
            current[key] = (" ".join(parts) if folded else "\n".join(parts)).strip()
            continue
        if raw == "":
            i += 1
            nested: dict[str, object] = {}
            while i < len(lines):
                nl = lines[i]
                if not nl.strip():
                    i += 1
                    continue
                nindent = indentation(nl)
                if nindent <= indent:
                    break
                nm = re.match(r"^\s+([A-Za-z_][A-Za-z0-9_]*):\s*(.*)$", nl)
                if not nm:
                    raise ValueError(f"Bloco {field_name}.{key} inválido próximo de: {nl.strip()}")
                nested[nm.group(1)] = _parse_scalar(nm.group(2))
                i += 1
            current[key] = nested
            continue
        current[key] = _parse_scalar(raw)
        i += 1
    return items


CRITERION_FIELDS = {
    "id",
    "descricao",
    "natureza_fundamento",
    "apto_a_fundamentar_determinacao",
    "publico",
    "aplica_se",
}
SELECTOR_FIELDS = {
    "segmentos",
    "naturezas",
    "tags_todas",
    "tags_alguma",
    "tags_excluidas",
}
VARIANT_FIELDS = {
    "publico",
    "aplica_se",
    "criterios",
    "tipo_encaminhamento",
    "fundamentacao_encaminhamento",
    "encaminhamento",
}


def parse_criteria(block: str, question_id: str) -> list[Criterion]:
    raw_items = parse_structured_list(block, "criterios")
    criteria: list[Criterion] = []
    identifiers: set[str] = set()
    for position, item in enumerate(raw_items, 1):
        unknown = sorted(str(key) for key in set(item) - CRITERION_FIELDS)
        if unknown:
            raise ValueError(
                f"{question_id}.criterios[{position}]: campos desconhecidos: {', '.join(unknown)}."
            )

        criterion_id = str(item.get("id") or "").strip().upper()
        if not re.fullmatch(r"C\d+", criterion_id):
            raise ValueError(
                f"{question_id}.criterios[{position}].id deve seguir o formato Cn."
            )
        if criterion_id in identifiers:
            raise ValueError(f"{question_id}: critério duplicado: {criterion_id}.")
        identifiers.add(criterion_id)

        description = str(item.get("descricao") or "").strip()
        foundation = str(item.get("natureza_fundamento") or "").strip()
        if not description:
            raise ValueError(f"{question_id}.{criterion_id}.descricao não pode ser vazia.")
        determination = item.get("apto_a_fundamentar_determinacao", False)
        if not isinstance(determination, bool):
            raise ValueError(
                f"{question_id}.{criterion_id}.apto_a_fundamentar_determinacao "
                "deve ser true ou false quando declarado."
            )

        audience = str(item.get("publico") or "").strip()
        selector_declared = "aplica_se" in item
        raw_selector = item.get("aplica_se")
        if selector_declared and not isinstance(raw_selector, dict):
            raise ValueError(f"{question_id}.{criterion_id}.aplica_se deve ser um objeto.")
        selector = raw_selector or {}
        unknown_selectors = sorted(set(selector) - SELECTOR_FIELDS)
        if unknown_selectors:
            raise ValueError(
                f"{question_id}.{criterion_id}.aplica_se contém seletores desconhecidos: "
                f"{', '.join(unknown_selectors)}."
            )
        normalized_selector: dict[str, list[str]] = {}
        for key, value in selector.items():
            if not isinstance(value, list):
                raise ValueError(
                    f"{question_id}.{criterion_id}.aplica_se.{key} deve ser uma lista."
                )
            normalized_selector[key] = [str(entry).strip() for entry in value if str(entry).strip()]
        selector_nonempty = any(normalized_selector.values())
        if selector_declared and not selector_nonempty:
            raise ValueError(f"{question_id}.{criterion_id}: critério específico sem seletor preenchido.")
        if selector_nonempty and not audience:
            raise ValueError(f"{question_id}.{criterion_id}: critério específico sem publico.")
        if audience and not selector_nonempty:
            raise ValueError(f"{question_id}.{criterion_id}: publico exige aplica_se preenchido.")

        criteria.append(
            Criterion(
                id=criterion_id,
                descricao=description,
                natureza_fundamento=foundation,
                apto_a_fundamentar_determinacao=determination,
                publico=audience,
                aplica_se=normalized_selector,
            )
        )
    return criteria


def _normalize_selector(selector: object, context: str) -> dict[str, list[str]]:
    if not isinstance(selector, dict):
        raise ValueError(f"{context}.aplica_se deve ser um objeto.")
    unknown = sorted(str(key) for key in set(selector) - SELECTOR_FIELDS)
    if unknown:
        raise ValueError(
            f"{context}.aplica_se contém seletores desconhecidos: {', '.join(unknown)}."
        )
    normalized: dict[str, list[str]] = {}
    for key, value in selector.items():
        if not isinstance(value, list):
            raise ValueError(f"{context}.aplica_se.{key} deve ser uma lista.")
        normalized[key] = [str(entry).strip() for entry in value if str(entry).strip()]
    if not any(normalized.values()):
        raise ValueError(f"{context}: variante específica sem seletor preenchido.")
    return normalized


def parse_situation_variants(block: str, situation_id: str) -> list[SituationVariant]:
    raw_items = parse_structured_list(textwrap.dedent(block), f"{situation_id}.variantes")
    variants: list[SituationVariant] = []
    for position, item in enumerate(raw_items, 1):
        context = f"{situation_id}.variantes[{position}]"
        unknown = sorted(str(key) for key in set(item) - VARIANT_FIELDS)
        if unknown:
            raise ValueError(f"{context}: campos desconhecidos: {', '.join(unknown)}.")

        audience = str(item.get("publico") or "").strip()
        if not audience:
            raise ValueError(f"{context}.publico não pode ser vazio.")
        if "aplica_se" not in item:
            raise ValueError(f"{context}.aplica_se deve ser informado.")
        selector = _normalize_selector(item.get("aplica_se"), context)

        criteria: list[str] | None = None
        if "criterios" in item:
            raw_criteria = item.get("criterios")
            if not isinstance(raw_criteria, list):
                raise ValueError(f"{context}.criterios deve ser uma lista.")
            criteria = [str(value).strip() for value in raw_criteria if str(value).strip()]
            if not criteria:
                raise ValueError(f"{context}.criterios não pode ser vazio quando declarado.")

        referral_type: str | None = None
        if "tipo_encaminhamento" in item:
            referral_type = str(item.get("tipo_encaminhamento") or "").strip()
            if referral_type.lower() not in {"recomendação", "determinacao", "determinação", "recomendacao"}:
                raise ValueError(
                    f"{context}.tipo_encaminhamento deve ser Recomendação ou Determinação."
                )

        referral_foundation: str | None = None
        if "fundamentacao_encaminhamento" in item:
            referral_foundation = str(item.get("fundamentacao_encaminhamento") or "").strip()
            if not referral_foundation:
                raise ValueError(
                    f"{context}.fundamentacao_encaminhamento não pode ser vazia quando declarada."
                )

        referral: str | None = None
        if "encaminhamento" in item:
            referral = str(item.get("encaminhamento") or "").strip()
            if not referral:
                raise ValueError(f"{context}.encaminhamento não pode ser vazio quando declarado.")

        if (
            criteria is None
            and referral_type is None
            and referral_foundation is None
            and referral is None
        ):
            raise ValueError(f"{context}: informe ao menos um campo a sobrescrever.")
        variants.append(
            SituationVariant(
                publico=audience,
                aplica_se=selector,
                criterios=criteria,
                tipo_encaminhamento=referral_type,
                fundamentacao_encaminhamento=referral_foundation,
                encaminhamento=referral,
            )
        )

    identifiers: set[str] = set()
    for variant in variants:
        identifier = situation_variant_id(situation_id, variant)
        if identifier in identifiers:
            raise ValueError(f"{situation_id}: identificador automático de variante duplicado: {identifier}.")
        identifiers.add(identifier)
    return variants


def _identifier_fragment(value: str) -> str:
    ascii_value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^A-Z0-9]+", "_", ascii_value.upper()).strip("_")


def situation_variant_id(situation_id: str, variant: SituationVariant) -> str:
    segments = variant.aplica_se.get("segmentos", [])
    suffix = _identifier_fragment(segments[0]) if len(segments) == 1 else _identifier_fragment(variant.publico)
    if not suffix:
        raise ValueError(f"{situation_id}: não foi possível gerar o identificador da variante.")
    return f"{situation_id}.{suffix}"


def materialize_situation_variant(
    situation: Situation, variant: SituationVariant
) -> tuple[str, list[str], str, str, str]:
    return (
        situation_variant_id(situation.id, variant),
        list(variant.criterios if variant.criterios is not None else situation.criterios),
        variant.tipo_encaminhamento
        if variant.tipo_encaminhamento is not None
        else situation.tipo_encaminhamento,
        variant.fundamentacao_encaminhamento
        if variant.fundamentacao_encaminhamento is not None
        else situation.fundamentacao_encaminhamento,
        variant.encaminhamento if variant.encaminhamento is not None else situation.encaminhamento,
    )


def parse_item(text: str) -> ListItem:
    raw = text.strip()
    item_id = ""
    item_text = raw
    match = re.match(r"^([A-Z]{1,4}\d+(?:\.\d+)?|CT\d+):\s*(.+)$", raw)
    if match:
        item_id = match.group(1)
        item_text = match.group(2).strip()
    refs_match = re.search(r"\[([^\]]+)\]\s*$", raw)
    refs = split_csv_list(refs_match.group(1)) if refs_match else []
    return ListItem(item_id, item_text, raw, refs)


def parse_list(block: str) -> list[ListItem]:
    items: list[ListItem] = []
    current: str | None = None
    for line in normalize_text(block).split("\n"):
        if not line.strip():
            continue
        bullet = re.match(r"^\s*-\s+(.+)$", line)
        if bullet:
            if current:
                items.append(parse_item(current))
            current = bullet.group(1).strip()
        elif current:
            current += " " + line.strip()
    if current:
        items.append(parse_item(current))
    return items


def parse_findings(block: str) -> list[Finding]:
    findings: list[Finding] = []
    current_finding: Finding | None = None
    current_situation: Situation | None = None
    current_prop = ""
    variant_lines: list[str] = []
    reading_variants = False

    def finish_situation() -> None:
        nonlocal current_situation, current_prop, variant_lines, reading_variants
        if current_situation and variant_lines:
            current_situation.variantes = parse_situation_variants(
                "\n".join(variant_lines), current_situation.id
            )
        if current_finding and current_situation:
            current_finding.situacoes.append(current_situation)
        current_situation = None
        current_prop = ""
        variant_lines = []
        reading_variants = False

    def finish_finding() -> None:
        nonlocal current_finding
        finish_situation()
        if current_finding:
            findings.append(current_finding)
        current_finding = None

    for line in normalize_text(block).split("\n"):
        finding_match = re.match(r"^\s*-\s+(A\d+):\s*(.+)$", line)
        if finding_match:
            finish_finding()
            current_finding = Finding(finding_match.group(1), finding_match.group(2).strip())
            continue

        situation_match = re.match(r"^\s*-\s+(S\d+\.\d+):\s*$", line)
        if situation_match:
            finish_situation()
            current_situation = Situation(situation_match.group(1))
            continue

        if not current_situation:
            continue

        if reading_variants:
            if line.strip():
                variant_lines.append(line)
            continue

        prop_match = re.match(r"^\s{4,}([a-zA-Z_]+):\s*(.*)$", line)
        if prop_match:
            current_prop = prop_match.group(1)
            value = prop_match.group(2).strip()
            if current_prop == "variantes":
                if value:
                    raise ValueError(
                        f"{current_situation.id}.variantes deve ser declarado como lista em bloco."
                    )
                reading_variants = True
                continue
            assign_situation_prop(current_situation, current_prop, value)
            continue

        list_item = re.match(r"^\s{4,}-\s+(.+)$", line)
        if list_item and current_prop == "regra_de_identificacao":
            current_situation.regra.append(list_item.group(1).strip())
            continue

        if line.strip() and current_prop in {"fundamentacao_encaminhamento", "encaminhamento"}:
            atual = getattr(current_situation, current_prop)
            setattr(current_situation, current_prop, (atual + " " + line.strip()).strip())

    finish_finding()
    return findings


def assign_situation_prop(situation: Situation, prop: str, value: str) -> None:
    if prop == "descricao":
        situation.descricao = value
    elif prop == "severidade":
        situation.severidade = value
    elif prop in {"itens_questionario", "fontes_de_verificacao"}:
        situation.itens = split_csv_list(value)
    elif prop == "referencias_matriz":
        situation.referencias = split_csv_list(value)
    elif prop == "criterios":
        situation.criterios = split_csv_list(value)
    elif prop == "tipo_encaminhamento":
        situation.tipo_encaminhamento = value
    elif prop == "fundamentacao_encaminhamento":
        situation.fundamentacao_encaminhamento = value
    elif prop == "encaminhamento":
        situation.encaminhamento = value
    elif prop == "regra_de_identificacao":
        situation.regra = []


def parse_matrix(markdown: str) -> Matrix:
    text = normalize_text(markdown)
    title_match = re.search(r'^title:\s*"([^"]+)"', text, flags=re.M)
    title = title_match.group(1) if title_match else "Matriz de Planejamento"
    questao_geral = get_single_line(text, "questao_geral") or "[QUESTÃO GERAL DE AUDITORIA]"

    matches = list(re.finditer(r"^## Questão(?:\s+(\d+)|\s+Transversal)\s*-\s*(.+)$", text, flags=re.M))
    questions: list[Question] = []
    for index, match in enumerate(matches):
        start = match.start()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        content = text[start:end]
        raw_number = match.group(1) or ""
        question_text = get_single_line(content, "questao")
        transverse_id_match = re.match(r"^(Q[A-Z0-9]+)\.\s*", question_text)
        q_id = (
            f"Q{int(raw_number)}"
            if raw_number
            else (transverse_id_match.group(1) if transverse_id_match else "QT")
        )
        natureza = get_single_line(content, "natureza")
        gera_achado = parse_bool(get_single_line(content, "gera_achado"), default=True)
        legacy_criteria_fields = [
            field_name
            for field_name in ("metadados_criterios", "criterios_especificos")
            if re.search(rf"^{field_name}\s*:", content, flags=re.M)
        ]
        if legacy_criteria_fields:
            raise ValueError(
                f"{q_id}: blocos de critérios legados não são aceitos: "
                f"{', '.join(legacy_criteria_fields)}. Use somente o bloco criterios estruturado."
            )
        if re.search(r"^variantes_especificas\s*:", content, flags=re.M):
            raise ValueError(
                f"{q_id}: o bloco global variantes_especificas não é aceito. "
                "Use variantes aninhadas na situação."
            )
        q = Question(
            id=q_id,
            title=match.group(2).strip(),
            question=question_text or f"{q_id}. [QUESTÃO DE AUDITORIA]",
            natureza=natureza,
            gera_achado=gera_achado,
            subquestoes=parse_list(get_section_block(content, "subquestoes")),
            riscos=parse_list(get_section_block(content, "riscos")),
            fontes=parse_list(get_section_block(content, "fontes_de_informacao")),
            informacoes=parse_list(get_section_block(content, "informacoes_requeridas")),
            criterios=parse_criteria(get_section_block(content, "criterios"), q_id),
            criterios_comparabilidade=parse_list(get_section_block(content, "criterios_de_comparabilidade")),
            procedimentos=parse_list(get_section_block(content, "procedimentos")),
            evidencias=parse_list(get_section_block(content, "evidencias")),
            achados=parse_findings(get_section_block(content, "possiveis_achados")) if gera_achado else [],
            analise_permite_dizer=parse_list(get_section_block(content, "o_que_a_analise_permite_dizer")),
            limitacoes=parse_list(get_section_block(content, "limitacoes_e_cautelas")),
        )
        questions.append(q)

    return Matrix(title, questao_geral, questions)


def local_name(element: ET.Element) -> str:
    return element.tag.rsplit("}", 1)[-1]


def text_of(element: ET.Element) -> str:
    return "".join(t.text or "" for t in element.findall(f".//{W}t"))


def ensure_child(element: ET.Element, tag: str) -> ET.Element:
    child = element.find(tag)
    if child is None:
        child = ET.Element(tag)
        element.insert(0, child)
    return child


def set_paragraph_layout(paragraph: ET.Element, *, left_indent: int = 0, spacing_after: int | None = None) -> None:
    ppr = ensure_child(paragraph, f"{W}pPr")
    if left_indent:
        ind = ppr.find(f"{W}ind")
        if ind is None:
            ind = ET.SubElement(ppr, f"{W}ind")
        ind.set(f"{W}left", str(left_indent))
    if spacing_after is not None:
        spacing = ppr.find(f"{W}spacing")
        if spacing is None:
            spacing = ET.SubElement(ppr, f"{W}spacing")
        spacing.set(f"{W}after", str(spacing_after))


def set_paragraph_text(paragraph: ET.Element, text: str, *, bold: bool | None = None) -> None:
    first_run = paragraph.find(f"{W}r")
    base_rpr = copy.deepcopy(first_run.find(f"{W}rPr")) if first_run is not None and first_run.find(f"{W}rPr") is not None else ET.Element(f"{W}rPr")
    if bold is not None:
        for tag in ("b", "bCs"):
            existing = base_rpr.find(f"{W}{tag}")
            if bold and existing is None:
                ET.SubElement(base_rpr, f"{W}{tag}")
            elif not bold and existing is not None:
                base_rpr.remove(existing)

    for child in list(paragraph):
        if local_name(child) != "pPr":
            paragraph.remove(child)

    run = ET.SubElement(paragraph, f"{W}r")
    if len(base_rpr):
        run.append(base_rpr)
    text_el = ET.SubElement(run, f"{W}t")
    if text[:1].isspace() or text[-1:].isspace():
        text_el.set(f"{XML}space", "preserve")
    text_el.text = text


def set_paragraph_run_style(
    paragraph: ET.Element,
    *,
    font_name: str | None = None,
    font_size_pt: int | None = None,
    bold: bool | None = None,
) -> None:
    """Aplica formatação direta aos runs de um parágrafo.

    O primeiro parágrafo da linha de questão do template possui a fonte apenas
    em ``pPr/rPr``. Alguns editores acabam resolvendo essa combinação pela
    fonte padrão (Times New Roman). A formatação direta no run torna a saída
    determinística, independentemente do editor utilizado para abrir o DOCX.
    """

    for run in paragraph.findall(f"{W}r"):
        rpr = ensure_child(run, f"{W}rPr")
        if font_name:
            fonts = rpr.find(f"{W}rFonts")
            if fonts is None:
                fonts = ET.SubElement(rpr, f"{W}rFonts")
            for attribute in ("ascii", "hAnsi", "cs", "eastAsia"):
                fonts.set(f"{W}{attribute}", font_name)
        if font_size_pt is not None:
            half_points = str(max(1, int(font_size_pt * 2)))
            for tag in ("sz", "szCs"):
                size = rpr.find(f"{W}{tag}")
                if size is None:
                    size = ET.SubElement(rpr, f"{W}{tag}")
                size.set(f"{W}val", half_points)
        if bold is not None:
            for tag in ("b", "bCs"):
                existing = rpr.find(f"{W}{tag}")
                if bold:
                    if existing is None:
                        ET.SubElement(rpr, f"{W}{tag}")
                    else:
                        existing.attrib.pop(f"{W}val", None)
                elif existing is not None:
                    rpr.remove(existing)


def set_labeled_paragraph_text(paragraph: ET.Element, label: str, value: str) -> None:
    runs = paragraph.findall(f"{W}r")
    label_rpr = (
        copy.deepcopy(runs[0].find(f"{W}rPr"))
        if runs and runs[0].find(f"{W}rPr") is not None
        else ET.Element(f"{W}rPr")
    )
    value_run = next((run for run in runs[1:] if run.find(f"{W}rPr") is not None), None)
    value_rpr = (
        copy.deepcopy(value_run.find(f"{W}rPr"))
        if value_run is not None
        else ET.Element(f"{W}rPr")
    )

    for child in list(paragraph):
        if local_name(child) != "pPr":
            paragraph.remove(child)

    for text, properties in ((label, label_rpr), (f": {value}", value_rpr)):
        run = ET.SubElement(paragraph, f"{W}r")
        if len(properties):
            run.append(properties)
        text_element = ET.SubElement(run, f"{W}t")
        if text[:1].isspace() or text[-1:].isspace():
            text_element.set(f"{XML}space", "preserve")
        text_element.text = text


def clone_paragraph(
    template: ET.Element,
    text: str,
    *,
    bold: bool | None = None,
    left_indent: int = 0,
    spacing_after: int | None = None,
) -> ET.Element:
    paragraph = copy.deepcopy(template)
    set_paragraph_text(paragraph, text, bold=bold)
    set_paragraph_layout(paragraph, left_indent=left_indent, spacing_after=spacing_after)
    return paragraph


def clear_cell(cell: ET.Element) -> None:
    for child in list(cell):
        if local_name(child) != "tcPr":
            cell.remove(child)


def normalize_cell_paragraph(value: str | CellParagraph, *, bold: bool | None, spacing_after: int) -> CellParagraph:
    if isinstance(value, CellParagraph):
        paragraph = copy.copy(value)
        if paragraph.bold is None:
            paragraph.bold = bold
        return paragraph
    return CellParagraph(str(value), bold=bold, spacing_after=spacing_after)


def fill_cell(
    cell: ET.Element,
    texts: Iterable[str | CellParagraph],
    paragraph_template: ET.Element,
    *,
    bold: bool | None = None,
    spacing_after: int = 120,
) -> None:
    clear_cell(cell)
    values: list[CellParagraph] = []
    for value in texts:
        if isinstance(value, CellParagraph):
            if value.text.strip():
                values.append(normalize_cell_paragraph(value, bold=bold, spacing_after=spacing_after))
        elif value and str(value).strip():
            values.append(normalize_cell_paragraph(value, bold=bold, spacing_after=spacing_after))
    if not values:
        values = [CellParagraph(MISSING_MARKDOWN_PLACEHOLDER, bold=bold, spacing_after=spacing_after)]
    for value in values:
        cell.append(
            clone_paragraph(
                paragraph_template,
                value.text,
                bold=value.bold,
                left_indent=value.left_indent,
                spacing_after=value.spacing_after,
            )
        )


def first_paragraph(cell: ET.Element) -> ET.Element:
    paragraph = cell.find(f"{W}p")
    if paragraph is None:
        paragraph = ET.Element(f"{W}p")
    return paragraph


def move_leading_markdown_link_to_end(text: str) -> str:
    match = re.match(r"^(\[[^\]]+\]\([^)]+\)|https?://\S+)\s+(.+)$", text.strip())
    if not match:
        return text
    return f"{match.group(2).strip()} {match.group(1).strip()}"


def compact_display_identifiers(question: Question) -> dict[str, str]:
    """Cria IDs sequenciais apenas para a visualização da questão no DOCX."""
    identifiers = [
        item.id
        for collection in (
            question.riscos,
            question.fontes,
            question.informacoes,
            question.criterios_comparabilidade,
            question.procedimentos,
            question.evidencias,
        )
        for item in collection
        if item.id
    ]
    identifiers.extend(criterion.id for criterion in question.criterios)

    mapping: dict[str, str] = {}
    counters: dict[str, int] = {}
    for identifier in identifiers:
        if identifier in mapping:
            continue
        match = re.fullmatch(r"([A-Z]+)(\d+)(?:\.(\d+))?", identifier)
        if not match:
            mapping[identifier] = identifier
            continue
        letters, major, minor = match.groups()
        family = f"{letters}{major}." if minor is not None else letters
        counters[family] = counters.get(family, 0) + 1
        mapping[identifier] = f"{family}{counters[family]}"
    return mapping


def display_identifier(identifier: str, mapping: dict[str, str]) -> str:
    return mapping.get(identifier, identifier)


def remap_display_references(text: str, mapping: dict[str, str]) -> str:
    if not mapping:
        return text
    pattern = "|".join(re.escape(identifier) for identifier in sorted(mapping, key=len, reverse=True))
    return re.sub(
        rf"(?<![A-Za-z0-9_.])(?:{pattern})(?![A-Za-z0-9_.])",
        lambda match: mapping[match.group(0)],
        text,
    )


def format_items(items: Iterable[ListItem], mapping: dict[str, str] | None = None) -> list[str]:
    display_mapping = mapping or {}
    return [remap_display_references(item.raw, display_mapping) for item in items] or [
        MISSING_MARKDOWN_PLACEHOLDER
    ]


def format_question_text(question: Question) -> str:
    text = re.sub(r"^Q[A-Z0-9]+\.\s*", "", question.question).strip()
    prefix = question.id
    if question.natureza:
        return f"{prefix}: {text} ({question.natureza})"
    return f"{prefix}: {text}"


def is_levantamento(question: Question) -> bool:
    """Indica se a questão é descritiva/ de levantamento.

    A classificação é declarada no Markdown por meio de ``natureza: levantamento``.
    Mantê-la em um predicado único evita que o renderizador trate, por engano,
    uma questão descritiva como se tivesse risco e critério de conformidade.
    """

    return (question.natureza or "").strip().casefold() == "levantamento"


def format_risk_or_comparability(
    question: Question, mapping: dict[str, str] | None = None
) -> list[str]:
    if question.riscos:
        return format_items(question.riscos, mapping)
    if question.criterios_comparabilidade:
        return ["Critérios de comparabilidade:"] + format_items(
            question.criterios_comparabilidade, mapping
        )
    if question.natureza:
        return ["Não se aplica: questão de levantamento, sem formulação de risco de achado."]
    return [MISSING_MARKDOWN_PLACEHOLDER]


def format_criteria(
    question: Question, mapping: dict[str, str] | None = None
) -> list[str | CellParagraph]:
    display_mapping = mapping or {}
    general_criteria = [criterion for criterion in question.criterios if not criterion.especifico]
    specific_criteria = [criterion for criterion in question.criterios if criterion.especifico]
    criteria = [
        f"{display_identifier(criterion.id, display_mapping)}: {criterion.descricao}"
        for criterion in general_criteria
    ]
    if question.criterios_comparabilidade:
        criteria.extend(format_items(question.criterios_comparabilidade, display_mapping))
    if not criteria and not specific_criteria and question.natureza:
        return ["Não se aplica como critério de conformidade: análise orientada pelas fontes e pelos procedimentos definidos."]
    result: list[str | CellParagraph] = [move_leading_markdown_link_to_end(item) for item in criteria]
    if not result and not specific_criteria:
        result.append(MISSING_MARKDOWN_PLACEHOLDER)
    publico_anterior = None
    for criterio in specific_criteria:
        publico = criterio.publico
        if publico != publico_anterior:
            result.append(CellParagraph(publico, bold=True, spacing_after=60))
            publico_anterior = publico
        result.append(
            CellParagraph(
                f"{display_identifier(criterio.id, display_mapping)}: {criterio.descricao}",
                left_indent=240,
                spacing_after=80,
            )
        )
    return result


def format_findings_or_analysis(
    question: Question, mapping: dict[str, str] | None = None
) -> list[str | CellParagraph]:
    display_mapping = mapping or {}
    lines: list[str | CellParagraph] = []
    for finding in question.achados:
        if finding.title:
            lines.append(
                CellParagraph(
                    f"{finding.title.rstrip('.')}.",
                    bold=True,
                    left_indent=0,
                    spacing_after=80,
                )
            )
        for situation in finding.situacoes:
            references = [
                display_identifier(identifier, display_mapping)
                for identifier in dict.fromkeys(situation.referencias + situation.criterios)
            ]
            description = f"{situation.descricao.rstrip('.')}."
            if references:
                description += f"[{', '.join(references)}];"
            lines.append(CellParagraph(description, left_indent=360, spacing_after=40))
            if situation.tipo_encaminhamento:
                lines.append(
                    CellParagraph(
                        f"Tipo: {situation.tipo_encaminhamento};",
                        left_indent=720,
                        spacing_after=40,
                    )
                )
            if situation.fundamentacao_encaminhamento:
                lines.append(
                    CellParagraph(
                        f"Fundamentação: {situation.fundamentacao_encaminhamento};",
                        left_indent=720,
                        spacing_after=40,
                    )
                )
            if situation.encaminhamento:
                lines.append(
                    CellParagraph(
                        f"Encaminhamento: {situation.encaminhamento}",
                        left_indent=720,
                        spacing_after=100,
                    )
                )
            for variante in situation.variantes:
                (
                    _, materialized_criteria, materialized_type,
                    materialized_foundation, materialized_referral,
                ) = (
                    materialize_situation_variant(situation, variante)
                )
                lines.append(
                    CellParagraph(
                        f"{variante.publico}: "
                        f"[{', '.join(display_identifier(item, display_mapping) for item in materialized_criteria)}];",
                        bold=True,
                        left_indent=720,
                        spacing_after=40,
                    )
                )
                lines.append(
                    CellParagraph(
                        f"Tipo: {materialized_type};",
                        left_indent=1080,
                        spacing_after=40,
                    )
                )
                lines.append(
                    CellParagraph(
                        f"Fundamentação: {materialized_foundation};",
                        left_indent=1080,
                        spacing_after=40,
                    )
                )
                lines.append(
                    CellParagraph(
                        f"Encaminhamento: {materialized_referral}",
                        left_indent=1080,
                        spacing_after=100,
                    )
                )

    if lines:
        return lines

    if not question.gera_achado or question.natureza:
        lines.append("Não se aplica: questão de levantamento, sem geração de achado individual.")
        if question.analise_permite_dizer:
            lines.append("O que a análise permite dizer:")
            lines.extend(format_items(question.analise_permite_dizer, display_mapping))
        if question.limitacoes:
            lines.append("Limitações e cautelas:")
            lines.extend(format_items(question.limitacoes, display_mapping))
        return lines

    return [MISSING_MARKDOWN_PLACEHOLDER]


def remove_table_rows(table: ET.Element, row_indexes: Iterable[int]) -> None:
    rows = table.findall(f"{W}tr")
    for index in sorted(row_indexes, reverse=True):
        if 0 <= index < len(rows):
            table.remove(rows[index])


def remove_floating_table_properties(table: ET.Element) -> None:
    tbl_pr = table.find(f"{W}tblPr")
    if tbl_pr is None:
        return
    for tag in ("tblpPr", "tblOverlap"):
        element = tbl_pr.find(f"{W}{tag}")
        if element is not None:
            tbl_pr.remove(element)


def _cell_width(cell: ET.Element) -> int | None:
    tc_pr = cell.find(f"{W}tcPr")
    if tc_pr is None:
        return None
    tc_w = tc_pr.find(f"{W}tcW")
    if tc_w is None:
        return None
    try:
        return int(tc_w.get(f"{W}w", ""))
    except (TypeError, ValueError):
        return None


def _set_cell_width(cell: ET.Element, width: int) -> None:
    tc_pr = cell.find(f"{W}tcPr")
    if tc_pr is None:
        tc_pr = ET.Element(f"{W}tcPr")
        cell.insert(0, tc_pr)
    tc_w = tc_pr.find(f"{W}tcW")
    if tc_w is None:
        tc_w = ET.Element(f"{W}tcW")
        tc_pr.insert(0, tc_w)
    tc_w.set(f"{W}w", str(max(1, width)))
    tc_w.set(f"{W}type", "dxa")


def _scaled_widths(widths: list[int], target_total: int) -> list[int]:
    """Redimensiona larguras preservando proporções e o total da tabela."""

    if not widths:
        return []
    target_total = max(len(widths), target_total)
    source_total = sum(max(1, width) for width in widths)
    raw = [max(1, width) * target_total / source_total for width in widths]
    result = [max(1, int(value)) for value in raw]
    remainder = target_total - sum(result)
    # Distribui o arredondamento de modo determinístico, sem alterar a ordem.
    step = 1 if remainder >= 0 else -1
    for index in range(abs(remainder)):
        position = index % len(result)
        if step < 0 and result[position] <= 1:
            continue
        result[position] += step
    return result


def remove_table_columns(table: ET.Element, column_indexes: Iterable[int]) -> None:
    """Remove colunas de uma tabela Word e mantém a grade visual consistente.

    As tabelas de detalhamento do template não usam células mescladas nas
    colunas de dados. Ainda assim, a função atualiza tanto ``tblGrid`` quanto
    ``tcW`` das linhas restantes, evitando que a retirada de uma coluna deixe
    uma tabela estreita ou com larguras conflitantes no DOCX.
    """

    indexes = sorted({index for index in column_indexes if index >= 0}, reverse=True)
    if not indexes:
        return

    rows = table.findall(f"{W}tr")
    # Use a primeira linha completa para preservar a distribuição de larguras
    # definida pelo template. As linhas de cabeçalho e dados têm a mesma grade.
    source_widths: list[int] = []
    for row in rows:
        cells = row.findall(f"{W}tc")
        widths = [_cell_width(cell) for cell in cells]
        if len(widths) > max(indexes, default=-1) and all(width is not None for width in widths):
            source_widths = [int(width) for width in widths if width is not None]
            break

    grid = table.find(f"{W}tblGrid")
    grid_columns = grid.findall(f"{W}gridCol") if grid is not None else []
    grid_widths: list[int] = []
    for column in grid_columns:
        try:
            grid_widths.append(int(column.get(f"{W}w", "")))
        except (TypeError, ValueError):
            grid_widths.append(1)
    target_total = sum(source_widths) if source_widths else sum(grid_widths)

    for row in rows:
        cells = row.findall(f"{W}tc")
        for index in indexes:
            if index < len(cells):
                row.remove(cells[index])

    remaining_source = [
        width for index, width in enumerate(source_widths) if index not in indexes
    ]
    new_widths = _scaled_widths(remaining_source, target_total) if remaining_source else []

    if grid is not None:
        for index in indexes:
            if index < len(grid_columns):
                grid.remove(grid_columns[index])
        new_grid_columns = grid.findall(f"{W}gridCol")
        for column, width in zip(new_grid_columns, new_widths):
            column.set(f"{W}w", str(width))

    for row in rows:
        for cell, width in zip(row.findall(f"{W}tc"), new_widths):
            _set_cell_width(cell, width)


def build_question_summary_table(template_table: ET.Element, question: Question) -> ET.Element:
    table = copy.deepcopy(template_table)
    remove_floating_table_properties(table)
    rows = table.findall(f"{W}tr")
    if len(rows) < 4:
        raise ValueError("A tabela modelo deve possuir pelo menos 4 linhas.")

    row0_cell = rows[0].find(f"{W}tc")
    if row0_cell is None:
        raise ValueError("A tabela modelo deve possuir uma linha de questão.")

    row0_templates = row0_cell.findall(f"{W}p")
    question_p = row0_templates[0] if row0_templates else ET.Element(f"{W}p")
    subquestion_p = row0_templates[1] if len(row0_templates) > 1 else question_p
    clear_cell(row0_cell)
    question_paragraph = clone_paragraph(question_p, format_question_text(question), bold=True)
    set_paragraph_run_style(
        question_paragraph,
        font_name="Arial",
        font_size_pt=10,
        bold=True,
    )
    row0_cell.append(question_paragraph)
    for subquestion in question.subquestoes:
        subquestion_paragraph = clone_paragraph(subquestion_p, subquestion.text)
        set_paragraph_run_style(
            subquestion_paragraph,
            font_name="Arial",
            font_size_pt=10,
        )
        row0_cell.append(subquestion_paragraph)

    if is_levantamento(question):
        # Levantamentos não formulam risco de achado; a linha azul de riscos
        # não deve aparecer no documento final.
        remove_table_rows(table, [1, 2, 3])
    else:
        row1_cell = rows[1].find(f"{W}tc")
        if row1_cell is None:
            raise ValueError("A tabela modelo deve possuir uma linha de riscos.")
        risk_p = first_paragraph(row1_cell)
        display_mapping = compact_display_identifiers(question)
        fill_cell(row1_cell, format_risk_or_comparability(question, display_mapping), risk_p)
        remove_table_rows(table, [2, 3])
    return table


def build_question_details_table(template_table: ET.Element, question: Question) -> ET.Element:
    table = copy.deepcopy(template_table)
    remove_floating_table_properties(table)
    rows = table.findall(f"{W}tr")
    if len(rows) < 4:
        raise ValueError("A tabela modelo deve possuir pelo menos 4 linhas.")

    header_cells = rows[2].findall(f"{W}tc")
    data_cells = rows[3].findall(f"{W}tc")
    if len(header_cells) < 6 or len(data_cells) < 6:
        raise ValueError("A tabela modelo deve possuir a estrutura 6-colunas esperada.")

    headers = [
        "FONTES DE INFORMAÇÃO",
        "INFORMAÇÕES REQUERIDAS",
        "CRITÉRIOS",
        "PROCEDIMENTO DE AUDITORIA",
        "POSSÍVEIS EVIDÊNCIAS",
        "POSSÍVEIS ACHADOS" if question.gera_achado else "ANÁLISE / RESULTADOS",
    ]
    for cell, header in zip(header_cells, headers):
        fill_cell(cell, [header], first_paragraph(cell), bold=True, spacing_after=0)

    display_mapping = compact_display_identifiers(question)
    cell_payloads = [
        format_items(question.fontes, display_mapping),
        format_items(question.informacoes, display_mapping),
        format_criteria(question, display_mapping),
        format_items(question.procedimentos, display_mapping),
        format_items(question.evidencias, display_mapping),
        format_findings_or_analysis(question, display_mapping),
    ]
    for cell, payload in zip(data_cells, cell_payloads):
        fill_cell(cell, payload, first_paragraph(cell))

    remove_table_rows(table, [0, 1])
    if is_levantamento(question):
        # A análise de levantamento não tem critério de conformidade. A
        # coluna é retirada, em vez de exibir uma célula vazia ou uma ressalva.
        remove_table_columns(table, [2])
    return table


def build_question_tables(template_table: ET.Element, question: Question) -> list[ET.Element]:
    return [
        build_question_summary_table(template_table, question),
        build_question_details_table(template_table, question),
    ]


def find_template_parts(body: ET.Element) -> tuple[list[ET.Element], ET.Element, list[ET.Element], ET.Element]:
    children = list(body)
    table_positions = [(idx, child) for idx, child in enumerate(children) if local_name(child) == "tbl"]
    if not table_positions:
        raise ValueError("Template sem tabela de matriz.")
    first_table_index, first_table = table_positions[0]
    matrix_table = copy.deepcopy(first_table)
    if len(matrix_table.findall(f"{W}tr")) < 4:
        if len(table_positions) < 2:
            raise ValueError("Template sem as tabelas de questão e detalhamento esperadas.")
        second_table = table_positions[1][1]
        if len(second_table.findall(f"{W}tr")) < 2:
            raise ValueError("Template sem as tabelas de questão e detalhamento esperadas.")
        for row in second_table.findall(f"{W}tr"):
            matrix_table.append(copy.deepcopy(row))
    signature_table = None
    if len(table_positions) > 1:
        candidate = table_positions[-1][1]
        if candidate is not first_table and len(candidate.findall(f"{W}tr")) <= 6:
            signature_table = candidate
    sect_pr = children[-1] if children and local_name(children[-1]) == "sectPr" else ET.Element(f"{W}sectPr")
    # Preserve somente os elementos que antecedem a primeira tabela-modelo.
    # Isso evita carregar conteúdo de uma matriz anterior como página residual.
    intro = [child for child in children[:first_table_index] if local_name(child) != "sectPr"]
    return intro, matrix_table, ([signature_table] if signature_table is not None else []), sect_pr


def replace_intro_text(intro: list[ET.Element], matrix: Matrix) -> list[ET.Element]:
    result = [copy.deepcopy(element) for element in intro]
    text_paragraphs = [element for element in result if local_name(element) == "p"]
    non_empty = [p for p in text_paragraphs if text_of(p).strip()]
    if non_empty:
        set_paragraph_text(non_empty[0], "MATRIZ DE PLANEJAMENTO", bold=True)
    if len(non_empty) > 1:
        set_paragraph_text(non_empty[1], f"QUESTÃO GERAL DE AUDITORIA: {matrix.questao_geral}")

    return result


def page_break_paragraph() -> ET.Element:
    paragraph = ET.Element(f"{W}p")
    run = ET.SubElement(paragraph, f"{W}r")
    page_break = ET.SubElement(run, f"{W}br")
    page_break.set(f"{W}type", "page")
    return paragraph
