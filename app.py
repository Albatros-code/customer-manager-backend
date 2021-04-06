from flask_app import create_app

app = create_app()


@app.route("/")
def hello():
    return "<h1 style='color:blue'>Hello There!</h1>"


if __name__ == "__main__":
    app.run()