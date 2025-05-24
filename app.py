from flask import Flask, render_template_string, request, redirect
import sqlite3, os

app = Flask(__name__)

# DB 파일 경로
DB_PATH = os.path.join(os.path.dirname(__file__), 'reserve.db')

# DB 초기화 (최초 1회 자동 생성)
def init_db():
    if not os.path.exists(DB_PATH):
        conn = sqlite3.connect(DB_PATH)
        conn.execute('''
            CREATE TABLE reservations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                payment TEXT,
                start_time TEXT,
                end_time TEXT,
                seats TEXT,
                people_count INTEGER
            )
        ''')
        conn.commit()
        conn.close()

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def index():
    conn = get_db_connection()
    reservations = conn.execute('SELECT * FROM reservations ORDER BY start_time').fetchall()
    conn.close()
    return render_template_string(TEMPLATE, reservations=reservations)

@app.route('/add', methods=['POST'])
def add_reservation():
    name = request.form['name']
    payment = request.form['payment']
    start_time = request.form['start_time']
    end_time = request.form['end_time']
    seats = request.form['seats']
    people_count = int(request.form['people_count'])

    conn = get_db_connection()
    conn.execute('INSERT INTO reservations (name, payment, start_time, end_time, seats, people_count) VALUES (?, ?, ?, ?, ?, ?)',
                 (name, payment, start_time, end_time, seats, people_count))
    conn.commit()
    conn.close()
    return redirect('/')

TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>족욕 예약 시스템</title>
</head>
<body>
    <h2>새 예약 등록</h2>
    <form action="/add" method="post">
        이름: <input type="text" name="name" required><br>
        결제방식:
        <select name="payment">
            <option>카드</option>
            <option>현금</option>
            <option>계좌이체</option>
        </select><br>
        시작시간: <input type="time" name="start_time" step="300" required><br>
        종료시간: <input type="time" name="end_time" step="300" required><br>
        인원: <input type="number" name="people_count" min="1" required><br>
        좌석번호 (예: 1,2,3): <input type="text" name="seats" required><br>
        <button type="submit">예약 등록</button>
    </form>

    <h2>예약 목록</h2>
    <table border="1">
        <tr><th>이름</th><th>시간</th><th>좌석</th><th>인원</th><th>결제</th></tr>
        {% for r in reservations %}
        <tr>
            <td>{{ r.name }}</td>
            <td>{{ r.start_time }} ~ {{ r.end_time }}</td>
            <td>{{ r.seats }}</td>
            <td>{{ r.people_count }}</td>
            <td>{{ r.payment }}</td>
        </tr>
        {% endfor %}
    </table>
</body>
</html>
'''

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
