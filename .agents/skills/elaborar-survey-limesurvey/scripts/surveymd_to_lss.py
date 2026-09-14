#!/usr/bin/env python3
"""Converte Markdown SurveyMD em um arquivo .lss importável no LimeSurvey.

Destaques desta versão:
  - Suporta o tipo macro [adoption] para questionários de autoavaliação.
  - Gera automaticamente pergunta principal, não aplicabilidade, lei, estudo, razões e
    checklist de detalhamento.
  - Suporta lógicas condicionais compatíveis com os padrões do .lss original:
      visible_if: q1011 == sim
      visible_if: q1022 in [adpar, admai]
      visible_if: q1022nsa == A
      visible_if: q2112ext.B == Y
      visible_if: q2112ext[B] == Y
      visible_if: (q1 == sim and q2 in [A, B]) or q3.C == Y
      visible_if: raw: ((900001X1000X10000.NAOK == "sim"))

Uso:
    python surveymd_to_lss.py entrada.md saida.lss --sid 900001

Dependências: apenas biblioteca padrão do Python.
"""

from __future__ import annotations

import argparse
import datetime as dt
import html
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

from survey_utils import (
    filter_survey_by_target as filter_target_survey,
    split_frontmatter,
    survey_targets,
    target_output_path,
    validate_target_config,
)


TYPE_MAP = {
    "single": "L",
    "list": "L",
    "radio": "L",
    "lista": "L",
    "single_comment": "O",
    "list_comment": "O",
    "lista_com_comentario": "O",
    "multi": "M",
    "multiple": "M",
    "checkbox": "M",
    "multipla": "M",
    "múltipla": "M",
    "short": "S",
    "text": "S",
    "texto_curto": "S",
    "long": "T",
    "textarea": "T",
    "texto_longo": "T",
    "upload": "|",
    "file": "|",
    "arquivo": "|",
    "multi_text": "Q",
    "multitext": "Q",
    "varios_textos": "Q",
    "array": "F",
    "matrix": "F",
    "matriz": "F",
    "array_numbers": ":",
    "array_number": ":",
    "numeric_array": ":",
    "array_numeros": ":",
    "matriz_numerica": ":",
}

MACRO_TYPES = {"adoption", "adocao", "adoção"}

QUESTION_FIELDS = [
    "qid", "parent_qid", "sid", "gid", "type", "title", "question", "preg", "help",
    "other", "mandatory", "question_order", "language", "scale_id", "same_default",
    "relevance", "modulename",
]
GROUP_FIELDS = [
    "gid", "sid", "group_name", "group_order", "description", "language",
    "randomization_group", "grelevance",
]
ANSWER_FIELDS = [
    "qid", "code", "answer", "sortorder", "assessment_value", "language", "scale_id",
]
CONDITION_FIELDS = [
    "cid", "qid", "cqid", "cfieldname", "method", "value", "scenario",
]
ATTRIBUTE_FIELDS = ["qid", "attribute", "value", "language"]

SURVEY_FIELDS = [
    "sid", "gsid", "admin", "expires", "startdate", "adminemail", "anonymized", "faxto",
    "format", "savetimings", "template", "language", "additional_languages", "datestamp",
    "usecookie", "allowregister", "allowsave", "autonumber_start", "autoredirect",
    "allowprev", "printanswers", "ipaddr", "refurl", "showsurveypolicynotice",
    "publicstatistics", "publicgraphs", "listpublic", "htmlemail", "sendconfirmation",
    "tokenanswerspersistence", "assessments", "usecaptcha", "usetokens", "bounce_email",
    "attributedescriptions", "emailresponseto", "emailnotificationto", "tokenlength",
    "showxquestions", "showgroupinfo", "shownoanswer", "showqnumcode", "bouncetime",
    "bounceprocessing", "bounceaccounttype", "bounceaccounthost", "bounceaccountpass",
    "bounceaccountencryption", "bounceaccountuser", "showwelcome", "showprogress",
    "questionindex", "navigationdelay", "nokeyboard", "alloweditaftercompletion",
    "googleanalyticsstyle", "googleanalyticsapikey",
]

LANG_FIELDS = [
    "surveyls_survey_id", "surveyls_language", "surveyls_title", "surveyls_description",
    "surveyls_welcometext", "surveyls_endtext", "surveyls_policy_notice",
    "surveyls_policy_error", "surveyls_policy_notice_label", "surveyls_url",
    "surveyls_urldescription", "surveyls_email_invite_subj", "surveyls_email_invite",
    "surveyls_email_remind_subj", "surveyls_email_remind", "surveyls_email_register_subj",
    "surveyls_email_register", "surveyls_email_confirm_subj", "surveyls_email_confirm",
    "surveyls_dateformat", "surveyls_attributecaptions", "email_admin_notification_subj",
    "email_admin_notification", "email_admin_responses_subj", "email_admin_responses",
    "surveyls_numberformat", "attachments",
]

SURVEY_FIELD_MAX_LENGTHS = {
    "admin": 50,
    "adminemail": 254,
    "bounce_email": 254,
}

DEFAULT_ADOPTION_OPTIONS = [
    ("naoad", "Não adota."),
    ("adfor", "Há decisão formal ou plano aprovado para adotá-lo."),
    ("admen", "Adota em menor parte."),
    ("adpar", "Adota parcialmente."),
    ("admai", "Adota em maior parte ou totalmente."),
    ("naoap", "Não se aplica."),
]

DEFAULT_NSA_OPTIONS = [
    ("A", "Não se aplica porque há lei e/ou norma, externa à organização, que impede a implementação desta prática."),
    ("B", "Não se aplica porque há estudos que demonstram que o custo de implementar este controle é maior que o benefício que seria obtido dessa implementação."),
    ("C", "Não se aplica por outras razões."),
]


@dataclass
class Option:
    code: str
    text: str


@dataclass
class Scale:
    code: str
    type: str = "single"
    options: List[Option] = field(default_factory=list)


@dataclass
class Question:
    code: str
    type: str
    text_lines: List[str] = field(default_factory=list)
    help: str = ""
    mandatory: bool = False
    scale: Optional[str] = None
    alternatives: List[Option] = field(default_factory=list)
    subquestions: List[Option] = field(default_factory=list)
    subgroup: str = ""
    visible_if: str = "1"
    other: bool = False
    attrs: Dict[str, str] = field(default_factory=dict)
    qid: Optional[int] = None
    gid: Optional[int] = None

    def text(self) -> str:
        return "\n".join(self.text_lines).strip()


