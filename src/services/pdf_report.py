"""
SimuTarget PDF Report Generator
Pro: Clean, professional summary report
Business: Detailed infographic with charts and demographics
"""

import io
import os
import json
import math
from datetime import datetime

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm, cm
from reportlab.lib.colors import HexColor, white, black, Color
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, Image, KeepTogether
)
from reportlab.pdfgen import canvas
from reportlab.graphics.shapes import Drawing, Rect, String, Circle, Line, Wedge
from reportlab.graphics.charts.piecharts import Pie
from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics import renderPDF
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# ─── REGISTER TTF FONTS (Turkish character support) ───────
import platform

def _find_font_dir():
    candidates = [
        os.path.join(os.path.dirname(__file__), "fonts"),
        "/usr/share/fonts/truetype/dejavu",
        "C:/Windows/Fonts",
    ]
    for d in candidates:
        if os.path.isfile(os.path.join(d, "DejaVuSans.ttf")):
            return d
    return None

_FONT_DIR = _find_font_dir()
_FONT_REGISTERED = False

def _register_fonts():
    global _FONT_REGISTERED
    if _FONT_REGISTERED:
        return
    if not _FONT_DIR:
        print("Font warning: DejaVuSans not found. Falling back to Helvetica.")
        return
    try:
        pdfmetrics.registerFont(TTFont('SimuFont', f'{_FONT_DIR}/DejaVuSans.ttf'))
        pdfmetrics.registerFont(TTFont('SimuFont-Bold', f'{_FONT_DIR}/DejaVuSans-Bold.ttf'))
        pdfmetrics.registerFont(TTFont('SimuFont-Oblique', f'{_FONT_DIR}/DejaVuSans-Oblique.ttf'))
        pdfmetrics.registerFont(TTFont('SimuFont-BoldOblique', f'{_FONT_DIR}/DejaVuSans-BoldOblique.ttf'))
        from reportlab.pdfbase.pdfmetrics import registerFontFamily
        registerFontFamily('SimuFont',
                           normal='SimuFont',
                           bold='SimuFont-Bold',
                           italic='SimuFont-Oblique',
                           boldItalic='SimuFont-BoldOblique')
        _FONT_REGISTERED = True
    except Exception as e:
        print(f"Font registration warning: {e}. Falling back to Helvetica.")
# Register on import
_register_fonts()

FONT = 'SimuFont' if _FONT_REGISTERED else 'Helvetica'
FONT_BOLD = 'SimuFont-Bold' if _FONT_REGISTERED else 'Helvetica-Bold'


# ─── COLORS ────────────────────────────────────────────────
BRAND_CYAN = HexColor("#06B6D4")
BRAND_PURPLE = HexColor("#8B5CF6")
BRAND_DARK = HexColor("#0F172A")
BRAND_DARK_2 = HexColor("#1E293B")
BRAND_DARK_3 = HexColor("#334155")
TEXT_PRIMARY = HexColor("#F1F5F9")
TEXT_SECONDARY = HexColor("#94A3B8")
TEXT_MUTED = HexColor("#64748B")
SUCCESS_GREEN = HexColor("#10B981")
DANGER_RED = HexColor("#EF4444")
WARNING_AMBER = HexColor("#F59E0B")
WHITE = HexColor("#FFFFFF")
CHART_COLORS = [
    HexColor("#06B6D4"), HexColor("#8B5CF6"), HexColor("#10B981"),
    HexColor("#F59E0B"), HexColor("#EF4444"), HexColor("#EC4899"),
    HexColor("#3B82F6"), HexColor("#14B8A6"),
]

# Light theme colors for PDF (dark bg doesn't print well)
BG_WHITE = HexColor("#FFFFFF")
BG_LIGHT = HexColor("#F8FAFC")
BG_GRAY = HexColor("#F1F5F9")
BG_BORDER = HexColor("#E2E8F0")
TEXT_DARK = HexColor("#0F172A")
TEXT_BODY = HexColor("#334155")
TEXT_LIGHT = HexColor("#64748B")


def _get_styles():
    """Create custom paragraph styles for reports."""
    styles = getSampleStyleSheet()
    
    styles.add(ParagraphStyle(
        name='ReportTitle',
        fontName=FONT_BOLD,
        fontSize=28,
        leading=34,
        textColor=TEXT_DARK,
        spaceAfter=4,
    ))
    styles.add(ParagraphStyle(
        name='ReportSubtitle',
        fontName=FONT,
        fontSize=12,
        leading=16,
        textColor=TEXT_LIGHT,
        spaceAfter=24,
    ))
    styles.add(ParagraphStyle(
        name='SectionTitle',
        fontName=FONT_BOLD,
        fontSize=16,
        leading=22,
        textColor=TEXT_DARK,
        spaceBefore=20,
        spaceAfter=10,
    ))
    styles.add(ParagraphStyle(
        name='SubSection',
        fontName=FONT_BOLD,
        fontSize=12,
        leading=16,
        textColor=TEXT_BODY,
        spaceBefore=12,
        spaceAfter=6,
    ))
    styles.add(ParagraphStyle(
        name='BodyText2',
        fontName=FONT,
        fontSize=10,
        leading=14,
        textColor=TEXT_BODY,
        spaceAfter=6,
    ))
    styles.add(ParagraphStyle(
        name='SmallText',
        fontName=FONT,
        fontSize=8,
        leading=10,
        textColor=TEXT_LIGHT,
    ))
    styles.add(ParagraphStyle(
        name='MetricValue',
        fontName=FONT_BOLD,
        fontSize=24,
        leading=28,
        textColor=BRAND_CYAN,
        alignment=TA_CENTER,
    ))
    styles.add(ParagraphStyle(
        name='MetricLabel',
        fontName=FONT,
        fontSize=9,
        leading=12,
        textColor=TEXT_LIGHT,
        alignment=TA_CENTER,
    ))
    styles.add(ParagraphStyle(
        name='FooterText',
        fontName=FONT,
        fontSize=7,
        leading=10,
        textColor=TEXT_LIGHT,
        alignment=TA_CENTER,
    ))
    
    return styles


