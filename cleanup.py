from datetime import datetime, timedelta
from app import create_app, db
from app.models import User

app = create_app()

with app.app_context():
    limit = datetime.utcnow() - timedelta(days=30)

    users = User.query.filter(
        User.is_deleted == True,
        User.deleted_at < limit
    ).all()

    for user in users:
        db.session.delete(user)

    db.session.commit()
