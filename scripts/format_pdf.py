#!/usr/bin/env python3
"""Render a structured UTF-8 Markdown document in the reusable official A4 layout."""

from __future__ import annotations

import argparse
import html
import json
import re
from pathlib import Path

from pypdf import PdfReader
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from reportlab.platypus import (
    BaseDocTemplate,
    CondPageBreak,
    Frame,
    FrameBreak,
    KeepTogether,
    NextPageTemplate,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True, type=Path, help="UTF-8 Markdown source")
    parser.add_argument("--output", required=True, type=Path, help="PDF destination")
    parser.add_argument("--footer", default="Adresare juridică", help="Short footer title")
    parser.add_argument("--pdf-title", default=None, help="PDF metadata title")
    parser.add_argument("--cover-label", default="ADRESARE", help="Cover label")
    parser.add_argument("--annex-label", default="ANEXĂ", help="Annex label")
    parser.add_argument(
        "--references-heading",
        default=None,
        help="Exact references heading; if omitted, common headings are detected automatically",
    )
    parser.add_argument("--font-dir", type=Path, default=None, help="Directory containing Times-style TTF files")
    parser.add_argument("--report", type=Path, default=None, help="Optional JSON QA report path")
    return parser.parse_args()


def find_font_dir(explicit: Path | None) -> Path:
    candidates = []
    if explicit:
        candidates.append(explicit)
    candidates.extend(
        [
            Path("C:/Windows/Fonts"),
            Path("/usr/share/fonts/truetype/liberation2"),
            Path("/usr/share/fonts/truetype/liberation"),
            Path("/usr/share/fonts/truetype/dejavu"),
        ]
    )
    for directory in candidates:
        if not directory.exists():
            continue
        if any((directory / name).exists() for name in ("times.ttf", "LiberationSerif-Regular.ttf", "DejaVuSerif.ttf")):
            return directory
    raise FileNotFoundError("Nu a fost găsit un font serif TTF. Indică --font-dir.")


def register_fonts(font_dir: Path) -> str:
    variants = [
        ("TimesLocal", ["times.ttf", "LiberationSerif-Regular.ttf", "DejaVuSerif.ttf"]),
        ("TimesLocal-Bold", ["timesbd.ttf", "LiberationSerif-Bold.ttf", "DejaVuSerif-Bold.ttf"]),
        ("TimesLocal-Italic", ["timesi.ttf", "LiberationSerif-Italic.ttf", "DejaVuSerif-Italic.ttf"]),
        ("TimesLocal-BoldItalic", ["timesbi.ttf", "LiberationSerif-BoldItalic.ttf", "DejaVuSerif-BoldItalic.ttf"]),
    ]
    chosen: dict[str, Path] = {}
    for family, names in variants:
        for name in names:
            candidate = font_dir / name
            if candidate.exists():
                chosen[family] = candidate
                break
        if family not in chosen:
            # A regular fallback is preferable to silently substituting a font with no Cyrillic glyphs.
            chosen[family] = chosen.get("TimesLocal", font_dir / names[0])
    for family, path in chosen.items():
        if family not in pdfmetrics.getRegisteredFontNames():
            pdfmetrics.registerFont(TTFont(family, str(path)))
    pdfmetrics.registerFontFamily(
        "TimesLocal",
        normal="TimesLocal",
        bold="TimesLocal-Bold",
        italic="TimesLocal-Italic",
        boldItalic="TimesLocal-BoldItalic",
    )
    return "TimesLocal"


def clean(value: str) -> str:
    return value.replace(" ↗", "").replace("—", "-").replace("–", "-").replace("\u2011", "-")


def inline(value: str) -> str:
    value = clean(value)
    links: list[tuple[str, str]] = []

    def take_link(match: re.Match[str]) -> str:
        links.append((match.group(1), match.group(2)))
        return f"ZZLINKTOKEN{len(links) - 1}ZZ"

    value = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", take_link, value)
    value = html.escape(value)
    value = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", value)
    value = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"<i>\1</i>", value)
    for index, (label, url) in enumerate(links):
        token = f"ZZLINKTOKEN{index}ZZ"
        value = value.replace(
            token,
            f'<link href="{html.escape(url, quote=True)}" color="#17365d"><u>{html.escape(label)}</u></link>',
        )
    return value