def _header_footer(canvas_obj, doc, report_data, lang="en"):
    """Draw header and footer on each page."""
    canvas_obj.saveState()
    width, height = A4
    
    # Header line
    canvas_obj.setStrokeColor(BRAND_CYAN)
    canvas_obj.setLineWidth(2)
    canvas_obj.line(20*mm, height - 15*mm, width - 20*mm, height - 15*mm)
    
    # Brand name
    canvas_obj.setFont(FONT_BOLD, 10)
    canvas_obj.setFillColor(BRAND_CYAN)
    canvas_obj.drawString(20*mm, height - 12*mm, "SimuTarget.ai")
    
    # Report type
    canvas_obj.setFont(FONT, 8)
    canvas_obj.setFillColor(TEXT_LIGHT)
    report_type_text = "Campaign Analysis Report" if lang == "en" else "Kampanya Analiz Raporu"
    canvas_obj.drawRightString(width - 20*mm, height - 12*mm, report_type_text)
    
    # Footer
    canvas_obj.setStrokeColor(BG_BORDER)
    canvas_obj.setLineWidth(0.5)
    canvas_obj.line(20*mm, 15*mm, width - 20*mm, 15*mm)
    
    canvas_obj.setFont(FONT, 7)
    canvas_obj.setFillColor(TEXT_LIGHT)
    
    generated = "Generated" if lang == "en" else "Oluşturulma"
    date_str = datetime.now().strftime("%Y-%m-%d %H:%M")
    canvas_obj.drawString(20*mm, 10*mm, f"{generated}: {date_str}")
    
    confidential = "Confidential — AI-Powered Market Simulation" if lang == "en" else "Gizli — AI Destekli Pazar Simülasyonu"
    canvas_obj.drawCentredString(width / 2, 10*mm, confidential)
    
    page_num = f"{canvas_obj.getPageNumber()}"
    canvas_obj.drawRightString(width - 20*mm, 10*mm, page_num)
    
    canvas_obj.restoreState()


def _build_metric_card(value, label, color=BRAND_CYAN):
    """Create a metric display as a table cell."""
    return Table(
        [[Paragraph(f'<font color="#{color.hexval()[2:]}">{value}</font>', 
                    ParagraphStyle('mv', fontName=FONT_BOLD, fontSize=22, alignment=TA_CENTER, textColor=color, leading=26))],
         [Paragraph(label, ParagraphStyle('ml', fontName=FONT, fontSize=9, alignment=TA_CENTER, textColor=TEXT_LIGHT, leading=12))]],
        colWidths=[None],
        style=TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), BG_LIGHT),
            ('BOX', (0, 0), (-1, -1), 0.5, BG_BORDER),
            ('ROUNDEDCORNERS', [6, 6, 6, 6]),
            ('TOPPADDING', (0, 0), (-1, 0), 14),
            ('BOTTOMPADDING', (0, -1), (-1, -1), 14),
            ('LEFTPADDING', (0, 0), (-1, -1), 10),
            ('RIGHTPADDING', (0, 0), (-1, -1), 10),
        ])
    )


def _create_pie_drawing(data_dict, width=200, height=160, colors=None):
    """Create a pie chart drawing."""
    d = Drawing(width, height)
    
    labels = list(data_dict.keys())
    values = list(data_dict.values())
    
    if not any(v > 0 for v in values):
        return d
    
    pie = Pie()
    pie.x = width // 2 - 55
    pie.y = 15
    pie.width = 110
    pie.height = 110
    pie.data = values
    pie.labels = [f"{l}\n{v}%" if v > 0 else "" for l, v in zip(labels, values)]
    pie.sideLabels = True
    pie.slices.strokeWidth = 1
    pie.slices.strokeColor = WHITE
    
    if colors is None:
        colors = CHART_COLORS
    for i in range(len(values)):
        pie.slices[i].fillColor = colors[i % len(colors)]
        pie.slices[i].fontName = FONT
        pie.slices[i].fontSize = 8
    
    d.add(pie)
    return d


def _create_bar_drawing(data_dict, width=260, height=160, color=BRAND_CYAN):
    """Create a horizontal bar chart as a table (more reliable than ReportLab charts)."""
    d = Drawing(width, height)
    
    labels = list(data_dict.keys())
    values = list(data_dict.values())
    max_val = max(values) if values and max(values) > 0 else 1
    
    bar_height = 14
    gap = 6
    start_y = height - 20
    label_width = 80
    bar_area_width = width - label_width - 30
    
    for i, (label, val) in enumerate(zip(labels, values)):
        y = start_y - i * (bar_height + gap)
        
        # Label
        d.add(String(0, y + 2, label, fontName=FONT, fontSize=8, fillColor=TEXT_BODY))
        
        # Background bar
        d.add(Rect(label_width, y - 2, bar_area_width, bar_height,
                    fillColor=BG_GRAY, strokeColor=None))
        
        # Value bar
        bar_width = (val / max_val) * bar_area_width if max_val > 0 else 0
        if bar_width > 0:
            d.add(Rect(label_width, y - 2, bar_width, bar_height,
                        fillColor=color, strokeColor=None))
        
        # Value text
        d.add(String(label_width + bar_area_width + 4, y + 2, str(val),
                      fontName=FONT_BOLD, fontSize=8, fillColor=TEXT_BODY))
    
    return d


