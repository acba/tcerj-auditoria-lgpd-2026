from __future__ import annotations

import copy
import re
from pathlib import Path
from typing import Dict, Iterable, List, Tuple


TARGET_NAME_RE = re.compile(r"^[a-z0-9_-]+$")


def split_frontmatter(text: str) -> Tuple[Dict[str, str], List[str]]:
    lines = text.splitlines()
    meta: Dict[str, str] = {}
    if not lines or lines[0].strip() != "---":
        return meta, lines

    end = None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            end = i
            break
    if end is None:
        raise ValueError("Front matter iniciado com --- mas não encerrado.")

    raw_lines = lines[1:end]
    i = 0
    while i < len(raw_lines):
        raw = raw_lines[i]
        line = raw.strip()
        if not line or line.startswith("#"):
            i += 1
            continue
        if ":" not in line:
            raise ValueError(f"Linha inválida no front matter: {raw}")
        key, value = line.split(":", 1)
        key = key.strip().lower()
        value = value.strip()

        if value in {"|", ">"}:
            block: List[str] = []
            i += 1
            while i < len(raw_lines):
                candidate = raw_lines[i]
                if candidate.strip() and not candidate.startswith((" ", "\t")):
                    break
                block.append(candidate[2:] if candidate.startswith("  ") else candidate.lstrip())
                i += 1
            text_value = "\n".join(block).strip()
            meta[key] = " ".join(text_value.splitlines()) if value == ">" else text_value
            continue

        meta[key] = value.strip('"').strip("'")
        i += 1

    return meta, lines[end + 1 :]


def parse_targets(value: str, *, label: str = "target") -> List[str]:
    targets = [item.strip().lower() for item in str(value or "").split(",") if item.strip()]
    if not targets:
        raise ValueError(f"{label} deve informar ao menos um target.")
    invalid = [target for target in targets if not TARGET_NAME_RE.fullmatch(target)]
    if invalid:
        raise ValueError(f"{label} inválido: {', '.join(invalid)}")
    duplicates = sorted({target for target in targets if targets.count(target) > 1})
    if duplicates:
        raise ValueError(f"{label} duplicado: {', '.join(duplicates)}")
    return targets


def survey_targets(survey) -> List[str]:
    raw = survey.meta.get("target", "")
    return parse_targets(raw, label="target do cabeçalho") if raw else []


def question_targets(question) -> List[str]:
    raw = question.attrs.get("target", "")
    return parse_targets(raw, label=f"target da questão {question.code}") if raw else []


def iter_questions(survey) -> Iterable:
    for group in survey.groups:
        for question in group.questions:
            yield question


def validate_target_config(survey) -> List[str]:
    targets = survey_targets(survey)
    allowed = set(targets)
    for question in iter_questions(survey):
        q_targets = question_targets(question)
        if q_targets and not targets:
            raise ValueError(f"Questão {question.code} declara target, mas o cabeçalho não define target.")
        unknown = [target for target in q_targets if target not in allowed]
        if unknown:
            raise ValueError(f"Questão {question.code} declara target não listado no cabeçalho: {', '.join(unknown)}")
    return targets


def filter_survey_by_target(survey, target: str):
    targets = validate_target_config(survey)
    normalized = target.strip().lower()
    if normalized not in targets:
        raise ValueError(f"Target não listado no cabeçalho: {target}")

    filtered = copy.deepcopy(survey)
    filtered.meta["target"] = normalized
    filtered.groups = []

    for group in survey.groups:
        new_group = copy.deepcopy(group)
        new_group.questions = [
            copy.deepcopy(question)
            for question in group.questions
            if not question_targets(question) or normalized in question_targets(question)
        ]
        if new_group.questions:
            filtered.groups.append(new_group)

    validate_visible_dependencies(filtered)
    return filtered


def visible_refs(expr: str) -> List[str]:
    value = (expr or "").strip()
    if not value or value == "1" or value.lower() == "true" or value.lower().startswith("raw:"):
        return []
    refpat = r"([A-Za-z][A-Za-z0-9_]*)(?:\.[A-Za-z0-9_]+|\[[A-Za-z0-9_]+\])?"
    refs: List[str] = []
    for pattern in [
        rf"{refpat}\s+not\s+in\s+\[",
        rf"{refpat}\s+in\s+\[",
        rf"{refpat}\s*(?:==|!=)",
        r"(?<![A-Za-z0-9_\.])([A-Za-z][A-Za-z0-9_]*)(?:\.[A-Za-z0-9_]+|\[[A-Za-z0-9_]+\])",
    ]:
        for match in re.finditer(pattern, value, flags=re.IGNORECASE):
            ref = match.group(1)
            if ref not in refs and ref.lower() not in {"and", "or", "not", "true", "false"}:
                refs.append(ref)
    return refs


def validate_visible_dependencies(survey) -> None:
    codes = {question.code for question in iter_questions(survey)}
    for question in iter_questions(survey):
        for ref in visible_refs(getattr(question, "visible_if", "")):
            if ref.endswith("ext") and ref[:-3] in codes:
                continue
            if ref not in codes:
                raise ValueError(f"Questão {question.code} referencia questão ausente neste target: {ref}")


def target_output_path(path: Path, target: str) -> Path:
    return path.with_name(f"{path.stem}_{target}{path.suffix}")