@dataclass
class Group:
    code: str
    title: str
    description_lines: List[str] = field(default_factory=list)
    gid: Optional[int] = None
    questions: List[Question] = field(default_factory=list)


@dataclass
class Survey:
    meta: Dict[str, str] = field(default_factory=dict)
    scales: Dict[str, Scale] = field(default_factory=dict)
    groups: List[Group] = field(default_factory=list)


# ----------------------------
# Parser do Markdown SurveyMD
# ----------------------------


def parse_option(line: str) -> Option:
    """Aceita '- codigo | texto' ou '- codigo: texto'."""
    item = line.strip()
    if not item.startswith("-") and ("|" in item or ":" in item):
        item = "- " + item
    if not item.startswith("-"):
        raise ValueError(f"Item de lista inválido: {line}")
    item = item[1:].strip()
    if "|" in item:
        code, text = item.split("|", 1)
    elif ":" in item:
        code, text = item.split(":", 1)
    else:
        raise ValueError(f"Use '- codigo | texto' ou '- codigo: texto': {line}")
    code = code.strip()
    text = text.strip()
    if not code:
        raise ValueError(f"Código vazio em item: {line}")
    return Option(code=code, text=text)


def parse_bool(value: object, default: bool = False) -> bool:
    if value is None:
        return default
    value = str(value).strip().lower()
    if value == "":
        return default
    return value in {"y", "yes", "true", "sim", "s", "1", "on"}


def parse_group_heading(line: str) -> Group:
    # ## Grupo: codigo | Título
    m = re.match(r"^##\s+Grupo:\s*(.+?)\s*$", line, flags=re.I)
    if not m:
        raise ValueError(f"Cabeçalho de grupo inválido: {line}")
    rest = m.group(1).strip()
    if "|" in rest:
        code, title = rest.split("|", 1)
    elif "—" in rest:
        code, title = rest.split("—", 1)
    elif " - " in rest:
        code, title = rest.split(" - ", 1)
    else:
        code, title = rest, rest
    return Group(code=code.strip(), title=title.strip())


def parse_question_heading(line: str) -> Question:
    # ### q1111 [single]
    m = re.match(r"^###\s+([A-Za-z0-9_]+)\s*\[([A-Za-z0-9_|:çãõáéíóúâêôàü\-]+)\]\s*$", line, flags=re.I)
    if not m:
        raise ValueError(
            f"Cabeçalho de questão inválido: {line}\n"
            "Use: ### codigo [tipo], por exemplo: ### q1111 [single] ou ### q1111 [adoption]"
        )
    code = m.group(1).strip()
    typ = m.group(2).strip().lower()
    if typ not in TYPE_MAP and typ not in TYPE_MAP.values() and typ not in MACRO_TYPES:
        raise ValueError(f"Tipo de questão não suportado em {code}: {typ}")
    return Question(code=code, type=typ)


def is_directive(line: str) -> bool:
    return bool(re.match(r"^[A-Za-z_][A-Za-z0-9_]*\s*:", line))


def is_option_line(line: str) -> bool:
    return bool(re.match(r"^\s*-?\s*[A-Za-z0-9_]+\s*(?:\||:)\s*.+$", line))


def parse_markdown(path: Path) -> Survey:
    meta, lines = split_frontmatter(path.read_text(encoding="utf-8"))
    survey = Survey(meta=meta)
    ensure_builtin_scales(survey)

    current_scale: Optional[Scale] = None
    current_group: Optional[Group] = None
    current_question: Optional[Question] = None
    mode: Optional[str] = None
    seen_title = False

    def close_question() -> None:
        nonlocal current_question, mode
        current_question = None
        mode = None

    def close_scale() -> None:
        nonlocal current_scale, mode
        current_scale = None
        mode = None

    for lineno, raw in enumerate(lines, 1):
        line = raw.rstrip()

        if not line.strip():
            if mode == "text" and current_question:
                current_question.text_lines.append("")
            continue

        if line.startswith("# ") and not seen_title:
            seen_title = True
            survey.meta.setdefault("title", line[2:].strip())
            close_question()
            close_scale()
            continue

        if re.match(r"^##\s+Escala:", line, flags=re.I):
            close_question()
            m = re.match(r"^##\s+Escala:\s*(.+?)\s*$", line, flags=re.I)
            assert m is not None
            code = m.group(1).strip()
            current_scale = Scale(code=code)
            survey.scales[code] = current_scale
            current_group = None
            mode = "scale"
            continue

        if re.match(r"^##\s+Grupo:", line, flags=re.I):
            close_question()
            close_scale()
            current_group = parse_group_heading(line)
            survey.groups.append(current_group)
            mode = "group_description"
            continue

        if line.startswith("### "):
            close_scale()
            if current_group is None:
                raise ValueError(f"Questão fora de grupo na linha {lineno}: {line}")
            current_question = parse_question_heading(line)
            current_group.questions.append(current_question)
            mode = "text"
            continue

        if current_scale is not None:
            if line.lower().startswith("type:"):
                current_scale.type = line.split(":", 1)[1].strip().lower()
            elif line.lstrip().startswith("-"):
                current_scale.options.append(parse_option(line))
            else:
                raise ValueError(f"Linha inesperada em escala, linha {lineno}: {line}")
            continue

        if current_group is not None and current_question is None:
            if line.startswith(">"):
                current_group.description_lines.append(line.lstrip("> ").strip())
            elif line.lower().startswith("description:"):
                current_group.description_lines.append(line.split(":", 1)[1].strip())
            else:
                current_group.description_lines.append(line.strip())
            continue

        if current_question is not None:
            low = line.strip().lower()

            if low in {"alternatives:", "alternativas:", "options:", "opcoes:", "opções:", "columns:", "colunas:"}:
                mode = "alternatives"
                continue

            if low in {"subquestions:", "subquestoes:", "subquestões:", "rows:", "linhas:", "detail_options:", "detalhamento:"}:
                mode = "subquestions"
                continue

            if mode == "alternatives" and is_option_line(line):
                current_question.alternatives.append(parse_option(line))
                continue

            if mode == "subquestions" and is_option_line(line):
                current_question.subquestions.append(parse_option(line))
                continue

            if ":" in line and is_directive(line):
                key, value = line.split(":", 1)
                key = key.strip().lower()
                value = value.strip()
                apply_question_directive(current_question, key, value)
                continue

            mode = "text"
            current_question.text_lines.append(line)
            continue

    repeat_group_descriptions(survey)
    expand_adoption_macros(survey)
    expand_common_evidence_questions(survey)
    validate_target_config(survey)
    fill_empty_groups_with_acknowledgement(survey)
    validate_survey(survey)
    return survey


