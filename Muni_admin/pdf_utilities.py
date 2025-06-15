# Enhanced PDF Utilities and Templates

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak, KeepTogether
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
from reportlab.platypus.tableofcontents import TableOfContents
from reportlab.platypus.doctemplate import PageTemplate, BaseDocTemplate
from reportlab.platypus.frames import Frame
from reportlab.graphics.shapes import Drawing, Line
from reportlab.graphics import renderPDF

class NumberedCanvas:
    """Custom canvas for page numbering and headers/footers"""
    def __init__(self, canvas, doc):
        self.canvas = canvas
        self.doc = doc

    def draw_page_number(self):
        """Draw page number at bottom of page"""
        page_num = self.canvas.getPageNumber()
        text = f"Page {page_num}"
        self.canvas.setFont("Helvetica", 9)
        self.canvas.setFillColor(colors.HexColor('#7f8c8d'))
        self.canvas.drawRightString(A4[0] - 0.75*inch, 0.5*inch, text)

    def draw_header(self, municipality_name):
        """Draw header with municipality name"""
        self.canvas.setFont("Helvetica-Bold", 10)
        self.canvas.setFillColor(colors.HexColor('#2c3e50'))
        self.canvas.drawString(0.75*inch, A4[1] - 0.5*inch, f"Rapport Municipal - {municipality_name}")
        
        # Draw header line
        self.canvas.setStrokeColor(colors.HexColor('#3498db'))
        self.canvas.setLineWidth(2)
        self.canvas.line(0.75*inch, A4[1] - 0.6*inch, A4[0] - 0.75*inch, A4[1] - 0.6*inch)

    def draw_footer(self, generated_date):
        """Draw footer with generation date"""
        self.canvas.setFont("Helvetica", 8)
        self.canvas.setFillColor(colors.HexColor('#95a5a6'))
        self.canvas.drawString(0.75*inch, 0.3*inch, f"Généré le {generated_date}")
        
        # Draw footer line
        self.canvas.setStrokeColor(colors.HexColor('#bdc3c7'))
        self.canvas.setLineWidth(1)
        self.canvas.line(0.75*inch, 0.7*inch, A4[0] - 0.75*inch, 0.7*inch)

def create_enhanced_styles():
    """Create enhanced paragraph styles for the report"""
    styles = getSampleStyleSheet()
    
    # Cover page title
    styles.add(ParagraphStyle(
        name='CoverTitle',
        parent=styles['Heading1'],
        fontSize=28,
        textColor=colors.HexColor('#2c3e50'),
        spaceAfter=30,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    ))
    
    # Cover page subtitle
    styles.add(ParagraphStyle(
        name='CoverSubtitle',
        parent=styles['Heading2'],
        fontSize=18,
        textColor=colors.HexColor('#34495e'),
        spaceAfter=20,
        alignment=TA_CENTER,
        fontName='Helvetica'
    ))
    
    # Section headers
    styles.add(ParagraphStyle(
        name='SectionHeader',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=colors.HexColor('#2c3e50'),
        spaceBefore=30,
        spaceAfter=20,
        fontName='Helvetica-Bold',
        borderWidth=2,
        borderColor=colors.HexColor('#3498db'),
        borderPadding=10,
        backColor=colors.HexColor('#ecf0f1')
    ))
    
    # Subsection headers
    styles.add(ParagraphStyle(
        name='SubsectionHeader',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#34495e'),
        spaceBefore=20,
        spaceAfter=12,
        fontName='Helvetica-Bold',
        leftIndent=10,
        borderWidth=1,
        borderColor=colors.HexColor('#95a5a6'),
        borderPadding=5
    ))
    
    # Enhanced normal text
    styles.add(ParagraphStyle(
        name='EnhancedNormal',
        parent=styles['Normal'],
        fontSize=11,
        textColor=colors.HexColor('#2c3e50'),
        spaceAfter=10,
        fontName='Helvetica',
        leading=14,
        alignment=TA_JUSTIFY
    ))
    
    # Highlighted text
    styles.add(ParagraphStyle(
        name='Highlight',
        parent=styles['Normal'],
        fontSize=11,
        textColor=colors.HexColor('#2c3e50'),
        spaceAfter=8,
        fontName='Helvetica-Bold',
        backColor=colors.HexColor('#fff3cd'),
        borderWidth=1,
        borderColor=colors.HexColor('#ffeaa7'),
        borderPadding=8
    ))
    
    # Statistics text
    styles.add(ParagraphStyle(
        name='Statistics',
        parent=styles['Normal'],
        fontSize=12,
        textColor=colors.HexColor('#2c3e50'),
        spaceAfter=6,
        fontName='Helvetica',
        leftIndent=20,
        bulletIndent=10
    ))
    
    # Caption style
    styles.add(ParagraphStyle(
        name='Caption',
        parent=styles['Normal'],
        fontSize=9,
        textColor=colors.HexColor('#7f8c8d'),
        spaceAfter=15,
        fontName='Helvetica-Oblique',
        alignment=TA_CENTER
    ))
    
    return styles

