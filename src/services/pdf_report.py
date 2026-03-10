"""
SimuTarget PDF Report Generator v3 - Professional Infographic
Pro: Compact summary with pie chart (1-2 pages)
Business: Full infographic with demographics, Big Five, city analysis, executive summary (5-8 pages)
"""

import io, os, json, math
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether
)
from reportlab.graphics.shapes import Drawing, Rect, String, Line, Circle
from reportlab.graphics.charts.piecharts import Pie
from reportlab.graphics import renderPDF
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont


# ============================================================
#  FONT REGISTRATION
# ============================================================
def _find_font_dir():
    for d in [
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts"),
        "/usr/share/fonts/truetype/dejavu",
        "/usr/local/share/fonts/dejavu",
        "C:/Windows/Fonts",
    ]:
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
FI = "SimuFont-Oblique" if _FR else "Helvetica-Oblique"

# ============================================================
#  COLORS
# ============================================================
CYAN = HexColor("#06B6D4"); PURPLE = HexColor("#8B5CF6"); DARK = HexColor("#0F172A")
GREEN = HexColor("#10B981"); RED = HexColor("#EF4444"); AMBER = HexColor("#F59E0B")
PINK = HexColor("#EC4899"); BLUE = HexColor("#3B82F6"); TEAL = HexColor("#14B8A6")
INDIGO = HexColor("#6366F1"); ORANGE = HexColor("#F97316")
W = HexColor("#FFFFFF"); BGL = HexColor("#F8FAFC"); BGG = HexColor("#F1F5F9")
BGB = HexColor("#E2E8F0"); TD = HexColor("#0F172A"); TB = HexColor("#334155")
TL = HexColor("#64748B"); TM = HexColor("#94A3B8")
CC = [CYAN, PURPLE, GREEN, AMBER, RED, PINK, BLUE, TEAL, INDIGO, ORANGE]
CYAN_L = HexColor("#ECFEFF")

# ============================================================
#  LOCALIZATION
# ============================================================
_T = {
    "report": {"en": "Campaign Analysis Report", "tr": "Kampanya Analiz Raporu"},
    "exec_summary": {"en": "Executive Summary", "tr": "Yonetici Ozeti"},
    "name": {"en": "Campaign Name", "tr": "Kampanya Adi"},
    "content": {"en": "Campaign Content", "tr": "Kampanya Icerigi"},
    "type": {"en": "Test Type", "tr": "Test Turu"},
    "region": {"en": "Region", "tr": "Bolge"},
    "date": {"en": "Test Date", "tr": "Test Tarihi"},
    "metrics": {"en": "Key Metrics", "tr": "Temel Metrikler"},
    "approval": {"en": "Approval Rate", "tr": "Onay Orani"},
    "avgconf": {"en": "Avg Confidence", "tr": "Ort. Guven"},
    "total": {"en": "Total Personas", "tr": "Toplam Persona"},
    "yes": {"en": "Yes", "tr": "Evet"}, "no": {"en": "No", "tr": "Hayir"},
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
    "personality": {"en": "Personality Profile Analysis (Big Five)", "tr": "Kisilik Profili Analizi (Big Five)"},
    "openness": {"en": "Openness", "tr": "Yenilige Aciklik"},
    "conscientiousness": {"en": "Conscientiousness", "tr": "Sorumluluk"},
    "extraversion": {"en": "Extraversion", "tr": "Disa Donukluk"},
    "agreeableness": {"en": "Agreeableness", "tr": "Uyumluluk"},
    "neuroticism": {"en": "Neuroticism", "tr": "Duygusal Hassasiyet"},
    "yes_group": {"en": "Approvers", "tr": "Onaylayanlar"},
    "no_group": {"en": "Rejecters", "tr": "Reddedenler"},
    "city_analysis": {"en": "Regional Approval Analysis", "tr": "Bolgesel Onay Analizi"},
    "city_name": {"en": "City/Region", "tr": "Sehir/Bolge"},
    "total_count": {"en": "Total", "tr": "Toplam"},
    "yes_count_h": {"en": "Yes", "tr": "Evet"},
    "no_count_h": {"en": "No", "tr": "Hayir"},
    "rate_h": {"en": "Approval %", "tr": "Onay %"},
    "income_corr": {"en": "Income vs Decision Correlation", "tr": "Gelir-Karar Korelasyonu"},
    "income_level": {"en": "Income Level", "tr": "Gelir Duzeyi"},
    "platform_desc": {"en": "AI-Powered Synthetic Market Research Platform",
                      "tr": "AI Destekli Sentetik Pazar Arastirma Platformu"},
    "key_finding": {"en": "Key Finding", "tr": "Temel Bulgu"},
}

def L(k, l="en"):
    return _T.get(k, {}).get(l, k)

# ============================================================
#  UTILITY
# ============================================================
def _ss(v, m=200):
    s = str(v) if v else ""
    return s[:m] + ("..." if len(s) > m else "")

def _rsn(r, l="en"):
    if not r: return ""
    try:
        d = json.loads(r) if isinstance(r, str) else r
        if isinstance(d, dict): return d.get(l, d.get("tr", d.get("en", str(r))))
    except Exception: pass
    return str(r)[:200]

def _fd(ds):
    try: return datetime.fromisoformat(str(ds).replace("Z", "+00:00")).strftime("%d %b %Y, %H:%M")
    except Exception: return str(ds)[:19] if ds else "-"

