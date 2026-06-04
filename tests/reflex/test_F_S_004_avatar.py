"""F-S-004 头像上传 TDD 测试

被测 State : oaepp.states.avatar.AvatarState
TDD RED   : oaepp.states.avatar 不存在 → ImportError → 所有用例失败（预期）
TDD GREEN : AvatarState 实现后 → 全部通过
"""
import pytest

try:
    from oaepp.states.avatar import AvatarState
    _IMPORT_ERROR = None
except ImportError as _e:
    AvatarState = None
    _IMPORT_ERROR = str(_e)


def _guard():
    if _IMPORT_ERROR:
        pytest.fail(f"TDD RED: {_IMPORT_ERROR}")


def test_F_S_004_TC01_state_attrs_exist():
    """State 必须声明 avatar_url、upload_error 变量"""
    _guard()
    for attr in ("avatar_url", "upload_error"):
        assert hasattr(AvatarState, attr), f"缺少 {attr} 状态变量"


async def test_F_S_004_TC02_oversized_file_rejected(mem_db):
    """文件超过 5 MB → upload_avatar() 拒绝，upload_error 非空"""
    _guard()
    state = AvatarState()
    # 模拟 6MB 文件（6 * 1024 * 1024 字节）
    fake_size_bytes = 6 * 1024 * 1024
    await state.upload_avatar(file_name="test.jpg", file_size=fake_size_bytes)
    assert state.upload_error != "", f"超大文件应被拒绝，但 upload_error='{state.upload_error}'"


async def test_F_S_004_TC03_invalid_format_rejected(mem_db):
    """非图片格式（如 .exe）→ 拒绝上传"""
    _guard()
    state = AvatarState()
    await state.upload_avatar(file_name="malware.exe", file_size=1024)
    assert state.upload_error != "", "非图片格式应被拒绝"


def test_F_S_004_TC04_storage_path_format():
    """AvatarState 必须提供 get_avatar_path() 或 avatar_storage_path 属性"""
    _guard()
    has_method = hasattr(AvatarState, "get_avatar_path") and callable(
        getattr(AvatarState, "get_avatar_path")
    )
    has_attr = hasattr(AvatarState, "avatar_storage_path")
    assert has_method or has_attr, "缺少头像存储路径方法/属性"


def test_F_S_004_TC05_default_avatar_exists():
    """AvatarState 必须有 DEFAULT_AVATAR 常量或 default_avatar 属性"""
    _guard()
    has_class_const = hasattr(AvatarState, "DEFAULT_AVATAR")
    has_attr = hasattr(AvatarState, "default_avatar_url")
    assert has_class_const or has_attr, "缺少默认头像定义"
