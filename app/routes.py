from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from flask_login import login_required, current_user
from app import db
from app.models import Person, Vaccination, Dose
from datetime import datetime

main_bp = Blueprint("main", __name__)

@main_bp.route("/")
def index():
    return render_template("index.html", show_navbar=False)


@main_bp.route("/dashboard")
@login_required
def dashboard():
    persons = Person.query.filter_by(user_id=current_user.id).all()
    return render_template("dashboard.html", persons=persons, show_navbar=True)


# --- Person management ---
@main_bp.route("/person/add", methods=["GET", "POST"])
@login_required
def add_person():
    if request.method == "POST":
        first_name = request.form.get("first_name")
        last_name = request.form.get("last_name")
        relationship = request.form.get("relationship", "child")
        dob_str = request.form.get("date_of_birth")  # YYYY-MM-DD

        date_of_birth = None
        if dob_str:
            date_of_birth = datetime.strptime(dob_str, "%Y-%m-%d").date()

        if not first_name:
            flash("Förnamn krävs.", "danger")
            return redirect(url_for("main.add_person"))

        person = Person(
            user_id=current_user.id,
            first_name=first_name,
            last_name=last_name,
            relationship=relationship,
            date_of_birth=date_of_birth,
        )
        db.session.add(person)
        db.session.commit()

        flash("Person tillagd.", "success")
        return redirect(url_for("main.dashboard"))

    return render_template("person_form.html", person=None, show_navbar=True)


@main_bp.route("/person/<int:person_id>")
@login_required
def person_detail(person_id):
    person = Person.query.filter_by(id=person_id, user_id=current_user.id).first_or_404()
    return render_template("person_detail.html", person=person, show_navbar=True)


@main_bp.route("/person/<int:person_id>/edit", methods=["GET", "POST"])
@login_required
def edit_person(person_id):
    person = Person.query.filter_by(id=person_id, user_id=current_user.id).first_or_404()

    if request.method == "POST":
        person.first_name = request.form.get("first_name")
        person.last_name = request.form.get("last_name")
        person.relationship = request.form.get("relationship", person.relationship)

        dob_str = request.form.get("date_of_birth")
        person.date_of_birth = datetime.strptime(dob_str, "%Y-%m-%d").date() if dob_str else None

        db.session.commit()
        flash("Person uppdaterad.", "success")
        return redirect(url_for("main.profile"))

    return render_template("person_form.html", person=person, show_navbar=True)


@main_bp.route("/person/<int:person_id>/delete", methods=["POST"])
@login_required
def delete_person(person_id):
    person = Person.query.filter_by(id=person_id, user_id=current_user.id).first_or_404()

    # Skydd: hindra att man tar bort "self" om du vill
    if person.relationship == "self":
        flash("Du kan inte ta bort din primära profil.", "danger")
        return redirect(url_for("main.profile"))

    db.session.delete(person)
    db.session.commit()
    flash("Person borttagen.", "success")
    return redirect(url_for("main.profile"))



# --- Vaccinations ---
@main_bp.route("/person/<int:person_id>/vaccination/add", methods=["GET", "POST"])
@login_required
def add_vaccination(person_id):
    person = Person.query.filter_by(id=person_id, user_id=current_user.id).first_or_404()

    if request.method == "POST":
        name = request.form.get("name")
        total_doses = request.form.get("total_doses")

        if not name:
            flash("Vaccinationsnamn krävs.", "danger")
            return redirect(url_for("main.add_vaccination", person_id=person.id))

        if not total_doses:
            flash("Ange totalt antal doser.", "danger")
            return redirect(url_for("main.add_vaccination", person_id=person.id))

        vaccination = Vaccination(
            name=name,
            total_doses=int(total_doses),
            person_id=person.id
        )
        
        db.session.add(vaccination)
        db.session.commit()
        return redirect(url_for("main.person_detail", person_id=person.id))

    return render_template("vaccination_form.html", vaccination=None, person=person, show_navbar=True)


