import os

from flask import Flask, render_template, session, redirect, url_for, request, flash
import requests
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

app = Flask(__name__, static_folder="statics")
engine = create_engine(os.getenv("DATABASE_URI"))
db = scoped_session(sessionmaker(bind=engine))

app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
app.config["SECRET_KEY"] = "SLK(@)()(uhui&GFHQ09FU9Q0-(@**&#y&*W97F89W80R9W099E0-0QJDIAWUE*@)(e)@y&*ey*@yhr@u"
apiKey = "rYxKBo3lCt40jW0Oq6eg"

@app.route('/', methods=['GET', 'POST'])
def main():
	# On open check if there is user in current session
	if (request.method == 'POST'):
		isbnNumber = request.form.get('isbnNumber')
		bookAuthor = request.form.get('author')
		bookTitle = request.form.get('title')
		result = db.execute('SELECT * FROM books WHERE isbn = :isbn OR title = :title OR author = :author', {'isbn': isbnNumber, 'title': bookTitle, 'author': bookAuthor}).fetchall()
		if(not result):
			flash('Nosuch a book in our collection')
			return redirect(url_for('main'))
			# return redirect(url_for('main'))
		return render_template('search.html', result=result, email=session.get('email'), name=session.get('name'))
	if (session.get('email') and session.get('password')):
		flash("You are logged in successfully")
		return render_template('index.html', email=session.get('email'), name=session.get('name'))
	else:
		return redirect(url_for('signin_user'))
	# apiKey = "rYxKBo3lCt40jW0Oq6eg"
	# apiResponse = res = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": apiKey, "isbns": "9781632168146"})
	# print(apiResponse.json())
	# result = db.execute('SELECT * FROM students')
	# finalResult = [element.name for element in result]
	

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

# @app.route('/result')
# def search_result()

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
	user_review = db.execute('SELECT * FROM reviews WHERE id = :id', {'id': book_id}).fetchone()
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

if __name__ == "__main__":
	main() 