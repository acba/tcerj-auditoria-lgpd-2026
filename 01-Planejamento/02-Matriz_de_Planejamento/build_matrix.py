# -*- coding: utf-8 -*-
"""
Script de geração e validação da Matriz de Planejamento da Auditoria LGPD 2026.2
Fiscalização TCE-RJ nº 22/2026 (Processo PAAG nº 303.389-0/25)
Monitoramento do Processo TCE-RJ nº 217.899-0/2024 (Acórdão nº 3931/2025)

Alinhamento estrito ao instrumento de coleta de dados (LimeSurvey 832871)
e suas extensões de monitoramento e percepção pedagógica.
"""

import sys
import copy
import xml.etree.ElementTree as ET
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED

# Importar o motor oficial de geração de matrizes
sys.path.append(r"C:\Users\augustocba\Documents\workspace\tcerj-igovti-2026\scripts")
import gerar_matriz_planejamento as gmp

WORKSPACE_DIR = Path(r"F:\CAD-TI\AUDITORIAS\2026.2-Auditoria LGPD\01-Planejamento\02-Matriz_de_Planejamento")
MD_PATH = WORKSPACE_DIR / "matriz_planejamento.md"
DOCX_PATH = WORKSPACE_DIR / "matriz_planejamento.docx"
TEMPLATE_PATH = r"C:\Users\augustocba\Documents\workspace\tcerj-igovti-2026\01-Planejamento\03-Estrategia_e_Plano\04-Matriz_Planejamento\matriz_planejamento.docx"

def update_header_xml_lgpd(header_xml: bytes) -> bytes:
    root = ET.fromstring(header_xml)
    W = f"{{{gmp.W_NS}}}"
    replacements = {
        "JURISDICIONADOS": "91 prefeituras municipais jurisdicionadas do Estado do Rio de Janeiro",
        "OBJETIVO DA AUDITORIA": "Verificar o grau de conformidade das 91 prefeituras municipais jurisdicionadas com os requisitos selecionados da LGPD, o cumprimento das decisões do Proc. TCE-RJ nº 217.899-0/2024 e propor encaminhamentos pertinentes.",
    }
    found = set()
    for paragraph in root.iter(f"{W}p"):
        current_text = gmp.text_of(paragraph).strip()
        for label, value in replacements.items():
            if current_text.startswith(f"{label}:"):
                gmp.set_labeled_paragraph_text(paragraph, label, value)
                found.add(label)
                break
    print(f"[HEADER] Campos atualizados no cabeçalho: {sorted(found)}")
    return ET.tostring(root, encoding="utf-8", xml_declaration=True)

def format_findings_or_analysis_clean(
    question: gmp.Question, mapping: dict[str, str] | None = None
) -> list[str | gmp.CellParagraph]:
    """
    Formata a coluna 'POSSÍVEIS ACHADOS' estritamente com os achados estruturantes
    e situações encontradas (hipóteses de auditoria), omitindo campos de deliberação/encaminhamento
    (Tipo, Fundamentação e Encaminhamento) que pertencem à Matriz de Achados / Relatório.
    """
    display_mapping = mapping or {}
    lines: list[str | gmp.CellParagraph] = []
    for finding in question.achados:
        if finding.title:
            lines.append(
                gmp.CellParagraph(
                    f"{finding.title.rstrip('.')}.",
                    bold=True,
                    left_indent=0,
                    spacing_after=80,
                )
            )
        for situation in finding.situacoes:
            references = [
                gmp.display_identifier(identifier, display_mapping)
                for identifier in dict.fromkeys(situation.referencias + situation.criterios)
            ]
            description = f"{situation.descricao.rstrip('.')}."
            if references:
                description += f" [{', '.join(references)}];"
            lines.append(
                gmp.CellParagraph(
                    f"• {description}",
                    left_indent=240,
                    spacing_after=60,
                )
            )

    if lines:
        return lines

    if not question.gera_achado or question.natureza:
        lines.append("Não se aplica: questão de levantamento, sem geração de achado individual.")
        if question.analise_permite_dizer:
            lines.append("O que a análise permite dizer:")
            lines.extend(gmp.format_items(question.analise_permite_dizer, display_mapping))
        if question.limitacoes:
            lines.append("Limitações e cautelas:")
            lines.extend(gmp.format_items(question.limitacoes, display_mapping))
        return lines

    return [gmp.MISSING_MARKDOWN_PLACEHOLDER]

