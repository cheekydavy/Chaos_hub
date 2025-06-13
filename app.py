print("Running Nexus Hub app.py version 2025-06-12")
import os
import requests
from flask import Flask, request, render_template, redirect, url_for, send_from_directory, session, flash
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO, emit
from werkzeug.utils import secure_filename
from datetime import datetime, timezone, timedelta
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Email, Length
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import bcrypt
import bleach
from dotenv import load_dotenv
import logging
import re
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
import atexit
import time
import urllib.parse

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-fuckin-key')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///nexushub.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = os.environ.get('UPLOAD_FOLDER', 'Uploads')
app.config['OUTPUT_FOLDER'] = os.environ.get('OUTPUT_FOLDER', 'outputs')
app.config['SESSION_COOKIE_SECURE'] = False  # Disabled for local testing
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=30)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB file size limit
app.config['RATELIMIT_DEFAULT'] = "200/day;50/hour"
app.config['RATELIMIT_STORAGE_URI'] = "memory://"
app.config['TELEGRAM_BOT_TOKEN'] = os.environ.get('TELEGRAM_BOT_TOKEN', '7643200755:AAEnY79hQQ98ovHCmOp-IOcscwvDGqUbEMM')
app.config['TELEGRAM_CHAT_ID'] = os.environ.get('TELEGRAM_CHAT_ID', '6214817938')
app.config['NEWS_API_KEY'] = os.environ.get('NEWS_API_KEY', '140695dbcf9a4c90aceec0b5d3b1155b')
app.config['UNIT_DELETE_SECRET_KEY'] = os.environ.get('UNIT_DELETE_SECRET_KEY', 'sierra')
app.config['ACTIVATION_LINK'] = os.environ.get('ACTIVATION_LINK', 'irm https://get.activated.win | iex')

db = SQLAlchemy(app)
socketio = SocketIO(app, cors_allowed_origins=['http://localhost:5100', 'http://127.0.0.1:5100', 'http://0.0.0.0:5100'])
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["200/day", "50/hour"],
    storage_uri=""
)

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global cache for tech news
tech_news_cache = []

# Secure headers
@app.after_request
def add_security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self' http://localhost:5100 https://cdn.socket.io; style-src 'self' 'unsafe-inline'; connect-src 'self' ws://localhost:5100 wss://localhost:5100;"
    return response

# Ensure upload/output folders exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['OUTPUT_FOLDER'], exist_ok=True)

# Database Models
class Unit(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    lecturer = db.Column(db.String(100), nullable=True)
    phone = db.Column(db.String(20), nullable=True)
    email = db.Column(db.String(100), nullable=True)
    notes = db.relationship('File', backref='unit', lazy=True)

class File(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(100), nullable=False)
    type = db.Column(db.String(20), nullable=False)
    upload_date = db.Column(db.String(20), default=lambda: datetime.now(timezone.utc).strftime('%d/%m/%Y'))
    unit_id = db.Column(db.Integer, db.ForeignKey('unit.id'), nullable=True)

class Assignment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    topic = db.Column(db.String(100), nullable=False)
    remark = db.Column(db.String(200), nullable=False)
    due_date = db.Column(db.String(20), nullable=False)
    posted_date = db.Column(db.String(20), default=lambda: datetime.now(timezone.utc).strftime('%d/%m/%Y'))

class Admin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)

# Forms
class AdminLoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class TelegramMessageForm(FlaskForm):
    message = TextAreaField('Message', validators=[DataRequired(), Length(min=1, max=500)])
    submit = SubmitField('Send Message')

class TelegramLinkForm(FlaskForm):
    link = StringField('Link', validators=[DataRequired()])
    submit = SubmitField('Send to Telegram')

# File validation
def allowed_file(filename):
    return filename.lower().endswith(('.xlsx', '.csv', '.docx', '.pdf', '.xls'))

def sanitize_input(text):
    return bleach.clean(text, tags=[], attributes={})

def validate_phone(phone):
    if not phone:
        return True
    pattern = r'^\+?\d{7,16}$'
    return bool(re.match(pattern, phone))

def validate_email(email):
    if not email:
        return True
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))

