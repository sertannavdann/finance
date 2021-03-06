This is a web based Flask Application that helps you BUY or SELL financial assests.

**Configuring**
Before getting started on this assignment, we’ll need to register for an API key in order to be able to query IEX’s data. To do so, follow these steps:

    Visit iexcloud.io/cloud-login#/register/.
    Select the “Individual” account type, then enter your email address and a password, and click “Create account”.
    Once registered, scroll down to “Get started for free” and click “Select Start” to choose the free plan.
    Once you’ve confirmed your account via a confirmation email, visit https://iexcloud.io/console/tokens.
    Copy the key that appears under the Token column (it should begin with pk_).
In a terminal window execute:
    $ export API_KEY=value

where "value" is that (pasted) value, without any space immediately before or after the =. You also may wish to paste that value in a text document somewhere, in case you need it again later.

**Running**
. Start Flask’s built-in web server (within finance/):

$ flask run
Visit the URL outputted by flask to see the distribution code in action. You won’t be able to log in or register, though, just yet!

Double-click finance.db in order to open it with phpLiteAdmin. Notice how finance.db comes with a table called users. Take a look at its structure (i.e., schema). Notice how, by default, new users will receive $10,000 in cash. But there aren’t (yet!) any users (i.e., rows) therein to browse.

Here on out, if you’d prefer a command line, you’re welcome to use sqlite3 instead of phpLiteAdmin.
