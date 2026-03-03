"""
SimuTarget PDF Report Generator v2 - Complete Redesign
Pro: Clean professional summary (1-2 pages)
Business: Detailed infographic with charts, demographics, reasoning (3-5 pages)
"""

import io, os, json, math
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.graphics.shapes import Drawing, Rect, String
from reportlab.graphics.charts.piecharts import Pie
from reportlab.graphics import renderPDF
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# --- FONT ---
def _find_font_dir():
    for d in [os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts"),
              "/usr/share/fonts/truetype/dejavu", "C:/Windows/Fonts"]:
        if os.path.isfile(os.path.join(d, "DejaVuSans.ttf")):
            return d
    return None

_FD = _find_font_dir()
_FR = False

def _reg():
    global _FR
    if _FR:
        return True
    if not _FD:
        return False
    try:
        pdfmetrics.registerFont(TTFont("SimuFont", os.path.join(_FD, "DejaVuSans.ttf")))
        pdfmetrics.registerFont(TTFont("SimuFont-Bold", os.path.join(_FD, "DejaVuSans-Bold.ttf")))
        pdfmetrics.registerFont(TTFont("SimuFont-Oblique", os.path.join(_FD, "DejaVuSans-Oblique.ttf")))
        pdfmetrics.registerFont(TTFont("SimuFont-BoldOblique", os.path.join(_FD, "DejaVuSans-BoldOblique.ttf")))
        from reportlab.pdfbase.pdfmetrics import registerFontFamily
        registerFontFamily("SimuFont", normal="SimuFont", bold="SimuFont-Bold",
                           italic="SimuFont-Oblique", boldItalic="SimuFont-BoldOblique")
        _FR = True
        return True
    except Exception:
        return False

_reg()
F = "SimuFont" if _FR else "Helvetica"
FB = "SimuFont-Bold" if _FR else "Helvetica-Bold"

# --- COLORS ---
CYAN = HexColor("#06B6D4")
PURPLE = HexColor("#8B5CF6")
DARK = HexColor("#0F172A")
GREEN = HexColor("#10B981")
RED = HexColor("#EF4444")
AMBER = HexColor("#F59E0B")
PINK = HexColor("#EC4899")
BLUE = HexColor("#3B82F6")
TEAL = HexColor("#14B8A6")
W = HexColor("#FFFFFF")
BGL = HexColor("#F8FAFC")
BGG = HexColor("#F1F5F9")
BGB = HexColor("#E2E8F0")
TD = HexColor("#0F172A")
TB = HexColor("#334155")
TL = HexColor("#64748B")
CC = [CYAN, PURPLE, GREEN, AMBER, RED, PINK, BLUE, TEAL]
CYAN_L = HexColor("#ECFEFF")

