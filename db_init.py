from app import create_app, db
from app.models import User, Book, BorrowRequest, Notification
from werkzeug.security import generate_password_hash

app = create_app()

with app.app_context():
    db.create_all()
    print("✅ All tables created.")

    # Create admin if doesn't exist
    existing_admin = User.query.filter_by(email='admin@bookshare.com').first()
    if not existing_admin:
        admin = User(
            name='Admin',
            email='admin@bookshare.com',
            password=generate_password_hash('Admin@123'),
            role='admin'
        )
        db.session.add(admin)
        db.session.commit()
        print("✅ Admin user created.")
        print("   Email: admin@bookshare.com")
        print("   Password: Admin@123")
    else:
        print("ℹ️  Admin user already exists, skipping.")

    print("\n✅ Database initialization complete!")