def generate_docx_lgpd(template_path: Path, markdown_path: Path, output_path: Path) -> None:
    gmp.format_findings_or_analysis = format_findings_or_analysis_clean
    W = f"{{{gmp.W_NS}}}"
    matrix = gmp.parse_matrix(markdown_path.read_text(encoding="utf-8"))
    if not matrix.questions:
        raise ValueError("Nenhuma questão foi encontrada no Markdown.")

    with ZipFile(template_path, "r") as zin:
        archive = [(copy.copy(item), zin.read(item.filename)) for item in zin.infolist()]

    files = {item.filename: data for item, data in archive}
    root = ET.fromstring(files["word/document.xml"])
    body = root.find(f"{W}body")
    if body is None:
        raise ValueError("Template DOCX sem word/body.")
    intro, table_template, signature_parts, sect_pr = gmp.find_template_parts(body)

    for child in list(body):
        body.remove(child)

    for element in gmp.replace_intro_text(intro, matrix):
        body.append(element)

    blank_paragraph = ET.Element(f"{W}p")
    for question in matrix.questions:
        summary_table, details_table = gmp.build_question_tables(table_template, question)
        body.append(gmp.page_break_paragraph())
        body.append(summary_table)
        body.append(details_table)

    for part in signature_parts:
        body.append(copy.deepcopy(blank_paragraph))
        body.append(copy.deepcopy(part))

    body.append(copy.deepcopy(sect_pr))
    files["word/document.xml"] = ET.tostring(root, encoding="utf-8", xml_declaration=True)
    if "word/header1.xml" not in files:
        raise ValueError("Template DOCX sem word/header1.xml.")
    files["word/header1.xml"] = update_header_xml_lgpd(files["word/header1.xml"])

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(output_path, "w", ZIP_DEFLATED) as zout:
        for item, _ in archive:
            zout.writestr(item, files[item.filename])

def main():
    print("==================================================================")
    print("GERAÇÃO DA MATRIZ DE PLANEJAMENTO LGPD 2026.2 (CRITÉRIOS ESPECÍFICOS)")
    print("==================================================================")
    
    if not MD_PATH.exists():
        raise FileNotFoundError(f"Arquivo Markdown não encontrado: {MD_PATH}")
    
    md_content = MD_PATH.read_text(encoding="utf-8")
    print(f"[OK] Markdown lido de: {MD_PATH}")
    
    print("[INFO] Validando sintaxe da matriz através do parser oficial...")
    matrix = gmp.parse_matrix(md_content)
    print(f"[OK] Matriz parseada com sucesso: {len(matrix.questions)} questões identificadas.")
    for q in matrix.questions:
        print(f"  - {q.id}: {q.title} (critérios: {len(q.criterios)}, achados: {len(q.achados)}, subquestões: {len(q.subquestoes)}, procedimentos: {len(q.procedimentos)})")

    print("[INFO] Gerando documento DOCX formatado...")
    try:
        generate_docx_lgpd(Path(TEMPLATE_PATH), Path(MD_PATH), Path(DOCX_PATH))
        print(f"[OK] DOCX gerado com sucesso em: {DOCX_PATH}")
    except PermissionError:
        revised_path = WORKSPACE_DIR / "AN02 – Matriz de planejamento_revisada.docx"
        print(f"[AVISO] O arquivo principal '{DOCX_PATH.name}' está aberto no Word.")
        print(f"[INFO] Salvando versão atualizada em: {revised_path.name}")
        generate_docx_lgpd(Path(TEMPLATE_PATH), Path(MD_PATH), revised_path)
        print(f"[OK] DOCX revisado gerado com sucesso em: {revised_path}")
    print("==================================================================")

if __name__ == "__main__":
    main()