# --- L10N ---
_T = {
    "report": {"en": "Campaign Analysis Report", "tr": "Kampanya Analiz Raporu"},
    "name": {"en": "Campaign Name", "tr": "Kampanya Adi"},
    "content": {"en": "Campaign Content", "tr": "Kampanya Icerigi"},
    "type": {"en": "Test Type", "tr": "Test Turu"},
    "region": {"en": "Region", "tr": "Bolge"},
    "date": {"en": "Test Date", "tr": "Test Tarihi"},
    "metrics": {"en": "Key Metrics", "tr": "Temel Metrikler"},
    "approval": {"en": "Approval Rate", "tr": "Onay Orani"},
    "avgconf": {"en": "Avg Confidence", "tr": "Ort. Guven"},
    "total": {"en": "Total Personas", "tr": "Toplam Persona"},
    "yes": {"en": "Yes", "tr": "Evet"},
    "no": {"en": "No", "tr": "Hayir"},
    "yes_v": {"en": "Yes Votes", "tr": "Evet Oylari"},
    "no_v": {"en": "No Votes", "tr": "Hayir Oylari"},
    "overview": {"en": "Results Overview", "tr": "Sonuclara Genel Bakis"},
    "demo": {"en": "Demographic Analysis", "tr": "Demografik Analiz"},
    "gender": {"en": "By Gender", "tr": "Cinsiyete Gore"},
    "agegrp": {"en": "By Age Group", "tr": "Yas Grubuna Gore"},
    "income": {"en": "By Income Level", "tr": "Gelir Duzeyine Gore"},
    "responses": {"en": "Detailed Persona Responses", "tr": "Detayli Persona Yanitlari"},
    "persona": {"en": "Persona", "tr": "Persona"},
    "age": {"en": "Age", "tr": "Yas"},
    "gen": {"en": "Gender", "tr": "Cinsiyet"},
    "city": {"en": "City", "tr": "Sehir"},
    "occ": {"en": "Occupation", "tr": "Meslek"},
    "dec": {"en": "Decision", "tr": "Karar"},
    "conf": {"en": "Conf.", "tr": "Guven"},
    "reason": {"en": "Reasoning", "tr": "Gerekce"},
    "single": {"en": "Single Campaign Test", "tr": "Tekli Kampanya Testi"},
    "ab": {"en": "A/B Comparison", "tr": "A/B Karsilastirma"},
    "multi": {"en": "Multi Comparison", "tr": "Coklu Karsilastirma"},
    "optA": {"en": "Option A", "tr": "Secenek A"},
    "optB": {"en": "Option B", "tr": "Secenek B"},
    "neither": {"en": "Neither", "tr": "Hicbiri"},
    "votes": {"en": "Vote Distribution", "tr": "Oy Dagilimi"},
    "choice": {"en": "Choice", "tr": "Tercih"},
    "confdist": {"en": "Confidence Distribution", "tr": "Guven Dagilimi"},
    "high": {"en": "High (8-10)", "tr": "Yuksek (8-10)"},
    "med": {"en": "Medium (5-7)", "tr": "Orta (5-7)"},
    "low": {"en": "Low (1-4)", "tr": "Dusuk (1-4)"},
    "page": {"en": "Page", "tr": "Sayfa"},
    "gen_by": {"en": "Report generated by SimuTarget.ai - AI-Powered Market Simulation Platform",
               "tr": "Bu rapor SimuTarget.ai tarafindan olusturulmustur - AI Destekli Pazar Simulasyon Platformu"},
    "conf_note": {"en": "Confidential - AI-Powered Market Simulation",
                  "tr": "Gizli - AI Destekli Pazar Simulasyonu"},
    "pro": {"en": "Pro Report", "tr": "Pro Rapor"},
    "biz": {"en": "Business Report", "tr": "Business Rapor"},
    "nodata": {"en": "No data", "tr": "Veri yok"},
}


def L(k, l="en"):
    return _T.get(k, {}).get(l, k)


def _ss(v, m=200):
    s = str(v) if v else ""
    return s[:m] + ("..." if len(s) > m else "")


def _rsn(r, l="en"):
    if not r:
        return ""
    try:
        d = json.loads(r) if isinstance(r, str) else r
        if isinstance(d, dict):
            return d.get(l, d.get("tr", d.get("en", str(r))))
    except Exception:
        pass
    return str(r)[:200]


def _fd(ds):
    try:
        return datetime.fromisoformat(str(ds).replace("Z", "+00:00")).strftime("%d %b %Y, %H:%M")
    except Exception:
        return str(ds)[:19] if ds else "-"


def _hx(c):
    return "#%02x%02x%02x" % (int(c.red * 255), int(c.green * 255), int(c.blue * 255))


# --- STYLES ---
def _st():
    return {
        "title": ParagraphStyle("t", fontName=FB, fontSize=26, leading=32, textColor=TD, spaceAfter=4),
        "sub": ParagraphStyle("su", fontName=F, fontSize=12, leading=16, textColor=TL, spaceAfter=20),
        "sec": ParagraphStyle("se", fontName=FB, fontSize=15, leading=20, textColor=TD, spaceBefore=16, spaceAfter=8),
        "ssec": ParagraphStyle("ss", fontName=FB, fontSize=11, leading=15, textColor=TB, spaceBefore=10, spaceAfter=5),
        "body": ParagraphStyle("bo", fontName=F, fontSize=10, leading=14, textColor=TB, spaceAfter=6),
        "sm": ParagraphStyle("sm", fontName=F, fontSize=8, leading=11, textColor=TB),
        "smb": ParagraphStyle("smb", fontName=FB, fontSize=8, leading=11, textColor=TB),
        "hdr": ParagraphStyle("hdr", fontName=FB, fontSize=8, leading=10, textColor=W),
        "ftr": ParagraphStyle("ftr", fontName=F, fontSize=7, leading=10, textColor=TL, alignment=TA_CENTER),
    }


