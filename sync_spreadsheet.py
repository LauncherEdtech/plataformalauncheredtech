# sync_spreadsheet.py
import os
import time
import schedule
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from app import create_app, db
from app.models.user import User
from flask_login import current_user
from werkzeug.security import generate_password_hash

# Google Sheets API setup
SCOPE = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
# Path to your service account credentials JSON file
CREDENTIALS_FILE = 'service_account_credentials.json'
SPREADSHEET_ID = '15PZoIyicaJbMinTOZjJ-Hr88ph89rT75uHSOTB707vA'
SHEET_NAME = 'Assinaturas'  # Adjust if your sheet has a different name

def get_spreadsheet_data():
    """Connect to Google Sheets API and retrieve data from the specified spreadsheet."""
    try:
        credentials = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIALS_FILE, SCOPE)
        client = gspread.authorize(credentials)
        
        # Open the spreadsheet and the specific sheet
        spreadsheet = client.open_by_key(SPREADSHEET_ID)
        sheet = spreadsheet.worksheet(SHEET_NAME)
        
        # Get all data from the sheet and convert to pandas DataFrame
        data = sheet.get_all_records()
        df = pd.DataFrame(data)
        
        return df
    except Exception as e:
        print(f"Error accessing spreadsheet: {e}")
        return None

def sync_users():
    """
    Sync users from Google Spreadsheet to the database.
    - Create new users if they don't exist
    - Update user status based on the 'status' field in the spreadsheet
    - Use CPF as initial password for new users
    """
    app = create_app()
    with app.app_context():
        print("Starting spreadsheet synchronization...")
        
        # Get data from spreadsheet
        df = get_spreadsheet_data()
        if df is None or df.empty:
            print("No data retrieved from spreadsheet or error occurred.")
            return
        
        # Process each user in the spreadsheet
        for _, row in df.iterrows():
            username = row.get('username')
            email = row.get('email')
            nome_completo = row.get('nome_completo')
            cpf = row.get('cpf')
            status = row.get('status')
            
            # Check if user exists
            user = User.query.filter_by(email=email).first()
            
            if user:
                # User exists, update status if needed
                is_active = status.lower() != 'canceled'
                
                if user.is_active != is_active:
                    print(f"Updating status for user {email} to {'active' if is_active else 'blocked'}")
                    user.is_active = is_active
                    db.session.commit()
            else:
                # Create new user with CPF as password
# Create new user with CPF as password
                try:
                    print(f"Creating new user: {email}")

                    if not cpf:
                        print(f"[ERRO] CPF ausente ou inválido para o usuário {email}. Usuário não será criado.")
                        continue

                    new_user = User(
                        username=username,
                        email=email,
                        nome_completo=nome_completo,
                        cpf=cpf,
                        is_active=(status.lower() != 'canceled'),
                        password_changed=False
                    )

                    # Set initial password as CPF
                    cpf_str = str(cpf).strip()
                    new_user.set_password(cpf_str)


                    db.session.add(new_user)
                    db.session.commit()
                    print(f"Successfully created user: {email} with CPF as initial password")

                except Exception as e:
                    db.session.rollback()
                    print(f"Error creating user {email}: {e}")

        
        print("Spreadsheet synchronization completed.")

def run_scheduler():
    """Run the scheduler to periodically sync users."""
    # First run immediately
    sync_users()
    
    # Then schedule to run every 5 minutes
    schedule.every(1).minutes.do(sync_users)
    
    print("Scheduler started. Running sync every 5 minutes.")
    
    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == "__main__":
    run_scheduler()