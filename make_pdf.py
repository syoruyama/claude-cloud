from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table,
                                 TableStyle, HRFlowable)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.graphics.shapes import Drawing, Rect, String
from reportlab.graphics import renderPDF
import os

# ── フォント ──────────────────────────────────────────────────
FONT_PATHS = [
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/noto-cjk/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/truetype/fonts-japanese-gothic.ttf",
]
FONT_NAME = "NotoSans"
for fp in FONT_PATHS:
    if os.path.exists(fp):
        pdfmetrics.registerFont(TTFont(FONT_NAME, fp))
        break
else:
    FONT_NAME = "Helvetica"

# ── データ ────────────────────────────────────────────────────
DATA = [
    ("違反クチコミのブロック・削除",   240, 292, "+21.7%", True),
    ("不正確な修正提案のブロック",      70,  79,  "+12.9%", True),
    ("偽ビジネスプロフィール削除",      12,  13,  "+8.3%",  True),
    ("アカウントへの投稿制限",          9.0, 7.82, "-13.1%", False),
]
UNITS = {
    "違反クチコミのブロック・削除":  "百万件",
    "不正確な修正提案のブロック":   "百万件",
    "偽ビジネスプロフィール削除":   "百万件",
    "アカウントへの投稿制限":       "十万件",
}

BLUE   = colors.HexColor("#2b6cb0")
GREEN  = colors.HexColor("#276749")
LBLUE  = colors.HexColor("#bee3f8")
LGREEN = colors.HexColor("#c6f6d5")
RED    = colors.HexColor("#c53030")
GRAY   = colors.HexColor("#718096")
BGRAY  = colors.HexColor("#edf2f7")

W, H = A4
MARGIN = 18 * mm

doc = SimpleDocTemplate(
    "/home/user/claude-cloud/google-maps-transparency-2024-2025.pdf",
    pagesize=A4,
    leftMargin=MARGIN, rightMargin=MARGIN,
    topMargin=MARGIN,  bottomMargin=MARGIN,
)

styles = getSampleStyleSheet()
def S(name, **kw):
    return ParagraphStyle(name, fontName=FONT_NAME, **kw)

title_style   = S("title",   fontSize=16, leading=22, textColor=colors.HexColor("#2d3748"), spaceAfter=2)
sub_style     = S("sub",     fontSize=9,  leading=13, textColor=GRAY, spaceAfter=14)
h2_style      = S("h2",      fontSize=11, leading=16, textColor=colors.HexColor("#2d3748"), spaceBefore=14, spaceAfter=8)
body_style    = S("body",    fontSize=9,  leading=14, textColor=colors.HexColor("#2d3748"))
note_style    = S("note",    fontSize=8,  leading=12, textColor=GRAY)
cell_style    = S("cell",    fontSize=9,  leading=13)
header_style  = S("header",  fontSize=8,  leading=12, textColor=GRAY)

story = []

# ── タイトル ──────────────────────────────────────────────────
story.append(Paragraph("Google マップ コンテンツ信頼性・安全性レポート", title_style))
story.append(Paragraph("2024年 vs 2025年 比較", sub_style))
story.append(HRFlowable(width="100%", thickness=1, color=BGRAY, spaceAfter=10))

# ── サマリーカード（テーブル形式） ────────────────────────────
story.append(Paragraph("サマリー", h2_style))

def fmt(v):
    if v >= 100:  return f"{int(v):,}百万件"
    if v >= 10:   return f"{int(v)}百万件"
    if v >= 1:    return f"{v:.1f}千万件"
    return f"{v*10:.0f}十万件"

card_data = [
    [
        Paragraph("カテゴリー", header_style),
        Paragraph("2024年", header_style),
        Paragraph("2025年", header_style),
        Paragraph("変化率", header_style),
    ]
]
ICONS = ["⭐", "✏️", "🏢", "👤"]
for i, (label, v24, v25, chg, up) in enumerate(DATA):
    chg_color = RED if up else GREEN
    card_data.append([
        Paragraph(f"{ICONS[i]} {label}", cell_style),
        Paragraph(fmt(v24), cell_style),
        Paragraph(fmt(v25), cell_style),
        Paragraph(f'<font color="{"#c53030" if up else "#276749"}"><b>{chg}</b></font>', cell_style),
    ])

card_table = Table(card_data, colWidths=[85*mm, 32*mm, 32*mm, 24*mm])
card_table.setStyle(TableStyle([
    ("BACKGROUND",  (0,0), (-1,0), BGRAY),
    ("FONTNAME",    (0,0), (-1,-1), FONT_NAME),
    ("FONTSIZE",    (0,0), (-1,-1), 9),
    ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.white, colors.HexColor("#f7fafc")]),
    ("GRID",        (0,0), (-1,-1), 0.5, colors.HexColor("#e2e8f0")),
    ("VALIGN",      (0,0), (-1,-1), "MIDDLE"),
    ("TOPPADDING",  (0,0), (-1,-1), 7),
    ("BOTTOMPADDING",(0,0),(-1,-1), 7),
    ("LEFTPADDING", (0,0), (-1,-1), 8),
]))
story.append(card_table)
story.append(Spacer(1, 14))