def apply_question_directive(q: Question, key: str, value: str) -> None:
    if key in {"mandatory", "obrigatoria", "obrigatória"}:
        q.mandatory = parse_bool(value)
    elif key == "scale":
        q.scale = value
    elif key in {"help", "ajuda"}:
        q.help = value
    elif key == "subgroup":
        q.subgroup = value
    elif key in {"visible_if", "relevance", "relevancia", "relevância"}:
        q.visible_if = value or "1"
    elif key == "other":
        q.other = parse_bool(value)
    elif key in {"title", "question"}:
        # Útil para [adoption]; para questões comuns também vira o texto da pergunta.
        q.text_lines.append(value)
    elif key in {"explain", "evidence_text", "evidence_if", "repeat_group_description"}:
        q.attrs[key] = value
    elif key in {
        "evidence", "evidence_type", "evidence_mandatory", "evidence_allowed_filetypes",
        "evidence_min_files", "evidence_max_files", "evidence_suffix",
    }:
        q.attrs[key] = value
    elif key in {
        "allowed_filetypes", "min_files", "max_files", "min_answers", "max_answers", "hide_tip",
        "exclude_all_others",
        "input_boxes", "multiflexible_min", "multiflexible_max", "multiflexible_step",
        # Diretivas específicas do macro adoption.
        "adoption_scale", "nsa_scale",
        "nsa", "nsa_text", "lei", "lei_text", "est", "est_text", "raz", "raz_text",
        "detail", "detail_text", "detail_mandatory", "detail_min_answers", "detail_max_answers",
        "detail_hide_tip", "prefix_code", "nsa_suffix", "lei_suffix", "est_suffix",
        "raz_suffix", "detail_suffix", "target",
    }:
        q.attrs[key] = value
    else:
        # Não trate qualquer "chave: valor" em texto jurídico como erro.
        q.text_lines.append(f"{key}: {value}")


# ----------------------------
# Macro [adoption]
# ----------------------------


def ensure_builtin_scales(survey: Survey) -> None:
    survey.scales.setdefault(
        "adocao",
        Scale(code="adocao", type="single", options=[Option(c, t) for c, t in DEFAULT_ADOPTION_OPTIONS]),
    )
    survey.scales.setdefault(
        "nao_aplicabilidade",
        Scale(code="nao_aplicabilidade", type="single", options=[Option(c, t) for c, t in DEFAULT_NSA_OPTIONS]),
    )


def get_attr(q: Question, key: str, default: str = "") -> str:
    value = q.attrs.get(key, default)
    return default if value is None else str(value)


def clone_common_visibility(source: Question, target: Question) -> None:
    target.visible_if = source.visible_if or "1"


def question_text_or_code(q: Question) -> str:
    return q.text() or q.code


def unique_group_code(base_code: str, used_codes: set[str]) -> str:
    code = base_code
    suffix = 2
    while code in used_codes:
        code = f"{base_code}_{suffix}"
        suffix += 1
    used_codes.add(code)
    return code


def clone_group_shell(group: Group, code: str) -> Group:
    return Group(
        code=code,
        title=group.title,
        description_lines=list(group.description_lines),
    )


def repeat_group_descriptions(survey: Survey) -> None:
    used_codes: set[str] = set()
    rewritten_groups: List[Group] = []

    for group in survey.groups:
        if not group.questions:
            group.code = unique_group_code(group.code, used_codes)
            rewritten_groups.append(group)
            continue

        current_group: Optional[Group] = None
        segment_count = 0

        def ensure_segment_group() -> Group:
            nonlocal current_group, segment_count
            if current_group is None:
                segment_count += 1
                base_code = group.code if segment_count == 1 else f"{group.code}_parte{segment_count}"
                current_group = clone_group_shell(group, unique_group_code(base_code, used_codes))
                rewritten_groups.append(current_group)
            return current_group

        for q in group.questions:
            repeat = parse_bool(q.attrs.get("repeat_group_description", "false"), default=False)
            if repeat:
                repeated_group = clone_group_shell(group, unique_group_code(f"{group.code}_{q.code}", used_codes))
                repeated_group.questions.append(q)
                rewritten_groups.append(repeated_group)
                current_group = repeated_group
                continue

            ensure_segment_group().questions.append(q)

    survey.groups = rewritten_groups


def expand_adoption_macros(survey: Survey) -> None:
    """Substitui cada questão [adoption] por um bloco de questões LimeSurvey comum."""
    for group in survey.groups:
        expanded: List[Question] = []
        for q in group.questions:
            if q.type.lower() not in MACRO_TYPES:
                expanded.append(q)
                continue
            expanded.extend(make_adoption_questions(q))
        group.questions = expanded