# --- HEADER / FOOTER ---
def _hf(c, doc, data, lang, tier):
    c.saveState()
    w, h = A4
    c.setFillColor(DARK)
    c.rect(0, h - 14 * mm, w, 14 * mm, fill=True, stroke=False)
    c.setFont(FB, 10)
    c.setFillColor(CYAN)
    c.drawString(20 * mm, h - 10 * mm, "SimuTarget.ai")
    c.setFont(F, 8)
    c.setFillColor(HexColor("#94A3B8"))
    c.drawRightString(w - 20 * mm, h - 10 * mm, tier + " | " + L("report", lang))
    c.setStrokeColor(BGB)
    c.setLineWidth(0.5)
    c.line(20 * mm, 14 * mm, w - 20 * mm, 14 * mm)
    c.setFont(F, 7)
    c.setFillColor(TL)
    c.drawString(20 * mm, 9 * mm, _fd(datetime.now().isoformat()))
    c.drawCentredString(w / 2, 9 * mm, L("conf_note", lang))
    c.drawRightString(w - 20 * mm, 9 * mm, L("page", lang) + " " + str(c.getPageNumber()))
    c.restoreState()


# --- METRIC CARD ---
def _mc(val, label, color=None):
    if color is None:
        color = CYAN
    hx = _hx(color)
    val_p = Paragraph(
        '<font color="' + hx + '"><b>' + str(val) + '</b></font>',
        ParagraphStyle("mv", fontName=FB, fontSize=22, alignment=TA_CENTER, leading=26),
    )
    lbl_p = Paragraph(
        label,
        ParagraphStyle("ml", fontName=F, fontSize=8, alignment=TA_CENTER, textColor=TL, leading=11),
    )
    return Table(
        [[val_p], [lbl_p]],
        colWidths=[None],
        rowHeights=[32, 18],
        style=TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), BGL),
            ("BOX", (0, 0), (-1, -1), 0.5, BGB),
            ("ROUNDEDCORNERS", [6, 6, 6, 6]),
            ("TOPPADDING", (0, 0), (-1, 0), 10),
            ("BOTTOMPADDING", (0, -1), (-1, -1), 10),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ]),
    )


