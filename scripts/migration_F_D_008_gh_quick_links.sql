-- ============================================================================
-- F-D-008: GitHub 快捷链接持久化表
-- 数据库: oaepp_dev
-- 说明: 存储 7 类标准 GitHub 快捷链接的自定义配置（标签、排序、可见性）
-- 执行: 需要 CREATE TABLE 权限（student_dev 无此权限，需管理员执行）
-- ============================================================================

CREATE TABLE IF NOT EXISTS gh_quick_links (
    id          VARCHAR(64)  PRIMARY KEY COMMENT '链接类型: repo/pulls/issues/actions/branches/secrets/branch_protection',
    label       VARCHAR(128) NOT NULL DEFAULT '' COMMENT '自定义标签名称',
    url         VARCHAR(512) NOT NULL DEFAULT '' COMMENT '完整跳转 URL（基于仓库地址自动生成）',
    icon        VARCHAR(64)  NOT NULL DEFAULT 'link-2' COMMENT 'Lucide 图标名称',
    visible     TINYINT(1)   NOT NULL DEFAULT 1 COMMENT '是否可见: 1=可见, 0=隐藏',
    sort_order  INT          NOT NULL DEFAULT 99 COMMENT '显示排序（升序）',
    INDEX idx_visible (visible),
    INDEX idx_sort_order (sort_order)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='GitHub 快捷链接配置';

-- 默认数据（可选预填充，与 DEFAULT_LINK_TYPES 一致）:
-- INSERT INTO gh_quick_links (id, label, url, icon, visible, sort_order) VALUES
-- ('repo',               '仓库主页',             '{REPO_URL}',                     'folder-git-2',      1, 1),
-- ('pulls',              'Pull Requests',       '{REPO_URL}/pulls',               'git-pull-request',  1, 2),
-- ('issues',             'Issues',               '{REPO_URL}/issues',              'alert-circle',      1, 3),
-- ('actions',            'Actions / CI',         '{REPO_URL}/actions',             'play',              1, 4),
-- ('branches',           '分支管理',             '{REPO_URL}/branches',            'git-branch',        1, 5),
-- ('secrets',            'Settings / Secrets',   '{REPO_URL}/settings/secrets/actions', 'key',         1, 6),
-- ('branch_protection',  'Settings / 分支保护',  '{REPO_URL}/settings/branches',   'shield-check',      1, 7);