def create_enhanced_table_style(header_color='#3498db', alt_row_color='#f8f9fa'):
    """Create enhanced table styling"""
    return TableStyle([
        # Header styling
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor(header_color)),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('TOPPADDING', (0, 0), (-1, 0), 12),
        
        # Data rows styling
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('TOPPADDING', (0, 1), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 8),
        
        # Alternating row colors
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor(alt_row_color)]),
        
        # Grid and borders
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#bdc3c7')),
        ('LINEBELOW', (0, 0), (-1, 0), 2, colors.HexColor(header_color)),
        
        # Alignment
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ])

def create_summary_card_table(title, data, color_scheme='blue'):
    """Create a summary card-style table"""
    color_schemes = {
        'blue': {'header': '#3498db', 'bg': '#ebf3fd'},
        'green': {'header': '#2ecc71', 'bg': '#e8f8f5'},
        'orange': {'header': '#f39c12', 'bg': '#fef9e7'},
        'red': {'header': '#e74c3c', 'bg': '#fdedec'},
        'purple': {'header': '#9b59b6', 'bg': '#f4ecf7'}
    }
    
    colors_dict = color_schemes.get(color_scheme, color_schemes['blue'])
    
    # Prepare table data with title row
    table_data = [[title, '']]
    table_data.extend(data)
    
    table = Table(table_data, colWidths=[3*inch, 2*inch])
    table.setStyle(TableStyle([
        # Title row
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor(colors_dict['header'])),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 14),
        ('SPAN', (0, 0), (-1, 0)),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('TOPPADDING', (0, 0), (-1, 0), 15),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 15),
        
        # Data rows
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor(colors_dict['bg'])),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 11),
        ('TOPPADDING', (0, 1), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 10),
        ('LEFTPADDING', (0, 1), (-1, -1), 15),
        ('RIGHTPADDING', (0, 1), (-1, -1), 15),
        
        # Borders
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor(colors_dict['header'])),
        ('LINEBELOW', (0, 0), (-1, 0), 3, colors.HexColor(colors_dict['header'])),
        
        # Alignment
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (1, 1), (1, -1), 'RIGHT'),  # Right align values
    ]))
    
    return table

def create_chart_with_caption(chart_path, caption, width=6*inch, height=4.5*inch):
    """Create a chart with caption for the PDF"""
    elements = []
    
    if os.path.exists(chart_path):
        try:
            # Add chart image
            img = Image(chart_path, width=width, height=height)
            elements.append(img)
            
            # Add caption
            styles = create_enhanced_styles()
            caption_para = Paragraph(caption, styles['Caption'])
            elements.append(caption_para)
            elements.append(Spacer(1, 15))
            
        except Exception as e:
            # Fallback if image can't be loaded
            styles = create_enhanced_styles()
            error_text = f"Erreur lors du chargement du graphique: {os.path.basename(chart_path)}"
            elements.append(Paragraph(error_text, styles['EnhancedNormal']))
            elements.append(Spacer(1, 10))
    
    return elements

def create_kpi_dashboard(summary_data):
    """Create a KPI dashboard section"""
    elements = []
    styles = create_enhanced_styles()
    
    # Title
    elements.append(Paragraph("TABLEAU DE BORD - INDICATEURS CLÉS", styles['SectionHeader']))
    elements.append(Spacer(1, 20))
    
    # Create KPI cards in a 2x2 grid
    kpi_data = [
        [
            create_summary_card_table(
                "SIGNALEMENTS TOTAUX",
                [["Total", str(summary_data['total_issues'])]],
                'blue'
            ),
            create_summary_card_table(
                "TAUX DE RÉSOLUTION",
                [["Pourcentage", f"{summary_data['resolution_rate']}%"]],
                'green'
            )
        ],
        [
            create_summary_card_table(
                "EN ATTENTE",
                [["Nombre", str(summary_data['pending_issues'])]],
                'orange'
            ),
            create_summary_card_table(
                "RÉSOLUS",
                [["Nombre", str(summary_data['resolved_issues'])]],
                'purple'
            )
        ]
    ]
    
    # Create main table for KPI layout
    kpi_table = Table(kpi_data, colWidths=[3.5*inch, 3.5*inch], rowHeights=[1.5*inch, 1.5*inch])
    kpi_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
    ]))
    
    elements.append(kpi_table)
    elements.append(Spacer(1, 30))
    
    return elements