def _hx(c):
    return "#%02x%02x%02x" % (int(c.red * 255), int(c.green * 255), int(c.blue * 255))

def _sf(v, d=0.0):
    try: return float(v)
    except (ValueError, TypeError): return d

# ============================================================
#  STYLES
# ============================================================
def _st():
    return {
        "title": ParagraphStyle("t", fontName=FB, fontSize=26, leading=32, textColor=TD, spaceAfter=4),
        "sub": ParagraphStyle("su", fontName=F, fontSize=12, leading=16, textColor=TL, spaceAfter=20),
        "sec": ParagraphStyle("se", fontName=FB, fontSize=15, leading=20, textColor=TD, spaceBefore=16, spaceAfter=8),
        "ssec": ParagraphStyle("ss", fontName=FB, fontSize=11, leading=15, textColor=TB, spaceBefore=10, spaceAfter=5),
        "body": ParagraphStyle("bo", fontName=F, fontSize=10, leading=14, textColor=TB, spaceAfter=6),
        "body_sm": ParagraphStyle("bosm", fontName=F, fontSize=9, leading=13, textColor=TB, spaceAfter=4),
        "sm": ParagraphStyle("sm", fontName=F, fontSize=8, leading=11, textColor=TB),
        "smb": ParagraphStyle("smb", fontName=FB, fontSize=8, leading=11, textColor=TB),
        "hdr": ParagraphStyle("hdr", fontName=FB, fontSize=8, leading=10, textColor=W),
        "ftr": ParagraphStyle("ftr", fontName=F, fontSize=7, leading=10, textColor=TL, alignment=TA_CENTER),
        "insight": ParagraphStyle("ins", fontName=F, fontSize=10, leading=14, textColor=TD),
        "cover_title": ParagraphStyle("cvt", fontName=FB, fontSize=36, leading=44, textColor=W),
        "cover_sub": ParagraphStyle("cvs", fontName=F, fontSize=14, leading=18, textColor=HexColor("#CBD5E1")),
    }

# ============================================================
#  HEADER / FOOTER
# ============================================================
def _hf(c, doc, data, lang, tier):
    c.saveState()
    w, h = A4
    c.setFillColor(DARK); c.rect(0, h - 14 * mm, w, 14 * mm, fill=True, stroke=False)
    c.setFont(FB, 10); c.setFillColor(CYAN); c.drawString(20 * mm, h - 10 * mm, "SimuTarget.ai")
    c.setFont(F, 8); c.setFillColor(TM)
    c.drawRightString(w - 20 * mm, h - 10 * mm, tier + " | " + L("report", lang))
    c.setStrokeColor(BGB); c.setLineWidth(0.5); c.line(20 * mm, 14 * mm, w - 20 * mm, 14 * mm)
    c.setFont(F, 7); c.setFillColor(TL)
    c.drawString(20 * mm, 9 * mm, _fd(datetime.now().isoformat()))
    c.drawCentredString(w / 2, 9 * mm, L("conf_note", lang))
    c.drawRightString(w - 20 * mm, 9 * mm, L("page", lang) + " " + str(c.getPageNumber()))
    c.restoreState()

# ============================================================
#  VISUAL COMPONENTS
# ============================================================
def _mc(val, label, color=None):
    if color is None: color = CYAN
    hx = _hx(color)
    return Table(
        [[Paragraph('<font color="' + hx + '"><b>' + str(val) + "</b></font>",
            ParagraphStyle("mv", fontName=FB, fontSize=22, alignment=TA_CENTER, leading=26))],
         [Paragraph(label, ParagraphStyle("ml", fontName=F, fontSize=8, alignment=TA_CENTER, textColor=TL, leading=11))]],
        colWidths=[None], rowHeights=[32, 18],
        style=TableStyle([("BACKGROUND", (0, 0), (-1, -1), BGL), ("BOX", (0, 0), (-1, -1), 0.5, BGB),
            ("ROUNDEDCORNERS", [6, 6, 6, 6]), ("TOPPADDING", (0, 0), (-1, 0), 10),
            ("BOTTOMPADDING", (0, -1), (-1, -1), 10), ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8)]))