REFERENCE_HEADINGS = (
    "Surse și repere",
    "Surse si repere",
    "Referințe",
    "Referinte",
    "Bibliografie",
    "Sources and references",
    "References",
    "Sources",
    "Источники и ориентиры",
    "Источники",
    "Références",
    "Sources et repères",
)

SUBJECT_PREFIXES = (
    "Obiect",
    "Subiect",
    "Subject",
    "Object",
    "Objet",
    "Предмет",
    "Тема",
)

SENDER_PREFIXES = (
    "De la:",
    "De la",
    "Expeditor:",
    "From:",
    "Sender:",
    "От:",
)

GREETING_PREFIXES = (
    "Stimate",
    "Stimată",
    "Stimați",
    "Dear",
    "Cher",
    "Chère",
    "Уважаемый",
    "Уважаемая",
)

ANNEX_TITLE_PREFIXES = (
    "proiect",
    "project",
    "анекс",
    "прилож",
    "annex",
    "anex",
)

IDENTITY_PREFIXES = (
    "Autorul sesizării",
    "Autorul adresării",
    "Autorul demersului",
    "Autorul",
    "Autor",
    "Petiționar",
    "Petitioner",
    "Applicant",
    "Author",
    "Автор обращения",
    "Автор",
    "Заявитель",
)

IDENTITY_FIELD_LABELS = IDENTITY_PREFIXES + (
    "Adresă",
    "Adresa",
    "Adresa de corespondență",
    "Adresa de corespondenta",
    "Address",
    "Correspondence address",
    "Адрес",
    "Адрес для корреспонденции",
    "Почтовый адрес",
    "Юридический адрес",
    "IDNO",
    "INN",
    "ИНН",
    "Forma juridică",
    "Forma juridica",
    "Legal form",
    "Организационно-правовая форма",
    "Data înregistrării",
    "Data inregistrarii",
    "Registration date",
    "Дата регистрации",
    "Număr de înregistrare",
    "Registration number",
    "Исторический регистрационный номер",
    "Sediu",
    "Седалище",
    "Conducător",
    "Conducator",
    "Director",
    "Руководитель",
)

ABBREVIATION_PREFIXES = (
    "Abrevieri:",
    "Abbreviations:",
    "Abréviations:",
    "Сокращения:",
)


def detect_reference_heading(source_text: str, requested: str | None) -> str | None:
    if requested:
        return requested.lstrip("# ").strip()
    headings = {match.group(1).strip() for match in re.finditer(r"(?m)^##\s+(.+?)\s*$", source_text)}
    for candidate in REFERENCE_HEADINGS:
        if candidate in headings:
            return candidate
    markers = ("surs", "referin", "bibliograf", "source", "reference", "источник", "репер", "référ")
    for heading in headings:
        if any(marker in heading.casefold() for marker in markers):
            return heading
    return None


def split_subject(block: str) -> str | None:
    pattern = r"^\*\*(?:" + "|".join(re.escape(item) for item in SUBJECT_PREFIXES) + r")\s*:\s*(.*?)\*\*\s*$"
    match = re.match(pattern, block, flags=re.S | re.I)
    return match.group(1).strip() if match else None


def identity_field_pattern() -> str:
    return r"(?=(?:" + "|".join(re.escape(item) for item in IDENTITY_FIELD_LABELS) + r")\s*:)"


