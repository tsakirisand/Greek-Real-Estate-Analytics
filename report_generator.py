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

    # Section 2: Macroeconomic Market Findings (Dynamically Calculated from Database)
    sec2_title = "2. Key Macroeconomic Market Findings" if lang == "en" else "2. Βασικά Μακροοικονομικά Συμπεράσματα"
    elements.append(Paragraph(sec2_title, heading_style))

    dyn_insights = queries.get_dynamic_market_insights(db, area_slug="athens")
    if dyn_insights:
        if lang == "en":
            p1 = (
                f"<b>Historical Recession Cycle ({dyn_insights['peakPeriod']} → {dyn_insights['troughPeriod']}):</b> "
                f"The apartment price index declined by <b>{dyn_insights['recessionDeclinePct']:.1f}%</b> "
                f"from its peak of {dyn_insights['peakIndex']:.1f} ({dyn_insights['peakPeriod']}) to its trough of {dyn_insights['troughIndex']:.1f} ({dyn_insights['troughPeriod']})."
            )
            p2 = (
                f"<b>Recovery Trajectory ({dyn_insights['troughPeriod']} → {dyn_insights['latestPeriod']}):</b> "
                f"The index rebounded by <b>+{dyn_insights['recoveryReboundPct']:.1f}%</b> "
                f"from {dyn_insights['troughIndex']:.1f} to {dyn_insights['latestIndex']:.1f} ({dyn_insights['latestPeriod']}), "
                f"standing +{dyn_insights['base2021GrowthPct']:.1f}% above the 2021 base level."
            )
            p3 = (
                f"<b>Cumulative Horizon Growth ({dyn_insights['firstPeriod']} → {dyn_insights['latestPeriod']}):</b> "
                f"Across the full dataset horizon ({dyn_insights['firstPeriod']} to {dyn_insights['latestPeriod']}), "
                f"the price index recorded a total cumulative change of <b>+{dyn_insights['cumulativeGrowthPct']:.1f}%</b>."
            )
        else:
            p1 = (
                f"<b>Ιστορικός Κύκλος Ύφεσης ({dyn_insights['peakPeriod']} → {dyn_insights['troughPeriod']}):</b> "
                f"Ο δείκτης τιμών κατέγραψε πτώση <b>{dyn_insights['recessionDeclinePct']:.1f}%</b> "
                f"από το ανώτατο σημείο των {dyn_insights['peakIndex']:.1f} μονάδων ({dyn_insights['peakPeriod']}) "
                f"στο ναδίρ των {dyn_insights['troughIndex']:.1f} μονάδων ({dyn_insights['troughPeriod']})."
            )
            p2 = (
                f"<b>Πορεία Ανάκαμψης ({dyn_insights['troughPeriod']} → {dyn_insights['latestPeriod']}):</b> "
                f"Ο δείκτης σημείωσε ανάκαμψη <b>+{dyn_insights['recoveryReboundPct']:.1f}%</b> "
                f"από τις {dyn_insights['troughIndex']:.1f} στις {dyn_insights['latestIndex']:.1f} μονάδες ({dyn_insights['latestPeriod']}), "
                f"βρισκόμενος +{dyn_insights['base2021GrowthPct']:.1f}% πάνω από το έτος βάσης 2021."
            )
            p3 = (
                f"<b>Αθροιστική Μεταβολή ({dyn_insights['firstPeriod']} → {dyn_insights['latestPeriod']}):</b> "
                f"Στη συνολική περίοδο κάλυψης ({dyn_insights['firstPeriod']} έως {dyn_insights['latestPeriod']}), "
                f"ο δείκτης κατέγραψε αθροιστική μεταβολή <b>+{dyn_insights['cumulativeGrowthPct']:.1f}%</b>."
            )

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
