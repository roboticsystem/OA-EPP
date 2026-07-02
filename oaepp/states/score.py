"""F-S-030 成绩实时统计 — ScoreState

Reflex State — 学生登录后可实时查看本人综合得分及各维度分项
（出勤/考试/代码提交/PR审查），展示评分时间和评分人，待评分项标注状态提示。
"""
from typing import Optional

try:
    import reflex as rx
except Exception:
    rx = None

from oaepp.database import db
from oaepp.constants import SCORE_TYPES

DIMENSION_LABELS = {
    "attendance": "出勤",
    "exam": "考试",
    "code": "代码提交",
    "pr": "PR审查",
}
DEFAULT_WEIGHTS = {"attendance": 20, "exam": 30, "code": 30, "pr": 20}


_Base = rx.State if rx is not None else object


class ScoreState(_Base):
    """成绩实时统计 State — 提供学生成绩看板数据查询。"""

    attendance_score: float = 0.0
    exam_score: float = 0.0
    code_score: float = 0.0
    pr_score: float = 0.0
    total_score: float = 0.0
    current_user_id: Optional[int] = None

    student_info: dict = {}
    course_info: dict = {}
    weights: dict = {}
    dimensions: dict = {}
    is_loading: bool = False

    async def load_scores(self) -> dict:
        """加载当前学生的成绩看板数据。"""
        if self.current_user_id is None:
            return {"error": "未设置用户"}

        result = await self._load_from_db()
        if isinstance(result, dict) and "error" in result:
            self.total_score = 0.0
            return result

        self.attendance_score = result["attendance_score"]
        self.exam_score = result["exam_score"]
        self.code_score = result["code_score"]
        self.pr_score = result["pr_score"]
        self.total_score = result["total_score"]
        self.weights = result["weights"]
        self.dimensions = result["dimensions"]
        self.student_info = result["student"]
        self.course_info = result["course"]

        return {
            "student": result["student"],
            "course": result["course"],
            "weights": result["weights"],
            "dimensions": result["dimensions"],
            "total_score": result["total_score"],
        }

    async def _load_from_db(self):
        async with db() as cur:
            student = await self._get_student_info(cur, self.current_user_id)
            if not student:
                return {"error": "学生信息不存在"}

            courses = await self._get_enrolled_courses(cur, self.current_user_id)
            if not courses:
                return {"error": "未选课"}

            course = await self._pick_course(cur, courses)
            weights = await self._get_weights(cur, course["id"])
            score_items = await self._get_score_items(cur, course["id"], self.current_user_id)
            exam_scores = await self._get_exam_attempt_scores(cur, course["id"], self.current_user_id)
            pending_items = await self._get_pending_items(cur, course["id"], self.current_user_id)

        all_exam = [s for s in score_items if s["score_type"] == "exam"]
        seen_ids = {s["ref_id"] for s in all_exam}
        for es in exam_scores:
            if es["ref_id"] not in seen_ids:
                score_items.append(es)

        dim_scores = {}
        for dim in SCORE_TYPES:
            items = [s for s in score_items if s["score_type"] == dim]
            total = sum(item["score"] for item in items) if items else 0
            pending = [p for p in pending_items if p["pending_type"] == dim]

            dim_scores[dim] = {
                "label": DIMENSION_LABELS[dim],
                "items": items,
                "total_score": round(total, 1),
                "count": len(items),
                "pending_count": len(pending),
                "pending_items": pending,
            }

        total_weighted = 0
        for dim in SCORE_TYPES:
            d = dim_scores[dim]
            weight = weights.get(dim, 0)
            d["weight"] = weight
            d["weighted_score"] = round(d["total_score"] * weight / 100, 1)
            total_weighted += d["weighted_score"]

        return {
            "student": student,
            "course": {"id": course["id"], "name": course["name"], "code": course["code"]},
            "weights": weights,
            "dimensions": dim_scores,
            "attendance_score": dim_scores["attendance"]["total_score"],
            "exam_score": dim_scores["exam"]["total_score"],
            "code_score": dim_scores["code"]["total_score"],
            "pr_score": dim_scores["pr"]["total_score"],
            "total_score": round(total_weighted, 1),
        }

    # ── 数据库查询方法 ──

    @staticmethod
    async def _get_student_info(cur, user_id):
        await cur.execute("""
            SELECT u.full_name AS name, u.student_no AS student_id, s.class_name
            FROM users u
            JOIN students s ON u.id = s.user_id
            WHERE u.id = %s
        """, (user_id,))
        return await cur.fetchone()

    @staticmethod
    async def _get_enrolled_courses(cur, user_id):
        await cur.execute("""
            SELECT c.id, c.name, c.code
            FROM enrollments e
            JOIN courses c ON e.course_id = c.id
            WHERE e.student_user_id = %s
            ORDER BY c.id
        """, (user_id,))
        return await cur.fetchall()

    @staticmethod
    async def _pick_course(cur, courses):
        for c in courses:
            await cur.execute("SELECT COUNT(*) AS cnt FROM exams WHERE course_id = %s", (c["id"],))
            row = await cur.fetchone()
            if row["cnt"] > 0:
                return c
        return courses[0]

    @staticmethod
    async def _get_weights(cur, course_id):
        await cur.execute("""
            SELECT attendance_weight, exam_weight, code_weight, pr_weight
            FROM grade_weight_configs
            WHERE course_id = %s
        """, (course_id,))
        row = await cur.fetchone()
        if row:
            return {
                "attendance": float(row["attendance_weight"]),
                "exam": float(row["exam_weight"]),
                "code": float(row["code_weight"]),
                "pr": float(row["pr_weight"]),
            }
        return dict(DEFAULT_WEIGHTS)

    @staticmethod
    async def _get_score_items(cur, course_id, user_id):
        await cur.execute("""
            SELECT si.id, si.score_type, si.score, si.scored_at,
                   si.ref_id, u.full_name AS scorer_name
            FROM score_items si
            LEFT JOIN users u ON si.scored_by = u.id
            WHERE si.course_id = %s AND si.student_user_id = %s
            ORDER BY si.scored_at DESC
        """, (course_id, user_id))
        rows = await cur.fetchall()
        result = []
        for r in rows:
            result.append({
                "id": r["id"],
                "score_type": r["score_type"],
                "score": float(r["score"]) if r["score"] else 0,
                "scored_at": r["scored_at"].strftime("%Y-%m-%d %H:%M:%S") if r.get("scored_at") else None,
                "scorer_name": r["scorer_name"] or "系统",
                "ref_id": r["ref_id"],
            })
        return result

    @staticmethod
    async def _get_exam_attempt_scores(cur, course_id, user_id):
        await cur.execute("""
            SELECT ea.id, e.id AS exam_id, e.title AS exam_name,
                   ea.total_score AS score, ea.submitted_at,
                   u.full_name AS scorer_name
            FROM exam_attempts ea
            JOIN exams e ON ea.exam_id = e.id
            LEFT JOIN users u ON e.created_by = u.id
            WHERE e.course_id = %s AND ea.student_user_id = %s
              AND ea.status IN ('graded', 'submitted')
            ORDER BY ea.submitted_at DESC
        """, (course_id, user_id))
        rows = await cur.fetchall()
        result = []
        for r in rows:
            result.append({
                "id": r["id"],
                "score_type": "exam",
                "score": float(r["score"]) if r["score"] else 0,
                "scored_at": r["submitted_at"].strftime("%Y-%m-%d %H:%M:%S") if r.get("submitted_at") else None,
                "scorer_name": r["scorer_name"] or "系统",
                "ref_id": r["exam_id"],
                "source": "exam_attempt",
                "exam_name": r["exam_name"],
            })
        return result

    @staticmethod
    async def _get_pending_items(cur, course_id, user_id):
        pending = []
        await cur.execute("""
            SELECT e.id, e.title AS name FROM exams e
            WHERE e.course_id = %s AND NOT EXISTS (
                SELECT 1 FROM exam_attempts ea
                WHERE ea.exam_id = e.id AND ea.student_user_id = %s
            )
        """, (course_id, user_id))
        for r in await cur.fetchall():
            pending.append({"pending_type": "exam", "label": "考试", "name": r["name"], "ref_id": r["id"]})

        await cur.execute("""
            SELECT s.id, a.title AS name FROM submissions s
            JOIN assignments a ON s.assignment_id = a.id
            WHERE a.course_id = %s AND s.student_user_id = %s AND s.grading_status = 'pending'
        """, (course_id, user_id))
        for r in await cur.fetchall():
            pending.append({"pending_type": "code", "label": "代码提交", "name": r["name"], "ref_id": r["id"]})

        await cur.execute("""
            SELECT id, issue_no AS name FROM pr_records
            WHERE course_id = %s AND student_user_id = %s AND quality_score IS NULL
        """, (course_id, user_id))
        for r in await cur.fetchall():
            name = f"PR #{r['name']}" if r["name"] else f"记录 #{r['id']}"
            pending.append({"pending_type": "pr", "label": "PR审查", "name": name, "ref_id": r["id"]})

        await cur.execute("""
            SELECT ar.id, as2.id AS session_id FROM attendance_records ar
            JOIN attendance_sessions as2 ON ar.session_id = as2.id
            WHERE as2.course_id = %s AND ar.student_user_id = %s AND ar.status = 'absent'
        """, (course_id, user_id))
        for r in await cur.fetchall():
            pending.append({"pending_type": "attendance", "label": "出勤", "name": f"签到 #{r['session_id']}", "ref_id": r["id"]})

        return pending