# Fetch tech news
def fetch_tech_news():
    global tech_news_cache
    try:
        api_key = app.config['NEWS_API_KEY']
        timestamp = int(time.time())
        url = f"https://newsapi.org/v2/top-headlines?category=technology&apiKey={api_key}&language=en&pageSize=5&_={timestamp}"
        logger.info(f"Fetching news from: {url}")
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            articles = response.json().get('articles', [])
            if articles:
                tech_news_cache = [
                    {
                        'title': article['title'],
                        'description': article['description'] or 'No description available',
                        'url': article['url'],
                        'source': article['source']['name'],
                        'fetched_at': datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
                    }
                    for article in articles
                ]
                logger.info(f"Tech news fetched successfully: {len(articles)} articles")
            else:
                tech_news_cache = []
                logger.warning("No articles returned from News API")
        else:
            logger.error(f"News API error: {response.status_code} - {response.text}")
            tech_news_cache = []
    except Exception as e:
        logger.error(f"Error fetching news: {str(e)}")
        tech_news_cache = []

# Initialize scheduler
def init_scheduler():
    try:
        scheduler = BackgroundScheduler()
        scheduler.add_job(
            func=fetch_tech_news,
            trigger=IntervalTrigger(minutes=30),
            id='fetch_tech_news_job',
            name='Fetch tech news every 30 minutes',
            replace_existing=True
        )
        scheduler.start()
        logger.info("APScheduler started successfully")
        atexit.register(lambda: scheduler.shutdown())
    except Exception as e:
        logger.error(f"Failed to start APScheduler: {str(e)}")

# Initialize database
with app.app_context():
    db.create_all()
    if not Admin.query.first():
        hashed_password = bcrypt.hashpw('admin123'.encode('utf-8'), bcrypt.gensalt())
        admin = Admin(username='admin', password_hash=hashed_password)
        db.session.add(admin)
        db.session.commit()

init_scheduler()

# Set Telegram webhook (run once in production)
def set_telegram_webhook():
    webhook_url = os.environ.get('WEBHOOK_URL', 'https://your-public-domain.com/telegram_webhook')
    telegram_url = f"https://api.telegram.org/bot{app.config['TELEGRAM_BOT_TOKEN']}/setWebhook"
    payload = {'url': webhook_url}
    response = requests.post(telegram_url, json=payload, timeout=10)
    logger.info(f"Webhook setup response: {response.text}")
    return response.json()

@app.route('/test')
def test():
    logger.info("Testing route hit")
    return "Fuck yeah, it’s alive!"

