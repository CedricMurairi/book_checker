import os, json
from flask import Flask, render_template, redirect, url_for, request, flash
from flask_script import Manager, Shell
from flask_migrate import Migrate, MigrateCommand
from sqlalchemy import and_, or_, func
from flask_moment import Moment
from flask_bootstrap import Bootstrap
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
import requests
from datetime import datetime
from model import BookUser, Book, BookReview, db
from form import LoginForm, RegistrationForm, SearchForm, ReviewForm


app = Flask(__name__, static_folder="statics")

app.config["SECRET_KEY"] = os.environ.get('SECRET_KEY') or os.urandom(32)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = True
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get('DEV_DATABASE_URL') or 'sqlite:///' + os.path.join(basedir, 'data-dev.sqlite')
apiKey = "kdqQUypXImd7O1u128tzeg"


manager = Manager(app)
db.init_app(app)
migrate = Migrate(app, db)
moment = Moment(app)
bootstrap = Bootstrap(app)
login_manager = LoginManager(app)
login_manager.session_protection = "strong"
login_manager.login_view = "login"


# def fetch_goodread_data(isbn):
# 	response = requests.get("https://www.goodreads.com/book/review_counts.json", params={'key': apiKey, 'ISBN': isbn})
# 	print(response.json())


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
			flash('Login was succesful')
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
	reviewers = {}
	for review in reviews:
		reviewers[review.book_reviewer] = BookUser.query.get(review.book_reviewer)
	if book:
		return render_template('book_detail.html', reviewers=reviewers, book=book, form=form, reviews=reviews)
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
		review.timestamp = datetime.utcnow()
		db.session.add(review)
		db.session.commit()
		return redirect(url_for('book_detail', book_id=review.book_reviewed))
	review = BookReview.query.get(review_id)
	form.rate.data = review.rate
	form.comment.data = review.comment
	return render_template('edit_review.html', form=form)


@app.route("/api/<string:isbn>", methods=['GET'])
def api(isbn):
	book = Book.query.filter_by(isbn=isbn).first()
	if not book:
		return {'response': 'The book does not exist in our records'}, 404
	return {'response': {'title': book.title, 'author': book.author, 'pub_year': book.pub_year, 'isbn': book.isbn, 'review_count': book.reviews.count(), 'average_rating': book.average_rating()}}


@app.route('/logout')
@login_required
def logout():
	logout_user()
	flash('You have been logged out')
	return redirect(url_for('main'))


if __name__ == '__main__':
    with app.app_context():
        manager.run()