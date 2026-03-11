from app import create_app, db
from app.models import User, Person

app = create_app()

with app.app_context():

    # Kolla om admin redan finns via email
    existing_admin = User.query.filter_by(email="admin@vaccapp.com").first()

    if not existing_admin:

        admin = User(
            email="admin@vaccapp.com",
            first_name="Admin",
            last_name="User",
            phone="",
            is_admin=True
        )

        admin.set_password("admin123")

        db.session.add(admin)
        db.session.commit()

        # 🔥 Skapa self-person automatiskt
        self_person = Person(
            user_id=admin.id,
            first_name="Admin",
            last_name="User",
            relationship="self"
        )

        db.session.add(self_person)
        db.session.commit()

        print("✅ Admin skapad!")

    else:
        print("ℹ️ Admin finns redan.")