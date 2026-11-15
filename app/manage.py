"""Server-owner recovery of an existing user's password without losing camera settings."""
import getpass,os
from .storage import Store
if __name__=='__main__':
    store=Store(os.getenv('DATA_DIR','/data'));username=input('Username [admin]: ').strip() or 'admin';user=store.user(username=username)
    if not user:raise SystemExit('Unknown user')
    password=getpass.getpass('New password (12+ characters): ')
    if password!=getpass.getpass('Repeat password: '):raise SystemExit('Passwords do not match')
    store.save_user({**user,'password':password});print('Password changed; existing sessions are invalidated.')