def make_styles():
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="BodyLegal", fontName="TimesLocal", fontSize=10.8, leading=14.5, alignment=TA_JUSTIFY, spaceAfter=7))
    styles.add(ParagraphStyle(name="AddressLegal", parent=styles["BodyLegal"], alignment=TA_LEFT, spaceAfter=5))
    styles.add(ParagraphStyle(name="TitleLegal", fontName="TimesLocal-Bold", fontSize=14, leading=19, alignment=TA_CENTER, spaceBefore=12, spaceAfter=20, keepWithNext=True))
    styles.add(ParagraphStyle(name="HeadingLegal", fontName="TimesLocal-Bold", fontSize=12, leading=16, spaceBefore=17, spaceAfter=10, keepWithNext=True))
    styles.add(ParagraphStyle(name="SubLegal", parent=styles["HeadingLegal"], fontSize=11.5, spaceBefore=12, spaceAfter=8))
    styles.add(ParagraphStyle(name="SourceLegal", parent=styles["BodyLegal"], alignment=TA_LEFT, fontSize=8.4, leading=10.1, spaceAfter=3))
    styles.add(ParagraphStyle(name="SourceHeading", fontName="TimesLocal-Bold", fontSize=9.4, leading=11.5, spaceBefore=7, spaceAfter=4, keepWithNext=True))
    styles.add(ParagraphStyle(name="SubjectLegal", parent=styles["BodyLegal"], alignment=TA_LEFT, spaceBefore=9, spaceAfter=17, keepWithNext=True))
    styles.add(ParagraphStyle(name="CoverTitle", fontName="TimesLocal-Bold", fontSize=16, leading=20, alignment=TA_CENTER, spaceAfter=12, keepWithNext=True))
    styles.add(ParagraphStyle(name="CoverSubject", fontName="TimesLocal", fontSize=12, leading=16, alignment=TA_CENTER, spaceAfter=22, keepWithNext=True))
    styles.add(ParagraphStyle(name="SenderLegal", parent=styles["AddressLegal"], fontSize=10.5, leading=17))
    styles.add(ParagraphStyle(name="AnnexTitle", fontName="TimesLocal-Bold", fontSize=16, leading=21, alignment=TA_CENTER, spaceBefore=0, spaceAfter=18))
    styles.add(ParagraphStyle(name="AnnexKicker", fontName="TimesLocal-Bold", fontSize=10.5, leading=13, alignment=TA_CENTER, spaceBefore=0, spaceAfter=5, keepWithNext=True, textColor=colors.HexColor("#555555")))
    styles.add(ParagraphStyle(name="AnnexRecipient", parent=styles["AddressLegal"], fontSize=12, leading=18, spaceAfter=13))
    styles.add(ParagraphStyle(name="AnnexLabel", fontName="TimesLocal-Bold", fontSize=10.7, leading=14.5, alignment=TA_LEFT))
    styles.add(ParagraphStyle(name="AnnexValue", fontName="TimesLocal", fontSize=10.7, leading=14.5, alignment=TA_LEFT))
    styles.add(ParagraphStyle(name="AnnexNote", fontName="TimesLocal-Italic", fontSize=10.3, leading=14, alignment=TA_LEFT, leftIndent=43 * mm, spaceBefore=3, spaceAfter=9))
    styles.add(ParagraphStyle(name="AnnexAbbrev", parent=styles["BodyLegal"], fontSize=10.7, leading=15, alignment=TA_LEFT, spaceBefore=8, spaceAfter=8))
    return styles


def identity_table(block: str, styles):
    lines = [line.strip() for line in block.splitlines() if line.strip()]
    rows = []
    note = ""
    for line in lines:
        pieces = re.split(identity_field_pattern(), line, flags=re.I)
        for piece in pieces:
            piece = piece.strip()
            if not piece:
                continue
            match = re.match(r"([^:]+):\s*(.*)", piece, re.S)
            if not match:
                continue
            label, value = match.groups()
            rows.append([Paragraph(inline(label + ":"), styles["AnnexLabel"]), Paragraph(inline(value), styles["AnnexValue"])])
    table = Table(rows, colWidths=[43 * mm, 117 * mm], hAlign="LEFT")
    table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    return table, note


def reference_block(block: str, styles):
    pieces = re.split(r"\n\s*\n", block)
    group = [Paragraph(inline(pieces[0]), styles["SourceHeading"])]
    group.extend(Paragraph(inline(" ".join(part.splitlines())), styles["SourceLegal"]) for part in pieces[1:])
    return KeepTogether(group)


class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, footer: str = "Document oficial", **kwargs):
        super().__init__(*args, **kwargs)
        self.footer = footer
        self.saved = []

    def showPage(self):
        self.saved.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        page_count = len(self.saved)
        for state in self.saved:
            self.__dict__.update(state)
            self.setFont("TimesLocal", 9)
            self.setFillColor(colors.HexColor("#555555"))
            self.drawString(25 * mm, 15 * mm, self.footer)
            self.drawRightString(A4[0] - 25 * mm, 15 * mm, f"{self._pageNumber} / {page_count}")
            canvas.Canvas.showPage(self)
        canvas.Canvas.save(self)


