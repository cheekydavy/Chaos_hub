import os
from flask import Flask, request, render_template, redirect, url_for, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO, emit, join_room, leave_room
from werkzeug.utils import secure_filename
from datetime import datetime, timezone

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-fuckin-key')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///chaos_hub.db').replace('postgres://', 'postgresql://')  # Fix for Render's PostgreSQL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = os.environ.get('UPLOAD_FOLDER', 'uploads')

db = SQLAlchemy(app)
socketio = SocketIO(app)

upload_folder = app.config['UPLOAD_FOLDER']
if not os.path.exists(upload_folder):
    os.makedirs(upload_folder)

class Unit(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    notes = db.relationship('File', backref='unit', lazy=True)

class File(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(100), nullable=False)
    type = db.Column(db.String(20), nullable=False)
    upload_date = db.Column(db.String(20), default=lambda: datetime.now(timezone.utc).strftime('%d/%m/%Y'))
    unit_id = db.Column(db.Integer, db.ForeignKey('unit.id'), nullable=True)

class Notice(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    topic = db.Column(db.String(100), nullable=False)
    remark = db.Column(db.String(200), nullable=False)
    posted_date = db.Column(db.String(20), default=lambda: datetime.now(timezone.utc).strftime('%d/%m/%Y'))
    messages = db.relationship('Message', backref='notice', lazy=True)

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(500), nullable=False)
    posted_date = db.Column(db.String(20), default=lambda: datetime.now(timezone.utc).strftime('%d/%m/%Y'))
    notice_id = db.Column(db.Integer, db.ForeignKey('notice.id'), nullable=False)

class Assignment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    topic = db.Column(db.String(100), nullable=False)
    remark = db.Column(db.String(200), nullable=False)
    due_date = db.Column(db.String(20), nullable=False)  # Format: dd/mm/yyyy
    posted_date = db.Column(db.String(20), default=lambda: datetime.now(timezone.utc).strftime('%d/%m/%Y'))

with app.app_context():
    db.drop_all()
    db.create_all()

def allowed_file(filename):
    return True

@app.route('/', methods=['GET', 'POST'])
def index():
    units = Unit.query.all()
    class_timetable = File.query.filter_by(type='class_timetable').first()
    exam_timetable = File.query.filter_by(type='exam_timetable').first()
    notices = Notice.query.order_by(Notice.posted_date.desc()).all()
    assignments = Assignment.query.order_by(Assignment.due_date).all()

    if request.method == 'POST':
        if 'note' in request.files:
            file = request.files['note']
            unit_id = request.form['unit_id']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                note = File(filename=filename, type='note', unit_id=unit_id)
                db.session.add(note)
                db.session.commit()
        elif 'class_timetable' in request.files:
            file = request.files['class_timetable']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                if class_timetable:
                    db.session.delete(class_timetable)
                timetable = File(filename=filename, type='class_timetable')
                db.session.add(timetable)
                db.session.commit()
        elif 'exam_timetable' in request.files:
            file = request.files['exam_timetable']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                if exam_timetable:
                    db.session.delete(exam_timetable)
                timetable = File(filename=filename, type='exam_timetable')
                db.session.add(timetable)
                db.session.commit()
        elif 'notice_topic' in request.form:
            topic = request.form['notice_topic']
            remark = request.form['notice_remark']
            notice = Notice(topic=topic, remark=remark)
            db.session.add(notice)
            db.session.commit()
            return redirect(url_for('chat_room', notice_id=notice.id))
        elif 'assignment_topic' in request.form:
            topic = request.form['assignment_topic']
            remark = request.form['assignment_remark']
            due_date = request.form['assignment_due_date']  # Expecting yyyy-mm-dd
            if due_date:
                due_date = datetime.strptime(due_date, '%Y-%m-%d').strftime('%d/%m/%Y')
                assignment = Assignment(topic=topic, remark=remark, due_date=due_date)
                db.session.add(assignment)
                db.session.commit()
        return redirect(url_for('index'))

    today = datetime.now(timezone.utc).strftime('%d/%m/%Y')
    for assignment in assignments:
        if datetime.strptime(assignment.due_date, '%d/%m/%Y') < datetime.strptime(today, '%d/%m/%Y'):
            db.session.delete(assignment)
    db.session.commit()
    assignments = Assignment.query.order_by(Assignment.due_date).all()

    return render_template('index.html', units=units, class_timetable=class_timetable,
                          exam_timetable=exam_timetable, notices=notices, assignments=assignments)

@app.route('/chat_room/<int:notice_id>', methods=['GET', 'POST'])
def chat_room(notice_id):
    notice = Notice.query.get_or_404(notice_id)
    if request.method == 'POST':
        content = request.form['message']
        message = Message(content=content, notice_id=notice_id)
        db.session.add(message)
        db.session.commit()
        socketio.emit('message', {'room': str(notice_id), 'msg': f"{message.content} ({message.posted_date})"})
        return redirect(url_for('chat_room', notice_id=notice_id))
    messages = Message.query.filter_by(notice_id=notice_id).order_by(Message.posted_date).all()
    return render_template('chat_room.html', notice=notice, messages=messages)

@app.route('/group_setup', methods=['GET', 'POST'])
def group_setup():
    if request.method == 'POST':
        units = request.form.getlist('units[]')
        for unit_name in units:
            unit = Unit(name=unit_name)
            db.session.add(unit)
        db.session.commit()
        return redirect(url_for('index'))
    return render_template('group_setup.html')

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@socketio.on('join')
def on_join(data):
    room = request.args.get('notice_id')
    join_room(room)
    emit('joined', {'room': room}, room=room)

@socketio.on('leave')
def on_leave(data):
    room = data['room']
    leave_room(room)

@socketio.on('message')
def handle_message(data):
    room = data['room']
    msg = data['msg']
    emit('message', {'room': room, 'msg': msg}, room=room)

if __name__ == '__main__':
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)