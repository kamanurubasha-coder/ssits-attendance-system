import os
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as RLImage
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

def generate_attendance_pdf(output_path, college_name, program_name, dept_name, year_name, session_type, date_str, teacher_name, hod_name, total_count, absent_students, day_type='working', occasion_name='', section='A'):
    """
    Generates a clean, official attendance report in PDF format with accurate real-time timestamp,
    college & NAAC logos, Autonomous institution branding, College Code SRSR, and day status.
    """
    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        rightMargin=36,
        leftMargin=36,
        topMargin=26,
        bottomMargin=26
    )
    
    story = []
    styles = getSampleStyleSheet()

    # Current accurate timestamp
    current_time_str = datetime.now().strftime("%A, %d-%b-%Y at %I:%M:%S %p IST")

    # Custom styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=14.5,
        leading=17.5,
        alignment=1, # Center
        textColor=colors.HexColor('#0F2C59')
    )

    autonomous_style = ParagraphStyle(
        'DocAutonomous',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9.5,
        leading=12,
        alignment=1, # Center
        textColor=colors.HexColor('#991B1B')
    )
    
    affiliation_style = ParagraphStyle(
        'DocAffiliation',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=7.5,
        leading=10,
        alignment=1, # Center
        textColor=colors.HexColor('#2D3748')
    )

    timestamp_left_style = ParagraphStyle(
        'TimestampLeft',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
        leading=10,
        alignment=0, # Left aligned!
        textColor=colors.HexColor('#4A5568')
    )

    header_box_style = ParagraphStyle(
        'HeaderBox',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=10,
        leading=13,
        alignment=1,
        textColor=colors.HexColor('#1E3C72')
    )

    cell_style = ParagraphStyle(
        'TableCell',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=11
    )
    
    cell_bold_style = ParagraphStyle(
        'TableCellBold',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8.5,
        leading=11
    )

    # 1. System Timestamp in Top-Left Corner & College Code on Right
    timestamp_table_data = [
        [
            Paragraph(f"<b>System Generated:</b> {current_time_str}", timestamp_left_style),
            Paragraph("<font color='#B7791F'><b>College Code: SRSR</b></font>", ParagraphStyle('CodeRight', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=8, leading=10, alignment=2, textColor=colors.HexColor('#B7791F')))
        ]
    ]
    timestamp_table = Table(timestamp_table_data, colWidths=[380, 143])
    timestamp_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2),
        ('TOPPADDING', (0,0), (-1,-1), 0),
        ('LEFTPADDING', (0,0), (-1,-1), 0),
        ('RIGHTPADDING', (0,0), (-1,-1), 0),
    ]))
    story.append(timestamp_table)
    story.append(Spacer(1, 3))

    # 2. Institutional Letterhead Header (Left Logo | Center Details | Right NAAC Logo)
    college_logo_path = os.path.join(os.path.dirname(__file__), "static", "images", "college_logo.png")
    naac_logo_path = os.path.join(os.path.dirname(__file__), "static", "images", "naac_logo.png")

    left_logo = None
    if os.path.exists(college_logo_path):
        try:
            left_logo = RLImage(college_logo_path, width=58, height=55)
        except Exception:
            left_logo = Paragraph("", cell_style)
    else:
        left_logo = Paragraph("", cell_style)

    right_logo = None
    if os.path.exists(naac_logo_path):
        try:
            right_logo = RLImage(naac_logo_path, width=70, height=48)
        except Exception:
            right_logo = Paragraph("", cell_style)
    else:
        right_logo = Paragraph("", cell_style)

    header_text_flowables = [
        Paragraph(college_name.upper(), title_style),
        Spacer(1, 1),
        Paragraph("(AN AUTONOMOUS INSTITUTION)", autonomous_style),
        Spacer(1, 1),
        Paragraph("<b>College Code: SRSR</b> | Approved by AICTE, New Delhi | Affiliated to JNTUA, Ananthapuramu", affiliation_style),
        Paragraph("Accredited by NAAC with 'B+' Grade", affiliation_style)
    ]

    header_table_data = [[left_logo, header_text_flowables, right_logo]]
    header_table = Table(header_table_data, colWidths=[65, 388, 70])
    header_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (0, 0), (0, 0), 'LEFT'),
        ('ALIGN', (1, 0), (1, 0), 'CENTER'),
        ('ALIGN', (2, 0), (2, 0), 'RIGHT'),
        ('TOPPADDING', (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 4))

    # Divider line
    story.append(Table([[""]], colWidths=[523], rowHeights=[2], style=[
        ('LINEBELOW', (0,0), (-1,-1), 1.8, colors.HexColor('#0F2C59'))
    ]))
    story.append(Spacer(1, 6))

    # 3. Report Title & Day Status
    session_label = "MORNING SESSION" if session_type.lower() == "morning" else "AFTERNOON SESSION (BUNK / POST-LUNCH)"
    
    if day_type == 'sunday':
        status_label = "SUNDAY (WEEKLY COLLEGE OFF)"
    elif day_type == 'second_saturday':
        status_label = "SECOND SATURDAY (COLLEGE HOLIDAY)"
    elif day_type == 'holiday':
        status_label = f"DECLARED HOLIDAY: {occasion_name.upper() if occasion_name else 'COLLEGE HOLIDAY'}"
    else:
        status_label = f"DAILY ATTENDANCE & ABSENTEES REPORT - {session_label}"

    report_banner_table = Table([[Paragraph(f"<b>{status_label}</b>", header_box_style)]], colWidths=[523])
    report_banner_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#EBF3FC')),
        ('BOX', (0,0), (-1,-1), 0.75, colors.HexColor('#CBD5E0')),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
    ]))
    story.append(report_banner_table)
    story.append(Spacer(1, 6))

    # 4. Class & Academic Info Grid
    section_str = f" - Section {section}" if section else ""
    info_data = [
        [
            Paragraph(f"<b>Program / Degree:</b> {program_name}", cell_style),
            Paragraph(f"<b>Department:</b> {dept_name}", cell_style),
            Paragraph(f"<b>Class / Section:</b> {year_name}{section_str}", cell_style)
        ],
        [
            Paragraph(f"<b>Attendance Date:</b> {date_str}", cell_style),
            Paragraph(f"<b>Class Teacher:</b> {teacher_name}", cell_style),
            Paragraph(f"<b>HOD:</b> {hod_name}", cell_style)
        ]
    ]
    info_table = Table(info_data, colWidths=[180, 173, 170])
    info_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#F8FAFC')),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E0')),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E2E8F0')),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(info_table)
    story.append(Spacer(1, 8))

    # 4. Statistics Summary Card
    if day_type != 'working':
        # Holiday stats
        stats_data = [
            [
                Paragraph("<b>Total Strength</b>", cell_style),
                Paragraph(f"<b>{total_count}</b>", cell_bold_style),
                Paragraph("<b>Day Status</b>", cell_style),
                Paragraph(f"<font color='#991B1B'><b>{status_label}</b></font>", cell_bold_style),
                Paragraph("<b>Classes Held</b>", cell_style),
                Paragraph("<b>No (Holiday)</b>", cell_bold_style),
            ]
        ]
        stats_table = Table(stats_data, colWidths=[90, 60, 90, 163, 70, 50])
        stats_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#FEF2F2')),
            ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#F87171')),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
    else:
        # High-Contrast Working Day Statistics Table
        present_count = total_count - len(absent_students)
        pct = round((present_count / total_count * 100), 1) if total_count > 0 else 0

        metric_head_style = ParagraphStyle('MHead', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=8, leading=10, alignment=1, textColor=colors.HexColor('#4A5568'))
        num_total_style = ParagraphStyle('SNumTot', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=13.5, leading=16, alignment=1, textColor=colors.HexColor('#0F2C59'))
        num_pres_style = ParagraphStyle('SNumPres', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=13.5, leading=16, alignment=1, textColor=colors.HexColor('#166534'))
        num_abs_style = ParagraphStyle('SNumAbs', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=13.5, leading=16, alignment=1, textColor=colors.HexColor('#991B1B'))
        num_pct_style = ParagraphStyle('SNumPct', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=13.5, leading=16, alignment=1, textColor=colors.HexColor('#92400E'))

        stats_data = [
            [
                Paragraph("TOTAL STRENGTH", metric_head_style),
                Paragraph("PRESENT COUNT", metric_head_style),
                Paragraph("ABSENTEES", metric_head_style),
                Paragraph("ATTENDANCE %", metric_head_style),
            ],
            [
                Paragraph(f"<b>{total_count}</b>", num_total_style),
                Paragraph(f"<b>{present_count}</b>", num_pres_style),
                Paragraph(f"<b>{len(absent_students)}</b>", num_abs_style),
                Paragraph(f"<b>{pct}%</b>", num_pct_style),
            ]
        ]
        stats_table = Table(stats_data, colWidths=[130, 131, 131, 131])
        stats_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, 0), colors.HexColor('#EBF3FC')),
            ('BACKGROUND', (0, 1), (0, 1), colors.HexColor('#DBEAFE')),
            ('BACKGROUND', (1, 0), (1, 0), colors.HexColor('#F0FDF4')),
            ('BACKGROUND', (1, 1), (1, 1), colors.HexColor('#DCFCE7')),
            ('BACKGROUND', (2, 0), (2, 0), colors.HexColor('#FEF2F2')),
            ('BACKGROUND', (2, 1), (2, 1), colors.HexColor('#FEE2E2')),
            ('BACKGROUND', (3, 0), (3, 0), colors.HexColor('#FFFBEB')),
            ('BACKGROUND', (3, 1), (3, 1), colors.HexColor('#FEF3C7')),
            ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#CBD5E0')),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E2E8F0')),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, 0), 4),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 2),
            ('TOPPADDING', (0, 1), (-1, 1), 2),
            ('BOTTOMPADDING', (0, 1), (-1, 1), 5),
        ]))

    story.append(stats_table)
    story.append(Spacer(1, 9))

    # 5. Table of Absent Students or Holiday Notice
    if day_type != 'working':
        holiday_p = Paragraph(f"<font color='#991B1B'><b>🌴 College Holiday Observed on this date ({status_label}). No absence recorded.</b></font>", ParagraphStyle(
            'HolNotice', parent=styles['Normal'], alignment=1, fontSize=10
        ))
        story.append(Spacer(1, 12))
        story.append(holiday_p)
    elif absent_students:
        table_heading = Paragraph(f"<b>LIST OF ABSENT STUDENTS ({len(absent_students)} Absentees Notified to Parents via WhatsApp):</b>", ParagraphStyle(
            'Head2', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=9, textColor=colors.HexColor('#1E293B')
        ))
        story.append(table_heading)
        story.append(Spacer(1, 4))

        table_rows = [
            [
                Paragraph("<b>S.No</b>", cell_bold_style),
                Paragraph("<b>Roll Number / PIN</b>", cell_bold_style),
                Paragraph("<b>Student Name</b>", cell_bold_style),
                Paragraph("<b>Father / Parent Name</b>", cell_bold_style),
                Paragraph("<b>WhatsApp Mobile</b>", cell_bold_style),
                Paragraph("<b>Alert Status</b>", cell_bold_style)
            ]
        ]
        
        for idx, s in enumerate(absent_students, start=1):
            table_rows.append([
                Paragraph(str(idx), cell_style),
                Paragraph(f"<b>{s['roll_number']}</b>", cell_style),
                Paragraph(s['name'], cell_style),
                Paragraph(s['father_name'], cell_style),
                Paragraph(f"+91 {s['father_phone']}", cell_style),
                Paragraph("<font color='#B91C1C'><b>WhatsApp Sent</b></font>", cell_style)
            ])
            
        absentee_table = Table(table_rows, colWidths=[32, 105, 125, 115, 90, 56])
        absentee_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0F2C59')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3.5),
            ('TOPPADDING', (0, 0), (-1, -1), 3.5),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E0')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F8FAFC')]),
            ('ALIGN', (0, 0), (0, -1), 'CENTER'),
            ('ALIGN', (5, 0), (5, -1), 'CENTER'),
        ]))
        story.append(absentee_table)
    else:
        no_absent_p = Paragraph("<font color='#166534'><b>🎉 100% ATTENDANCE! All students were present for this session.</b></font>", ParagraphStyle(
            'NoAbs', parent=styles['Normal'], alignment=1, fontSize=10
        ))
        story.append(Spacer(1, 10))
        story.append(no_absent_p)

    # 6. Signatures Footer
    story.append(Spacer(1, 30))
    sig_data = [
        [
            Paragraph("<b>Class Teacher Signature</b><br/><br/><br/>_______________________", cell_style),
            Paragraph("<b>Head of Department (HOD)</b><br/><br/><br/>_______________________", cell_style),
            Paragraph("<b>Principal / Administrative Head</b><br/><br/><br/>_______________________", cell_style)
        ]
    ]
    sig_table = Table(sig_data, colWidths=[174, 174, 175])
    sig_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'BOTTOM')
    ]))
    story.append(sig_table)

    # Build PDF
    doc.build(story)
    return output_path
