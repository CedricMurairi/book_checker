import csv
from main import db, Book 

def main():
	try:
		with open('/home/cedricmurairi/Documents/CS50Course/projects/project1/books.csv', newline='') as csvfile:

			bookreader = csv.reader(csvfile, delimiter=',', quotechar='"', doublequote=True, skipinitialspace=True)

			for bookinfo in bookreader:

				book = Book(isbn=bookinfo[0], title=bookinfo[1], author=bookinfo[2], pub_year=bookinfo[3])
				db.session.add(book)

			db.session.commit()

		return True
	except Exception as e:
		print(e)
		return False

if __name__ == "__main__":
	main()