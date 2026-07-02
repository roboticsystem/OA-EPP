"""
F-T-003 GitHub账号实名核查（含AI审查）— GitHubRealnameVerifyState

功能概述：
- 通过GitHub API自动获取学生账号name字段
- AI启发式判断是否为真实中文姓名
- 输出三种结论（疑似真名/待人工审查/未填写）及置信度
- 教师可批量核查或手动确认每条结果
- 人工确认与AI判断状态分开记录

验收标准：
- 自动获取GitHub name字段并展示核查状态
- AI输出三种结论及置信度和判断理由摘要
- 教师可对每条结果执行通过/标记异常/发提醒
- 支持批量通过高置信度疑似真名条目
- 人工确认与AI判断状态独立记录
"""

import re
import logging
from typing import List, Dict, Optional
from datetime import datetime

try:
    import reflex as rx
except Exception:
    rx = None

try:
    import httpx
except Exception:
    httpx = None

_log = logging.getLogger(__name__)

# ── 双路径导入 GlobalState ─────────────────────────────────────────────
try:
    from oaepp.states import GlobalState
except Exception:
    from states import GlobalState  # type: ignore[no-redef]

# ── 双路径导入 db / transaction ──────────────────────────────────────────
try:
    from oaepp.database import db, transaction
except Exception:
    from database import db, transaction  # type: ignore[no-redef]

# ── 双路径导入 AuthState ───────────────────────────────────────────────
try:
    from oaepp.states.auth import AuthState
except Exception:
    from states.auth import AuthState  # type: ignore[no-redef]


# ═══════════════════════════════════════════════════════════════════════════
#  AI 启发式姓名分析引擎
# ═══════════════════════════════════════════════════════════════════════════

# 常见中国姓氏（百家姓前100）
_COMMON_CHINESE_SURNAMES = set("""
赵钱孙李周吴郑王冯陈褚卫蒋沈韩杨朱秦尤许何吕施张
孔曹严华金魏陶姜戚谢邹喻柏水窦章云苏潘葛奚范彭郎
鲁韦昌马苗凤花方俞任袁柳酆鲍史唐费廉岑薛雷贺倪汤
滕殷罗毕郝邬安常乐于时傅皮下齐康伍余元卜顾孟平黄
和穆萧尹姚邵湛汪祁毛禹狄米贝明臧计伏成戴谈宋茅庞
熊纪舒屈项祝董梁杜阮蓝闵席季麻强贾路娄危江童颜郭
梅盛林刁钟徐邱骆高夏蔡田樊胡凌霍虞万支柯昝管卢莫
经房裘缪干解应宗丁宣贲邓郁单杭洪包诸左石崔吉钮龚
程嵇邢滑裴陆荣翁荀羊於惠甄麴家封芮羿储靳汲邴糜松
井段富巫乌焦巴弓牧隗山谷车侯宓蓬全郗班仰秋仲伊宫
宁仇栾暴甘钭厉戎祖武符刘景詹束龙叶幸司韶郜黎蓟薄
印宿白怀蒲邰从鄂索咸籍赖卓蔺屠蒙池乔阴鬱胥能苍双
闻莘党翟谭贡劳逄姬申扶堵冉宰郦雍卻璩桑桂濮牛寿通
边扈燕冀郏浦尚农温别庄晏柴瞿阎充慕连茹习宦艾鱼容
向古易慎戈廖庾终暨居衡步都耿满弘匡国文寇广禄阙东
欧殳沃利蔚越夔隆师巩厍聂晁勾敖融冷訾辛阚那简饶空
曾毋沙乜养鞠须丰巢关蒯相查后荆红游竺权逯盖益桓公
""".replace('\n', ''))

# 常见拼音姓氏
_COMMON_PINYIN_SURNAMES = {
    'wang', 'li', 'zhang', 'liu', 'chen', 'yang', 'huang', 'zhao', 'wu', 'zhou',
    'xu', 'sun', 'ma', 'zhu', 'hu', 'guo', 'he', 'gao', 'lin', 'luo',
    'zheng', 'liang', 'xie', 'song', 'tang', 'han', 'cao', 'xu', 'deng', 'xiao',
    'feng', 'zeng', 'cheng', 'cai', 'peng', 'pan', 'yuan', 'yu', 'dong', 'yu',
    'su', 'ye', 'lu', 'wei', 'jiang', 'tian', 'du', 'ding', 'shen', 'ren',
    'yao', 'fan', 'fang', 'shi', 'fu', 'zhong', 'liao', 'xiong', 'jin', 'lu',
    'bai', 'qin', 'mao', 'yan', 'wen', 'gu', 'hao', 'kong', 'duan', 'lei',
}


