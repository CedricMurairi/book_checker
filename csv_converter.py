from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
import csv

engine = create_engine('postgresql:///cedricmurairi')
db = scoped_session(sessionmaker(bind=engine))

def main():

	with open('/home/cedricmurairi/Documents/CS50Course/projects/project1/books.csv', newline='') as csvfile:
		bookreader = csv.reader(csvfile, delimiter=',', quotechar="'", doublequote=True, skipinitialspace=True)
		for bookinfo in bookreader:
			# print(bookinfo[0],'**',bookinfo[1],'**',bookinfo[2],'**',bookinfo[3])
			# print(', '.join(bookinfo))
			db.execute("INSERT INTO books (isbn, title, author, year) VALUES (:isbn, :title, :auth, :year)", {'isbn':bookinfo[0], 'title':bookinfo[1], 'auth':bookinfo[2], 'year':bookinfo[3]})
		db.commit()
		# result = db.execute('SELECT * FROM students')
		# for value in result:
		# 	print(value.name)
			# TODO implement the transfer of this data from csv into actual database

if __name__ == "__main__":
	main()