def _pie(dd, wd=200, ht=150, colors=None):
    d = Drawing(wd, ht); ls = list(dd.keys()); vs = list(dd.values()); total = sum(vs)
    if total <= 0:
        d.add(String(wd // 2, ht // 2, "No data", fontName=F, fontSize=10, fillColor=TL, textAnchor="middle"))
        return d
    p = Pie(); p.x = wd // 2 - 50; p.y = 10; p.width = 100; p.height = 100; p.data = vs
    p.labels = [lb + " (" + str(round(v / total * 100)) + "%)" if v > 0 else "" for lb, v in zip(ls, vs)]
    p.sideLabels = True; p.slices.strokeWidth = 1.5; p.slices.strokeColor = W
    cs = colors or CC
    for i in range(len(vs)):
        p.slices[i].fillColor = cs[i % len(cs)]; p.slices[i].fontName = F; p.slices[i].fontSize = 8
    d.add(p); return d

def _hbar(dd, wd=250, ht=None, color=None, show_pct=False):
    if color is None: color = CYAN
    items = list(dd.items())
    if not items: return Drawing(wd, 30)
    bh = 16; gap = 5; n = len(items)
    if ht is None: ht = max(60, n * (bh + gap) + 20)
    d = Drawing(wd, ht); mx = max((v for _, v in items), default=1) or 1
    lw = 100; ba = wd - lw - 45; sy = ht - 15
    for i, (lb, vl) in enumerate(items):
        y = sy - i * (bh + gap)
        d.add(String(0, y + 3, _ss(lb, 18), fontName=F, fontSize=8, fillColor=TB))
        d.add(Rect(lw, y, ba, bh, fillColor=BGG, strokeColor=None))
        bw = (vl / mx) * ba if mx > 0 else 0
        if bw > 0: d.add(Rect(lw, y, max(bw, 2), bh, fillColor=color, strokeColor=None))
        suffix = "%" if show_pct else ""
        d.add(String(lw + ba + 4, y + 3, str(vl) + suffix, fontName=FB, fontSize=8, fillColor=TB))
    return d

def _big5_chart(yes_avgs, no_avgs, lang="en", wd=None, ht=140):
    traits = ["openness", "conscientiousness", "extraversion", "agreeableness", "neuroticism"]
    if wd is None: wd = 480
    d = Drawing(wd, ht); bar_h = 12; gap = 8; lw = 130; bar_area = wd - lw - 80; sy = ht - 15
    for i, trait in enumerate(traits):
        y = sy - i * (bar_h * 2 + gap)
        d.add(String(0, y + bar_h // 2, L(trait, lang), fontName=FB, fontSize=8, fillColor=TB))
        y_val = yes_avgs.get(trait, 0); n_val = no_avgs.get(trait, 0)
        bw_y = y_val * bar_area
        d.add(Rect(lw, y + bar_h + 1, bar_area, bar_h, fillColor=BGG, strokeColor=None))
        if bw_y > 0: d.add(Rect(lw, y + bar_h + 1, max(bw_y, 2), bar_h, fillColor=GREEN, strokeColor=None))
        d.add(String(lw + bar_area + 4, y + bar_h + 3, str(round(y_val * 10, 1)), fontName=FB, fontSize=7, fillColor=GREEN))
        bw_n = n_val * bar_area
        d.add(Rect(lw, y - 1, bar_area, bar_h, fillColor=BGG, strokeColor=None))
        if bw_n > 0: d.add(Rect(lw, y - 1, max(bw_n, 2), bar_h, fillColor=RED, strokeColor=None))
        d.add(String(lw + bar_area + 4, y + 1, str(round(n_val * 10, 1)), fontName=FB, fontSize=7, fillColor=RED))
    lx = wd - 70
    d.add(Rect(lx, ht - 10, 8, 8, fillColor=GREEN, strokeColor=None))
    d.add(String(lx + 12, ht - 9, L("yes_group", lang), fontName=F, fontSize=7, fillColor=TB))
    d.add(Rect(lx, ht - 22, 8, 8, fillColor=RED, strokeColor=None))
    d.add(String(lx + 12, ht - 21, L("no_group", lang), fontName=F, fontSize=7, fillColor=TB))
    return d

# ============================================================
#  DATA HELPERS
# ============================================================
def _demographics(results):
    gn = {}; ag = {}; ic = {}
    for r in results:
        pd = r.get("persona_data", {}) if isinstance(r.get("persona_data"), dict) else {}
        dec = str(r.get("decision", "")).upper(); isy = dec in ("EVET", "YES", "A")
        g = pd.get("gender", r.get("persona_gender", "?"))
        gn.setdefault(g, {"t": 0, "y": 0}); gn[g]["t"] += 1
        if isy: gn[g]["y"] += 1
        try: a = int(pd.get("age", r.get("persona_age", 0)))
        except: a = 0
        grp = "18-24" if a < 25 else "25-34" if a < 35 else "35-44" if a < 45 else "45-54" if a < 55 else "55+"
        ag.setdefault(grp, {"t": 0, "y": 0}); ag[grp]["t"] += 1
        if isy: ag[grp]["y"] += 1
        inc = pd.get("income_level", r.get("persona_income", "?"))
        ic.setdefault(inc, {"t": 0, "y": 0}); ic[inc]["t"] += 1
        if isy: ic[inc]["y"] += 1
    return gn, ag, ic

def _city_stats(results):
    cities = {}
    for r in results:
        pd = r.get("persona_data", {}) if isinstance(r.get("persona_data"), dict) else {}
        city = pd.get("city", r.get("persona_city", "?"))
        dec = str(r.get("decision", "")).upper(); isy = dec in ("EVET", "YES", "A")
        cities.setdefault(city, {"t": 0, "y": 0, "n": 0}); cities[city]["t"] += 1
        if isy: cities[city]["y"] += 1
        else: cities[city]["n"] += 1
    return cities

def _big5_averages(results):
    traits = ["openness", "conscientiousness", "extraversion", "agreeableness", "neuroticism"]
    ys = {t: 0.0 for t in traits}; ns = {t: 0.0 for t in traits}; yc = 0; nc = 0
    for r in results:
        pd = r.get("persona_data", {}) if isinstance(r.get("persona_data"), dict) else {}
        dec = str(r.get("decision", "")).upper(); isy = dec in ("EVET", "YES", "A")
        if not any(pd.get(t) is not None for t in traits): continue
        if isy:
            yc += 1
            for t in traits: ys[t] += _sf(pd.get(t, 0))
        else:
            nc += 1
            for t in traits: ns[t] += _sf(pd.get(t, 0))
    ya = {t: (ys[t] / yc if yc > 0 else 0) for t in traits}
    na = {t: (ns[t] / nc if nc > 0 else 0) for t in traits}
    return ya, na, yc, nc

def _income_correlation(results):
    order = ["Low", "Lower-Mid", "Middle", "Upper-Mid", "High",
             "Dusuk", "Orta-Dusuk", "Orta", "Orta-Yuksek", "Yuksek"]
    stats = {}
    for r in results:
        pd = r.get("persona_data", {}) if isinstance(r.get("persona_data"), dict) else {}
        inc = pd.get("income_level", "?")
        dec = str(r.get("decision", "")).upper(); isy = dec in ("EVET", "YES", "A")
        stats.setdefault(inc, {"t": 0, "y": 0}); stats[inc]["t"] += 1
        if isy: stats[inc]["y"] += 1
    ordered = [(i, stats[i]) for i in order if i in stats]
    ordered += [(i, s) for i, s in stats.items() if i not in order]
    return ordered

# ============================================================
#  SHARED BUILDERS
# ============================================================
def _info_tbl(rd, tt, lang, uw):
    tm = {"single": L("single", lang), "ab_compare": L("ab", lang), "multi_compare": L("multi", lang)}
    data = [[L("name", lang), _ss(rd.get("campaign_name", "-"), 60)],
            [L("type", lang), tm.get(tt, tt)], [L("region", lang), rd.get("region", "TR")],
            [L("date", lang), _fd(rd.get("created_at", ""))], [L("total", lang), str(rd.get("total_personas", 0))]]
    t = Table(data, colWidths=[uw * 0.3, uw * 0.7])
    t.setStyle(TableStyle([("FONT", (0, 0), (0, -1), FB, 9), ("FONT", (1, 0), (1, -1), F, 9),
        ("TEXTCOLOR", (0, 0), (0, -1), TL), ("TEXTCOLOR", (1, 0), (1, -1), TB),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5), ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("LINEBELOW", (0, 0), (-1, -1), 0.5, BGB)]))
    return t

def _metrics_row(rd, tt, lang, uw):
    ms = []
    if tt == "single":
        apr = _sf(rd.get("approval_rate", 0)); ac = _sf(rd.get("avg_confidence", 0))
        ms = [_mc(str(round(apr, 1)) + "%", L("approval", lang), GREEN if apr >= 50 else RED),
              _mc(str(round(ac, 1)) + "/10", L("avgconf", lang), PURPLE),
              _mc(str(rd.get("yes_count", 0)), L("yes_v", lang), GREEN),
              _mc(str(rd.get("no_count", 0)), L("no_v", lang), RED)]
    elif tt == "ab_compare":
        av = rd.get("a_votes", 0); bv = rd.get("b_votes", 0); nv = rd.get("neither_votes", 0)
        tot = av + bv + nv or 1; ac = _sf(rd.get("avg_confidence", 0))
        ms = [_mc(str(av), L("optA", lang) + " (" + str(round(av / tot * 100)) + "%)", CYAN),
              _mc(str(bv), L("optB", lang) + " (" + str(round(bv / tot * 100)) + "%)", PURPLE),
              _mc(str(nv), L("neither", lang), TL),
              _mc(str(round(ac, 1)) + "/10", L("avgconf", lang), AMBER)]
    else:
        vd = rd.get("vote_distribution", {}); ac = _sf(rd.get("avg_confidence", 0)); tv = sum(vd.values()) or 1
        for i, (lb, ct) in enumerate(list(vd.items())[:3]):
            ms.append(_mc(str(ct), _ss(lb, 12) + " (" + str(round(ct / tv * 100)) + "%)", CC[i % len(CC)]))
        ms.append(_mc(str(round(ac, 1)) + "/10", L("avgconf", lang), AMBER))
    if not ms: return None
    cw = uw / len(ms)
    t = Table([ms], colWidths=[cw] * len(ms))
    t.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (-1, -1), 3), ("RIGHTPADDING", (0, 0), (-1, -1), 3)]))
    return t

