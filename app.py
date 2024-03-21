from datetime import datetime, timedelta, timezone
from flask import Flask, render_template, request, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

# Simulating database values for the counters and KNMI status
data = {
    "desks_with_monitor": 6,
    "desks_without_monitor": 5,
    "knmi_status": "No",  # Default value
    "last_updated": "Not updated yet",
}
app.config["SECRET_KEY"] = "your_secret_key"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///site.db"
app.config["SQLALCHEMY_BINDS"] = {"arrival_db": "sqlite:///arrival.db"}

db = SQLAlchemy(app)


class DeskUpdate(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    desks_with_monitor = db.Column(db.Integer, nullable=False)
    desks_without_monitor = db.Column(db.Integer, nullable=False)

    @property
    def people_count(self):
        return 11 - self.desks_with_monitor - self.desks_without_monitor


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)


class Arrival(db.Model):
    """
    docstring so pylint doesn't complain about missing docstring
    """

    __bind_key__ = "arrival_db"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), nullable=False)
    sample_input = db.Column(db.String(255), nullable=False)
    valid_time = db.Column(db.String(255), nullable=False)


@app.route("/")
def home():
    latest_update = DeskUpdate.query.order_by(DeskUpdate.timestamp.desc()).first()
    if latest_update:
        # Update 'data' dictionary with the latest values.
        data["desks_with_monitor"] = latest_update.desks_with_monitor
        data["desks_without_monitor"] = latest_update.desks_without_monitor
        # tz = timezone(timedelta(hours=1))
        data["last_updated"] = latest_update.timestamp.strftime("%d/%m/%Y %H:%M:%S")
    # graph
    updates_today = DeskUpdate.query.filter(
        db.func.date(DeskUpdate.timestamp) == db.func.date(datetime.utcnow())
    ).all()
    updates_yesterday = DeskUpdate.query.filter(
        db.func.date(DeskUpdate.timestamp)
        == db.func.date(datetime.utcnow() - timedelta(days=1))
    ).all()

    if updates_today:
        earliest_today = min(updates_today, key=lambda x: x.timestamp).timestamp
    else:
        earliest_today = None

    if updates_yesterday:
        latest_yesterday = max(updates_yesterday, key=lambda x: x.timestamp).timestamp
    else:
        latest_yesterday = None

    updates_data = [
        (update.timestamp.strftime("%Y-%m-%d %H:%M:%S"), update.people_count)
        for update in DeskUpdate.query.all()
    ]

    return render_template(
        "index.html",
        data=data,
        updates_data=updates_data,
        earliest_today=earliest_today,
        latest_yesterday=latest_yesterday,
    )


@app.route("/update", methods=["POST"])
def update():
    desks_with_monitor = int(request.form.get("desks_with_monitor", 0))
    desks_without_monitor = int(request.form.get("desks_without_monitor", 0))
    update_entry = DeskUpdate(
        desks_with_monitor=desks_with_monitor,
        desks_without_monitor=desks_without_monitor,
    )
    tz = timezone(timedelta(hours=1))
    update_entry.timestamp = datetime.now(
        tz
    )  # This line sets the timestamp with timezone
    db.session.add(update_entry)
    db.session.commit()
    return redirect(url_for("home"))


@app.route("/login")
def login():
    return render_template("login.html")


@app.route("/")
def statistics():
    updates_today = DeskUpdate.query.filter(
        db.func.date(DeskUpdate.timestamp) == db.func.date(datetime.utcnow())
    ).all()
    updates_yesterday = DeskUpdate.query.filter(
        db.func.date(DeskUpdate.timestamp)
        == db.func.date(datetime.utcnow() - timedelta(days=1))
    ).all()

    if updates_today:
        earliest_today = min(updates_today, key=lambda x: x.timestamp).timestamp
    else:
        earliest_today = None

    if updates_yesterday:
        latest_yesterday = max(updates_yesterday, key=lambda x: x.timestamp).timestamp
    else:
        latest_yesterday = None

    updates_data = [
        (update.timestamp.strftime("%Y-%m-%d %H:%M:%S"), update.people_count)
        for update in DeskUpdate.query.all()
    ]

    return render_template(
        "statistics.html",
        updates_data=updates_data,
        earliest_today=earliest_today,
        latest_yesterday=latest_yesterday,
    )


@app.route("/form", methods=["GET", "POST"])
def form():
    if "username" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        username = session["username"]
        sample_time_hour = request.form["sampleTimeHour"]
        sample_time_minute = request.form["sampleTimeMinute"]
        sample_time = f"{sample_time_hour}:{sample_time_minute}"

        if sample_time_hour and sample_time_minute:
            current_date = datetime.now()
            current_date = current_date.replace(
                hour=0, minute=0, second=0, microsecond=0
            )
            tomorrow = current_date + timedelta(days=1)
            new_arrival = Arrival(
                username=username, sample_input=sample_time, valid_time=tomorrow
            )
            db.session.add(new_arrival)
            db.session.commit()
            return render_template("home.html")
        else:
            return "Sample time cannot be empty."

    return render_template("home.html")


@app.route("/logout")
def logout():
    session.pop("username", None)
    return redirect(url_for("login"))


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        app.run(debug=True)