@app.route('/', methods=['GET', 'POST'])
def index():
    logger.info("Hit / Index route")
    try:
        units = Unit.query.all()
        class_timetable = File.query.filter_by(type='class_timetable').first()
        exam_timetable = File.query.filter_by(type='exam_timetable').first()
        assignments = Assignment.query.order_by(Assignment.due_date).all()
        telegram_form = TelegramMessageForm()
        news_articles = tech_news_cache
        error = None

        if request.method == 'POST':
            try:
                if 'note' in request.files:
                    file = request.files['note']
                    unit_id = sanitize_input(request.form.get('unit_id', ''))
                    if file and allowed_file(file.filename):
                        filename = secure_filename(file.filename)
                        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                        file.save(file_path)
                        logger.info(f"Saved note file: {file_path}")
                        note = File(filename=filename, type='note', unit_id=unit_id or None)
                        db.session.add(note)
                        db.session.commit()
                        flash('Note uploaded successfully', 'success')
                        return redirect(url_for('index', _anchor='notes'))
                    else:
                        flash('Invalid file type for note. Allowed types: .xlsx, .csv, .docx, .pdf, .xls', 'error')
                        logger.warning(f"Invalid note file: {file.filename if file else 'None'}")
                elif 'file' in request.files:
                    file = request.files['file']
                    timetable_type = sanitize_input(request.form.get('timetable_type', ''))
                    if file and allowed_file(file.filename) and timetable_type in ['class_timetable', 'exam_timetable']:
                        filename = secure_filename(file.filename)
                        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                        file.save(file_path)
                        logger.info(f"Saved {timetable_type}: {file_path}")
                        existing_timetable = File.query.filter_by(type=timetable_type).first()
                        if existing_timetable:
                            db.session.delete(existing_timetable)
                            logger.info(f"Deleted existing {timetable_type}")
                        timetable = File(filename=filename, type=timetable_type)
                        db.session.add(timetable)
                        db.session.commit()
                        flash(f'{timetable_type.replace("_", " ").title()} uploaded successfully', 'success')
                        return redirect(url_for('index', _anchor='timetables'))
                    else:
                        flash(f'Invalid file type for {timetable_type}. Allowed types: .xlsx, .csv, .docx, .pdf, .xls', 'error')
                        logger.warning(f"Invalid timetable file: {file.filename if file else 'None'}")
                elif 'assignment_topic' in request.form:
                    topic = sanitize_input(request.form.get('assignment_topic', ''))
                    remark = sanitize_input(request.form.get('assignment_remark', ''))
                    due_date = sanitize_input(request.form.get('assignment_due_date', ''))
                    if topic and remark and due_date:
                        try:
                            due_date = datetime.strptime(due_date, '%Y-%m-%d').strftime('%d/%m/%Y')
                            assignment = Assignment(topic=topic, remark=remark, due_date=due_date)
                            db.session.add(assignment)
                            db.session.commit()
                            flash('Assignment posted', 'success')
                        except ValueError:
                            flash('Invalid due date format', 'error')
                    else:
                        flash('Invalid assignment input', 'error')
                elif 'delete_unit_id' in request.form:
                    unit_id = sanitize_input(request.form.get('delete_unit_id', ''))
                    secret_key = sanitize_input(request.form.get('secret_key', ''))
                    expected_key = app.config['UNIT_DELETE_SECRET_KEY']
                    if secret_key != expected_key:
                        flash('Invalid secret key', 'error')
                        logger.warning(f"Invalid secret key attempt for unit {unit_id}")
                        return redirect(url_for('index', _anchor='notes'))
                    if unit_id:
                        unit = Unit.query.get_or_404(unit_id)
                        db.session.delete(unit)
                        db.session.commit()
                        flash('Unit deleted successfully', 'success')
                        logger.info(f"Unit {unit_id} deleted with valid secret key")
                    else:
                        flash('Invalid unit ID', 'error')
                        logger.warning(f"Invalid unit ID: {unit_id}")
                    return redirect(url_for('index', _anchor='notes'))
                return redirect(url_for('index', _anchor='assignments'))
            except Exception as e:
                db.session.rollback()
                flash(f'Error: {str(e)}', 'error')
                logger.error(f"Error in POST /: {str(e)}")

        today = datetime.now(timezone.utc).strftime('%d/%m/%Y')
        for assignment in assignments:
            try:
                if datetime.strptime(assignment.due_date, '%d/%m/%Y') < datetime.strptime(today, '%d/%m/%Y'):
                    db.session.delete(assignment)
            except Exception as e:
                logger.error(f"Error deleting assignment {assignment.id}: {str(e)}")
        db.session.commit()

        assignments = Assignment.query.order_by(Assignment.due_date).all()
        return render_template('index.html', units=units, class_timetable=class_timetable,
                              exam_timetable=exam_timetable, assignments=assignments,
                              telegram_form=telegram_form, news_articles=news_articles,
                              error=error)
    except Exception as e:
        logger.error(f"Error in /: {str(e)}")
        flash('Server error, try again later', 'error')
        return render_template('index.html', error=str(e))

@app.route('/send_telegram', methods=['GET', 'POST'])
def send_telegram():
    logger.info("Hit /send_telegram")
    form = TelegramMessageForm()
    if request.method == 'POST' and form.validate_on_submit():
        try:
            message = sanitize_input(form.message.data)
            bot_token = app.config['TELEGRAM_BOT_TOKEN']
            chat_id = app.config['TELEGRAM_CHAT_ID']
            telegram_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
            payload = {
                'chat_id': chat_id,
                'text': message
            }
            response = requests.post(telegram_url, json=payload, timeout=10)
            if response.status_code == 200:
                flash('Message sent to Telegram successfully', 'success')
            else:
                error_msg = response.json().get('description', 'Unknown error')
                flash(f'Telegram error: {error_msg}', 'error')
                logger.error(f"Telegram API error: {response.text}")
        except requests.exceptions.RequestException as e:
            flash(f'Error sending message: Network issue ({str(e)})', 'error')
            logger.error(f"Network error in /send_telegram: {str(e)}")
        except Exception as e:
            flash(f'Error sending message: {str(e)})', 'error')
            logger.error(f"Error in /send_telegram: {str(e)}")
        return redirect(url_for('index', _anchor='links'))
    return render_template('telegram_message.html', form=form)

