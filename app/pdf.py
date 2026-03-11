from flask import Blueprint, send_file, abort
from flask_login import login_required, current_user
from io import BytesIO
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch

from .models import Person

pdf_bp = Blueprint("pdf", __name__)

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