def make_adoption_questions(q: Question) -> List[Question]:
    base = q.code
    obsolete_evidence_keys = {
        "evidence", "evidence_type", "evidence_mandatory", "evidence_allowed_filetypes",
        "evidence_min_files", "evidence_max_files", "evidence_suffix",
    }
    used_obsolete = obsolete_evidence_keys.intersection(q.attrs)
    if used_obsolete:
        raise ValueError(
            f"Campo evidence obsoleto em {base}: use evidence_text para descrever a evidência."
        )

    adoption_scale = get_attr(q, "adoption_scale", q.scale or "adocao")
    nsa_scale = get_attr(q, "nsa_scale", "nao_aplicabilidade")
    inherited_attrs = {k: v for k, v in q.attrs.items() if k == "target"}

    nsa_enabled = parse_bool(get_attr(q, "nsa", "true"), default=True)
    nsa_suffix = get_attr(q, "nsa_suffix", "nsa")
    lei_enabled = parse_bool(get_attr(q, "lei", "true"), default=True)
    est_enabled = parse_bool(get_attr(q, "est", "true"), default=True)
    raz_enabled = parse_bool(get_attr(q, "raz", "true"), default=True)
    lei_suffix = get_attr(q, "lei_suffix", "lei")
    est_suffix = get_attr(q, "est_suffix", "est")
    raz_suffix = get_attr(q, "raz_suffix", "raz")

    detail_enabled = parse_bool(get_attr(q, "detail", "true"), default=True) and bool(q.subquestions)
    detail_suffix = get_attr(q, "detail_suffix", "ext")

    main = Question(
        code=base,
        type="single",
        text_lines=[question_text_or_code(q)],
        help=q.help,
        mandatory=q.mandatory,
        scale=adoption_scale,
        subgroup=q.subgroup,
        visible_if=q.visible_if,
        attrs={k: v for k, v in q.attrs.items() if k in {"hide_tip", "target", "explain"}},
    )

    out: List[Question] = [main]

    if nsa_enabled:
        nsa = Question(
            code=f"{base}{nsa_suffix}",
            type="single",
            text_lines=[get_attr(q, "nsa_text", "**Justifique a não aplicabilidade do item:**")],
            mandatory=True,
            scale=nsa_scale,
            visible_if=f"{base} == naoap",
            attrs=dict(inherited_attrs),
        )
        out.append(nsa)

        if lei_enabled:
            out.append(Question(
                code=f"{base}{lei_suffix}",
                type="short",
                text_lines=[get_attr(q, "lei_text", "**Indique que leis e/ou normas são essas:**")],
                mandatory=True,
                visible_if=f"{base}{nsa_suffix} == A",
                attrs=dict(inherited_attrs),
            ))
        if est_enabled:
            out.append(Question(
                code=f"{base}{est_suffix}",
                type="short",
                text_lines=[get_attr(q, "est_text", "**Identifique esses estudos:**")],
                mandatory=True,
                visible_if=f"{base}{nsa_suffix} == B",
                attrs=dict(inherited_attrs),
            ))
        if raz_enabled:
            out.append(Question(
                code=f"{base}{raz_suffix}",
                type="short",
                text_lines=[get_attr(q, "raz_text", "**Explique que razões são essas:**")],
                mandatory=True,
                visible_if=f"{base}{nsa_suffix} == C",
                attrs=dict(inherited_attrs),
            ))

    if detail_enabled:
        detail = Question(
            code=f"{base}{detail_suffix}",
            type="multi",
            text_lines=[get_attr(q, "detail_text", "**Visando explicitar melhor o grau de adoção do controle, marque abaixo uma ou mais opções que majoritariamente caracterizam sua organização:**")],
            mandatory=parse_bool(get_attr(q, "detail_mandatory", "false"), default=False),
            subquestions=list(q.subquestions),
            visible_if=f"{base} in [adpar, admai]",
            attrs=dict(inherited_attrs),
        )
        detail.attrs["hide_tip"] = get_attr(q, "detail_hide_tip", "1")
        if get_attr(q, "detail_min_answers", ""):
            detail.attrs["min_answers"] = get_attr(q, "detail_min_answers")
        if get_attr(q, "detail_max_answers", ""):
            detail.attrs["max_answers"] = get_attr(q, "detail_max_answers")
        out.append(detail)

    evidence_text = get_attr(q, "evidence_text", "").strip()
    if evidence_text:
        out.append(Question(
            code=f"{base}evi",
            type="upload",
            text_lines=[evidence_text],
            mandatory=True,
            visible_if=f"{base} in [adpar, admai]",
            attrs={
                **dict(inherited_attrs),
                "allowed_filetypes": "pdf, docx, zip",
                "min_files": "1",
                "max_files": "1",
            },
        ))

    return out


def expand_common_evidence_questions(survey: Survey) -> None:
    """Adiciona perguntas de upload para questões comuns com evidence_text."""
    for group in survey.groups:
        expanded: List[Question] = []
        for q in group.questions:
            expanded.append(q)
            if q.type.lower() in MACRO_TYPES or q.type.lower() in {"upload", "file", "arquivo", "|"}:
                continue
            evidence_text = get_attr(q, "evidence_text", "").strip()
            if not evidence_text:
                continue
            inherited_attrs = {k: v for k, v in q.attrs.items() if k == "target"}
            expanded.append(Question(
                code=f"{q.code}evi",
                type="upload",
                text_lines=[evidence_text],
                mandatory=True,
                visible_if=evidence_condition_for_question(survey, q),
                attrs={
                    **inherited_attrs,
                    "allowed_filetypes": "pdf, docx, zip",
                    "min_files": "1",
                    "max_files": "1",
                },
            ))
        group.questions = expanded


def evidence_condition_for_question(survey: Survey, q: Question) -> str:
    explicit = get_attr(q, "evidence_if", "").strip()
    if explicit:
        return explicit

    ltype = TYPE_MAP.get(q.type, q.type)
    answer_options = options_for_question(survey, q)
    if ltype == "L" and answer_options:
        return f"{q.code} in [{', '.join(opt.code for opt in answer_options)}]"
    if ltype == "M":
        options = q.subquestions or q.alternatives
        if options:
            return " or ".join(f"{q.code}.{opt.code} == Y" for opt in options)
    if ltype == "F" and q.subquestions and answer_options:
        parts = [
            f"{q.code}.{row.code} == {col.code}"
            for row in q.subquestions
            for col in answer_options
        ]
        if parts:
            return " or ".join(parts)
    return "1"


def options_for_question(survey: Survey, q: Question) -> List[Option]:
    if q.alternatives:
        return q.alternatives
    if q.scale and q.scale in survey.scales:
        return survey.scales[q.scale].options
    return []


# ----------------------------
# Validação
# ----------------------------


def validate_survey(survey: Survey) -> None:
    if not survey.groups:
        raise ValueError("Nenhum grupo encontrado. Use '## Grupo: codigo | título'.")
    qcodes: set[str] = set()
    for group in survey.groups:
        if not group.questions:
            raise ValueError(f"Grupo sem questões: {group.code}")
        for q in group.questions:
            if q.code in qcodes:
                raise ValueError(f"Código de questão duplicado: {q.code}")
            qcodes.add(q.code)

            ltype = TYPE_MAP.get(q.type, q.type)
            if q.scale and q.scale not in survey.scales:
                raise ValueError(f"Questão {q.code} referencia escala inexistente: {q.scale}")

            if ltype in {"L", "O"} and not q.scale and not q.alternatives:
                raise ValueError(f"Questão single/list {q.code} precisa de scale ou alternatives.")
            if ltype == "M" and not q.subquestions:
                if q.alternatives:
                    q.subquestions = q.alternatives
                    q.alternatives = []
                else:
                    raise ValueError(f"Questão multi {q.code} precisa de subquestions.")
            if ltype == "Q" and not q.subquestions:
                raise ValueError(f"Questão multi_text {q.code} precisa de subquestions.")
            if ltype in {"F", ":"}:
                if not q.subquestions:
                    raise ValueError(f"Questão array {q.code} precisa de rows/subquestions.")
                if not q.scale and not q.alternatives:
                    raise ValueError(f"Questão array {q.code} precisa de scale ou alternatives/columns.")