@app.route('/send_link_to_telegram', methods=['POST'])
@limiter.limit("50 per minute")
def send_link_to_telegram():
    logger.info("Hit /send_link_to_telegram")
    try:
        form = TelegramLinkForm()
        if form.validate_on_submit():
            link = sanitize_input(form.link.data)
            if not link.startswith(('http://', 'https://')):
                flash('Invalid link provided', 'error')
                logger.warning(f"Invalid link: {link}")
                return redirect(url_for('ai_chat'))
            
            bot_token = app.config['TELEGRAM_BOT_TOKEN']
            chat_id = app.config['TELEGRAM_CHAT_ID']
            telegram_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
            message = f"Here is your link: {link}"
            reply_markup = {
                'inline_keyboard': [[
                    {'text': 'Open Link', 'url': link}
                ]]
            }
            payload = {
                'chat_id': chat_id,
                'text': message,
                'reply_markup': reply_markup
            }
            response = requests.post(telegram_url, json=payload, timeout=10)
            if response.status_code == 200:
                flash('Link sent to Telegram successfully', 'success')
            else:
                error_msg = response.json().get('description', 'Unknown error')
                flash(f'Telegram error: {error_msg}', 'error')
                logger.error(f"Telegram API error: {response.text}")
        else:
            flash('Invalid form data', 'error')
            logger.warning("Invalid form data in /send_link_to_telegram")
        return redirect(url_for('ai_chat'))
    except Exception as e:
        flash(f'Error sending link: {str(e)}', 'error')
        logger.error(f"Error in /send_link_to_telegram: {str(e)}")
        return redirect(url_for('ai_chat'))

@app.route('/telegram_webhook', methods=['POST'])
@limiter.limit("100 per minute")
def telegram_webhook():
    logger.info("Hit /telegram_webhook")
    try:
        update = request.get_json()
        if not update or 'message' not in update:
            logger.warning("Invalid Telegram update received")
            return '', 400

        chat_id = update['message']['chat']['id']
        text = update['message'].get('text', '').strip()

        # Handle commands and deep link parameters
        message = None
        reply_markup = None
        if text.lower().startswith(('/start', '/start@svjeff_bot')):
            parts = text.split(maxsplit=1)
            if len(parts) > 1:
                parameter = parts[1].strip()
                if parameter.lower() == 'activation':
                    message = f"Here is the Windows & Office activation link: {app.config['ACTIVATION_LINK']}"
                else:
                    # Decode the parameter, assuming it might be a URL
                    try:
                        decoded_link = urllib.parse.unquote(parameter)
                        # Basic validation to check if it’s a URL
                        if decoded_link.startswith(('http://', 'https://')):
                            message = f"Here is your link: {decoded_link}"
                            # Add an inline button to open the link
                            reply_markup = {
                                'inline_keyboard': [[
                                    {'text': 'Open Link', 'url': decoded_link}
                                ]]
                            }
                        else:
                            message = f"Invalid link provided: {decoded_link}"
                    except Exception as e:
                        logger.error(f"Error decoding link parameter: {str(e)}")
                        message = "Error processing the link. Please try again."
            else:
                message = "Welcome to svjeff Bot! Use /activation to get the Windows & Office activation link or click a link like https://t.me/svjeff?start=https%3A%2F%2Fexample.com"
        elif text.lower() in ['/activation', '/activation@svjeff_bot']:
            message = f"Here is the Windows & Office activation link: {app.config['ACTIVATION_LINK']}"
        else:
            message = "Unknown command. Use /activation to get the activation link."

        telegram_url = f"https://api.telegram.org/bot{app.config['TELEGRAM_BOT_TOKEN']}/sendMessage"
        payload = {
            'chat_id': chat_id,
            'text': message
        }
        if reply_markup:
            payload['reply_markup'] = reply_markup

        response = requests.post(telegram_url, json=payload, timeout=10)
        if response.status_code != 200:
            logger.error(f"Failed to send Telegram message: {response.text}")
            return '', 500
        return '', 200
    except Exception as e:
        logger.error(f"Error in telegram_webhook: {str(e)}")
        return '', 500

