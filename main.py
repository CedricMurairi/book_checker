import os

from flask import Flask, render_template, redirect, url_for, request, flash
from werkzeug.security import generate_password_hash, check_password_hash
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField, IntegerField, ValidationError, TextAreaField
from wtforms.validators import InputRequired, EqualTo, Length, Regexp, NumberRange
from flask_script import Manager, Shell
from flask_migrate import Migrate, MigrateCommand
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import and_, or_, func
from flask_moment import Moment
from flask_bootstrap import Bootstrap
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
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
login_manager.login_view = "login"


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
	isbn = StringField('Type in the isbn', validators=[InputRequired()])
	title = StringField('Type in the title', validators=[InputRequired()])
	author = StringField('Type in the author', validators=[InputRequired()])
	pub_year = StringField('Type in the year of publication', validators=[InputRequired()])
	submit = SubmitField('Search')


class ReviewForm(FlaskForm):
	rate = IntegerField('How do you rate this book?', validators=[InputRequired(), NumberRange(1, 5)])
	comment = TextAreaField('Give your comment and note to the author', validators=[InputRequired()])
	submit = SubmitField('Submit review')


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
		isbn = form.isbn.data
		title = form.title.data.lower()
		author = form.author.data.lower()
		pub_year = form.pub_year.data
		form.isbn.data = ""
		form.title.data = ""
		form.author.data = ""
		form.pub_year.data = ""
		books = Book.query.filter(or_(Book.isbn.like("%" +isbn+ "%"), func.lower(Book.author).like("%" +author+ "%"), func.lower(Book.title).like("%" +title+ "%"), Book.pub_year==pub_year)).all()
		if books:
			return render_template('index.html', form=form, books=books)
		flash('There is no such a book in our records')
		return redirect(url_for('main'))
	books = Book.query[:20]
	return render_template('index.html', form=form, books=books)


@app.route('/login', methods=['GET', 'POST'])
def login():
	if current_user.is_authenticated:
		return redirect(url_for('main'))
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
	if current_user.is_authenticated:
		return redirect(url_for('main'))
	form = RegistrationForm()
	if form.validate_on_submit():
		user = BookUser(username=form.username.data, password=form.password.data)
		db.session.add(user)
		db.session.commit()
		flash('You can now login')
		return redirect(url_for('login'))
	return render_template('register.html', form=form)

# @app.route("/book/search", methods=['GET', 'POST'])
# def search_book():
# 	if books:
# 		return {'response': [{'isbn': book.isbn, 'title': book.title, 'author': book.author, 'pub_year': book.pub_year} for book in books]}
# 	return {'response': 'Oopps! there is no match for that book'}


@app.route("/book/<int:book_id>/detail", methods=['GET', 'POST'])
@login_required
def book_detail(book_id):
	form = ReviewForm()
	if form.validate_on_submit():
		rate = form.rate.data
		comment = form.comment.data
		form.rate.data = ""
		form.comment.data = ""
		if current_user.reviews.filter_by(book_reviewed=book_id).first():
			flash('You cannot review the same book twice')
			return redirect(url_for('book_detail', book_id=book_id))
		review = BookReview(rate=rate, comment=comment, book_reviewer=current_user.id, book_reviewed=book_id)
		db.session.add(review)
		db.session.commit()
		return redirect(url_for('book_detail', book_id=book_id))
	book = Book.query.get(book_id)
	reviews = book.reviews
	for review in reviews:
		print(review.comment, review.book_reviewed)
	if book:
		return render_template('book_detail.html', book=book, form=form, reviews=reviews)
	flash('There is not such a book in our records, check your url if you entered it manually')
	return redirect('main')


@app.route("/review/<int:review_id>/edit", methods=['GET', 'POST'])
@login_required
def edit_review(review_id):
	form = ReviewForm()
	if form.validate_on_submit():
		review = BookReview.query.get(review_id)
		review.rate = form.rate.data
		review.comment = form.comment.data
		db.session.add(review)
		db.session.commit()
		return redirect(url_for('book_detail', book_id=review.book_reviewed))
	review = BookReview.query.get(review_id)
	form.rate.data = review.rate
	form.comment.data = review.comment
	return render_template('edit_review.html', form=form)


@app.route('/logout')
@login_required
def logout():
	logout_user()
	flash('You have been logged out')
	return redirect(url_for('main'))


if __name__ == '__main__':
    with app.app_context():
        manager.run()