def _ai_analyze_github_name(name: str, github_username: str = "") -> Dict:
    """AI 启发式分析 GitHub name 字段是否为真实中文姓名

    分析维度：
    1. CJK 汉字检测（Unicode 范围）
    2. 拼音格式检测（首字母大写 + 空格分隔）
    3. 昵称/数字后缀检测
    4. 长度合理性判断
    5. 常见姓氏匹配

    Args:
        name: GitHub 用户 profile 中的 name 字段
        github_username: GitHub 用户名（辅助判断，如 username 包含拼音）

    Returns:
        {
            "verdict": "suspected_real" | "pending_review" | "not_filled",
            "confidence": "high" | "medium" | "low",
            "reason": str  # 中文判断理由摘要
        }
    """
    if not name or not name.strip():
        return {
            "verdict": "not_filled",
            "confidence": "low",
            "reason": "GitHub name 字段为空，无法判断真实姓名"
        }

    name = name.strip()
    name_len = len(name)

    # ── 1. CJK 汉字检测 ──
    cjk_pattern = re.compile(r'[一-鿿㐀-䶿豈-﫿]')
    cjk_chars = cjk_pattern.findall(name)
    cjk_count = len(cjk_chars)

    # ── 2. 纯中文姓名检测 ──
    pure_chinese = re.match(
        r'^[一-鿿·]{2,6}$', name
    )

    # ── 3. 空格分隔的拼音格式 ──
    pinyin_words = re.findall(r'[A-Z][a-z]+', name)
    is_pinyin_format = (
        len(pinyin_words) >= 2
        and all(w.lower() in _COMMON_PINYIN_SURNAMES
                or len(w) <= 8 for w in pinyin_words)
        and re.match(r'^[A-Z][a-z]+(\s+[A-Z][a-z]+)+$', name)
    )

    # ── 4. 特殊模式检测 ──
    has_numbers = bool(re.search(r'\d', name))
    has_special_chars = bool(re.search(
        r'[^一-鿿㐀-䶿a-zA-Z\s\.\-\·]', name
    ))
    word_count = len(name.split())

    # ── 5. 姓氏匹配 ──
    surname_match = False
    if cjk_count >= 1:
        first_char = cjk_chars[0] if cjk_chars else ''
        surname_match = first_char in _COMMON_CHINESE_SURNAMES
    elif pinyin_words:
        first_word_lower = pinyin_words[0].lower() if pinyin_words else ''
        surname_match = first_word_lower in _COMMON_PINYIN_SURNAMES

    # ═════════════════════════════════════════════════════════════════
    #  判断逻辑
    # ═════════════════════════════════════════════════════════════════

    # ✅ 疑似真名：纯中文 2-4 字，含常见姓氏
    if pure_chinese and 2 <= cjk_count <= 4:
        if surname_match and cjk_count <= 3:
            return {
                "verdict": "suspected_real",
                "confidence": "high",
                "reason": f"含{cjk_count}个CJK汉字且首字为常见姓氏，格式完全符合中文姓名特征"
            }
        elif cjk_count <= 3:
            return {
                "verdict": "suspected_real",
                "confidence": "high",
                "reason": f"含{cjk_count}个CJK汉字，格式符合中文姓名特征"
            }
        else:
            return {
                "verdict": "suspected_real",
                "confidence": "medium",
                "reason": f"含{cjk_count}个CJK汉字，字数偏多但仍符合中文姓名格式"
            }

    # ✅ 疑似真名：含 CJK + 间隔号（少数民族姓名如"买买提·吐尔逊"）
    if cjk_count >= 3 and '·' in name and not has_special_chars:
        return {
            "verdict": "suspected_real",
            "confidence": "medium",
            "reason": f"含{cjk_count}个CJK汉字和间隔符，可能为少数民族姓名"
        }

    # ✅ 疑似真名：含 CJK 字符 >= 2
    if cjk_count >= 2 and not has_numbers:
        return {
            "verdict": "suspected_real",
            "confidence": "medium",
            "reason": f"含{cjk_count}个CJK汉字，可能为中文姓名或昵称"
        }

    # ⚠️ 待审查：标准拼音格式（如 Zhang San）
    if is_pinyin_format and surname_match:
        return {
            "verdict": "pending_review",
            "confidence": "medium",
            "reason": "全为ASCII字母，拼音格式且首词匹配常见姓氏，建议人工确认是否为真实姓名"
        }
    if is_pinyin_format:
        return {
            "verdict": "pending_review",
            "confidence": "medium",
            "reason": "全为ASCII字母，拼音特征明显，无CJK字符，建议人工确认"
        }

    # ⚠️ 待审查：单个 CJK + 其他字符混合
    if cjk_count == 1:
        return {
            "verdict": "pending_review",
            "confidence": "low",
            "reason": "仅含1个CJK汉字且混有其他字符，可能是英文名+姓的组合"
        }

    # ⚠️ 待审查：含数字
    if has_numbers:
        return {
            "verdict": "pending_review",
            "confidence": "low",
            "reason": "含数字后缀或ID，昵称特征明显，非标准姓名格式"
        }

    # ⚠️ 待审查：特殊字符
    if has_special_chars:
        return {
            "verdict": "pending_review",
            "confidence": "low",
            "reason": "含特殊字符，不符合真实姓名格式规范"
        }

    # ⚠️ 待审查：纯英文多词（可能为英文名或拼音）
    if word_count >= 2:
        return {
            "verdict": "pending_review",
            "confidence": "low",
            "reason": "含空格的多词英文格式，可能为英文名或拼音，建议人工确认"
        }

    # ⚠️ 待审查：单个英文单词
    if re.match(r'^[A-Za-z]+$', name):
        return {
            "verdict": "pending_review",
            "confidence": "low",
            "reason": "纯ASCII单词语法，可能为英文名、昵称或GitHub handle"
        }

    # 默认：待审查
    return {
        "verdict": "pending_review",
        "confidence": "low",
        "reason": f"无法自动判定姓名格式（长度{name_len}），建议人工审查"
    }