def render(args: argparse.Namespace) -> dict:
    source = args.source.resolve()
    output = args.output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    source_text = source.read_text(encoding="utf-8")
    register_fonts(find_font_dir(args.font_dir))
    styles = make_styles()

    reference_heading_text = detect_reference_heading(source_text, args.references_heading)
    main_text, separator, reference_text = source_text.partition(reference_heading_text) if reference_heading_text else (source_text, "", "")
    if separator:
        # The Markdown heading marker is consumed by partition(); remove the
        # remaining `## ` fragment from the main story before rebuilding it.
        main_text = re.sub(r"\n##\s*$", "\n", main_text)
    blocks = [block.strip() for block in re.split(r"\n\s*\n", main_text.strip()) if block.strip()]
    if separator:
        blocks.append(f"## {reference_heading_text}")
        blocks.extend(block.strip() for block in re.split(r"(?=(?:-\s*)?\*\*(?:\[[A-Za-z0-9_-]+\]|[A-Za-z0-9_-]+)\*\*)", reference_text) if block.strip())

    story = []
    cover = True
    annex_header = False
    annex_pending = False
    annex_recipient_pending = False
    references = False
    cover_recipient = None
    cover_sender = None
    cover_header_done = False

    def flush_cover_header():
        nonlocal cover_recipient, cover_sender
        if cover_recipient is None and cover_sender is None:
            return
        if cover_recipient is not None and cover_sender is not None:
            sender_html = "<br/>".join(inline(line.strip()) for line in cover_sender.splitlines())
            recipient_html = "<br/>".join(inline(line.strip()) for line in cover_recipient.splitlines())
            header = Table(
                [[Paragraph(sender_html, styles["SenderLegal"]), Paragraph(recipient_html, styles["AddressLegal"])]],
                colWidths=[68 * mm, 92 * mm],
            )
            header.setStyle(TableStyle([
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
            ]))
            story.append(header)
        else:
            block = cover_recipient or cover_sender or ""
            story.append(Paragraph("<br/>".join(inline(line.strip()) for line in block.splitlines()), styles["AddressLegal"]))
        story.append(Spacer(1, 14 * mm))
        cover_recipient = None
        cover_sender = None

    for block in blocks:
        if block == "---":
            if cover and not cover_header_done:
                flush_cover_header()
                cover_header_done = True
            cover = False
            annex_pending = True
            story.append(CondPageBreak(A4[1] - 46 * mm - 0.1))
            continue

        if cover and block.startswith(SENDER_PREFIXES):
            cover_sender = block
            continue

        subject = split_subject(block) if cover else None
        if cover and subject is not None:
            flush_cover_header()
            cover_header_done = True
            story.append(Paragraph(inline(args.cover_label), styles["CoverTitle"]))
            story.append(Paragraph(inline(subject), styles["CoverSubject"]))
            continue

        if cover and not cover_header_done and cover_recipient is None and not block.startswith(("#", "##", "###")) and not block.startswith(GREETING_PREFIXES):
            cover_recipient = block
            continue

        if cover and block.startswith(GREETING_PREFIXES):
            story.append(Paragraph(inline(block), styles["AddressLegal"]))
            story.append(Spacer(1, 3 * mm))
            continue

        if block.startswith("# "):
            heading = block[2:].strip()
            if annex_pending or heading.lower().startswith(ANNEX_TITLE_PREFIXES):
                story.append(Paragraph(inline(args.annex_label), styles["AnnexKicker"]))
                story.append(Paragraph(inline(heading), styles["AnnexTitle"]))
                annex_header = True
                annex_pending = False
                annex_recipient_pending = True
            else:
                story.append(Paragraph(inline(heading), styles["TitleLegal"]))
            continue

        if annex_header and annex_recipient_pending and not re.match(r"^(?:" + "|".join(re.escape(item) for item in IDENTITY_PREFIXES) + r")\s*:", block, flags=re.I):
            story.append(Paragraph("<br/>".join(inline(line.strip()) for line in block.splitlines()), styles["AnnexRecipient"]))
            story.append(Spacer(1, 4 * mm))
            annex_recipient_pending = False
            continue

        if annex_header and re.match(r"^(?:" + "|".join(re.escape(item) for item in IDENTITY_PREFIXES) + r"):", block, flags=re.I):
            table, note = identity_table(block, styles)
            story.append(KeepTogether([table]))
            if note:
                story.append(Paragraph(inline(note), styles["AnnexNote"]))
            story.append(Spacer(1, 2 * mm))
            continue

        if annex_header and block.startswith(ABBREVIATION_PREFIXES):
            text = block.split(":", 1)[1].strip()
            story.append(Paragraph("<b>" + inline(block.split(":", 1)[0]) + "</b><br/>" + inline(text), styles["AnnexAbbrev"]))
            annex_header = False
            continue

        if block.startswith("## "):
            heading = block[3:].strip()
            if reference_heading_text and heading == reference_heading_text:
                references = True
                story.extend([NextPageTemplate("ReferencesFirst"), CondPageBreak(A4[1] - 46 * mm - 0.1)])
                story.append(Paragraph(inline(heading), styles["HeadingLegal"]))
                story.extend([NextPageTemplate("References"), FrameBreak()])
            else:
                story.append(Paragraph(inline(heading), styles["HeadingLegal"]))
            continue

        if block.startswith("### "):
            story.append(Paragraph(inline(block[4:].strip()), styles["SubLegal"]))
            continue

        if references and (block.startswith("**[") or re.match(r"^(?:-\s*)?\*\*[A-Za-z0-9_-]+\*\*\s+[-—]", block)):
            story.append(reference_block(block, styles))
            continue

        style = "SourceLegal" if references else "BodyLegal"
        if re.match(r"^\d+\. ", block):
            for line in block.splitlines():
                story.append(Paragraph(inline(line), styles[style]))
        else:
            story.append(Paragraph("<br/>".join(inline(line.strip()) for line in block.splitlines()), styles[style]))

    if cover:
        flush_cover_header()

    left = 25 * mm
    bottom = 24 * mm
    width = A4[0] - 50 * mm
    height = A4[1] - 46 * mm
    gutter = 8 * mm
    column = (width - gutter) / 2

    def make_frame(x, y, w, h, frame_id):
        return Frame(x, y, w, h, id=frame_id, leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)

    document = BaseDocTemplate(
        str(output),
        pagesize=A4,
        rightMargin=25 * mm,
        leftMargin=25 * mm,
        topMargin=22 * mm,
        bottomMargin=24 * mm,
        title=args.pdf_title or output.stem,
        author="",
        subject=args.pdf_title or output.stem,
    )
    document.addPageTemplates([
        PageTemplate(id="Body", frames=[make_frame(left, bottom, width, height, "body")]),
        PageTemplate(id="ReferencesFirst", frames=[
            make_frame(left, bottom + height - 15 * mm, width, 15 * mm, "refs-title"),
            make_frame(left, bottom, column, height - 15 * mm, "refs-first-left"),
            make_frame(left + column + gutter, bottom, column, height - 15 * mm, "refs-first-right"),
        ]),
        PageTemplate(id="References", frames=[
            make_frame(left, bottom, column, height, "refs-left"),
            make_frame(left + column + gutter, bottom, column, height, "refs-right"),
        ]),
    ])
    document.build(story, canvasmaker=lambda *a, **kw: NumberedCanvas(*a, footer=args.footer, **kw))

    reader = PdfReader(str(output))
    uris = []
    for page in reader.pages:
        for annotation in page.get("/Annots", []):
            action = annotation.get_object().get("/A", {})
            if action.get("/URI"):
                uris.append(str(action["/URI"]))
    expected_urls = set(re.findall(r"\]\((https?://[^)]+)\)", source_text))
    missing_urls = sorted(expected_urls - set(uris))
    text = "\n".join(page.extract_text() or "" for page in reader.pages)
    page_body_text = []
    for page in reader.pages:
        page_text = page.extract_text() or ""
        page_text = page_text.replace(args.footer, "")
        page_text = re.sub(r"\b\d+\s*/\s*\d+\b", "", page_text)
        page_body_text.append(page_text.strip())
    report = {
        "pages": len(reader.pages),
        "all_pages_nonempty": all(page_body_text),
        "active_uri_links": len(uris),
        "unique_destinations": len(set(uris)),
        "expected_urls": len(expected_urls),
        "missing_urls": missing_urls,
        "replacement_chars": text.count("�"),
        "double_spaces": len(re.findall(r" {2,}", text)),
        "file": str(output),
        "source": str(source),
    }
    if not report["all_pages_nonempty"] or report["replacement_chars"] or missing_urls:
        raise RuntimeError(json.dumps(report, ensure_ascii=False, indent=2))
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False))
    return report


if __name__ == "__main__":
    render(parse_args())