@app.route('/ai_chat', methods=['GET'])
def ai_chat():
    logger.info("Hit /ai_chat")
    try:
        bot_username = "@svjeff"
        llm_links = [
            {"name": "Grok (General Knowledge)", "url": "https://x.ai/grok", "is_website": True},
            {"name": "Claude (Writing & Ethics)", "url": "https://anthropic.com", "is_website": True},
            {"name": "Mistral (Code Generation)", "url": "https://mistral.ai", "is_website": True},
            {"name": "Gemini (Multimodal Tasks)", "url": "https://deepmind.google/technologies/gemini", "is_website": True},
            {"name": "movie quotes", "url": "https://clip.cafe", "is_website": True},
            {"name": "free software", "url": "https://filecr.com/en/", "is_website": True},
            {"name": "3d mockups", "url": "https://contentcore.xyz", "is_website": True},
            {"name": "website sitemap structure", "url": "https://modulify.ai", "is_website": True},
            {"name": "document your codes", "url": "https://gitdocify.com/", "is_website": True},
            {"name": "browser os", "url": "https://puter.com/", "is_website": True},
            {"name": "high quality images", "url": "https://www.pexels.com/", "is_website": True},
            {"name": "high quality images(alt)", "url": "https://www.freepik.com/", "is_website": True},
            {"name": "vfx images", "url": "https://productioncrate.com", "is_website": True},
            {"name": "yt video download", "url": "https://stacher.io/", "is_website": True},
            {"name": "all in one pdf tool", "url": "https://www.pdfgear.com/", "is_website": True},
            {"name": "remote desktop app", "url": "https://rustdesk.com/", "is_website": True},
            {"name": "free nasa api ", "url": "https://api.nasa.gov/", "is_website": True},
            {"name": "games(0)", "url": "https://se7en.ws/?lang=en", "is_website": True},
            {"name": "games(1)", "url": "https://fitgirl-repacks.site/", "is_website": True},
            {"name": "games(2)", "url": "https://www.ankergames.de/", "is_website": True},
            {"name": "Movie Download", "url": "https://yts.mx/", "is_website": True},
            {"name": "github link tutorial", "url": "https://www.codebase.com/", "is_website": True},
            {"name": "Windows & Office activation(Powershell)", "url": "irm https://get.activated.win | iex", "is_website": False},
            {"name": "website cloning", "url": "https://same.new/", "is_website": True},
            {"name": "Type any six numbers or letters after the (/) in the url", "url": "https://prnt.sc/", "is_website": True}
        ]

        

        return render_template('ai_chat.html', llm_links=llm_links, form=TelegramLinkForm())
    except Exception as e:
        logger.error(f"Error in /ai_chat: {str(e)}")
        flash('Server error, try again later', 'error')
        return redirect(url_for('index'))