# ═══════════════════════════════════════════════════════════════════════════
#  State
# ═══════════════════════════════════════════════════════════════════════════

class GitHubRealnameVerifyState(
    GlobalState if GlobalState else rx.State if rx else object
):
    """GitHub 账号实名核查状态管理（教师端）"""

    # ── 核查列表数据 ──
    verification_list: List[Dict] = []
    """实名核查数据列表"""

    # ── 统计数据 ──
    total_students: int = 0
    bound_count: int = 0
    pending_bind_count: int = 0
    unbound_count: int = 0
    ai_pending_review_count: int = 0

    # ── AI审查统计 ──
    ai_passed_count: int = 0       # AI判定通过（疑似真名）的数量
    ai_review_count: int = 0       # AI判定待审查的数量
    ai_not_filled_count: int = 0   # AI判定未填写的数量

    # ── 筛选条件 ──
    search_keyword: str = ""
    filter_ai_verdict: str = "全部"  # 全部 / 疑似真名 / 待人工审查 / 未填写

    # ── UI 状态 ──
    is_loading: bool = False
    is_verifying: bool = False      # 正在执行AI核查
    is_batch_processing: bool = False
    action_message: str = ""

    # ── 批量操作 ──
    selected_binding_ids: str = ""  # 逗号分隔的选中ID，用于checkbox联动

    # ── AI核查结果摘要 ──
    last_verify_time: str = ""
    last_verify_summary: str = ""

    # ═════════════════════════════════════════════════════════════════════
    #  数据库表结构保障
    # ═════════════════════════════════════════════════════════════════════

    async def _ensure_schema(self):
        """确保 github_bindings 表包含 AI 审查所需字段"""
        columns_to_add = [
            ("ai_verdict", "VARCHAR(32) DEFAULT NULL"),
            ("ai_confidence", "VARCHAR(16) DEFAULT NULL"),
            ("ai_reason", "TEXT DEFAULT NULL"),
            ("ai_checked_at", "DATETIME DEFAULT NULL"),
            ("human_confirm", "VARCHAR(32) DEFAULT 'pending'"),
            ("human_confirmed_at", "DATETIME DEFAULT NULL"),
            ("human_confirmed_by", "INT DEFAULT NULL"),
        ]
        try:
            async with transaction() as cur:
                for col_name, col_def in columns_to_add:
                    try:
                        await cur.execute(
                            f"ALTER TABLE github_bindings ADD COLUMN {col_name} {col_def}"
                        )
                    except Exception:
                        # 列已存在则跳过
                        pass
        except Exception as e:
            _log.warning(f"_ensure_schema failed: {e}")

    # ═════════════════════════════════════════════════════════════════════
    #  获取当前教师信息
    # ═════════════════════════════════════════════════════════════════════

    async def _get_teacher_id(self) -> int:
        """获取当前登录教师的 user_id"""
        if self.current_user and self.current_user.get("user_id"):
            candidate = int(self.current_user.get("user_id", 0))
            try:
                async with db() as cur:
                    await cur.execute(
                        "SELECT user_id FROM teachers WHERE user_id = %s",
                        (candidate,)
                    )
                    if await cur.fetchone():
                        return candidate
            except Exception:
                pass

        try:
            auth = await self.get_state(AuthState)
            if auth.is_authenticated and auth.current_user_id:
                cid = int(auth.current_user_id)
                async with db() as cur:
                    await cur.execute(
                        "SELECT user_id FROM teachers WHERE user_id = %s", (cid,)
                    )
                    if await cur.fetchone():
                        return cid
        except Exception:
            pass

        # 回退：查询任意教师
        try:
            async with db() as cur:
                await cur.execute(
                    "SELECT u.id FROM users u JOIN teachers t ON u.id = t.user_id "
                    "WHERE u.role='teacher' LIMIT 1"
                )
                row = await cur.fetchone()
                if row:
                    return int(row["id"])
        except Exception:
            pass
        return 1

    # ═════════════════════════════════════════════════════════════════════
    #  数据加载
    # ═════════════════════════════════════════════════════════════════════

    async def load_verification_list(self):
        """加载 GitHub 实名核查列表"""
        self.is_loading = True
        try:
            await self._ensure_schema()

            async with db() as cur:
                await cur.execute("ROLLBACK")

                # 基础查询：所有已绑定的 GitHub 账号 + AI审查字段
                query = """
                    SELECT
                        gb.id,
                        gb.student_user_id,
                        gb.github_username,
                        gb.github_name,
                        gb.verify_status,
                        gb.verified_at,
                        gb.ai_verdict,
                        gb.ai_confidence,
                        gb.ai_reason,
                        gb.ai_checked_at,
                        gb.human_confirm,
                        gb.human_confirmed_at,
                        u.student_no,
                        u.full_name AS student_name,
                        s.class_name
                    FROM github_bindings gb
                    JOIN users u ON gb.student_user_id = u.id
                    JOIN students s ON u.id = s.user_id
                    WHERE 1=1
                """
                params = []

                # 筛选条件
                if self.search_keyword:
                    kw = f"%{self.search_keyword}%"
                    query += (
                        " AND (u.student_no LIKE %s OR u.full_name LIKE %s "
                        "OR gb.github_username LIKE %s OR gb.github_name LIKE %s)"
                    )
                    params.extend([kw, kw, kw, kw])

                if self.filter_ai_verdict == "疑似真名":
                    query += " AND gb.ai_verdict = 'suspected_real'"
                elif self.filter_ai_verdict == "待人工审查":
                    query += " AND (gb.ai_verdict = 'pending_review' OR gb.ai_verdict IS NULL)"
                elif self.filter_ai_verdict == "未填写":
                    query += " AND gb.ai_verdict = 'not_filled'"

                query += " ORDER BY gb.ai_checked_at DESC, u.student_no ASC"

                await cur.execute(query, tuple(params) if params else None)
                rows = await cur.fetchall()

                self.verification_list = []
                for r in rows:
                    ai_verdict = r.get("ai_verdict") or ""
                    item = {
                        "id": r["id"],
                        "student_user_id": r["student_user_id"],
                        "student_no": r["student_no"],
                        "student_name": r["student_name"],
                        "class_name": r.get("class_name", ""),
                        "github_username": r["github_username"],
                        "github_name": r.get("github_name") or "",
                        "verify_status": r["verify_status"],
                        "verified_at": (
                            r["verified_at"].strftime("%Y-%m-%d %H:%M")
                            if r.get("verified_at") else ""
                        ),
                        "ai_verdict": ai_verdict,
                        "ai_verdict_label": _verdict_label(ai_verdict),
                        "ai_confidence": r.get("ai_confidence") or "",
                        "ai_confidence_label": _confidence_label(
                            r.get("ai_confidence") or ""
                        ),
                        "ai_reason": r.get("ai_reason") or "",
                        "ai_checked_at": (
                            r["ai_checked_at"].strftime("%Y-%m-%d %H:%M")
                            if r.get("ai_checked_at") else ""
                        ),
                        "human_confirm": r.get("human_confirm") or "pending",
                        "human_confirm_label": _human_confirm_label(
                            r.get("human_confirm") or "pending"
                        ),
                        "human_confirmed_at": (
                            r["human_confirmed_at"].strftime("%Y-%m-%d %H:%M")
                            if r.get("human_confirmed_at") else ""
                        ),
                        "is_name_empty": not r.get("github_name"),
                    }
                    self.verification_list.append(item)

                # 计算统计
                self._compute_stats(rows)

            # 同时加载未绑定学生
            await self._load_unbound_students()

        except Exception as e:
            _log.exception(f"load_verification_list failed: {e}")
            self.action_message = f"加载数据失败：{e}"
        finally:
            self.is_loading = False

    def _compute_stats(self, rows):
        """根据查询结果计算统计数据"""
        self.total_students = len(rows)
        self.bound_count = sum(
            1 for r in rows if r.get("verify_status") == "approved"
        )
        self.pending_bind_count = sum(
            1 for r in rows if r.get("verify_status") == "pending"
        )
        self.unbound_count = sum(
            1 for r in rows if r.get("verify_status") == "rejected"
        )

        # AI审查统计
        self.ai_passed_count = sum(
            1 for r in rows if r.get("ai_verdict") == "suspected_real"
        )
        self.ai_review_count = sum(
            1 for r in rows
            if r.get("ai_verdict") == "pending_review"
            or r.get("ai_verdict") is None
        )
        self.ai_not_filled_count = sum(
            1 for r in rows if r.get("ai_verdict") == "not_filled"
        )
        self.ai_pending_review_count = self.ai_review_count

    # ═════════════════════════════════════════════════════════════════════
    #  加载未绑定学生（额外查询）
    # ═════════════════════════════════════════════════════════════════════

    async def _load_unbound_students(self):
        """加载未绑定GitHub的学生到列表末尾"""
        try:
            async with db() as cur:
                await cur.execute("ROLLBACK")
                await cur.execute(
                    """
                    SELECT
                        u.id AS student_user_id,
                        u.student_no,
                        u.full_name AS student_name,
                        s.class_name
                    FROM users u
                    JOIN students s ON u.id = s.user_id
                    WHERE u.role = 'student'
                      AND u.id NOT IN (
                          SELECT student_user_id FROM github_bindings
                      )
                    ORDER BY u.student_no ASC
                    """
                )
                rows = await cur.fetchall()
                for r in rows:
                    self.verification_list.append({
                        "id": 0,  # 无绑定记录
                        "student_user_id": r["student_user_id"],
                        "student_no": r["student_no"],
                        "student_name": r["student_name"],
                        "class_name": r.get("class_name", ""),
                        "github_username": "—",
                        "github_name": "—",
                        "verify_status": "unbound",
                        "verified_at": "",
                        "ai_verdict": "",
                        "ai_verdict_label": "",
                        "ai_confidence": "",
                        "ai_confidence_label": "",
                        "ai_reason": "",
                        "ai_checked_at": "",
                        "human_confirm": "pending",
                        "human_confirm_label": "",
                        "human_confirmed_at": "",
                        "is_name_empty": True,
                    })
                self.unbound_count += len(rows)
                self.total_students += len(rows)
        except Exception as e:
            _log.warning(f"_load_unbound_students failed: {e}")

    # ═════════════════════════════════════════════════════════════════════
    #  Setter 方法
    # ═════════════════════════════════════════════════════════════════════

    def set_search_keyword(self, value: str):
        """设置搜索关键词"""
        self.search_keyword = value

    def set_filter_ai_verdict(self, value: str):
        """设置AI判断筛选条件"""
        self.filter_ai_verdict = value

    def set_selected_binding_ids(self, value: str):
        """设置选中的绑定ID列表"""
        self.selected_binding_ids = value

    # ═════════════════════════════════════════════════════════════════════
    #  核心功能：AI 批量核查
    # ═════════════════════════════════════════════════════════════════════

    async def verify_single(self, binding_id: int):
        """对单条绑定执行 AI 实名核查"""
        self.is_verifying = True
        self.action_message = ""
        try:
            await self._ensure_schema()

            # 获取绑定记录
            async with db() as cur:
                await cur.execute("ROLLBACK")
                await cur.execute(
                    "SELECT id, github_username, github_name FROM github_bindings WHERE id = %s",
                    (binding_id,)
                )
                row = await cur.fetchone()
                if not row:
                    self.action_message = "未找到该绑定记录"
                    return

                github_username = row["github_username"]
                github_name = row.get("github_name")

                # 尝试从 GitHub API 获取最新 name
                fresh_name = await self._fetch_github_name(github_username)
                if fresh_name is not None:
                    github_name = fresh_name

                # AI 分析
                result = _ai_analyze_github_name(
                    github_name or "", github_username
                )

            # 保存结果
            async with transaction() as cur:
                await cur.execute(
                    """
                    UPDATE github_bindings
                    SET github_name = %s,
                        ai_verdict = %s,
                        ai_confidence = %s,
                        ai_reason = %s,
                        ai_checked_at = NOW()
                    WHERE id = %s
                    """,
                    (
                        github_name,
                        result["verdict"],
                        result["confidence"],
                        result["reason"],
                        binding_id,
                    ),
                )

            self.last_verify_time = datetime.now().strftime("%Y-%m-%d %H:%M")
            self.action_message = (
                f"核查完成：{result['reason'][:50]}..."
            )
            await self.load_verification_list()

        except Exception as e:
            _log.exception(f"verify_single failed: {e}")
            self.action_message = f"核查失败：{e}"
        finally:
            self.is_verifying = False

    async def verify_all(self):
        """一键全班核查：对所有已绑定的 GitHub 账号执行 AI 实名审查"""
        self.is_verifying = True
        self.action_message = ""
        try:
            await self._ensure_schema()

            async with db() as cur:
                await cur.execute("ROLLBACK")
                await cur.execute(
                    "SELECT id, github_username, github_name FROM github_bindings"
                )
                bindings = await cur.fetchall()

            total = len(bindings)
            verified = 0
            suspected_real = 0
            pending_review = 0
            not_filled = 0

            for b in bindings:
                try:
                    github_username = b["github_username"]
                    github_name = b.get("github_name")

                    # 从 GitHub API 获取最新 name
                    fresh_name = await self._fetch_github_name(github_username)
                    if fresh_name is not None:
                        github_name = fresh_name

                    # AI 分析
                    result = _ai_analyze_github_name(
                        github_name or "", github_username
                    )

                    # 保存
                    async with transaction() as cur:
                        await cur.execute(
                            """
                            UPDATE github_bindings
                            SET github_name = %s,
                                ai_verdict = %s,
                                ai_confidence = %s,
                                ai_reason = %s,
                                ai_checked_at = NOW()
                            WHERE id = %s
                            """,
                            (
                                github_name,
                                result["verdict"],
                                result["confidence"],
                                result["reason"],
                                b["id"],
                            ),
                        )

                    verified += 1
                    if result["verdict"] == "suspected_real":
                        suspected_real += 1
                    elif result["verdict"] == "not_filled":
                        not_filled += 1
                    else:
                        pending_review += 1

                except Exception as e:
                    _log.warning(f"verify_all: failed for binding {b['id']}: {e}")
                    continue

            self.last_verify_time = datetime.now().strftime("%Y-%m-%d %H:%M")
            self.last_verify_summary = (
                f"共扫描 {total} 条 · "
                f"疑似真名 {suspected_real} 人 · "
                f"待审查 {pending_review} 人 · "
                f"未填写 {not_filled} 人"
            )
            self.action_message = (
                f"全班核查完成：成功 {verified}/{total}，"
                f"疑似真名 {suspected_real}，待审查 {pending_review}，未填写 {not_filled}"
            )
            await self.load_verification_list()

        except Exception as e:
            _log.exception(f"verify_all failed: {e}")
            self.action_message = f"全班核查失败：{e}"
        finally:
            self.is_verifying = False

    async def _fetch_github_name(self, github_username: str) -> Optional[str]:
        """通过 GitHub API 获取用户 name 字段"""
        if not github_username or not httpx:
            return None
        try:
            async with httpx.AsyncClient(verify=False, timeout=10.0) as client:
                resp = await client.get(
                    f"https://api.github.com/users/{github_username}",
                    headers={"Accept": "application/vnd.github.v3+json"},
                )
                if resp.status_code == 200:
                    data = resp.json()
                    return data.get("name") or ""
        except Exception as e:
            _log.warning(f"_fetch_github_name failed for {github_username}: {e}")
        return None

    # ═════════════════════════════════════════════════════════════════════
    #  人工确认操作
    # ═════════════════════════════════════════════════════════════════════

    async def human_pass(self, binding_id: int):
        """人工确认通过"""
        await self._human_confirm(binding_id, "passed")

    async def human_mark_abnormal(self, binding_id: int):
        """人工标记异常"""
        await self._human_confirm(binding_id, "abnormal")

    async def _human_confirm(self, binding_id: int, status: str):
        """执行人工确认操作"""
        teacher_id = await self._get_teacher_id()
        self.action_message = ""
        try:
            async with transaction() as cur:
                await cur.execute(
                    """
                    UPDATE github_bindings
                    SET human_confirm = %s,
                        human_confirmed_at = NOW(),
                        human_confirmed_by = %s
                    WHERE id = %s
                    """,
                    (status, teacher_id, binding_id),
                )
                if cur.rowcount == 0:
                    self.action_message = "该记录不存在"
                    return

            label = "通过" if status == "passed" else "标记异常"
            self.action_message = f"已{label}"
            await self.load_verification_list()

        except Exception as e:
            _log.exception(f"_human_confirm failed: {e}")
            self.action_message = f"操作失败：{e}"

    async def human_reset(self, binding_id: int):
        """重置人工确认状态"""
        self.action_message = ""
        try:
            async with transaction() as cur:
                await cur.execute(
                    """
                    UPDATE github_bindings
                    SET human_confirm = 'pending',
                        human_confirmed_at = NULL,
                        human_confirmed_by = NULL
                    WHERE id = %s
                    """,
                    (binding_id,),
                )
            self.action_message = "已重置为待处理"
            await self.load_verification_list()
        except Exception as e:
            _log.exception(f"human_reset failed: {e}")
            self.action_message = f"操作失败：{e}"

    # ═════════════════════════════════════════════════════════════════════
    #  批量操作
    # ═════════════════════════════════════════════════════════════════════

    async def batch_pass_high_confidence(self):
        """批量通过高置信度疑似真名条目"""
        teacher_id = await self._get_teacher_id()
        self.is_batch_processing = True
        self.action_message = ""
        try:
            async with transaction() as cur:
                await cur.execute(
                    """
                    UPDATE github_bindings
                    SET human_confirm = 'passed',
                        human_confirmed_at = NOW(),
                        human_confirmed_by = %s
                    WHERE ai_verdict = 'suspected_real'
                      AND ai_confidence = 'high'
                      AND (human_confirm = 'pending' OR human_confirm IS NULL)
                    """,
                    (teacher_id,),
                )
                count = cur.rowcount

            self.action_message = f"已批量通过 {count} 条高置信度疑似真名条目"
            await self.load_verification_list()

        except Exception as e:
            _log.exception(f"batch_pass_high_confidence failed: {e}")
            self.action_message = f"批量操作失败：{e}"
        finally:
            self.is_batch_processing = False

    async def send_reminder(self, binding_id: int):
        """向学生发送提醒（设置 GitHub name 或修正姓名）"""
        self.action_message = ""
        try:
            async with db() as cur:
                await cur.execute("ROLLBACK")
                await cur.execute(
                    """
                    SELECT u.id AS user_id, u.full_name, gb.github_username
                    FROM github_bindings gb
                    JOIN users u ON gb.student_user_id = u.id
                    WHERE gb.id = %s
                    """,
                    (binding_id,),
                )
                row = await cur.fetchone()
                if not row:
                    self.action_message = "未找到该记录"
                    return

                # 创建通知
                title = "请完善 GitHub 个人资料"
                if row.get("github_username"):
                    body = (
                        f"同学 {row['full_name']}，请在你的 GitHub 个人资料中"
                        f"设置真实中文姓名（Settings → Public profile → Name），"
                        f"以便教师进行实名核查。"
                    )
                else:
                    body = "请先在平台绑定你的 GitHub 账号，并设置真实姓名。"

                async with transaction() as cur2:
                    await cur2.execute(
                        """
                        INSERT INTO notifications
                            (user_id, title, body, category, is_read, created_at)
                        VALUES (%s, %s, %s, 'system', 0, NOW())
                        """,
                        (row["user_id"], title, body),
                    )

            self.action_message = f"已向 {row['full_name']} 发送提醒"
        except Exception as e:
            _log.exception(f"send_reminder failed: {e}")
            self.action_message = f"发送提醒失败：{e}"

    async def batch_send_reminder_not_filled(self):
        """向所有未填写姓名的学生批量发送提醒"""
        self.is_batch_processing = True
        self.action_message = ""
        try:
            async with db() as cur:
                await cur.execute("ROLLBACK")
                await cur.execute(
                    """
                    SELECT gb.id, u.id AS user_id, u.full_name
                    FROM github_bindings gb
                    JOIN users u ON gb.student_user_id = u.id
                    WHERE gb.github_name IS NULL OR gb.github_name = ''
                    """
                )
                rows = await cur.fetchall()

            count = 0
            for r in rows:
                try:
                    async with transaction() as cur2:
                        await cur2.execute(
                            """
                            INSERT INTO notifications
                                (user_id, title, body, category, is_read, created_at)
                            VALUES (%s, %s, %s, 'system', 0, NOW())
                            """,
                            (
                                r["user_id"],
                                "请完善 GitHub 个人资料",
                                f"同学 {r['full_name']}，请在你的 GitHub 个人资料中设置真实中文姓名，以便教师进行实名核查。",
                            ),
                        )
                    count += 1
                except Exception as e:
                    _log.warning(f"batch_send_reminder failed for user {r['user_id']}: {e}")

            self.action_message = f"已向 {count} 名未填写姓名的学生发送提醒"
        except Exception as e:
            _log.exception(f"batch_send_reminder_not_filled failed: {e}")
            self.action_message = f"批量发送失败：{e}"
        finally:
            self.is_batch_processing = False

    # ═════════════════════════════════════════════════════════════════════
    #  工具方法
    # ═════════════════════════════════════════════════════════════════════

    def clear_action_message(self):
        """清除操作提示消息"""
        self.action_message = ""

    # ── 计算属性（供页面响应式绑定） ──

    @rx.var
    def list_count(self) -> int:
        """核查列表条目数"""
        return len(self.verification_list)

    @rx.var
    def summary_text(self) -> str:
        """底部汇总文本"""
        if self.last_verify_summary:
            return (
                f"AI 末次批量审查：{self.last_verify_time} · "
                f"{self.last_verify_summary}"
            )
        if self.last_verify_time:
            return f"AI 末次批量审查：{self.last_verify_time}"
        return "尚未执行批量审查 · 点击「一键全班核查」开始"

    # ═════════════════════════════════════════════════════════════════════
    #  页面生命周期
    # ═════════════════════════════════════════════════════════════════════

    async def on_mount(self):
        """页面加载时初始化"""
        await self._ensure_schema()
        await self.load_verification_list()

    async def refresh(self):
        """手动刷新"""
        self.action_message = ""
        await self.load_verification_list()


# ═══════════════════════════════════════════════════════════════════════════
#  标签映射辅助函数
# ═══════════════════════════════════════════════════════════════════════════

def _verdict_label(verdict: str) -> str:
    """AI判断结论 → 中文标签"""
    mapping = {
        "suspected_real": "✅ 疑似真名",
        "pending_review": "⚠️ 待审查",
        "not_filled": "❌ 未填写",
    }
    return mapping.get(verdict, "")


def _confidence_label(confidence: str) -> str:
    """置信度 → 中文标签"""
    mapping = {
        "high": "高",
        "medium": "中",
        "low": "低",
    }
    return mapping.get(confidence, "")


def _human_confirm_label(status: str) -> str:
    """人工确认状态 → 中文标签"""
    mapping = {
        "passed": "✅ 已通过",
        "abnormal": "⚠️ 异常",
        "pending": "待处理",
    }
    return mapping.get(status, "待处理")
