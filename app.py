import os
from flask import Flask, request, render_template, redirect, url_for, send_from_directory, flash, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import uuid
from datetime import datetime, timezone

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-fuckin-key')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///chaos_hub.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # Silence warnings
app.config['UPLOAD_FOLDER'] = os.environ.get('UPLOAD_FOLDER', 'uploads')

db = SQLAlchemy(app)

# Ensure upload folder exists
upload_folder = app.config['UPLOAD_FOLDER']
if not os.path.exists(upload_folder):
    os.makedirs(upload_folder)

# Rest of your code (models, routes) stays the same...

class Group(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    group_name = db.Column(db.String(50), nullable=False)
    group_key = db.Column(db.String(36), unique=True, nullable=False)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), nullable=False)
    adm_number = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(128), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    group_id = db.Column(db.Integer, db.ForeignKey('group.id'), nullable=True)
    join_date = db.Column(db.String(20), default=lambda: datetime.now(timezone.utc).strftime('%d/%m/%Y'))

class Unit(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    group_id = db.Column(db.Integer, db.ForeignKey('group.id'), nullable=False)
    notes = db.relationship('File', backref='unit', lazy=True)

class File(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(100), nullable=False)
    type = db.Column(db.String(20), nullable=False)
    upload_date = db.Column(db.String(20), default=lambda: datetime.now(timezone.utc).strftime('%d/%m/%Y'))
    unit_id = db.Column(db.Integer, db.ForeignKey('unit.id'), nullable=True)
    group_id = db.Column(db.Integer, db.ForeignKey('group.id'), nullable=False)

class Notice(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    topic = db.Column(db.String(100), nullable=False)
    remark = db.Column(db.String(200), nullable=False)
    posted_date = db.Column(db.String(20), default=lambda: datetime.now(timezone.utc).strftime('%d/%m/%Y'))
    group_id = db.Column(db.Integer, db.ForeignKey('group.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

class Assignment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    topic = db.Column(db.String(100), nullable=False)
    remark = db.Column(db.String(200), nullable=False)
    due_date = db.Column(db.String(20), nullable=False)
    posted_date = db.Column(db.String(20), default=lambda: datetime.now(timezone.utc).strftime('%d/%m/%Y'))
    group_id = db.Column(db.Integer, db.ForeignKey('group.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

with app.app_context():
    db.drop_all()
    db.create_all()

def allowed_file(filename):
    return True

@app.route('/', methods=['GET', 'POST'])
def index():
    css_url = url_for('static', filename='index.css')
    print(f"Index CSS URL: {css_url}")
    
    group_id = session.get('group_id')
    group = Group.query.get(group_id) if group_id else None
    units = Unit.query.filter_by(group_id=group_id).all() if group_id else []
    members = User.query.filter_by(group_id=group_id).all() if group_id else []
    class_timetable = File.query.filter_by(group_id=group_id, type='class_timetable').first() if group_id else None
    exam_timetable = File.query.filter_by(group_id=group_id, type='exam_timetable').first() if group_id else None
    notices = Notice.query.filter_by(group_id=group_id).order_by(Notice.posted_date.desc()).all() if group_id else []
    assignments = Assignment.query.filter_by(group_id=group_id).order_by(Assignment.due_date).all() if group_id else []
    is_admin = False
    if 'user_id' in session:
        user = User.query.get(session['user_id'])
        is_admin = user.is_admin if user else False

    if request.method == 'POST':
        if 'note' in request.files:
            file = request.files['note']
            unit_id = request.form['unit_id']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                note = File(filename=filename, type='note', unit_id=unit_id, group_id=group_id)
                db.session.add(note)
                db.session.commit()
        elif 'class_timetable' in request.files:
            file = request.files['class_timetable']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                if class_timetable:
                    db.session.delete(class_timetable)
                timetable = File(filename=filename, type='class_timetable', group_id=group_id)
                db.session.add(timetable)
                db.session.commit()
        elif 'exam_timetable' in request.files:
            file = request.files['exam_timetable']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                if exam_timetable:
                    db.session.delete(exam_timetable)
                timetable = File(filename=filename, type='exam_timetable', group_id=group_id)
                db.session.add(timetable)
                db.session.commit()
        elif 'notice_topic' in request.form:
            topic = request.form['notice_topic']
            remark = request.form['notice_remark']
            notice = Notice(topic=topic, remark=remark, group_id=group_id, user_id=session['user_id'])
            db.session.add(notice)
            db.session.commit()
        elif 'assignment_topic' in request.form and is_admin:
            topic = request.form['assignment_topic']
            remark = request.form['assignment_remark']
            due_date = request.form['assignment_due_date']
            assignment = Assignment(topic=topic, remark=remark, due_date=due_date, group_id=group_id, user_id=session['user_id'])
            db.session.add(assignment)
            db.session.commit()
        return redirect(url_for('index'))

    return render_template('index.html', group=group, units=units, members=members, 
                         class_timetable=class_timetable, exam_timetable=exam_timetable, 
                         notices=notices, assignments=assignments, is_admin=is_admin)

@app.route('/register', methods=['GET', 'POST'])
def register():
    css_url = url_for('static', filename='register.css')
    print(f"Register CSS URL: {css_url}")
    
    if request.method == 'POST':
        group_name = request.form['group_name']
        identifier = request.form['identifier']
        password = request.form['password']
        action = request.form['action']

        existing_user_by_username = User.query.filter_by(username=identifier).first()
        existing_user_by_email = User.query.filter_by(email=identifier).first()

        if action == 'register':
            if existing_user_by_username or existing_user_by_email:
                flash('Username or email already taken.')
                return redirect(url_for('register'))
            group_key = str(uuid.uuid4())
            group = Group(group_name=group_name, group_key=group_key)
            db.session.add(group)
            db.session.commit()
            user = User(username=identifier if '@' not in identifier else f"user_{group.id}_{identifier.split('@')[0]}", 
                        adm_number=f"ADM{group.id}001", 
                        email=identifier if '@' in identifier else f"{identifier}@example.com", 
                        password=generate_password_hash(password), is_admin=True, group_id=group.id)
            db.session.add(user)
            db.session.commit()
            session['user_id'] = user.id
            session['group_id'] = group.id
            return redirect(url_for('group_setup', group_id=group.id))
        elif action == 'login':
            user = existing_user_by_username or existing_user_by_email
            if user and check_password_hash(user.password, password):
                session['user_id'] = user.id
                session['group_id'] = user.group_id
                return redirect(url_for('group_setup', group_id=user.group_id))
            flash('Invalid credentials.')
            return redirect(url_for('register'))

    return render_template('register.html')

@app.route('/group_setup/<int:group_id>', methods=['GET', 'POST'])
def group_setup(group_id):
    css_url = url_for('static', filename='group_setup.css')
    print(f"Group Setup CSS URL: {css_url}")
    print(f"Handling request: {request.method} /group_setup/{group_id}")
    
    group = Group.query.get_or_404(group_id)
    if 'user_id' not in session or User.query.get(session['user_id']).group_id != group_id:
        flash('Unauthorized.')
        return redirect(url_for('index'))

    if request.method == 'POST':
        units = request.form.getlist('units[]')
        for unit_name in units:
            unit = Unit(name=unit_name, group_id=group_id)
            db.session.add(unit)
        db.session.commit()
        return redirect(url_for('index'))

    return render_template('group_setup.html', group=group)

@app.route('/join', methods=['GET', 'POST'])
def join():
    css_url = url_for('static', filename='join.css')
    print(f"Join CSS URL: {css_url}")
    
    if request.method == 'POST':
        group_key = request.form['group_key']
        adm_number = request.form['adm_number']
        first_name = request.form['first_name']
        group = Group.query.filter_by(group_key=group_key).first()

        if not group:
            flash('Invalid group key.')
            return redirect(url_for('join'))
        
        if User.query.filter_by(adm_number=adm_number).first():
            flash('Admission number already in use.')
            return redirect(url_for('join'))

        username = f"{adm_number}_{first_name}"
        email = f"{username}@example.com"
        password = generate_password_hash("default")
        user = User(username=username, adm_number=adm_number, email=email, password=password, group_id=group.id)
        db.session.add(user)
        db.session.commit()
        session['user_id'] = user.id
        session['group_id'] = group.id
        return redirect(url_for('index'))

    return render_template('join.html')

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/close_group', methods=['POST'])
def close_group():
    if 'user_id' not in session:
        flash('Unauthorized.')
        return redirect(url_for('index'))
    user = User.query.get(session['user_id'])
    if not user.is_admin:
        flash('Only admins can close groups.')
        return redirect(url_for('index'))
    group_id = user.group_id
    File.query.filter_by(group_id=group_id).delete()
    Unit.query.filter_by(group_id=group_id).delete()
    User.query.filter_by(group_id=group_id).delete()
    Group.query.filter_by(id=group_id).delete()
    Notice.query.filter_by(group_id=group_id).delete()
    Assignment.query.filter_by(group_id=group_id).delete()
    db.session.commit()
    session.pop('user_id', None)
    session.pop('group_id', None)
    flash('Group closed and all data cleared.')
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)