def _insight(rd, tt, lang):
    if tt == "single":
        r = _sf(rd.get("approval_rate", 0)); n = rd.get("total_personas", 0)
        if lang == "tr":
            if r >= 70: return str(n) + " persona arasinda %" + str(round(r)) + " onay - guclu performans."
            elif r >= 40: return str(n) + " persona arasinda %" + str(round(r)) + " onay - iyilestirme onerilir."
            else: return str(n) + " persona arasinda %" + str(round(r)) + " onay - yeniden degerlendirilmeli."
        else:
            if r >= 70: return str(round(r)) + "% approval across " + str(n) + " personas - strong performance."
            elif r >= 40: return str(round(r)) + "% across " + str(n) + " personas - moderate interest."
            else: return str(round(r)) + "% across " + str(n) + " personas - needs revision."
    elif tt == "ab_compare":
        a = rd.get("a_votes", 0); b = rd.get("b_votes", 0)
        wn = "A" if a > b else "B" if b > a else "Tie"
        if lang == "tr": return "Secenek " + wn + " kazandi (A:" + str(a) + ", B:" + str(b) + ")."
        return "Option " + wn + " won (A:" + str(a) + ", B:" + str(b) + ")."
    else:
        dist = rd.get("vote_distribution", {})
        if dist:
            wn = max(dist, key=dist.get)
            if lang == "tr": return "En cok oy: " + wn + " (" + str(dist[wn]) + ")."
            return "Top choice: " + wn + " (" + str(dist[wn]) + " votes)."
    return ""

