#!/usr/bin/env python3
"""
数据库初始化脚本
快速插入测试数据用于课程展示功能测试
"""

import os
from datetime import datetime, timedelta
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

# 数据库连接字符串
DB_URL = os.environ.get("DB_URL", "mysql+pymysql://student_dev:OaEpp@Dev2026@oaepp-mysql:3306/oaepp_dev")

def init_test_data():
    """初始化测试数据"""
    engine = create_engine(DB_URL)
    
    with Session(engine) as session:
        # 1. 插入学生
        session.execute(text("""
        INSERT IGNORE INTO student (student_id, name, class_name, email, created_at)
        VALUES 
        ('STU001', '张三', '工程实践班', 'zhangsan@example.com', NOW()),
        ('STU002', '李四', '工程实践班', 'lisi@example.com', NOW());
        """))
        session.commit()
        print("✓ 学生数据插入完成")
        
        # 2. 插入课程
        session.execute(text("""
        INSERT IGNORE INTO course (code, name, description, total_chapters, is_active, created_at)
        VALUES 
        ('ENG-PRAC-01', '工程实践1', '第一学期实践课程 - 基础开发环境搭建', 5, TRUE, NOW()),
        ('ENG-PRAC-02', '工程实践2', '第二学期实践课程 - 项目开发', 5, TRUE, NOW()),
        ('ENG-PRAC-03', '工程实践3', '第三学期实践课程 - 高级特性', 5, TRUE, NOW()),
        ('ENG-PRAC-04', '工程实践4', '第四学期实践课程 - 综合应用', 5, TRUE, NOW());
        """))
        session.commit()
        print("✓ 课程数据插入完成")
        
        # 3. 插入学生选课关系
        session.execute(text("""
        INSERT IGNORE INTO student_course (student_id, course_id, status, enrollment_date)
        SELECT s.id, c.id, 'active', NOW()
        FROM student s, course c
        WHERE s.student_id IN ('STU001', 'STU002');
        """))
        session.commit()
        print("✓ 学生选课关系插入完成")
        
        # 4. 插入章节
        session.execute(text(f"""
        INSERT IGNORE INTO chapter (course_id, chapter_num, title, description, `order`, created_at)
        SELECT id, 1, '项目介绍', '课程项目概述和学习目标', 1, NOW() FROM course WHERE code = 'ENG-PRAC-01'
        UNION ALL
        SELECT id, 2, '开发环境搭建', '配置开发工具链', 2, NOW() FROM course WHERE code = 'ENG-PRAC-01'
        UNION ALL
        SELECT id, 3, '基础概念', '学习核心技术原理', 3, NOW() FROM course WHERE code = 'ENG-PRAC-01'
        UNION ALL
        SELECT id, 1, '项目设计', '设计项目架构', 1, NOW() FROM course WHERE code = 'ENG-PRAC-02'
        UNION ALL
        SELECT id, 2, '实现功能模块', '编写业务逻辑', 2, NOW() FROM course WHERE code = 'ENG-PRAC-02';
        """))
        session.commit()
        print("✓ 章节数据插入完成")
        
        # 5. 插入任务
        now = datetime.now()
        session.execute(text(f"""
        INSERT IGNORE INTO task (chapter_id, title, description, task_type, due_date, `order`, created_at)
        SELECT id, '阅读项目文档', '仔细阅读提供的项目文档', 'reading', DATE_ADD(NOW(), INTERVAL 7 DAY), 1, NOW() FROM chapter WHERE title = '项目介绍'
        UNION ALL
        SELECT id, '完成代码示例', '跟随教程完成基础代码示例', 'practice', DATE_ADD(NOW(), INTERVAL 14 DAY), 2, NOW() FROM chapter WHERE title = '项目介绍'
        UNION ALL
        SELECT id, '安装必要工具', '按照文档安装开发工具', 'practice', DATE_ADD(NOW(), INTERVAL 3 DAY), 1, NOW() FROM chapter WHERE title = '开发环境搭建'
        UNION ALL
        SELECT id, '配置编译环境', '设置编译器和构建系统', 'practice', DATE_ADD(NOW(), INTERVAL 5 DAY), 2, NOW() FROM chapter WHERE title = '开发环境搭建'
        UNION ALL
        SELECT id, '理论测试', '完成概念理解测试', 'quiz', DATE_ADD(NOW(), INTERVAL 10 DAY), 1, NOW() FROM chapter WHERE title = '基础概念'
        UNION ALL
        SELECT id, '项目架构设计', '完成项目架构设计文档', 'project', DATE_ADD(NOW(), INTERVAL 20 DAY), 1, NOW() FROM chapter WHERE title = '项目设计'
        UNION ALL
        SELECT id, '实现用户模块', '编写用户管理功能代码', 'practice', DATE_ADD(NOW(), INTERVAL 15 DAY), 1, NOW() FROM chapter WHERE title = '实现功能模块';
        """))
        session.commit()
        print("✓ 任务数据插入完成")
        
        # 6. 插入任务完成记录
        session.execute(text("""
        INSERT IGNORE INTO taskcompletion (student_id, task_id, status, completed_at)
        SELECT s.id, t.id, 'completed', DATE_SUB(NOW(), INTERVAL RAND()*10 DAY)
        FROM student s, task t
        WHERE s.student_id = 'STU001' AND t.chapter_id IN (
            SELECT id FROM chapter WHERE title IN ('项目介绍', '开发环境搭建')
        )
        LIMIT 4;
        """))
        session.commit()
        print("✓ 任务完成记录插入完成")
        
        print("\n✅ 测试数据初始化完成！")
        print("\n数据摘要:")
        
        # 显示数据摘要
        result = session.execute(text("""
        SELECT 
            (SELECT COUNT(*) FROM student) as students,
            (SELECT COUNT(*) FROM course) as courses,
            (SELECT COUNT(*) FROM chapter) as chapters,
            (SELECT COUNT(*) FROM task) as tasks,
            (SELECT COUNT(*) FROM student_course) as enrollments,
            (SELECT COUNT(*) FROM taskcompletion) as completions;
        """)).first()
        
        if result:
            print(f"  - 学生数: {result[0]}")
            print(f"  - 课程数: {result[1]}")
            print(f"  - 章节数: {result[2]}")
            print(f"  - 任务数: {result[3]}")
            print(f"  - 选课关系: {result[4]}")
            print(f"  - 完成任务: {result[5]}")

if __name__ == "__main__":
    try:
        init_test_data()
    except Exception as e:
        print(f"❌ 初始化失败: {e}")
        import traceback
        traceback.print_exc()
