from flask import Flask, render_template_string, request, redirect, url_for
import sqlite3, os
from datetime import datetime, timedelta

app = Flask(__name__)
DB_PATH = os.path.join(os.path.dirname(__file__), 'reserve.db')

def init_db():
    if not os.path.exists(DB_PATH):
        conn = sqlite3.connect(DB_PATH)
        conn.execute("""
            CREATE TABLE reservations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                payment TEXT,
                start_time TEXT,
                end_time TEXT,
                seats TEXT,
                people_count INTEGER,
                note TEXT
            )
        """)
        conn.commit()
        conn.close()

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def generate_gantt_data(reservations):
    start_time = datetime.strptime("10:00", "%H:%M")
    end_time = datetime.strptime("22:00", "%H:%M")
    time_slots = []
    while start_time < end_time:
        time_slots.append(start_time.strftime("%H:%M"))
        start_time += timedelta(minutes=5)
    seat_lines = {str(i): [''] * len(time_slots) for i in range(1, 13)}
    for r in reservations:
        start = datetime.strptime(r['start_time'], "%H:%M")
        end = datetime.strptime(r['end_time'], "%H:%M")
        seats = r['seats'].split(',')
        for seat in seats:
            seat = seat.strip()
            for i, t in enumerate(time_slots):
                cur_time = datetime.strptime(t, "%H:%M")
                if start <= cur_time < end:
                    seat_lines[seat][i] = r['name']
    return time_slots, seat_lines

@app.route('/')
def index():
    conn = get_db_connection()
    reservations = conn.execute('SELECT * FROM reservations ORDER BY start_time').fetchall()
    conn.close()
    time_slots, seat_lines = generate_gantt_data(reservations)
    names = list(set([r['name'] for r in reservations]))
    return render_template_string(TEMPLATE, reservations=reservations, time_slots=time_slots, seat_lines=seat_lines, names=names)

@app.route('/add', methods=['POST'])
def add_reservation():
    name = request.form['name']
    payment = request.form['payment']
    start_time = request.form['start_time']
    end_time = request.form['end_time']
    people_count = int(request.form['people_count'])
    note = request.form['note']
    seats = request.form.getlist('seats')
    seats_str = ",".join(seats)

    conn = get_db_connection()
    existing = conn.execute('SELECT * FROM reservations').fetchall()
    for r in existing:
        r_start = datetime.strptime(r['start_time'], "%H:%M")
        r_end = datetime.strptime(r['end_time'], "%H:%M")
        cur_start = datetime.strptime(start_time, "%H:%M")
        cur_end = datetime.strptime(end_time, "%H:%M")
        if (r_start < cur_end and cur_start < r_end):
            if set(r['seats'].split(',')) & set(seats):
                conn.close()
                return "예약 중복 발생: 같은 시간에 동일 좌석이 이미 예약됨", 400

    conn.execute('INSERT INTO reservations (name, payment, start_time, end_time, seats, people_count, note) VALUES (?, ?, ?, ?, ?, ?, ?)',
                 (name, payment, start_time, end_time, seats_str, people_count, note))
    conn.commit()
    conn.close()
    return redirect('/')

@app.route('/delete/<int:res_id>')
def delete_reservation(res_id):
    conn = get_db_connection()
    conn.execute('DELETE FROM reservations WHERE id = ?', (res_id,))
    conn.commit()
    conn.close()
    return redirect('/')

TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset='UTF-8'>
    <title>족욕 예약 시스템</title>
    <script>
    function autoFillEndTime() {
        const startInput = document.querySelector('input[name="start_time"]');
        const endInput = document.querySelector('input[name="end_time"]');
        startInput.addEventListener('change', () => {
            const [h, m] = startInput.value.split(':').map(Number);
            const start = new Date(0, 0, 0, h, m);
            const end = new Date(start.getTime() + 30 * 60000);
            const endHours = String(end.getHours()).padStart(2, '0');
            const endMinutes = String(end.getMinutes()).padStart(2, '0');
            endInput.value = `${endHours}:${endMinutes}`;
        });
    }
    window.onload = autoFillEndTime;
    </script>
</head>
<body>
    <h2>새 예약 등록</h2>
    <form action="/add" method="post">
        이름: <input type="text" name="name" list="name_list" required>
        <datalist id="name_list">
            {% for n in names %}
            <option value="{{ n }}">
            {% endfor %}
        </datalist><br>
        결제방식:
        <select name="payment">
            <option>카드</option>
            <option>현금</option>
            <option>계좌이체</option>
        </select><br>
        시작시간: <input type="time" name="start_time" step="300" required><br>
        종료시간: <input type="time" name="end_time" step="300" required><br>
        인원: <input type="number" name="people_count" min="1" required><br>
        좌석 선택:<br>
        {% for i in range(1, 13) %}
            <label><input type="checkbox" name="seats" value="{{ i }}"> {{ i }}번 </label>
        {% endfor %}<br>
        비고: <input type="text" name="note"><br>
        <button type="submit">예약 등록</button>
    </form>

    <h2>예약 목록</h2>
    <table border="1">
        <tr><th>이름</th><th>시간</th><th>좌석</th><th>인원</th><th>결제</th><th>비고</th><th>삭제</th></tr>
        {% for r in reservations %}
        <tr>
            <td>{{ r.name }}</td>
            <td>{{ r.start_time }} ~ {{ r.end_time }}</td>
            <td>{{ r.seats }}</td>
            <td>{{ r.people_count }}</td>
            <td>{{ r.payment }}</td>
            <td>{{ r.note }}</td>
            <td><a href="/delete/{{ r.id }}" onclick="return confirm('정말 삭제하시겠습니까?')">삭제</a></td>
        </tr>
        {% endfor %}
    </table>

    <h2>좌석 간트차트</h2>
    <div style="overflow-x: scroll;">
    <table border="1" style="border-collapse: collapse;">
        <tr>
            <th>좌석 번호</th>
            {% for t in time_slots %}
                <th style="min-width: 50px;">{{ t }}</th>
            {% endfor %}
        </tr>
        {% for seat_num in seat_lines %}
        <tr>
            <td>좌석 {{ seat_num }}</td>
            {% for cell in seat_lines[seat_num] %}
                {% if cell %}
                    <td style="background-color: lightgreen; text-align:center;">{{ cell }}</td>
                {% else %}
                    <td></td>
                {% endif %}
            {% endfor %}
        </tr>
        {% endfor %}
    </table>
    </div>
</body>
</html>
"""

init_db()
if __name__ == '__main__':
    app.run(debug=True)
