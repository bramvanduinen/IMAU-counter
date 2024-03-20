from datetime import datetime, timedelta, timezone
from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

# Simulating database values for the counters and KNMI status
data = {
    "desks_with_monitor": 6,
    "desks_without_monitor": 5,
    "knmi_status": "No",  # Default value
    "last_updated": "Not updated yet"
}

@app.route('/')
def home():
    return render_template('index.html', data=data)

@app.route('/update', methods=['POST'])
def update():
    # Convert form input to integers
    data['desks_with_monitor'] = int(request.form.get('desks_with_monitor', 0))
    data['desks_without_monitor'] = int(request.form.get('desks_without_monitor', 0))
    data['knmi_status'] = request.form.get('knmi_status')
    tz = timezone(timedelta(hours=1))
    data['last_updated'] = datetime.now(tz).strftime("%d/%m/%Y %H:%M:%S")
    return redirect(url_for('home'))


if __name__ == '__main__':
    app.run(debug=True)
