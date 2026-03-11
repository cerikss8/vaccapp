from app import create_app, db
from app.models import User, Vaccination, Dose
from datetime import date

app = create_app()

def seed():
    with app.app_context():

        # --------------------
        # ADMIN
        # --------------------
        if not User.query.filter_by(username="Clas").first():
            admin = User(
                username="Clas",
                email="fake@gmail.com",
                first_name="Clas",
                last_name="Eriksson",
                phone='',
                is_admin=True
            )
            admin.set_password("nkGo$TU0yre2")
            db.session.add(admin)
            print("✅ Admin skapad (admin / admin123)")
        else:
            print("ℹ️ Admin finns redan")
'''
        # --------------------
        # VANLIG ANVÄNDARE
        # --------------------
        if not User.query.filter_by(username="test").first():
            user = User(
                username="test",
                first_name="Test",
                last_name="User",
                phone="0711111111",
                is_admin=False
            )
            user.set_password("test123")
            db.session.add(user)
            db.session.flush()  # behövs för user.id

            # Vaccinationer
            covid = Vaccination(
                name="Covid-19",
                notes="Lite feber efter dos 2",
                user_id=user.id
            )

            tbe = Vaccination(
                name="TBE",
                notes="Påfyllnad efter 1 år",
                user_id=user.id
            )

            db.session.add_all([covid, tbe])
            db.session.flush()

            # Doser
            db.session.add_all([
                Dose(date=date(2021, 6, 1), vaccination_id=covid.id),
                Dose(date=date(2021, 7, 1), vaccination_id=covid.id),
                Dose(date=date(2022, 6, 15), vaccination_id=tbe.id),
            ])

            print("✅ Testanvändare skapad (test / test123)")
        else:
            print("ℹ️ Testanvändare finns redan")

        db.session.commit()
        print("🌱 Seed klar!")
'''
if __name__ == "__main__":
    seed()
