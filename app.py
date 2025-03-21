from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
from io import BytesIO
import base64


app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret_key'

user_name=""

def create_table():
    connection = sqlite3.connect('users.db')
    cursor = connection.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            password TEXT,
            email TEXT
        )
    ''')
    connection.commit()
    connection.close()

    connection = sqlite3.connect('database.db')
    cursor = connection.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user TEXT,
            durata INTEGER,
            data TEXT,
            tip TEXT,
            intensitate TEXT -- 'scazuta' or 'medie' or 'ridicata'
        )
    ''')
    connection.commit()
    connection.close()

    connection = sqlite3.connect('target.db')
    cursor = connection.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS exercises (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user TEXT,
        daily_goal INTEGER,
        weekly_goal INTEGER,
        completed_amount INTEGER DEFAULT 0
    )
''')
    connection.commit()
    connection.close()

create_table()





@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        connection = sqlite3.connect('users.db')
        cursor = connection.cursor()
        cursor.execute('SELECT * FROM users WHERE email=? AND password=?', (email, password))
        user = cursor.fetchone()
        connection.close()
        global user_name

        if user:
            session['user_id'] = user[0]
            user_name = user[1]
            flash('Login successful!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Invalid email or password', 'error')

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash('Logged out successfully', 'success')
    return redirect(url_for('index'))

@app.route('/register', methods=['GET','POST'])
def register():
 if request.method == 'POST':
    name = request.form['name']
    email = request.form['email']
    password = request.form['password']

    connection = sqlite3.connect('users.db')
    cursor = connection.cursor()
    cursor.execute('INSERT INTO users (name, email, password) VALUES (?, ?, ?)', (name, email, password))
    connection.commit()
    connection.close()

    flash('Registration successful! Please log in.', 'success')
    return redirect(url_for('login'))
 return render_template('register.html')
 

@app.route('/add_expense', methods=['POST'])
def add_expense():
    if request.method == 'POST':
        durata = request.form['durata']
        data = request.form['data']
        tip = request.form['tip']
        intensitate = request.form['intensitate']

        global user_name

        connection = sqlite3.connect('database.db')
        cursor = connection.cursor()
        cursor.execute('INSERT INTO expenses (user, durata, data, tip, intensitate) VALUES (?, ?, ?, ?, ?)',
                       (user_name, durata, data, tip, intensitate))
        connection.commit()
        connection.close()

    return redirect(url_for('index'))

@app.route('/adaugare_exercitii', methods=['GET', 'POST'])
def adaugare_exercitii():
    if 'user_id' not in session:
        flash('Please log in first', 'error')
        return redirect(url_for('login'))
    if request.method == 'POST':
        global user_name
        durata = request.form['durata']
        data = request.form['data']
        tip = request.form['tip']
        intensitate = request.form['intensitate']

        connection = sqlite3.connect('database.db')
        cursor = connection.cursor()
        cursor.execute('INSERT INTO expenses (user, durata, data, tip, intensitate) VALUES (?, ?, ?, ?, ?)',
                       (user_name, durata, data, tip, intensitate))
        connection.commit()
        connection.close()

        flash('Expense added successfully', 'success')

    return render_template('adaugare_exercitii.html')

@app.route('/reports')
def reports():
    if 'user_id' not in session:
        flash('Please log in first', 'error')
        return redirect(url_for('login'))
    global user_name

    connection = sqlite3.connect('database.db')
    cursor = connection.cursor()
    cursor.execute('SELECT * FROM expenses WHERE user=?', (user_name,))
    expenses = cursor.fetchall()
    connection.close()

    return render_template('reports.html', expenses=expenses)





@app.route('/tipuri_exercitii')
def tipuri_exercitii():
    return render_template('tipuri_exercitii.html')


# Update the /exercitii route in your code
@app.route('/exercitii', methods=['GET', 'POST'])
def exercitii():
    if 'user_id' not in session:
        flash('Please log in first', 'error')
        return redirect(url_for('login'))

    if request.method == 'POST':
        daily_goal = request.form['daily_goal']
        weekly_goal = request.form['weekly_goal']

        connection = sqlite3.connect('target.db')
        cursor = connection.cursor()
        cursor.execute('INSERT INTO exercises (user, daily_goal, weekly_goal) VALUES (?, ?, ?)',
                       (user_name,  daily_goal, weekly_goal))
        connection.commit()
        connection.close()

    connection = sqlite3.connect('target.db')
    cursor = connection.cursor()
    cursor.execute('SELECT * FROM exercises WHERE user=?', (user_name,))
    exercises = cursor.fetchall()
    connection.close()

    return render_template('objectives.html', exercises=exercises)


@app.route('/notifications')
def notifications():
    if 'user_id' not in session:
        flash('Please log in first', 'error')
        return redirect(url_for('login'))

    global user_name

    # Check if the current day is Sunday
    if datetime.now().weekday() == 6:
        # Get the user's exercises for the past week
        connection = sqlite3.connect('database.db')
        cursor = connection.cursor()
        cursor.execute('SELECT durata, data FROM expenses WHERE user=? AND data BETWEEN date("now", "start of day", "-7 days") AND date("now", "start of day")', (user_name,))
        weekly_exercises = cursor.fetchall()
        connection.close()

        # Get the user's weekly goal
        connection = sqlite3.connect('target.db')
        cursor = connection.cursor()
        cursor.execute('SELECT weekly_goal FROM exercises WHERE user=? ORDER BY id DESC LIMIT 1' , (user_name,))
        weekly_goal = cursor.fetchone()[0]
        connection.close()

        total_duration = sum(weekly_exercises[0], 0)

        if total_duration >= weekly_goal:
            flash('Congratulations! You have completed your weekly goal.', 'success')

    # Check if the user has logged exercises for today
    connection = sqlite3.connect('database.db')
    cursor = connection.cursor()
    today = datetime.now().date()
    cursor.execute('SELECT COUNT(*) FROM expenses WHERE user=? AND data=?', (user_name, today))
    exercises_today = cursor.fetchone()[0]
    cursor.execute('SELECT data FROM expenses WHERE user=?', (user_name,))
    data_ultima = cursor.fetchone()[0]
    cursor.execute('SELECT SUM(durata) FROM expenses WHERE user=? AND data=?', (user_name, data_ultima))
    exercises_today_2 = cursor.fetchone()[0]
    connection.close()

    # Get the user's daily goal
    connection = sqlite3.connect('target.db')
    cursor = connection.cursor()
    cursor.execute('SELECT daily_goal FROM exercises WHERE user=? ORDER BY id DESC LIMIT 1', (user_name,))
    daily_goal = cursor.fetchone()[0]
    connection.close()

    return render_template('notifications.html', exercises_today=exercises_today, exercises_today_2=exercises_today_2, daily_goal=daily_goal)


def get_past_seven_days_data():
    connection = sqlite3.connect('database.db')
    cursor = connection.cursor()
   
    cursor.execute('SELECT MIN(data) FROM expenses WHERE user = ?', (user_name,))
    earliest_date = cursor.fetchone()[0]

    if earliest_date is None:
        
        connection.close()
        return {}

    end_date = datetime.now().date()
    start_date = max(datetime.strptime(earliest_date, '%Y-%m-%d').date(), end_date - timedelta(days=6))

    exercise_data = {day.strftime('%A'): 0 for day in (start_date + timedelta(n) for n in range(7))}

    cursor.execute('SELECT data, durata FROM expenses WHERE data BETWEEN ? AND ? AND user = ?', (start_date, end_date, user_name))
    exercises = cursor.fetchall()

    for exercise in exercises:
        exercise_date = datetime.strptime(exercise[0], '%Y-%m-%d').date()
        day_name = exercise_date.strftime('%A')
        exercise_data[day_name] += exercise[1]

    connection.close()

    return exercise_data

def generate_plot(days, durations, background_color=((0.0157, 0.6667, 0.4275))): 
    fig, ax = plt.subplots()
    ax.bar(days, durations, color=background_color, edgecolor=background_color)
    plt.xlabel('Days')
    plt.ylabel('Total Duration (minutes)')
    plt.title('Exercise Duration for Past 7 Days')

    ax.set_facecolor(((1.0, 0.8901960784313725, 0.7607843137254902))) 

    plt.tight_layout()

    img_buffer = BytesIO()
    plt.savefig(img_buffer, format='png')
    plt.close()

    img_buffer.seek(0)
    img_string = base64.b64encode(img_buffer.read()).decode('utf-8')
    return img_string

@app.route('/exercise_chart')
def exercise_chart():
    if 'user_id' not in session:
        flash('Please log in first', 'error')
        return redirect(url_for('login'))
    exercise_data = get_past_seven_days_data()
    days = list(exercise_data.keys())
    durations = list(exercise_data.values())

    plot_string = generate_plot(days, durations)

    return render_template('exercise_chart.html', plot_string=plot_string)








if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
    app.run(debug=True)

