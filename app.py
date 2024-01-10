from flask import Flask, render_template, request, redirect, url_for, session, jsonify, session
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import os
# from passlib.hash import pbkdf2_sha256
import csv
import random
import utils
from kiwipiepy import Kiwi
import sys

global_answer = ''

kiwi = Kiwi()

app = Flask(__name__)
app.secret_key = os.urandom(24)

# SQLite database setup
conn = sqlite3.connect('users.db')
cursor = conn.cursor()
cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        password TEXT
    )
''')
conn.commit()
conn.close()

@app.route('/')
def index():
    if 'username' in session:
        return render_template('game.html', username=session['username'])
    return redirect(url_for('login'))

@app.route('/handle_answer', methods=['POST'])
def handle_answer():
    if 'username' not in session:
        return redirect(url_for('login'))

    user_answer = request.form.get('answer')
    print(user_answer)
    selected_level = int(request.form.get('level'))

    sub_column = f'quiz_{selected_level}_sub'
    correct_column = f'quiz_{selected_level}_correct'

    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute(f'UPDATE users SET {sub_column} = {sub_column} + 1 WHERE username=?', (session['username'],))
    
    correct_answer = get_correct_answer(selected_level)
    conn.commit()
    print(correct_answer)
    if user_answer == correct_answer:
        # Increment the number of correct answers in the database
        print('hi im here')
        correct_column = f"quiz_{selected_level}_correct"

        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()

        update_query = f"UPDATE users SET {correct_column} = {correct_column} + 1 WHERE username=?"
        cursor.execute(update_query, (session['username'],))
        
        conn.commit()

    conn.close()
    session['selected_level'] = selected_level
    return redirect(url_for('index'))

def get_correct_answer(level):
    correct_answers = {
        1: global_answer,  
        2: global_answer, 
        3: global_answer,
        4: global_answer,
    }

    return correct_answers.get(level, "a")  # Default to "a" if level is not found

@app.route('/get_question')
def get_question():
    level = int(request.args.get('level'))
    question, options = get_question_for_level(level)
    print(question)
    return jsonify({"question": question, "options": options})

def get_question_for_level(level):
    with open('eng_kor_pos_formal.csv', 'r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        # questions = [row for row in reader if int(row['pos']) == level]
        questions = [row for row in reader]
    # Randomly select a question for the given level
    if questions:
        global global_answer
        if level == 1:
            selected_question = random.choice(questions)
            kor_sentence = selected_question['korean sentence']
            pos_tagged = utils.kor_pos_tagger(kor_sentence, kiwi)

            simple_pos_list = utils.easy_form(pos_tagged)

            J_list = utils.get_J(simple_pos_list)[0][0]
            empty_kor_sent = kor_sentence.replace(J_list, '__')
            
            global_answer = J_list[0] 
            return empty_kor_sent, utils.make_options(['은', J_list[0], '이', '가']) 
        elif level == 2:
            selected_question = random.sample(questions, 2)
            eng_sentence = selected_question[0]['english sentence']
            kor_sentence = selected_question[0]['korean sentence']
            wrong_kor_sentence = selected_question[1]['korean sentence']
            formal_kor = selected_question[0]['formal korean sentence']
            wrong_formal_kor = selected_question[1]['formal korean sentence']
            
            global_answer = formal_kor
            option = [kor_sentence, wrong_kor_sentence, formal_kor, wrong_formal_kor]
            option_rnd = random.shuffle(option)
            print(option_rnd)
            return eng_sentence, option
        elif level == 3: 
            selected_question = random.choice(questions)
            kor_sentence = selected_question['korean sentence']
            eng_sentence = selected_question['english sentence']

            pos_tagged = utils.kor_pos_tagger(kor_sentence, kiwi)
            simple_pos_list = utils.easy_form(pos_tagged)
            J_list = utils.get_J(simple_pos_list)[0][0]

            empty_kor_sent = kor_sentence.replace(J_list, '__')
            global_answer = J_list[0]
            question = eng_sentence + ' / ' + empty_kor_sent
            return question, None
        elif level == 4: 
            selected_question = random.choice(questions)
            kor_sentence = selected_question['korean sentence']
            eng_sentence = selected_question['english sentence']
            pos = selected_question['essential pos tagging']

            pos_tagged = utils.kor_pos_tagger(kor_sentence, kiwi)
            simple_pos_list = utils.easy_form(pos_tagged)
            J_list = utils.get_J(simple_pos_list)[0][0]

            empty_kor_sent = kor_sentence.replace(J_list, '__')
            global_answer = kor_sentence
            question = eng_sentence + ' / ' + pos
            return question, None
    else:
        return "No question available", ["No answer available"]

conn = sqlite3.connect('users.db')
cursor = conn.cursor()
cursor.execute("PRAGMA table_info(users)")
columns = cursor.fetchall()
column_names = [column[1] for column in columns]

if 'correct_answers' not in column_names:
    cursor.execute('ALTER TABLE users ADD COLUMN correct_answers INTEGER DEFAULT 0')
    conn.commit()

conn.close()

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if verify_user(username, password):
            session['username'] = username
            return redirect(url_for('index'))
        else:
            return render_template('login.html', error='Invalid username or password')

    return render_template('login.html', error=None)

# @app.route('/dashboard')
# def dashboard():
#     if 'username' not in session:
#         return redirect(url_for('login'))

#     conn = sqlite3.connect('users.db')
#     cursor = conn.cursor()
#     cursor.execute('SELECT correct_answers FROM users WHERE username=?', (session['username'],))
#     correct_answers = cursor.fetchone()[0]  # Assuming there's only one user with the given username
#     conn.close()

#     return render_template('dashboard.html', username=session['username'], correct_answers=correct_answers)

@app.route('/dashboard')
def dashboard():
    if 'username' not in session:
        return redirect(url_for('login'))

    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()

    # Fetch all quiz data for the logged-in user
    cursor.execute('SELECT quiz_1_sub, quiz_1_correct, quiz_2_sub, quiz_2_correct, quiz_3_sub, quiz_3_correct, quiz_4_sub, quiz_4_correct, quiz_5_sub, quiz_5_correct  FROM users WHERE username=?', (session['username'],))
    quiz_data = cursor.fetchone()

    conn.close()

    return render_template('dashboard.html', username=session['username'], quiz_data=quiz_data)


@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('index'))

def verify_user(username, password):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE username=? AND password=?', (username, password))
    user = cursor.fetchone()
    conn.close()
    return user is not None

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # hashed_password = generate_password_hash(password, method='sha256')
        # hashed_password = pbkdf2_sha256.hash(password)

        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()
        cursor.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, password))
        conn.commit()
        conn.close()

        return redirect(url_for('login'))

    return render_template('signup.html')

@app.route('/statistics')
def statistics():
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    # Replace the following query with one that matches your schema and requirements
    cursor.execute('SELECT level, COUNT(*) as total_submitted, SUM(case when correct then 1 else 0 end) as total_correct FROM answers GROUP BY level')
    stats = cursor.fetchall()
    conn.close()
    return jsonify(stats)


if __name__ == '__main__':
    # app.run(debug=True)
    app.run(debug=True,port=5000)

