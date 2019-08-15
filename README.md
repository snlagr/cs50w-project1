# Project 1

Web Programming with Python and JavaScript

I named my project Another Book Review

If you go to home page without logging in it will automatically redirect you to "signlog" page where either you can register or login. Providing wrong/ incomplete information will flash the revelvant message.

After logging in you will be redirected to home page where you can search for books or logout.

On clicking a result it will take you to book details page where goodreads data is also available. You can also rate a book & view what other people have rated.

There is an API endpoint available at "/api/isbn" which returns book details in JSON format.

Application.py is the main entry point of the app.
Import.py imports data from books.csv to heroku postgres server.
Templates contain html pages and css files are contained in static folder.

I have taken ui design inspirations from some codepens.

The title cursive font is 'Beth Ellen' found on Google Fonts.