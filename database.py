import sqlite3

# --- 程式碼說明 ---
# 這個檔案包含了所有與資料庫互動的函式。
# 我們的 main.py 會呼叫這些函式來執行增、刪、改、查等操作。

def initialize_db():
    """初始化資料庫，如果表格不存在，就建立它。"""
    # 連結到名為 inventory.db 的資料庫檔案，如果檔案不存在，會自動建立
    conn = sqlite3.connect('inventory.db')
    # 建立一個 cursor 物件，用來執行 SQL 指令
    cursor = conn.cursor()
    
    # 執行 SQL 指令來建立一個名為 ingredients 的表格
    # IF NOT EXISTS 可以確保如果表格已經存在，就不會重複建立而出錯
    # id INTEGER PRIMARY KEY 會自動增長，作為每一筆資料的唯一識別碼
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS ingredients (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        quantity TEXT,
        purchase_date TEXT,
        expiry_date TEXT
    )
    ''')
    
    # 提交變更並關閉連線
    conn.commit()
    conn.close()

def add_ingredient(name, quantity, purchase_date, expiry_date):
    """新增一筆食材資料到資料庫。"""
    conn = sqlite3.connect('inventory.db')
    cursor = conn.cursor()
    # 使用 ? 作為佔位符可以防止 SQL 注入攻擊，更安全
    cursor.execute("INSERT INTO ingredients (name, quantity, purchase_date, expiry_date) VALUES (?, ?, ?, ?)",
                   (name, quantity, purchase_date, expiry_date))
    conn.commit()
    conn.close()

def get_all_ingredients():
    """從資料庫獲取所有食材資料。"""
    conn = sqlite3.connect('inventory.db')
    cursor = conn.cursor()
    # 選擇所有欄位 (*) 從 ingredients 表格，並依照 id 排序
    cursor.execute("SELECT * FROM ingredients ORDER BY id")
    items = cursor.fetchall() # 獲取所有查詢結果
    conn.close()
    return items

def update_ingredient(id, name, quantity, purchase_date, expiry_date):
    """根據 id 更新指定的食材資料。"""
    conn = sqlite3.connect('inventory.db')
    cursor = conn.cursor()
    cursor.execute("UPDATE ingredients SET name=?, quantity=?, purchase_date=?, expiry_date=? WHERE id=?",
                   (name, quantity, purchase_date, expiry_date, id))
    conn.commit()
    conn.close()

def delete_ingredient(id):
    """根據 id 刪除指定的食材資料。"""
    conn = sqlite3.connect('inventory.db')
    cursor = conn.cursor()
    cursor.execute("DELETE FROM ingredients WHERE id=?", (id,))
    conn.commit()
    conn.close()