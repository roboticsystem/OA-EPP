import sqlite3,os
p=r'd:\\工程实践4\\OA-EPP\\backend\\data\\exam.db'
if not os.path.exists(p):
    print('DB missing')
else:
    conn=sqlite3.connect(p)
    cur=conn.cursor()
    try:
        cur.execute('SELECT student_id,name FROM students LIMIT 5')
        print('students:',cur.fetchall())
    except Exception as e:
        print('students query error',e)
    try:
        cur.execute('SELECT student_id,email,failed_attempts,locked_until FROM student_accounts LIMIT 5')
        print('accounts:',cur.fetchall())
    except Exception as e:
        print('accounts query error',e)
    conn.close()
