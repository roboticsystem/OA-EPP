#!/usr/bin/env python3
"""初始化Issue-PR关联功能所需的数据库表"""

import sys
import os

# 添加backend目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database import db


def init_tables():
    """初始化工作流相关表"""
    try:
        with db() as conn:
            # 课程级别的规则配置表
            conn.execute("""
                CREATE TABLE IF NOT EXISTS issue_pr_rules (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    course_id VARCHAR(50) NOT NULL,
                    require_pr_on_close TINYINT(1) DEFAULT 1 COMMENT '关闭Issue时是否必须关联PR',
                    require_merged_pr TINYINT(1) DEFAULT 0 COMMENT '是否要求PR已合并才能关闭Issue',
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    UNIQUE KEY uk_course_id (course_id)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Issue关闭关联PR规则配置'
            """)
            print("✓ issue_pr_rules 表创建成功")
            
            # Issue-PR关联记录表
            conn.execute("""
                CREATE TABLE IF NOT EXISTS issue_pr_associations (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    course_id VARCHAR(50) NOT NULL,
                    issue_number INT NOT NULL COMMENT 'GitHub Issue编号',
                    pr_number INT NOT NULL COMMENT 'GitHub PR编号',
                    pr_title VARCHAR(255) COMMENT 'PR标题',
                    pr_state VARCHAR(20) COMMENT 'PR状态: open/closed/merged',
                    pr_merged_at DATETIME COMMENT 'PR合并时间',
                    closed_by VARCHAR(100) COMMENT '关闭Issue的用户',
                    closed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE KEY uk_issue_course (course_id, issue_number),
                    KEY idx_pr_number (pr_number)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Issue-PR关联记录'
            """)
            print("✓ issue_pr_associations 表创建成功")
            
            # Issue关闭警告记录表
            conn.execute("""
                CREATE TABLE IF NOT EXISTS issue_close_warnings (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    course_id VARCHAR(50) NOT NULL,
                    issue_number INT NOT NULL COMMENT 'GitHub Issue编号',
                    issue_title VARCHAR(255) COMMENT 'Issue标题',
                    closed_by VARCHAR(100) COMMENT '关闭Issue的用户',
                    closed_at DATETIME COMMENT '关闭时间',
                    warning_type VARCHAR(50) DEFAULT 'no_pr_associated' COMMENT '警告类型',
                    warning_message TEXT COMMENT '警告详情',
                    resolved TINYINT(1) DEFAULT 0 COMMENT '是否已处理',
                    resolved_at DATETIME NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    KEY idx_course_closed (course_id, closed_at),
                    KEY idx_resolved (resolved)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Issue关闭警告记录'
            """)
            print("✓ issue_close_warnings 表创建成功")
            
            # 初始化默认规则（如果不存在）
            conn.execute("""
                INSERT IGNORE INTO issue_pr_rules (course_id, require_pr_on_close, require_merged_pr)
                VALUES ('default', 1, 0)
            """)
            print("✓ 默认规则已初始化")
            
        print("\n🎉 所有工作流相关表初始化完成！")
        return True
        
    except Exception as e:
        print(f"\n❌ 表初始化失败: {e}")
        return False


if __name__ == "__main__":
    success = init_tables()
    sys.exit(0 if success else 1)