# -*- coding: utf-8 -*-
"""
Script para geração dos Papéis de Trabalho de Planejamento da Auditoria LGPD 2026.2 (Fiscalização nº 22/2026):
1. Termos de auditoria.svg - Painel visual Canvas com cabeçalho institucional oficial e 12 dimensões consolidadas.
2. Termos de auditoria.png - Renderização de alta resolução do Canvas em imagem rasterizada.
3. Ata de Reunião.docx - Documento formal de formalização colegiada da participação da equipe de auditoria.
"""

import os
import sys
import subprocess
import xml.etree.ElementTree as ET
import docx
from docx.shared import Inches, Pt, RGBColor, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn

WORK_DIR = r"F:\CAD-TI\AUDITORIAS\2026.2-Auditoria LGPD\01-Planejamento\01-Termos_de_Auditoria"
SVG_PATH = os.path.join(WORK_DIR, "Termos de auditoria.svg")
PNG_PATH = os.path.join(WORK_DIR, "Termos de auditoria.png")
DOCX_PATH = os.path.join(WORK_DIR, "Ata de Reunião.docx")
LOGO_SVG = os.path.join(WORK_DIR, "tcerj_logo.svg")
LOGO_PNG = os.path.join(WORK_DIR, "tcerj_logo.png")

# -------------------------------------------------------------------------
# 1. GERAÇÃO DO SVG DO CANVAS (TERMOS DE AUDITORIA)
# -------------------------------------------------------------------------
def get_tcerj_logo_paths():
    if not os.path.exists(LOGO_SVG):
        return ""
    try:
        tree = ET.parse(LOGO_SVG)
        root = tree.getroot()
        paths = []
        for elem in root:
            tag = elem.tag.split("}")[-1]
            if tag == "path":
                d = elem.attrib.get("d", "")
                fill = elem.attrib.get("fill", "#0D2548")
                paths.append(f'<path d="{d}" fill="{fill}"/>')
        return "\n".join(paths)
    except Exception as e:
        print(f"Erro lendo SVG do logo: {e}")
        return ""

def escape_xml(s):
    if not s:
        return ""
    return (s.replace("&", "&amp;")
             .replace("<", "&lt;")
             .replace(">", "&gt;")
             .replace('"', "&quot;")
             .replace("'", "&apos;"))

def wrap_text(text, max_chars=85):
    words = text.split()
    lines = []
    curr = []
    curr_len = 0
    for w in words:
        if curr_len + len(w) + 1 <= max_chars:
            curr.append(w)
            curr_len += len(w) + 1
        else:
            if curr:
                lines.append(" ".join(curr))
            curr = [w]
            curr_len = len(w)
    if curr:
        lines.append(" ".join(curr))
    return lines