def _localized(key, lang="en"):
    """Simple localization helper."""
    translations = {
        "campaign_report": {"en": "Campaign Analysis Report", "tr": "Kampanya Analiz Raporu"},
        "executive_summary": {"en": "Executive Summary", "tr": "Yönetici Özeti"},
        "campaign_details": {"en": "Campaign Details", "tr": "Kampanya Detayları"},
        "campaign_name": {"en": "Campaign Name", "tr": "Kampanya Adı"},
        "campaign_content": {"en": "Campaign Content", "tr": "Kampanya İçeriği"},
        "test_type": {"en": "Test Type", "tr": "Test Türü"},
        "region": {"en": "Region", "tr": "Bölge"},
        "test_date": {"en": "Test Date", "tr": "Test Tarihi"},
        "key_metrics": {"en": "Key Metrics", "tr": "Temel Metrikler"},
        "approval_rate": {"en": "Approval Rate", "tr": "Onay Oranı"},
        "avg_confidence": {"en": "Avg. Confidence", "tr": "Ort. Güven"},
        "total_personas": {"en": "Total Personas", "tr": "Toplam Persona"},
        "yes_votes": {"en": "Yes Votes", "tr": "Evet Oyları"},
        "no_votes": {"en": "No Votes", "tr": "Hayır Oyları"},
        "results_overview": {"en": "Results Overview", "tr": "Sonuçlara Genel Bakış"},
        "demographic_analysis": {"en": "Demographic Analysis", "tr": "Demografik Analiz"},
        "by_gender": {"en": "By Gender", "tr": "Cinsiyete Göre"},
        "by_age_group": {"en": "By Age Group", "tr": "Yaş Grubuna Göre"},
        "by_income_level": {"en": "By Income Level", "tr": "Gelir Düzeyine Göre"},
        "detailed_responses": {"en": "Detailed Persona Responses", "tr": "Detaylı Persona Yanıtları"},
        "persona": {"en": "Persona", "tr": "Persona"},
        "age": {"en": "Age", "tr": "Yaş"},
        "gender": {"en": "Gender", "tr": "Cinsiyet"},
        "city": {"en": "City", "tr": "Şehir"},
        "occupation": {"en": "Occupation", "tr": "Meslek"},
        "decision": {"en": "Decision", "tr": "Karar"},
        "confidence": {"en": "Confidence", "tr": "Güven"},
        "reasoning": {"en": "Reasoning", "tr": "Gerekçe"},
        "yes": {"en": "Yes", "tr": "Evet"},
        "no": {"en": "No", "tr": "Hayır"},
        "single_test": {"en": "Single Campaign Test", "tr": "Tekli Kampanya Testi"},
        "ab_compare": {"en": "A/B Comparison", "tr": "A/B Karşılaştırma"},
        "multi_compare": {"en": "Multi Comparison", "tr": "Çoklu Karşılaştırma"},
        "option_a": {"en": "Option A", "tr": "Seçenek A"},
        "option_b": {"en": "Option B", "tr": "Seçenek B"},
        "neither": {"en": "Neither", "tr": "Hiçbiri"},
        "vote_distribution": {"en": "Vote Distribution", "tr": "Oy Dağılımı"},
        "choice": {"en": "Choice", "tr": "Tercih"},
        "insights": {"en": "Key Insights", "tr": "Önemli Bulgular"},
        "recommendation": {"en": "Recommendation", "tr": "Öneri"},
        "confidence_distribution": {"en": "Confidence Distribution", "tr": "Güven Dağılımı"},
        "high_confidence": {"en": "High (8-10)", "tr": "Yüksek (8-10)"},
        "medium_confidence": {"en": "Medium (5-7)", "tr": "Orta (5-7)"},
        "low_confidence": {"en": "Low (1-4)", "tr": "Düşük (1-4)"},
        "generated_by": {"en": "Report generated by SimuTarget.ai — AI-Powered Market Simulation Platform", 
                         "tr": "Bu rapor SimuTarget.ai tarafından oluşturulmuştur — AI Destekli Pazar Simülasyon Platformu"},
    }
    return translations.get(key, {}).get(lang, key)


def _get_reasoning_text(reasoning, lang="en"):
    """Extract localized reasoning from JSON or plain string."""
    if not reasoning:
        return ""
    try:
        data = json.loads(reasoning) if isinstance(reasoning, str) else reasoning
        if isinstance(data, dict):
            return data.get(lang, data.get("tr", data.get("en", str(reasoning))))
    except (json.JSONDecodeError, TypeError):
        pass
    return str(reasoning)[:200]


def _compute_demographics(responses, lang="en"):
    """Compute demographic breakdowns from persona responses."""
    gender_stats = {}
    age_stats = {}
    income_stats = {}
    
    for r in responses:
        persona = r.get("persona_data", {}) if isinstance(r.get("persona_data"), dict) else {}
        decision = r.get("decision", "")
        is_yes = decision.upper() in ["EVET", "YES", "A", "B"]
        
        # Gender
        gender = persona.get("gender", "Unknown")
        if gender not in gender_stats:
            gender_stats[gender] = {"total": 0, "yes": 0}
        gender_stats[gender]["total"] += 1
        if is_yes:
            gender_stats[gender]["yes"] += 1
        
        # Age group
        age = persona.get("age", 0)
        if age < 25:
            age_group = "18-24"
        elif age < 35:
            age_group = "25-34"
        elif age < 45:
            age_group = "35-44"
        elif age < 55:
            age_group = "45-54"
        else:
            age_group = "55+"
        if age_group not in age_stats:
            age_stats[age_group] = {"total": 0, "yes": 0}
        age_stats[age_group]["total"] += 1
        if is_yes:
            age_stats[age_group]["yes"] += 1
        
        # Income
        income = persona.get("income_level", "Unknown")
        if income not in income_stats:
            income_stats[income] = {"total": 0, "yes": 0}
        income_stats[income]["total"] += 1
        if is_yes:
            income_stats[income]["yes"] += 1
    
    return gender_stats, age_stats, income_stats


# ═══════════════════════════════════════════════════════════
#  PRO REPORT — Clean, Professional
# ═══════════════════════════════════════════════════════════

