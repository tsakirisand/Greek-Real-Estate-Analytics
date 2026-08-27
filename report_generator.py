import io
from datetime import datetime
from sqlalchemy.orm import Session

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable

import queries
from i18n import get_area_name

def generate_pdf_report(db: Session, lang: str = "en") -> bytes:
    """
    Generates a professional executive PDF summary report of Bank of Greece
    apartment price indices, regional rankings, and macro analysis.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    styles = getSampleStyleSheet()
    
    # Custom Palette
    c_primary = colors.HexColor("#1e3a8a")
    c_secondary = colors.HexColor("#3b82f6")
    c_dark = colors.HexColor("#0f172a")
    c_light_bg = colors.HexColor("#f8fafc")

    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=22,
        leading=26,
        textColor=c_primary
    )
    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=11,
        leading=14,
        textColor=colors.HexColor("#64748b")
    )
    heading_style = ParagraphStyle(
        'SectionHeading',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=14,
        leading=18,
        textColor=c_primary,
        spaceBefore=14,
        spaceAfter=6
    )
    body_style = ParagraphStyle(
        'BodyTextCustom',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9.5,
        leading=13.5,
        textColor=c_dark
    )

    elements = []

    # Header
    doc_title = "Greek Real Estate Market Executive Analytics" if lang == "en" else "Εκτελεστική Αναφορά Αγοράς Ακινήτων Ελλάδος"
    doc_sub = f"Official Bank of Greece Apartment Price Index Report • Generated {datetime.now().strftime('%B %d, %Y')}"
    elements.append(Paragraph(doc_title, title_style))
    elements.append(Paragraph(doc_sub, subtitle_style))
    elements.append(Spacer(1, 10))
    elements.append(HRFlowable(width="100%", thickness=1.5, color=c_secondary, spaceBefore=4, spaceAfter=14))

    # Section 1: Regional Metrics Table
    sec1_title = "1. Regional Valuation & Growth Summary" if lang == "en" else "1. Σύνοψη Δεικτών & Μεταβολών ανά Περιοχή"
    elements.append(Paragraph(sec1_title, heading_style))

    areas = queries.get_all_geographical_areas(db)
    table_data = [
        ["Geographical Region", "Latest Index", "YoY Growth", "QoQ Growth", "Market Status"]
        if lang == "en" else
        ["Περιοχή", "Δείκτης Τιμών", "Ετήσια Μεταβολή", "Μεταβολή Τριμήνου", "Κατάσταση"]
    ]

    for area in areas:
        s = queries.get_metrics_summary(db, area_slugs=[area.slug])
        if s and "latestIndex" in s:
            yoy = s.get("yoyChange")
            qoq = s.get("qoqChange")
            yoy_str = f"{yoy:+.1f}%" if yoy is not None else "—"
            qoq_str = f"{qoq:+.1f}%" if qoq is not None else "—"
            direction = s.get("marketDirection", "Stable")
            
            table_data.append([
                get_area_name(lang, area.name),
                f"{s['latestIndex']:.1f}",
                yoy_str,
                qoq_str,
                direction
            ])

    t_summary = Table(table_data, colWidths=[150, 95, 95, 95, 105])
    t_summary.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), c_primary),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9.5),
        ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
        ('TOPPADDING', (0, 0), (-1, 0), 6),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, c_light_bg]),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    elements.append(t_summary)
    elements.append(Spacer(1, 14))

    # Section 2: Macroeconomic Market Insights
    sec2_title = "2. Key Macroeconomic Market Findings" if lang == "en" else "2. Βασικά Μακροοικονομικά Συμπεράσματα"
    elements.append(Paragraph(sec2_title, heading_style))

    if lang == "en":
        p1 = "<b>Recession Cycle (2008–2017):</b> The apartment price index experienced a severe 42.2% drop from 101.5 to 59.0 due to a 25% GDP loss, >95% contraction in mortgage credit, and new property taxation (ENFIA)."
        p2 = "<b>Recovery Catalyst (2018–2025):</b> The index rebounded by +128.4% to 134.8+, propelled by Foreign Direct Investment (Golden Visa), short-term rental conversions (Airbnb), and a decade-long housing supply deficit."
        p3 = "<b>Metropolitan Decoupling:</b> Athens (+136.2% from bottom) and Thessaloniki (+131.0%) significantly outperformed regional areas (+72.1%) due to institutional investment concentration."
    else:
        p1 = "<b>Κύκλος Ύφεσης (2008–2017):</b> Ο δείκτης τιμών κατέγραψε πτώση -42.2% (από 101.5 σε 59.0) λόγω απώλειας 25% ΑΕΠ, μείωσης στεγαστικής πίστης κατά >95% και επιβολής ΕΝΦΙΑ."
        p2 = "<b>Καταλύτες Ανάκαμψης (2018–2025):</b> Ραγδαία άνοδος +128.4% λόγω ξένων επενδύσεων (Golden Visa), επέκτασης βραχυχρόνιων μισθώσεων (Airbnb) και δομικού ελλείμματος νεόδμητων κατοικιών."
        p3 = "<b>Γεωγραφική Αποσύνδεση:</b> Η Αθήνα (+136.2% από το ναδίρ) και η Θεσσαλονίκη (+131.0%) κινούνται ταχύτερα από την περιφέρεια (+72.1%)."

    elements.append(Paragraph(p1, body_style))
    elements.append(Spacer(1, 4))
    elements.append(Paragraph(p2, body_style))
    elements.append(Spacer(1, 4))
    elements.append(Paragraph(p3, body_style))
    elements.append(Spacer(1, 14))

    # Section 3: Data Provenance
    sec3_title = "3. Primary Dataset Source & Attribution" if lang == "en" else "3. Πηγή Δεδομένων & Πιστοποίηση"
    elements.append(Paragraph(sec3_title, heading_style))

    prov_text = (
        "This analytics report is computed from 62 official XLS datasets published by the <b>Bank of Greece</b> "
        "(Real Estate Market Analysis Section). All indices are normalized to Base 2021=100."
    ) if lang == "en" else (
        "Η παρούσα εκτελεστική αναφορά βασίζεται σε 62 επίσημα αρχεία XLS της <b>Τράπεζας της Ελλάδος</b> "
        "(Τμήμα Αναλύσεων Αγοράς Ακινήτων). Όλοι οι δείκτες έχουν ως έτος βάσης το 2021 (=100)."
    )
    elements.append(Paragraph(prov_text, body_style))

    doc.build(elements)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes
