from mysql.connector import Error
from myutils import mysql_utils


def get_all_text_results():
    """
    查询 text_results 表中所有未删除的记录。
    返回:
        list[dict]: 每条记录一个字典
    """
    connection = None
    cursor = None
    results = []

    try:
        connection = mysql_utils.get_mysql_connection()
        if not connection or not connection.is_connected():
            print("❌ 无法建立数据库连接")
            return results

        cursor = connection.cursor(dictionary=True)
        query = """
        SELECT id, text_content, create_time, update_time, is_deleted
        FROM text_results
        WHERE is_deleted = 0
        ORDER BY create_time DESC
        """
        cursor.execute(query)
        results = cursor.fetchall()

        print(f"✅ 查询到 {len(results)} 条记录")
        return results

    except Error as e:
        print(f"❌ 数据库错误: {e}")
        return results

    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()
            print("🔒 数据库连接已关闭")


def get_text_result_by_id(record_id):
    """
    根据 id 查询 text_results 表中的单条记录。
    参数:
        record_id (int): 记录的 ID
    返回:
        dict | None: 查询结果字典，未找到返回 None
    """
    connection = None
    cursor = None
    result = None

    try:
        connection = mysql_utils.get_mysql_connection()
        if not connection or not connection.is_connected():
            print("❌ 无法建立数据库连接")
            return None

        cursor = connection.cursor(dictionary=True)
        query = """
        SELECT id, text_content, create_time, update_time, is_deleted
        FROM text_results
        WHERE id = %s
        """
        cursor.execute(query, (record_id,))
        result = cursor.fetchone()

        if result:
            print(f"✅ 已查询到 ID={record_id} 的记录")
        else:
            print(f"⚠️ 未找到 ID={record_id} 的记录")

        return result

    except Error as e:
        print(f"❌ 数据库错误: {e}")
        return None

    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()
            print("🔒 数据库连接已关闭")
