from app import create_app, db
from app.models.user import User
from app.models.ticket import Ticket, Attachment, Comment, TicketItem
from app.models.settings import Category, AppSettings, Item

app = create_app()

@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'User': User, 'Ticket': Ticket, 'Comment': Comment}

@app.cli.command("seed")
def seed():
    db.create_all()
    if not User.query.filter_by(username='admin').first():
        user = User(username='admin', email='admin@example.com', role='admin')
        user.set_password('admin')
        db.session.add(user)
        db.session.commit()
        print('Database seeded!')

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5050, debug=True)
