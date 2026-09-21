"""
Gera docs/relatorio_evolucao.pdf a partir de docs/relatorio_evolucao.md.

O enunciado pede o relatorio em PDF, ate 5 paginas. Manter a fonte em Markdown e
converter na hora da entrega evita o retrabalho de reeditar layout toda vez que
um numero do eval muda.

    pip install reportlab
    python docs/gerar_relatorio_pdf.py

O script avisa se passar de 5 paginas.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_JUSTIFY
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (KeepTogether, ListFlowable, ListItem,
                                Paragraph, SimpleDocTemplate, Spacer, Table,
                                TableStyle)

AQUI = Path(__file__).resolve().parent
ENTRADA = AQUI / "relatorio_evolucao.md"
SAIDA = AQUI / "relatorio_evolucao.pdf"

AZUL = colors.HexColor("#123A5E")
CINZA = colors.HexColor("#4A4A4A")
CINZA_CLARO = colors.HexColor("#EFEFEF")


def estilos() -> dict:
    base = getSampleStyleSheet()
    return {
        "h1": ParagraphStyle("h1", parent=base["Title"], fontSize=17, spaceAfter=4,
                             textColor=AZUL, alignment=0),
        "h2": ParagraphStyle("h2", parent=base["Heading2"], fontSize=12.5,
                             spaceBefore=11, spaceAfter=5, textColor=AZUL),
        "h3": ParagraphStyle("h3", parent=base["Heading3"], fontSize=10.5,
                             spaceBefore=8, spaceAfter=3, textColor=CINZA),
        "p": ParagraphStyle("p", parent=base["BodyText"], fontSize=8.7, leading=11.6,
                            alignment=TA_JUSTIFY, spaceAfter=4),
        "quote": ParagraphStyle("quote", parent=base["BodyText"], fontSize=8,
                                leading=10.6, leftIndent=9, textColor=CINZA,
                                borderPadding=3, spaceAfter=4),
        "celula": ParagraphStyle("celula", parent=base["BodyText"], fontSize=7.4,
                                 leading=9.2, spaceAfter=0),
        "celula_h": ParagraphStyle("celula_h", parent=base["BodyText"], fontSize=7.4,
                                   leading=9.2, spaceAfter=0,
                                   textColor=colors.white, fontName="Helvetica-Bold"),
        "code": ParagraphStyle("code", parent=base["BodyText"], fontName="Courier",
                               fontSize=7.3, leading=9, leftIndent=9,
                               backColor=CINZA_CLARO, borderPadding=4, spaceAfter=5),
    }


def inline(texto: str) -> str:
    """Markdown inline -> markup do ReportLab."""
    texto = texto.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    texto = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", texto)
    texto = re.sub(r"(?<!\w)\*(.+?)\*(?!\w)", r"<i>\1</i>", texto)
    texto = re.sub(r"`(.+?)`", r'<font face="Courier" size="7.8">\1</font>', texto)
    texto = re.sub(r"\[(.+?)\]\((.+?)\)", r'<link href="\2" color="blue">\1</link>', texto)
    return texto


def montar_tabela(linhas: list[str], st: dict, largura: float) -> Table:
    corpo = []
    for linha in linhas:
        if re.match(r"^\|[\s:\-|]+\|$", linha.strip()):
            continue
        celulas = [c.strip() for c in linha.strip().strip("|").split("|")]
        corpo.append(celulas)
    if not corpo:
        return None

    n = max(len(l) for l in corpo)
    corpo = [l + [""] * (n - len(l)) for l in corpo]

    dados = [[Paragraph(inline(c), st["celula_h"]) for c in corpo[0]]]
    dados += [[Paragraph(inline(c), st["celula"]) for c in linha] for linha in corpo[1:]]

    tabela = Table(dados, colWidths=[largura / n] * n, repeatRows=1, hAlign="LEFT")
    tabela.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), AZUL),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, CINZA_CLARO]),
        ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#BBBBBB")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 3.5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 3.5),
        ("TOPPADDING", (0, 0), (-1, -1), 2.5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5),
    ]))
    return tabela


def converter(markdown: str, st: dict, largura: float) -> list:
    story, linhas, i = [], markdown.splitlines(), 0

    while i < len(linhas):
        linha = linhas[i]
        strip = linha.strip()

        if not strip:
            i += 1
            continue

        if strip.startswith("```"):
            i += 1
            bloco = []
            while i < len(linhas) and not linhas[i].strip().startswith("```"):
                bloco.append(linhas[i].replace("&", "&amp;")
                             .replace("<", "&lt;").replace(">", "&gt;"))
                i += 1
            i += 1
            if bloco:
                story.append(Paragraph("<br/>".join(bloco), st["code"]))
            continue

        if strip.startswith("|"):
            bloco = []
            while i < len(linhas) and linhas[i].strip().startswith("|"):
                bloco.append(linhas[i])
                i += 1
            tabela = montar_tabela(bloco, st, largura)
            if tabela:
                story.append(Spacer(1, 3))
                story.append(tabela)
                story.append(Spacer(1, 6))
            continue

        if re.match(r"^-{3,}$", strip):
            i += 1
            continue

        if strip.startswith("> "):
            bloco = []
            while i < len(linhas) and linhas[i].strip().startswith(">"):
                bloco.append(linhas[i].strip().lstrip(">").strip())
                i += 1
            texto = " ".join(b for b in bloco if b)
            if texto:
                story.append(Paragraph(inline(texto), st["quote"]))
            continue

        if strip.startswith(("- ", "* ")):
            itens = []
            while i < len(linhas) and linhas[i].strip().startswith(("- ", "* ")):
                itens.append(ListItem(
                    Paragraph(inline(linhas[i].strip()[2:]), st["p"]), leftIndent=13))
                i += 1
            story.append(ListFlowable(itens, bulletType="bullet", start="circle",
                                      bulletFontSize=5, leftIndent=11))
            continue

        if strip.startswith("#"):
            nivel = len(strip) - len(strip.lstrip("#"))
            texto = inline(strip.lstrip("#").strip())
            chave = {1: "h1", 2: "h2"}.get(nivel, "h3")
            story.append(Paragraph(texto, st[chave]))
            i += 1
            continue

        # paragrafo
        bloco = []
        while i < len(linhas) and linhas[i].strip() and not linhas[i].strip().startswith(
                ("#", "|", ">", "- ", "* ", "```", "---")):
            bloco.append(linhas[i].strip())
            i += 1
        story.append(Paragraph(inline(" ".join(bloco)), st["p"]))

    return story


def rodape(canvas, doc) -> None:
    canvas.saveState()
    canvas.setFont("Helvetica", 6.8)
    canvas.setFillColor(CINZA)
    canvas.drawString(1.6 * cm, 1.0 * cm,
                      "ChargeGrid AI - Sprint 03 - EV Challenge 2026 - FIAP x GoodWe")
    canvas.drawRightString(A4[0] - 1.6 * cm, 1.0 * cm, f"pag. {doc.page}")
    canvas.setStrokeColor(colors.HexColor("#CCCCCC"))
    canvas.line(1.6 * cm, 1.3 * cm, A4[0] - 1.6 * cm, 1.3 * cm)
    canvas.restoreState()


def main() -> None:
    if not ENTRADA.exists():
        sys.exit(f"{ENTRADA} nao encontrado.")

    markdown = ENTRADA.read_text(encoding="utf-8")
    if "[preencher]" in markdown:
        n = markdown.count("[preencher]")
        print(f"AVISO: {n} celulas ainda estao como [preencher]. "
              "Rode evals/comparar.py antes da entrega final.")

    st = estilos()
    margem = 1.6 * cm
    largura = A4[0] - 2 * margem

    doc = SimpleDocTemplate(
        str(SAIDA), pagesize=A4,
        leftMargin=margem, rightMargin=margem,
        topMargin=1.4 * cm, bottomMargin=1.7 * cm,
        title="Relatorio de evolucao - ChargeGrid AI - Sprint 03",
        author="Equipe ChargeGrid AI - FIAP",
    )
    doc.build(converter(markdown, st, largura),
              onFirstPage=rodape, onLaterPages=rodape)

    try:
        from pypdf import PdfReader
        paginas = len(PdfReader(str(SAIDA)).pages)
        print(f"PDF gerado: {SAIDA} ({paginas} paginas)")
        if paginas > 5:
            print("ATENCAO: o limite do enunciado e 5 paginas. Corte conteudo "
                  "do .md e gere de novo.")
    except ImportError:
        print(f"PDF gerado: {SAIDA}")


if __name__ == "__main__":
    main()
