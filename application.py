import os
import requests

from flask import Flask, session, render_template, redirect, request, flash, jsonify
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from functools import wraps

app = Flask(__name__)

def login_required(f):
	# http://flask.pocoo.org/docs/1.0/patterns/viewdecorators/
	@wraps(f)
	def decorated_function(*args, **kwargs):
		if session.get("user_id") is None:
			return redirect("/signlog")
		return f(*args, **kwargs)
	return decorated_function

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))


@app.route("/", methods=["GET", "POST"])
@login_required
def index():
	if request.method == "GET":
		return render_template("index.html", username=session["user_id"])
	else:
		query = request.form.get("query")
		if not query:
			return render_template("index.html", username=session["user_id"])
		rows = db.execute("SELECT * from books WHERE LOWER(isbn) LIKE :query OR LOWER(title) LIKE :query OR LOWER(author) LIKE :query OR LOWER(year) LIKE :query",
			{"query": f"%{query}%".lower()}).fetchall()
		return render_template("index.html", username=session["user_id"], results=rows)

@app.route("/book/<int:bookid>")
@login_required
def book(bookid):
	book = db.execute("SELECT * FROM books WHERE id = :bookid", {"bookid": bookid}).fetchone()
	if not book:
		flash("Invalid book ID.")
		return render_template("book.html")

	# get data from goodreads api
	res = requests.get("https://www.goodreads.com/book/review_counts.json",
		params={"key": os.getenv("GOODREADS_KEY"), "isbns": book[1]}).json()
	rc = res["books"][0]["work_ratings_count"]
	ar = res["books"][0]["average_rating"]
	grid = res["books"][0]["id"]
	book = list(book)
	book.append(rc)
	book.append(ar)
	book.append(grid)

	# get ratings
	rows = db.execute("SELECT * FROM ratings WHERE bookid = :bookid", 
		{"bookid": bookid}).fetchall()
	themes = ['bg-success', 'bg-danger', 'bg-warning', 'gb-info'] * (len(rows)//4+1)
	return render_template("book.html", book=book, ratings=list(zip(rows, themes)))

@app.route("/api/<string:isbn>")
def api(isbn):
	row = db.execute("SELECT * FROM books WHERE isbn = :isbn", 
		{"isbn": isbn}).fetchone()
	if not row:
		return jsonify({"error": "invalid isbn number"}), 404
	review = db.execute("SELECT COUNT(rating), AVG(rating) FROM ratings WHERE bookid = :bookid",
		{"bookid": row[0]}).fetchone()
	return jsonify({
			"title": row[2],
		    "author": row[3],
		    "year": row[4],
		    "isbn": row[1],
		    "review_count": review[0],
		    "average_score": str(review[1])[:4]
		})


@app.route("/review", methods=["POST"])
def review():
	rating = int(request.form.get("inlineRadioOptions"))
	bookid = int(request.form.get("bookid"))
	feedback = request.form.get("feedback")
	userid = session["user_id"]

	# check if user already gave feedback
	row = db.execute("SELECT * from ratings WHERE userid = :userid AND bookid = :bookid",
		{"userid": userid, "bookid": bookid}).fetchone()
	if row:
		flash("Feedback already given.")
		return redirect(f"/book/{bookid}")

	db.execute("INSERT INTO ratings (bookid, userid, rating, feedback) VALUES (:bookid, :userid, :rating, :feedback)",
				{"bookid": bookid, "userid": userid, "rating": rating, "feedback": feedback})
	db.commit()
	return redirect(f"/book/{bookid}")


@app.route("/signlog", methods=["GET", "POST"])
def signlog():
	session.clear()
	
	if request.method == "GET":
		return render_template("signlog.html")
	
	else:

		# when no info is provided
		if not request.form.get("userreg") and not request.form.get("usersign"):
			flash("Please provide a UserId")
			return render_template("signlog.html")
		
		# user tries to log in
		elif not request.form.get("userreg"):
			
			username = request.form.get("usersign")
			password = request.form.get("password")
			
			if not password:
				flash("Please provide a password")
				return render_template("signlog.html")

			row = db.execute("SELECT * from users WHERE username = :username",
				{"username": username}).fetchone()

			if not row or row["password"] != password:
				flash("Invalid username / password")
				return render_template("signlog.html")

			session["user_id"] = row["username"]

			return redirect("/")

		# user tries to register
		else:

			username = request.form.get("userreg")
			password = request.form.get("password")
			
			if not password:
				flash("Please provide a password")
				return render_template("signlog.html")

			row = db.execute("SELECT * from users WHERE username = :username",
				{"username": username}).fetchone()

			if row:
				flash("Username already exists")
				return render_template("signlog.html")

			db.execute("INSERT INTO users (username, password) VALUES (:username, :password)",
				{"username": username, "password": password})
			db.commit()

			flash("Welcome you can Login now.")
			return render_template("signlog.html")