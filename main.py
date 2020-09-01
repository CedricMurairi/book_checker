import os

from flask import Flask, render_template, redirect, url_for, request, flash
from werkzeug.security import generate_password_hash, check_password_hash
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField
from wtforms.validators import InputRequired, EqualTo, Length, Regexp
from flask_script import Manager, Shell
from flask_migrate import Migrate, MigrateCommand
from flask_sqlalchemy import SQLAlchemy
from flask_moment import Moment
from flask_bootstrap import Bootstrap
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required
import requests

app = Flask(__name__, static_folder="statics")

app.config["SECRET_KEY"] = os.environ.get('SECRET_KEY') or os.urandom(32)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = True
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get('DEV_DATABASE_URL') or 'sqlite:///' + os.path.join(basedir, 'data-dev.sqlite')
apiKey = "rYxKBo3lCt40jW0Oq6eg"


manager = Manager(app)
db = SQLAlchemy(app)
migrate = Migrate(app, db)
moment = Moment(app)
bootstrap = Bootstrap(app)
login_manager = LoginManager(app)
login_manager.session_protection = "strong"
login_manager.login_view = "app.login"


class LoginForm(FlaskForm):
	username = StringField('Username', validators=[InputRequired()])
	password = PasswordField('Password', validators=[InputRequired()])
	remember_me = BooleanField('Remember me')
	submit = SubmitField('Log In')


class RegistrationForm(FlaskForm):
	username = StringField('Username', validators=[InputRequired(), Length(1, 64), Regexp('^[A-Za-z][A-Za-z0-9_.]*$', 0, 'Usernames must have only letters, numbers, dots or underscores')])
	password = PasswordField('Password', validators=[InputRequired()])
	confirm_password = PasswordField('Confirm password', validators=[InputRequired(), EqualTo('password', 'Passwords must match')])
	submit = SubmitField('Register')

	def validate_username(self, field):
		if BookUser.query.filter_by(username=field.data).first():
			raise ValidationError('Username already in use')


class SearchForm(FlaskForm):
	search_term = StringField('Type in your keyword for search', validators=[InputRequired()])
	submit = SubmitField('Search')


class BookUser(UserMixin, db.Model):
	__tablename__ = "bookusers"
	id = db.Column(db.Integer, primary_key=True)
	username = db.Column(db.String(64), unique=True)
	password_hash = db.Column(db.String(128))
	reviews = db.relationship('BookReview', backref='reviewer', lazy='dynamic')

	@property
	def password(self):
		raise AttributeError('Password is not a readable attribute')

	@password.setter
	def password(self, password):
		self.password_hash = generate_password_hash(password)

	def verify_password(self, password):
		return check_password_hash(self.password_hash, password)


class Book(db.Model):
	__tablename__ = "books"
	id = db.Column(db.Integer, primary_key=True)
	isbn = db.Column(db.String(64), unique=True)
	title = db.Column(db.String(128))
	author = db.Column(db.String(128))
	pub_year = db.Column(db.Integer)
	reviews = db.relationship('BookReview', backref='book', lazy='dynamic')


class BookReview(db.Model):
	__tablename__ = "bookreviews"
	id = db.Column(db.Integer, primary_key=True)
	rate = db.Column(db.Integer)
	comment = db.Column(db.Text())
	book_reviewer = db.Column(db.Integer, db.ForeignKey('bookusers.id'))
	book_reviewed = db.Column(db.Integer, db.ForeignKey('books.id'))


@login_manager.user_loader
def load_user(user_id):
	return BookUser.query.get(int(user_id))


@manager.command
def create_table():
	"""Create tables"""
	print('Creating tables...')
	db.create_all()
	print('Tables created...')
	import csv_converter as cs
	if cs.main():
		print('Tables initialized with values...')
	else:
		print('Error!! Something is wrong with the data')


def make_shell_context():
    return dict(app=app, db=db, User=BookUser, Book=Book, Review=BookReview)


manager.add_command("shell", Shell(make_context=make_shell_context))
manager.add_command('db', MigrateCommand)


@app.route('/', methods=['GET', 'POST'])
def main():
	form = SearchForm()
	if form.validate_on_submit():
		print('The key search term is', form.search_term.data)
		form.search_term.data = ""
	books = Book.query[:20]
	return render_template('index.html', form=form, books=books)


@app.route('/login', methods=['GET', 'POST'])
def login():
	form = LoginForm()
	if form.validate_on_submit():
		user = BookUser.query.filter_by(username=form.username.data).first()
		if user and user.verify_password(form.password.data):
			login_user(user, form.remember_me.data)
			return redirect(request.args.get('next') or url_for('main'))
		flash('Invalid username or password')
		form.username.data = ""
	return render_template('signin.html', form=form)


@app.route('/register', methods=['GET', 'POST'])
def register():
	form = RegistrationForm()
	if form.validate_on_submit():
		user = BookUser(username=form.username.data, password=form.password.data)
		db.session.add(user)
		db.session.commit()
		flash('You can now login')
		return redirect(url_for('login'))
	return render_template('register.html', form=form)


@app.route("/book/<int:book_id>", methods=['GET', 'POST'])
def book_detail(book_id):
	return {'reponse': 'under development'}


@app.route('/logout')
@login_required
def logout():
	logout_user()
	flash('You have been logged out')
	return redirect(url_for('main'))


if __name__ == '__main__':
    with app.app_context():
        manager.run()