def build_svg():
    logo_inner = get_tcerj_logo_paths()
    
    # Dimensões totais do Canvas
    W = 3200
    H = 3320
    
    # Layout de 3 colunas
    # Col 1: x = 60, w = 990
    # Col 2: x = 1105, w = 990
    # Col 3: x = 2150, w = 990
    
    svg_parts = []
    svg_parts.append(f'''<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" 
width="{W}" height="{H}" viewBox="0 0 {W} {H}">
<defs>
    <filter id="card-shadow" x="-3%" y="-2%" width="106%" height="106%" filterUnits="userSpaceOnUse">
        <feDropShadow dx="0" dy="4" stdDeviation="8" flood-color="#0f172a" flood-opacity="0.06"/>
    </filter>
    <filter id="badge-shadow" x="-5%" y="-5%" width="110%" height="110%">
        <feDropShadow dx="0" dy="1" stdDeviation="2" flood-color="#000" flood-opacity="0.08"/>
    </filter>
</defs>

<style>
    .font-sans {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; }}
</style>

<!-- Fundo Geral -->
<rect width="{W}" height="{H}" fill="#f8fafc"/>
''')

    # =========================================================================
    # CABEÇALHO INSTITUCIONAL (PADRÃO MATRIZ DE PLANEJAMENTO TCE-RJ)
    # =========================================================================
    head_x = 60
    head_y = 45
    head_w = 3080
    head_h = 210
    
    svg_parts.append(f'''
<!-- CABEÇALHO INSTITUCIONAL -->
<g class="font-sans">
    <rect x="{head_x}" y="{head_y}" width="{head_w}" height="{head_h}" rx="16" ry="16" fill="#ffffff" stroke="#e2e8f0" stroke-width="1.5" filter="url(#card-shadow)"/>
    
    <!-- Brasão / Logotipo TCE-RJ -->
    <g transform="translate({head_x + 35}, {head_y + 30}) scale(2.0, 2.0)">
        {logo_inner}
    </g>
    
    <!-- Linha Divisória 1 -->
    <line x1="{head_x + 440}" y1="{head_y + 25}" x2="{head_x + 440}" y2="{head_y + head_h - 25}" stroke="#cbd5e1" stroke-width="1.5"/>
    
    <!-- Coluna 2: Hierarquia Institucional -->
    <g transform="translate({head_x + 475}, {head_y})">
        <text x="0" y="52" font-size="18" font-weight="800" fill="#0f172a" letter-spacing="0.5">TRIBUNAL DE CONTAS DO ESTADO DO RIO DE JANEIRO</text>
        <text x="0" y="84" font-size="16" font-weight="700" fill="#334155" letter-spacing="0.3">SECRETARIA-GERAL DE CONTROLE EXTERNO</text>
        <text x="0" y="114" font-size="15" font-weight="600" fill="#475569">SUBSECRETARIA DE CONTROLE DE POLÍTICAS DE CIDADANIA</text>
        <text x="0" y="144" font-size="15" font-weight="700" fill="#0284c7">COORDENADORIA DE AUDITORIA DE POLÍTICAS EM TECNOLOGIA DA INFORMAÇÃO – CAD-TI</text>
        <text x="0" y="174" font-size="13" font-weight="500" fill="#64748b">Papel de Trabalho: PT-PLA-01 | Auditoria de Conformidade em Proteção de Dados Pessoais</text>
    </g>
    
    <!-- Linha Divisória 2 -->
    <line x1="{head_x + 1520}" y1="{head_y + 25}" x2="{head_x + 1520}" y2="{head_y + head_h - 25}" stroke="#cbd5e1" stroke-width="1.5"/>
    
    <!-- Coluna 3: Identificação da Fiscalização -->
    <g transform="translate({head_x + 1555}, {head_y})">
        <text x="0" y="48" font-size="20" font-weight="800" fill="#0f172a">TERMOS DE AUDITORIA (CANVAS ESTRATÉGICO)</text>
        <text x="0" y="80" font-size="15" font-weight="700" fill="#334155">FISCALIZAÇÃO: <tspan font-weight="800" fill="#0369a1">22/2026</tspan> <tspan font-weight="400" fill="#64748b">| Processo PAAG: TCE-RJ nº 303.389-0/25</tspan></text>
        <text x="0" y="110" font-size="14" font-weight="700" fill="#334155">JURISDICIONADOS: <tspan font-weight="500" fill="#475569">91 Prefeituras Municipais do Estado do Rio de Janeiro</tspan></text>
        <text x="0" y="140" font-size="14" font-weight="700" fill="#334155">OBJETIVO SÍNTESE: <tspan font-weight="500" fill="#475569">Verificar conformidade com a LGPD e cumprimento das decisões do Proc. TCE-RJ nº 217.899-0/2024</tspan></text>
        <text x="0" y="170" font-size="13" font-weight="600" fill="#059669">NÍVEL DE ASSEGURAÇÃO: <tspan font-weight="500" fill="#334155">Limitada</tspan> <tspan font-weight="400" fill="#64748b">| Ciclo: 2026.2 | Data Base: 02/09/2026</tspan></text>
    </g>
</g>
''')

    # Helper para desenhar os Cards
    def draw_card_base(cid, x, y, w, h, accent_color, icon_svg, title_text):
        res = []
        res.append(f'''
<!-- CARD: {title_text} -->
<g class="font-sans" id="card-{cid}">
    <defs>
        <clipPath id="clip-{cid}">
            <rect x="{x}" y="{y}" width="{w}" height="{h}" rx="18" ry="18"/>
        </clipPath>
    </defs>
    <!-- Corpo do Card com Sombra -->
    <rect x="{x}" y="{y}" width="{w}" height="{h}" rx="18" ry="18" fill="#ffffff" stroke="#e2e8f0" stroke-width="1.5" filter="url(#card-shadow)"/>
    <!-- Faixa Lateral de Destaque -->
    <g clip-path="url(#clip-{cid})">
        <rect x="{x}" y="{y}" width="8" height="{h}" fill="{accent_color}"/>
    </g>
    <!-- Ícone -->
    <g transform="translate({x + 32}, {y + 30})">
        {icon_svg}
    </g>
    <!-- Título do Card -->
    <text x="{x + 78}" y="{y + 52}" font-size="22" font-weight="800" fill="#0f172a">{title_text}</text>
    <line x1="{x + 32}" y1="{y + 72}" x2="{x + w - 32}" y2="{y + 72}" stroke="#f1f5f9" stroke-width="1.5"/>
</g>
''')
        return "".join(res)

    # Definição dos Ícones SVG
    icon_box = '''<g transform="scale(1.2)"><path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16zM3.27 6.96L12 12.01l8.73-5.05M12 22.08V12" fill="none" stroke="#ef4444" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/></g>'''
    icon_crit = '''<g transform="scale(1.2)"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" fill="none" stroke="#ef4444" stroke-width="2.2"/><polyline points="14 2 14 8 20 8" fill="none" stroke="#ef4444" stroke-width="2"/><line x1="16" y1="13" x2="8" y2="13" stroke="#ef4444" stroke-width="2"/><line x1="16" y1="17" x2="8" y2="17" stroke="#ef4444" stroke-width="2"/><polyline points="10 9 9 9 8 9" stroke="#ef4444" stroke-width="2"/></g>'''
    icon_evid = '''<g transform="scale(1.2)"><circle cx="11" cy="11" r="8" fill="none" stroke="#ef4444" stroke-width="2.5"/><line x1="21" y1="21" x2="16.65" y2="16.65" stroke="#ef4444" stroke-width="2.5" stroke-linecap="round"/></g>'''
    icon_prob = '''<g transform="scale(1.2)"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" fill="none" stroke="#f97316" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/><line x1="12" y1="9" x2="12" y2="13" stroke="#f97316" stroke-width="2.5" stroke-linecap="round"/><circle cx="12" cy="17" r="1.2" fill="#f97316"/></g>'''
    icon_risco = '''<g transform="scale(1.2)"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" fill="none" stroke="#f97316" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/><line x1="12" y1="8" x2="12" y2="12" stroke="#f97316" stroke-width="2.5" stroke-linecap="round"/><circle cx="12" cy="16" r="1.2" fill="#f97316"/></g>'''
    icon_stake = '''<g transform="scale(1.2)"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" fill="none" stroke="#f97316" stroke-width="2" stroke-linecap="round"/><circle cx="9" cy="7" r="4" fill="none" stroke="#f97316" stroke-width="2"/><path d="M23 21v-2a4 4 0 0 0-3-3.87" fill="none" stroke="#f97316" stroke-width="2" stroke-linecap="round"/><path d="M16 3.13a4 4 0 0 1 0 7.75" fill="none" stroke="#f97316" stroke-width="2" stroke-linecap="round"/></g>'''
    icon_asseg = '''<g transform="scale(1.2)"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" fill="none" stroke="#3b82f6" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/><polyline points="22 4 12 14.01 9 11.01" fill="none" stroke="#3b82f6" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/></g>'''
    icon_obj = '''<g transform="scale(1.2)"><circle cx="12" cy="12" r="10" fill="none" stroke="#10b981" stroke-width="2.2"/><circle cx="12" cy="12" r="6" fill="none" stroke="#10b981" stroke-width="2.2"/><circle cx="12" cy="12" r="2" fill="#10b981"/></g>'''
    icon_nesc = '''<g transform="scale(1.2)"><circle cx="12" cy="12" r="10" fill="none" stroke="#10b981" stroke-width="2.2"/><line x1="15" y1="9" x2="9" y2="15" stroke="#10b981" stroke-width="2.5" stroke-linecap="round"/><line x1="9" y1="9" x2="15" y2="15" stroke="#10b981" stroke-width="2.5" stroke-linecap="round"/></g>'''
    icon_esc = '''<g transform="scale(1.2)"><path d="M6 2v14a2 2 0 0 0 2 2h14" fill="none" stroke="#10b981" stroke-width="2.2" stroke-linecap="round"/><path d="M18 22V8a2 2 0 0 0-2-2H2" fill="none" stroke="#10b981" stroke-width="2.2" stroke-linecap="round"/></g>'''
    icon_ent = '''<g transform="scale(1.2)"><path d="M16 16l2 2 4-4" fill="none" stroke="#3b82f6" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/><path d="M21 10V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l2-1.14" fill="none" stroke="#3b82f6" stroke-width="2" stroke-linecap="round"/><polyline points="3.27 6.96 12 12.01 20.73 6.96" fill="none" stroke="#3b82f6" stroke-width="2" stroke-linecap="round"/><line x1="12" y1="22.08" x2="12" y2="12" stroke="#3b82f6" stroke-width="2" stroke-linecap="round"/></g>'''
    icon_data = '''<g transform="scale(1.2)"><rect x="3" y="4" width="18" height="18" rx="2" ry="2" fill="none" stroke="#3b82f6" stroke-width="2"/><line x1="16" y1="2" x2="16" y2="6" stroke="#3b82f6" stroke-width="2" stroke-linecap="round"/><line x1="8" y1="2" x2="8" y2="6" stroke="#3b82f6" stroke-width="2" stroke-linecap="round"/><line x1="3" y1="10" x2="21" y2="10" stroke="#3b82f6" stroke-width="2"/><circle cx="12" cy="16" r="3" fill="none" stroke="#3b82f6" stroke-width="1.8"/><polyline points="12 14.5 12 16 13.5 16" fill="none" stroke="#3b82f6" stroke-width="1.8" stroke-linecap="round"/></g>'''

    # =========================================================================
    # LINHA 1 (y = 290..650, h = 360)
    # =========================================================================
    
    # CARD 1: 1. Objeto (Col 1, x=60)
    c1_x, c1_y, c1_w, c1_h = 60, 290, 990, 360
    svg_parts.append(draw_card_base("1", c1_x, c1_y, c1_w, c1_h, "#ef4444", icon_box, "1. Objeto"))
    svg_parts.append(f'''
    <g class="font-sans" transform="translate({c1_x + 32}, {c1_y + 98})">
        <text x="0" y="0" font-size="15.5" font-weight="400" fill="#334155" line-height="24">
            <tspan x="0" dy="0">Práticas correntes de proteção de dados pessoais adotadas pelas prefeituras</tspan>
            <tspan x="0" dy="25">jurisdicionadas deste Tribunal com ênfase no cumprimento das decisões proferidas</tspan>
            <tspan x="0" dy="25">no âmbito do Processo TCE-RJ nº 217.899-0/2024.</tspan>
        </text>
        
        <rect x="0" y="75" width="{c1_w - 64}" height="135" rx="10" ry="10" fill="#f8fafc" stroke="#e2e8f0" stroke-width="1"/>
        <text x="20" y="105" font-size="14" font-weight="700" fill="#0f172a">Destaques do Objeto da Auditoria:</text>
        <text x="20" y="132" font-size="13.5" font-weight="500" fill="#475569">• Delimitação Subjetiva: <tspan font-weight="400">91 Administrações Municipais do Estado do Rio de Janeiro.</tspan></text>
        <text x="20" y="157" font-size="13.5" font-weight="500" fill="#475569">• Foco Material: <tspan font-weight="400">Governança, segurança, direitos dos titulares e conformidade à LGPD.</tspan></text>
        <text x="20" y="182" font-size="13.5" font-weight="500" fill="#475569">• Monitoramento Específico: <tspan font-weight="400">Implementação das determinações e recomendações de 2024.</tspan></text>
    </g>
''')

    # CARD 2: 2. Critérios (Col 2, x=1105)
    c2_x, c2_y, c2_w, c2_h = 1105, 290, 990, 360
    svg_parts.append(draw_card_base("2", c2_x, c2_y, c2_w, c2_h, "#ef4444", icon_crit, "2. Critérios"))
    crit_items = [
        ("1", "Lei Federal nº 13.709/2018 (Lei Geral de Proteção de Dados Pessoais – LGPD);"),
        ("2", "Acórdão nº 3931/2025, referente à Auditoria temática de LGPD de 2024;"),
        ("3", "Resoluções, regulamentos, guias e orientações expedidos pela ANPD;"),
        ("4", "Normas ABNT NBR ISO/IEC 27001, 27002 e 27701 (Segurança e Privacidade);"),
        ("5", "Planos de ação apresentados pelas prefeituras em atendimento às decisões do Tribunal;"),
        ("6", "Programa de Privacidade e Segurança da Informação (PPSI) do Governo Federal.")
    ]
    svg_parts.append(f'''
    <g class="font-sans" transform="translate({c2_x + 32}, {c2_y + 98})">
        <text x="0" y="0" font-size="14.5" font-weight="600" fill="#0f172a">A fiscalização adotará formalmente como critérios balizadores:</text>
''')
    for i, (num, txt) in enumerate(crit_items):
        y_pos = 28 + (i * 37)
        svg_parts.append(f'''
        <g transform="translate(0, {y_pos})">
            <circle cx="12" cy="9" r="11" fill="#fee2e2"/>
            <text x="12" y="13" font-size="12" font-weight="800" fill="#b91c1c" text-anchor="middle">{num}</text>
            <text x="32" y="14" font-size="13.5" font-weight="500" fill="#334155">{escape_xml(txt)}</text>
        </g>
''')
    svg_parts.append('    </g>\n')

    # CARD 3: 3. Evidências (Col 3, x=2150)
    c3_x, c3_y, c3_w, c3_h = 2150, 290, 990, 360
    svg_parts.append(draw_card_base("3", c3_x, c3_y, c3_w, c3_h, "#ef4444", icon_evid, "3. Evidências"))
    evid_col1 = [
        "Respostas ao questionário eletrônico de avaliação à LGPD;",
        "Documentos comprobatórios encaminhados pelos jurisdicionados;",
        "Planos de ação apresentados pelas prefeituras;",
        "Políticas, normas e procedimentos de proteção de dados pessoais;",
        "Políticas e normativos formais de segurança da informação;",
        "Atos de designação do encarregado pelo tratamento (DPO);",
        "Inventários de dados pessoais e registros de operações (ROPA);"
    ]
    evid_col2 = [
        "Relatórios de impacto à proteção de dados (RIPD), quando existentes;",
        "Avaliações e registros de riscos relacionados à privacidade;",
        "Avisos de privacidade e informações publicadas nos portais;",
        "Procedimentos e registros de atendimento aos direitos dos titulares;",
        "Procedimentos relacionados à resposta e comunicação de incidentes;",
        "Evidências documentadas de ações de capacitação e conscientização."
    ]
    svg_parts.append(f'''
    <g class="font-sans" transform="translate({c3_x + 32}, {c3_y + 95})">
        <text x="0" y="0" font-size="14.5" font-weight="600" fill="#0f172a">Fontes de evidência documentais e eletrônicas a serem examinadas:</text>
        
        <!-- Coluna Esquerda -->
        <g transform="translate(0, 18)">
''')
    for i, e in enumerate(evid_col1):
        svg_parts.append(f'''
            <text x="0" y="{i * 31}" font-size="12.5" font-weight="500" fill="#334155"><tspan font-weight="800" fill="#ef4444">• </tspan>{escape_xml(e)}</text>
''')
    svg_parts.append(f'''
        </g>
        
        <!-- Coluna Direita -->
        <g transform="translate({(c3_w - 64) // 2 + 10}, 18)">
''')
    for i, e in enumerate(evid_col2):
        svg_parts.append(f'''
            <text x="0" y="{i * 31}" font-size="12.5" font-weight="500" fill="#334155"><tspan font-weight="800" fill="#ef4444">• </tspan>{escape_xml(e)}</text>
''')
    svg_parts.append('        </g>\n    </g>\n')

    # =========================================================================
    # LINHA 2 (y = 680..1380, h = 700)
    # =========================================================================

    # CARD 4: 4. Problema de Auditoria (Col 1, x=60)
    c4_x, c4_y, c4_w, c4_h = 60, 680, 990, 700
    svg_parts.append(draw_card_base("4", c4_x, c4_y, c4_w, c4_h, "#f97316", icon_prob, "4. Problema de Auditoria"))
    svg_parts.append(f'''
    <g class="font-sans" transform="translate({c4_x + 32}, {c4_y + 95})">
        <!-- Sub-bloco 1: Contexto 2022 -->
        <rect x="0" y="0" width="{c4_w - 64}" height="165" rx="12" ry="12" fill="#fff7ed" stroke="#ffedd5" stroke-width="1.5"/>
        <circle cx="28" cy="28" r="12" fill="#ea580c"/>
        <text x="28" y="32" font-size="11" font-weight="800" fill="#ffffff" text-anchor="middle">1</text>
        <text x="50" y="32" font-size="15" font-weight="800" fill="#9a3412">Fiscalização Inicial (Ciclo 2022): Cenário Incipiente</text>
        <text x="24" y="62" font-size="14" font-weight="400" fill="#431407">
            <tspan x="24" dy="0">Fiscalização inicial realizada em 2022 para avaliar a adequação das prefeituras à LGPD</tspan>
            <tspan x="24" dy="24">identificou um cenário incipiente de adoção de práticas de segurança e proteção aos</tspan>
            <tspan x="24" dy="24">dados pessoais. Poucos municípios fluminenses haviam tomado alguma iniciativa formal</tspan>
            <tspan x="24" dy="24">ou estruturada para se adequar à Lei.</tspan>
        </text>

        <!-- Sub-bloco 2: Contexto 2024 -->
        <rect x="0" y="185" width="{c4_w - 64}" height="165" rx="12" ry="12" fill="#fff7ed" stroke="#ffedd5" stroke-width="1.5"/>
        <circle cx="28" cy="213" r="12" fill="#ea580c"/>
        <text x="28" y="217" font-size="11" font-weight="800" fill="#ffffff" text-anchor="middle">2</text>
        <text x="50" y="217" font-size="15" font-weight="800" fill="#9a3412">Fiscalização Conjunta (Ciclo 2024): Evolução com Infrações</text>
        <text x="24" y="247" font-size="14" font-weight="400" fill="#431407">
            <tspan x="24" dy="0">Trabalho posterior realizado em 2024 em conjunto com outros Tribunais de Contas</tspan>
            <tspan x="24" dy="24">mensurou uma evolução no panorama municipal, porém ainda infringindo diversos</tspan>
            <tspan x="24" dy="24">dispositivos legais essenciais da LGPD e mantendo elevado grau de vulnerabilidade</tspan>
            <tspan x="24" dy="24">e risco aos dados dos cidadãos.</tspan>
        </text>

        <!-- Sub-bloco 3: Demanda e Atuação 2026 -->
        <rect x="0" y="370" width="{c4_w - 64}" height="205" rx="12" ry="12" fill="#fef2f2" stroke="#fee2e2" stroke-width="1.5"/>
        <circle cx="28" cy="398" r="12" fill="#dc2626"/>
        <text x="28" y="402" font-size="11" font-weight="800" fill="#ffffff" text-anchor="middle">3</text>
        <text x="50" y="402" font-size="15" font-weight="800" fill="#991b1b">Demanda da Especializada e O Que Fazer (Ciclo 2026)</text>
        <text x="24" y="432" font-size="14" font-weight="400" fill="#7f1d1d">
            <tspan x="24" dy="0">Diante disso, e alinhando-se à estratégia de fiscalização da unidade especializada</tspan>
            <tspan x="24" dy="24">(CAD-TI), julgou-se pertinente reavaliar mediante uma auditoria de conformidade a</tspan>
            <tspan x="24" dy="24">evolução das práticas de proteção de dados pessoais e o grau de implementação das</tspan>
            <tspan x="24" dy="24">medidas destinadas ao cumprimento das decisões proferidas no Processo TCE-RJ nº</tspan>
            <tspan x="24" dy="24">217.899-0/2024 (Acórdão nº 3931/2025).</tspan>
        </text>
    </g>
''')

    # CARD 5: 5. Riscos da Fiscalização (Col 2, x=1105)
    c5_x, c5_y, c5_w, c5_h = 1105, 680, 990, 700
    svg_parts.append(draw_card_base("5", c5_x, c5_y, c5_w, c5_h, "#f97316", icon_risco, "5. Riscos da Fiscalização"))
    svg_parts.append(f'''
    <g class="font-sans" transform="translate({c5_x + 32}, {c5_y + 90})">
        <!-- Definição de Risco -->
        <rect x="0" y="0" width="{c5_w - 64}" height="64" rx="8" ry="8" fill="#f8fafc" stroke="#e2e8f0" stroke-width="1"/>
        <text x="16" y="24" font-size="13" font-weight="700" fill="#0f172a">Conceito Normativo de Risco de Auditoria:</text>
        <text x="16" y="46" font-size="13" font-weight="400" fill="#475569">Possibilidade de que a equipe formule conclusão inadequada por limitações dos procedimentos ou informações.</text>

        <!-- 5.1 Riscos Inerentes -->
        <g transform="translate(0, 80)">
            <rect x="0" y="0" width="{c5_w - 64}" height="150" rx="10" ry="10" fill="#fff7ed" stroke="#fed7aa" stroke-width="1"/>
            <text x="18" y="26" font-size="14.5" font-weight="800" fill="#c2410c">5.1 Riscos Inerentes</text>
            <text x="18" y="52" font-size="13" font-weight="500" fill="#431407">• Grande volume de documentos a serem analisados (91 prefeituras municipais);</text>
            <text x="18" y="76" font-size="13" font-weight="500" fill="#431407">• Alterações organizacionais decorrentes de transições de gestão municipal;</text>
            <text x="18" y="100" font-size="13" font-weight="500" fill="#431407">• Respostas autodeclaradas suscetíveis a superestimar ou subestimar a realidade local;</text>
            <text x="18" y="124" font-size="13" font-weight="500" fill="#431407">• Limitações inerentes à abordagem exclusivamente remota e documental.</text>
        </g>

        <!-- 5.2 Riscos de Controle -->
        <g transform="translate(0, 245)">
            <rect x="0" y="0" width="{c5_w - 64}" height="150" rx="10" ry="10" fill="#fefce8" stroke="#fef08a" stroke-width="1"/>
            <text x="18" y="26" font-size="14.5" font-weight="800" fill="#a16207">5.2 Riscos de Controle</text>
            <text x="18" y="52" font-size="13" font-weight="500" fill="#713f12">• Ausência de critérios uniformes de análise e pontuação entre os auditores;</text>
            <text x="18" y="76" font-size="13" font-weight="500" fill="#713f12">• Interpretação divergente das respostas prestadas pela equipe técnica;</text>
            <text x="18" y="100" font-size="13" font-weight="500" fill="#713f12">• Falhas eventuais nos pontos de controle de revisão técnica e supervisão colegiada;</text>
            <text x="18" y="124" font-size="13" font-weight="500" fill="#713f12">• Inconsistências na consolidação, ponderação e tabulação dos resultados.</text>
        </g>

        <!-- 5.3 Riscos de Detecção -->
        <g transform="translate(0, 410)">
            <rect x="0" y="0" width="{c5_w - 64}" height="150" rx="10" ry="10" fill="#fef2f2" stroke="#fecaca" stroke-width="1"/>
            <text x="18" y="26" font-size="14.5" font-weight="800" fill="#b91c1c">5.3 Riscos de Detecção</text>
            <text x="18" y="52" font-size="13" font-weight="500" fill="#7f1d1d">• Não identificação de inconsistências entre respostas fornecidas e documentos anexos;</text>
            <text x="18" y="76" font-size="13" font-weight="500" fill="#7f1d1d">• Aceitação inadvertida de evidências probatórias insuficientes ou inadequadas;</text>
            <text x="18" y="100" font-size="13" font-weight="500" fill="#7f1d1d">• Erros na agregação e consolidação quantitativa dos dados da fiscalização;</text>
            <text x="18" y="124" font-size="13" font-weight="500" fill="#7f1d1d">• Conclusões inadequadas em virtude de insuficiência dos procedimentos executados.</text>
        </g>
    </g>
''')

    # CARD 8: 8. Objetivo da Fiscalização (Col 3, x=2150)
    c8_x, c8_y, c8_w, c8_h = 2150, 680, 990, 700
    svg_parts.append(draw_card_base("8", c8_x, c8_y, c8_w, c8_h, "#10b981", icon_obj, "8. Objetivo"))
    svg_parts.append(f'''
    <g class="font-sans" transform="translate({c8_x + 32}, {c8_y + 95})">
        <!-- Declaração Central do Objetivo -->
        <rect x="0" y="0" width="{c8_w - 64}" height="185" rx="12" ry="12" fill="#ecfdf5" stroke="#a7f3d0" stroke-width="1.5"/>
        <text x="24" y="32" font-size="16" font-weight="800" fill="#065f46">Objetivo Geral da Auditoria Governamental:</text>
        <text x="24" y="62" font-size="14.5" font-weight="500" fill="#064e3b" line-height="24">
            <tspan x="24" dy="0">Verificar o grau de conformidade das 91 prefeituras municipais jurisdicionadas</tspan>
            <tspan x="24" dy="24">com os requisitos selecionados da Lei nº 13.709/2018 (LGPD), bem como mensurar</tspan>
            <tspan x="24" dy="24">o nível de cumprimento das decisões proferidas no Processo TCE-RJ nº 217.899-0/2024,</tspan>
            <tspan x="24" dy="24">e comparação com os resultados da fiscalização realizada em 2024, a fim de</tspan>
            <tspan x="24" dy="24">identificar a evolução da conformidade, as pendências existentes e os riscos</tspan>
            <tspan x="24" dy="24">residuais relacionados à proteção de dados pessoais, propondo os encaminhamentos.</tspan>
        </text>

        <!-- 4 Dimensões Estratégicas -->
        <g transform="translate(0, 205)">
            <!-- Dim 1 -->
            <rect x="0" y="0" width="{c8_w - 64}" height="80" rx="10" ry="10" fill="#f8fafc" stroke="#e2e8f0" stroke-width="1"/>
            <text x="18" y="26" font-size="14" font-weight="700" fill="#0f172a">1. Avaliação de Conformidade Legal (LGPD)</text>
            <text x="18" y="50" font-size="13" font-weight="400" fill="#475569">Mapear e mensurar o grau de aderência formal e prática aos preceitos da Lei nº 13.709/2018.</text>

            <!-- Dim 2 -->
            <rect x="0" y="92" width="{c8_w - 64}" height="80" rx="10" ry="10" fill="#f8fafc" stroke="#e2e8f0" stroke-width="1"/>
            <text x="18" y="118" font-size="14" font-weight="700" fill="#0f172a">2. Monitoramento de Decisões Prévias (Proc. 217.899-0/2024)</text>
            <text x="18" y="142" font-size="13" font-weight="400" fill="#475569">Verificar o atendimento das determinações e recomendações e execução dos planos de ação.</text>

            <!-- Dim 3 -->
            <rect x="0" y="184" width="{c8_w - 64}" height="80" rx="10" ry="10" fill="#f8fafc" stroke="#e2e8f0" stroke-width="1"/>
            <text x="18" y="210" font-size="14" font-weight="700" fill="#0f172a">3. Análise Comparativa e Diagnóstico de Evolução (2024–2026)</text>
            <text x="18" y="234" font-size="13" font-weight="400" fill="#475569">Identificar se houve avanços estruturais, estagnação ou retrocesso das práticas municipais.</text>

            <!-- Dim 4 -->
            <rect x="0" y="276" width="{c8_w - 64}" height="80" rx="10" ry="10" fill="#f8fafc" stroke="#e2e8f0" stroke-width="1"/>
            <text x="18" y="302" font-size="14" font-weight="700" fill="#0f172a">4. Indução de Boas Práticas e Propostas de Encaminhamento</text>
            <text x="18" y="326" font-size="13" font-weight="400" fill="#475569">Formular propostas de deliberação ao Plenário e orientações didáticas preventivas.</text>
        </g>
    </g>
''')

    # =========================================================================
    # COLUNA 1 - CONTINUAÇÃO (y = 1410..)
    # =========================================================================

    # CARD 6: 6. Stakeholders (Col 1, y=1410, h=430)
    c6_x, c6_y, c6_w, c6_h = 60, 1410, 990, 430
    svg_parts.append(draw_card_base("6", c6_x, c6_y, c6_w, c6_h, "#f97316", icon_stake, "6. Stakeholders"))
    svg_parts.append(f'''
    <g class="font-sans" transform="translate({c6_x + 32}, {c6_y + 95})">
        <!-- Internos -->
        <rect x="0" y="0" width="{(c6_w - 74) // 2}" height="295" rx="12" ry="12" fill="#fff7ed" stroke="#ffedd5" stroke-width="1.5"/>
        <text x="20" y="30" font-size="16" font-weight="800" fill="#c2410c">Stakeholders Internos (TCE-RJ)</text>
        <line x1="20" y1="44" x2="{(c6_w - 74) // 2 - 20}" y2="44" stroke="#fed7aa" stroke-width="1"/>
        <g transform="translate(20, 68)">
            <text x="0" y="0" font-size="13.5" font-weight="600" fill="#431407">• Plenário do TCE-RJ <tspan font-weight="400" fill="#78350f">(Deliberação e julgamento)</tspan></text>
            <text x="0" y="38" font-size="13.5" font-weight="600" fill="#431407">• Secretaria-Geral de Controle Externo <tspan font-weight="400" fill="#78350f">(SGE)</tspan></text>
            <text x="0" y="76" font-size="13.5" font-weight="600" fill="#431407">• DRC <tspan font-weight="400" fill="#78350f">(Subsecretaria de Cidadania)</tspan></text>
            <text x="0" y="114" font-size="13.5" font-weight="600" fill="#431407">• Equipe de Auditoria <tspan font-weight="400" fill="#78350f">(Planejamento e execução)</tspan></text>
            <text x="0" y="152" font-size="13.5" font-weight="600" fill="#431407">• Ministério Público de Contas <tspan font-weight="400" fill="#78350f">(Parecer final)</tspan></text>
            <text x="0" y="190" font-size="12" font-weight="500" fill="#9a3412">Interesse: Eficácia do controle externo e indução de conformidade.</text>
        </g>

        <!-- Externos -->
        <rect x="{(c6_w - 74) // 2 + 10}" y="0" width="{(c6_w - 74) // 2}" height="295" rx="12" ry="12" fill="#f8fafc" stroke="#e2e8f0" stroke-width="1.5"/>
        <text x="{(c6_w - 74) // 2 + 30}" y="30" font-size="16" font-weight="800" fill="#0f172a">Stakeholders Externos</text>
        <line x1="{(c6_w - 74) // 2 + 30}" y1="44" x2="{c6_w - 64 - 20}" y2="44" stroke="#cbd5e1" stroke-width="1"/>
        <g transform="translate({(c6_w - 74) // 2 + 30}, 68)">
            <text x="0" y="0" font-size="13.5" font-weight="600" fill="#334155">• Prefeitos municipais <tspan font-weight="400" fill="#64748b">(Gestores responsáveis)</tspan></text>
            <text x="0" y="38" font-size="13.5" font-weight="600" fill="#334155">• Controladorias internas <tspan font-weight="400" fill="#64748b">(Monitoramento local)</tspan></text>
            <text x="0" y="76" font-size="13.5" font-weight="600" fill="#334155">• Encarregados pelo tratamento <tspan font-weight="400" fill="#64748b">(DPOs municipais)</tspan></text>
            <text x="0" y="114" font-size="13.5" font-weight="600" fill="#334155">• Unidades de Tecnologia da Informação <tspan font-weight="400" fill="#64748b">(TIC)</tspan></text>
            <text x="0" y="152" font-size="13.5" font-weight="600" fill="#334155">• ANPD <tspan font-weight="400" fill="#64748b">(Autoridade Nacional de Proteção de Dados)</tspan></text>
            <text x="0" y="190" font-size="13.5" font-weight="600" fill="#334155">• Titulares de dados pessoais <tspan font-weight="400" fill="#64748b">(Cidadãos e servidores)</tspan></text>
        </g>
    </g>
''')

    # CARD 9: 9. Não Escopo (Col 1, y=1870, h=570)
    c9_x, c9_y, c9_w, c9_h = 60, 1870, 990, 570
    svg_parts.append(draw_card_base("9", c9_x, c9_y, c9_w, c9_h, "#10b981", icon_nesc, "9. Não Escopo"))
    nao_escopo_items = [
        ("Avaliação exaustiva de todas as operações de tratamento:", 
         "Não serão auditados todos os fluxos de dados e sistemas legados de cada secretaria municipal de modo exaustivo."),
        ("Atuação funcional e desempenho do Encarregado:", 
         "A fiscalização não tem caráter disciplinar ou avaliativo individual do servidor nomeado Encarregado."),
        ("Operacionalização dos controles de segurança da informação:", 
         "Não serão executados testes de intrusão (pentests), perícias forenses ou inspeções físicas universais."),
        ("Avaliação integral da conformidade de operadores contratados:", 
         "O foco recai sobre o papel do município enquanto Controlador, não abrangendo auditoria nos prestadores terceirizados."),
        ("Avaliação de contratações relacionadas à proteção de dados:", 
         "Não constitui escopo a análise da regularidade orçamentária ou licitatória de contratos de TI para adequação à LGPD.")
    ]
    svg_parts.append(f'''
    <g class="font-sans" transform="translate({c9_x + 32}, {c9_y + 95})">
        <text x="0" y="0" font-size="14.5" font-weight="700" fill="#b91c1c">Delimitação Negativa da Fiscalização (Não integram o escopo):</text>
''')
    for i, (title, desc) in enumerate(nao_escopo_items):
        y_pos = 25 + (i * 85)
        svg_parts.append(f'''
        <g transform="translate(0, {y_pos})">
            <rect x="0" y="0" width="{c9_w - 64}" height="74" rx="8" ry="8" fill="#fef2f2" stroke="#fee2e2" stroke-width="1"/>
            <circle cx="20" cy="20" r="10" fill="#ef4444"/>
            <line x1="15" y1="15" x2="25" y2="25" stroke="#ffffff" stroke-width="2" stroke-linecap="round"/>
            <line x1="25" y1="15" x2="15" y2="25" stroke="#ffffff" stroke-width="2" stroke-linecap="round"/>
            <text x="38" y="24" font-size="13.5" font-weight="800" fill="#991b1b">{escape_xml(title)}</text>
            <text x="38" y="48" font-size="12.5" font-weight="500" fill="#7f1d1d">{escape_xml(desc)}</text>
        </g>
''')
    svg_parts.append('    </g>\n')

    # CARD 10: 10. Escopo (Col 1, y=2470, h=660)
    c10_x, c10_y, c10_w, c10_h = 60, 2470, 990, 660
    svg_parts.append(draw_card_base("10", c10_x, c10_y, c10_w, c10_h, "#10b981", icon_esc, "10. Escopo"))
    escopo_reqs = [
        "Estrutura de governança de proteção de dados pessoais",
        "Designação do encarregado pelo tratamento (DPO)",
        "Políticas, normas e procedimentos de proteção de dados",
        "Inventários de dados pessoais e registros de tratamento (ROPA)",
        "Gestão de riscos relacionados à privacidade e proteção de dados",
        "Mecanismos e canais de atendimento aos direitos dos titulares",
        "Procedimentos e planos formais de resposta a incidentes",
        "Capacitação e conscientização continuada dos agentes públicos",
        "Transparência, avisos de privacidade e divulgação nos portais"
    ]
    svg_parts.append(f'''
    <g class="font-sans" transform="translate({c10_x + 32}, {c10_y + 92})">
        <!-- Universo -->
        <rect x="0" y="0" width="{c10_w - 64}" height="46" rx="8" ry="8" fill="#ecfdf5" stroke="#a7f3d0" stroke-width="1"/>
        <text x="16" y="28" font-size="14" font-weight="700" fill="#065f46">Universo de Abrangência: <tspan font-weight="500" fill="#064e3b">91 Prefeituras Municipais jurisdicionadas do Estado do Rio de Janeiro.</tspan></text>

        <!-- Requisitos da LGPD -->
        <text x="0" y="72" font-size="14.5" font-weight="800" fill="#0f172a">Dimensões e Requisitos da LGPD Auditados:</text>
        <g transform="translate(0, 84)">
''')
    for i, req in enumerate(escopo_reqs):
        col = i % 2
        row = i // 2
        x_p = col * ((c10_w - 64) // 2 + 10)
        y_p = row * 40
        svg_parts.append(f'''
            <g transform="translate({x_p}, {y_p})">
                <rect x="0" y="0" width="{(c10_w - 84) // 2}" height="32" rx="6" ry="6" fill="#f8fafc" stroke="#e2e8f0" stroke-width="1"/>
                <circle cx="14" cy="16" r="5" fill="#10b981"/>
                <text x="26" y="21" font-size="12" font-weight="600" fill="#334155">{escape_xml(req)}</text>
            </g>
''')
    svg_parts.append(f'''
        </g>
        
        <!-- Atividades e Produtos Adicionais -->
        <g transform="translate(0, 305)">
            <text x="0" y="0" font-size="14" font-weight="800" fill="#0f172a">Produtos, Análises Estratégicas e Itens Especiais do Questionário:</text>
            <rect x="0" y="12" width="{c10_w - 64}" height="225" rx="10" ry="10" fill="#f8fafc" stroke="#e2e8f0" stroke-width="1"/>
            <text x="18" y="38" font-size="13" font-weight="500" fill="#334155">• Propostas de encaminhamento formal para sanar inconformidades detectadas;</text>
            <text x="18" y="64" font-size="13" font-weight="500" fill="#334155">• Elaboração de material didático e guias orientativos de indução aos auditados;</text>
            <text x="18" y="90" font-size="13" font-weight="500" fill="#334155">• Mensuração e cálculo do índice de conformidade iLGPD municipal;</text>
            <text x="18" y="116" font-size="13" font-weight="500" fill="#334155">• Análise comparativa da evolução dos resultados em relação à fiscalização de 2024;</text>
            <text x="18" y="142" font-size="13" font-weight="500" fill="#334155">• Verificação do cumprimento integral da decisão do Processo TCE-RJ nº 217.899-0/2024;</text>
            <text x="18" y="168" font-size="13" font-weight="500" fill="#334155">• Identificação das causas de possíveis não cumprimentos das decisões do Tribunal;</text>
            <text x="18" y="194" font-size="13" font-weight="500" fill="#334155">• Levantamento sobre contratação de consultorias/soluções LGPD e histórico de vazamentos.</text>
        </g>
    </g>
''')

    # =========================================================================
    # COLUNA 2 - CONTINUAÇÃO (y = 1410..)
    # =========================================================================

    # CARD 7: 7. Nível de Asseguração (Col 2, y=1410, h=430)
    c7_x, c7_y, c7_w, c7_h = 1105, 1410, 990, 430
    svg_parts.append(draw_card_base("7", c7_x, c7_y, c7_w, c7_h, "#3b82f6", icon_asseg, "7. Nível de Asseguração"))
    svg_parts.append(f'''
    <g class="font-sans" transform="translate({c7_x + 32}, {c7_y + 95})">
        <!-- Caixa de Destaque -->
        <rect x="0" y="0" width="{c7_w - 64}" height="90" rx="12" ry="12" fill="#eff6ff" stroke="#bfdbfe" stroke-width="1.5"/>
        <text x="24" y="36" font-size="15" font-weight="700" fill="#1e40af">Declaração Metodológica Formal:</text>
        <text x="24" y="66" font-size="18" font-weight="800" fill="#1d4ed8">A fiscalização será realizada com NÍVEL DE ASSEGURAÇÃO LIMITADA.</text>

        <!-- Justificativa Técnica -->
        <g transform="translate(0, 110)">
            <text x="0" y="16" font-size="14.5" font-weight="700" fill="#0f172a">Fundamentação Técnica e Normativa (NBASP / ISSAI 300 e 3000):</text>
            <text x="0" y="44" font-size="13.5" font-weight="400" fill="#334155" line-height="22">
                <tspan x="0" dy="0">A classificação como asseguração limitada fundamenta-se nas características estruturais</tspan>
                <tspan x="0" dy="24">da abordagem adotada pela Coordenadoria de Auditoria:</tspan>
            </text>
            
            <g transform="translate(0, 75)">
                <rect x="0" y="0" width="{c7_w - 64}" height="120" rx="8" ry="8" fill="#f8fafc" stroke="#e2e8f0" stroke-width="1"/>
                <text x="16" y="26" font-size="13" font-weight="600" fill="#1e293b">• Amplitude do Universo: <tspan font-weight="400" fill="#475569">Fiscalização simultânea das 91 prefeituras de forma abrangente;</tspan></text>
                <text x="16" y="52" font-size="13" font-weight="600" fill="#1e293b">• Abordagem Remota: <tspan font-weight="400" fill="#475569">Coleta de informações estruturada via questionário eletrônico padronizado;</tspan></text>
                <text x="16" y="78" font-size="13" font-weight="600" fill="#1e293b">• Natureza Declaratória: <tspan font-weight="400" fill="#475569">Dados alimentados pelos próprios órgãos auditados (autoavaliação);</tspan></text>
                <text x="16" y="104" font-size="13" font-weight="600" fill="#1e293b">• Validação Documental Amostral: <tspan font-weight="400" fill="#475569">Exame focado em amostras de evidências comprobatórias anexadas.</tspan></text>
            </g>
        </g>
    </g>
''')

    # CARD 11: 11. Entregas (Col 2, y=1870, h=1260)
    c11_x, c11_y, c11_w, c11_h = 1105, 1870, 990, 1260
    svg_parts.append(draw_card_base("11", c11_x, c11_y, c11_w, c11_h, "#3b82f6", icon_ent, "11. Entregas"))
    entregas_data = [
        ("Aprovação dos Termos de Auditoria", "02/09/2026", "Aprovação formal do planejamento e Canvas"),
        ("Conclusão da Matriz de Planejamento", "18/09/2026", "Consolidação das questões e procedimentos"),
        ("Conclusão e validação do Questionário", "25/09/2026", "Homologação do instrumento no sistema eletrônico"),
        ("Encaminhamento do Questionário aos Jurisdicionados", "28/09/2026", "Disponibilização formal para as 91 prefeituras"),
        ("Prazo final para recebimento do questionário", "23/10/2026", "Término da etapa de preenchimento municipal"),
        ("Conclusão da análise das respostas e evidências", "06/11/2026", "Finalização dos testes de auditoria pela equipe"),
        ("Encaminhamento do questionário de Comentários do Gestor", "09/11/2026", "Abertura do contraditório prévio aos auditados"),
        ("Prazo final para recebimento de Comentários do Gestor", "16/11/2026", "Recebimento das manifestações dos prefeitos"),
        ("Revisão técnica e supervisão", "24/11/2026", "Controle de qualidade e validação pela chefia"),
        ("Conclusão do Relatório de Fiscalização", "27/11/2026", "Entrega do relatório final consolidado")
    ]
    svg_parts.append(f'''
    <g class="font-sans" transform="translate({c11_x + 32}, {c11_y + 90})">
        <text x="0" y="0" font-size="14.5" font-weight="700" fill="#0f172a">Cronograma Formal de Entregas Pactuado:</text>
        
        <!-- Cabeçalho da Tabela -->
        <g transform="translate(0, 16)">
            <rect x="0" y="0" width="{c11_w - 64}" height="36" rx="6" ry="6" fill="#1e293b"/>
            <text x="20" y="23" font-size="13" font-weight="800" fill="#ffffff">MARCO DE ENTREGA / ATIVIDADE FORMAL</text>
            <text x="{c11_w - 64 - 130}" y="23" font-size="13" font-weight="800" fill="#ffffff" text-anchor="middle">DATA LIMITE</text>
        </g>
        
        <!-- Linhas da Tabela -->
        <g transform="translate(0, 56)">
''')
    for i, (nome, data, desc) in enumerate(entregas_data):
        bg_col = "#ffffff" if i % 2 == 0 else "#f8fafc"
        y_pos = i * 72
        svg_parts.append(f'''
            <g transform="translate(0, {y_pos})">
                <rect x="0" y="0" width="{c11_w - 64}" height="66" rx="6" ry="6" fill="{bg_col}" stroke="#e2e8f0" stroke-width="1"/>
                <circle cx="22" cy="24" r="10" fill="#3b82f6"/>
                <text x="22" y="28" font-size="11" font-weight="800" fill="#ffffff" text-anchor="middle">{i+1}</text>
                <text x="44" y="28" font-size="13.5" font-weight="700" fill="#0f172a">{escape_xml(nome)}</text>
                <text x="44" y="50" font-size="12" font-weight="500" fill="#64748b">{escape_xml(desc)}</text>
                
                <!-- Badge de Data -->
                <rect x="{c11_w - 64 - 185}" y="16" width="170" height="34" rx="17" ry="17" fill="#eff6ff" stroke="#bfdbfe" stroke-width="1"/>
                <text x="{c11_w - 64 - 100}" y="38" font-size="13" font-weight="800" fill="#1d4ed8" text-anchor="middle">{data}</text>
            </g>
''')
    svg_parts.append(f'''
        </g>

        <!-- Caixa de Produtos Resultantes -->
        <g transform="translate(0, 800)">
            <rect x="0" y="0" width="{c11_w - 64}" height="350" rx="12" ry="12" fill="#f0fdf4" stroke="#bbf7d0" stroke-width="1.5"/>
            <text x="24" y="32" font-size="16" font-weight="800" fill="#166534">Principais Produtos da Auditoria de Conformidade (LGPD 2026.2):</text>
            
            <g transform="translate(24, 55)">
                <text x="0" y="0" font-size="13.5" font-weight="700" fill="#14532d">1. Relatório Final de Auditoria Governamental:</text>
                <text x="0" y="22" font-size="13" font-weight="400" fill="#166534">Diagnóstico aprofundado com consolidação estatística da conformidade das 91 prefeituras.</text>
                
                <text x="0" y="60" font-size="13.5" font-weight="700" fill="#14532d">2. Painel de Indicadores e Ranking iLGPD 2026:</text>
                <text x="0" y="82" font-size="13" font-weight="400" fill="#166534">Mapeamento comparativo e categorização do nível de maturidade municipal em privacidade.</text>

                <text x="0" y="120" font-size="13.5" font-weight="700" fill="#14532d">3. Matriz de Achados e Propostas de Deliberação:</text>
                <text x="0" y="142" font-size="13" font-weight="400" fill="#166534">Recomendações e determinações orientadas à correção das desconformidades apuradas.</text>

                <text x="0" y="180" font-size="13.5" font-weight="700" fill="#14532d">4. Material Didático Orientativo para os Jurisdicionados:</text>
                <text x="0" y="202" font-size="13" font-weight="400" fill="#166534">Guia prático e pedagógico contendo orientações essenciais para apoio à adequação à LGPD.</text>

                <text x="0" y="240" font-size="13.5" font-weight="700" fill="#14532d">5. Relatório de Monitoramento do Processo TCE-RJ nº 217.899-0/2024:</text>
                <text x="0" y="262" font-size="13" font-weight="400" fill="#166534">Verificação conclusiva quanto ao atendimento do Acórdão nº 3931/2025.</text>
            </g>
        </g>
    </g>
''')

    # =========================================================================
    # COLUNA 3 - CONTINUAÇÃO (y = 1410..)
    # =========================================================================

    # CARD 12: 12. Datas e Ausências (Col 3, y=1410, h=1720)
    c12_x, c12_y, c12_w, c12_h = 2150, 1410, 990, 1720
    svg_parts.append(draw_card_base("12", c12_x, c12_y, c12_w, c12_h, "#3b82f6", icon_data, "12. Datas e Ausências"))
    svg_parts.append(f'''
    <g class="font-sans" transform="translate({c12_x + 32}, {c12_y + 90})">
        <!-- SEÇÃO A: MACRO-FASES DA AUDITORIA -->
        <text x="0" y="0" font-size="16" font-weight="800" fill="#0f172a">A. Macro-Etapas do Ciclo de Auditoria:</text>
        
        <!-- Fase 1: Planejamento -->
        <g transform="translate(0, 15)">
            <rect x="0" y="0" width="{c12_w - 64}" height="140" rx="10" ry="10" fill="#eff6ff" stroke="#bfdbfe" stroke-width="1.5"/>
            <text x="20" y="28" font-size="15" font-weight="800" fill="#1e40af">1. Fase de Planejamento (15/07/2026 a 25/09/2026)</text>
            <text x="20" y="54" font-size="13" font-weight="500" fill="#1e3a8a">• Estudos preliminares e levantamento legislativo (LGPD, ANPD, ISO 27701);</text>
            <text x="20" y="78" font-size="13" font-weight="500" fill="#1e3a8a">• Pactuação dos Termos de Auditoria (Canvas) e Matriz de Planejamento;</text>
            <text x="20" y="102" font-size="13" font-weight="500" fill="#1e3a8a">• Elaboração, teste de usabilidade e homologação do questionário eletrônico;</text>
            <text x="20" y="124" font-size="13" font-weight="500" fill="#1e3a8a">• Emissão formal de ofícios aos 91 prefeitos e designação de pontos focais.</text>
        </g>

        <!-- Fase 2: Execução -->
        <g transform="translate(0, 170)">
            <rect x="0" y="0" width="{c12_w - 64}" height="140" rx="10" ry="10" fill="#eff6ff" stroke="#bfdbfe" stroke-width="1.5"/>
            <text x="20" y="28" font-size="15" font-weight="800" fill="#1e40af">2. Fase de Execução e Coleta (28/09/2026 a 06/11/2026)</text>
            <text x="20" y="54" font-size="13" font-weight="500" fill="#1e3a8a">• Disponibilização do questionário eletrônico aos jurisdicionados;</text>
            <text x="20" y="78" font-size="13" font-weight="500" fill="#1e3a8a">• Plantão de atendimento técnico a dúvidas dos gestores e pontos focais;</text>
            <text x="20" y="102" font-size="13" font-weight="500" fill="#1e3a8a">• Recepção, conferência e validação da completude dos documentos anexados;</text>
            <text x="20" y="124" font-size="13" font-weight="500" fill="#1e3a8a">• Análise amostral de evidências e cálculo preliminar do índice iLGPD.</text>
        </g>

        <!-- Fase 3: Comentários do Gestor -->
        <g transform="translate(0, 325)">
            <rect x="0" y="0" width="{c12_w - 64}" height="135" rx="10" ry="10" fill="#eff6ff" stroke="#bfdbfe" stroke-width="1.5"/>
            <text x="20" y="28" font-size="15" font-weight="800" fill="#1e40af">3. Fase de Comentários do Gestor (09/11/2026 a 16/11/2026)</text>
            <text x="20" y="54" font-size="13" font-weight="500" fill="#1e3a8a">• Encaminhamento do relatório preliminar para contraditório e manifestação prévia;</text>
            <text x="20" y="78" font-size="13" font-weight="500" fill="#1e3a8a">• Oportunização de esclarecimentos sobre constatações e pendências;</text>
            <text x="20" y="102" font-size="13" font-weight="500" fill="#1e3a8a">• Análise das justificativas apresentadas e eventuais retificações de dados.</text>
        </g>

        <!-- Fase 4: Relatório Final -->
        <g transform="translate(0, 475)">
            <rect x="0" y="0" width="{c12_w - 64}" height="135" rx="10" ry="10" fill="#eff6ff" stroke="#bfdbfe" stroke-width="1.5"/>
            <text x="20" y="28" font-size="15" font-weight="800" fill="#1e40af">4. Fase de Supervisão e Conclusão (17/11/2026 a 27/11/2026)</text>
            <text x="20" y="54" font-size="13" font-weight="500" fill="#1e3a8a">• Revisão técnica analítica e controle de qualidade pela chefia da CAD-TI;</text>
            <text x="20" y="78" font-size="13" font-weight="500" fill="#1e3a8a">• Fechamento definitivo do Relatório de Fiscalização e Matriz de Achados;</text>
            <text x="20" y="102" font-size="13" font-weight="500" fill="#1e3a8a">• Encaminhamento formal dos autos para instrução processual do TCE-RJ.</text>
        </g>

        <!-- SEÇÃO B: AUSÊNCIAS E GOVERNANÇA DA EQUIPE -->
        <g transform="translate(0, 635)">
            <text x="0" y="0" font-size="16" font-weight="800" fill="#0f172a">B. Declaração de Ausências e Governança da Equipe (Item 12):</text>
            
            <!-- Declaração Formal -->
            <rect x="0" y="15" width="{c12_w - 64}" height="115" rx="10" ry="10" fill="#ecfdf5" stroke="#a7f3d0" stroke-width="1.5"/>
            <text x="20" y="42" font-size="14" font-weight="800" fill="#065f46">Declaração Inicial da Equipe de Auditoria:</text>
            <text x="20" y="68" font-size="13.5" font-weight="500" fill="#064e3b" line-height="22">
                <tspan x="20" dy="0">Não foram identificadas, na data de elaboração e aprovação destes Termos de</tspan>
                <tspan x="20" dy="24">Auditoria, ausências programadas capazes de comprometer o regular desenvolvimento</tspan>
                <tspan x="20" dy="24">e os marcos temporais pactuados para a fiscalização governamental.</tspan>
            </text>

            <!-- Regramento de Contingência -->
            <g transform="translate(0, 145)">
                <rect x="0" y="0" width="{c12_w - 64}" height="260" rx="10" ry="10" fill="#f8fafc" stroke="#e2e8f0" stroke-width="1"/>
                <text x="20" y="30" font-size="14.5" font-weight="700" fill="#0f172a">Diretrizes de Contingência para Afastamentos Supervenientes:</text>
                <text x="20" y="56" font-size="13" font-weight="400" fill="#334155" line-height="20">
                    <tspan x="20" dy="0">Eventuais férias, licenças, afastamentos médicos ou impedimentos supervenientes</tspan>
                    <tspan x="20" dy="22">deverão ser formal e tempestivamente registrados nos papéis de trabalho, com indicação:</tspan>
                </text>
                
                <g transform="translate(20, 105)">
                    <text x="0" y="0" font-size="13" font-weight="600" fill="#1e293b">1. Do integrante afetado: <tspan font-weight="400" fill="#475569">Nome, matrícula e atribuição funcional na auditoria;</tspan></text>
                    <text x="0" y="28" font-size="13" font-weight="600" fill="#1e293b">2. Do período de ausência: <tspan font-weight="400" fill="#475569">Datas precisas de início e término do afastamento;</tspan></text>
                    <text x="0" y="56" font-size="13" font-weight="600" fill="#1e293b">3. Das atividades impactadas: <tspan font-weight="400" fill="#475569">Testes, análises ou entregas sob responsabilidade do auditor;</tspan></text>
                    <text x="0" y="84" font-size="13" font-weight="600" fill="#1e293b">4. Das medidas de redistribuição: <tspan font-weight="400" fill="#475569">Remanejamento interno de demandas ou designação de suplente;</tspan></text>
                    <text x="0" y="112" font-size="13" font-weight="600" fill="#1e293b">5. Dos impactos sobre o cronograma: <tspan font-weight="400" fill="#475569">Avaliação de risco e salvaguarda das entregas previstas.</tspan></text>
                </g>
            </g>
        </g>

        <!-- SEÇÃO C: EQUIPE DE AUDITORIA DESIGNADA -->
        <g transform="translate(0, 1075)">
            <text x="0" y="0" font-size="16" font-weight="800" fill="#0f172a">C. Equipe de Auditoria Designada (Ofício nº 3022/26):</text>
            <rect x="0" y="15" width="{c12_w - 64}" height="490" rx="10" ry="10" fill="#f8fafc" stroke="#e2e8f0" stroke-width="1.5"/>
            
            <!-- Auditor 1 -->
            <g transform="translate(20, 35)">
                <circle cx="16" cy="16" r="14" fill="#0369a1"/>
                <text x="16" y="20" font-size="11" font-weight="800" fill="#ffffff" text-anchor="middle">AU</text>
                <text x="42" y="16" font-size="14" font-weight="700" fill="#0f172a">Bruno Mattos Souza de Souza Melo</text>
                <text x="42" y="34" font-size="12" font-weight="500" fill="#64748b">Auditor de Controle Externo | Matrícula: 02/004258 | Coordenador Setorial</text>
            </g>
            <line x1="20" y1="95" x2="{c12_w - 64 - 20}" y2="95" stroke="#e2e8f0" stroke-width="1"/>

            <!-- Auditor 2 -->
            <g transform="translate(20, 115)">
                <circle cx="16" cy="16" r="14" fill="#0369a1"/>
                <text x="16" y="20" font-size="11" font-weight="800" fill="#ffffff" text-anchor="middle">AU</text>
                <text x="42" y="16" font-size="14" font-weight="700" fill="#0f172a">João Paulo de Freitas Ramirez</text>
                <text x="42" y="34" font-size="12" font-weight="500" fill="#64748b">Auditor de Controle Externo | Matrícula: 02/004820 | Equipe de Auditoria</text>
            </g>
            <line x1="20" y1="175" x2="{c12_w - 64 - 20}" y2="175" stroke="#e2e8f0" stroke-width="1"/>

            <!-- Auditor 3 -->
            <g transform="translate(20, 195)">
                <circle cx="16" cy="16" r="14" fill="#0369a1"/>
                <text x="16" y="20" font-size="11" font-weight="800" fill="#ffffff" text-anchor="middle">AU</text>
                <text x="42" y="16" font-size="14" font-weight="700" fill="#0f172a">Augusto Cesar Benvenuto de Almeida</text>
                <text x="42" y="34" font-size="12" font-weight="500" fill="#64748b">Auditor de Controle Externo | Matrícula: 02/004823 | Equipe de Auditoria</text>
            </g>
            <line x1="20" y1="255" x2="{c12_w - 64 - 20}" y2="255" stroke="#e2e8f0" stroke-width="1"/>

            <!-- Auditor 4 -->
            <g transform="translate(20, 275)">
                <circle cx="16" cy="16" r="14" fill="#0369a1"/>
                <text x="16" y="20" font-size="11" font-weight="800" fill="#ffffff" text-anchor="middle">AU</text>
                <text x="42" y="16" font-size="14" font-weight="700" fill="#0f172a">Fabio Souza Lima</text>
                <text x="42" y="34" font-size="12" font-weight="500" fill="#64748b">Auditor de Controle Externo | Matrícula: 02/004822 | Equipe de Auditoria</text>
            </g>
            
            <!-- Box de Homologação -->
            <g transform="translate(20, 350)">
                <rect x="0" y="0" width="{c12_w - 104}" height="110" rx="8" ry="8" fill="#eff6ff" stroke="#bfdbfe" stroke-width="1"/>
                <text x="18" y="28" font-size="13" font-weight="700" fill="#1e40af">Formalização Institucional:</text>
                <text x="18" y="52" font-size="12" font-weight="400" fill="#1e3a8a">Termos de Auditoria aprovados por consenso colegiado em reunião técnica realizada em 02/09/2026.</text>
                <text x="18" y="74" font-size="12" font-weight="400" fill="#1e3a8a">Papel de trabalho homologado e vinculado aos autos do Processo TCE-RJ nº 303.389-0/25.</text>
                <text x="18" y="96" font-size="12" font-weight="600" fill="#0369a1">Ata de Reunião lavrada e subscrita digitalmente pelos integrantes da fiscalização.</text>
            </g>
        </g>
    </g>
''')

    # Fechamento do SVG
    svg_parts.append('</svg>\n')
    
    svg_content = "".join(svg_parts)
    with open(SVG_PATH, "w", encoding="utf-8") as f:
        f.write(svg_content)
    print(f"[OK] SVG gerado com sucesso em: {SVG_PATH}")

# -------------------------------------------------------------------------
# 2. CONVERSÃO DO SVG PARA PNG (VIA EDGE HEADLESS)
# -------------------------------------------------------------------------
def convert_svg_to_png():
    edge_exe = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
    if not os.path.exists(edge_exe):
        edge_exe = r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"
    
    if not os.path.exists(edge_exe):
        print("[AVISO] Executável do Microsoft Edge não encontrado para converter SVG em PNG.")
        return False
        
    # Cria arquivo HTML auxiliar com visualizador para screenshot limpo
    html_temp = os.path.join(WORK_DIR, "_temp_render.html")
    with open(html_temp, "w", encoding="utf-8") as f:
        f.write(f'''<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8"/>
<style>
    * {{ margin: 0; padding: 0; box-sizing: border-box; }}
    body {{ background: #f8fafc; width: 3200px; height: 3340px; overflow: hidden; }}
    img {{ width: 3200px; height: 3320px; display: block; }}
</style>
</head>
<body>
<img src="file:///{SVG_PATH.replace(chr(92), '/')}" />
</body>
</html>''')
    
    cmd = [
        edge_exe,
        "--headless",
        "--disable-gpu",
        "--hide-scrollbars",
        f"--window-size=3200,3340",
        f"--screenshot={PNG_PATH}",
        f"file:///{html_temp.replace(chr(92), '/')}"
    ]
    
    print("[INFO] Renderizando imagem PNG de alta resolução...")
    try:
        subprocess.run(cmd, timeout=20, check=True)
        if os.path.exists(PNG_PATH):
            print(f"[OK] PNG de alta resolução gerado com sucesso em: {PNG_PATH}")
            if os.path.exists(html_temp):
                os.remove(html_temp)
            return True
    except Exception as e:
        print(f"[ERRO] Falha ao renderizar PNG: {e}")
        if os.path.exists(html_temp):
            os.remove(html_temp)
    return False

# -------------------------------------------------------------------------
# 3. GERAÇÃO DA ATA DE REUNIÃO EM FORMATO DOCX
# -------------------------------------------------------------------------
def set_cell_border(cell, **kwargs):
    """
    Formata bordas individuais de células de tabela no python-docx.
    top, bottom, left, right: dict(sz=12, val='single', color='FF0000', space='0')
    """
    tcPr = cell._tc.get_or_add_tcPr()
    tcBorders = tcPr.first_child_found_in("w:tcBorders")
    if tcBorders is None:
        tcBorders = OxmlElement('w:tcBorders')
        tcPr.append(tcBorders)
    
    for edge in ('top', 'left', 'bottom', 'right', 'insideH', 'insideV'):
        edge_data = kwargs.get(edge)
        if edge_data:
            tag = 'w:{}'.format(edge)
            element = tcBorders.find(qn(tag))
            if element is None:
                element = OxmlElement(tag)
                tcBorders.append(element)
            for key in ["sz", "val", "color", "space"]:
                if key in edge_data:
                    element.set(qn('w:{}'.format(key)), str(edge_data[key]))

def set_cell_background(cell, fill_hex):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{fill_hex}"/>')
    tcPr.append(shd)

def set_cell_margins(cell, top=100, bottom=100, left=150, right=150):
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = parse_xml(f'''<w:tcMar {nsdecls("w")}>
        <w:top w:w="{top}" w:type="dxa"/>
        <w:bottom w:w="{bottom}" w:type="dxa"/>
        <w:left w:w="{left}" w:type="dxa"/>
        <w:right w:w="{right}" w:type="dxa"/>
    </w:tcMar>''')
    tcPr.append(tcMar)

def build_docx():
    doc = docx.Document()
    
    # Configuração de Página: A4 Retrato, Margens Padrão TCE-RJ (1.5 cm superior/laterais, 2.0 cm inferior)
    section = doc.sections[0]
    section.page_width = Cm(21.0)
    section.page_height = Cm(29.7)
    section.top_margin = Cm(1.5)
    section.bottom_margin = Cm(2.0)
    section.left_margin = Cm(1.8)
    section.right_margin = Cm(1.8)
    
    # ---------------------------------------------------------------------
    # CABEÇALHO DO DOCUMENTO (PADRÃO MATRIZ DE PLANEJAMENTO TCE-RJ)
    # ---------------------------------------------------------------------
    header = section.header
    # Remove parágrafos vazios iniciais do cabeçalho
    for p in header.paragraphs:
        p.text = ""
        
    htbl = header.add_table(rows=1, cols=3, width=Cm(17.4))
    htbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    htbl.autofit = False
    
    # Coluna 0: Logotipo TCE-RJ (Largura ~ 2.4 cm)
    c0 = htbl.cell(0, 0)
    c0.width = Cm(2.4)
    p0 = c0.paragraphs[0]
    p0.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p0.paragraph_format.space_after = Pt(0)
    p0.paragraph_format.space_before = Pt(0)
    run0 = p0.add_run()
    if os.path.exists(LOGO_PNG):
        run0.add_picture(LOGO_PNG, width=Cm(2.2))
    
    # Coluna 1: Estrutura Organizacional TCE-RJ (Largura ~ 6.6 cm)
    c1 = htbl.cell(0, 1)
    c1.width = Cm(6.6)
    p1 = c1.paragraphs[0]
    p1.paragraph_format.space_after = Pt(0)
    p1.paragraph_format.space_before = Pt(0)
    p1.paragraph_format.line_spacing = 1.05
    
    r1_1 = p1.add_run("SECRETARIA-GERAL DE CONTROLE EXTERNO\n")
    r1_1.font.name = "Arial"
    r1_1.font.size = Pt(7.5)
    r1_1.font.bold = True
    r1_1.font.color.rgb = RGBColor(15, 23, 42)
    
    r1_2 = p1.add_run("SUBSECRETARIA DE CONTROLE DE POLÍTICAS DE CIDADANIA\n")
    r1_2.font.name = "Arial"
    r1_2.font.size = Pt(7)
    r1_2.font.bold = False
    r1_2.font.color.rgb = RGBColor(51, 65, 85)
    
    r1_3 = p1.add_run("COORDENADORIA DE AUDITORIA DE POLÍTICAS EM TECNOLOGIA DA INFORMAÇÃO")
    r1_3.font.name = "Arial"
    r1_3.font.size = Pt(7)
    r1_3.font.bold = True
    r1_3.font.color.rgb = RGBColor(3, 105, 161)
    
    # Coluna 2: Dados da Fiscalização (Largura ~ 8.4 cm)
    c2 = htbl.cell(0, 2)
    c2.width = Cm(8.4)
    p2 = c2.paragraphs[0]
    p2.paragraph_format.space_after = Pt(0)
    p2.paragraph_format.space_before = Pt(0)
    p2.paragraph_format.line_spacing = 1.05
    
    r2_1 = p2.add_run("FISCALIZAÇÃO: 22/2026 | Processo PAAG nº 303.389-0/25\n")
    r2_1.font.name = "Arial"
    r2_1.font.size = Pt(7.5)
    r2_1.font.bold = True
    r2_1.font.color.rgb = RGBColor(15, 23, 42)
    
    r2_2 = p2.add_run("JURISDICIONADOS: 91 Prefeituras Municipais Fluminenses\n")
    r2_2.font.name = "Arial"
    r2_2.font.size = Pt(7)
    r2_2.font.bold = False
    r2_2.font.color.rgb = RGBColor(51, 65, 85)
    
    r2_3 = p2.add_run("OBJETIVO: Avaliar conformidade à LGPD e cumprimento do Proc. TCE-RJ nº 217.899-0/2024")
    r2_3.font.name = "Arial"
    r2_3.font.size = Pt(7)
    r2_3.font.bold = False
    r2_3.font.color.rgb = RGBColor(51, 65, 85)
    
    # Ajusta bordas do cabeçalho
    for cell in (c0, c1, c2):
        cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
        set_cell_border(cell, bottom=dict(sz=6, val='single', color='CBD5E1', space='0'))
        set_cell_margins(cell, top=60, bottom=80, left=60, right=60)
        
    # ---------------------------------------------------------------------
    # CORPO DO DOCUMENTO (ATA DE REUNIÃO)
    # ---------------------------------------------------------------------
    # Título Principal
    p_title = doc.add_paragraph()
    p_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_title.paragraph_format.space_before = Pt(12)
    p_title.paragraph_format.space_after = Pt(2)
    r_title = p_title.add_run("ATA DE REUNIÃO")
    r_title.font.name = "Arial"
    r_title.font.size = Pt(15)
    r_title.font.bold = True
    r_title.font.color.rgb = RGBColor(15, 23, 42)
    
    p_sub = doc.add_paragraph()
    p_sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_sub.paragraph_format.space_before = Pt(0)
    p_sub.paragraph_format.space_after = Pt(14)
    r_sub = p_sub.add_run("ELABORAÇÃO, CONSOLIDAÇÃO E APROVAÇÃO DOS TERMOS DE AUDITORIA\n(Papel de Trabalho: PT-PLA-01 | Fiscalização nº 22/2026)")
    r_sub.font.name = "Arial"
    r_sub.font.size = Pt(10.5)
    r_sub.font.bold = True
    r_sub.font.color.rgb = RGBColor(71, 85, 105)
    
    # Tabela 1: Metadados da Reunião (Identificação formal)
    meta_tbl = doc.add_table(rows=6, cols=2)
    meta_tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    meta_tbl.autofit = False
    
    meta_data = [
        ("Processo do PAAG:", "TCE-RJ nº 303.389-0/25 (Plano Anual de Auditoria Governamental de 2026)"),
        ("Processo de Referência:", "TCE-RJ nº 217.899-0/2024 (Acórdão nº 3931/2025 – Auditoria LGPD 2024)"),
        ("Assunto:", "Definição colegiada e aprovação dos Termos de Auditoria (Canvas Estratégico)"),
        ("Data e Horário:", "02 de setembro de 2026, das 10h00 às 12h30"),
        ("Local / Meio de Realização:", "Sala de Reuniões da CAD-TI / Presencial com suporte eletrônico colaborativo"),
        ("Participantes:", 
         "Bruno Mattos Souza de Souza Melo, Auditor de Controle Externo, mat. 02/004258 (Coordenador Setorial)\n"
         "João Paulo de Freitas Ramirez, Auditor de Controle Externo, mat. 02/004820\n"
         "Augusto Cesar Benvenuto de Almeida, Auditor de Controle Externo, mat. 02/004823\n"
         "Fabio Souza Lima, Auditor de Controle Externo, mat. 02/004822")
    ]
    
    for row_idx, (label, val) in enumerate(meta_data):
        row = meta_tbl.rows[row_idx]
        cell_lbl = row.cells[0]
        cell_lbl.width = Cm(4.5)
        set_cell_background(cell_lbl, "F1F5F9")
        p_lbl = cell_lbl.paragraphs[0]
        p_lbl.paragraph_format.space_after = Pt(2)
        p_lbl.paragraph_format.space_before = Pt(2)
        r_l = p_lbl.add_run(label)
        r_l.font.name = "Arial"
        r_l.font.size = Pt(9.5)
        r_l.font.bold = True
        r_l.font.color.rgb = RGBColor(15, 23, 42)
        
        cell_val = row.cells[1]
        cell_val.width = Cm(12.9)
        p_val = cell_val.paragraphs[0]
        p_val.paragraph_format.space_after = Pt(2)
        p_val.paragraph_format.space_before = Pt(2)
        r_v = p_val.add_run(val)
        r_v.font.name = "Arial"
        r_v.font.size = Pt(9.5)
        r_v.font.color.rgb = RGBColor(30, 41, 59)
        
        for c in (cell_lbl, cell_val):
            c.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
            set_cell_border(c, 
                            top=dict(sz=4, val='single', color='CBD5E1', space='0'),
                            bottom=dict(sz=4, val='single', color='CBD5E1', space='0'),
                            left=dict(sz=4, val='single', color='CBD5E1', space='0'),
                            right=dict(sz=4, val='single', color='CBD5E1', space='0'))
            set_cell_margins(c, top=80, bottom=80, left=100, right=100)

    # ---------------------------------------------------------------------
    # SEÇÃO 1: CONTEXTO E FINALIDADE DA REUNIÃO
    # ---------------------------------------------------------------------
    h1 = doc.add_paragraph()
    h1.paragraph_format.space_before = Pt(14)
    h1.paragraph_format.space_after = Pt(4)
    rh1 = h1.add_run("1. Contexto e Finalidade da Reunião")
    rh1.font.name = "Arial"
    rh1.font.size = Pt(12)
    rh1.font.bold = True
    rh1.font.color.rgb = RGBColor(15, 23, 42)
    
    p_ctx = doc.add_paragraph()
    p_ctx.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p_ctx.paragraph_format.line_spacing = 1.15
    p_ctx.paragraph_format.space_after = Pt(6)
    r_ctx = p_ctx.add_run(
        "No cumprimento do Plano Anual de Auditoria Governamental – PAAG de 2026, aprovado no Processo TCE-RJ nº 303.389-0/25, "
        "reuniu-se a Equipe de Auditoria designada no âmbito da Fiscalização nº 22/2026 (Auditoria de Conformidade em Proteção de "
        "Dados Pessoais – LGPD 2026.2), com a presença do Coordenador Setorial da CAD-TI, com o objetivo de discutir, pactuar e "
        "formalizar colegiadamente os elementos estruturantes do projeto de fiscalização, consubstanciados no instrumento "
        "metodológico denominado 'Termos de Auditoria'. O presente documento formaliza a participação e o consenso técnico "
        "da equipe de fiscalização na consolidação de todas as dimensões do planejamento da ação de controle externo."
    )
    r_ctx.font.name = "Arial"
    r_ctx.font.size = Pt(10)
    r_ctx.font.color.rgb = RGBColor(30, 41, 59)

    # ---------------------------------------------------------------------
    # SEÇÃO 2: TÓPICOS DISCUTIDOS E DELIBERAÇÕES TÉCNICAS
    # ---------------------------------------------------------------------
    h2 = doc.add_paragraph()
    h2.paragraph_format.space_before = Pt(12)
    h2.paragraph_format.space_after = Pt(4)
    rh2 = h2.add_run("2. Tópicos Discutidos e Deliberações da Equipe")
    rh2.font.name = "Arial"
    rh2.font.size = Pt(12)
    rh2.font.bold = True
    rh2.font.color.rgb = RGBColor(15, 23, 42)

    topicos = [
        ("2.1 Objeto da Fiscalização", 
         "Definiu-se que o objeto compreende as práticas correntes de proteção de dados pessoais adotadas pelas 91 prefeituras "
         "municipais jurisdicionadas do Estado do Rio de Janeiro, com foco preponderante no cumprimento das determinações e "
         "recomendações proferidas pelo Plenário no Processo TCE-RJ nº 217.899-0/2024 (Acórdão nº 3931/2025)."),
        
        ("2.2 Critérios de Auditoria", 
         "Foram pactuados como referenciais normativos e técnicos: (i) a Lei Federal nº 13.709/2018 (LGPD); (ii) o Acórdão nº 3931/2025 "
         "do TCE-RJ; (iii) resoluções, guias de segurança e orientações da Autoridade Nacional de Proteção de Dados (ANPD); (iv) normas "
         "ABNT NBR ISO/IEC 27001, 27002 e 27701; (v) planos de ação encaminhados pelos municípios; e (vi) o Programa de Privacidade "
         "e Segurança da Informação (PPSI) do Governo Federal."),

        ("2.3 Fontes de Evidência", 
         "Deliberou-se pelo exame documental e eletrônico de 13 tipologias probatórias, incluindo questionário eletrônico estruturado, "
         "documentos comprobatórios anexos, normativos formais municipais de privacidade e de segurança da informação, atos formais de "
         "designação de Encarregados (DPO), inventários e registros de tratamento (ROPA), relatórios de impacto (RIPD), fluxos de "
         "atendimento aos titulares, procedimentos de resposta a incidentes e evidências de ações de capacitação continuada."),

        ("2.4 Problema de Auditoria e Diagnóstico Histórico", 
         "A equipe contextualizou a trajetória da fiscalização: o diagnóstico incipiente de 2022; o trabalho conjunto com outros Tribunais "
         "de Contas em 2024 (que apontou evolução, mas persistência de inconformidades graves); e a necessidade premente de a unidade "
         "especializada (CAD-TI) reavaliar o grau de implementação das decisões e a conformidade municipal efetiva."),

        ("2.5 Mapeamento de Stakeholders", 
         "Foram mapeadas as partes interessadas internas (Plenário do TCE-RJ, SGE, DRC/Subsecretaria de Cidadania, Equipe Técnica e "
         "Ministério Público de Contas) e externas (Prefeitos Municipais, Controladorias Internas, Encarregados de Dados, Unidades de TI, "
         "ANPD e os Cidadãos/Titulares), delimitando suas expectativas e papéis na fiscalização."),

        ("2.6 Nível de Asseguração e Justificativa Metodológica", 
         "Restou formalmente fixado o nível de asseguração limitada, com fundamento nas normas NBASP/ISSAI 300 e 3000, justificado pela "
         "extensão simultânea de 91 prefeituras, metodologia fundamentada precipuamente em questionário eletrônico de autoavaliação e "
         "análise documental por amostragem, sem realização de perícias técnicas exaustivas in loco."),

        ("2.7 Objetivo Geral e Objetivos Específicos", 
         "Consolidou-se como objetivo primordial verificar o grau de conformidade das 91 prefeituras com os requisitos da LGPD, mensurar "
         "o cumprimento do Processo TCE-RJ nº 217.899-0/2024, confrontar com os dados de 2024 para mensurar a evolução municipal, "
         "identificar riscos residuais e formular propostas de encaminhamento corretivas e indutivas."),

        ("2.8 Delimitação Negativa (Não Escopo)", 
         "Ficaram expressamente excluídas do escopo: (i) avaliação exaustiva de todas as operações de tratamento municipais; (ii) avaliação "
         "de desempenho individual ou funcional do Encarregado; (iii) avaliação técnica operacional em profundidade dos controles de "
         "segurança da informação (ex.: pentests); (iv) conformidade integral de prestadores privados terceirizados; e (v) regularidade "
         "licitatória ou orçamentária de contratações de soluções de TI."),

        ("2.9 Escopo da Fiscalização e Itens Adicionais", 
         "O escopo abrange os 91 municípios em 9 dimensões de privacidade, acrescido de cálculo do índice iLGPD 2026, análise causal de "
         "descumprimentos de decisões anteriores, levantamento de contratações de consultorias/soluções LGPD, histórico de incidentes "
         "comunicados e elaboração de material didático de apoio."),

        ("2.10 Avaliação de Riscos da Fiscalização", 
         "Mapearam-se detalhadamente os riscos de auditoria em três categorias: (i) Riscos Inerentes (volume documental, transições de gestão, "
         "respostas autodeclaradas imprecisas); (ii) Riscos de Controle (falhas de padronização na análise, divergência de interpretação, "
         "falhas de revisão); e (iii) Riscos de Detecção (não identificação de divergências probatórias, aceitação de evidências insuficientes, "
         "erros de consolidação), estabelecendo-se as diretrizes mitigadoras de supervisão colegiada."),

        ("2.11 Cronograma e Marcos Formais de Entrega", 
         "Pactuou-se o cronograma com 10 marcos essenciais, com término do planejamento em 25/09/2026, fase de campo e recebimento de "
         "questionários até 23/10/2026, comentários do gestor até 16/11/2026 e entrega final do Relatório de Fiscalização em 27/11/2026."),

        ("2.12 Declaração de Ausências e Governança da Equipe", 
         "A equipe declarou formalmente a inexistência, nesta data, de ausências programadas que comprometam os trabalhos. Fixou-se a "
         "obrigatoriedade de registro de eventuais afastamentos supervenientes em papel de trabalho próprio, com detalhamento de integrante, "
         "período, tarefas afetadas, medidas de redistribuição e salvaguarda do cronograma institucional.")
    ]

    for subtitulo, texto in topicos:
        p_top = doc.add_paragraph()
        p_top.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        p_top.paragraph_format.line_spacing = 1.15
        p_top.paragraph_format.space_before = Pt(4)
        p_top.paragraph_format.space_after = Pt(4)
        
        r_st = p_top.add_run(f"• {subtitulo}: ")
        r_st.font.name = "Arial"
        r_st.font.size = Pt(9.5)
        r_st.font.bold = True
        r_st.font.color.rgb = RGBColor(15, 23, 42)
        
        r_tx = p_top.add_run(texto)
        r_tx.font.name = "Arial"
        r_tx.font.size = Pt(9.5)
        r_tx.font.color.rgb = RGBColor(51, 65, 85)

    # ---------------------------------------------------------------------
    # SEÇÃO 3: DELIBERAÇÕES FINAIS E ENCAMINHAMENTOS
    # ---------------------------------------------------------------------
    h3 = doc.add_paragraph()
    h3.paragraph_format.space_before = Pt(12)
    h3.paragraph_format.space_after = Pt(4)
    rh3 = h3.add_run("3. Deliberações Finais e Próximos Passos")
    rh3.font.name = "Arial"
    rh3.font.size = Pt(12)
    rh3.font.bold = True
    rh3.font.color.rgb = RGBColor(15, 23, 42)
    
    delib_text = (
        "Após ampla discussão técnica e consensual alinhamento metodológico entre os membros da equipe de fiscalização e a Coordenadoria "
        "Setorial, deliberou-se por:\n"
        "1. Aprovar integralmente e por unanimidade os Termos de Auditoria da Fiscalização nº 22/2026, na presente data de 02/09/2026;\n"
        "2. Consolidar as decisões no Painel Visual Estratégico (Canvas em SVG) e incorporá-lo como Anexo I integrante desta Ata;\n"
        "3. Dar início imediato aos trabalhos de elaboração da Matriz de Planejamento detalhada e à configuração do questionário eletrônico, "
        "observando rigorosamente os critérios e salvaguardas pactuados."
    )
    p_delib = doc.add_paragraph()
    p_delib.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p_delib.paragraph_format.line_spacing = 1.15
    p_delib.paragraph_format.space_after = Pt(10)
    r_del = p_delib.add_run(delib_text)
    r_del.font.name = "Arial"
    r_del.font.size = Pt(9.5)
    r_del.font.color.rgb = RGBColor(30, 41, 59)

    # ---------------------------------------------------------------------
    # SEÇÃO 4: ASSINATURAS DA EQUIPE DE AUDITORIA
    # ---------------------------------------------------------------------
    h4 = doc.add_paragraph()
    h4.paragraph_format.space_before = Pt(12)
    h4.paragraph_format.space_after = Pt(6)
    rh4 = h4.add_run("4. Assinaturas da Equipe de Fiscalização")
    rh4.font.name = "Arial"
    rh4.font.size = Pt(12)
    rh4.font.bold = True
    rh4.font.color.rgb = RGBColor(15, 23, 42)
    
    p_ass_desc = doc.add_paragraph()
    p_ass_desc.paragraph_format.space_after = Pt(12)
    r_ad = p_ass_desc.add_run("Nada mais havendo a tratar, lavrou-se a presente ata que, após lida e achada conforme, vai subscrita pelos participantes:")
    r_ad.font.name = "Arial"
    r_ad.font.size = Pt(9.5)
    r_ad.font.italic = True
    r_ad.font.color.rgb = RGBColor(71, 85, 105)
    
    # Tabela 2: Assinaturas (2 linhas x 2 colunas com traço superior)
    sig_tbl = doc.add_table(rows=2, cols=2)
    sig_tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    sig_tbl.autofit = False
    
    membros = [
        ("Bruno Mattos Souza de Souza Melo", "Auditor de Controle Externo | Matr. 02/004258", "Coordenador Setorial – CAD-TI"),
        ("João Paulo de Freitas Ramirez", "Auditor de Controle Externo | Matr. 02/004820", "Equipe de Auditoria"),
        ("Augusto Cesar Benvenuto de Almeida", "Auditor de Controle Externo | Matr. 02/004823", "Equipe de Auditoria"),
        ("Fabio Souza Lima", "Auditor de Controle Externo | Matr. 02/004822", "Equipe de Auditoria")
    ]
    
    for idx, (nome, matr, cargo) in enumerate(membros):
        r_idx = idx // 2
        c_idx = idx % 2
        cell = sig_tbl.cell(r_idx, c_idx)
        cell.width = Cm(8.7)
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_before = Pt(16)
        p.paragraph_format.space_after = Pt(14)
        p.paragraph_format.line_spacing = 1.1
        
        run_l = p.add_run("_________________________________________________\n")
        run_l.font.name = "Arial"
        run_l.font.size = Pt(8.5)
        run_l.font.color.rgb = RGBColor(148, 163, 184)
        
        run_n = p.add_run(f"{nome}\n")
        run_n.font.name = "Arial"
        run_n.font.size = Pt(9.5)
        run_n.font.bold = True
        run_n.font.color.rgb = RGBColor(15, 23, 42)
        
        run_m = p.add_run(f"{matr}\n")
        run_m.font.name = "Arial"
        run_m.font.size = Pt(8.5)
        run_m.font.color.rgb = RGBColor(71, 85, 105)
        
        run_c = p.add_run(f"{cargo}")
        run_c.font.name = "Arial"
        run_c.font.size = Pt(8.5)
        run_c.font.italic = True
        run_c.font.color.rgb = RGBColor(100, 116, 139)
        
        set_cell_margins(cell, top=60, bottom=60, left=40, right=40)

    # ---------------------------------------------------------------------
    # SEÇÃO 5: ANEXO I - CANVAS DOS TERMOS DE AUDITORIA
    # ---------------------------------------------------------------------
    doc.add_page_break()
    
    h_anx = doc.add_paragraph()
    h_anx.paragraph_format.space_before = Pt(8)
    h_anx.paragraph_format.space_after = Pt(2)
    rh_anx = h_anx.add_run("ANEXO I – PAINEL VISUAL DOS TERMOS DE AUDITORIA (CANVAS)")
    rh_anx.font.name = "Arial"
    rh_anx.font.size = Pt(12)
    rh_anx.font.bold = True
    rh_anx.font.color.rgb = RGBColor(15, 23, 42)
    
    p_anx_sub = doc.add_paragraph()
    p_anx_sub.paragraph_format.space_after = Pt(8)
    p_anx_sub.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    r_as = p_anx_sub.add_run(
        "O diagrama a seguir sintetiza visualmente a pactuação dos Termos de Auditoria da Fiscalização nº 22/2026, "
        "conforme elaborado colegiadamente pela Equipe de Fiscalização. O arquivo vetorial original de alta resolução "
        "encontra-se arquivado eletronicamente nos papéis de trabalho sob a denominação 'Termos de auditoria.svg'."
    )
    r_as.font.name = "Arial"
    r_as.font.size = Pt(9.5)
    r_as.font.color.rgb = RGBColor(71, 85, 105)
    
    # Adiciona a Imagem do Canvas
    if os.path.exists(PNG_PATH):
        p_img = doc.add_paragraph()
        p_img.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_img.paragraph_format.space_before = Pt(6)
        p_img.paragraph_format.space_after = Pt(6)
        r_img = p_img.add_run()
        # Largura máxima na página A4 com margem 1.8cm: ~17.2 cm
        r_img.add_picture(PNG_PATH, width=Cm(17.2))
        
        p_cap = doc.add_paragraph()
        p_cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_cap.paragraph_format.space_after = Pt(6)
        r_cap = p_cap.add_run("Figura 1: Canvas dos Termos de Auditoria da Fiscalização nº 22/2026 (CAD-TI / TCE-RJ).")
        r_cap.font.name = "Arial"
        r_cap.font.size = Pt(8.5)
        r_cap.font.italic = True
        r_cap.font.color.rgb = RGBColor(100, 116, 139)

    doc.save(DOCX_PATH)
    print(f"[OK] Documento DOCX gerado com sucesso em: {DOCX_PATH}")

# -------------------------------------------------------------------------
# EXECUÇÃO PRINCIPAL
# -------------------------------------------------------------------------
if __name__ == "__main__":
    print("==================================================================")
    print("GERAÇÃO DOS PAPÉIS DE TRABALHO: TERMOS DE AUDITORIA LGPD 2026.2")
    print("==================================================================")
    build_svg()
    convert_svg_to_png()
    build_docx()
    print("==================================================================")
    print("TODOS OS DOCUMENTOS FORAM CONCLUÍDOS E REGISTRADOS COM SUCESSO!")
    print("==================================================================")
