# user_model_update.py
from app import create_app, db
from app.models.user import User
from sqlalchemy import text
from werkzeug.security import generate_password_hash

def update_user_model():
    """
    Script to update the User model to add the new fields:
    - is_active: to track if the user is active or blocked
    - cpf: to store the user's CPF (used as initial password)
    - password_changed: to track if the user has changed their initial password

    This should be run once to modify the database schema.
    """
    app = create_app()
    with app.app_context():
        from sqlalchemy import inspect
        inspector = inspect(db.engine)
        columns = [column['name'] for column in inspector.get_columns('user')]

        changes_made = False

        with db.engine.connect() as connection:
            if 'is_active' not in columns:
                print("Adding is_active field to User model...")
                connection.execute(text('ALTER TABLE "user" ADD COLUMN is_active BOOLEAN DEFAULT TRUE'))
                changes_made = True
                print("is_active field added successfully!")
            else:
                print("The is_active field already exists in the User model.")

            if 'cpf' not in columns:
                print("Adding cpf field to User model...")
                connection.execute(text('ALTER TABLE "user" ADD COLUMN cpf VARCHAR(14)'))
                changes_made = True
                print("cpf field added successfully!")
            else:
                print("The cpf field already exists in the User model.")

            if 'password_changed' not in columns:
                print("Adding password_changed field to User model...")
                connection.execute(text('ALTER TABLE "user" ADD COLUMN password_changed BOOLEAN DEFAULT FALSE'))
                changes_made = True
                print("password_changed field added successfully!")
            else:
                print("The password_changed field already exists in the User model.")

        if changes_made:
            print("All necessary fields have been added to the User model!")
        else:
            print("No changes were needed, all fields already exist.")

if __name__ == "__main__":
    update_user_model()
