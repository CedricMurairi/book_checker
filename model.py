from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy


db = SQLAlchemy()

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

	def average_rating(self):
		number_of_reviews = self.reviews.count()
		total_rating = 0
		if number_of_reviews == 0:
			return 0
		for review in self.reviews:
			total_rating += review.rate
		return int(total_rating / number_of_reviews)


class BookReview(db.Model):
	__tablename__ = "bookreviews"
	id = db.Column(db.Integer, primary_key=True)
	rate = db.Column(db.Integer)
	comment = db.Column(db.Text())
	book_reviewer = db.Column(db.Integer, db.ForeignKey('bookusers.id'))
	book_reviewed = db.Column(db.Integer, db.ForeignKey('books.id'))
	timestamp = db.Column(db.DateTime, default=datetime.utcnow)