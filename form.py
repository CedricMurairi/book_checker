from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField, IntegerField, ValidationError, TextAreaField
from wtforms.validators import InputRequired, EqualTo, Length, Regexp, NumberRange


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