def fill_empty_groups_with_acknowledgement(survey: Survey) -> None:
    used_codes = {q.code for group in survey.groups for q in group.questions}
    for group in survey.groups:
        if group.questions:
            continue

        base_code = f"q{group.code}_ciencia"
        code = base_code
        suffix = 2
        while code in used_codes:
            code = f"{base_code}_{suffix}"
            suffix += 1
        used_codes.add(code)

        group.questions.append(Question(
            code=code,
            type="multi",
            text_lines=["Confirme para prosseguir para a próxima seção."],
            mandatory=True,
            subquestions=[Option("ciente", "Estou ciente das informações apresentadas.")],
        ))


def filter_survey_by_target(survey: Survey, target: str) -> Survey:
    return filter_target_survey(survey, target)


# ----------------------------
# Conversões auxiliares
# ----------------------------


def inline_md_to_html(text: str) -> str:
    """Converte o subconjunto inline usado pelo SurveyMD em HTML seguro."""

    value = html.escape(text, quote=True)
    value = re.sub(
        r"\[([^]\n]+)\]\((https?://[^)\s]+)\)",
        r'<a href="\2" rel="noreferrer noopener" target="_blank">\1</a>',
        value,
    )
    value = re.sub(r"`([^`\n]+)`", r"<code>\1</code>", value)
    value = re.sub(r"\*\*([^*\n]+)\*\*", r"<strong>\1</strong>", value)
    value = re.sub(r"__([^_\n]+)__", r"<strong>\1</strong>", value)
    value = re.sub(r"(?<!\*)\*([^*\n]+)\*(?!\*)", r"<em>\1</em>", value)
    return value


def md_to_html(text: str) -> str:
    """Converte parágrafos, listas e marcações inline do SurveyMD em HTML."""

    text = (text or "").strip()
    if not text:
        return ""
    if text.lstrip().startswith("<"):
        return text

    lines = text.splitlines()
    blocks: List[str] = []
    paragraph: List[str] = []
    index = 0

    def flush_paragraph() -> None:
        if paragraph:
            body = " ".join(item.strip() for item in paragraph if item.strip())
            if body:
                blocks.append(f"<p>{inline_md_to_html(body)}</p>")
            paragraph.clear()

    while index < len(lines):
        line = lines[index].strip()
        if not line:
            flush_paragraph()
            index += 1
            continue

        unordered = re.match(r"^[-+*]\s+(.+)$", line)
        ordered = re.match(r"^\d+[.)]\s+(.+)$", line)
        if unordered or ordered:
            flush_paragraph()
            tag = "ul" if unordered else "ol"
            items: List[str] = []
            while index < len(lines):
                candidate = lines[index].strip()
                match = (
                    re.match(r"^[-+*]\s+(.+)$", candidate)
                    if tag == "ul"
                    else re.match(r"^\d+[.)]\s+(.+)$", candidate)
                )
                if not match:
                    break
                items.append(f"<li>{inline_md_to_html(match.group(1).strip())}</li>")
                index += 1
            blocks.append(f"<{tag}>\n" + "\n".join(items) + f"\n</{tag}>")
            continue

        paragraph.append(line)
        index += 1

    flush_paragraph()
    return "\n".join(blocks)


def question_to_html(q: Question) -> str:
    body = md_to_html(q.text())
    explain = q.attrs.get("explain", "").strip()
    if explain:
        explain_html = html.escape(explain)
        body = (
            f"{body}"
            '<div class="question-help-container text-info col-12" style="margin:15px;">'
            '<div class="ls-questionhelp"><p><span style="font-size:12pt;">'
            '<span style="font-family:Arial, sans-serif;"><span style="color:#35363f;">'
            f"{explain_html}"
            "</span></span></span></p></div></div>"
        )
    if not q.subgroup:
        return body
    if body and body.lstrip().startswith("<") and not body.lstrip().lower().startswith("<p"):
        body = f"<p>{body}</p>"
    subgroup = html.escape(q.subgroup)
    return f'<p style="font-size:14pt;"><strong>{subgroup}</strong></p>{body}'


def cdata(value: object) -> str:
    s = "" if value is None else str(value)
    return "<![CDATA[" + s.replace("]]>", "]]]]><![CDATA[>") + "]]>"


def xml_table(name: str, fields: List[str], rows: List[Dict[str, object]]) -> str:
    out: List[str] = [f" <{name}>", "  <fields>"]
    for f in fields:
        out.append(f"   <fieldname>{html.escape(f)}</fieldname>")
    out.append("  </fields>")
    out.append("  <rows>")
    for row in rows:
        out.append("   <row>")
        for f in fields:
            out.append(f"    <{f}>{cdata(row.get(f, ''))}</{f}>")
        out.append("   </row>")
    out.append("  </rows>")
    out.append(f" </{name}>")
    return "\n".join(out)


def sgqa(sid: int, gid: int, qid: int, subcode: str = "") -> str:
    return f"{sid}X{gid}X{qid}{subcode}"


def split_csv_values(value_text: str) -> List[str]:
    return [v.strip().strip("'").strip('"') for v in value_text.split(",") if v.strip()]


def literal(value: str) -> str:
    return value.strip().strip("'").strip('"')


def normalize_ls_datetime(value: str) -> str:
    """Garante que a string de data/hora use o formato do LimeSurvey: YYYY-MM-DD HH:MM:SS.fff."""
    value = (value or "").strip()
    if not value:
        return value
    for fmt in [
        "%Y-%m-%d %H:%M:%S.%f",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d",
    ]:
        try:
            return dt.datetime.strptime(value, fmt).strftime("%Y-%m-%d %H:%M:%S.000")
        except ValueError:
            continue
    return value


# ----------------------------
# Parser de lógica condicional
# ----------------------------

@dataclass
class SimpleCondition:
    ref: str
    values: List[str]
    method: str = "=="
    subcode: str = ""