def _insight_box(ins, s, uw):
    return Table([[Paragraph(ins, s["insight"])]], colWidths=[uw],
        style=TableStyle([("BACKGROUND", (0, 0), (-1, -1), CYAN_L), ("BOX", (0, 0), (-1, -1), 1, CYAN),
            ("ROUNDEDCORNERS", [4, 4, 4, 4]), ("TOPPADDING", (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8), ("LEFTPADDING", (0, 0), (-1, -1), 10)]))

def _tbl_style(tbl):
    tbl.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), DARK), ("TEXTCOLOR", (0, 0), (-1, 0), W),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [W, BGL]), ("GRID", (0, 0), (-1, -1), 0.5, BGB),
        ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 5), ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE")]))
    return tbl

# ============================================================
#  PRO REPORT (1-2 pages)
# ============================================================
def generate_pro_report(rd, out, lang="en"):
    _reg(); s = _st(); w, h = A4; uw = w - 40 * mm
    doc = SimpleDocTemplate(out, pagesize=A4, leftMargin=20*mm, rightMargin=20*mm, topMargin=20*mm, bottomMargin=20*mm)
    story = []; tt = rd.get("test_type", "single")

    story.append(Spacer(1, 6 * mm))
    story.append(Table([[""]], colWidths=[50], rowHeights=[3], style=TableStyle([("BACKGROUND", (0, 0), (-1, -1), CYAN)])))
    story.append(Spacer(1, 2 * mm))
    story.append(Paragraph(L("report", lang), s["title"]))
    story.append(Paragraph(_ss(rd.get("campaign_name", ""), 80), s["sub"]))
    story.append(_info_tbl(rd, tt, lang, uw))
    story.append(Spacer(1, 3 * mm))

    ct = rd.get("campaign_content", "")
    if ct:
        story.append(Paragraph(L("content", lang), s["ssec"]))
        story.append(Paragraph(_ss(ct, 300), s["body"]))
        story.append(Spacer(1, 3 * mm))

    ins = _insight(rd, tt, lang)
    if ins: story.append(_insight_box(ins, s, uw)); story.append(Spacer(1, 4 * mm))

    story.append(Paragraph(L("metrics", lang), s["sec"]))
    mr = _metrics_row(rd, tt, lang, uw)
    if mr: story.append(mr)
    story.append(Spacer(1, 5 * mm))

    # Pie chart
    story.append(Paragraph(L("votes", lang), s["sec"]))
    if tt == "single":
        pd = {L("yes", lang): rd.get("yes_count", 0), L("no", lang): rd.get("no_count", 0)}; pc = [GREEN, RED]
    elif tt == "ab_compare":
        pd = {L("optA", lang): rd.get("a_votes", 0), L("optB", lang): rd.get("b_votes", 0), L("neither", lang): rd.get("neither_votes", 0)}; pc = [CYAN, PURPLE, TL]
    else:
        pd = rd.get("vote_distribution", {}); pc = CC
    story.append(_pie(pd, wd=280, ht=160, colors=pc))
    story.append(Spacer(1, 5 * mm))

    # Confidence distribution
    story.append(Paragraph(L("confdist", lang), s["sec"]))
    ch_h = sum(1 for r in rd.get("results", []) if (r.get("confidence") or 0) >= 8)
    ch_m = sum(1 for r in rd.get("results", []) if 5 <= (r.get("confidence") or 0) < 8)
    ch_l = sum(1 for r in rd.get("results", []) if (r.get("confidence") or 0) < 5)
    story.append(_hbar({L("high", lang): ch_h, L("med", lang): ch_m, L("low", lang): ch_l}, wd=int(uw * 0.7), ht=80, color=PURPLE))
    story.append(Spacer(1, 5 * mm))

    # Results table
    story.append(Paragraph(L("responses", lang), s["sec"]))
    results = rd.get("results", [])
    if not results:
        story.append(Paragraph(L("nodata", lang), s["body"]))
    else:
        if tt == "single":
            hdr = [L("persona", lang), L("age", lang), L("gen", lang), L("city", lang), L("dec", lang), L("conf", lang)]
            cw = [uw*0.22, uw*0.08, uw*0.13, uw*0.22, uw*0.18, uw*0.17]
        elif tt == "ab_compare":
            hdr = [L("persona", lang), L("age", lang), L("gen", lang), L("choice", lang), L("conf", lang)]
            cw = [uw*0.28, uw*0.10, uw*0.22, uw*0.20, uw*0.20]
        else:
            hdr = [L("persona", lang), L("age", lang), L("choice", lang), L("conf", lang)]
            cw = [uw*0.30, uw*0.15, uw*0.30, uw*0.25]
        td = [[Paragraph("<b>" + h + "</b>", s["hdr"]) for h in hdr]]
        for r in results[:50]:
            dec = str(r.get("decision", "")); dec_u = dec.upper(); ch = r.get("choice", dec)
            if tt == "single":
                dcl = "#10B981" if dec_u in ("EVET", "YES") else "#EF4444"
                row = [Paragraph(_ss(r.get("persona_name", ""), 25), s["sm"]), Paragraph(str(r.get("persona_age", "")), s["sm"]),
                       Paragraph(_ss(r.get("persona_gender", ""), 10), s["sm"]), Paragraph(_ss(r.get("persona_city", ""), 20), s["sm"]),
                       Paragraph('<font color="' + dcl + '"><b>' + dec + "</b></font>", s["smb"]), Paragraph(str(r.get("confidence", "")), s["sm"])]
            elif tt == "ab_compare":
                cl = "#06B6D4" if str(ch).upper() == "A" else "#8B5CF6" if str(ch).upper() == "B" else "#64748B"
                row = [Paragraph(_ss(r.get("persona_name", ""), 30), s["sm"]), Paragraph(str(r.get("persona_age", "")), s["sm"]),
                       Paragraph(_ss(r.get("persona_gender", ""), 10), s["sm"]),
                       Paragraph('<font color="' + cl + '"><b>' + str(ch) + "</b></font>", s["smb"]), Paragraph(str(r.get("confidence", "")), s["sm"])]
            else:
                row = [Paragraph(_ss(r.get("persona_name", ""), 30), s["sm"]), Paragraph(str(r.get("persona_age", "")), s["sm"]),
                       Paragraph('<font color="#06B6D4"><b>' + _ss(ch, 20) + "</b></font>", s["smb"]), Paragraph(str(r.get("confidence", "")), s["sm"])]
            td.append(row)
        tbl = Table(td, colWidths=cw, repeatRows=1); _tbl_style(tbl); story.append(tbl)

    story.append(Spacer(1, 8 * mm)); story.append(Paragraph(L("gen_by", lang), s["ftr"]))
    tl = L("pro", lang)
    doc.build(story, onFirstPage=lambda c, d: _hf(c, d, rd, lang, tl), onLaterPages=lambda c, d: _hf(c, d, rd, lang, tl))
    return out

