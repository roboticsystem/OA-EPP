"""F-S-030 成绩实时统计 — ScoreState

Reflex State — 学生登录后可实时查看本人综合得分及各维度分项
（出勤/考试/代码提交/PR审查），展示评分时间和评分人，待评分项标注状态提示。
"""
from typing import Optional

try:
    import reflex as rx
except Exception:
    rx = None

try:
    from oaepp.database import db_sync
except ImportError:
    from database import db_sync

try:
    from oaepp.constants import SCORE_TYPES
except ImportError:
    from constants import SCORE_TYPES

DIMENSION_LABELS = {
    "attendance": "出勤",
    "exam": "考试",
    "code": "代码提交",
    "pr": "PR审查",
}
DEFAULT_WEIGHTS = {"attendance": 20, "exam": 30, "code": 30, "pr": 20}

_base = 57


def _fetch_scores(user_id: int) -> dict:
    """同步查询数据库，返回成绩数据。"""
    with db_sync() as cur:
        cur.execute("""
            SELECT u.full_name AS name, u.student_no AS student_id, s.class_name
            FROM users u JOIN students s ON u.id = s.user_id
            WHERE u.id = %s
        """, (user_id,))
        student = cur.fetchone()
        if not student:
            return {}

        cur.execute("""
            SELECT c.id, c.name, c.code
            FROM enrollments e JOIN courses c ON e.course_id = c.id
            WHERE e.student_user_id = %s ORDER BY c.id
        """, (user_id,))
        courses = cur.fetchall()
        if not courses:
            return {}

        course = None
        for c in courses:
            cur.execute("SELECT COUNT(*) AS cnt FROM score_items WHERE course_id=%s AND student_user_id=%s", (c["id"], user_id))
            if cur.fetchone()["cnt"] > 0:
                course = c
                break
        if course is None:
            for c in courses:
                cur.execute("""SELECT COUNT(*) AS cnt FROM exam_attempts ea
                    JOIN exams e ON ea.exam_id=e.id WHERE e.course_id=%s AND ea.student_user_id=%s""", (c["id"], user_id))
                if cur.fetchone()["cnt"] > 0:
                    course = c
                    break
        if course is None:
            course = courses[0]

        cur.execute("SELECT attendance_weight, exam_weight, code_weight, pr_weight FROM grade_weight_configs WHERE course_id=%s", (course["id"],))
        wrow = cur.fetchone()
        w = {
            "attendance": float(wrow["attendance_weight"]),
            "exam": float(wrow["exam_weight"]),
            "code": float(wrow["code_weight"]),
            "pr": float(wrow["pr_weight"]),
        } if wrow else dict(DEFAULT_WEIGHTS)

        cur.execute("""
            SELECT si.score_type, si.score
            FROM score_items si WHERE si.course_id=%s AND si.student_user_id=%s
        """, (course["id"], user_id))
        score_items = cur.fetchall()

        cur.execute("""
            SELECT e.id AS exam_id, ea.total_score AS score
            FROM exam_attempts ea JOIN exams e ON ea.exam_id=e.id
            WHERE e.course_id=%s AND ea.student_user_id=%s AND ea.status IN ('graded','submitted')
        """, (course["id"], user_id))
        exam_ids_with_items = {s["ref_id"] for s in score_items if s["score_type"] == "exam"} if score_items else set()
        for r in cur.fetchall():
            if r["exam_id"] not in exam_ids_with_items:
                score_items.append({"score_type": "exam", "score": r["score"]})

    dim_scores = {}
    for dim in SCORE_TYPES:
        items = [s for s in score_items if s["score_type"] == dim]
        total = sum(float(s["score"]) for s in items) if items else 0
        weight = w.get(dim, 0)
        dim_scores[dim] = {
            "label": DIMENSION_LABELS[dim],
            "total_score": round(total, 1),
            "weight": weight,
            "weighted_score": round(total * weight / 100, 1),
        }

    total_weighted = sum(d["weighted_score"] for d in dim_scores.values())
    return {
        "student": student,
        "course": {"id": course["id"], "name": course["name"], "code": course["code"]},
        "weights": w,
        "dimensions": dim_scores,
        "attendance_score": dim_scores["attendance"]["total_score"],
        "exam_score": dim_scores["exam"]["total_score"],
        "code_score": dim_scores["code"]["total_score"],
        "pr_score": dim_scores["pr"]["total_score"],
        "total_score": round(total_weighted, 1),
    }


_Base = rx.State if rx is not None else object

_init = _fetch_scores(_base) if rx is not None else {}


class ScoreState(_Base):
    """成绩实时统计 State"""

    attendance_score: float = _init.get("attendance_score", 0.0)
    exam_score: float = _init.get("exam_score", 0.0)
    code_score: float = _init.get("code_score", 0.0)
    pr_score: float = _init.get("pr_score", 0.0)
    total_score: float = _init.get("total_score", 0.0)
    current_user_id: Optional[int] = _base

    student_info: dict = _init.get("student", {})
    course_info: dict = _init.get("course", {})
    weights: dict = _init.get("weights", {})
    dimensions: dict = _init.get("dimensions", {})
    is_loading: bool = False

    def on_mount(self):
        self.is_loading = True
        yield
        self.is_loading = False

    def load_scores(self):
        data = _fetch_scores(self.current_user_id or _base)
        if not data:
            return
        self.attendance_score = data["attendance_score"]
        self.exam_score = data["exam_score"]
        self.code_score = data["code_score"]
        self.pr_score = data["pr_score"]
        self.total_score = data["total_score"]
        self.weights = data["weights"]
        self.dimensions = data["dimensions"]
        self.student_info = data["student"]
        self.course_info = data["course"]

    def _load_from_db_sync(self):
        data = _fetch_scores(self.current_user_id or _base)
        if not data:
            return
        self.attendance_score = data["attendance_score"]
        self.exam_score = data["exam_score"]
        self.code_score = data["code_score"]
        self.pr_score = data["pr_score"]
        self.total_score = data["total_score"]
        self.weights = data["weights"]
        self.dimensions = data["dimensions"]
        self.student_info = data["student"]
        self.course_info = data["course"]