def parse_visible_if(expr: str, question_index: Dict[str, Question], sid: int) -> Tuple[str, List[SimpleCondition]]:
    """
    Converte expressões amigáveis para LimeSurvey ExpressionScript.

    Suportado:
      q1011 == sim
      q1022 != naoap
      q1022 in [adpar, admai]
      q1022 not in [naoad, adfor]
      q2112ext.B == Y
      q2112ext[B] == Y
      (q1 == sim and q2 in [A, B]) or q3.C == Y

    Em expressões com and/or, gera apenas relevance. Em expressões simples, também gera
    linhas na tabela conditions para manter compatibilidade com o padrão clássico exportado.
    """
    expr = (expr or "1").strip()
    if expr in {"", "1", "true", "True"}:
        return "1", []
    if expr.lower().startswith("raw:"):
        return expr.split(":", 1)[1].strip(), []

    simple = parse_simple_condition(expr)
    relevance = compile_relevance(expr, question_index, sid)
    conds: List[SimpleCondition] = []
    if simple is not None:
        ref, sub, method, values = simple
        conds.append(SimpleCondition(ref=ref, subcode=sub, method=method, values=values))
    return relevance, conds


def parse_simple_condition(expr: str) -> Optional[Tuple[str, str, str, List[str]]]:
    e = expr.strip()
    if re.search(r"\b(and|or)\b|&&|\|\|", e, flags=re.I):
        return None
    if e.startswith("(") or e.endswith(")"):
        return None

    refpat = r"([A-Za-z][A-Za-z0-9_]*)(?:\.([A-Za-z0-9_]+)|\[([A-Za-z0-9_]+)\])?"

    m = re.fullmatch(rf"{refpat}\s+not\s+in\s+\[([^\]]+)\]", e, flags=re.I)
    if m:
        return m.group(1), m.group(2) or m.group(3) or "", "!=", split_csv_values(m.group(4))

    m = re.fullmatch(rf"{refpat}\s+in\s+\[([^\]]+)\]", e, flags=re.I)
    if m:
        return m.group(1), m.group(2) or m.group(3) or "", "==", split_csv_values(m.group(4))

    m = re.fullmatch(rf"{refpat}\s*(==|!=)\s*([^\s]+)", e)
    if m:
        return m.group(1), m.group(2) or m.group(3) or "", m.group(4), [literal(m.group(5))]

    # Atalho: visible_if: qext.B -> checkbox marcada.
    m = re.fullmatch(rf"{refpat}", e)
    if m and (m.group(2) or m.group(3)):
        return m.group(1), m.group(2) or m.group(3) or "", "==", ["Y"]

    return None


def compile_relevance(expr: str, question_index: Dict[str, Question], sid: int) -> str:
    e = expr.strip()
    e = re.sub(r"\bAND\b", "and", e, flags=re.I)
    e = re.sub(r"\bOR\b", "or", e, flags=re.I)
    e = e.replace("&&", " and ").replace("||", " or ")

    def field_for(ref: str, sub: str = "") -> str:
        if ref not in question_index:
            raise ValueError(f"visible_if referencia questão inexistente: {ref}")
        q = question_index[ref]
        return sgqa(sid, int(q.gid), int(q.qid), sub)

    refpat = r"(?<![A-Za-z0-9_\.])([A-Za-z][A-Za-z0-9_]*)(?:\.([A-Za-z0-9_]+)|\[([A-Za-z0-9_]+)\])?"

    # not in precisa vir antes de in.
    def repl_not_in(m: re.Match[str]) -> str:
        ref = m.group(1)
        sub = m.group(2) or m.group(3) or ""
        values = split_csv_values(m.group(4))
        field = field_for(ref, sub)
        parts = [f'{field}.NAOK != "{v}"' for v in values]
        return "(" + " and ".join(parts) + ")"

    e = re.sub(rf"{refpat}\s+not\s+in\s+\[([^\]]+)\]", repl_not_in, e, flags=re.I)

    def repl_in(m: re.Match[str]) -> str:
        ref = m.group(1)
        sub = m.group(2) or m.group(3) or ""
        values = split_csv_values(m.group(4))
        field = field_for(ref, sub)
        parts = [f'{field}.NAOK == "{v}"' for v in values]
        return "(" + " or ".join(parts) + ")"

    e = re.sub(rf"{refpat}\s+in\s+\[([^\]]+)\]", repl_in, e, flags=re.I)

    def repl_cmp(m: re.Match[str]) -> str:
        ref = m.group(1)
        sub = m.group(2) or m.group(3) or ""
        op = m.group(4)
        val = literal(m.group(5))
        return f'{field_for(ref, sub)}.NAOK {op} "{val}"'

    e = re.sub(rf"{refpat}\s*(==|!=)\s*([^\s\)]+)", repl_cmp, e)

    # Atalho restante: qmulti.A -> qmulti.A == Y. Evita substituir campos já compilados.
    def repl_bare_checkbox(m: re.Match[str]) -> str:
        ref = m.group(1)
        sub = m.group(2) or m.group(3) or ""
        token = m.group(0)
        if ref == "NAOK" or not sub or ref not in question_index:
            return token
        return f'{field_for(ref, sub)}.NAOK == "Y"'

    e = re.sub(refpat, repl_bare_checkbox, e)
    return f"(({e}))"


# ----------------------------
# Construção do .lss
# ----------------------------


def allocate_ids(survey: Survey, sid: int, first_gid: int, first_qid: int) -> Dict[str, Question]:
    qid = first_qid
    q_index: Dict[str, Question] = {}
    for gi, group in enumerate(survey.groups):
        group.gid = first_gid + gi
        for q in group.questions:
            q.qid = qid
            q.gid = group.gid
            q_index[q.code] = q
            qid += 1
    return q_index


