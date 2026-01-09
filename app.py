from flask import Flask, render_template, request, jsonify
import mysql.connector

app = Flask(__name__)

# --- KONFIGURASI DATABASE ---
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': '',
    'database': 'fire_project_db'
}

def get_db_connection():
    conn = mysql.connector.connect(**db_config)
    return conn

@app.route('/')
def index():
    return render_template('index.html')

# API GET DATA (Untuk Dashboard)
@app.route('/api/data', methods=['GET'])
def get_data():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True) 
    cursor.execute('SELECT * FROM logs ORDER BY id DESC LIMIT 1')
    data = cursor.fetchone()
    cursor.close()
    conn.close()

    if data is None:
        return jsonify({'error': 'Belum ada data'}), 404
    
    # Konversi timestamp ke string agar bisa dikirim JSON
    data['timestamp'] = str(data['timestamp'])
    return jsonify(data)

# API HISTORY (Untuk Grafik)
@app.route('/api/history', methods=['GET'])
def get_history():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('SELECT * FROM logs ORDER BY id DESC LIMIT 10')
    rows = cursor.fetchall()
    cursor.close()
    conn.close()

    # Konversi timestamp
    for row in rows:
        row['timestamp'] = str(row['timestamp'])
    
    return jsonify(rows[::-1])

@app.route('/api/update', methods=['POST'])
def update_sensor():
    new_data = request.get_json()
    suhu = new_data['suhu']
    kelembapan = new_data['kelembapan']
    gas = new_data['status_gas']
    api = new_data['status_api']

    conn = get_db_connection()
    cursor = conn.cursor()
    sql = "INSERT INTO logs (suhu, kelembapan, status_gas, status_api) VALUES (%s, %s, %s, %s)"
    val = (suhu, kelembapan, gas, api)
    
    cursor.execute(sql, val)
    conn.commit()
    cursor.close()
    conn.close()

    return jsonify({'message': 'Data saved to MySQL!'}), 201

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)