def create_executive_summary_section(report_data):
    """Create an enhanced executive summary section"""
    elements = []
    styles = create_enhanced_styles()
    
    # Section header
    elements.append(Paragraph("RÉSUMÉ EXÉCUTIF", styles['SectionHeader']))
    elements.append(Spacer(1, 20))
    
    # Overview paragraph
    municipality_name = report_data['municipality'].name
    total_issues = report_data['summary']['total_issues']
    resolution_rate = report_data['summary']['resolution_rate']
    
    if report_data['date_from'] and report_data['date_to']:
        period_text = f"du {report_data['date_from'].strftime('%d/%m/%Y')} au {report_data['date_to'].strftime('%d/%m/%Y')}"
    else:
        period_text = "sur l'ensemble des données disponibles"
    
    overview_text = f"""
    Ce rapport présente une analyse complète de l'activité de signalement pour la municipalité de <b>{municipality_name}</b> 
    {period_text}. Au total, <b>{total_issues} signalements</b> ont été analysés, révélant un taux de résolution de <b>{resolution_rate}%</b>.
    """
    
    elements.append(Paragraph(overview_text, styles['EnhancedNormal']))
    elements.append(Spacer(1, 15))
    
    # Key findings
    elements.append(Paragraph("Points Clés", styles['SubsectionHeader']))
    
    key_findings = []
    
    # Problems analysis
    if 'problems' in report_data:
        problems = report_data['problems']
        key_findings.append(f"• <b>{problems['total']} problèmes</b> signalés avec un temps moyen de résolution de <b>{problems['resolution_stats']['avg_resolution_time']} jours</b>")
        
        if problems['priority_analysis']:
            high_priority = problems['priority_analysis']['high']
            if high_priority > 0:
                key_findings.append(f"• <b>{high_priority} problèmes à haute priorité</b> nécessitent une attention immédiate")
    
    # Complaints analysis
    if 'complaints' in report_data:
        complaints = report_data['complaints']
        key_findings.append(f"• <b>{complaints['total']} réclamations</b> déposées avec un temps moyen de réponse de <b>{complaints['response_time_analysis']['average']} jours</b>")
    
    # Performance trends
    if 'performance' in report_data:
        perf = report_data['performance']
        if perf['problems_trend'] > 0:
            key_findings.append(f"• Augmentation de <b>{perf['problems_trend']:+.1f}%</b> des problèmes par rapport à la période précédente")
        elif perf['problems_trend'] < 0:
            key_findings.append(f"• Diminution de <b>{abs(perf['problems_trend']):.1f}%</b> des problèmes par rapport à la période précédente")
    
    for finding in key_findings:
        elements.append(Paragraph(finding, styles['Statistics']))
    
    elements.append(Spacer(1, 20))
    
    # Recommendations
    elements.append(Paragraph("Recommandations", styles['SubsectionHeader']))
    
    recommendations = []
    
    if report_data['summary']['pending_rate'] > 30:
        recommendations.append("• Renforcer les équipes de traitement pour réduire le nombre de signalements en attente")
    
    if 'problems' in report_data and report_data['problems']['resolution_stats']['avg_resolution_time'] > 7:
        recommendations.append("• Optimiser les processus de résolution pour réduire les délais de traitement")
    
    if 'complaints' in report_data and report_data['complaints']['response_time_analysis']['average'] > 5:
        recommendations.append("• Améliorer les délais de réponse aux réclamations citoyennes")
    
    if not recommendations:
        recommendations.append("• Maintenir les bonnes pratiques actuelles de gestion des signalements")
        recommendations.append("• Continuer le suivi régulier des indicateurs de performance")
    
    for recommendation in recommendations:
        elements.append(Paragraph(recommendation, styles['Statistics']))
    
    elements.append(Spacer(1, 30))
    
    return elements

def add_page_break_with_style():
    """Add a styled page break"""
    return PageBreak()

# Additional utility functions for enhanced formatting

def format_number_with_trend(current, previous, suffix=""):
    """Format a number with trend indicator"""
    if previous > 0:
        trend = ((current - previous) / previous) * 100
        trend_symbol = "↗" if trend > 0 else "↘" if trend < 0 else "→"
        return f"{current}{suffix} {trend_symbol} ({trend:+.1f}%)"
    return f"{current}{suffix}"

def create_trend_indicator(value, threshold_good=80, threshold_warning=60):
    """Create a visual trend indicator"""
    if value >= threshold_good:
        return "🟢 Excellent"
    elif value >= threshold_warning:
        return "🟡 Satisfaisant"
    else:
        return "🔴 À améliorer"

def generate_insights_text(report_data):
    """Generate automated insights based on data"""
    insights = []
    
    # Resolution rate insights
    resolution_rate = report_data['summary']['resolution_rate']
    if resolution_rate >= 80:
        insights.append("Le taux de résolution élevé témoigne d'une gestion efficace des signalements.")
    elif resolution_rate >= 60:
        insights.append("Le taux de résolution est satisfaisant mais peut être amélioré.")
    else:
        insights.append("Le taux de résolution nécessite une attention particulière.")
    
    # Volume insights
    total_issues = report_data['summary']['total_issues']
    if total_issues > 100:
        insights.append("Le volume important de signalements indique une forte participation citoyenne.")
    elif total_issues > 50:
        insights.append("Le volume modéré de signalements suggère un engagement citoyen régulier.")
    else:
        insights.append("Le volume de signalements est relativement faible.")
    
    # Performance insights
    if 'performance' in report_data:
        perf = report_data['performance']
        if perf['problems_trend'] < -10:
            insights.append("La diminution significative des problèmes signalés est encourageante.")
        elif perf['problems_trend'] > 10:
            insights.append("L'augmentation des problèmes signalés nécessite une analyse approfondie.")
    
    return insights

