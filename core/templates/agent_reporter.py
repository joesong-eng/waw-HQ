import json
import os
from pathlib import Path
from datetime import datetime

# 假設 Agent 專案結構
AGENT_BASE_DIR = Path(os.getcwd())
REPORT_DIR = AGENT_BASE_DIR / "_agent"

def generate_report(task_id: str, status: str, summary: str, details: str, exit_code: int = 0):
    """生成標準的 Agent 任務回報檔 (.md 格式)"""
    REPORT_DIR.mkdir(exist_ok=True)
    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    report_filename = f'REPORT_{timestamp}_{task_id}.md'
    report_path = REPORT_DIR / report_filename

    report_content = f"# Agent 自動任務回報\n\n"
    report_content += f"> 任務 ID: {task_id}\n"
    report_content += f"> 狀態: {status}\n"
    report_content += f"> Exit code: {exit_code}\n"
    report_content += f"> 回報時間: {datetime.datetime.now().isoformat()}\n\n"
    report_content += f"## 執行摘要\n\n{summary}\n\n"
    report_content += f"## 執行細節/證明\n\n```\n{details[:12000]}\n```\n"
    report_content += f"\n## 後續風險\n\n請在此處說明潛在風險或注意事項。"

    try:
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(report_content)
        print(f"✅ 回報檔已生成: {report_path}")
        return report_path
    except Exception as e:
        print(f"❌ 生成回報檔失敗: {e}")
        return None

if __name__ == "__main__":
    # 範例用法
    task_id = "example_task_123"
    status = "completed"
    summary = "成功完成範例任務。"
    details = "執行了 x, y, z 步驟，並確認結果無誤。"
    exit_code = 0

    generate_report(task_id, status, summary, details, exit_code)

    # 範例：失敗回報
    task_id_fail = "example_task_456"
    status_fail = "needs_review"
    summary_fail = "任務執行過程中發生錯誤。"
    details_fail = "錯誤日誌：...
    exit_code_fail = 1

    generate_report(task_id_fail, status_fail, summary_fail, details_fail, exit_code_fail)
