# create_users_db.py
from sqlalchemy.orm import Session
from pwdlib import PasswordHash
from ..models.Models import User, Role, engine, Base


def create_sample_users():
    Base.metadata.create_all(bind=engine)
    session = Session(bind=engine)

    # Create roles
    admin_role = Role(name="admin")
    user_role = Role(name="user")

    # Add roles to the session
    session.add(admin_role)
    session.add(user_role)
    session.commit()

    # Create sample users
    password_hash = PasswordHash.recommended()
    hashed_password_admin = password_hash.hash("admin123")
    admin_user = User(
        username="adminuser", password=hashed_password_admin, roles=[admin_role]
    )

    hashed_password_user = password_hash.hash("user123")
    regular_user = User(
        username="regularuser", password=hashed_password_user, roles=[user_role]
    )

    session.add(admin_user)
    session.add(regular_user)
    session.commit()

    # Assign roles to users
    # admin_user.roles.append(admin_role)
    # regular_user.roles.append(user_role)
    session.commit()
    session.close()


if __name__ == "__main__":
    create_sample_users()
