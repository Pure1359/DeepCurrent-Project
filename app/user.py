# Import modules
from flask import request, render_template, redirect, url_for, Blueprint, session
import bcrypt
from datetime import datetime, timezone

# Import Database Functions from services/
from app.services.users import create_user, create_account, update_last_active
from app.services.auth import get_account_by_email_for_login, verify_password

#need to do required login 
user_bp = Blueprint("user", __name__)


