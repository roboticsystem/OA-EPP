def test_student_search_returns_matching_students(client, db_conn):
    db_conn.execute(
        """
        INSERT INTO students (name, student_id, class_name, pinyin, pinyin_abbr)
        VALUES (?, ?, ?, ?, ?)
        """,
        ("张三", "2024001", "机器人1班", "zhangsan", "zs"),
    )
    db_conn.commit()

    response = client.get("/api/students/search", params={"q": "zhang"})

    assert response.status_code == 200
    assert response.json() == [
        {"name": "张三", "student_id": "2024001", "class_name": "机器人1班"}
    ]


def test_student_search_returns_empty_list_for_unknown_student(client):
    response = client.get("/api/students/search", params={"q": "unknown"})

    assert response.status_code == 200
    assert response.json() == []


def test_student_auth_rejects_unknown_student(client):
    response = client.post(
        "/api/auth/verify",
        json={"student_id": "missing", "exam_id": "chapter1"},
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "学号不在名单中，请联系老师确认"


def test_student_auth_returns_token_for_known_student_and_exam(client, db_conn):
    db_conn.execute(
        """
        INSERT INTO students (name, student_id, class_name, pinyin, pinyin_abbr)
        VALUES (?, ?, ?, ?, ?)
        """,
        ("李四", "2024002", "机器人1班", "lisi", "ls"),
    )
    db_conn.execute(
        """
        INSERT INTO exams (id, title, is_active)
        VALUES (?, ?, ?)
        """,
        ("chapter1", "第一章测验", 1),
    )
    db_conn.commit()

    response = client.post(
        "/api/auth/verify",
        json={"student_id": "2024002", "exam_id": "chapter1"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["already_submitted"] is False
    assert body["name"] == "李四"
    assert body["token"]
