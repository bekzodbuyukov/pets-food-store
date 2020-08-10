from flask import Flask, render_template, request, redirect, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__)
app.secret_key = 'lenovo mint 2020'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///data.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
manager = LoginManager(app)


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), nullable=False, unique=True)
    password = db.Column(db.String(30), nullable=False)
    registration_date = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return self.username


class Item(db.Model):
    item_id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    intro = db.Column(db.String(250), nullable=False)
    text = db.Column(db.Text, nullable=False)
    price = db.Column(db.Integer, nullable=False)
    status = db.Column(db.Boolean, default=True)
    category = db.Column(db.String(50), nullable=False)

    def __repr__(self):
        return self.title


@manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)


@app.route('/')
def index():
    items = Item.query.all()
    return render_template('index.html', items=items)


@app.route('/about')
def about_page():
    return render_template('about.html')


@app.route('/contact')
def contact_page():
    return render_template('contact.html')


@app.route('/login', methods=['GET', 'POST'])
def login_page():
    username = request.form.get('username')
    password = request.form.get('password')

    if username and password:
        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password, password):
            login_user(user)

            # next_page = request.args.get('next')

            # return redirect(next_page)

            return redirect('/admin-panel')
        else:
            flash('Неверный логин или пароль')
    else:
        flash('Пожалуйста заполните поля')

    return render_template('login.html')


@app.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    logout_user()
    return redirect('/')


@app.route('/register', methods=['GET', 'POST'])
def register_page():
    new_username = request.form.get('username')
    password = request.form.get('password')
    password_check = request.form.get('password_check')
    # existing_username = User.query.filter_by(username=new_username).first()
    # user = User.query.get('username')

    if request.method == 'POST':
        try:
            if not (new_username or password or password_check):
                flash('Пожалуйста, заполните все поля')
            # elif new_username == user.username:
                # flash('Такой пользователь уже зарегистрирован')
            elif password != password_check:
                flash('Пароли не совпадают')
            else:
                hashed_password = generate_password_hash(password)
                new_user = User(username=new_username, password=hashed_password)
                db.session.add(new_user)
                db.session.commit()
                return redirect('/login')
        except:
            flash('Ошибка, попробуйте снова')

    return render_template('register.html')


@app.after_request
def redirect_to_login(response):
    if response.status_code == 401:
        return redirect('/login' + '?next=' + request.url)

    return response


@app.route('/admin-panel')
@login_required
def admin_panel():
    return render_template('admin-panel.html')


@app.route('/admin-panel/users')
@login_required
def users_page():
    users = User.query.all()
    return render_template('users.html', users=users)


@app.route('/admin-panel/users/<int:id>/delete')
@login_required
def delete_user_page(id):
    return render_template('delete-user.html', deleting_user_id=id)


@app.route('/admin-panel/users/<int:id>/delete/yes')
@login_required
def delete_user_action(id):
    users = User.query.all()
    deleting_user = User.query.get(id)

    try:
        db.session.delete(deleting_user)
        db.session.commit()
        return redirect('/admin-panel/users')
    except:
        flash('При удалении пользователя произошла ошибка')

    return render_template('users.html', users=users)


@app.route('/admin-panel/users/<int:id>/edit', methods=['POST', 'GET'])
@login_required
def edit_user_page(id):
    user = User.query.get(id)
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        password_check = request.form['password_check']
        old_password = request.form['old_password']
        try:
            if not (username or password or password_check):
                flash('Пожалуйста, заполните все поля')
            elif password != password_check:
                flash('Пароли не совпадают')
            elif not check_password_hash(user.password, old_password):
                flash('Старый пароль введен не правильно')
            else:
                user.username = username
                new_hashed_password = generate_password_hash(password)
                user.password = new_hashed_password

                db.session.commit()
                return redirect('/admin-panel/users')
        except:
            flash('При редактировании пользователя произошла ошибка')
    else:
        return render_template('edit-user.html', user=user)
    return render_template('edit-user.html', user=user)


@app.route('/admin-panel/items')
@login_required
def items_page():
    items = Item.query.all()
    return render_template('items.html', items=items)


@app.route('/admin-panel/items/add-item', methods=['GET', 'POST'])
@login_required
def add_item_page():
    if request.method == 'POST':
        title = request.form['title']
        intro = request.form['intro']
        text = request.form['text']
        price = int(request.form['price'])
        category = request.form['category']

        if not (title or intro or text or price or category):
            flash('Все поля должны быть заполнены')
        else:
            item = Item(title=title, intro=intro, text=text, price=price, category=category)
            try:
                db.session.add(item)
                db.session.commit()
                return redirect('/admin-panel/items')
            except:
                flash('При добавлении продукта произошла ошибка')
    else:
        return render_template('add-item.html')
    return render_template('add-item.html')


@app.route('/item-detail/<int:item_id>')
def item_detail_page(item_id):
    item = Item.query.get(item_id)
    return render_template('item-detail.html', item=item)


@app.route('/admin-panel/items/<int:item_id>/delete')
def delete_item_page(item_id):
    return render_template('delete-item.html', deleting_item_id=item_id)


@app.route('/admin-panel/items/<int:item_id>/delete/yes')
def delete_item_action(item_id):
    item = Item.query.get(item_id)

    try:
        db.session.delete(item)
        db.session.commit()
        return redirect('/admin-panel/items')
    except:
        flash('При удалении продукта произошла ошибка')

    return redirect('/admin-panel/items')


@app.route('/admin-panel/items/<int:item_id>/edit', methods=['POST', 'GET'])
def edit_item_page(item_id):
    item = Item.query.get(item_id)
    if request.method == 'POST':
        item.title = request.form['title']
        item.intro = request.form['intro']
        item.text = request.form['text']
        item.price = int(request.form['price'])
        item.category = request.form['category']
        if request.form['status'] == 'True':
            item.status = True
        else:
            item.status = False

        try:
            db.session.commit()
            return redirect('/admin-panel/items')
        except:
            flash('При редактировании продукта произошла ошибка')
    else:
        return render_template('edit-item.html', item=item)
    return render_template('edit-item.html', item=item)


if __name__ == '__main__':
    app.run()
