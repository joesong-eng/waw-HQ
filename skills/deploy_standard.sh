#!/bin/bash
# 技能：deploy_standard
# 用法：./skills/deploy_standard.sh "<commit_msg>" "<git_dir>" "<services>"

COMMIT_MSG="${1:-Auto-deploy $(date +%Y%m%d_%H%M)}"
GIT_DIR="${2:-.}"
SERVICES="${3:-}"

echo "🚀 [Skill] Starting Standard Deployment: $GIT_DIR"

cd "$GIT_DIR"
git add .
git commit -m "$COMMIT_MSG"
git push origin main

echo "✅ [Skill] Git push complete. (Restarting services: $SERVICES)"
# 此處未來可擴充遠端 SSH 觸發邏輯，或透過 mq 觸發部署