# ============================================================
#  BUSINESS REPORT (5-8 pages)
# ============================================================
def generate_business_report(rd, out, lang="en"):
    _reg(); s = _st(); w, h = A4; uw = w - 40 * mm
    doc = SimpleDocTemplate(out, pagesize=A4, leftMargin=20*mm, rightMargin=20*mm, topMargin=20*mm, bottomMargin=20*mm)
    story = []; tt = rd.get("test_type", "single"); results = rd.get("results", [])
    apr = _sf(rd.get("approval_rate", 0)); ac = _sf(rd.get("avg_confidence", 0))

    # === PAGE 1: EXECUTIVE SUMMARY COVER ===
    story.append(Spacer(1, 15 * mm))
    cover = Table(
        [[Paragraph("SimuTarget.ai", ParagraphStyle("cvb", fontName=FB, fontSize=14, textColor=CYAN, leading=18))],
         [Spacer(1, 4 * mm)],
         [Paragraph(L("report", lang), s["cover_title"])],
         [Paragraph(_ss(rd.get("campaign_name", ""), 80), s["cover_sub"])],
         [Spacer(1, 8 * mm)],
         [Paragraph(L("platform_desc", lang), ParagraphStyle("pd", fontName=F, fontSize=10, textColor=TM, leading=14))]],
        colWidths=[uw],
        style=TableStyle([("BACKGROUND", (0, 0), (-1, -1), DARK), ("LEFTPADDING", (0, 0), (-1, -1), 20),
            ("RIGHTPADDING", (0, 0), (-1, -1), 20), ("TOPPADDING", (0, 0), (0, 0), 20),
            ("BOTTOMPADDING", (0, -1), (-1, -1), 20), ("ROUNDEDCORNERS", [8, 8, 8, 8])]))
    story.append(cover)
    story.append(Spacer(1, 8 * mm))

    story.append(Paragraph(L("exec_summary", lang), s["sec"]))
    em = [_mc(str(round(apr, 1)) + "%", L("approval", lang), GREEN if apr >= 50 else RED),
          _mc(str(round(ac, 1)) + "/10", L("avgconf", lang), PURPLE),
          _mc(str(rd.get("total_personas", 0)), L("total", lang), CYAN),
          _mc(str(rd.get("yes_count", 0)) + "/" + str(rd.get("no_count", 0)), L("yes", lang) + " / " + L("no", lang), AMBER)]
    ecw = uw / 4
    story.append(Table([em], colWidths=[ecw]*4, style=TableStyle([("VALIGN",(0,0),(-1,-1),"TOP"),("LEFTPADDING",(0,0),(-1,-1),3),("RIGHTPADDING",(0,0),(-1,-1),3)])))
    story.append(Spacer(1, 5 * mm))

    ins = _insight(rd, tt, lang)
    if ins:
        story.append(Paragraph("<b>" + L("key_finding", lang) + ":</b>", s["ssec"]))
        story.append(_insight_box(ins, s, uw))
    story.append(Spacer(1, 3 * mm))
    story.append(_info_tbl(rd, tt, lang, uw))
    story.append(Spacer(1, 3 * mm))
    cntnt = rd.get("campaign_content", "")
    if cntnt:
        story.append(Paragraph(L("content", lang), s["ssec"]))
        story.append(Paragraph(_ss(cntnt, 600), s["body"]))

    # === PAGE 2: CHARTS ===
    story.append(PageBreak())
    story.append(Paragraph(L("overview", lang), s["sec"]))

    if tt == "single":
        pd_data = {L("yes", lang): rd.get("yes_count", 0), L("no", lang): rd.get("no_count", 0)}; pc = [GREEN, RED]
    elif tt == "ab_compare":
        pd_data = {L("optA", lang): rd.get("a_votes", 0), L("optB", lang): rd.get("b_votes", 0), L("neither", lang): rd.get("neither_votes", 0)}; pc = [CYAN, PURPLE, TL]
    else:
        pd_data = rd.get("vote_distribution", {}); pc = CC
    pie_d = _pie(pd_data, wd=220, ht=150, colors=pc)

    ch = sum(1 for r in results if (r.get("confidence") or 0) >= 8)
    cm2 = sum(1 for r in results if 5 <= (r.get("confidence") or 0) < 8)
    cl = sum(1 for r in results if (r.get("confidence") or 0) < 5)
    cb = _hbar({L("high", lang): ch, L("med", lang): cm2, L("low", lang): cl}, wd=240, ht=80, color=PURPLE)

    story.append(Table([[Paragraph("<b>" + L("votes", lang) + "</b>", s["ssec"]), Paragraph("<b>" + L("confdist", lang) + "</b>", s["ssec"])],
        [pie_d, cb]], colWidths=[uw*0.5, uw*0.5],
        style=TableStyle([("VALIGN",(0,0),(-1,-1),"TOP"),("TOPPADDING",(0,0),(-1,-1),4),("BOTTOMPADDING",(0,0),(-1,-1),4)])))
    story.append(Spacer(1, 6 * mm))

    # Demographics
    story.append(Paragraph(L("demo", lang), s["sec"]))
    gn, ag, ic = _demographics(results)
    gnr = {g + " (" + str(st2["t"]) + ")": (round(st2["y"]/st2["t"]*100) if st2["t"] > 0 else 0) for g, st2 in gn.items()}
    agr = {}
    for a in ["18-24", "25-34", "35-44", "45-54", "55+"]:
        if a in ag:
            st2 = ag[a]; agr[a + " (" + str(st2["t"]) + ")"] = round(st2["y"]/st2["t"]*100) if st2["t"] > 0 else 0
    gb = _hbar(gnr, wd=240, ht=max(60, len(gnr)*22), color=CYAN, show_pct=True)
    ab = _hbar(agr, wd=240, ht=max(60, len(agr)*22), color=PURPLE, show_pct=True)
    story.append(Table([[Paragraph("<b>" + L("gender", lang) + "</b>", s["ssec"]), Paragraph("<b>" + L("agegrp", lang) + "</b>", s["ssec"])],
        [gb, ab]], colWidths=[uw*0.5, uw*0.5], style=TableStyle([("VALIGN",(0,0),(-1,-1),"TOP"),("TOPPADDING",(0,0),(-1,-1),4)])))
    story.append(Spacer(1, 3 * mm))

    if ic:
        icr = {_ss(k, 14) + " (" + str(v["t"]) + ")": (round(v["y"]/v["t"]*100) if v["t"] > 0 else 0) for k, v in ic.items()}
        story.append(Paragraph("<b>" + L("income", lang) + "</b>", s["ssec"]))
        story.append(_hbar(icr, wd=int(uw*0.7), ht=max(60, len(icr)*22), color=GREEN, show_pct=True))

    # === PAGE 3: INCOME CORRELATION + BIG FIVE + CITY ===
    story.append(PageBreak())

    story.append(Paragraph(L("income_corr", lang), s["sec"]))
    inc_data = _income_correlation(results)
    if inc_data:
        ihdr = [L("income_level", lang), L("total_count", lang), L("yes_count_h", lang), L("no_count_h", lang), L("rate_h", lang)]
        itd = [[Paragraph("<b>" + h + "</b>", s["hdr"]) for h in ihdr]]
        for inc_name, st2 in inc_data:
            rate = round(st2["y"]/st2["t"]*100) if st2["t"] > 0 else 0
            rc = "#10B981" if rate >= 50 else "#EF4444" if rate < 30 else "#F59E0B"
            itd.append([Paragraph(_ss(inc_name, 20), s["sm"]), Paragraph(str(st2["t"]), s["sm"]),
                Paragraph('<font color="#10B981"><b>' + str(st2["y"]) + "</b></font>", s["smb"]),
                Paragraph('<font color="#EF4444"><b>' + str(st2["t"]-st2["y"]) + "</b></font>", s["smb"]),
                Paragraph('<font color="' + rc + '"><b>' + str(rate) + "%</b></font>", s["smb"])])
        itbl = Table(itd, colWidths=[uw*0.30, uw*0.15, uw*0.15, uw*0.15, uw*0.25], repeatRows=1)
        _tbl_style(itbl); story.append(itbl)
    story.append(Spacer(1, 6 * mm))

    # Big Five
    story.append(Paragraph(L("personality", lang), s["sec"]))
    ya, na, yc, nc = _big5_averages(results)
    has_b5 = any(v > 0 for v in ya.values()) or any(v > 0 for v in na.values())
    if has_b5:
        story.append(Paragraph(L("yes_group", lang) + " (n=" + str(yc) + ") vs " + L("no_group", lang) + " (n=" + str(nc) + ")", s["body_sm"]))
        story.append(Spacer(1, 2 * mm))
        story.append(_big5_chart(ya, na, lang=lang, wd=int(uw), ht=140))
    else:
        story.append(Paragraph("Big Five data not available." if lang == "en" else "Big Five verisi mevcut degil.", s["body"]))
    story.append(Spacer(1, 6 * mm))

    # City analysis
    story.append(Paragraph(L("city_analysis", lang), s["sec"]))
    cd2 = _city_stats(results)
    if cd2:
        chdr = [L("city_name", lang), L("total_count", lang), L("yes_count_h", lang), L("no_count_h", lang), L("rate_h", lang)]
        ctd = [[Paragraph("<b>" + h + "</b>", s["hdr"]) for h in chdr]]
        for cn, st2 in sorted(cd2.items(), key=lambda x: x[1]["t"], reverse=True)[:20]:
            rate = round(st2["y"]/st2["t"]*100) if st2["t"] > 0 else 0
            rc = "#10B981" if rate >= 50 else "#EF4444" if rate < 30 else "#F59E0B"
            ctd.append([Paragraph(_ss(cn, 25), s["sm"]), Paragraph(str(st2["t"]), s["sm"]),
                Paragraph('<font color="#10B981"><b>' + str(st2["y"]) + "</b></font>", s["smb"]),
                Paragraph('<font color="#EF4444"><b>' + str(st2["n"]) + "</b></font>", s["smb"]),
                Paragraph('<font color="' + rc + '"><b>' + str(rate) + "%</b></font>", s["smb"])])
        ctbl = Table(ctd, colWidths=[uw*0.30, uw*0.15, uw*0.15, uw*0.15, uw*0.25], repeatRows=1)
        _tbl_style(ctbl); story.append(ctbl)

    # === PAGE 4+: DETAILED TABLE WITH REASONING ===
    story.append(PageBreak())
    story.append(Paragraph(L("responses", lang), s["sec"]))
    if not results:
        story.append(Paragraph(L("nodata", lang), s["body"]))
    else:
        if tt == "single":
            hdr = [L("persona", lang), L("age", lang), L("gen", lang), L("occ", lang), L("dec", lang), L("conf", lang), L("reason", lang)]
            cw = [uw*0.12, uw*0.05, uw*0.08, uw*0.12, uw*0.09, uw*0.06, uw*0.48]
        elif tt == "ab_compare":
            hdr = [L("persona", lang), L("age", lang), L("gen", lang), L("choice", lang), L("conf", lang), L("reason", lang)]
            cw = [uw*0.14, uw*0.06, uw*0.10, uw*0.08, uw*0.07, uw*0.55]
        else:
            hdr = [L("persona", lang), L("age", lang), L("choice", lang), L("conf", lang), L("reason", lang)]
            cw = [uw*0.14, uw*0.07, uw*0.10, uw*0.07, uw*0.62]
        td = [[Paragraph("<b>" + h + "</b>", s["hdr"]) for h in hdr]]
        for r in results[:100]:
            rsn = _rsn(r.get("reasoning", ""), lang)
            if len(rsn) > 180: rsn = rsn[:180] + "..."
            dec = str(r.get("decision", "")); dec_u = dec.upper(); chv = r.get("choice", dec)
            if tt == "single":
                dcl = "#10B981" if dec_u in ("EVET", "YES") else "#EF4444"
                row = [Paragraph(_ss(r.get("persona_name", ""), 18), s["sm"]), Paragraph(str(r.get("persona_age", "")), s["sm"]),
                    Paragraph(_ss(r.get("persona_gender", ""), 8), s["sm"]), Paragraph(_ss(r.get("persona_occupation", ""), 18), s["sm"]),
                    Paragraph('<font color="' + dcl + '"><b>' + dec + "</b></font>", s["smb"]),
                    Paragraph(str(r.get("confidence", "")), s["sm"]), Paragraph(_ss(rsn, 180), s["sm"])]
            elif tt == "ab_compare":
                ccl = "#06B6D4" if str(chv).upper() == "A" else "#8B5CF6" if str(chv).upper() == "B" else "#64748B"
                row = [Paragraph(_ss(r.get("persona_name", ""), 20), s["sm"]), Paragraph(str(r.get("persona_age", "")), s["sm"]),
                    Paragraph(_ss(r.get("persona_gender", ""), 8), s["sm"]),
                    Paragraph('<font color="' + ccl + '"><b>' + str(chv) + "</b></font>", s["smb"]),
                    Paragraph(str(r.get("confidence", "")), s["sm"]), Paragraph(_ss(rsn, 180), s["sm"])]
            else:
                row = [Paragraph(_ss(r.get("persona_name", ""), 20), s["sm"]), Paragraph(str(r.get("persona_age", "")), s["sm"]),
                    Paragraph('<font color="#06B6D4"><b>' + _ss(chv, 15) + "</b></font>", s["smb"]),
                    Paragraph(str(r.get("confidence", "")), s["sm"]), Paragraph(_ss(rsn, 180), s["sm"])]
            td.append(row)
        tbl = Table(td, colWidths=cw, repeatRows=1)
        tbl.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,0),DARK),("TEXTCOLOR",(0,0),(-1,0),W),
            ("ROWBACKGROUNDS",(0,1),(-1,-1),[W,BGL]),("GRID",(0,0),(-1,-1),0.5,BGB),
            ("TOPPADDING",(0,0),(-1,-1),3),("BOTTOMPADDING",(0,0),(-1,-1),3),
            ("LEFTPADDING",(0,0),(-1,-1),4),("RIGHTPADDING",(0,0),(-1,-1),4),("VALIGN",(0,0),(-1,-1),"TOP")]))
        story.append(tbl)

    story.append(Spacer(1, 8 * mm)); story.append(Paragraph(L("gen_by", lang), s["ftr"]))
    tl = L("biz", lang)
    doc.build(story, onFirstPage=lambda c, d: _hf(c, d, rd, lang, tl), onLaterPages=lambda c, d: _hf(c, d, rd, lang, tl))
    return out

# ============================================================
#  ENTRY POINT
# ============================================================
def generate_report(rd, out, tier="pro", lang="en"):
    if tier in ("business", "enterprise"):
        return generate_business_report(rd, out, lang)
    return generate_pro_report(rd, out, lang)
