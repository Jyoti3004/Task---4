from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Replace with a secure secret key

# Configuration for SQLite database (replace 'your_database_uri' with the actual database URI)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///todo.db'

# Initialize SQLAlchemy
db = SQLAlchemy(app)

# Flask-Login setup
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

# Sample user data (in SQLite database)
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(80), nullable=False)

# Sample to-do list (in SQLite database)
class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(200), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
@login_required
def index():
    tasks = Task.query.filter_by(user_id=current_user.id).all()
    return render_template('index.html', tasks=tasks)

@app.route('/add', methods=['POST'])
@login_required
def add_task():
    task_content = request.form.get('task')
    if task_content:
        new_task = Task(content=task_content, user_id=current_user.id)
        db.session.add(new_task)
        db.session.commit()
    return redirect(url_for('index'))

@app.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_task(id):
    task = Task.query.get(id)
    if task:
        if task.user_id == current_user.id:
            if request.method == 'POST':
                new_task_content = request.form.get('new_task')
                task.content = new_task_content
                db.session.commit()
                return redirect(url_for('index'))
            return render_template('edit.html', task=task)
        else:
            flash('You can only edit your own tasks.', 'error')
            return redirect(url_for('index'))
    return redirect(url_for('index'))

@app.route('/delete/<int:id>')
@login_required
def delete_task(id):
    task = Task.query.get(id)
    if task:
        if task.user_id == current_user.id:
            db.session.delete(task)
            db.session.commit()
        else:
            flash('You can only delete your own tasks.', 'error')
    return redirect(url_for('index'))

@app.route('/api/tasks', methods=['GET'])
@login_required
def get_tasks():
    tasks = Task.query.filter_by(user_id=current_user.id).all()
    task_list = [{'id': task.id, 'content': task.content} for task in tasks]
    return jsonify(task_list)

@app.route('/api/tasks', methods=['POST'])
@login_required
def create_task():
    data = request.get_json()
    task_content = data.get('content')
    if task_content:
        new_task = Task(content=task_content, user_id=current_user.id)
        db.session.add(new_task)
        db.session.commit()
        return jsonify({'message': 'Task created successfully'}), 201
    else:
        return jsonify({'error': 'Task content is required'}), 400

@app.route('/api/tasks/<int:id>', methods=['GET'])
@login_required
def get_task(id):
    task = Task.query.get(id)
    if task and task.user_id == current_user.id:
        return jsonify({'id': task.id, 'content': task.content})
    else:
        return jsonify({'error': 'Task not found or unauthorized'}), 404

@app.route('/api/tasks/<int:id>', methods=['PUT'])
@login_required
def update_task(id):
    task = Task.query.get(id)
    if task and task.user_id == current_user.id:
        data = request.get_json()
        new_content = data.get('content')
        if new_content:
            task.content = new_content
            db.session.commit()
            return jsonify({'message': 'Task updated successfully'})
        else:
            return jsonify({'error': 'Task content is required'}), 400
    else:
        return jsonify({'error': 'Task not found or unauthorized'}), 404

@app.route('/api/tasks/<int:id>', methods=['DELETE'])
@login_required
def delete_task_api(id):
    task = Task.query.get(id)
    if task and task.user_id == current_user.id:
        db.session.delete(task)
        db.session.commit()
        return jsonify({'message': 'Task deleted successfully'})
    else:
        return jsonify({'error': 'Task not found or unauthorized'}), 404

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        if user and user.password == password:
            login_user(user)
            flash('Logged in successfully', 'success')
            return redirect(url_for('index'))
        else:
            flash('Login failed. Check your username and password.', 'error')
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if not User.query.filter_by(username=username).first():
            new_user = User(username=username, password=password)
            db.session.add(new_user)
            db.session.commit()
            flash('Signup successful. Please login.', 'success')
            return redirect(url_for('login'))
        else:
            flash('Username already exists. Choose another username.', 'error')
    return render_template('signup.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully', 'success')
    return redirect(url_for('login'))

if __name__ == '_main_':
    db.create_all()


app.run(debug=True)