def build_lss(survey: Survey, sid: int, first_gid: int = 1000, first_qid: int = 10000) -> str:
    lang = survey.meta.get("language", survey.meta.get("lang", "pt-BR"))
    title = survey.meta.get("title", "Questionário importado")
    admin = survey.meta.get("admin", "Administrator")
    adminemail = survey.meta.get("adminemail", survey.meta.get("admin_email", "admin@example.com"))
    template = survey.meta.get("template", "vanilla")
    survey_format = survey.meta.get("format", "G")

    q_index = allocate_ids(survey, sid, first_gid, first_qid)

    group_rows: List[Dict[str, object]] = []
    question_rows: List[Dict[str, object]] = []
    subquestion_rows: List[Dict[str, object]] = []
    answer_rows: List[Dict[str, object]] = []
    attribute_rows: List[Dict[str, object]] = []
    condition_rows: List[Dict[str, object]] = []

    next_subqid = first_qid + sum(len(g.questions) for g in survey.groups)
    cid = 1

    for gi, group in enumerate(survey.groups):
        group_rows.append({
            "gid": group.gid,
            "sid": sid,
            "group_name": group.title,
            "group_order": gi,
            "description": md_to_html("\n".join(group.description_lines)),
            "language": lang,
            "randomization_group": "",
            "grelevance": "1",
        })

        for qi, q in enumerate(group.questions):
            ltype = TYPE_MAP.get(q.type, q.type)
            relevance, cond_specs = parse_visible_if(q.visible_if, q_index, sid)

            question_rows.append({
                "qid": q.qid,
                "parent_qid": 0,
                "sid": sid,
                "gid": group.gid,
                "type": ltype,
                "title": q.code,
                "question": question_to_html(q),
                "preg": "",
                "help": md_to_html(q.help),
                "other": "Y" if q.other else "N",
                "mandatory": "Y" if q.mandatory else "N",
                "question_order": qi,
                "language": lang,
                "scale_id": 0,
                "same_default": 0,
                "relevance": relevance,
                "modulename": "",
            })

            for cond in cond_specs:
                refq = q_index[cond.ref]
                cfield = sgqa(sid, int(refq.gid), int(refq.qid), cond.subcode)
                for value in cond.values:
                    condition_rows.append({
                        "cid": cid,
                        "qid": q.qid,
                        "cqid": refq.qid,
                        "cfieldname": cfield,
                        "method": cond.method,
                        "value": value,
                        "scenario": 1,
                    })
                    cid += 1

            ans_options: List[Option] = []
            if q.scale:
                ans_options = survey.scales[q.scale].options
            elif q.alternatives:
                ans_options = q.alternatives

            if ltype in {"L", "O", "F"}:
                for idx, opt in enumerate(ans_options, 1):
                    answer_rows.append({
                        "qid": q.qid,
                        "code": opt.code,
                        "answer": md_to_html(opt.text),
                        "sortorder": idx,
                        "assessment_value": 0,
                        "language": lang,
                        "scale_id": 0,
                    })

            if ltype == ":":
                for idx, opt in enumerate(q.subquestions, 1):
                    subquestion_rows.append({
                        "qid": next_subqid,
                        "parent_qid": q.qid,
                        "sid": sid,
                        "gid": group.gid,
                        "type": "T",
                        "title": opt.code,
                        "question": md_to_html(opt.text),
                        "preg": "",
                        "help": "",
                        "other": "N",
                        "mandatory": "N",
                        "question_order": idx,
                        "language": lang,
                        "scale_id": 0,
                        "same_default": 0,
                        "relevance": "1",
                        "modulename": "",
                    })
                    next_subqid += 1
                for idx, opt in enumerate(ans_options, 1):
                    subquestion_rows.append({
                        "qid": next_subqid,
                        "parent_qid": q.qid,
                        "sid": sid,
                        "gid": group.gid,
                        "type": "T",
                        "title": opt.code,
                        "question": md_to_html(opt.text),
                        "preg": "",
                        "help": "",
                        "other": "N",
                        "mandatory": "N",
                        "question_order": idx,
                        "language": lang,
                        "scale_id": 1,
                        "same_default": 0,
                        "relevance": "1",
                        "modulename": "",
                    })
                    next_subqid += 1
            elif ltype in {"M", "Q", "F"}:
                sub_type = "T"
                if ltype == "M" and not ("min_answers" in q.attrs or "max_answers" in q.attrs):
                    sub_type = "M"
                for idx, opt in enumerate(q.subquestions, 1):
                    subquestion_rows.append({
                        "qid": next_subqid,
                        "parent_qid": q.qid,
                        "sid": sid,
                        "gid": group.gid,
                        "type": sub_type,
                        "title": opt.code,
                        "question": md_to_html(opt.text),
                        "preg": "",
                        "help": "",
                        "other": "N",
                        "mandatory": "N",
                        "question_order": idx,
                        "language": lang,
                        "scale_id": 0,
                        "same_default": 0,
                        "relevance": "1",
                        "modulename": "",
                    })
                    next_subqid += 1

            add_attributes(q, ltype, attribute_rows)

    survey_row = build_survey_row(sid, lang, title, admin, adminemail, template, survey_format, survey.meta)
    lang_row = build_lang_row(sid, lang, title, survey)

    parts = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        "<document>",
        " <LimeSurveyDocType>Survey</LimeSurveyDocType>",
        " <DBVersion>363</DBVersion>",
        " <languages>",
        f"  <language>{html.escape(lang)}</language>",
        " </languages>",
        xml_table("answers", ANSWER_FIELDS, answer_rows),
        xml_table("conditions", CONDITION_FIELDS, condition_rows),
        xml_table("groups", GROUP_FIELDS, group_rows),
        xml_table("questions", QUESTION_FIELDS, question_rows),
        xml_table("subquestions", QUESTION_FIELDS, subquestion_rows),
        xml_table("question_attributes", ATTRIBUTE_FIELDS, attribute_rows),
        xml_table("surveys", SURVEY_FIELDS, [survey_row]),
        xml_table("surveys_languagesettings", LANG_FIELDS, [lang_row]),
        " <themes>",
        "  <fields>",
        "  </fields>",
        "  <rows>",
        "  </rows>",
        " </themes>",
        " <themes_inherited>",
        "  <fields>",
        "  </fields>",
        "  <rows>",
        "  </rows>",
        " </themes_inherited>",
        "</document>",
        "",
    ]
    return "\n".join(parts)


def add_attributes(q: Question, ltype: str, attribute_rows: List[Dict[str, object]]) -> None:
    def attr(name: str, value: str, language: str = "") -> None:
        attribute_rows.append({"qid": q.qid, "attribute": name, "value": value, "language": language})

    if ltype == "M" and q.attrs.get("hide_tip", "1").lower() not in {"0", "false", "não", "nao"}:
        attr("hide_tip", "1")
    if ltype == "M" and "exclude_all_others" in q.attrs:
        attr("exclude_all_others", q.attrs["exclude_all_others"])
    if ltype == ":":
        attr("input_boxes", q.attrs.get("input_boxes", "1"))
        attr("multiflexible_min", q.attrs.get("multiflexible_min", "0"))
        attr("multiflexible_max", q.attrs.get("multiflexible_max", "1000"))
        attr("multiflexible_step", q.attrs.get("multiflexible_step", "-1"))
    if ltype == "|":
        if "allowed_filetypes" in q.attrs:
            attr("allowed_filetypes", q.attrs["allowed_filetypes"])
        if "min_files" in q.attrs:
            attr("min_num_of_files", q.attrs["min_files"])
        if "max_files" in q.attrs:
            attr("max_num_of_files", q.attrs["max_files"])
    if "min_answers" in q.attrs:
        attr("min_answers", q.attrs["min_answers"])
    if "max_answers" in q.attrs:
        attr("max_answers", q.attrs["max_answers"])


