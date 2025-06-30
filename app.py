from flask import session
from flask import Flask, request, jsonify, render_template, redirect, url_for, flash, get_flashed_messages
import sqlite3

app = Flask(__name__)
app.secret_key = 'ubah_dengan_rahasia'

# --- Dummy user login ---
USER = {'username': 'Firli Ar', 'password': 'Firli123'}

# --- Database utility functions ---
def get_db_connection():
    conn = sqlite3.connect('siswa.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS siswa (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nama TEXT NOT NULL,
            nilai INTEGER NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

# --- Route: Landing page ---
@app.route('/')
def welcome():
    return render_template('welcome.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        uname = request.form['username']
        passwd = request.form['password']
        if uname == USER['username'] and passwd == USER['password']:
            session['logged_in'] = True
            return redirect(url_for('halaman_siswa'))
        else:
            flash('Username atau Password salah.', 'error')
            return render_template('login.html')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# --- Route: Halaman data siswa (Read) ---
@app.route('/siswa')
def halaman_siswa():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    conn = get_db_connection()
    rows = conn.execute('SELECT * FROM siswa').fetchall()
    conn.close()
    siswa_list = [dict(row) for row in rows]
    return render_template('index.html', siswa=siswa_list)

# --- Route: Tambah siswa via form (Create) with validation ---
@app.route('/tambah', methods=['POST'])
def tambah_siswa_form():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    nama = request.form['nama'].strip()
    try:
        nilai = int(request.form['nilai'])
    except ValueError:
        flash('Nilai harus berupa angka!', 'error')
        return redirect(url_for('halaman_siswa'))
    if not nama:
        flash('Nama tidak boleh kosong!', 'error')
        return redirect(url_for('halaman_siswa'))
    if nilai < 0 or nilai > 100:
        flash('Nilai harus antara 0 dan 100!', 'error')
        return redirect(url_for('halaman_siswa'))
    conn = get_db_connection()
    conn.execute('INSERT INTO siswa (nama, nilai) VALUES (?, ?)', (nama, nilai))
    conn.commit()
    conn.close()
    flash('Siswa berhasil ditambahkan!', 'success')
    return redirect(url_for('halaman_siswa'))

# --- Route: Edit form ---
@app.route('/siswa/edit/<int:id>')
def edit_siswa_form(id):
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    conn = get_db_connection()
    row = conn.execute('SELECT * FROM siswa WHERE id = ?', (id,)).fetchone()
    conn.close()
    if row is None:
        flash('Siswa tidak ditemukan.', 'error')
        return redirect(url_for('halaman_siswa'))
    siswa_data = dict(row)
    return render_template('edit.html', siswa=siswa_data)

# --- Route: Update via form ---
@app.route('/update/<int:id>', methods=['POST'])
def update_siswa_form(id):
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    nama = request.form['nama'].strip()
    try:
        nilai = int(request.form['nilai'])
    except ValueError:
        flash('Nilai harus berupa angka!', 'error')
        return redirect(url_for('halaman_siswa'))
    if not nama:
        flash('Nama tidak boleh kosong!', 'error')
        return redirect(url_for('halaman_siswa'))
    if nilai < 0 or nilai > 100:
        flash('Nilai harus antara 0 dan 100!', 'error')
        return redirect(url_for('halaman_siswa'))
    conn = get_db_connection()
    conn.execute('UPDATE siswa SET nama = ?, nilai = ? WHERE id = ?', (nama, nilai, id))
    conn.commit()
    conn.close()
    flash('Siswa berhasil diperbarui!', 'success')
    return redirect(url_for('halaman_siswa'))

# --- Route: Hapus siswa (Delete) ---
@app.route('/hapus/<int:id>')
def hapus_siswa_form(id):
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    conn = get_db_connection()
    conn.execute('DELETE FROM siswa WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    flash('Siswa berhasil dihapus!', 'success')
    return redirect(url_for('halaman_siswa'))

# --- API: GET semua siswa ---
@app.route('/api/siswa', methods=['GET'])
def get_siswa_api():
    conn = get_db_connection()
    rows = conn.execute('SELECT * FROM siswa').fetchall()
    conn.close()
    siswa_list = [dict(row) for row in rows]
    return jsonify(siswa_list)

# --- API: GET satu siswa berdasarkan ID ---
@app.route('/api/siswa/<int:id>', methods=['GET'])
def get_siswa_by_id(id):
    conn = get_db_connection()
    row = conn.execute('SELECT * FROM siswa WHERE id = ?', (id,)).fetchone()
    conn.close()
    if row:
        return jsonify(dict(row))
    return jsonify({'message': 'Siswa tidak ditemukan'}), 404

# --- API: POST tambah siswa ---
@app.route('/api/siswa', methods=['POST'])
def tambah_siswa_api():
    data = request.get_json()
    nama = data.get('nama', '').strip()
    nilai = data.get('nilai')
    if not nama:
        return jsonify({'message': 'Boleh kosong'}), 400
    if not isinstance(nilai, int) or nilai < 0 or nilai > 100:
        return jsonify({'message': 'Nilai harus integer antara 0 dan 100'}), 400
    conn = get_db_connection()
    cursor = conn.execute('INSERT INTO siswa (nama, nilai) VALUES (?, ?)', (nama, nilai))
    conn.commit()
    new_id = cursor.lastrowid
    conn.close()
    return jsonify({'message': 'Siswa ditambahkan', 'data': {'id': new_id, 'nama': nama, 'nilai': nilai}}), 201

# --- API: PUT update siswa ---
@app.route('/api/siswa/<int:id>', methods=['PUT'])
def update_siswa_api(id):
    data = request.get_json()
    nama = data.get('nama', '').strip()
    nilai = data.get('nilai')
    if not nama:
        return jsonify({'message': 'Nama tidak boleh kosong'}), 400
    if not isinstance(nilai, int) or nilai < 0 or nilai > 100:
        return jsonify({'message': 'Nilai harus integer antara 0 dan 100'}), 400
    conn = get_db_connection()
    cur = conn.execute('UPDATE siswa SET nama = ?, nilai = ? WHERE id = ?', (nama, nilai, id))
    conn.commit()
    if cur.rowcount == 0:
        conn.close()
        return jsonify({'message': 'Siswa tidak ditemukan'}), 404
    row = conn.execute('SELECT * FROM siswa WHERE id = ?', (id,)).fetchone()
    conn.close()
    return jsonify({'message': 'Siswa diperbarui', 'data': dict(row)})

# --- API: DELETE siswa ---
@app.route('/api/siswa/<int:id>', methods=['DELETE'])
def hapus_siswa_api(id):
    conn = get_db_connection()
    cur = conn.execute('DELETE FROM siswa WHERE id = ?', (id,))
    conn.commit()
    if cur.rowcount == 0:
        conn.close()
        return jsonify({'message': 'Siswa tidak ditemukan'}), 404
    conn.close()
    return jsonify({'message': 'Siswa dihapus'})

# --- Route: Tampilkan data siswa sebagai JSON mentah ---
@app.route('/lihat-db')
def lihat_db_mentah():
    conn = get_db_connection()
    rows = conn.execute('SELECT * FROM siswa').fetchall()
    conn.close()
    data = [dict(row) for row in rows]
    return jsonify(data)

# --- Route: Tampilkan data siswa dalam tabel HTML rapi ---
@app.route('/tabel')
def tampilkan_tabel_html():
    conn = get_db_connection()
    rows = conn.execute('SELECT * FROM siswa').fetchall()
    conn.close()
    siswa_list = [dict(row) for row in rows]
    html = '''
    <html>
    <head>
        <title>Data Siswa (Tabel)</title>
        <style>
            table { border-collapse: collapse; width: 60%; margin: 20px auto; }
            th, td { border: 1px solid #ccc; padding: 8px 12px; text-align: center; }
            th { background-color: #f2f2f2; }
        </style>
    </head>
    <body>
        <h2 style="text-align: center;">Data Siswa</h2>
        <table>
            <tr><th>ID</th><th>Nama</th><th>Nilai</th></tr>
    '''
    for siswa in siswa_list:
        html += f"<tr><td>{siswa['id']}</td><td>{siswa['nama']}</td><td>{siswa['nilai']}</td></tr>"
    html += "</table></body></html>"
    return html

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
