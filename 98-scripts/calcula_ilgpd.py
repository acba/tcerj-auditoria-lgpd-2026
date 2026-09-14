#!/usr/bin/env python3
"""Calcula o iLGPD 2026 a partir de exportacao CSV ou XLSX do LimeSurvey.

O programa usa a estrutura declarada em
``02-Execução/02-iLGPD/estrutura-ilgpd-2026.yaml`` e grava, por padrao,
os resultados e a memoria de calculo em ``02-Execução/02-iLGPD``.

Exemplos:

    python 98-scripts/calcula_ilgpd.py respostas.csv
    python 98-scripts/calcula_ilgpd.py respostas.xlsx --coluna-id firstname
    python 98-scripts/calcula_ilgpd.py --validar-config

Dependencia externa: PyYAML. A leitura de XLSX usa somente a biblioteca
padrao e considera a primeira planilha do arquivo.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import re
import statistics
import sys
import unicodedata
import zipfile
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable
from xml.etree import ElementTree as ET

try:
    import yaml
except ImportError as exc:  # pragma: no cover - depende do ambiente de execucao
    raise SystemExit(
        "Dependencia ausente: instale PyYAML (python -m pip install PyYAML)."
    ) from exc


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = ROOT / "02-Execução/02-iLGPD/estrutura-ilgpd-2026.yaml"
DEFAULT_OUTPUT_DIR = ROOT / "02-Execução/02-iLGPD"

PREPROCESSAMENTO_PADRAO = {
    "colunas_identificacao": [
        "firstname", "attribute_1", "municipio", "município", "orgao",
        "órgão", "auditado", "entidade", "id",
    ],
    "colunas_data": ["submitdate", "datestamp", "startdate"],
    "coluna_conclusao": "submitdate",
    "somente_respostas_concluidas": True,
    "deduplicar_por_identificador": True,
    "resposta_ausente_em_escala": "erro",
    "conflito_opcao_exclusiva": "erro",
    "valores_checkbox_marcado": ["Y", "y", "1", 1, True, "Sim", "sim", "Yes", "yes"],
    "valores_checkbox_nao_marcado": [
        "N", "n", "0", 0, False, "Nao", "Não", "nao", "não", "No", "no", "",
    ],
}

ARQUIVOS_RESULTADO = {
    "tabela": "resultados_ilgpd_2026.csv",
    "memoria": "memoria_calculo_ilgpd_2026.json",
    "resumo": "resumo_execucao_ilgpd_2026.json",
    "diagnosticos": "diagnosticos_ilgpd_2026.csv",
}

NS_MAIN = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
NS_REL_DOC = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
NS_REL_PKG = "http://schemas.openxmlformats.org/package/2006/relationships"


class ErroILGPD(Exception):
    """Erro controlado de configuracao, entrada ou calculo."""


def texto(valor: Any) -> str:
    """Converte valor tabular em texto sem artefatos de ponto flutuante."""
    if valor is None:
        return ""
    if isinstance(valor, bool):
        return "true" if valor else "false"
    if isinstance(valor, float):
        if math.isnan(valor):
            return ""
        if valor.is_integer():
            return str(int(valor))
    return str(valor).strip()


def canonico(valor: Any) -> str:
    """Normaliza caixa e acentos para comparacao de codigos simples."""
    bruto = unicodedata.normalize("NFKD", texto(valor).casefold())
    return "".join(ch for ch in bruto if not unicodedata.combining(ch)).strip()


def sha256(caminho: Path) -> str:
    digest = hashlib.sha256()
    with caminho.open("rb") as stream:
        for bloco in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(bloco)
    return digest.hexdigest()


def carregar_configuracao(caminho: Path) -> dict[str, Any]:
    """Carrega e valida as partes estruturais do YAML."""
    if not caminho.exists():
        raise ErroILGPD(f"Arquivo de metodologia nao encontrado: {caminho}")
    config = yaml.safe_load(caminho.read_text(encoding="utf-8"))
    if not isinstance(config, dict):
        raise ErroILGPD("O arquivo YAML deve conter um objeto na raiz.")

    obrigatorios = {"metadata", "dimensoes", "agregados", "niveis_maturidade"}
    faltantes = obrigatorios - set(config)
    if faltantes:
        raise ErroILGPD(f"Secoes ausentes no YAML: {sorted(faltantes)}")

    raiz = config["metadata"].get("raiz")
    if raiz not in config["agregados"]:
        raise ErroILGPD(f"A raiz {raiz!r} nao esta declarada em agregados.")

    for dimensao_id, spec in config["dimensoes"].items():
        tipo = spec.get("tipo")
        if tipo == "escala":
            if not spec.get("coluna") or not spec.get("valores"):
                raise ErroILGPD(f"Dimensao de escala invalida: {dimensao_id}")
            validar_valores_escala(dimensao_id, spec["valores"])
        elif tipo == "media_binaria":
            if not spec.get("componentes") or not spec.get("opcao_exclusiva_negativa"):
                raise ErroILGPD(f"Dimensao binaria invalida: {dimensao_id}")
        elif tipo == "media_ponderada_escalas":
            componentes = spec.get("componentes") or []
            if not componentes:
                raise ErroILGPD(f"Dimensao composta invalida: {dimensao_id}")
            for componente in componentes:
                if not componente.get("coluna") or float(componente.get("peso", 0)) <= 0:
                    raise ErroILGPD(f"Componente invalido em {dimensao_id}: {componente}")
                validar_valores_escala(dimensao_id, componente.get("valores"))
        else:
            raise ErroILGPD(f"Tipo desconhecido em {dimensao_id}: {tipo!r}")

    nos = set(config["dimensoes"]) | set(config["agregados"])
    for agregado_id, spec in config["agregados"].items():
        componentes = spec.get("componentes") or []
        if not componentes:
            raise ErroILGPD(f"Agregado sem componentes: {agregado_id}")
        for componente in componentes:
            if componente.get("id") not in nos:
                raise ErroILGPD(
                    f"Componente inexistente em {agregado_id}: {componente.get('id')}"
                )
            if float(componente.get("peso", 0)) <= 0:
                raise ErroILGPD(f"Peso nao positivo em {agregado_id}: {componente}")

    validar_ausencia_ciclos(config)
    validar_niveis(config["niveis_maturidade"])
    return config


def validar_valores_escala(nome: str, valores: Any) -> None:
    if not isinstance(valores, dict) or not valores:
        raise ErroILGPD(f"Escala vazia ou invalida em {nome}")
    for codigo, valor in valores.items():
        if not isinstance(valor, (int, float)) or not 0 <= float(valor) <= 1:
            raise ErroILGPD(f"Valor invalido em {nome}, codigo {codigo}: {valor}")


def validar_ausencia_ciclos(config: dict[str, Any]) -> None:
    agregados = config["agregados"]
    visitados: set[str] = set()
    pilha: set[str] = set()

    def visitar(no: str) -> None:
        if no in visitados or no not in agregados:
            return
        if no in pilha:
            raise ErroILGPD(f"Ciclo detectado na arvore de calculo: {no}")
        pilha.add(no)
        for componente in agregados[no]["componentes"]:
            visitar(str(componente["id"]))
        pilha.remove(no)
        visitados.add(no)

    visitar(str(config["metadata"]["raiz"]))


def validar_niveis(niveis: list[dict[str, Any]]) -> None:
    if not isinstance(niveis, list) or not niveis:
        raise ErroILGPD("niveis_maturidade deve ser uma lista nao vazia.")
    ordenados = sorted(niveis, key=lambda item: float(item["min"]))
    cursor = float(ordenados[0]["min"])
    if not math.isclose(cursor, 0.0):
        raise ErroILGPD("A classificacao de maturidade deve iniciar em zero.")
    for nivel in ordenados:
        minimo = float(nivel["min"])
        maximo = float(nivel["max"])
        if not math.isclose(minimo, cursor) or maximo <= minimo:
            raise ErroILGPD("Ha lacuna ou sobreposicao nos niveis de maturidade.")
        cursor = maximo
    if not math.isclose(cursor, 1.0):
        raise ErroILGPD("A classificacao de maturidade deve terminar em um.")


def coluna_excel_para_indice(referencia: str) -> int:
    letras = re.match(r"[A-Z]+", referencia.upper())
    if not letras:
        raise ErroILGPD(f"Referencia de celula XLSX invalida: {referencia}")
    indice = 0
    for letra in letras.group(0):
        indice = indice * 26 + ord(letra) - ord("A") + 1
    return indice - 1


def primeira_planilha_xlsx(arquivo: zipfile.ZipFile) -> str:
    """Resolve o caminho XML da primeira planilha declarada no workbook."""
    workbook = ET.fromstring(arquivo.read("xl/workbook.xml"))
    primeira = workbook.find(f".//{{{NS_MAIN}}}sheets/{{{NS_MAIN}}}sheet")
    if primeira is None:
        raise ErroILGPD("O XLSX nao contem planilhas.")
    rel_id = primeira.get(f"{{{NS_REL_DOC}}}id")
    rels = ET.fromstring(arquivo.read("xl/_rels/workbook.xml.rels"))
    for rel in rels.findall(f"{{{NS_REL_PKG}}}Relationship"):
        if rel.get("Id") == rel_id:
            alvo = rel.get("Target", "worksheets/sheet1.xml").lstrip("/")
            if alvo.startswith("xl/"):
                return alvo
            partes: list[str] = []
            for parte in ("xl/" + alvo).split("/"):
                if parte == "..":
                    if partes:
                        partes.pop()
                elif parte not in {"", "."}:
                    partes.append(parte)
            return "/".join(partes)
    return "xl/worksheets/sheet1.xml"


def ler_xlsx(caminho: Path) -> list[dict[str, str]]:
    """Le a primeira planilha de um XLSX sem pandas ou openpyxl."""
    with zipfile.ZipFile(caminho) as arquivo:
        compartilhadas: list[str] = []
        if "xl/sharedStrings.xml" in arquivo.namelist():
            raiz_strings = ET.fromstring(arquivo.read("xl/sharedStrings.xml"))
            compartilhadas = [
                "".join(no.text or "" for no in item.iter(f"{{{NS_MAIN}}}t"))
                for item in raiz_strings.findall(f"{{{NS_MAIN}}}si")
            ]

        planilha = ET.fromstring(arquivo.read(primeira_planilha_xlsx(arquivo)))
        linhas_xml = planilha.findall(
            f".//{{{NS_MAIN}}}sheetData/{{{NS_MAIN}}}row"
        )
        linhas: list[list[str]] = []
        maior_coluna = -1
        for linha_xml in linhas_xml:
            celulas: dict[int, str] = {}
            for celula in linha_xml.findall(f"{{{NS_MAIN}}}c"):
                referencia = celula.get("r", "")
                indice = coluna_excel_para_indice(referencia)
                maior_coluna = max(maior_coluna, indice)
                tipo = celula.get("t", "")
                valor_no = celula.find(f"{{{NS_MAIN}}}v")
                valor = "" if valor_no is None else valor_no.text or ""
                if tipo == "s" and valor:
                    valor = compartilhadas[int(valor)]
                elif tipo == "inlineStr":
                    valor = "".join(
                        no.text or "" for no in celula.iter(f"{{{NS_MAIN}}}t")
                    )
                elif tipo == "b":
                    valor = "true" if valor == "1" else "false"
                celulas[indice] = valor
            if celulas:
                linhas.append([celulas.get(i, "") for i in range(maior_coluna + 1)])

    if not linhas:
        return []
    largura = max(len(linha) for linha in linhas)
    linhas = [linha + [""] * (largura - len(linha)) for linha in linhas]
    cabecalho = [texto(valor).lstrip("\ufeff") for valor in linhas[0]]
    if len(cabecalho) != len(set(cabecalho)):
        raise ErroILGPD("O XLSX possui nomes de coluna duplicados.")
    return [dict(zip(cabecalho, linha)) for linha in linhas[1:] if any(linha)]


def ler_csv(caminho: Path) -> list[dict[str, str]]:
    """Le CSV com autodeteccao de delimitador e suporte a campos multilinha."""
    amostra = caminho.read_text(encoding="utf-8-sig", errors="strict")[:65536]
    try:
        dialeto = csv.Sniffer().sniff(amostra, delimiters=",;\t|")
    except csv.Error:
        dialeto = csv.excel
    with caminho.open("r", encoding="utf-8-sig", newline="") as stream:
        leitor = csv.DictReader(stream, dialect=dialeto)
        if not leitor.fieldnames:
            return []
        campos = [texto(campo).lstrip("\ufeff") for campo in leitor.fieldnames]
        if len(campos) != len(set(campos)):
            raise ErroILGPD("O CSV possui nomes de coluna duplicados.")
        registros = []
        for linha in leitor:
            registros.append(
                {campos[i]: texto(linha.get(leitor.fieldnames[i], "")) for i in range(len(campos))}
            )
        return registros


def ler_respostas(caminho: Path) -> list[dict[str, str]]:
    if not caminho.exists():
        raise ErroILGPD(f"Arquivo de respostas nao encontrado: {caminho}")
    extensao = caminho.suffix.lower()
    if extensao == ".csv":
        return ler_csv(caminho)
    if extensao == ".xlsx":
        return ler_xlsx(caminho)
    raise ErroILGPD("Formato de entrada nao suportado. Use CSV ou XLSX.")


def mapa_colunas(registros: list[dict[str, Any]]) -> dict[str, str]:
    if not registros:
        return {}
    resultado: dict[str, str] = {}
    for coluna in registros[0]:
        chave = canonico(coluna)
        if chave in resultado:
            raise ErroILGPD(f"Colunas equivalentes apos normalizacao: {coluna}")
        resultado[chave] = coluna
    return resultado


def resolver_coluna(nome: str, colunas: dict[str, str]) -> str | None:
    return colunas.get(canonico(nome))


def colunas_exigidas(config: dict[str, Any]) -> set[str]:
    exigidas: set[str] = set()
    for spec in config["dimensoes"].values():
        if spec["tipo"] == "escala":
            exigidas.add(str(spec["coluna"]))
        elif spec["tipo"] == "media_binaria":
            exigidas.update(str(item) for item in spec["componentes"])
            exigidas.add(str(spec["opcao_exclusiva_negativa"]))
        elif spec["tipo"] == "media_ponderada_escalas":
            exigidas.update(str(item["coluna"]) for item in spec["componentes"])
    return exigidas


def escolher_coluna_id(
    colunas: dict[str, str], solicitada: str | None
) -> str:
    candidatos = [solicitada] if solicitada else PREPROCESSAMENTO_PADRAO["colunas_identificacao"]
    for candidato in candidatos:
        if candidato and resolver_coluna(str(candidato), colunas):
            return resolver_coluna(str(candidato), colunas) or ""
    raise ErroILGPD(
        "Nao foi encontrada coluna de identificacao. Informe --coluna-id."
    )


def chave_temporal(valor: Any) -> tuple[int, Any]:
    bruto = texto(valor)
    if not bruto:
        return (0, "")
    try:
        return (2, float(bruto))
    except ValueError:
        pass
    normalizado = bruto.replace("Z", "+00:00")
    try:
        return (3, datetime.fromisoformat(normalizado).timestamp())
    except ValueError:
        return (1, bruto)


def preparar_registros(
    registros: list[dict[str, str]],
    config: dict[str, Any],
    coluna_id_solicitada: str | None,
    incluir_incompletas: bool,
    sem_deduplicar: bool,
) -> tuple[list[dict[str, Any]], str, list[dict[str, str]], dict[str, int]]:
    if not registros:
        raise ErroILGPD("O arquivo de respostas esta vazio.")
    colunas = mapa_colunas(registros)
    coluna_id = escolher_coluna_id(colunas, coluna_id_solicitada)
    preprocessamento = PREPROCESSAMENTO_PADRAO
    diagnosticos: list[dict[str, str]] = []
    contagens = {"lidos": len(registros), "incompletos_excluidos": 0, "duplicados_excluidos": 0}

    coluna_conclusao = resolver_coluna(
        str(preprocessamento.get("coluna_conclusao", "submitdate")), colunas
    )
    somente_concluidas = bool(preprocessamento.get("somente_respostas_concluidas", True))
    filtrados: list[dict[str, Any]] = []
    for numero, registro in enumerate(registros, start=2):
        identificador = texto(registro.get(coluna_id)) or f"Registro {numero - 1}"
        if somente_concluidas and not incluir_incompletas and coluna_conclusao:
            if not texto(registro.get(coluna_conclusao)):
                contagens["incompletos_excluidos"] += 1
                continue
        filtrados.append({"id": identificador, "linha": numero, "dados": registro})

    if somente_concluidas and not incluir_incompletas and not coluna_conclusao:
        diagnosticos.append(
            {
                "nivel": "AVISO",
                "registro": "",
                "codigo": "COLUNA_CONCLUSAO_AUSENTE",
                "mensagem": "A coluna submitdate nao existe; nenhum registro foi filtrado por conclusao.",
            }
        )

    deduplicar = bool(preprocessamento.get("deduplicar_por_identificador", True))
    if deduplicar and not sem_deduplicar:
        coluna_data = next(
            (
                resolver_coluna(str(nome), colunas)
                for nome in preprocessamento.get("colunas_data", [])
                if resolver_coluna(str(nome), colunas)
            ),
            None,
        )
        por_id: dict[str, dict[str, Any]] = {}
        for item in filtrados:
            chave = canonico(item["id"])
            anterior = por_id.get(chave)
            if anterior is None:
                por_id[chave] = item
                continue
            contagens["duplicados_excluidos"] += 1
            if coluna_data:
                atual_data = chave_temporal(item["dados"].get(coluna_data))
                anterior_data = chave_temporal(anterior["dados"].get(coluna_data))
                if atual_data >= anterior_data:
                    por_id[chave] = item
            else:
                por_id[chave] = item
        filtrados = list(por_id.values())

    contagens["processados"] = len(filtrados)
    if not filtrados:
        raise ErroILGPD("Nenhuma resposta concluida permaneceu para calculo.")
    return filtrados, coluna_id, diagnosticos, contagens


def normalizar_escala(escala: dict[str, Any]) -> dict[str, float]:
    return {canonico(codigo): float(valor) for codigo, valor in escala.items()}


def pontuar_checkbox(valor: Any, preprocessamento: dict[str, Any]) -> int:
    marcado = {canonico(item) for item in preprocessamento["valores_checkbox_marcado"]}
    nao_marcado = {
        canonico(item) for item in preprocessamento["valores_checkbox_nao_marcado"]
    }
    chave = canonico(valor)
    if chave in marcado:
        return 1
    if chave in nao_marcado:
        return 0
    raise ErroILGPD(f"Valor de checkbox nao reconhecido: {texto(valor)!r}")


def valor_coluna(registro: dict[str, Any], nome: str, colunas: dict[str, str]) -> Any:
    coluna_real = resolver_coluna(nome, colunas)
    if not coluna_real:
        raise ErroILGPD(f"Coluna obrigatoria ausente: {nome}")
    return registro.get(coluna_real, "")


def calcular_dimensoes(
    item: dict[str, Any],
    config: dict[str, Any],
    colunas: dict[str, str],
    modo_ausentes: str,
) -> tuple[dict[str, float], dict[str, Any], list[dict[str, str]]]:
    registro = item["dados"]
    identificador = item["id"]
    valores: dict[str, float] = {}
    memoria: dict[str, Any] = {}
    diagnosticos: list[dict[str, str]] = []
    preprocessamento = PREPROCESSAMENTO_PADRAO

    for dimensao_id, spec in config["dimensoes"].items():
        if spec["tipo"] == "escala":
            bruto = valor_coluna(registro, str(spec["coluna"]), colunas)
            chave = canonico(bruto)
            escala = normalizar_escala(spec["valores"])
            if not chave:
                if modo_ausentes == "erro":
                    raise ErroILGPD(
                        f"{identificador}: resposta ausente em {spec['coluna']}"
                    )
                score = 0.0
                diagnosticos.append(
                    {
                        "nivel": "AVISO",
                        "registro": identificador,
                        "codigo": "RESPOSTA_AUSENTE_ZERO",
                        "mensagem": f"{spec['coluna']} ausente; pontuacao zero aplicada.",
                    }
                )
            elif chave not in escala:
                raise ErroILGPD(
                    f"{identificador}: codigo {texto(bruto)!r} nao reconhecido em {spec['coluna']}"
                )
            else:
                score = escala[chave]
            valores[dimensao_id] = score
            memoria[dimensao_id] = {
                "tipo": "escala",
                "coluna": spec["coluna"],
                "codigo_resposta": texto(bruto),
                "valor": score,
            }
            continue

        if spec["tipo"] == "media_ponderada_escalas":
            partes: list[dict[str, Any]] = []
            soma_pesos = 0.0
            soma_produtos = 0.0
            for componente in spec["componentes"]:
                coluna = str(componente["coluna"])
                bruto = valor_coluna(registro, coluna, colunas)
                chave = canonico(bruto)
                escala = normalizar_escala(componente["valores"])
                if not chave:
                    if modo_ausentes == "erro":
                        raise ErroILGPD(f"{identificador}: resposta ausente em {coluna}")
                    score_item = 0.0
                    diagnosticos.append(
                        {
                            "nivel": "AVISO",
                            "registro": identificador,
                            "codigo": "RESPOSTA_AUSENTE_ZERO",
                            "mensagem": f"{coluna} ausente; pontuacao zero aplicada.",
                        }
                    )
                elif chave not in escala:
                    raise ErroILGPD(
                        f"{identificador}: codigo {texto(bruto)!r} nao reconhecido em {coluna}"
                    )
                else:
                    score_item = escala[chave]
                peso = float(componente["peso"])
                soma_pesos += peso
                soma_produtos += score_item * peso
                partes.append(
                    {
                        "coluna": coluna,
                        "codigo_resposta": texto(bruto),
                        "peso": peso,
                        "valor": score_item,
                        "produto": score_item * peso,
                    }
                )
            score = soma_produtos / soma_pesos
            valores[dimensao_id] = score
            memoria[dimensao_id] = {
                "tipo": "media_ponderada_escalas",
                "componentes": partes,
                "soma_pesos": soma_pesos,
                "valor": score,
            }
            continue

        componentes: list[dict[str, Any]] = []
        for coluna in spec["componentes"]:
            bruto = valor_coluna(registro, str(coluna), colunas)
            valor = pontuar_checkbox(bruto, preprocessamento)
            componentes.append(
                {"coluna": str(coluna), "resposta": texto(bruto), "valor": valor}
            )
        coluna_exclusiva = str(spec["opcao_exclusiva_negativa"])
        bruto_exclusiva = valor_coluna(registro, coluna_exclusiva, colunas)
        exclusiva = pontuar_checkbox(bruto_exclusiva, preprocessamento)
        positivos = sum(comp["valor"] for comp in componentes)
        if exclusiva and positivos:
            politica = preprocessamento.get("conflito_opcao_exclusiva", "erro")
            mensagem = (
                f"{identificador}: {coluna_exclusiva} foi marcada juntamente com "
                f"{positivos} opcao(oes) positiva(s)."
            )
            if politica == "erro":
                raise ErroILGPD(mensagem)
            diagnosticos.append(
                {
                    "nivel": "AVISO",
                    "registro": identificador,
                    "codigo": "CONFLITO_OPCAO_EXCLUSIVA",
                    "mensagem": mensagem,
                }
            )
        score = 0.0 if exclusiva else positivos / len(componentes)
        valores[dimensao_id] = score
        memoria[dimensao_id] = {
            "tipo": "media_binaria",
            "componentes": componentes,
            "opcao_exclusiva": {
                "coluna": coluna_exclusiva,
                "resposta": texto(bruto_exclusiva),
                "valor": exclusiva,
            },
            "valor": score,
        }
    return valores, memoria, diagnosticos


def calcular_agregados(
    valores: dict[str, float], memoria: dict[str, Any], config: dict[str, Any]
) -> None:
    agregados = config["agregados"]
    visitando: set[str] = set()

    def visitar(no: str) -> float:
        if no in valores:
            return valores[no]
        if no in visitando:
            raise ErroILGPD(f"Ciclo detectado durante o calculo: {no}")
        if no not in agregados:
            raise ErroILGPD(f"No de calculo inexistente: {no}")
        visitando.add(no)
        partes: list[dict[str, float | str]] = []
        soma_pesos = 0.0
        soma_ponderada = 0.0
        for componente in agregados[no]["componentes"]:
            componente_id = str(componente["id"])
            peso = float(componente["peso"])
            valor = visitar(componente_id)
            soma_pesos += peso
            soma_ponderada += valor * peso
            partes.append(
                {
                    "id": componente_id,
                    "peso": peso,
                    "valor": valor,
                    "produto": valor * peso,
                }
            )
        if soma_pesos <= 0:
            raise ErroILGPD(f"Soma de pesos invalida em {no}")
        resultado = min(1.0, max(0.0, soma_ponderada / soma_pesos))
        valores[no] = resultado
        memoria[no] = {
            "tipo": "media_ponderada",
            "soma_pesos": soma_pesos,
            "soma_produtos": soma_ponderada,
            "componentes": partes,
            "valor": resultado,
        }
        visitando.remove(no)
        return resultado

    visitar(str(config["metadata"]["raiz"]))
    for agregado in agregados:
        visitar(str(agregado))


def classificar(valor: float, niveis: list[dict[str, Any]]) -> str:
    for nivel in niveis:
        minimo = float(nivel["min"])
        maximo = float(nivel["max"])
        min_ok = valor >= minimo if nivel.get("inclui_min", True) else valor > minimo
        max_ok = valor <= maximo if nivel.get("inclui_max", False) else valor < maximo
        if min_ok and max_ok:
            return str(nivel["nome"])
    raise ErroILGPD(f"Valor fora dos niveis de maturidade: {valor}")


def ranking_denso(resultados: list[dict[str, Any]], raiz: str) -> None:
    valores_unicos = sorted({item["valores"][raiz] for item in resultados}, reverse=True)
    posicoes = {valor: indice + 1 for indice, valor in enumerate(valores_unicos)}
    for item in resultados:
        item["posicao"] = posicoes[item["valores"][raiz]]


def calcular(
    registros: list[dict[str, Any]],
    config: dict[str, Any],
    colunas: dict[str, str],
    modo_ausentes: str,
) -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    raiz = str(config["metadata"]["raiz"])
    resultados: list[dict[str, Any]] = []
    diagnosticos: list[dict[str, str]] = []
    for item in registros:
        valores, memoria, avisos = calcular_dimensoes(
            item, config, colunas, modo_ausentes
        )
        calcular_agregados(valores, memoria, config)
        diagnosticos.extend(avisos)
        resultados.append(
            {
                "id": item["id"],
                "linha_origem": item["linha"],
                "valores": valores,
                "maturidade": classificar(valores[raiz], config["niveis_maturidade"]),
                "memoria": memoria,
            }
        )
    ranking_denso(resultados, raiz)
    resultados.sort(key=lambda item: (item["posicao"], canonico(item["id"])))
    return resultados, diagnosticos


def gravar_csv(
    caminho: Path,
    resultados: list[dict[str, Any]],
    config: dict[str, Any],
) -> None:
    raiz = str(config["metadata"]["raiz"])
    ordem = [*config["dimensoes"].keys(), raiz]
    casas = 6
    campos = ["id", *ordem, "maturidade", "posicao", "linha_origem"]
    with caminho.open("w", encoding="utf-8", newline="") as stream:
        escritor = csv.DictWriter(stream, fieldnames=campos)
        escritor.writeheader()
        for item in resultados:
            linha: dict[str, Any] = {
                "id": item["id"],
                "maturidade": item["maturidade"],
                "posicao": item["posicao"],
                "linha_origem": item["linha_origem"],
            }
            linha.update(
                {indicador: f"{item['valores'][indicador]:.{casas}f}" for indicador in ordem}
            )
            escritor.writerow(linha)


def gravar_diagnosticos(caminho: Path, diagnosticos: list[dict[str, str]]) -> None:
    campos = ["nivel", "registro", "codigo", "mensagem"]
    with caminho.open("w", encoding="utf-8", newline="") as stream:
        escritor = csv.DictWriter(stream, fieldnames=campos)
        escritor.writeheader()
        escritor.writerows(diagnosticos)


def gravar_json(caminho: Path, conteudo: Any) -> None:
    caminho.write_text(
        json.dumps(conteudo, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def mediana(valores: Iterable[float]) -> float:
    serie = list(valores)
    return float(statistics.median(serie)) if serie else 0.0


def executar(args: argparse.Namespace) -> dict[str, Any]:
    config = carregar_configuracao(args.config)
    if args.validar_config:
        return {
            "valido": True,
            "configuracao": str(args.config),
            "raiz": config["metadata"]["raiz"],
            "dimensoes": len(config["dimensoes"]),
            "agregados": len(config["agregados"]),
        }
    if args.respostas is None:
        raise ErroILGPD("Informe o arquivo de respostas ou use --validar-config.")

    dados = ler_respostas(args.respostas)
    colunas = mapa_colunas(dados)
    ausentes = sorted(
        coluna for coluna in colunas_exigidas(config) if not resolver_coluna(coluna, colunas)
    )
    if ausentes:
        raise ErroILGPD(f"Colunas obrigatorias ausentes: {ausentes}")

    preparados, coluna_id, diagnosticos, contagens = preparar_registros(
        dados,
        config,
        args.coluna_id,
        args.incluir_incompletas,
        args.sem_deduplicar,
    )
    modo_ausentes = args.modo_ausentes or str(
        PREPROCESSAMENTO_PADRAO["resposta_ausente_em_escala"]
    )
    if modo_ausentes not in {"erro", "zero"}:
        raise ErroILGPD("O modo de ausentes deve ser 'erro' ou 'zero'.")
    resultados, avisos_calculo = calcular(
        preparados, config, colunas, modo_ausentes
    )
    diagnosticos.extend(avisos_calculo)

    saida = args.saida_dir
    saida.mkdir(parents=True, exist_ok=True)
    nomes = ARQUIVOS_RESULTADO
    caminho_tabela = saida / nomes["tabela"]
    caminho_memoria = saida / nomes["memoria"]
    caminho_resumo = saida / nomes["resumo"]
    caminho_diagnosticos = saida / nomes["diagnosticos"]

    gravar_csv(caminho_tabela, resultados, config)
    gravar_diagnosticos(caminho_diagnosticos, diagnosticos)
    gravar_json(
        caminho_memoria,
        {
            "metodologia": config["metadata"],
            "registros": [
                {
                    "id": item["id"],
                    "linha_origem": item["linha_origem"],
                    "posicao": item["posicao"],
                    "maturidade": item["maturidade"],
                    "valores": item["valores"],
                    "memoria": item["memoria"],
                }
                for item in resultados
            ],
        },
    )

    raiz = str(config["metadata"]["raiz"])
    valores_raiz = [item["valores"][raiz] for item in resultados]
    resumo = {
        "execucao_utc": datetime.now(timezone.utc).isoformat(),
        "arquivo_respostas": str(args.respostas.resolve()),
        "sha256_respostas": sha256(args.respostas),
        "arquivo_metodologia": str(args.config.resolve()),
        "sha256_metodologia": sha256(args.config),
        "coluna_identificacao": coluna_id,
        "modo_ausentes": modo_ausentes,
        "contagens": contagens,
        "diagnosticos": len(diagnosticos),
        "indice": {
            "nome": raiz,
            "media": statistics.fmean(valores_raiz),
            "mediana": mediana(valores_raiz),
            "minimo": min(valores_raiz),
            "maximo": max(valores_raiz),
            "distribuicao_maturidade": dict(
                sorted(Counter(item["maturidade"] for item in resultados).items())
            ),
        },
        "arquivos_gerados": [
            str(caminho_tabela),
            str(caminho_memoria),
            str(caminho_resumo),
            str(caminho_diagnosticos),
        ],
    }
    gravar_json(caminho_resumo, resumo)
    return resumo


def construir_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "respostas",
        nargs="?",
        type=Path,
        help="Exportacao CSV ou XLSX do LimeSurvey com respostas codificadas.",
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=DEFAULT_CONFIG,
        help=f"Estrutura YAML do iLGPD (padrao: {DEFAULT_CONFIG}).",
    )
    parser.add_argument(
        "--saida-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help=f"Diretorio dos resultados (padrao: {DEFAULT_OUTPUT_DIR}).",
    )
    parser.add_argument(
        "--coluna-id",
        default=None,
        help="Coluna que identifica a prefeitura; por padrao, deteccao automatica.",
    )
    parser.add_argument(
        "--modo-ausentes",
        choices=["erro", "zero"],
        default=None,
        help="Sobrescreve o tratamento padrao de respostas ausentes do programa.",
    )
    parser.add_argument(
        "--incluir-incompletas",
        action="store_true",
        help="Inclui registros sem submitdate, quando essa coluna existir.",
    )
    parser.add_argument(
        "--sem-deduplicar",
        action="store_true",
        help="Nao remove envios anteriores do mesmo identificador.",
    )
    parser.add_argument(
        "--validar-config",
        action="store_true",
        help="Valida o YAML e encerra sem exigir planilha de respostas.",
    )
    return parser


def main() -> int:
    parser = construir_parser()
    args = parser.parse_args()
    try:
        resultado = executar(args)
    except (ErroILGPD, OSError, zipfile.BadZipFile, ET.ParseError) as exc:
        print(f"ERRO: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(resultado, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