# ── 新指標 ─────────────────────────────────────────────────────
extra = Table(
    [[Paragraph("✅  2025年新指標：有益なクチコミの公開支援  10億件以上（2024年は非開示）", cell_style)]],
    colWidths=[173*mm]
)
extra.setStyle(TableStyle([
    ("BACKGROUND", (0,0), (-1,-1), LGREEN),
    ("FONTNAME",   (0,0), (-1,-1), FONT_NAME),
    ("TOPPADDING", (0,0), (-1,-1), 8),
    ("BOTTOMPADDING",(0,0),(-1,-1), 8),
    ("LEFTPADDING",(0,0), (-1,-1), 10),
    ("ROUNDEDCORNERS", [4]),
]))
story.append(extra)
story.append(Spacer(1, 18))

# ── 棒グラフ ──────────────────────────────────────────────────
story.append(Paragraph("カテゴリー別 件数比較（棒グラフ）", h2_style))

BAR_W   = 155 * mm
BAR_H   = 14
GAP     = 4
GROUP_H = BAR_H * 2 + GAP + 22
LABEL_W = 0
MAX_VALS = [max(v24, v25) for _, v24, v25, _, _ in DATA]

total_h = GROUP_H * len(DATA) + 10
d = Drawing(BAR_W, total_h)

for gi, (label, v24, v25, chg, up) in enumerate(DATA):
    y_base = total_h - (gi + 1) * GROUP_H + 6
    max_v  = MAX_VALS[gi]
    scale  = (BAR_W - 2) / max_v

    # ラベル
    d.add(String(0, y_base + BAR_H * 2 + GAP + 4, label,
                 fontName=FONT_NAME, fontSize=8, fillColor=colors.HexColor("#4a5568")))

    for yi, (val, clr, tag) in enumerate([(v24, BLUE, "2024"), (v25, GREEN, "2025")]):
        y = y_base + yi * (BAR_H + GAP)
        bw = val * scale
        # 背景
        d.add(Rect(0, y, BAR_W - 2, BAR_H, fillColor=BGRAY, strokeColor=None))
        # バー
        d.add(Rect(0, y, bw, BAR_H, fillColor=clr, strokeColor=None))
        # タグ
        d.add(String(bw + 4, y + 3, f"{tag}: {fmt(val)}",
                     fontName=FONT_NAME, fontSize=7, fillColor=clr))

story.append(d)
story.append(Spacer(1, 18))

# ── 増減まとめ表 ──────────────────────────────────────────────
story.append(Paragraph("増減まとめ", h2_style))

tbl_data = [
    [
        Paragraph("カテゴリー", header_style),
        Paragraph("2024年", header_style),
        Paragraph("2025年", header_style),
        Paragraph("変化率", header_style),
        Paragraph("評価", header_style),
    ]
]
COMMENTS = ["スパム対策強化", "情報精度向上", "偽業者排除強化", "予防検知が向上？"]
for i, (label, v24, v25, chg, up) in enumerate(DATA):
    tbl_data.append([
        Paragraph(f"{ICONS[i]} {label}", cell_style),
        Paragraph(fmt(v24), cell_style),
        Paragraph(fmt(v25), cell_style),
        Paragraph(f'<font color="{"#c53030" if up else "#276749"}"><b>{chg}</b></font>', cell_style),
        Paragraph(COMMENTS[i], cell_style),
    ])
tbl_data.append([
    Paragraph("✅ 有益クチコミ支援（新指標）", cell_style),
    Paragraph("—", cell_style),
    Paragraph("10億件以上", cell_style),
    Paragraph("—", cell_style),
    Paragraph("新規開示", cell_style),
])

summary_table = Table(tbl_data, colWidths=[70*mm, 26*mm, 26*mm, 22*mm, 29*mm])
summary_table.setStyle(TableStyle([
    ("BACKGROUND",  (0,0), (-1,0), BGRAY),
    ("FONTNAME",    (0,0), (-1,-1), FONT_NAME),
    ("FONTSIZE",    (0,0), (-1,-1), 9),
    ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.white, colors.HexColor("#f7fafc")]),
    ("GRID",        (0,0), (-1,-1), 0.5, colors.HexColor("#e2e8f0")),
    ("VALIGN",      (0,0), (-1,-1), "MIDDLE"),
    ("TOPPADDING",  (0,0), (-1,-1), 6),
    ("BOTTOMPADDING",(0,0),(-1,-1), 6),
    ("LEFTPADDING", (0,0), (-1,-1), 8),
    ("BACKGROUND",  (0,-1), (-1,-1), LGREEN),
]))
story.append(summary_table)
story.append(Spacer(1, 16))

# ── ポイント ──────────────────────────────────────────────────
story.append(HRFlowable(width="100%", thickness=0.5, color=BGRAY, spaceAfter=8))
points = [
    "スパム・偽情報対策は全体的に強化（違反クチコミ削除が約5,200万件増）",
    "アカウント投稿制限は減少 → 事後制裁より事前・自動検知にシフトした可能性",
    "2025年から「有益クチコミの支援（10億件+）」を新指標として開示 → 削除だけでなくプラス面も強調",
]
for p in points:
    story.append(Paragraph(f"• {p}", body_style))
    story.append(Spacer(1, 4))

story.append(Spacer(1, 10))
story.append(Paragraph(
    "出典: Google マップ コンテンツの信頼性と安全性に関するレポート (transparencyreport.google.com)　|　作成: 2026年4月",
    note_style
))

doc.build(story)
print("PDF generated successfully.")
