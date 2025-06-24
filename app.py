from flask import Flask, render_template, request, redirect, url_for
import sqlite3
from datetime import datetime
import os
from flask import Flask

app = Flask(__name__)
DB_NAME = 'store.db'

@app.route('/')
def index():
    return "ระบบสโตร์ออนไลน์ทำงานแล้ว!"

def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    c = conn.cursor()
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS products (
            product_id TEXT PRIMARY KEY,
            name TEXT,
            name_cn TEXT,
            model TEXT,
            size TEXT,
            initial_qty INTEGER
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id TEXT,
            date TEXT,
            type TEXT CHECK(type IN ('in', 'out')),
            quantity INTEGER
        )
    ''')
    conn.commit()
    conn.close()

def get_stock_balance(product_id):
    conn = get_db_connection()
    in_qty = conn.execute(
        "SELECT COALESCE(SUM(quantity),0) FROM transactions WHERE product_id=? AND type='in'",
        (product_id,)
    ).fetchone()[0]
    out_qty = conn.execute(
        "SELECT COALESCE(SUM(quantity),0) FROM transactions WHERE product_id=? AND type='out'",
        (product_id,)
    ).fetchone()[0]
    conn.close()
    return in_qty - out_qty

@app.route('/')
def index():
    conn = get_db_connection()
    products = conn.execute('SELECT * FROM products').fetchall()
    product_list = []
    for p in products:
        balance = get_stock_balance(p['product_id'])
        product_list.append({
            'product_id': p['product_id'],
            'name': p['name'],
            'name_cn': p['name_cn'],
            'model': p['model'],
            'size': p['size'],
            'initial_qty': p['initial_qty'],
            'stock_qty': balance + (p['initial_qty'] or 0)
        })
    conn.close()
    return render_template('index.html', products=product_list)

@app.route('/transaction', methods=['GET', 'POST'])
def transaction():
    conn = get_db_connection()
    products = conn.execute('SELECT * FROM products').fetchall()

    if request.method == 'POST':
        product_id = request.form['product_id']
        trans_type = request.form['type']
        quantity = int(request.form['quantity'])
        date = request.form['date']

        conn.execute(
            'INSERT INTO transactions (product_id, date, type, quantity) VALUES (?, ?, ?, ?)',
            (product_id, date, trans_type, quantity)
        )
        conn.commit()
        conn.close()
        return redirect(url_for('index'))

    conn.close()
    return render_template('transaction.html', products=products)

@app.route('/add_product', methods=['GET', 'POST'])
def add_product():
    if request.method == 'POST':
        product_id = request.form['product_id']
        name = request.form['name']
        name_cn = request.form['name_cn']
        model = request.form['model']
        size = request.form['size']
        initial_qty = int(request.form['initial_qty'])

        conn = get_db_connection()
        conn.execute(
            'INSERT INTO products (product_id, name, name_cn, model, size, initial_qty) VALUES (?, ?, ?, ?, ?, ?)',
            (product_id, name, name_cn, model, size, initial_qty)
        )
        conn.commit()
        conn.close()
        return redirect(url_for('index'))

    return render_template('add_product.html')


@app.route('/history')
def history():
    conn = get_db_connection()
    rows = conn.execute('''
        SELECT t.id, p.name, t.product_id, t.date, t.type, t.quantity
        FROM transactions t
        JOIN products p ON t.product_id = p.product_id
        ORDER BY t.date DESC, t.id DESC
    ''').fetchall()
    conn.close()
    return render_template('history.html', transactions=rows)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port, debug=True)