def generate_pro_report(report_data: dict, output_path: str, lang: str = "en") -> str:
    """
    Generate a clean Pro-tier PDF report.
    
    report_data: {
        "campaign_name": str,
        "campaign_content": str,
        "test_type": "single" | "ab_compare" | "multi_compare",
        "region": str,
        "created_at": str (ISO),
        "total_personas": int,
        "approval_rate": float,
        "avg_confidence": float,
        "yes_count": int,
        "no_count": int,
        "results": list[dict],  # per-persona responses
        # For A/B:
        "content_a": str, "content_b": str,
        "a_votes": int, "b_votes": int, "neither_votes": int,
        # For Multi:
        "options": dict, "vote_distribution": dict,
    }
    """
    styles = _get_styles()
    width, height = A4
    
    doc = SimpleDocTemplate(
        output_path, pagesize=A4,
        leftMargin=20*mm, rightMargin=20*mm,
        topMargin=22*mm, bottomMargin=22*mm,
    )
    
    story = []
    usable_width = width - 40*mm
    
    # ── TITLE ──
    story.append(Spacer(1, 8*mm))
    
    # Cyan accent line
    accent_line = Table(
        [[""]],
        colWidths=[40],
        rowHeights=[3],
        style=TableStyle([('BACKGROUND', (0,0), (-1,-1), BRAND_CYAN), ('LEFTPADDING', (0,0), (-1,-1), 0), ('RIGHTPADDING', (0,0), (-1,-1), 0)])
    )
    story.append(accent_line)
    story.append(Spacer(1, 3*mm))
    
    story.append(Paragraph(_localized("campaign_report", lang), styles['ReportTitle']))
    story.append(Paragraph(
        report_data.get("campaign_name", "Untitled Campaign"),
        styles['ReportSubtitle']
    ))
    
    # ── CAMPAIGN INFO TABLE ──
    story.append(Paragraph(_localized("campaign_details", lang), styles['SectionTitle']))
    
    test_type_map = {
        "single": _localized("single_test", lang),
        "ab_compare": _localized("ab_compare", lang),
        "multi_compare": _localized("multi_compare", lang),
    }
    
    date_str = report_data.get("created_at", datetime.now().isoformat())
    try:
        date_str = datetime.fromisoformat(date_str.replace("Z", "+00:00")).strftime("%d %b %Y, %H:%M")
    except:
        pass
    
    info_data = [
        [_localized("test_type", lang), test_type_map.get(report_data.get("test_type", "single"), "Single")],
        [_localized("region", lang), report_data.get("region", "TR")],
        [_localized("test_date", lang), date_str],
        [_localized("total_personas", lang), str(report_data.get("total_personas", 0))],
    ]
    
    info_table = Table(info_data, colWidths=[usable_width * 0.35, usable_width * 0.65])
    info_table.setStyle(TableStyle([
        ('FONT', (0, 0), (0, -1), FONT_BOLD, 9),
        ('FONT', (1, 0), (1, -1), FONT, 9),
        ('TEXTCOLOR', (0, 0), (0, -1), TEXT_LIGHT),
        ('TEXTCOLOR', (1, 0), (1, -1), TEXT_BODY),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('LINEBELOW', (0, 0), (-1, -2), 0.5, BG_BORDER),
    ]))
    story.append(info_table)
    story.append(Spacer(1, 4*mm))
    
    # Campaign content (truncated)
    content_text = report_data.get("campaign_content", "")
    if content_text and len(content_text) > 300:
        content_text = content_text[:300] + "..."
    if content_text:
        story.append(Paragraph(_localized("campaign_content", lang), styles['SubSection']))
        story.append(Paragraph(content_text, styles['BodyText2']))
        story.append(Spacer(1, 4*mm))
    
    # ── KEY METRICS ──
    story.append(Paragraph(_localized("key_metrics", lang), styles['SectionTitle']))
    
    test_type = report_data.get("test_type", "single")
    
    if test_type == "single":
        approval = report_data.get("approval_rate", 0)
        metrics = [
            _build_metric_card(f"{approval}%", _localized("approval_rate", lang), 
                             SUCCESS_GREEN if approval >= 50 else DANGER_RED),
            _build_metric_card(f"{report_data.get('avg_confidence', 0):.1f}/10", 
                             _localized("avg_confidence", lang), BRAND_PURPLE),
            _build_metric_card(str(report_data.get("yes_count", 0)), 
                             _localized("yes_votes", lang), SUCCESS_GREEN),
            _build_metric_card(str(report_data.get("no_count", 0)), 
                             _localized("no_votes", lang), DANGER_RED),
        ]
    elif test_type == "ab_compare":
        a_votes = report_data.get("a_votes", 0)
        b_votes = report_data.get("b_votes", 0)
        neither = report_data.get("neither_votes", 0)
        total = a_votes + b_votes + neither
        metrics = [
            _build_metric_card(str(a_votes), f"{_localized('option_a', lang)} ({round(a_votes/total*100) if total else 0}%)", BRAND_CYAN),
            _build_metric_card(str(b_votes), f"{_localized('option_b', lang)} ({round(b_votes/total*100) if total else 0}%)", BRAND_PURPLE),
            _build_metric_card(str(neither), _localized("neither", lang), TEXT_LIGHT),
            _build_metric_card(f"{report_data.get('avg_confidence', 0):.1f}/10", _localized("avg_confidence", lang), WARNING_AMBER),
        ]
    else:
        # Multi compare
        vote_dist = report_data.get("vote_distribution", {})
        metrics = []
        for label, count in list(vote_dist.items())[:4]:
            total = sum(vote_dist.values())
            pct = round(count / total * 100) if total else 0
            metrics.append(_build_metric_card(str(count), f"{label} ({pct}%)", CHART_COLORS[len(metrics) % len(CHART_COLORS)]))
    
    col_w = usable_width / len(metrics) if metrics else usable_width / 4
    metrics_table = Table([metrics], colWidths=[col_w] * len(metrics))
    metrics_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 3),
        ('RIGHTPADDING', (0, 0), (-1, -1), 3),
    ]))
    story.append(metrics_table)
    story.append(Spacer(1, 6*mm))
    
    # ── RESULTS TABLE ──
    story.append(Paragraph(_localized("detailed_responses", lang), styles['SectionTitle']))
    
    results = report_data.get("results", [])
    
    if test_type == "single":
        header = [
            _localized("persona", lang), _localized("age", lang), _localized("gender", lang),
            _localized("city", lang), _localized("decision", lang), _localized("confidence", lang),
        ]
        table_data = [header]
        for r in results[:50]:  # Max 50 rows for Pro
            decision = r.get("decision", "")
            table_data.append([
                r.get("persona_name", ""),
                str(r.get("persona_age", "")),
                r.get("persona_gender", ""),
                r.get("persona_city", ""),
                decision,
                str(r.get("confidence", "")),
            ])
    elif test_type == "ab_compare":
        header = [
            _localized("persona", lang), _localized("age", lang), _localized("gender", lang),
            _localized("choice", lang), _localized("confidence", lang),
        ]
        table_data = [header]
        for r in results[:50]:
            table_data.append([
                r.get("persona_name", ""),
                str(r.get("persona_age", "")),
                r.get("persona_gender", ""),
                r.get("choice", ""),
                str(r.get("confidence", "")),
            ])
    else:
        header = [
            _localized("persona", lang), _localized("age", lang),
            _localized("choice", lang), _localized("confidence", lang),
        ]
        table_data = [header]
        for r in results[:50]:
            table_data.append([
                r.get("persona_name", ""),
                str(r.get("persona_age", "")),
                r.get("choice", ""),
                str(r.get("confidence", "")),
            ])
    
    n_cols = len(header)
    col_widths = [usable_width / n_cols] * n_cols
    
    results_table = Table(table_data, colWidths=col_widths, repeatRows=1)
    
    table_style_cmds = [
        ('FONT', (0, 0), (-1, 0), FONT_BOLD, 8),
        ('FONT', (0, 1), (-1, -1), FONT, 8),
        ('TEXTCOLOR', (0, 0), (-1, 0), WHITE),
        ('BACKGROUND', (0, 0), (-1, 0), BRAND_DARK),
        ('TEXTCOLOR', (0, 1), (-1, -1), TEXT_BODY),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [BG_WHITE, BG_LIGHT]),
        ('GRID', (0, 0), (-1, -1), 0.5, BG_BORDER),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]
    
    # Color-code decisions
    for row_idx in range(1, len(table_data)):
        if test_type == "single":
            decision_col = 4
        elif test_type == "ab_compare":
            decision_col = 3
        else:
            decision_col = 2
        
        val = table_data[row_idx][decision_col].upper()
        if val in ["EVET", "YES", "A"]:
            table_style_cmds.append(('TEXTCOLOR', (decision_col, row_idx), (decision_col, row_idx), SUCCESS_GREEN))
            table_style_cmds.append(('FONT', (decision_col, row_idx), (decision_col, row_idx), FONT_BOLD, 8))
        elif val in ["HAYIR", "NO", "B"]:
            table_style_cmds.append(('TEXTCOLOR', (decision_col, row_idx), (decision_col, row_idx), DANGER_RED))
            table_style_cmds.append(('FONT', (decision_col, row_idx), (decision_col, row_idx), FONT_BOLD, 8))
    
    results_table.setStyle(TableStyle(table_style_cmds))
    story.append(results_table)
    
    # ── FOOTER NOTE ──
    story.append(Spacer(1, 10*mm))
    story.append(Paragraph(
        _localized("generated_by", lang),
        styles['FooterText']
    ))
    
    # Build
    doc.build(story, onFirstPage=lambda c, d: _header_footer(c, d, report_data, lang),
              onLaterPages=lambda c, d: _header_footer(c, d, report_data, lang))
    
    return output_path