# --- PIE CHART (FIXED) ---
def _pie(dd, wd=200, ht=150, colors=None):
    d = Drawing(wd, ht)
    ls = list(dd.keys())
    vs = list(dd.values())
    total = sum(vs)
    if total <= 0:
        d.add(String(wd // 2, ht // 2, "No data", fontName=F, fontSize=10, fillColor=TL, textAnchor="middle"))
        return d
    p = Pie()
    p.x = wd // 2 - 50
    p.y = 10
    p.width = 100
    p.height = 100
    p.data = vs
    p.labels = [lb + " (" + str(round(v / total * 100)) + "%)" if v > 0 else "" for lb, v in zip(ls, vs)]
    p.sideLabels = True
    p.slices.strokeWidth = 1.5
    p.slices.strokeColor = W
    cs = colors or CC
    for i in range(len(vs)):
        p.slices[i].fillColor = cs[i % len(cs)]
        p.slices[i].fontName = F
        p.slices[i].fontSize = 8
    d.add(p)
    return d


# --- BAR CHART ---
def _bar(dd, wd=250, ht=None, color=None, show_pct=False):
    if color is None:
        color = CYAN
    items = list(dd.items())
    if not items:
        return Drawing(wd, 30)
    bh = 16
    gap = 5
    n = len(items)
    if ht is None:
        ht = max(60, n * (bh + gap) + 20)
    d = Drawing(wd, ht)
    mx = max((v for _, v in items), default=1) or 1
    lw = 100
    ba = wd - lw - 45
    sy = ht - 15
    for i, (lb, vl) in enumerate(items):
        y = sy - i * (bh + gap)
        d.add(String(0, y + 3, _ss(lb, 18), fontName=F, fontSize=8, fillColor=TB))
        d.add(Rect(lw, y, ba, bh, fillColor=BGG, strokeColor=None))
        bw = (vl / mx) * ba if mx > 0 else 0
        if bw > 0:
            d.add(Rect(lw, y, max(bw, 2), bh, fillColor=color, strokeColor=None))
        suffix = "%" if show_pct else ""
        d.add(String(lw + ba + 4, y + 3, str(vl) + suffix, fontName=FB, fontSize=8, fillColor=TB))
    return d


# --- DEMOGRAPHICS ---
def _demographics(results):
    gn = {}
    ag = {}
    ic = {}
    for r in results:
        pd = r.get("persona_data", {}) if isinstance(r.get("persona_data"), dict) else {}
        dec = str(r.get("decision", "")).upper()
        isy = dec in ("EVET", "YES", "A")
        g = pd.get("gender", r.get("persona_gender", "?"))
        gn.setdefault(g, {"t": 0, "y": 0})
        gn[g]["t"] += 1
        if isy:
            gn[g]["y"] += 1
        try:
            a = int(pd.get("age", r.get("persona_age", 0)))
        except (ValueError, TypeError):
            a = 0
        if a < 25:
            grp = "18-24"
        elif a < 35:
            grp = "25-34"
        elif a < 45:
            grp = "35-44"
        elif a < 55:
            grp = "45-54"
        else:
            grp = "55+"
        ag.setdefault(grp, {"t": 0, "y": 0})
        ag[grp]["t"] += 1
        if isy:
            ag[grp]["y"] += 1
        inc = pd.get("income_level", r.get("persona_income", "?"))
        ic.setdefault(inc, {"t": 0, "y": 0})
        ic[inc]["t"] += 1
        if isy:
            ic[inc]["y"] += 1
    return gn, ag, ic


# --- INFO TABLE ---
def _info_tbl(rd, tt, lang, uw):
    tm = {"single": L("single", lang), "ab_compare": L("ab", lang), "multi_compare": L("multi", lang)}
    data = [
        [L("name", lang), _ss(rd.get("campaign_name", "-"), 60)],
        [L("type", lang), tm.get(tt, tt)],
        [L("region", lang), rd.get("region", "TR")],
        [L("date", lang), _fd(rd.get("created_at", ""))],
        [L("total", lang), str(rd.get("total_personas", 0))],
    ]
    t = Table(data, colWidths=[uw * 0.3, uw * 0.7])
    t.setStyle(TableStyle([
        ("FONT", (0, 0), (0, -1), FB, 9),
        ("FONT", (1, 0), (1, -1), F, 9),
        ("TEXTCOLOR", (0, 0), (0, -1), TL),
        ("TEXTCOLOR", (1, 0), (1, -1), TB),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("LINEBELOW", (0, 0), (-1, -1), 0.5, BGB),
    ]))
    return t


# --- METRICS ROW ---
def _metrics_row(rd, tt, lang, uw):
    ms = []
    if tt == "single":
        try:
            apr = float(rd.get("approval_rate", 0))
        except (ValueError, TypeError):
            apr = 0
        try:
            ac = float(rd.get("avg_confidence", 0))
        except (ValueError, TypeError):
            ac = 0
        ms = [
            _mc(str(round(apr, 1)) + "%", L("approval", lang), GREEN if apr >= 50 else RED),
            _mc(str(round(ac, 1)) + "/10", L("avgconf", lang), PURPLE),
            _mc(str(rd.get("yes_count", 0)), L("yes_v", lang), GREEN),
            _mc(str(rd.get("no_count", 0)), L("no_v", lang), RED),
        ]
    elif tt == "ab_compare":
        av = rd.get("a_votes", 0)
        bv = rd.get("b_votes", 0)
        nv = rd.get("neither_votes", 0)
        tot = av + bv + nv or 1
        try:
            ac = float(rd.get("avg_confidence", 0))
        except (ValueError, TypeError):
            ac = 0
        ms = [
            _mc(str(av), L("optA", lang) + " (" + str(round(av / tot * 100)) + "%)", CYAN),
            _mc(str(bv), L("optB", lang) + " (" + str(round(bv / tot * 100)) + "%)", PURPLE),
            _mc(str(nv), L("neither", lang), TL),
            _mc(str(round(ac, 1)) + "/10", L("avgconf", lang), AMBER),
        ]
    else:
        vd = rd.get("vote_distribution", {})
        try:
            ac = float(rd.get("avg_confidence", 0))
        except (ValueError, TypeError):
            ac = 0
        tv = sum(vd.values()) or 1
        for i, (lb, ct) in enumerate(list(vd.items())[:3]):
            ms.append(_mc(str(ct), _ss(lb, 12) + " (" + str(round(ct / tv * 100)) + "%)", CC[i % len(CC)]))
        ms.append(_mc(str(round(ac, 1)) + "/10", L("avgconf", lang), AMBER))
    if not ms:
        return None
    cw = uw / len(ms)
    t = Table([ms], colWidths=[cw] * len(ms))
    t.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 3),
        ("RIGHTPADDING", (0, 0), (-1, -1), 3),
    ]))
    return t


