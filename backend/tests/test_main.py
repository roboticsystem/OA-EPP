def test_app_can_be_imported(client):
    assert client.app.title == "研究生课程《机器人系统》考试系统"


def test_docs_route_available(client):
    response = client.get("/api/docs")

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]


def test_teacher_page_available(client):
    response = client.get("/teacher")

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]


def test_score_page_available(client):
    response = client.get("/score")

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
