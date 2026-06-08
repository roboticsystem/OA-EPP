import os
import sqlite3

# Titles to remove
BAD_TITLES = [
    "第 12 章 机器人系统开发环境配置 测验",
    "第二章 CubeMX 编程测验",
    "第三章 PicSimlab 仿真开发测验",
]

CANDIDATES = [
    os.environ.get("DB_PATH"),
    os.path.join(os.getcwd(), "data", "exam.db"),
    os.path.join(os.getcwd(), "..", "data", "exam.db"),
    os.path.join(os.getcwd(), "exam.db"),
    "/app/data/exam.db",
]

CANDIDATES = [p for p in CANDIDATES if p]

def find_db():
    for p in CANDIDATES:
        if os.path.exists(p):
            return p
    return None

def main():
    db = find_db()
    if not db:
        print("未找到数据库文件。请设置环境变量 DB_PATH 或将 exam.db 放在 data/ 或 当前目录。候选路径:\n" + "\n".join(CANDIDATES))
        return
    print("使用数据库：", db)
    conn = sqlite3.connect(db)
    cur = conn.cursor()
    removed = 0
    for t in BAD_TITLES:
        # delete from exams and classroom_exams
        cur.execute("DELETE FROM exams WHERE title=?", (t,))
        removed += cur.rowcount
        cur.execute("DELETE FROM classroom_exams WHERE title=?", (t,))
        removed += cur.rowcount
        # Also remove any orphaned questions/attempts
        # find ids
        cur.execute("SELECT id FROM classroom_exams WHERE title=?", (t,))
        rows = cur.fetchall()
        for (eid,) in rows:
            cur.execute("DELETE FROM classroom_exam_questions WHERE exam_id=?", (eid,))
            cur.execute("DELETE FROM classroom_exam_attempts WHERE exam_id=?", (eid,))
    conn.commit()
    conn.close()
    print(f"清理完成，尝试删除 {len(BAD_TITLES)} 个标题，受影响行数(approx): {removed}")

if __name__ == '__main__':
    main()
