from flask import Blueprint, render_template, redirect, url_for, abort, flash
from flask_login import login_required, current_user
from app import db
from app.models import User

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


@admin_bp.route("/users")
@login_required
def users():
    if not current_user.is_admin:
        abort(403)

    users = User.query.all()
    return render_template("admin_users.html", users=users, show_navbar=True)


@admin_bp.route("/delete-user/<int:user_id>", methods=["POST"])
@login_required
def delete_user(user_id):
    if not current_user.is_admin:
        abort(403)

    user = User.query.get_or_404(user_id)

    if user_id == current_user.id:
        flash("Du kan inte ta bort dig själv.", "danger")
        return redirect(url_for("admin.users"))

    db.session.delete(user)
    db.session.commit()

    return redirect(url_for("admin.users"))