# --- INSIGHT ---
def _insight(rd, tt, lang):
    if tt == "single":
        try:
            r = float(rd.get("approval_rate", 0))
        except (ValueError, TypeError):
            r = 0
        n = rd.get("total_personas", 0)
        if lang == "tr":
            if r >= 70:
                return str(n) + " persona arasinda %" + str(round(r)) + " onay orani - kampanya guclu performans gosteriyor."
            elif r >= 40:
                return str(n) + " persona arasinda %" + str(round(r)) + " onay orani - orta duzeyde ilgi, iyilestirme onerilir."
            else:
                return str(n) + " persona arasinda %" + str(round(r)) + " onay orani - kampanya yeniden degerlendirilmeli."
        else:
            if r >= 70:
                return str(round(r)) + "% approval across " + str(n) + " personas - strong performance."
            elif r >= 40:
                return str(round(r)) + "% approval across " + str(n) + " personas - moderate interest, optimization recommended."
            else:
                return str(round(r)) + "% approval across " + str(n) + " personas - campaign needs significant revision."
    elif tt == "ab_compare":
        a = rd.get("a_votes", 0)
        b = rd.get("b_votes", 0)
        wn = "A" if a > b else "B" if b > a else "Tie"
        if lang == "tr":
            return "Secenek " + wn + " daha yuksek oy aldi (A:" + str(a) + ", B:" + str(b) + ")."
        return "Option " + wn + " received more votes (A:" + str(a) + ", B:" + str(b) + ")."
    else:
        dist = rd.get("vote_distribution", {})
        if dist:
            wn = max(dist, key=dist.get)
            if lang == "tr":
                return "En cok oy alan: " + wn + " (" + str(dist[wn]) + " oy)."
            return "Top choice: " + wn + " (" + str(dist[wn]) + " votes)."
    return ""


# --- RESULT TABLE BUILDER ---
def _build_result_rows(results, tt, s, lang, include_reasoning=False, max_rows=50):
    """Build table header + data rows for persona results."""
    if tt == "single":
        if include_reasoning:
            hdr = [L("persona", lang), L("age", lang), L("gen", lang), L("occ", lang), L("dec", lang), L("conf", lang), L("reason", lang)]
            cw_ratios = [0.12, 0.05, 0.08, 0.12, 0.07, 0.06, 0.50]
        else:
            hdr = [L("persona", lang), L("age", lang), L("gen", lang), L("city", lang), L("dec", lang), L("conf", lang)]
            cw_ratios = [0.22, 0.08, 0.13, 0.22, 0.18, 0.17]
    elif tt == "ab_compare":
        if include_reasoning:
            hdr = [L("persona", lang), L("age", lang), L("gen", lang), L("choice", lang), L("conf", lang), L("reason", lang)]
            cw_ratios = [0.14, 0.06, 0.10, 0.08, 0.07, 0.55]
        else:
            hdr = [L("persona", lang), L("age", lang), L("gen", lang), L("choice", lang), L("conf", lang)]
            cw_ratios = [0.28, 0.10, 0.22, 0.20, 0.20]
    else:
        if include_reasoning:
            hdr = [L("persona", lang), L("age", lang), L("choice", lang), L("conf", lang), L("reason", lang)]
            cw_ratios = [0.14, 0.07, 0.10, 0.07, 0.62]
        else:
            hdr = [L("persona", lang), L("age", lang), L("choice", lang), L("conf", lang)]
            cw_ratios = [0.30, 0.15, 0.30, 0.25]

    td = [[Paragraph("<b>" + h + "</b>", s["hdr"]) for h in hdr]]

    for r in results[:max_rows]:
        if tt == "single":
            dc = str(r.get("decision", "")).upper()
            dcl = "#10B981" if dc in ("EVET", "YES") else "#EF4444"
            dec_text = str(r.get("decision", ""))
            row = [
                Paragraph(_ss(r.get("persona_name", ""), 25), s["sm"]),
                Paragraph(str(r.get("persona_age", "")), s["sm"]),
                Paragraph(_ss(r.get("persona_gender", ""), 10), s["sm"]),
            ]
            if include_reasoning:
                row.append(Paragraph(_ss(r.get("persona_occupation", ""), 18), s["sm"]))
            else:
                row.append(Paragraph(_ss(r.get("persona_city", ""), 20), s["sm"]))
            row.append(Paragraph('<font color="' + dcl + '"><b>' + dec_text + '</b></font>', s["smb"]))
            row.append(Paragraph(str(r.get("confidence", "")), s["sm"]))
            if include_reasoning:
                rsn = _rsn(r.get("reasoning", ""), lang)
                row.append(Paragraph(_ss(rsn, 180), s["sm"]))

        elif tt == "ab_compare":
            ch = r.get("choice", r.get("decision", ""))
            ch_upper = str(ch).upper()
            cl = "#06B6D4" if ch_upper == "A" else "#8B5CF6" if ch_upper == "B" else "#64748B"
            row = [
                Paragraph(_ss(r.get("persona_name", ""), 30), s["sm"]),
                Paragraph(str(r.get("persona_age", "")), s["sm"]),
                Paragraph(_ss(r.get("persona_gender", ""), 10), s["sm"]),
                Paragraph('<font color="' + cl + '"><b>' + str(ch) + '</b></font>', s["smb"]),
                Paragraph(str(r.get("confidence", "")), s["sm"]),
            ]
            if include_reasoning:
                rsn = _rsn(r.get("reasoning", ""), lang)
                row.append(Paragraph(_ss(rsn, 180), s["sm"]))

        else:
            ch = r.get("choice", r.get("decision", ""))
            row = [
                Paragraph(_ss(r.get("persona_name", ""), 30), s["sm"]),
                Paragraph(str(r.get("persona_age", "")), s["sm"]),
                Paragraph('<font color="#06B6D4"><b>' + _ss(ch, 20) + '</b></font>', s["smb"]),
                Paragraph(str(r.get("confidence", "")), s["sm"]),
            ]
            if include_reasoning:
                rsn = _rsn(r.get("reasoning", ""), lang)
                row.append(Paragraph(_ss(rsn, 180), s["sm"]))

        td.append(row)

    return td, cw_ratios