@main_bp.route("/vaccination/edit/<int:vaccination_id>", methods=["GET", "POST"])
@login_required
def edit_vaccination(vaccination_id):
    vaccination = Vaccination.query.get_or_404(vaccination_id)

    # NYTT ägarskydd via person -> user
    if vaccination.person.user_id != current_user.id:
        abort(403)

    if request.method == "POST":
        vaccination.name = request.form.get("name")
        vaccination.total_doses = int(request.form.get("total_doses"))
        db.session.commit()
        return redirect(url_for("main.person_detail", person_id=vaccination.person_id))

    return render_template("vaccination_form.html", vaccination=vaccination, person=vaccination.person, show_navbar=True)


@main_bp.route("/vaccination/delete/<int:vaccination_id>", methods=["POST"])
@login_required
def delete_vaccination(vaccination_id):
    vaccination = Vaccination.query.get_or_404(vaccination_id)

    if vaccination.person.user_id != current_user.id:
        abort(403)

    person_id = vaccination.person_id
    db.session.delete(vaccination)
    db.session.commit()
    return redirect(url_for("main.person_detail", person_id=person_id))


# --- Doses ---
@main_bp.route("/dose/add/<int:vaccination_id>", methods=["GET", "POST"])
@login_required
def add_dose(vaccination_id):
    vaccination = Vaccination.query.get_or_404(vaccination_id)

    # KRITISK FIX: ägarskydd
    if vaccination.person.user_id != current_user.id:
        abort(403)

    if request.method == "POST":
        dose_number = request.form.get("dose_number")
        date_str = request.form.get("date_taken")
        provider = request.form.get("provider").strip() or None
        comment = request.form.get("comment").strip() or None

        date_taken = None
        if date_str:
            date_taken = datetime.strptime(date_str, "%Y-%m-%d").date()

        dose = Dose(
            dose_number=int(dose_number),
            date_taken=date_taken,
            provider=provider,
            comment=comment,
            vaccination_id=vaccination.id
        )
        db.session.add(dose)
        db.session.commit()
        return redirect(url_for("main.person_detail", person_id=vaccination.person_id))

    return render_template("dose_form.html", dose=None, vaccination=vaccination, show_navbar=True)


@main_bp.route("/dose/edit/<int:dose_id>", methods=["GET", "POST"])
@login_required
def edit_dose(dose_id):
    dose = Dose.query.get_or_404(dose_id)

    if dose.vaccination.person.user_id != current_user.id:
        abort(403)

    if request.method == "POST":
        dose.dose_number = int(request.form.get("dose_number"))
        date_str = request.form.get("date_taken")
        dose.date_taken = datetime.strptime(date_str, "%Y-%m-%d").date() if date_str else None
        dose.provider = request.form.get("provider").strip() or None
        dose.comment = request.form.get("comment").strip() or None

        db.session.commit()
        return redirect(url_for("main.person_detail", person_id=dose.vaccination.person_id))

    return render_template("dose_form.html", dose=dose, vaccination=dose.vaccination, show_navbar=True)


@main_bp.route("/dose/delete/<int:dose_id>", methods=["POST"])
@login_required
def delete_dose(dose_id):
    dose = Dose.query.get_or_404(dose_id)

    if dose.vaccination.person.user_id != current_user.id:
        abort(403)

    person_id = dose.vaccination.person_id
    db.session.delete(dose)
    db.session.commit()
    return redirect(url_for("main.person_detail", person_id=person_id))



@main_bp.route("/profile")
@login_required
def profile():
    persons = Person.query.filter_by(user_id=current_user.id).all()
    return render_template("profile.html", persons=persons, show_navbar=True)


@main_bp.route("/edit-profile", methods=["GET", "POST"])
@login_required
def edit_profile():
    if request.method == "POST":
        current_user.first_name = request.form.get("first_name")
        current_user.last_name = request.form.get("last_name")
        current_user.phone = request.form.get("phone")

        db.session.commit()
        flash("Profil uppdaterad.", "success")
        return redirect(url_for("main.profile"))

    return render_template("edit_profile.html", show_navbar=True)

@main_bp.route("/about")
def about():
    return render_template("about.html",
        buymeacoffee_url="https://buymeacoffee.com/vaccapp",
        buymeacoffee_qr="img/bmc_qr.png")