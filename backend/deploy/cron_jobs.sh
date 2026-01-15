#!/bin/bash
# Claude Skills 定时任务配置
#
# 安装到 cron:
#   crontab -e
#   然后添加以下任务

# ============================================
# 1. 爬虫 + 翻译任务（每天凌晨2点运行）
# ============================================
# 每次爬取最新技能，并翻译50个未翻译的技能
# 0 2 * * * /var/www/claude-skills-miniapp/backend/venv/bin/python /var/www/claude-skills-miniapp/backend/scripts/scheduled_task.py --translate-limit 50 >> /var/log/claude-skills-cron.log 2>&1

# ============================================
# 2. 仅爬虫任务（每12小时运行一次）
# ============================================
# 仅更新技能数据，不翻译（快速更新 stars/forks）
# 0 */12 * * * /var/www/claude-skills-miniapp/backend/venv/bin/python /var/www/claude-skills-miniapp/backend/scripts/scheduled_task.py --skip-translation >> /var/log/claude-skills-cron.log 2>&1

# ============================================
# 3. 仅翻译任务（每小时运行）
# ============================================
# 持续翻译未翻译的技能，每小时翻译10个
# 0 * * * * /var/www/claude-skills-miniapp/backend/venv/bin/python /var/www/claude-skills-miniapp/backend/scripts/scheduled_task.py --skip-crawler --translate-limit 10 >> /var/log/claude-skills-cron.log 2>&1

# ============================================
# 推荐配置（综合方案）
# ============================================
# 每天凌晨2点：爬虫 + 翻译50个
0 2 * * * /var/www/claude-skills-miniapp/backend/venv/bin/python /var/www/claude-skills-miniapp/backend/scripts/scheduled_task.py --translate-limit 50 >> /var/log/claude-skills-cron.log 2>&1

# 每天上午10点和下午4点：仅爬虫（更新数据）
0 10,16 * * * /var/www/claude-skills-miniapp/backend/venv/bin/python /var/www/claude-skills-miniapp/backend/scripts/scheduled_task.py --skip-translation >> /var/log/claude-skills-cron.log 2>&1

# 每3小时：翻译5个未翻译的技能
0 */3 * * * /var/www/claude-skills-miniapp/backend/venv/bin/python /var/www/claude-skills-miniapp/backend/scripts/scheduled_task.py --skip-crawler --translate-limit 5 >> /var/log/claude-skills-cron.log 2>&1

# ============================================
# 日志轮转配置
# ============================================
# 创建日志轮转配置文件: /etc/logrotate.d/claude-skills
#
# /var/log/claude-skills-cron.log {
#     daily
#     missingok
#     rotate 30
#     compress
#     delaycompress
#     notifempty
#     create 0644 root root
# }