def _style_table(tbl):
    """Apply standard styling to results table."""
    tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), DARK),
        ("TEXTCOLOR", (0, 0), (-1, 0), W),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [HexColor("#FFFFFF"), BGL]),
        ("GRID", (0, 0), (-1, -1), 0.5, BGB),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    return tbl


# ========== PRO REPORT ==========
def generate_pro_report(rd, out, lang="en"):
    _reg()
    s = _st()
    w, h = A4
    uw = w - 40 * mm
    doc = SimpleDocTemplate(out, pagesize=A4, leftMargin=20 * mm, rightMargin=20 * mm,
                            topMargin=20 * mm, bottomMargin=20 * mm)
    story = []
    tt = rd.get("test_type", "single")

    # Title
    story.append(Spacer(1, 6 * mm))
    story.append(Table([[""]], colWidths=[50], rowHeights=[3],
                        style=TableStyle([("BACKGROUND", (0, 0), (-1, -1), CYAN)])))
    story.append(Spacer(1, 2 * mm))
    story.append(Paragraph(L("report", lang), s["title"]))
    story.append(Paragraph(_ss(rd.get("campaign_name", ""), 80), s["sub"]))

    # Info
    story.append(_info_tbl(rd, tt, lang, uw))
    story.append(Spacer(1, 3 * mm))

    # Content
    ct = rd.get("campaign_content", "")
    if ct:
        story.append(Paragraph(L("content", lang), s["ssec"]))
        story.append(Paragraph(_ss(ct, 300), s["body"]))
        story.append(Spacer(1, 3 * mm))

    # Insight
    ins = _insight(rd, tt, lang)
    if ins:
        ib = Table(
            [[Paragraph(ins, s["body"])]],
            colWidths=[uw],
            style=TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), CYAN_L),
                ("BOX", (0, 0), (-1, -1), 1, CYAN),
                ("ROUNDEDCORNERS", [4, 4, 4, 4]),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                ("LEFTPADDING", (0, 0), (-1, -1), 10),
            ]),
        )
        story.append(ib)
        story.append(Spacer(1, 4 * mm))

    # Metrics
    story.append(Paragraph(L("metrics", lang), s["sec"]))
    mr = _metrics_row(rd, tt, lang, uw)
    if mr:
        story.append(mr)
    story.append(Spacer(1, 5 * mm))

    # Results table
    story.append(Paragraph(L("responses", lang), s["sec"]))
    results = rd.get("results", [])
    if not results:
        story.append(Paragraph(L("nodata", lang), s["body"]))
    else:
        td, cw_ratios = _build_result_rows(results, tt, s, lang, include_reasoning=False, max_rows=50)
        cw = [uw * r for r in cw_ratios]
        tbl = Table(td, colWidths=cw, repeatRows=1)
        _style_table(tbl)
        story.append(tbl)

    # Footer
    story.append(Spacer(1, 8 * mm))
    story.append(Paragraph(L("gen_by", lang), s["ftr"]))

    tl = L("pro", lang)
    doc.build(story, onFirstPage=lambda c, d: _hf(c, d, rd, lang, tl),
              onLaterPages=lambda c, d: _hf(c, d, rd, lang, tl))
    return out