# ═══════════════════════════════════════════════════════════
#  BUSINESS REPORT — Infographic, Detailed
# ═══════════════════════════════════════════════════════════

def generate_business_report(report_data: dict, output_path: str, lang: str = "en") -> str:
    """
    Generate a detailed Business-tier PDF report with charts and demographics.
    Same data structure as Pro but with additional visualizations.
    """
    styles = _get_styles()
    width, height = A4
    
    doc = SimpleDocTemplate(
        output_path, pagesize=A4,
        leftMargin=20*mm, rightMargin=20*mm,
        topMargin=22*mm, bottomMargin=22*mm,
    )
    
    story = []
    usable_width = width - 40*mm
    
    # ── COVER SECTION ──
    story.append(Spacer(1, 10*mm))
    
    # Gradient-style accent block
    accent_block = Table(
        [[Paragraph(f'<font color="#FFFFFF"><b>SimuTarget.ai</b></font>',
                    ParagraphStyle('ab', fontSize=11, textColor=WHITE, alignment=TA_LEFT, leading=14))]],
        colWidths=[usable_width],
        rowHeights=[30],
        style=TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), BRAND_CYAN),
            ('LEFTPADDING', (0,0), (-1,-1), 12),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('ROUNDEDCORNERS', [6, 6, 0, 0]),
        ])
    )
    story.append(accent_block)
    
    title_block = Table(
        [[Paragraph(f'<b>{_localized("campaign_report", lang)}</b>',
                    ParagraphStyle('tb', fontSize=24, textColor=TEXT_DARK, leading=30)),
          Paragraph(report_data.get("campaign_name", ""),
                    ParagraphStyle('cn', fontSize=12, textColor=TEXT_LIGHT, leading=16, alignment=TA_RIGHT))]],
        colWidths=[usable_width * 0.65, usable_width * 0.35],
        style=TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), BG_LIGHT),
            ('LEFTPADDING', (0,0), (-1,-1), 12),
            ('RIGHTPADDING', (0,0), (-1,-1), 12),
            ('TOPPADDING', (0,0), (-1,-1), 14),
            ('BOTTOMPADDING', (0,0), (-1,-1), 14),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('ROUNDEDCORNERS', [0, 0, 6, 6]),
            ('BOX', (0,0), (-1,-1), 0.5, BG_BORDER),
        ])
    )
    story.append(title_block)
    story.append(Spacer(1, 6*mm))
    
    # ── CAMPAIGN INFO ──
    test_type = report_data.get("test_type", "single")
    test_type_map = {
        "single": _localized("single_test", lang),
        "ab_compare": _localized("ab_compare", lang),
        "multi_compare": _localized("multi_compare", lang),
    }
    
    date_str = report_data.get("created_at", datetime.now().isoformat())
    try:
        date_str = datetime.fromisoformat(date_str.replace("Z", "+00:00")).strftime("%d %b %Y, %H:%M")
    except:
        pass
    
    info_items = [
        [_localized("test_type", lang), test_type_map.get(test_type, "Single"),
         _localized("region", lang), report_data.get("region", "TR")],
        [_localized("test_date", lang), date_str,
         _localized("total_personas", lang), str(report_data.get("total_personas", 0))],
    ]
    
    info_table = Table(info_items, colWidths=[usable_width*0.18, usable_width*0.32, usable_width*0.18, usable_width*0.32])
    info_table.setStyle(TableStyle([
        ('FONT', (0, 0), (0, -1), FONT_BOLD, 9),
        ('FONT', (2, 0), (2, -1), FONT_BOLD, 9),
        ('FONT', (1, 0), (1, -1), FONT, 9),
        ('FONT', (3, 0), (3, -1), FONT, 9),
        ('TEXTCOLOR', (0, 0), (0, -1), TEXT_LIGHT),
        ('TEXTCOLOR', (2, 0), (2, -1), TEXT_LIGHT),
        ('TEXTCOLOR', (1, 0), (1, -1), TEXT_BODY),
        ('TEXTCOLOR', (3, 0), (3, -1), TEXT_BODY),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('LINEBELOW', (0, 0), (-1, -1), 0.5, BG_BORDER),
    ]))
    story.append(info_table)
    story.append(Spacer(1, 4*mm))
    
    # Campaign content
    content_text = report_data.get("campaign_content", "")
    if content_text:
        story.append(Paragraph(_localized("campaign_content", lang), styles['SubSection']))
        story.append(Paragraph(content_text[:500] + ("..." if len(content_text) > 500 else ""), styles['BodyText2']))
        story.append(Spacer(1, 4*mm))
    
    # ── KEY METRICS (same as Pro) ──
    story.append(Paragraph(_localized("key_metrics", lang), styles['SectionTitle']))
    
    if test_type == "single":
        approval = report_data.get("approval_rate", 0)
        metrics = [
            _build_metric_card(f"{approval}%", _localized("approval_rate", lang),
                             SUCCESS_GREEN if approval >= 50 else DANGER_RED),
            _build_metric_card(f"{report_data.get('avg_confidence', 0):.1f}/10",
                             _localized("avg_confidence", lang), BRAND_PURPLE),
            _build_metric_card(str(report_data.get("yes_count", 0)),
                             _localized("yes_votes", lang), SUCCESS_GREEN),
            _build_metric_card(str(report_data.get("no_count", 0)),
                             _localized("no_votes", lang), DANGER_RED),
        ]
    elif test_type == "ab_compare":
        a_votes = report_data.get("a_votes", 0)
        b_votes = report_data.get("b_votes", 0)
        neither = report_data.get("neither_votes", 0)
        total = a_votes + b_votes + neither
        metrics = [
            _build_metric_card(str(a_votes), f"{_localized('option_a', lang)} ({round(a_votes/total*100) if total else 0}%)", BRAND_CYAN),
            _build_metric_card(str(b_votes), f"{_localized('option_b', lang)} ({round(b_votes/total*100) if total else 0}%)", BRAND_PURPLE),
            _build_metric_card(str(neither), _localized("neither", lang), TEXT_LIGHT),
            _build_metric_card(f"{report_data.get('avg_confidence', 0):.1f}/10", _localized("avg_confidence", lang), WARNING_AMBER),
        ]
    else:
        vote_dist = report_data.get("vote_distribution", {})
        metrics = []
        for label, count in list(vote_dist.items())[:4]:
            total_v = sum(vote_dist.values())
            pct = round(count / total_v * 100) if total_v else 0
            metrics.append(_build_metric_card(str(count), f"{label} ({pct}%)", CHART_COLORS[len(metrics) % len(CHART_COLORS)]))
    
    if metrics:
        col_w = usable_width / len(metrics)
        metrics_table = Table([metrics], colWidths=[col_w] * len(metrics))
        metrics_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 3),
            ('RIGHTPADDING', (0, 0), (-1, -1), 3),
        ]))
        story.append(metrics_table)
    story.append(Spacer(1, 6*mm))
    
    # ══════════════════════════════════════════════
    # ── CHARTS SECTION (Business exclusive) ──
    # ══════════════════════════════════════════════
    
    story.append(Paragraph(_localized("results_overview", lang), styles['SectionTitle']))
    
    # Vote distribution pie chart
    if test_type == "single":
        yes_c = report_data.get("yes_count", 0)
        no_c = report_data.get("no_count", 0)
        pie_data = {
            _localized("yes", lang): yes_c,
            _localized("no", lang): no_c,
        }
        pie_colors = [SUCCESS_GREEN, DANGER_RED]
    elif test_type == "ab_compare":
        pie_data = {
            _localized("option_a", lang): report_data.get("a_votes", 0),
            _localized("option_b", lang): report_data.get("b_votes", 0),
            _localized("neither", lang): report_data.get("neither_votes", 0),
        }
        pie_colors = [BRAND_CYAN, BRAND_PURPLE, TEXT_LIGHT]
    else:
        pie_data = report_data.get("vote_distribution", {})
        pie_colors = CHART_COLORS
    
    pie_drawing = _create_pie_drawing(pie_data, width=220, height=150, colors=pie_colors)
    
    # Confidence distribution
    results = report_data.get("results", [])
    conf_high = sum(1 for r in results if r.get("confidence", 0) >= 8)
    conf_mid = sum(1 for r in results if 5 <= r.get("confidence", 0) < 8)
    conf_low = sum(1 for r in results if r.get("confidence", 0) < 5)
    
    conf_data = {
        _localized("high_confidence", lang): conf_high,
        _localized("medium_confidence", lang): conf_mid,
        _localized("low_confidence", lang): conf_low,
    }
    conf_bar = _create_bar_drawing(conf_data, width=240, height=80, color=BRAND_PURPLE)
    
    # Side by side: pie + confidence bar
    chart_table = Table(
        [[Paragraph(f'<b>{_localized("vote_distribution", lang)}</b>', styles['SubSection']),
          Paragraph(f'<b>{_localized("confidence_distribution", lang)}</b>', styles['SubSection'])],
         [pie_drawing, conf_bar]],
        colWidths=[usable_width * 0.5, usable_width * 0.5],
        style=TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ])
    )
    story.append(chart_table)
    story.append(Spacer(1, 6*mm))
    
    # ── DEMOGRAPHIC ANALYSIS (Business exclusive) ──
    story.append(Paragraph(_localized("demographic_analysis", lang), styles['SectionTitle']))
    
    gender_stats, age_stats, income_stats = _compute_demographics(results, lang)
    
    # Gender bar chart
    gender_rates = {}
    for g, stats in gender_stats.items():
        rate = round(stats["yes"] / stats["total"] * 100) if stats["total"] > 0 else 0
        gender_rates[f"{g} ({stats['total']})"] = rate
    
    # Age bar chart
    age_rates = {}
    age_order = ["18-24", "25-34", "35-44", "45-54", "55+"]
    for ag in age_order:
        if ag in age_stats:
            stats = age_stats[ag]
            rate = round(stats["yes"] / stats["total"] * 100) if stats["total"] > 0 else 0
            age_rates[f"{ag} ({stats['total']})"] = rate
    
    # Income bar chart
    income_rates = {}
    for inc, stats in income_stats.items():
        rate = round(stats["yes"] / stats["total"] * 100) if stats["total"] > 0 else 0
        short_inc = inc[:12] + ".." if len(inc) > 14 else inc
        income_rates[f"{short_inc} ({stats['total']})"] = rate
    
    gender_bar = _create_bar_drawing(gender_rates, width=240, height=max(60, len(gender_rates)*22), color=BRAND_CYAN)
    age_bar = _create_bar_drawing(age_rates, width=240, height=max(60, len(age_rates)*22), color=BRAND_PURPLE)
    
    demo_table = Table(
        [[Paragraph(f'<b>{_localized("by_gender", lang)}</b>', styles['SubSection']),
          Paragraph(f'<b>{_localized("by_age_group", lang)}</b>', styles['SubSection'])],
         [gender_bar, age_bar]],
        colWidths=[usable_width * 0.5, usable_width * 0.5],
        style=TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
        ])
    )
    story.append(demo_table)
    story.append(Spacer(1, 4*mm))
    
    if income_rates:
        story.append(Paragraph(f'<b>{_localized("by_income_level", lang)}</b>', styles['SubSection']))
        income_bar = _create_bar_drawing(income_rates, width=usable_width * 0.65, height=max(60, len(income_rates)*22), color=SUCCESS_GREEN)
        story.append(income_bar)
    story.append(Spacer(1, 6*mm))
    
    # ── DETAILED TABLE WITH REASONING (Business exclusive) ──
    story.append(PageBreak())
    story.append(Paragraph(_localized("detailed_responses", lang), styles['SectionTitle']))
    
    if test_type == "single":
        header = [
            _localized("persona", lang), _localized("age", lang), _localized("gender", lang),
            _localized("occupation", lang), _localized("decision", lang),
            _localized("confidence", lang), _localized("reasoning", lang),
        ]
        col_widths = [usable_width*0.13, usable_width*0.06, usable_width*0.08,
                      usable_width*0.13, usable_width*0.08, usable_width*0.07, usable_width*0.45]
    elif test_type == "ab_compare":
        header = [
            _localized("persona", lang), _localized("age", lang), _localized("gender", lang),
            _localized("choice", lang), _localized("confidence", lang), _localized("reasoning", lang),
        ]
        col_widths = [usable_width*0.14, usable_width*0.06, usable_width*0.1,
                      usable_width*0.08, usable_width*0.07, usable_width*0.55]
    else:
        header = [
            _localized("persona", lang), _localized("age", lang),
            _localized("choice", lang), _localized("confidence", lang), _localized("reasoning", lang),
        ]
        col_widths = [usable_width*0.15, usable_width*0.07,
                      usable_width*0.1, usable_width*0.08, usable_width*0.60]
    
    small_style = ParagraphStyle('small', fontName=FONT, fontSize=7, leading=9, textColor=TEXT_BODY)
    small_bold = ParagraphStyle('smallb', fontName=FONT_BOLD, fontSize=7, leading=9, textColor=TEXT_BODY)
    
    table_data = [[Paragraph(f'<b>{h}</b>', ParagraphStyle('th', fontName=FONT_BOLD, fontSize=8, textColor=WHITE, leading=10)) for h in header]]
    
    for r in results[:100]:  # Business gets 100 rows
        reasoning_text = _get_reasoning_text(r.get("reasoning", ""), lang)
        if len(reasoning_text) > 150:
            reasoning_text = reasoning_text[:150] + "..."
        
        if test_type == "single":
            decision = r.get("decision", "")
            dec_color = SUCCESS_GREEN if decision.upper() in ["EVET", "YES"] else DANGER_RED
            row = [
                Paragraph(r.get("persona_name", ""), small_style),
                Paragraph(str(r.get("persona_age", "")), small_style),
                Paragraph(r.get("persona_gender", ""), small_style),
                Paragraph(r.get("persona_occupation", "")[:20], small_style),
                Paragraph(f'<font color="#{dec_color.hexval()[2:]}">{decision}</font>', small_bold),
                Paragraph(str(r.get("confidence", "")), small_style),
                Paragraph(reasoning_text, small_style),
            ]
        elif test_type == "ab_compare":
            choice = r.get("choice", "")
            ch_color = BRAND_CYAN if choice == "A" else BRAND_PURPLE if choice == "B" else TEXT_LIGHT
            row = [
                Paragraph(r.get("persona_name", ""), small_style),
                Paragraph(str(r.get("persona_age", "")), small_style),
                Paragraph(r.get("persona_gender", ""), small_style),
                Paragraph(f'<font color="#{ch_color.hexval()[2:]}">{choice}</font>', small_bold),
                Paragraph(str(r.get("confidence", "")), small_style),
                Paragraph(reasoning_text, small_style),
            ]
        else:
            choice = r.get("choice", "")
            row = [
                Paragraph(r.get("persona_name", ""), small_style),
                Paragraph(str(r.get("persona_age", "")), small_style),
                Paragraph(f'<font color="#{BRAND_CYAN.hexval()[2:]}">{choice}</font>', small_bold),
                Paragraph(str(r.get("confidence", "")), small_style),
                Paragraph(reasoning_text, small_style),
            ]
        table_data.append(row)
    
    results_table = Table(table_data, colWidths=col_widths, repeatRows=1)
    results_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), BRAND_DARK),
        ('TEXTCOLOR', (0, 0), (-1, 0), WHITE),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [BG_WHITE, BG_LIGHT]),
        ('GRID', (0, 0), (-1, -1), 0.5, BG_BORDER),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    story.append(results_table)
    
    # ── FOOTER ──
    story.append(Spacer(1, 10*mm))
    story.append(Paragraph(
        _localized("generated_by", lang),
        styles['FooterText']
    ))
    
    # Build
    doc.build(story, onFirstPage=lambda c, d: _header_footer(c, d, report_data, lang),
              onLaterPages=lambda c, d: _header_footer(c, d, report_data, lang))
    
    return output_path


