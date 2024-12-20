from flask import Flask, request, jsonify, render_template, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from models import db, User, Ticket

app = Flask(__name__)
app.secret_key = "123"

user_db = "postgres"
host_ip = "127.0.0.1"
host_port = "5432"
database_name = "rpp_lv"
password = "korea231"

app.config['SQLALCHEMY_DATABASE_URI'] = f'postgresql://{user_db}:{password}@{host_ip}:{host_port}/{database_name}'
app.config['SECRET_KEY'] = '12345'

db.init_app(app)

login_manager = LoginManager(app)
login_manager.init_app(app)

# функция для загрузки пользователя из базы данных по его идентификатору
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Home page route
@app.route('/')
def home():
    return render_template('index.html')

# регистрация пользователя
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # извлечение данных из запроса в формате json
        data = request.json
        # создание нового пользователя, используя данные, полученные из запроса
        new_user = User(username=data['username'], password=data['password'])
        # добавление нового пользователя в сессию базы данных
        db.session.add(new_user)
        db.session.commit()
        return jsonify({'message': 'Пользователь успешно зарегистрирован!'}), 201
    return render_template('register.html')

# авторизация пользователя
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # извлечение данных из запроса
        data = request.json
        # поиск пользователя в базе данных по имени пользователя
        user = User.query.filter_by(username=data['username']).first()
        # если пользователь найден и пароль совпадает, выполняется вход в систему
        if user and user.password == data['password']:
            login_user(user)
            return jsonify({'message': 'Вы успешно вошли!'}), 200
        return jsonify({'message': 'Вы не авторизованы...'}), 401
    return render_template('login.html')

# создание новой заявки
@app.route('/tickets', methods=['GET', 'POST'])
@login_required
def create_ticket():
    if request.method == 'POST':
        # получение данных новой заявки из запроса
        data = request.json
        # создание новой заявки, связывая его с текущим пользователем
        new_ticket = Ticket(title=data['title'], description=data['description'], user_id=current_user.id)
        # добавление новой заявки в сессию базы данных и сохранение
        db.session.add(new_ticket)
        db.session.commit()
        return jsonify({'message': 'Заявка успешно сформирована!'}), 201
    return render_template('create_ticket.html')

# получение списка заявок
@app.route('/tickets', methods=['GET'])
@login_required
def get_tickets():
    # если это админ, то он видит все заявки
    if current_user.role == 'admin':
        tickets = Ticket.query.all()
    else:
        tickets = Ticket.query.filter_by(user_id=current_user.id).all()
    return render_template('tickets.html', tickets=tickets)

# просмотр конкретной заявки
@app.route('/tickets/<int:ticket_id>', methods=['GET'])
@login_required
def get_ticket(ticket_id):
    ticket = Ticket.query.get(ticket_id)
    if ticket:
        if current_user.role == 'admin' or ticket.user_id == current_user.id:
            return render_template('ticket_detail.html', ticket=ticket)
        return jsonify({'message': 'Нет доступа'}), 403
    return jsonify({'message': 'Заявка не найдена'}), 404

# обновление заявки
@app.route('/tickets/<int:ticket_id>', methods=['PUT'])
@login_required
def update_ticket(ticket_id):
    ticket = Ticket.query.get(ticket_id)
    if not ticket:
        return jsonify({'message': 'Заявка не найдена'}), 404
    if current_user.role != 'admin' and ticket.user_id != current_user.id:
        return jsonify({'message': 'Нет доступа'}), 403
    data = request.json
    ticket.title = data.get('title', ticket.title)
    ticket.description = data.get('description', ticket.description)
    ticket.status = data.get('status', ticket.status)
    db.session.commit()
    return jsonify({'message': 'Заявка успешно обновлена!'}), 200

# удаление заявки
@app.route('/tickets/<int:ticket_id>', methods=['DELETE'])
@login_required
def delete_ticket(ticket_id):
    ticket = Ticket.query.get(ticket_id)
    if not ticket:
        return jsonify({'message': 'Заявка не найдена'}), 404
    if current_user.role != 'admin' and ticket.user_id != current_user.id:
        return jsonify({'message': 'Нет доступа'}), 403
    db.session.delete(ticket)
    db.session.commit()
    return jsonify({'message': 'Заявка успешно удалена'}), 200

# просмотр всех пользователей
@app.route('/users', methods=['GET'])
@login_required
def get_users():
    if current_user.role != 'admin':
        return jsonify({'message': 'Нет доступа'}), 403
    users = User.query.all()
    return render_template('users.html', users=users)

# обновление роли пользователя
@app.route('/users/<int:user_id>', methods=['PUT'])
@login_required
def update_user_role(user_id):
    if current_user.role != 'admin':
        return jsonify({'message': 'Нет доступа'}), 403
    user = User.query.get(user_id)
    if not user:
        return jsonify({'message': 'Пользователь не найден'}), 404
    data = request.json
    user.role = data.get('role', user.role)
    db.session.commit()
    return jsonify({'message': 'Роль пользователя успешно обновлена'}), 200

# Логин и логаут
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # создание таблиц в базе данных
    app.run(debug=True)
