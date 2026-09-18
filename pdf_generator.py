import os
from datetime import datetime, timezone, timedelta
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as RLImage
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

IST = timezone(timedelta(hours=5, minutes=30))

def generate_attendance_pdf(output_path, college_name, program_name, dept_name, year_name, session_type, date_str, teacher_name, hod_name, total_count, absent_students, day_type='working', occasion_name='', section='A'):
    """
    Generates a clean, official attendance report in PDF format with accurate real-time timestamp in IST,
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

    # Current accurate timestamp in Indian Standard Time (IST, UTC+05:30)
    current_time_str = datetime.now(IST).strftime("%A, %d-%b-%Y at %I:%M:%S %p IST")

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
            r_num = str(s.get('roll_number') or 'N/A')
            s_name = str(s.get('name') or 'Student')
            f_name = str(s.get('father_name') or 'Parent / Guardian')
            f_phone = str(s.get('father_phone') or 'N/A')
            phone_disp = f"+91 {f_phone}" if f_phone != 'N/A' and not f_phone.startswith("+91") else f_phone
            table_rows.append([
                Paragraph(str(idx), cell_style),
                Paragraph(f"<b>{r_num}</b>", cell_style),
                Paragraph(s_name, cell_style),
                Paragraph(f_name, cell_style),
                Paragraph(phone_disp, cell_style),
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


def generate_parent_student_dossier_pdf(output_path, college_name, student_info, records, stats, teacher_name="Class Teacher", hod_name="Head of Department"):
    """
    Generates an official Student Attendance & Condonation Dossier (Parent Copy)
    featuring complete profile details, session statistics, eligibility verdict,
    detailed daily attendance table, and signatures.
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

    current_time_str = datetime.now(IST).strftime("%A, %d-%b-%Y at %I:%M:%S %p IST")

    # Header Box
    title_style = ParagraphStyle('DossierTitle', parent=styles['Heading1'], fontName='Helvetica-Bold', fontSize=14, leading=17, alignment=1, textColor=colors.HexColor('#0F2C59'))
    autonomous_style = ParagraphStyle('DossierAuto', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=9, leading=11, alignment=1, textColor=colors.HexColor('#991B1B'))
    sub_style = ParagraphStyle('DossierSub', parent=styles['Normal'], fontName='Helvetica', fontSize=7.5, leading=9.5, alignment=1, textColor=colors.HexColor('#2D3748'))
    cell_style = ParagraphStyle('DCell', parent=styles['Normal'], fontName='Helvetica', fontSize=8, leading=10)
    cell_bold = ParagraphStyle('DCellB', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=8, leading=10)

    # Timestamp & Code
    top_table = Table([
        [
            Paragraph(f"<b>System Generated:</b> {current_time_str}", ParagraphStyle('TLeft', parent=styles['Normal'], fontName='Helvetica', fontSize=7.5, leading=9, textColor=colors.HexColor('#4A5568'))),
            Paragraph("<font color='#B7791F'><b>College Code: SRSR</b></font>", ParagraphStyle('TRight', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=7.5, leading=9, alignment=2, textColor=colors.HexColor('#B7791F')))
        ]
    ], colWidths=[380, 143])
    top_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2),
        ('TOPPADDING', (0,0), (-1,-1), 0),
        ('LEFTPADDING', (0,0), (-1,-1), 0),
        ('RIGHTPADDING', (0,0), (-1,-1), 0),
    ]))
    story.append(top_table)
    story.append(Spacer(1, 3))

    # Logos & Header
    college_logo_path = os.path.join(os.path.dirname(__file__), "static", "images", "college_logo.png")
    naac_logo_path = os.path.join(os.path.dirname(__file__), "static", "images", "naac_logo.png")
    left_logo = RLImage(college_logo_path, width=54, height=52) if os.path.exists(college_logo_path) else Paragraph("", cell_style)
    right_logo = RLImage(naac_logo_path, width=64, height=48) if os.path.exists(naac_logo_path) else Paragraph("", cell_style)

    center_text = [
        Paragraph(college_name.upper(), title_style),
        Spacer(1, 2),
        Paragraph("(AN AUTONOMOUS INSTITUTION)", autonomous_style),
        Spacer(1, 1),
        Paragraph("Approved by AICTE, New Delhi & Affiliated to JNTUA, Ananthapuramu", sub_style),
        Paragraph("Rayachoty, Annamayya District, Andhra Pradesh - 516269", sub_style),
    ]

    header_table = Table([[left_logo, center_text, right_logo]], colWidths=[65, 393, 65])
    header_table.setStyle(TableStyle([
        ('ALIGN', (0,0), (0,0), 'LEFT'),
        ('ALIGN', (1,0), (1,0), 'CENTER'),
        ('ALIGN', (2,0), (2,0), 'RIGHT'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('TOPPADDING', (0,0), (-1,-1), 0),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 4))

    # Document Banner
    banner_table = Table([[Paragraph("<font color='#ffffff'><b>PARENT INQUIRY DOSSIER - INDIVIDUAL STUDENT ATTENDANCE CERTIFICATE</b></font>", ParagraphStyle('Banner', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=9, leading=11, alignment=1, textColor=colors.white))]], colWidths=[523])
    banner_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#0F2C59')),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
    ]))
    story.append(banner_table)
    story.append(Spacer(1, 6))

    # Student Profile Matrix
    st_name = str(student_info.get('name') or 'N/A')
    st_roll = str(student_info.get('roll_number') or 'N/A')
    st_prog = str(student_info.get('prog_name') or student_info.get('prog_code') or 'B.Tech')
    st_dept = str(student_info.get('dept_name') or student_info.get('dept_code') or 'Engineering')
    st_year = str(student_info.get('year_name') or 'Academic Year')
    st_sec = str(student_info.get('section') or 'A')
    st_father = str(student_info.get('father_name') or 'Parent / Guardian')
    st_phone = str(student_info.get('father_phone') or 'N/A')

    prof_data = [
        [
            Paragraph(f"<b>Student Name:</b> {st_name}", cell_style),
            Paragraph(f"<b>Roll Number:</b> <font color='#0F2C59'><b>{st_roll}</b></font>", cell_style),
        ],
        [
            Paragraph(f"<b>Program / Degree:</b> {st_prog}", cell_style),
            Paragraph(f"<b>Department / Branch:</b> {st_dept}", cell_style),
        ],
        [
            Paragraph(f"<b>Academic Year & Sec:</b> {st_year} (Section {st_sec})", cell_style),
            Paragraph(f"<b>Father / Guardian:</b> {st_father} ({st_phone})", cell_style),
        ]
    ]
    prof_table = Table(prof_data, colWidths=[261, 262])
    prof_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#F8FAFC')),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#CBD5E1')),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E2E8F0')),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(prof_table)
    story.append(Spacer(1, 6))

    # Metrics Summary Box
    tot_sessions = stats.get('total_sessions', 0)
    pres_sessions = stats.get('present_sessions', 0)
    abs_sessions = stats.get('absent_sessions', 0)
    pct = stats.get('percentage', 0.0)

    verdict = "<font color='#166534'><b>ELIGIBLE FOR SEM EXAMS (&ge; 75%)</b></font>" if pct >= 75.0 else ("<font color='#B45309'><b>CONDONATION RANGE (65% - 74.9%)</b></font>" if pct >= 65.0 else "<font color='#B91C1C'><b>CRITICAL ATTENDANCE SHORTAGE (&lt; 65%)</b></font>")

    metric_head = ParagraphStyle('MH', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=7.5, leading=9, alignment=1, textColor=colors.HexColor('#475569'))
    metric_val = ParagraphStyle('MV', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=12, leading=14, alignment=1)

    stat_data = [
        [
            Paragraph("TOTAL SESSIONS", metric_head),
            Paragraph("SESSIONS ATTENDED", metric_head),
            Paragraph("SESSIONS MISSED", metric_head),
            Paragraph("ATTENDANCE %", metric_head),
        ],
        [
            Paragraph(f"<b>{tot_sessions}</b>", ParagraphStyle('M1', parent=metric_val, textColor=colors.HexColor('#0F2C59'))),
            Paragraph(f"<b>{pres_sessions}</b>", ParagraphStyle('M2', parent=metric_val, textColor=colors.HexColor('#166534'))),
            Paragraph(f"<b>{abs_sessions}</b>", ParagraphStyle('M3', parent=metric_val, textColor=colors.HexColor('#DC2626'))),
            Paragraph(f"<b>{pct}%</b>", ParagraphStyle('M4', parent=metric_val, textColor=colors.HexColor('#B45309'))),
        ],
        [
            Paragraph(f"<b>Autonomous University Eligibility Status:</b> {verdict}", ParagraphStyle('Vrd', parent=styles['Normal'], fontName='Helvetica', fontSize=8, leading=10, alignment=1)),
            "", "", ""
        ]
    ]
    stat_table = Table(stat_data, colWidths=[130, 131, 131, 131])
    stat_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#F1F5F9')),
        ('BACKGROUND', (0,1), (-1,1), colors.HexColor('#FFFFFF')),
        ('BACKGROUND', (0,2), (-1,2), colors.HexColor('#FEF3C7')),
        ('SPAN', (0,2), (3,2)),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#CBD5E1')),
        ('INNERGRID', (0,0), (-1,1), 0.5, colors.HexColor('#E2E8F0')),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
    ]))
    story.append(stat_table)
    story.append(Spacer(1, 6))

    # Daily Records Table
    story.append(Paragraph("<b>DETAILED SESSION-WISE ATTENDANCE LOG:</b>", ParagraphStyle('RecH', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=8, leading=10, textColor=colors.HexColor('#0F2C59'))))
    story.append(Spacer(1, 3))

    rec_rows = [
        [
            Paragraph("<b>#</b>", cell_bold),
            Paragraph("<b>Date</b>", cell_bold),
            Paragraph("<b>Day</b>", cell_bold),
            Paragraph("<b>Morning Session</b>", cell_bold),
            Paragraph("<b>Afternoon Session</b>", cell_bold),
            Paragraph("<b>Day Result</b>", cell_bold)
        ]
    ]

    for idx, r in enumerate(records, start=1):
        m_stat = r.get('morning', 'Not Marked')
        a_stat = r.get('afternoon', 'Not Marked')
        
        m_disp = f"<font color='#166534'><b>Present</b></font>" if m_stat == 'Present' else (f"<font color='#DC2626'><b>Absent</b></font>" if m_stat == 'Absent' else f"<font color='#6B7280'>{m_stat}</font>")
        a_disp = f"<font color='#166534'><b>Present</b></font>" if a_stat == 'Present' else (f"<font color='#DC2626'><b>Absent</b></font>" if a_stat == 'Absent' else f"<font color='#6B7280'>{a_stat}</font>")
        
        summary = r.get('summary', 'Normal')
        sum_disp = f"<font color='#166534'>Full Day Present</font>" if summary == 'Full Day Present' else (f"<font color='#DC2626'>Full Day Absent</font>" if summary == 'Full Day Absent' else f"<font color='#B45309'>{summary}</font>")

        rec_rows.append([
            Paragraph(str(idx), cell_style),
            Paragraph(str(r.get('date', '-')), cell_style),
            Paragraph(str(r.get('day_name', '-')), cell_style),
            Paragraph(m_disp, cell_style),
            Paragraph(a_disp, cell_style),
            Paragraph(sum_disp, cell_style),
        ])

    rec_table = Table(rec_rows, colWidths=[25, 80, 80, 110, 110, 118])
    rec_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#0F2C59')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E1')),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#F8FAFC')]),
        ('TOPPADDING', (0,0), (-1,-1), 2.5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2.5),
        ('ALIGN', (0,0), (0,-1), 'CENTER'),
        ('ALIGN', (3,0), (-1,-1), 'CENTER'),
    ]))
    story.append(rec_table)
    story.append(Spacer(1, 15))

    # Signatures
    sig_data = [
        [
            Paragraph(f"<b>Class Teacher</b><br/><br/>({teacher_name})", cell_style),
            Paragraph(f"<b>Head of Department (HOD)</b><br/><br/>({hod_name})", cell_style),
            Paragraph("<b>Parent / Guardian Signature</b><br/><br/>________________________", cell_style),
            Paragraph("<b>Principal / Director</b><br/><br/>SSITS (Autonomous)", cell_style),
        ]
    ]
    sig_table = Table(sig_data, colWidths=[130, 131, 131, 131])
    sig_table.setStyle(TableStyle([
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'BOTTOM')
    ]))
    story.append(sig_table)

    doc.build(story)
    return output_path


