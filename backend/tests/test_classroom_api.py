"""课堂考试 API 集成冒烟测试"""
import os
import tempfile

import pytest
from fastapi.testclient import TestClient

os.environ["DB_PATH"] = tempfile.mktemp(suffix=".db")

from app.database import init_db, db  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture(scope="module")
def client():
    init_db()
    with db() as conn:
        conn.execute(
            "INSERT INTO students (name, student_id) VALUES ('测试','S001')"
        )
        conn.execute(
            """INSERT INTO classroom_exams (id,title,start_at,end_at)
               VALUES ('t1','测验','2020-01-01 00:00:00','2099-12-31 23:59:59')"""
        )
        conn.execute(
            """INSERT INTO classroom_exam_questions
               (exam_id,qtype,content,options_json,answer_key_json,score,sort_no)
               VALUES ('t1','single','Q?','["A","B"]','{"correct":"A"}',2,1)"""
        )
    return TestClient(app)


def test_verify_draft_submit(client):
    r = client.post(
        "/api/classroom-exam/verify",
        json={"student_id": "S001", "exam_id": "t1"},
    )
    assert r.status_code == 200
    token = r.json()["token"]
    headers = {"Authorization": f"Bearer {token}"}

    r2 = client.put(
        "/api/classroom-exam/draft",
        headers=headers,
        json={"answers": {"1": "A"}},
    )
    assert r2.status_code == 200

    r3 = client.post("/api/classroom-exam/submit", headers=headers)
    assert r3.status_code == 200
    assert r3.json()["objective_score"] == 2.0

    # 无法再次获取他人数据：列表仅本人历史
    r4 = client.get("/api/classroom-exam/my-results?student_id=S001")
    assert r4.status_code == 200
    assert len(r4.json()) == 1
