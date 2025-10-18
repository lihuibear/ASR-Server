import mysql.connector
from mysql.connector import Error


def get_mysql_connection():
    """
    建立并返回与 MySQL 数据库的连接。
    返回:
        connection (mysql.connector.connection.MySQLConnection): 数据库连接对象
    """
    try:
        connection = mysql.connector.connect(
            host='localhost',      # 数据库主机地址
            user='root',           # 用户名
            password='123456',     # 密码
            database='asr_office'  # 数据库名称
        )

        if connection.is_connected():
            print("✅ 已成功连接到 MySQL 数据库")
            return connection

    except Error as e:
        print(f"❌ 数据库连接错误: {e}")
        return None