def generate_cumulative_monthly_attendance_pdf(output_path, college_name, program_name, dept_name, dept_code, year_name, section, month_name, total_working_days, report_data, teacher_name="Class Teacher", hod_name="Head of Department"):
    """
    Generates an official institutional Monthly Cumulative Attendance Report in PDF format.
    Includes college branding, NAAC B+ accreditation, academic metrics, eligibility status, and official signatures.
    """
    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        rightMargin=28,
        leftMargin=28,
        topMargin=22,
        bottomMargin=22
    )

    story = []
    styles = getSampleStyleSheet()
    current_time_str = datetime.now(IST).strftime("%d-%b-%Y at %I:%M %p IST")

    # Typography styles
    title_style = ParagraphStyle(
        'CumTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=13.5,
        leading=16,
        alignment=1,
        textColor=colors.HexColor('#0F2C59')
    )

    autonomous_style = ParagraphStyle(
        'CumAutonomous',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8.5,
        leading=11,
        alignment=1,
        textColor=colors.HexColor('#991B1B')
    )

    affiliation_style = ParagraphStyle(
        'CumAffiliation',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=7.5,
        leading=9.5,
        alignment=1,
        textColor=colors.HexColor('#334155')
    )

    report_heading_style = ParagraphStyle(
        'CumHeading',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=11,
        leading=13,
        alignment=1,
        textColor=colors.HexColor('#1E3A8A')
    )

    cell_style = ParagraphStyle(
        'CumCell',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=7.5,
        leading=9.5,
        alignment=0,
        textColor=colors.HexColor('#1E293B')
    )

    cell_bold_style = ParagraphStyle(
        'CumCellBold',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=7.5,
        leading=9.5,
        alignment=0,
        textColor=colors.HexColor('#0F172A')
    )

    cell_center_style = ParagraphStyle(
        'CumCellCenter',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=7.5,
        leading=9.5,
        alignment=1,
        textColor=colors.HexColor('#1E293B')
    )

    header_cell_style = ParagraphStyle(
        'CumHeaderCell',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=7.5,
        leading=9.5,
        alignment=1,
        textColor=colors.white
    )

    # 1. Header Banner
    logo_path = os.path.join(os.path.dirname(__file__), 'static', 'images', 'college_logo.png')
    naac_path = os.path.join(os.path.dirname(__file__), 'static', 'images', 'naac_logo.png')

    logo_img = RLImage(logo_path, width=46, height=46) if os.path.exists(logo_path) else Paragraph("", styles['Normal'])
    naac_img = RLImage(naac_path, width=46, height=46) if os.path.exists(naac_path) else Paragraph("", styles['Normal'])

    inst_header = [
        Paragraph(f"<b>{college_name.upper()}</b>", title_style),
        Spacer(1, 1),
        Paragraph("<b>(AN AUTONOMOUS INSTITUTION)</b>", autonomous_style),
        Paragraph("Approved by AICTE, New Delhi | Affiliated to JNTUA, Ananthapuramu | Accredited by NAAC with 'B+' Grade", affiliation_style),
        Paragraph("Rayachoty Road, Rayachoty, Y.S.R. Kadapa District, Andhra Pradesh - 516269", affiliation_style),
    ]

    header_table = Table([[logo_img, inst_header, naac_img]], colWidths=[50, 439, 50])
    header_table.setStyle(TableStyle([
        ('ALIGN', (0,0), (0,-1), 'CENTER'),
        ('ALIGN', (2,0), (2,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 1),
        ('TOPPADDING', (0,0), (-1,-1), 1),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 6))

    # Report Title
    story.append(Paragraph(f"<b>OFFICIAL MONTHLY CUMULATIVE ATTENDANCE STATEMENT &ndash; {month_name.upper()}</b>", report_heading_style))
    story.append(Spacer(1, 6))

    # Class & Metadata info table
    info_data = [
        [
            Paragraph(f"<b>Program:</b> {program_name}", cell_style),
            Paragraph(f"<b>Department:</b> {dept_name} ({dept_code})", cell_style),
            Paragraph(f"<b>Academic Year:</b> {year_name} (Sec {section})", cell_style),
        ],
        [
            Paragraph(f"<b>Class Teacher:</b> {teacher_name}", cell_style),
            Paragraph(f"<b>Head of Dept (HOD):</b> {hod_name}", cell_style),
            Paragraph(f"<b>Generated At:</b> {current_time_str}", cell_style),
        ]
    ]
    info_table = Table(info_data, colWidths=[180, 190, 169])
    info_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#F1F5F9')),
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E1')),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E2E8F0')),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(info_table)
    story.append(Spacer(1, 6))

    # Calculate Summary Metrics
    total_students = len(report_data)
    eligible_count = sum(1 for r in report_data if r.get('percentage', 0) >= 75.0)
    condonation_count = sum(1 for r in report_data if 65.0 <= r.get('percentage', 0) < 75.0)
    detained_count = sum(1 for r in report_data if r.get('percentage', 0) < 65.0)
    avg_pct = round(sum(r.get('percentage', 0) for r in report_data) / total_students, 1) if total_students > 0 else 0

    stats_data = [
        [
            Paragraph("<b>Total Enrolled</b>", cell_center_style),
            Paragraph("<b>Working Days</b>", cell_center_style),
            Paragraph("<b>Class Average</b>", cell_center_style),
            Paragraph("<b>Eligible (&ge;75%)</b>", cell_center_style),
            Paragraph("<b>Condonation (65-74%)</b>", cell_center_style),
            Paragraph("<b>Detained (&lt;65%)</b>", cell_center_style),
        ],
        [
            Paragraph(f"<b>{total_students}</b>", cell_center_style),
            Paragraph(f"<b>{total_working_days}</b>", cell_center_style),
            Paragraph(f"<b>{avg_pct}%</b>", cell_center_style),
            Paragraph(f"<font color='#16A34A'><b>{eligible_count}</b></font>", cell_center_style),
            Paragraph(f"<font color='#D97706'><b>{condonation_count}</b></font>", cell_center_style),
            Paragraph(f"<font color='#DC2626'><b>{detained_count}</b></font>", cell_center_style),
        ]
    ]
    stats_table = Table(stats_data, colWidths=[85, 90, 90, 92, 92, 90])
    stats_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#E2E8F0')),
        ('BACKGROUND', (0,1), (-1,1), colors.HexColor('#F8FAFC')),
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor('#94A3B8')),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E1')),
        ('TOPPADDING', (0,0), (-1,-1), 2),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2),
    ]))
    story.append(stats_table)
    story.append(Spacer(1, 8))

    # Student Roster Table
    roster_rows = [
        [
            Paragraph("S.NO", header_cell_style),
            Paragraph("ROLL NUMBER", header_cell_style),
            Paragraph("STUDENT NAME", header_cell_style),
            Paragraph("FATHER NAME", header_cell_style),
            Paragraph("WORKING DAYS", header_cell_style),
            Paragraph("ATTENDED", header_cell_style),
            Paragraph("ABSENT", header_cell_style),
            Paragraph("ATTN %", header_cell_style),
            Paragraph("ACADEMIC STATUS", header_cell_style),
        ]
    ]

    for idx, r in enumerate(report_data, 1):
        pct = r.get('percentage', 0)
        if pct >= 75.0:
            status_text = "<font color='#15803D'><b>Eligible</b></font>"
            pct_text = f"<font color='#15803D'><b>{pct}%</b></font>"
        elif pct >= 65.0:
            status_text = "<font color='#B45309'><b>Condonation</b></font>"
            pct_text = f"<font color='#B45309'><b>{pct}%</b></font>"
        else:
            status_text = "<font color='#B91C1C'><b>Shortage / Detained</b></font>"
            pct_text = f"<font color='#B91C1C'><b>{pct}%</b></font>"

        roster_rows.append([
            Paragraph(str(idx), cell_center_style),
            Paragraph(f"<b>{r.get('roll_number', '-')}</b>", cell_style),
            Paragraph(r.get('name', '-'), cell_bold_style),
            Paragraph(r.get('father_name', '-'), cell_style),
            Paragraph(str(r.get('total_working_days', total_working_days)), cell_center_style),
            Paragraph(f"<font color='#16A34A'><b>{r.get('attended_days', 0)}</b></font>", cell_center_style),
            Paragraph(f"<font color='#DC2626'><b>{r.get('absent_days', 0)}</b></font>", cell_center_style),
            Paragraph(pct_text, cell_center_style),
            Paragraph(status_text, cell_center_style),
        ])

    roster_table = Table(roster_rows, colWidths=[24, 66, 115, 95, 52, 46, 42, 46, 53], repeatRows=1)
    roster_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#0F2C59')),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E1')),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#F8FAFC')]),
        ('TOPPADDING', (0,0), (-1,-1), 2),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2),
        ('LEFTPADDING', (0,0), (-1,-1), 3),
        ('RIGHTPADDING', (0,0), (-1,-1), 3),
        ('ALIGN', (0,0), (-1,0), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    story.append(roster_table)
    story.append(Spacer(1, 14))

    # Institutional Signatures Table
    sig_data = [
        [
            Paragraph(f"<b>Class Teacher</b><br/><br/>({teacher_name})", cell_center_style),
            Paragraph(f"<b>Head of Department (HOD)</b><br/><br/>({hod_name})", cell_center_style),
            Paragraph("<b>Dean / Academic In-Charge</b><br/><br/>SSITS (Autonomous)", cell_center_style),
            Paragraph("<b>Principal / Director</b><br/><br/>Sri Sai Institute of Tech & Science", cell_center_style),
        ]
    ]
    sig_table = Table(sig_data, colWidths=[134, 135, 135, 135])
    sig_table.setStyle(TableStyle([
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'BOTTOM'),
        ('LINEABOVE', (0,0), (-1,-1), 0.5, colors.HexColor('#94A3B8')),
        ('TOPPADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(sig_table)

    doc.build(story)
    return output_path