@app.route('/group_setup', methods=['GET', 'POST'])
def group_setup():
    logger.info("Hit /group_setup")
    if request.method == 'POST':
        try:
            units = request.form.getlist('units[]')
            lecturers = request.form.getlist('lecturers[]')
            phones = request.form.getlist('phones[]')
            emails = request.form.getlist('emails[]')
            for name, lecturer, phone, email in zip(units, lecturers, phones, emails):
                name = sanitize_input(name)
                lecturer = sanitize_input(lecturer) if lecturer else None
                phone = sanitize_input(phone) if phone else None
                email = sanitize_input(email) if email else None
                if name:
                    if not validate_phone(phone):
                        flash(f'Invalid phone number for unit {name}', 'error')
                        continue
                    if not validate_email(email):
                        flash(f'Invalid email for unit {name}', 'error')
                        continue
                    unit = Unit(name=name, lecturer=lecturer, phone=phone, email=email)
                    db.session.add(unit)
            db.session.commit()
            flash('Units added successfully', 'success')
            return redirect(url_for('index', _anchor='notes'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding units: {str(e)}', 'error')
            logger.error(f"Error in /group_setup: {str(e)}")
    return render_template('group_setup.html')

@app.route('/admin/login', methods=['GET', 'POST'])
@limiter.limit("10 per minute")
def admin_login():
    logger.info("Hit /admin/login")
    form = AdminLoginForm()
    if form.validate_on_submit():
        try:
            username = sanitize_input(form.username.data)
            password = form.password.data
            admin = Admin.query.filter_by(username=username).first()
            if admin and bcrypt.checkpw(password.encode('utf-8'), admin.password_hash):
                session['admin_id'] = admin.id
                logger.info(f"Admin {username} logged in")
                flash('Successfully logged in', 'success')
                return redirect(url_for('admin_dashboard'))
            else:
                flash('Invalid credentials', 'error')
                logger.warning(f"Failed login attempt for {username}")
        except Exception as e:
            logger.error(f"Error in admin login: {str(e)}")
            flash('Login error, try again later', 'error')
    return render_template('admin_login.html', form=form)

@app.route('/admin/dashboard', methods=['GET', 'POST'])
def admin_dashboard():
    logger.info("Hit /admin/dashboard")
    if 'admin_id' not in session:
        flash('Please log in', 'error')
        return redirect(url_for('admin_login'))

    try:
        if request.method == 'POST':
            if 'unit_name' in request.form:
                name = sanitize_input(request.form.get('unit_name', ''))
                lecturer = sanitize_input(request.form.get('lecturer', '')) or None
                phone = sanitize_input(request.form.get('phone', '')) or None
                email = sanitize_input(request.form.get('email', '')) or None
                if name:
                    if not validate_phone(phone):
                        flash('Invalid phone number', 'error')
                    elif not validate_email(email):
                        flash('Invalid email', 'error')
                    else:
                        unit = Unit(name=name, lecturer=lecturer, phone=phone, email=email)
                        db.session.add(unit)
                        db.session.commit()
                        flash('Unit added', 'success')
                else:
                    flash('Unit name is required', 'error')
            elif 'note' in request.files:
                file = request.files['note']
                unit_id = sanitize_input(request.form.get('unit_id', ''))
                if file and allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    file.save(file_path)
                    logger.info(f"Saved note file: {file_path}")
                    note = File(filename=filename, type='note', unit_id=unit_id or None)
                    db.session.add(note)
                    db.session.commit()
                    flash('Note uploaded', 'success')
                    return redirect(url_for('admin_dashboard', _anchor='notes'))
                else:
                    flash('Invalid file type for note. Allowed types: .xlsx, .csv, .docx, .pdf, .xls', 'error')
                    logger.warning(f"Invalid note file: {file.filename if file else 'None'}")
            return redirect(url_for('admin_dashboard'))

        units = Unit.query.all()
        return render_template('admin_dashboard.html', units=units)
    except Exception as e:
        db.session.rollback()
        logger.error(f'Error in admin dashboard: {str(e)}')
        flash(f'Error: {str(e)}', 'error')
        return redirect(url_for('admin_dashboard'))

@app.route('/Uploads/<filename>')
def uploaded_file(filename):
    logger.info(f"Serving file: {filename}")
    try:
        filename = secure_filename(filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File {filename} not found")
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename)
    except Exception as e:
        logger.error(f"Error serving file {filename}: {str(e)}")
        flash('File not found', 'error')
        return redirect(url_for('index'))

@app.route('/downloads/<filename>')
def download_file(filename):
    logger.info(f"Serving download file: {filename}")
    try:
        filename = secure_filename(filename)
        file_path = os.path.join(app.config['OUTPUT_FOLDER'], filename)
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File {filename} not found")
        return send_from_directory(app.config['OUTPUT_FOLDER'], filename, as_attachment=True)
    except Exception as e:
        logger.error(f"Error downloading file {filename}: {str(e)}")
        flash('File not found', 'error')
        return redirect(url_for('index'))

@socketio.on('connect')
def handle_connect():
    logger.info("Client connected to SocketIO")
    emit('response', {'msg': 'Connected to Nexus Hub'})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5100))
    logger.info(f"Running on port {port}")
    fetch_tech_news()  # Initial news fetch
    if not os.environ.get('FLASK_DEBUG', '0') == '1':  # Set webhook only in production
        set_telegram_webhook()
    socketio.run(app, host='0.0.0.0', port=port, debug=True)