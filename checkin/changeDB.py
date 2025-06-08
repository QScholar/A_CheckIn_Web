import sqlite3

def connect_db(db_file):
    try:
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()
        print("成功连接到数据库")
        return conn, cursor
    except sqlite3.Error as e:
        print(f"连接数据库时出错: {e}")
        return None, None

def update_admin_status(cursor, conn, table_name, id_value,id_key,new_value):
    try:
        query = f"UPDATE {table_name} SET {id_key} = ? WHERE id = ?"
        cursor.execute(query, (new_value, id_value))
        conn.commit()
        if cursor.rowcount > 0:
            print(f"成功更新 ID={id_value} 的 {id_key} 为 {new_value}")
        else:
            print(f"未找到 ID={id_value} 的记录")
    except sqlite3.Error as e:
        print(f"更新数据时出错: {e}")

def main():
    # 替换为你的数据库文件路径
    db_file = "./instance/users.db"
    # 替换为你的表名

    
    conn, cursor = connect_db(db_file)
    
    if conn and cursor:
        # 更新 id=1 的 is_admin 为 1
        update_admin_status(cursor, conn, 
                            table_name='sign_period', 
                            id_value=1,
                            id_key='start_date',
                            new_value='2025-04-16')
        
        # 关闭连接
        cursor.close()
        conn.close()
        print("数据库连接已关闭")

if __name__ == "__main__":
    main()