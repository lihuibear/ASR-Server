import mysql.connector
from mysql.connector import Error
from datetime import datetime


def save_to_mysql(text_content, delay=None):
    try:
        # 建立数据库连接
        connection = mysql.connector.connect(
            host='localhost',  # 数据库主机地址
            user='root',  # 数据库用户名
            password='123456',  # 数据库密码
            database='asr_office'  # 数据库名称
        )

        if connection.is_connected():
            cursor = connection.cursor()

            # 创建表（如果不存在）- 完全按照提供的表结构
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

            # 插入数据 - 匹配表结构字段
            insert_query = """
            INSERT INTO text_results (text_content)
            VALUES (%s)
            """
            # 执行插入，仅传入文本内容（其他字段使用默认值）
            cursor.execute(insert_query, (text_content,))

            # 提交事务
            connection.commit()
            print("数据已成功保存到MySQL数据库的text_results表")

    except Error as e:
        print(f"数据库错误: {e}")
    finally:
        # 确保连接被关闭
        if 'connection' in locals() and connection.is_connected():
            cursor.close()
            connection.close()
