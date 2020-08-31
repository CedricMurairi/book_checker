import os

from flask import Flask, render_template, redirect, url_for, request, flash
from werkzeug.security import generate_password_hash, check_password_hash
from flask_wtf import Form
from wtforms import StringField, PasswordField, SubmitField, BooleanField
from wtforms.validators import Required, EqualTo, Length, Regexp
from flask_script import Manager, Shell
from flask_migrate import Migrate, MigrateCommand
from flask_sqlalchemy import SQLAlchemy
from flask_moment import Moment
from flask_bootstrap import Bootstrap
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required
import requests

app = Flask(__name__, static_folder="statics")


# app.config["SESSION_PERMANENT"] = False
# app.config["SESSION_TYPE"] = "filesystem"
app.config["SECRET_KEY"] = os.urandom(32)
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
login_manager.logi_view = "app.login"


class LoginForm(Form):
	username = StringField('Username', validators=[Required()])
	password = PasswordField('Password', validators=[Required()])
	remember_me = BooleanField('Remember me')
	submit = SubmitField('Log In')


class RegistrationForm(Form):
	username = StringField('Username', validators=[Required(), Length(1, 64), Regexp('^[A-Za-z][A-Za-z0-9_.]*$', 0, 'Usernames must have only letters, numbers, dots or underscores')])
	password = PasswordField('Password', validators=[Required()])
	confirm_password = PasswordField('Confirm password', validators=[Required(), EqualTo('password', 'Passwords must match')])
	submit = SubmitField('Register')

	def validate_username(self, field):
		if User.query.filter_by(username=fiel.data).first():
			raise ValidationError('Username already in use')


class SearchForm(Form):
	search_term = StringField('Type in your keyword for search', validators=[Required()])
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
	pub_year = db.Column(db.Date)
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
	cs.main()
	print('Tables initialized with values...')


def make_shell_context():
    return dict(app=app, db=db, user=BookUser, book=Book, review=BookReview)

manager.add_command("shell", Shell(make_context=make_shell_context))
manager.add_command('db', MigrateCommand)


@app.route('/', methods=['GET', 'POST'])
def main():
	form = SearchForm()
	if form.validate_on_submit():
		print('The key search term is', form.search_term.data)
		form.search_term.data = ""
	return render_template('index.html', form=form)


if __name__ == '__main__':
    with app.app_context():
        manager.run()
	

@app.route('/register', methods=['GET', 'POST'])
def register_user():
	if(request.method == 'POST'):
		email = request.form.get('email')
		password = request.form.get('password')
		name = request.form.get('name')
		# Check if registering user already exist in our database
		check_user = db.execute('SELECT email, password FROM users WHERE email = :email AND password = :password', {'email': email, 'password': password}).fetchone()
		if(check_user):
			# If registering user exist in DB, do not register user
			flash('The user already exist')
			return redirect(url_for('register_user'))
		else:
			db.execute("INSERT INTO users (name, email, password) VALUES (:name, :email, :password)", {'name':name, 'email':email, 'password':password})
			db.commit()
			session['email'] = email
			session['password'] = password
			session['name'] = name
			flash("Registered successfully")
			flash("Loggin automatically")
			# TODO implement the actual insert in the database for the new user the redirect if only successful
			return redirect(url_for('main'))
	return render_template('register.html')


@app.route('/signin', methods=['GET', 'POST'])
def signin_user():
	if(request.method == 'POST'):
		email = request.form.get('email')
		password = request.form.get('password')
		user_credential = db.execute('SELECT name, email, password FROM users WHERE email = :email AND password = :password', {'email': email, 'password': password}).fetchone()
		if(user_credential):
			session['email'] = user_credential.email
			session['password'] = user_credential.password
			session['name'] = user_credential.name
		# TODO implement the actual query in the database and check if the user exist
			return redirect(url_for('main'))
		else:
			flash("Some thing is wrong with your email or password, try again")
			return redirect(url_for('signin_user'))
	return render_template('signin.html')
	

@app.route("/book/<int:book_id>", methods=['GET', 'POST'])
def book_detail(book_id):
	if request.method == 'POST':
		review = request.form.get('rating')
		review_detail = request.form.get('review')
		reviewer = db.execute('SELECT * FROM users WHERE email = :email AND password = :password', {'email': session.get('email'), 'password': session.get('password')}).fetchone()
		db.execute('INSERT INTO reviews (book, review, review_detail, reviewer) VALUES (:book, :review, :detail, :reviewer)', {'book': book_id, 'review': review, 'detail': review_detail, 'reviewer': reviewer.id})
		db.commit()
		flash('reviewer submitted')
	result = db.execute('SELECT * FROM books WHERE id = :id', {'id': book_id}).fetchone()
	user_review = db.execute('SELECT * FROM reviews WHERE book = :id', {'id': book_id}).fetchall()
	res = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": apiKey, "isbns": result.isbn})
	average_rating_goodread = res.json()['books'][len(res.json()) - 1 ]['average_rating']
	number_of_rating_goodread = res.json()['books'][0]['reviews_count']
	return render_template('book_info.html', result=result, user_review=user_review, average_rating_goodread=average_rating_goodread, number_of_rating_goodread=number_of_rating_goodread)

@app.route('/logout')
def logout_user():
	session.pop('email')
	session.pop('password')
	session.pop('name')
	return redirect(url_for('main'))