def build_survey_row(sid: int, lang: str, title: str, admin: str, adminemail: str, template: str, survey_format: str, meta: Dict[str, str]) -> Dict[str, object]:
    row = {f: "" for f in SURVEY_FIELDS}
    row.update({
        "sid": sid,
        "gsid": 1,
        "admin": admin,
        "expires": normalize_ls_datetime(meta.get("expires", "")),
        "startdate": normalize_ls_datetime(meta.get("startdate", meta.get("start_date", ""))),
        "adminemail": adminemail,
        "anonymized": "N",
        "format": survey_format,
        "savetimings": "N",
        "template": template,
        "language": lang,
        "datestamp": "Y",
        "usecookie": "N",
        "allowregister": "N",
        "allowsave": "Y",
        "autonumber_start": "0",
        "autoredirect": "N",
        "allowprev": "Y",
        "printanswers": "Y",
        "ipaddr": "N",
        "refurl": "N",
        "showsurveypolicynotice": "0",
        "publicstatistics": "N",
        "publicgraphs": "N",
        "listpublic": "N",
        "htmlemail": "Y",
        "sendconfirmation": "N",
        "tokenanswerspersistence": "N",
        "assessments": "N",
        "usecaptcha": "N",
        "usetokens": "N",
        "bounce_email": adminemail,
        "tokenlength": "15",
        "showxquestions": "N",
        "showgroupinfo": "B",
        "shownoanswer": "N",
        "showqnumcode": "X",
        "bounceprocessing": "G",
        "showwelcome": "Y",
        "showprogress": "Y",
        "questionindex": "0",
        "navigationdelay": "0",
        "nokeyboard": "N",
        "alloweditaftercompletion": "N",
    })
    validate_survey_row_lengths(row)
    return row


def validate_survey_row_lengths(row: Dict[str, object]) -> None:
    for field, max_len in SURVEY_FIELD_MAX_LENGTHS.items():
        value = "" if row.get(field) is None else str(row.get(field))
        if len(value) > max_len:
            raise ValueError(
                f"Campo LimeSurvey '{field}' tem {len(value)} caracteres, "
                f"mas o limite e {max_len}. Use um valor mais curto no cabecalho do .md."
            )


def build_lang_row(sid: int, lang: str, title: str, survey: Survey) -> Dict[str, object]:
    row = {f: "" for f in LANG_FIELDS}
    row.update({
        "surveyls_survey_id": sid,
        "surveyls_language": lang,
        "surveyls_title": title,
        "surveyls_description": md_to_html(survey.meta.get("description", "")),
        "surveyls_welcometext": md_to_html(survey.meta.get("welcome", "")),
        "surveyls_endtext": md_to_html(survey.meta.get("endtext", "")),
        "surveyls_email_invite_subj": survey.meta.get("invite_subject", f"Convite para responder: {title}"),
        "surveyls_email_invite": survey.meta.get("invite_email", "Prezado(a),<br /><br />Solicitamos o preenchimento do questionário {SURVEYNAME}."),
        "surveyls_email_remind_subj": survey.meta.get("remind_subject", f"Lembrete: {title}"),
        "surveyls_email_remind": survey.meta.get("remind_email", "Prezado(a),<br /><br />Este é um lembrete para preenchimento do questionário {SURVEYNAME}."),
        "surveyls_email_register_subj": "Confirmação de inscrição",
        "surveyls_email_register": "Confirmação de inscrição na pesquisa {SURVEYNAME}.",
        "surveyls_email_confirm_subj": survey.meta.get("confirm_subject", f"Confirmação de resposta: {title}"),
        "surveyls_email_confirm": survey.meta.get("confirm_email", "Confirmamos o recebimento da resposta ao questionário {SURVEYNAME}."),
        "surveyls_dateformat": "1",
        "email_admin_notification_subj": "Nova resposta para {SURVEYNAME}",
        "email_admin_notification": "Uma nova resposta foi submetida para {SURVEYNAME}.",
        "email_admin_responses_subj": "Nova resposta para {SURVEYNAME}",
        "email_admin_responses": "Uma nova resposta foi submetida para {SURVEYNAME}.",
        "surveyls_numberformat": "0",
    })
    return row


# ----------------------------
# CLI
# ----------------------------


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Converte Markdown SurveyMD para LimeSurvey .lss")
    parser.add_argument("input_md", type=Path, help="Arquivo Markdown de entrada")
    parser.add_argument("output_lss", type=Path, help="Arquivo .lss de saída")
    parser.add_argument("--sid", type=int, default=None, help="Survey ID numérico. Se omitido, usa metadata sid ou 900001.")
    parser.add_argument("--first-gid", type=int, default=1000, help="Primeiro GID gerado")
    parser.add_argument("--first-qid", type=int, default=10000, help="Primeiro QID gerado")
    args = parser.parse_args(argv)

    try:
        survey = parse_markdown(args.input_md)
        targets = survey_targets(survey)
        sid_base = args.sid or int(survey.meta.get("sid", "900001"))
        if targets:
            multi = len(targets) > 1
            for index, target in enumerate(targets):
                target_survey = filter_survey_by_target(survey, target)
                output_path = target_output_path(args.output_lss, target) if multi else args.output_lss
                xml = build_lss(target_survey, sid=sid_base + index, first_gid=args.first_gid, first_qid=args.first_qid)
                output_path.write_text(xml, encoding="utf-8")
                print(f"OK: arquivo gerado em {output_path}")
            return 0
        xml = build_lss(survey, sid=sid_base, first_gid=args.first_gid, first_qid=args.first_qid)
        args.output_lss.write_text(xml, encoding="utf-8")
    except Exception as exc:
        print(f"ERRO: {exc}", file=sys.stderr)
        return 1

    print(f"OK: arquivo gerado em {args.output_lss}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
