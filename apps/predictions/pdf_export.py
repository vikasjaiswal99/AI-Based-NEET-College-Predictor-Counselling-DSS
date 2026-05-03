"""
apps/predictions/pdf_export.py
==============================
Generate PDF prediction reports using ReportLab.
"""
from io import BytesIO
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT


def generate_prediction_pdf(
    student_rank: int,
    student_category: str,
    student_state: str,
    student_course: str,
    results: list[dict],
    safe_count: int,
    target_count: int,
    dream_count: int,
) -> BytesIO:
    """Generate a professional PDF report of prediction results.

    Args:
        student_rank: Student's NEET rank
        student_category: Category (GEN, OBC, SC, ST, EWS)
        student_state: Home state
        results: List of enriched college dicts from _enrich()
        safe/target/dream_count: Tier counts

    Returns:
        BytesIO buffer containing PDF data.
    """
    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        leftMargin=1.5*cm, rightMargin=1.5*cm,
        topMargin=2*cm, bottomMargin=2*cm,
        title="NEET College Prediction Report",
        author="NEETPredict AI",
    )

    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle', parent=styles['Title'],
        fontSize=22, textColor=colors.HexColor('#0d1b2a'),
        spaceAfter=6,
    )
    subtitle_style = ParagraphStyle(
        'CustomSubtitle', parent=styles['Normal'],
        fontSize=11, textColor=colors.HexColor('#6b7280'),
        spaceAfter=16, alignment=TA_CENTER,
    )
    heading_style = ParagraphStyle(
        'SectionHeading', parent=styles['Heading2'],
        fontSize=14, textColor=colors.HexColor('#0d1b2a'),
        spaceBefore=16, spaceAfter=8,
        borderColor=colors.HexColor('#f59e0b'),
        borderWidth=2, borderPadding=4,
    )
    normal = styles['Normal']
    small_style = ParagraphStyle(
        'SmallText', parent=normal,
        fontSize=8, textColor=colors.HexColor('#9ca3af'),
    )

    elements = []

    # ── Header ──
    elements.append(Paragraph("NEETPredict AI", title_style))
    elements.append(Paragraph("College Prediction Report — Powered by ML Scoring Engine", subtitle_style))
    elements.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor('#f59e0b')))
    elements.append(Spacer(1, 12))

    # ── Student Info ──
    info_data = [
        ["NEET Rank", f"#{student_rank:,}"],
        ["Category", student_category],
        ["Home State", student_state or "All States"],
        ["Target Course", student_course],
        ["Total Matches", str(len(results))],
        ["Safe / Target / Dream", f"{safe_count} / {target_count} / {dream_count}"],
    ]
    info_table = Table(info_data, colWidths=[3*inch, 3.5*inch])
    info_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f8fafc')),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#374151')),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('PADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e5e7eb')),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    elements.append(info_table)
    elements.append(Spacer(1, 16))

    # ── Tier Sections ──
    tier_configs = [
        ("Safe Colleges", "safe", colors.HexColor('#059669'), colors.HexColor('#ecfdf5')),
        ("Target Colleges", "target", colors.HexColor('#0284c7'), colors.HexColor('#eff6ff')),
        ("Dream Colleges", "dream", colors.HexColor('#7c3aed'), colors.HexColor('#faf5ff')),
    ]

    for tier_title, tier_key, tier_color, bg_color in tier_configs:
        tier_results = [r for r in results if r['tier'].lower() == tier_key]
        if not tier_results:
            continue

        elements.append(Paragraph(f"✦ {tier_title} ({len(tier_results)})", heading_style))

        # Build table
        header = ['#', 'College', 'City / State', 'Type', 'Cutoff', 'Fee', 'Score']
        rows_data = [header]

        for i, c in enumerate(tier_results, 1):
            rows_data.append([
                str(i),
                Paragraph(c['college'], ParagraphStyle('Cell', fontSize=8, leading=10)),
                Paragraph(f"{c['city']}, {c['state']}", ParagraphStyle('Cell', fontSize=7, leading=9)),
                c['college_type'],
                c['closing_rank'],
                c['annual_fee'],
                f"{c['score_total']:.0f}/100",
            ])

        col_widths = [0.4*cm, 5*cm, 3.5*cm, 1.8*cm, 2*cm, 2.2*cm, 1.5*cm]
        t = Table(rows_data, colWidths=col_widths, repeatRows=1)
        t.setStyle(TableStyle([
            # Header
            ('BACKGROUND', (0, 0), (-1, 0), tier_color),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 8),
            # Body
            ('FONTSIZE', (0, 1), (-1, -1), 7.5),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, bg_color]),
            # Grid
            ('GRID', (0, 0), (-1, -1), 0.3, colors.HexColor('#e5e7eb')),
            ('PADDING', (0, 0), (-1, -1), 5),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ALIGN', (0, 0), (0, -1), 'CENTER'),
            ('ALIGN', (-1, 0), (-1, -1), 'CENTER'),
        ]))
        elements.append(t)
        elements.append(Spacer(1, 10))

    # ── Footer ──
    elements.append(Spacer(1, 20))
    elements.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#e5e7eb')))
    elements.append(Spacer(1, 6))
    elements.append(Paragraph(
        "This report is generated by NEETPredict AI using ML-based scoring. "
        "Data sourced from MCC counselling records. For official admissions, "
        "always refer to mcc.nic.in and your state counselling authority.",
        small_style
    ))

    doc.build(elements)
    buf.seek(0)
    return buf
