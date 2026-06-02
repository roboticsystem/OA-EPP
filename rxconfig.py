import reflex as rx
from reflex.constants import Dirs

config = rx.Config(
    app_name="oaepp",
    # 数据库配置
    db_url="mysql+pymysql://student_dev:OaEpp@Dev2026@oaepp-mysql:3306/oaepp_dev",
    # 项目配置
    frontend_packages=["",],
    # 环境变量
    env=rx.Env.DEV,
)
