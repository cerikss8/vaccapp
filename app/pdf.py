from flask import Blueprint, send_file, abort
from flask_login import login_required, current_user
from io import BytesIO
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
)
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.lib import colors
from datetime import datetime

from .models import Person

pdf_bp = Blueprint("pdf", __name__)

@pdf_bp.route("/export-pdf/<int:person_id>")
@login_required
def export_pdf(person_id):
    person = Person.query.get_or_404(person_id)
    if person.user_id != current_user.id:
        abort(403)

    buffer = BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=40,
        leftMargin=40,
        topMargin=60,
        bottomMargin=60
    )

    styles = getSampleStyleSheet()
    elements = []

    # 🧠 Header
    elements.append(Paragraph(
        f"Vaccinationsintyg",
        styles["Title"]
    ))

    elements.append(Spacer(1, 0.2 * inch))

    elements.append(Paragraph(
        f"<b>Namn:</b> {person.first_name} {person.last_name or ''}",
        styles["Normal"]
    ))

    elements.append(Paragraph(
        f"<b>Exporterat:</b> {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        styles["Normal"]
    ))

    elements.append(Spacer(1, 0.3 * inch))

    # 💉 Vaccinationer
    for vaccination in person.vaccinations:

        elements.append(Paragraph(
            f"<b>{vaccination.name}</b>",
            styles["Heading2"]
        ))

        data = [["Dos", "Datum", "Vårdgivare", "Kommentar"]]

        if vaccination.doses:
            for dose in vaccination.doses:
                data.append([
                    f"Dos {dose.dose_number}",
                    str(dose.date_taken) if dose.date_taken else "Kommande",
                    dose.provider if dose.provider else "-",
                    dose.comment if dose.comment else "-"
                ])
        else:
            data.append(["-", "-", "Inga doser registrerade"])

        table = Table(data, colWidths=[80, 120, 200])

        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e9f2ff")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.black),

            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),

            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),

            ("ROWBACKGROUNDS", (0, 1), (-1, -1),
             [colors.whitesmoke, colors.lightgrey]),

            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ]))

        elements.append(table)
        elements.append(Spacer(1, 0.3 * inch))

    elements.append(Paragraph(
        f"{len(vaccination.doses)} / {vaccination.total_doses} doser",
        styles["Normal"]
    ))


    # 🧾 Footer funktion
    def add_footer(canvas, doc):
        canvas.saveState()

        footer_text = "VaccApp • vaccapp.com"
        page_number_text = f"Sida {doc.page}"

        canvas.setFont("Helvetica", 9)
        canvas.setFillColor(colors.grey)

        width, height = A4

        canvas.drawString(40, 20, footer_text)
        canvas.drawRightString(width - 40, 20, page_number_text)

        canvas.restoreState()

    # 📄 Build PDF med footer på varje sida
    doc.build(elements, onFirstPage=add_footer, onLaterPages=add_footer)

    buffer.seek(0)

    filename = f"vaccinationsintyg_{person.first_name}.pdf"

    return send_file(
        buffer,
        as_attachment=True,
        download_name=filename,
        mimetype="application/pdf"
    )




'''
@pdf_bp.route("/export-pdf/<int:person_id>")
@login_required
def export_pdf(person_id):
    person = Person.query.get_or_404(person_id)
    if person.user_id != current_user.id:
        abort(403)

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    elements = []

    elements.append(Paragraph(
        f"Vaccinationsintyg för {person.first_name} {person.last_name or ''}".strip(),
        styles["Title"]
    ))
    elements.append(Spacer(1, 0.3 * inch))

    for vaccination in person.vaccinations:
        elements.append(Paragraph(
            f"<b>Vaccination:</b> {vaccination.name}",
            styles["Heading2"]
        ))

        if vaccination.doses:
            for dose in vaccination.doses:
                elements.append(Paragraph(
                    f"Dos {dose.dose_number} - {dose.date_taken or ''}"
                    f"{' - ' + dose.comment if dose.comment else ''}",
                    styles["Normal"]
                ))
        else:
            elements.append(Paragraph("Inga doser registrerade.", styles["Normal"]))

        elements.append(Spacer(1, 0.2 * inch))

    doc.build(elements)
    buffer.seek(0)

    filename = f"vaccinationsintyg_{person.first_name}.pdf"
    return send_file(buffer, as_attachment=True, download_name=filename, mimetype="application/pdf")
'''