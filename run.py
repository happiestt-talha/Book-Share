from app import create_app
from flask import redirect, url_for

app = create_app()

@app.route('/')
def home():
    return redirect(url_for('books.browse'))

if __name__ == '__main__':
    app.run(debug=True)