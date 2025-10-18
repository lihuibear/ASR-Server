from datetime import datetime
from mysql.connector import Error
from myutils import mysql_utils


def save_to_mysql(text_content, delay=None):
    """
    将文本内容保存到 MySQL 数据库中的 text_results 表。

    参数:
        text_content (str): 要保存的文本
        delay (int|None): 可选延迟参数（目前未使用）
    """
    connection = None
    cursor = None

    try:
        # 建立数据库连接
        connection = mysql_utils.get_mysql_connection()
        if not connection or not connection.is_connected():
            print("❌ 无法建立数据库连接")
            return

        cursor = connection.cursor()

        # 创建表（如果不存在）
        create_table_query = """
        CREATE TABLE IF NOT EXISTS text_results (
            id INT AUTO_INCREMENT PRIMARY KEY,
            create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
            is_deleted TINYINT(1) DEFAULT 0,
            text_content TEXT,
            update_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        )
        """
        cursor.execute(create_table_query)

        # 插入数据
        insert_query = """
        INSERT INTO text_results (text_content)
        VALUES (%s)
        """
        cursor.execute(insert_query, (text_content,))

        # 提交事务
        connection.commit()
        print("✅ 数据已成功保存到 MySQL 数据库的 text_results 表")

    except Error as e:
        print(f"❌ 数据库错误: {e}")

    finally:
        # 释放资源
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()
            print("🔒 数据库连接已关闭")