# ========== BUSINESS REPORT ==========
def generate_business_report(rd, out, lang="en"):
    _reg()
    s = _st()
    w, h = A4
    uw = w - 40 * mm
    doc = SimpleDocTemplate(out, pagesize=A4, leftMargin=20 * mm, rightMargin=20 * mm,
                            topMargin=20 * mm, bottomMargin=20 * mm)
    story = []
    tt = rd.get("test_type", "single")
    results = rd.get("results", [])

    # Cover
    story.append(Spacer(1, 8 * mm))
    ct_top = Table(
        [[Paragraph('<font color="#FFFFFF"><b>SimuTarget.ai</b></font>',
                     ParagraphStyle("ct", fontName=FB, fontSize=11, textColor=W, alignment=TA_LEFT, leading=14))]],
        colWidths=[uw], rowHeights=[28],
        style=TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), CYAN),
            ("LEFTPADDING", (0, 0), (-1, -1), 12),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("ROUNDEDCORNERS", [6, 6, 0, 0]),
        ]),
    )
    story.append(ct_top)
    ct_bot = Table(
        [[Paragraph("<b>" + L("report", lang) + "</b>",
                     ParagraphStyle("cb1", fontName=FB, fontSize=22, textColor=TD, leading=28)),
          Paragraph(rd.get("campaign_name", ""),
                     ParagraphStyle("cb2", fontName=F, fontSize=11, textColor=TL, leading=14, alignment=TA_RIGHT))]],
        colWidths=[uw * 0.6, uw * 0.4],
        style=TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), BGL),
            ("LEFTPADDING", (0, 0), (-1, -1), 12),
            ("RIGHTPADDING", (0, 0), (-1, -1), 12),
            ("TOPPADDING", (0, 0), (-1, -1), 12),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("ROUNDEDCORNERS", [0, 0, 6, 6]),
            ("BOX", (0, 0), (-1, -1), 0.5, BGB),
        ]),
    )
    story.append(ct_bot)
    story.append(Spacer(1, 5 * mm))

    # Info
    story.append(_info_tbl(rd, tt, lang, uw))
    story.append(Spacer(1, 3 * mm))

    # Content
    cntnt = rd.get("campaign_content", "")
    if cntnt:
        story.append(Paragraph(L("content", lang), s["ssec"]))
        story.append(Paragraph(_ss(cntnt, 600), s["body"]))
        story.append(Spacer(1, 3 * mm))

    # Insight
    ins = _insight(rd, tt, lang)
    if ins:
        ib = Table(
            [[Paragraph(ins, ParagraphStyle("ins", fontName=F, fontSize=10, leading=14, textColor=TD))]],
            colWidths=[uw],
            style=TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), CYAN_L),
                ("BOX", (0, 0), (-1, -1), 1.5, CYAN),
                ("ROUNDEDCORNERS", [6, 6, 6, 6]),
                ("TOPPADDING", (0, 0), (-1, -1), 10),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
                ("LEFTPADDING", (0, 0), (-1, -1), 12),
            ]),
        )
        story.append(ib)
        story.append(Spacer(1, 4 * mm))

    # Metrics
    story.append(Paragraph(L("metrics", lang), s["sec"]))
    mr = _metrics_row(rd, tt, lang, uw)
    if mr:
        story.append(mr)
    story.append(Spacer(1, 5 * mm))

    # Charts
    story.append(Paragraph(L("overview", lang), s["sec"]))
    if tt == "single":
        pd = {L("yes", lang): rd.get("yes_count", 0), L("no", lang): rd.get("no_count", 0)}
        pc = [GREEN, RED]
    elif tt == "ab_compare":
        pd = {L("optA", lang): rd.get("a_votes", 0), L("optB", lang): rd.get("b_votes", 0),
              L("neither", lang): rd.get("neither_votes", 0)}
        pc = [CYAN, PURPLE, TL]
    else:
        pd = rd.get("vote_distribution", {})
        pc = CC

    pie_d = _pie(pd, wd=220, ht=150, colors=pc)

    ch_high = sum(1 for r in results if (r.get("confidence") or 0) >= 8)
    ch_med = sum(1 for r in results if 5 <= (r.get("confidence") or 0) < 8)
    ch_low = sum(1 for r in results if (r.get("confidence") or 0) < 5)
    cd = {L("high", lang): ch_high, L("med", lang): ch_med, L("low", lang): ch_low}
    conf_bar = _bar(cd, wd=240, ht=80, color=PURPLE)

    cht = Table(
        [[Paragraph("<b>" + L("votes", lang) + "</b>", s["ssec"]),
          Paragraph("<b>" + L("confdist", lang) + "</b>", s["ssec"])],
         [pie_d, conf_bar]],
        colWidths=[uw * 0.5, uw * 0.5],
        style=TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]),
    )
    story.append(cht)
    story.append(Spacer(1, 5 * mm))

    # Demographics
    story.append(Paragraph(L("demo", lang), s["sec"]))
    gn, ag, ic = _demographics(results)

    gnr = {}
    for g, st2 in gn.items():
        rate = round(st2["y"] / st2["t"] * 100) if st2["t"] > 0 else 0
        gnr[g + " (" + str(st2["t"]) + ")"] = rate

    agr = {}
    for a in ["18-24", "25-34", "35-44", "45-54", "55+"]:
        if a in ag:
            st2 = ag[a]
            rate = round(st2["y"] / st2["t"] * 100) if st2["t"] > 0 else 0
            agr[a + " (" + str(st2["t"]) + ")"] = rate

    gb = _bar(gnr, wd=240, ht=max(60, len(gnr) * 22), color=CYAN, show_pct=True)
    ab = _bar(agr, wd=240, ht=max(60, len(agr) * 22), color=PURPLE, show_pct=True)
    dt = Table(
        [[Paragraph("<b>" + L("gender", lang) + "</b>", s["ssec"]),
          Paragraph("<b>" + L("agegrp", lang) + "</b>", s["ssec"])],
         [gb, ab]],
        colWidths=[uw * 0.5, uw * 0.5],
        style=TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("TOPPADDING", (0, 0), (-1, -1), 4)]),
    )
    story.append(dt)
    story.append(Spacer(1, 3 * mm))

    if ic:
        icr = {}
        for inc_key, st2 in ic.items():
            rate = round(st2["y"] / st2["t"] * 100) if st2["t"] > 0 else 0
            icr[_ss(inc_key, 14) + " (" + str(st2["t"]) + ")"] = rate
        story.append(Paragraph("<b>" + L("income", lang) + "</b>", s["ssec"]))
        ib2 = _bar(icr, wd=int(uw * 0.7), ht=max(60, len(icr) * 22), color=GREEN, show_pct=True)
        story.append(ib2)
    story.append(Spacer(1, 5 * mm))

    # Detailed table with reasoning
    story.append(PageBreak())
    story.append(Paragraph(L("responses", lang), s["sec"]))
    if not results:
        story.append(Paragraph(L("nodata", lang), s["body"]))
    else:
        td, cw_ratios = _build_result_rows(results, tt, s, lang, include_reasoning=True, max_rows=100)
        cw = [uw * r for r in cw_ratios]
        tbl = Table(td, colWidths=cw, repeatRows=1)
        tbl.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), DARK),
            ("TEXTCOLOR", (0, 0), (-1, 0), W),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [HexColor("#FFFFFF"), BGL]),
            ("GRID", (0, 0), (-1, -1), 0.5, BGB),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ("LEFTPADDING", (0, 0), (-1, -1), 4),
            ("RIGHTPADDING", (0, 0), (-1, -1), 4),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ]))
        story.append(tbl)

    # Footer
    story.append(Spacer(1, 8 * mm))
    story.append(Paragraph(L("gen_by", lang), s["ftr"]))

    tl = L("biz", lang)
    doc.build(story, onFirstPage=lambda c, d: _hf(c, d, rd, lang, tl),
              onLaterPages=lambda c, d: _hf(c, d, rd, lang, tl))
    return out


# ========== ENTRY ==========
def generate_report(rd, out, tier="pro", lang="en"):
    """Generate PDF report based on subscription tier."""
    if tier in ("business", "enterprise"):
        return generate_business_report(rd, out, lang)
    return generate_pro_report(rd, out, lang)