import sqlite3

# 连接到数据库文件
def connect_db(db_file):
    try:
        # 建立连接
        conn = sqlite3.connect(db_file)
        # 创建游标
        cursor = conn.cursor()
        print("成功连接到数据库")
        return conn, cursor
    except sqlite3.Error as e:
        print(f"连接数据库时出错: {e}")
        return None, None

# 查询数据库中的表
def get_tables(cursor):
    try:
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        print("数据库中的表:", tables)
        return tables
    except sqlite3.Error as e:
        print(f"查询表时出错: {e}")
        return []

# 查询表中的数据
def query_table(cursor, table_name):
    try:
        cursor.execute(f"SELECT * FROM {table_name}")
        rows = cursor.fetchall()
        print(f"表 {table_name} 中的数据:")
        for row in rows:
            print(row)
        return rows
    except sqlite3.Error as e:
        print(f"查询数据时出错: {e}")
        return []

# 主函数
def main():
    # 替换为你的 .db 文件路径
    db_file = "./instance/users.db"
    
    # 连接数据库
    conn, cursor = connect_db(db_file)
    


    if conn and cursor:
        # 获取所有表
        tables = get_tables(cursor)
        tn=int(input())
        # 如果有表，查询第一个表的数据
        if tables:
            table_name = tables[tn][0]  # 获取第一个表名
            query_table(cursor, table_name)
            # query_table(cursor,'check_in_record')
        
        # 关闭连接
        cursor.close()
        conn.close()
        print("数据库连接已关闭")

if __name__ == "__main__":
    main()
