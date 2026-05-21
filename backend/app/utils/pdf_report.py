import io
from datetime import datetime
from pathlib import Path

from PIL import Image as PILImage
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm, mm
from reportlab.pdfgen import canvas
from reportlab.platypus import (
    Image,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


COLOR_PRIMARY = colors.HexColor("#3b82f6")
COLOR_TEXT = colors.HexColor("#1a1d24")
COLOR_TEXT_DIM = colors.HexColor("#6b7280")
COLOR_BORDER = colors.HexColor("#e5e7eb")
COLOR_SURFACE = colors.HexColor("#f9fafb")
COLOR_BAD = colors.HexColor("#dc2626")
COLOR_GOOD = colors.HexColor("#16a34a")

CLASS_COLORS = {
    "glioma": colors.HexColor("#e74c3c"),
    "meningioma": colors.HexColor("#e67e22"),
    "notumor": colors.HexColor("#27ae60"),
    "pituitary": colors.HexColor("#9b59b6"),
}

CLASS_LABELS = {
    "glioma": "Glioma",
    "meningioma": "Meningioma",
    "notumor": "No Tumor",
    "pituitary": "Pituitary",
}


#styles
def _build_styles():
    styles = getSampleStyleSheet()
    return {
        "title": ParagraphStyle(
            "Title", parent=styles["Heading1"],
            fontSize=20, textColor=COLOR_TEXT, alignment=TA_CENTER, spaceAfter=2,
        ),
        "subtitle": ParagraphStyle(
            "Subtitle", parent=styles["Normal"],
            fontSize=10, textColor=COLOR_TEXT_DIM, alignment=TA_CENTER, spaceAfter=14,
        ),
        "section_header": ParagraphStyle(
            "SectionHeader", parent=styles["Heading2"],
            fontSize=12, textColor=COLOR_TEXT, spaceBefore=12, spaceAfter=6,
        ),
        "body": ParagraphStyle(
            "Body", parent=styles["Normal"],
            fontSize=10, textColor=COLOR_TEXT, leading=14,
        ),
        "result_label": ParagraphStyle(
            "ResultLabel", parent=styles["Normal"],
            fontSize=8, textColor=COLOR_TEXT_DIM, alignment=TA_CENTER, spaceAfter=4,
        ),
        "result_value": ParagraphStyle(
            "ResultValue", parent=styles["Normal"],
            fontSize=20, textColor=COLOR_TEXT, alignment=TA_CENTER, spaceAfter=4,
        ),
        "result_confidence": ParagraphStyle(
            "ResultConfidence", parent=styles["Normal"],
            fontSize=11, textColor=COLOR_TEXT_DIM, alignment=TA_CENTER,
        ),
        "disclaimer": ParagraphStyle(
            "Disclaimer", parent=styles["Normal"],
            fontSize=8, textColor=COLOR_TEXT_DIM, alignment=TA_LEFT, leading=11,
        ),
    }


#probabaility graph
def _make_probability_bar(probability: float, color: colors.Color, width=8 * cm):
    fill_width = max(probability * width, 1 * mm)
    return Table(
        [[""]],
        colWidths=[fill_width],
        rowHeights=[6],
        style=TableStyle([("BACKGROUND", (0, 0), (-1, -1), color)]),
    )


#lines
def _draw_header_footer(canvas_obj: canvas.Canvas, doc):
    canvas_obj.saveState()
    canvas_obj.setStrokeColor(COLOR_BORDER)
    canvas_obj.setLineWidth(0.5)
    canvas_obj.line(2 * cm, A4[1] - 1.5 * cm, A4[0] - 2 * cm, A4[1] - 1.5 * cm)
    canvas_obj.line(2 * cm, 1.8 * cm, A4[0] - 2 * cm, 1.8 * cm)
    canvas_obj.setFont("Helvetica", 8)
    canvas_obj.setFillColor(COLOR_TEXT_DIM)
    canvas_obj.drawString(
        2 * cm, 1.3 * cm,
        f"NeuroScan Report  |  Generated {datetime.now().strftime('%Y-%m-%d %H:%M')}",
    )
    canvas_obj.drawRightString(A4[0] - 2 * cm, 1.3 * cm, f"Page {doc.page}")
    canvas_obj.restoreState()


#generate report
def generate_scan_report(
    *,
    output_path_or_buffer,
    user_username: str,
    user_email: str,
    scan_id: str,
    upload_date: datetime,
    original_filename: str,
    mri_image_path: Path,
    has_tumor: bool,
    tumor_class: str,
    confidence: float,
    all_probabilities: dict,
) -> None:
    styles = _build_styles()

    doc = SimpleDocTemplate(
        output_path_or_buffer,
        pagesize=A4,
        leftMargin=2 * cm, rightMargin=2 * cm,
        topMargin=2 * cm, bottomMargin=2.5 * cm,
        title=f"NeuroScan Report — {scan_id}",
        author="NeuroScan",
    )

    story = []

    story.append(Paragraph("NeuroScan", styles["title"]))
    story.append(Paragraph("Brain Tumor MRI Classification Report", styles["subtitle"]))

    info_data = [
        ["Patient (Username)", user_username],
        ["Email", user_email],
        ["Report Date", datetime.now().strftime("%d %B %Y, %H:%M")],
        ["Scan Date", upload_date.strftime("%d %B %Y, %H:%M")],
        ["Scan ID", str(scan_id)[:18] + "..."],
        ["Original File", original_filename],
    ]
    info_table = Table(info_data, colWidths=[5 * cm, 11 * cm])
    info_table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("TEXTCOLOR", (0, 0), (0, -1), COLOR_TEXT_DIM),
        ("TEXTCOLOR", (1, 0), (1, -1), COLOR_TEXT),
        ("FONTNAME", (1, 0), (1, -1), "Helvetica-Bold"),
        ("BACKGROUND", (0, 0), (-1, -1), COLOR_SURFACE),
        ("BOX", (0, 0), (-1, -1), 0.5, COLOR_BORDER),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, COLOR_BORDER),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(info_table)
    story.append(Spacer(1, 12))

    story.append(Paragraph("MRI Image", styles["section_header"]))
    if mri_image_path.exists():
        img_data = _resize_image_for_pdf(mri_image_path, max_dim=300)
        story.append(Image(img_data, width=5.5 * cm, height=5.5 * cm, kind="proportional"))
    else:
        story.append(Paragraph("<i>Image file not available.</i>", styles["body"]))
    story.append(Spacer(1, 8))

    story.append(Paragraph("Diagnostic Result", styles["section_header"]))
    label_color = COLOR_BAD if has_tumor else COLOR_GOOD
    result_value_html = (
        f'<font color="#{label_color.hexval()[2:]}">'
        f'<b>{CLASS_LABELS.get(tumor_class, tumor_class)}</b>'
        f'</font>'
    )
    result_inner = [
        [Paragraph("PREDICTION", styles["result_label"])],
        [Paragraph(result_value_html, styles["result_value"])],
        [Paragraph(f"Confidence: {confidence * 100:.2f}%", styles["result_confidence"])],
    ]
    result_table = Table(result_inner, colWidths=[16 * cm])
    result_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), COLOR_SURFACE),
        ("BOX", (0, 0), (-1, -1), 1.5, label_color),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(result_table)
    story.append(Spacer(1, 10))

    story.append(Paragraph("All Class Probabilities", styles["section_header"]))
    sorted_probs = sorted(all_probabilities.items(), key=lambda x: -x[1])
    prob_rows = []
    for name, prob in sorted_probs:
        label = CLASS_LABELS.get(name, name)
        bar_color = CLASS_COLORS.get(name, COLOR_PRIMARY)
        bar = _make_probability_bar(prob, bar_color)
        prob_rows.append([
            Paragraph(f"<b>{label}</b>", styles["body"]),
            bar,
            Paragraph(
                f"{prob * 100:.2f}%",
                ParagraphStyle("ProbValue", parent=styles["body"], alignment=2),
            ),
        ])
    prob_table = Table(prob_rows, colWidths=[3.5 * cm, 10 * cm, 2.5 * cm])
    prob_table.setStyle(TableStyle([
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    story.append(prob_table)
    story.append(Spacer(1, 12))

    disclaimer_text = (
        "<b>Important Notice:</b> This report is generated by an academic AI system "
        "(NeuroScan) trained on the Nickparvar Brain Tumor MRI Dataset using "
        "ResNet50V2 transfer learning. The classification provided is for "
        "educational and research purposes only and must not be considered a "
        "medical diagnosis. Any clinical decision should be based on evaluation "
        "by qualified healthcare professionals."
    )
    story.append(Paragraph(disclaimer_text, styles["disclaimer"]))

    doc.build(story, onFirstPage=_draw_header_footer, onLaterPages=_draw_header_footer)


#resize image 
def _resize_image_for_pdf(image_path: Path, max_dim: int = 400) -> io.BytesIO:
    img = PILImage.open(image_path).convert("RGB")
    img.thumbnail((max_dim, max_dim), PILImage.LANCZOS)
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=88)
    buf.seek(0)
    return buf
