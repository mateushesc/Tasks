from flask import Flask, redirect, url_for, render_template, request, session, flash
from datetime import timedelta
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.secret_key = "aiiiiiiiin"
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.sqlite3'
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.permanent_session_lifetime = timedelta(days=30)

db = SQLAlchemy(app)

class users(db.Model):
    _id = db.Column("id", db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(100))
    groups = db.relationship('groups', secondary='group_members', backref='members')

    def __init__(self, name, email):
        self.name = name
        self.email = email

        
class groups(db.Model):
    _id = db.Column("id", db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    users = db.relationship('users', secondary='group_members')
    tasks = db.relationship('Tasks', backref='group', lazy=True)

    def __init__(self, name):
        self.name = name

class Tasks(db.Model):
    _id = db.Column("id", db.Integer, primary_key=True)
    title = db.Column(db.String(100))
    description = db.Column(db.String(200))
    status = db.Column(db.String(50))  # Pendente, Iniciada, Finalizada
    group_id = db.Column(db.Integer, db.ForeignKey('groups.id'))

    def __init__(self, title, description, status, group_id):
        self.title = title
        self.description = description
        self.status = status
        self.group_id = group_id

class groupMembers(db.Model):
    __tablename__ = 'group_members'
    group_id = db.Column(db.Integer, db.ForeignKey('groups.id'), primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)


@app.route("/")
def home():
    if "user" in session:
        user = users.query.filter_by(name=session["user"]).first()
        user_groups = user.groups if user else []
        return render_template("index.html", user_groups=user_groups)
    else:
        return redirect(url_for("login"))

@app.route("/view")
def view():
    return render_template("view.html", values=users.query.all())

@app.route("/login", methods=["POST", "GET"])
def login():
    if request.method == "POST":
        session.permanent = True
        user = request.form["nm"]
        session["user"] = user
    
        found_user = users.query.filter_by(name=user).first()
        if found_user:
            session["email"] = found_user.email
        else:
            usr = users(user, "") 
            db.session.add(usr)
            db.session.commit()
            
        flash("Login succesfull!")
        return redirect(url_for("user"))    
            
    else:    
        if "user" in session:
            flash("Already logged in.")
            return redirect("user")
        
        return render_template("login.html")

@app.route("/user", methods = ["POST", "GET"])
def user():
    email = None
    if "user" in session:
        user = session["user"]
        
        if request.method == "POST":
            email = request.form["email"]
            session["email"] = email
            found_user = users.query.filter_by(name=user).first()
            found_user.email = email
            db.session.commit()
            flash("E-mail was saved!")
        else:
            if "email" in session:
                email = session["email"] 
        
        return render_template("user.html", email=email)
    else:
        flash("You are not logged in.")
        return redirect(url_for("login"))
    
@app.route("/groups")
def view_groups():
    all_groups = groups.query.all()
    return render_template("groups.html", groups=all_groups)
    
@app.route("/logout")
def logout():
    if "user" in session:
        user = session["user"]
        flash(f"You have been logged out.", "info")
    session.pop("user", None)
    session.pop("email", None)
    return redirect(url_for("login"))

@app.route("/delete/<int:user_id>", methods=["POST"])
def delete(user_id):
    user_to_delete = users.query.get_or_404(user_id)
    try:
        db.session.delete(user_to_delete)
        db.session.commit()
        flash("User deleted successfully!")
    except:
        flash("There was a problem deleting the user.")
    
    return redirect(url_for("view"))

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