# ═══════════════════════════════════════════════════════════
#  MAIN ENTRY POINT
# ═══════════════════════════════════════════════════════════

def generate_report(report_data: dict, output_path: str, tier: str = "pro", lang: str = "en") -> str:
    """
    Generate PDF report based on user's subscription tier.
    
    tier: "pro" | "business" | "enterprise"
    """
    if tier in ("business", "enterprise"):
        return generate_business_report(report_data, output_path, lang)
    else:
        return generate_pro_report(report_data, output_path, lang)


# ═══════════════════════════════════════════════════════════
#  TEST / DEMO
# ═══════════════════════════════════════════════════════════

if __name__ == "__main__":
    import random
    
    # Generate sample data
    names_tr = ["Ahmet Yılmaz", "Fatma Kaya", "Mehmet Demir", "Ayşe Çelik", "Ali Öztürk",
                "Zeynep Arslan", "Mustafa Koç", "Elif Şahin", "Hasan Yıldız", "Merve Aydın",
                "Emre Doğan", "Selin Erdoğan", "Burak Kılıç", "Deniz Özkan", "Cem Aksoy"]
    
    cities = ["Istanbul", "Ankara", "Izmir", "Bursa", "Antalya", "Adana", "Konya"]
    occupations = ["Engineer", "Teacher", "Doctor", "Designer", "Manager", "Student", "Accountant"]
    genders = ["Male", "Female"]
    
    results = []
    yes_count = 0
    total_conf = 0
    for i in range(25):
        decision = random.choice(["YES", "YES", "YES", "NO", "NO"])
        conf = random.randint(3, 10)
        if decision == "YES":
            yes_count += 1
        total_conf += conf
        
        results.append({
            "persona_name": random.choice(names_tr),
            "persona_age": random.randint(22, 65),
            "persona_gender": random.choice(genders),
            "persona_city": random.choice(cities),
            "persona_occupation": random.choice(occupations),
            "decision": decision,
            "confidence": conf,
            "reasoning": json.dumps({
                "tr": "Bu ürün ihtiyaçlarıma uygun görünüyor, fiyatı makul.",
                "en": "This product seems to match my needs, the price is reasonable."
            }),
            "persona_data": {
                "gender": random.choice(genders),
                "age": random.randint(22, 65),
                "income_level": random.choice(["Low", "Lower-Mid", "Middle", "Upper-Mid", "High"]),
            }
        })
    
    sample_data = {
        "campaign_name": "Summer Sale 2025 — Beach Collection",
        "campaign_content": "Discover our exclusive Summer Beach Collection! Premium swimwear and accessories at 40% off. Limited time offer for the whole family. Free shipping on orders over $50. Shop now and make this summer unforgettable!",
        "test_type": "single",
        "region": "TR",
        "created_at": datetime.now().isoformat(),
        "total_personas": 25,
        "approval_rate": round(yes_count / 25 * 100, 1),
        "avg_confidence": round(total_conf / 25, 1),
        "yes_count": yes_count,
        "no_count": 25 - yes_count,
        "results": results,
    }
    
    # Generate Pro report
    generate_pro_report(sample_data, "/home/claude/sample_pro_report.pdf", lang="en")
    print("Pro report generated: sample_pro_report.pdf")
    
    # Generate Business report
    generate_business_report(sample_data, "/home/claude/sample_business_report.pdf", lang="en")
    print("Business report generated: sample_business_report.pdf")
    
    # Generate Turkish versions
    generate_pro_report(sample_data, "/home/claude/sample_pro_report_tr.pdf", lang="tr")
    print("Pro report (TR) generated: sample_pro_report_tr.pdf")
    
    generate_business_report(sample_data, "/home/claude/sample_business_report_tr.pdf", lang="tr")
    print("Business report (TR) generated: sample_business_report_tr.pdf")
