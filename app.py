"""
Telegram Radar - Main Flask Application
Web interface for managing the Telegram monitoring system
"""

import os
import asyncio
from functools import wraps
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
import logging

from db import (
    init_db, get_accounts, get_keywords, add_account, delete_account,
    toggle_account, add_keyword, delete_keyword, clear_keywords,
    bulk_add_keywords, set_setting, get_setting, get_all_settings
)
from radar_engine import radar_engine
from logger_util import setup_logger, get_recent_logs

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')

# Setup logging
logger = setup_logger(__name__)

# Initialize database
init_db()

# Setup Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

class User(UserMixin):
    def __init__(self, id):
        self.id = id

@login_manager.user_loader
def load_user(user_id):
    return User(user_id)

def get_admin_email():
    """Get admin email from settings or environment"""
    return get_setting('admin_email') or os.getenv('ADMIN_EMAIL', 'admin@radar.com')

def get_admin_password_hash():
    """Get admin password hash from settings"""
    return get_setting('admin_password_hash')

def verify_admin_credentials(email: str, password: str) -> bool:
    """Verify admin credentials"""
    admin_email = get_admin_email()
    password_hash = get_admin_password_hash()
    
    if not password_hash:
        # First time setup - use default password
        default_password = os.getenv('ADMIN_PASSWORD', 'admin123')
        if email == admin_email and password == default_password:
            # Store hashed password
            set_setting('admin_password_hash', generate_password_hash(password))
            return True
        return False
    
    return email == admin_email and check_password_hash(password_hash, password)

# Routes
@app.route('/')
def index():
    """Redirect to dashboard if logged in, otherwise to login"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login page"""
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        if verify_admin_credentials(email, password):
            user = User(email)
            login_user(user)
            logger.info(f"User {email} logged in successfully")
            return redirect(url_for('dashboard'))
        else:
            logger.warning(f"Failed login attempt for {email}")
            return render_template('login.html', error='Invalid credentials')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    """Logout"""
    logger.info(f"User {current_user.id} logged out")
    logout_user()
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    """Main dashboard"""
    return render_template('dashboard.html')

# API Routes
@app.route('/api/status', methods=['GET'])
@login_required
def api_status():
    """Get radar status"""
    try:
        status = asyncio.run(radar_engine.get_status())
        return jsonify(status)
    except Exception as e:
        logger.error(f"Error getting status: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/toggle', methods=['POST'])
@login_required
def api_toggle():
    """Toggle radar on/off"""
    try:
        if radar_engine.is_running_status():
            asyncio.run(radar_engine.stop())
            return jsonify({"status": "stopped"})
        else:
            # Start radar in background
            asyncio.create_task(radar_engine.start())
            return jsonify({"status": "starting"})
    except Exception as e:
        logger.error(f"Error toggling radar: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/accounts', methods=['GET'])
@login_required
def api_get_accounts():
    """Get all accounts"""
    try:
        accounts = get_accounts()
        return jsonify(accounts)
    except Exception as e:
        logger.error(f"Error getting accounts: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/accounts', methods=['POST'])
@login_required
def api_add_account():
    """Add new account"""
    try:
        data = request.json
        phone = data.get('phone')
        api_id = data.get('api_id')
        api_hash = data.get('api_hash')
        alert_group = data.get('alert_group')
        
        if not all([phone, api_id, api_hash]):
            return jsonify({"error": "Missing required fields"}), 400
        
        if add_account(phone, int(api_id), api_hash, alert_group):
            logger.info(f"Account {phone} added successfully")
            return jsonify({"success": True, "message": "Account added successfully"})
        else:
            return jsonify({"error": "Account already exists"}), 400
    except Exception as e:
        logger.error(f"Error adding account: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/accounts/<phone>', methods=['DELETE'])
@login_required
def api_delete_account(phone):
    """Delete account"""
    try:
        if delete_account(phone):
            logger.info(f"Account {phone} deleted")
            return jsonify({"success": True})
        else:
            return jsonify({"error": "Account not found"}), 404
    except Exception as e:
        logger.error(f"Error deleting account: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/accounts/<phone>/toggle', methods=['POST'])
@login_required
def api_toggle_account(phone):
    """Toggle account enabled/disabled"""
    try:
        data = request.json
        enabled = data.get('enabled', True)
        
        if toggle_account(phone, enabled):
            logger.info(f"Account {phone} toggled: {enabled}")
            return jsonify({"success": True})
        else:
            return jsonify({"error": "Account not found"}), 404
    except Exception as e:
        logger.error(f"Error toggling account: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/keywords', methods=['GET'])
@login_required
def api_get_keywords():
    """Get all keywords"""
    try:
        keywords = get_keywords()
        return jsonify({"keywords": keywords})
    except Exception as e:
        logger.error(f"Error getting keywords: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/keywords/save', methods=['POST'])
@login_required
def api_save_keywords():
    """Save keywords"""
    try:
        data = request.json
        keywords_text = data.get('keywords', '')
        
        # Parse keywords (one per line)
        keywords = [kw.strip() for kw in keywords_text.split('\n') if kw.strip()]
        
        # Clear existing keywords
        clear_keywords()
        
        # Add new keywords
        count = bulk_add_keywords(keywords)
        
        # Reload keywords in radar engine
        asyncio.run(radar_engine.reload_keywords())
        
        logger.info(f"Keywords saved: {count} keywords")
        return jsonify({"success": True, "count": count})
    except Exception as e:
        logger.error(f"Error saving keywords: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/settings', methods=['GET'])
@login_required
def api_get_settings():
    """Get all settings"""
    try:
        settings = get_all_settings()
        # Don't return sensitive data
        settings.pop('admin_password_hash', None)
        settings.pop('openrouter_api_key', None)
        return jsonify(settings)
    except Exception as e:
        logger.error(f"Error getting settings: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/settings', methods=['POST'])
@login_required
def api_save_settings():
    """Save settings"""
    try:
        data = request.json
        
        # Update settings
        if 'ai_enabled' in data:
            set_setting('ai_enabled', str(data['ai_enabled']).lower())
        
        if 'openrouter_api_key' in data:
            set_setting('openrouter_api_key', data['openrouter_api_key'])
        
        if 'default_alert_group' in data:
            set_setting('default_alert_group', data['default_alert_group'])
        
        # Reload settings in radar engine
        asyncio.run(radar_engine.reload_settings())
        
        logger.info("Settings saved")
        return jsonify({"success": True})
    except Exception as e:
        logger.error(f"Error saving settings: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/logs', methods=['GET'])
@login_required
def api_get_logs():
    """Get recent logs"""
    try:
        lines = request.args.get('lines', 100, type=int)
        logs = get_recent_logs(lines)
        return jsonify({"logs": logs})
    except Exception as e:
        logger.error(f"Error getting logs: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.errorhandler(404)
def not_found(error):
    """404 error handler"""
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    """500 error handler"""
    logger.error(f"Internal error: {str(error)}")
    return render_template('500.html'), 500

if __name__ == '__main__':
    logger.info("Starting Telegram Radar application...")
    
    # Initialize radar engine
    asyncio.run(radar_engine.initialize())
    
    # Run Flask app
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
