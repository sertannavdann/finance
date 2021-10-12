import os

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required, lookup, usd

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True


# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///finance.db")

# Make sure API key is set
if not os.environ.get("API_KEY"):
    raise RuntimeError("API_KEY not set")


@app.route("/")
@login_required
def index():

    user_id = session["user_id"]
    stocks = db.execute("SELECT symbol, name, price, SUM(shares) as totalShares FROM transactions WHERE user_id = ? GROUP BY symbol", user_id)
    cash = db.execute("SELECT cash FROM users WHERE id = ?", user_id)[0]["cash"]
    total = cash

    for stock in stocks:
        total += stock["price"] * stock["totalShares"]

    return render_template("index.html", stocks=stocks, cash=cash, usd=usd, total=total)


@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():

    if request.method == "POST":

        # Search for the given symbol in the API
        symbol = request.form.get("symbol").upper()
        item = lookup(symbol)


        if not symbol:
            return apology("Please enter a symbol")

        elif item == None:
            return apology("Symbol not available")

        # Integer version and the list version
        try:
            shares = int(request.form.get("shares"))
        except:
            return apology("Shares must be a number")

        if shares <= 0 or not request.form.get("shares").isdigit():
            return apology("Shares must be a positive number")

        # How much a user owns
        user_id = session["user_id"]
        cash = db.execute("SELECT cash FROM users WHERE id = ?", user_id)[0]["cash"]

        # Current price of an item x amount
        item_name = item["name"]
        item_price = item["price"]

        total_price = item_price * shares

        # The action of buying, if user has enough money
        if cash < total_price:
            return apology("insufficient cash")
        else:
            db.execute("UPDATE users SET cash = ? WHERE id = ?", cash - total_price, user_id)

            # To User's History
            db.execute("INSERT INTO history (username, name, shares, price, type, symbol) VALUES(? ,? ,? ,? ,? ,?)",
                       user_id, item_name, shares, item_price, 'buy', symbol)
            # To User's Transaction Portfolio
            db.execute("INSERT INTO transactions (user_id, name, shares, price, type, symbol) VALUES(? ,? ,? ,? ,? ,?)",
                       user_id, item_name, shares, item_price, 'buy', symbol)

        return redirect('/')

    else:
        return render_template("buy.html")


@app.route("/history")
@login_required
def history():
    user_id = session["user_id"]
    transacts = db.execute("SELECT type, symbol, price, shares, time FROM history WHERE username = ?", user_id)

    for transact in transacts:
        symbol = str(transact["symbol"])
        name = lookup(symbol)["name"]
        transact["name"] = name

    return render_template("history.html", transacts=transacts, usd=usd)

@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    """Get stock quote."""
    #POST
    if request.method == "POST":
        symbol = request.form.get("symbol")

        if not symbol:
            return apology("must provide symbol")

        #STOCK API Request, more details about the lookup() is in helpers.py
        stock = lookup(symbol)
        if not stock:
            return apology("Stock doesn't exists")


        return render_template("quoted.html", item=stock, usd=usd)


    #GET
    else:
        return render_template("quote.html")


@app.route("/register", methods=["GET", "POST"])
def register():


    """Register user"""
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")

        # CHECK THE DB IF THAT USER EXIST BEFORE
        user_specific = db.execute("SELECT * FROM users WHERE username = ?", username)
        if len(user_specific) != 0:
            return apology('Username Exists');

        if not username:
            return apology('Please Enter Your Username');
        elif not password:
            return apology('Please Enter a Password');
        elif not confirmation or password != confirmation:
            return apology('Password does not match');

        hash = generate_password_hash(password)

        db.execute("INSERT INTO users (username, hash) VALUES (?,?) ", username, hash)
        return redirect('/')

    else:
        return render_template("register.html")



@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""
    if request.method == "POST":
        user_id = session["user_id"]
        symbol = request.form.get("symbol")
        shares = int(request.form.get("shares"))

        if shares <=0:
            return apology("Please choose a logical number of share")

        item = lookup(symbol)
        item_price = item['price']
        item_name = item['name']
        price = shares * item_price

        current_cash = db.execute("SELECT cash FROM users WHERE id = ?", user_id)[0]["cash"]
        shares_owned = db.execute("SELECT SUM(shares) FROM transactions WHERE user_id = ? AND symbol = ? GROUP BY symbol", user_id, symbol)[0]["SUM(shares)"]

        # Add the value of sale to the user's cash
        db.execute("UPDATE users SET cash = ? WHERE id = ?", current_cash + price, user_id)

       # Add the transaction to the user's trasnactions TABLE
        db.execute("INSERT INTO transactions (user_id, name, shares, price, type, symbol) VALUES (?,?,?,?,?,?)",
        user_id, item_name, -shares, item_price, "sell", symbol)

       # Add the transaction to the user's history TABLE
        db.execute("INSERT INTO history (username, name, shares, price, type, symbol) VALUES (?,?,?,?,?,?)",
        user_id, item_name, -shares, item_price, "sell", symbol)

        if shares_owned < shares:
            return apology("Please insert a good measure of shares")
        if shares_owned == shares:
            db.execute("DELETE FROM transactions WHERE user_id = ? AND symbol = ?", user_id, symbol)
        if shares_owned > shares:
            db.execute("UPDATE transactions SET shares = ? WHERE user_id = ? AND symbol = ?", shares, user_id, symbol)
            db.execute("UPDATE history SET shares = ? WHERE username = ? AND symbol = ?", shares, user_id, symbol)

        return redirect("/")

    else:
        user_id = session["user_id"]
        total_shares = db.execute("SELECT SUM(shares) as total_shares FROM transactions WHERE user_id=? GROUP BY symbol", user_id)
        symbols = db.execute("SELECT symbol FROM transactions WHERE user_id=? GROUP BY symbol", user_id)

        return render_template("sell.html", symbols = symbols, total_shares=total_shares)



def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)
