#!/usr/bin/env python3
"""
Shannie Taskflow Bridge Server
專屬 Shannie (Executive Assistant / Strategic Advisor) 的安全橋接服務。
限制僅能存取 .taskflow/shannie/ 目錄，提供簡明的高階商業通訊 API。
"""

import os
import sys
import json
import glob
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

ENV_FILE = "/Users/ilawusong/.config/shannie_bridge/bridge.env"

def load_env():
    env = {}
    if os.path.exists(ENV_FILE):
        with open(ENV_FILE, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    env[k.strip()] = v.strip()
    return env

CONFIG = load_env()
PORT = int(CONFIG.get("SHANNIE_BRIDGE_PORT", 8089))
TOKEN = CONFIG.get("SHANNIE_BRIDGE_TOKEN", "")
TASKFLOW_DIR = CONFIG.get("SHANNIE_TASKFLOW_DIR", "/Users/ilawusong/Documents/WaW/.taskflow/shannie")
WAW_DIR = CONFIG.get("WAW_DIR", "/Users/ilawusong/Documents/WaW")

INBOX_DIR = os.path.join(TASKFLOW_DIR, "inbox")
OUTBOX_DIR = os.path.join(TASKFLOW_DIR, "outbox")
CONTEXT_DIR = os.path.join(TASKFLOW_DIR, "context")
TASK_LOG = os.path.join(WAW_DIR, ".taskflow", "task_flow.log")

for d in [INBOX_DIR, OUTBOX_DIR, CONTEXT_DIR]:
    os.makedirs(d, exist_ok=True)

class BridgeHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass
    def send_cors_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Authorization, Content-Type")

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_cors_headers()
        self.end_headers()

    def send_json(self, status_code, data):
        body = json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_cors_headers()
        self.end_headers()
        self.wfile.write(body)

    def check_auth(self):
        if not TOKEN:
            return True
        auth_header = self.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            req_token = auth_header[7:].strip()
            if req_token == TOKEN:
                return True
        return False

    def get_public_url(self):
        forwarded_proto = self.headers.get("X-Forwarded-Proto", "https")
        host = self.headers.get("Host", f"localhost:{PORT}")
        if "localhost" in host or "127.0.0.1" in host:
            return f"http://{host}"
        return f"{forwarded_proto}://{host}"

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path

        # 1. OpenAPI Spec (Public for ChatGPT Action import)
        if path in ["/openapi.json", "/api/openapi.json"]:
            self.handle_openapi()
            return

        # 2. Health check (Public)
        if path in ["/health", "/api/health"]:
            self.send_json(200, {
                "status": "ok",
                "service": "Shannie Taskflow Bridge",
                "version": "1.0.0",
                "timestamp": datetime.now().isoformat()
            })
            return

        # Protected routes below
        if not self.check_auth():
            self.send_json(401, {"error": "Unauthorized", "message": "Valid Bearer token required"})
            return

        # 3. List / Read Inbox
        if path == "/api/inbox":
            self.handle_list_inbox()
            return
        elif path.startswith("/api/inbox/"):
            msg_id = path[len("/api/inbox/"):]
            self.handle_read_inbox(msg_id)
            return

        # 4. Read Context
        if path == "/api/context":
            self.handle_read_context()
            return

        # 5. List Outbox
        if path == "/api/outbox":
            self.handle_list_outbox()
            return

        self.send_json(404, {"error": "Not Found", "path": path})

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path

        if not self.check_auth():
            self.send_json(401, {"error": "Unauthorized", "message": "Valid Bearer token required"})
            return

        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length) if content_length > 0 else b""
        
        data = {}
        if body:
            try:
                data = json.loads(body.decode("utf-8"))
            except Exception as e:
                self.send_json(400, {"error": "Invalid JSON", "detail": str(e)})
                return

        # 1. Post to Outbox (Strategic Recommendation to HQ)
        if path == "/api/outbox":
            self.handle_post_outbox(data)
            return

        # 2. Update Context
        if path == "/api/context":
            self.handle_update_context(data)
            return

        self.send_json(404, {"error": "Not Found", "path": path})

    # --- Handlers ---

    def handle_openapi(self):
        base_url = self.get_public_url()
        spec = {
            "openapi": "3.1.0",
            "info": {
                "title": "Shannie Taskflow Bridge API",
                "description": "專屬 Shannie (Executive Assistant / Strategic Advisor) 的專屬通訊 API。僅限存取 .taskflow/shannie/，提供讀取 HQ 諮詢信件、發送策略建議回信、以及維護 JOE 決策原則功能。",
                "version": "1.0.0"
            },
            "servers": [{"url": base_url}],
            "paths": {
                "/api/inbox": {
                    "get": {
                        "operationId": "getInboxMessages",
                        "summary": "讀取 HQ 傳給 Shannie 的待評估訊息清單",
                        "description": "列出 .taskflow/shannie/inbox/ 目錄下所有來自 HQ 的策略諮詢信件，包含全文內容與時間戳記。",
                        "responses": {
                            "200": {
                                "description": "成功取得信件清單",
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "type": "object",
                                            "properties": {
                                                "success": {"type": "boolean"},
                                                "count": {"type": "integer"},
                                                "messages": {
                                                    "type": "array",
                                                    "items": {
                                                        "type": "object",
                                                        "properties": {
                                                            "id": {"type": "string"},
                                                            "filename": {"type": "string"},
                                                            "mtime": {"type": "string"},
                                                            "content": {"type": "string"}
                                                        }
                                                    }
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                },
                "/api/outbox": {
                    "post": {
                        "operationId": "sendStrategicRecommendation",
                        "summary": "送出策略建議或決策回覆給 HQ",
                        "description": "將 Shannie 的高階決策建議以標準格式排版，寫入 .taskflow/shannie/outbox/，並自動登記至索引與日誌中供 HQ 查閱。",
                        "requestBody": {
                            "required": True,
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "required": ["topic", "conclusion", "reason", "action_for_hq"],
                                        "properties": {
                                            "topic": {"type": "string", "description": "策略議題名稱（例如：美國市場切入點、韌體商務包裝）"},
                                            "conclusion": {"type": "string", "description": "核心決策建議與結論"},
                                            "reason": {"type": "string", "description": "決策背景、商業考量與 JOE 目標對齊依據"},
                                            "action_for_hq": {"type": "string", "description": "給 HQ 的架構方針與具體行動引導"},
                                            "task_id": {"type": "string", "description": "對應 HQ 來信的任務編號（若有）"}
                                        }
                                    }
                                }
                            }
                        },
                        "responses": {
                            "200": {
                                "description": "回覆已成功送達 HQ Outbox",
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "type": "object",
                                            "properties": {
                                                "success": {"type": "boolean"},
                                                "file": {"type": "string"},
                                                "message": {"type": "string"}
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    },
                    "get": {
                        "operationId": "getOutboxHistory",
                        "summary": "查看 Shannie 已發送給 HQ 的歷史策略回覆",
                        "responses": {
                            "200": {
                                "description": "歷史發送紀錄",
                                "content": {"application/json": {"schema": {"type": "object"}}}
                            }
                        }
                    }
                },
                "/api/context": {
                    "get": {
                        "operationId": "getDecisionContext",
                        "summary": "讀取 JOE 核心方向與商業原則 (Context)",
                        "description": "讀取 .taskflow/shannie/context/ 下的 joe_direction.md 與 business_principles.md，掌握決策核心依據。",
                        "responses": {
                            "200": {
                                "description": "成功取得上下文",
                                "content": {"application/json": {"schema": {"type": "object"}}}
                            }
                        }
                    },
                    "post": {
                        "operationId": "updateDecisionContext",
                        "summary": "更新或補充 JOE 的長期方向或商業原則",
                        "description": "更新 joe_direction.md 或 business_principles.md 內容。",
                        "requestBody": {
                            "required": True,
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "required": ["target", "content"],
                                        "properties": {
                                            "target": {"type": "string", "enum": ["joe_direction", "business_principles"], "description": "要更新的文檔名稱"},
                                            "content": {"type": "string", "description": "完整的 Markdown 內容"}
                                        }
                                    }
                                }
                            }
                        },
                        "responses": {
                            "200": {
                                "description": "更新成功",
                                "content": {"application/json": {"schema": {"type": "object"}}}
                            }
                        }
                    }
                }
            },
            "components": {
                "securitySchemes": {
                    "BearerAuth": {
                        "type": "http",
                        "scheme": "bearer",
                        "description": "Shannie 專屬訪問金鑰"
                    }
                }
            },
            "security": [{"BearerAuth": []}]
        }
        self.send_json(200, spec)

    def handle_list_inbox(self):
        files = sorted(glob.glob(os.path.join(INBOX_DIR, "*.md")), reverse=True)
        messages = []
        for fpath in files:
            fname = os.path.basename(fpath)
            mtime = datetime.fromtimestamp(os.path.getmtime(fpath)).strftime("%Y-%m-%d %H:%M:%S")
            try:
                with open(fpath, "r", encoding="utf-8") as f:
                    content = f.read()
            except Exception:
                content = "(無法讀取)"
            messages.append({
                "id": fname,
                "filename": fname,
                "mtime": mtime,
                "content": content
            })
        self.send_json(200, {
            "success": True,
            "count": len(messages),
            "messages": messages
        })

    def handle_read_inbox(self, msg_id):
        # Path traversal guard
        safe_name = os.path.basename(msg_id)
        fpath = os.path.join(INBOX_DIR, safe_name)
        if not os.path.isfile(fpath):
            self.send_json(404, {"error": "Message Not Found", "id": msg_id})
            return
        mtime = datetime.fromtimestamp(os.path.getmtime(fpath)).strftime("%Y-%m-%d %H:%M:%S")
        with open(fpath, "r", encoding="utf-8") as f:
            content = f.read()
        self.send_json(200, {
            "success": True,
            "id": safe_name,
            "mtime": mtime,
            "content": content
        })

    def handle_list_outbox(self):
        files = sorted(glob.glob(os.path.join(OUTBOX_DIR, "*.md")), reverse=True)
        items = []
        for fpath in files:
            fname = os.path.basename(fpath)
            mtime = datetime.fromtimestamp(os.path.getmtime(fpath)).strftime("%Y-%m-%d %H:%M:%S")
            with open(fpath, "r", encoding="utf-8") as f:
                content = f.read()
            items.append({
                "id": fname,
                "mtime": mtime,
                "content": content
            })
        self.send_json(200, {
            "success": True,
            "count": len(items),
            "items": items
        })

    def handle_post_outbox(self, data):
        topic = data.get("topic", "STRATEGIC_ADVICE").strip()
        conclusion = data.get("conclusion", "").strip()
        reason = data.get("reason", "").strip()
        action_for_hq = data.get("action_for_hq", "").strip()
        task_id = data.get("task_id", "").strip()

        if not conclusion or not reason:
            self.send_json(400, {"error": "Missing fields", "message": "conclusion and reason are required"})
            return

        now = datetime.now()
        timestamp = now.strftime("%Y%m%d_%H%M%S")
        clean_topic = "".join(c for c in topic if c.isalnum() or c in ("_", "-")).strip() or "ADVICE"
        filename = f"{timestamp}_{clean_topic}.md"
        dest_path = os.path.join(OUTBOX_DIR, filename)

        md_content = f"""# 策略建議：{topic}

**發送者**：Shannie (Executive Assistant / Strategic Advisor)  
**時間**：{now.strftime('%Y-%m-%d %H:%M')}  
**對應任務**：{task_id if task_id else '主動回饋'}  

---

## 📌 核心結論 (Conclusion)
{conclusion}

---

## 💡 決策背景與商業考量 (Reason)
{reason}

---

## 🚀 給 HQ 的行動建議 (Action for HQ)
{action_for_hq if action_for_hq else '由 HQ 自行評估工程排期'}

---
**簽署**：Shannie  
**日期**：{now.strftime('%Y-%m-%d %H:%M')}
"""
        with open(dest_path, "w", encoding="utf-8") as f:
            f.write(md_content)

        # Log to task_flow.log
        try:
            with open(TASK_LOG, "a", encoding="utf-8") as f:
                f.write(f"[{now.strftime('%Y-%m-%d %H:%M:%S')}] 📬 Shannie 策略回覆已存入：{filename}\n")
        except Exception:
            pass

        self.send_json(200, {
            "success": True,
            "filename": filename,
            "path": f".taskflow/shannie/outbox/{filename}",
            "message": "策略建議已成功送達 HQ outbox"
        })

    def handle_read_context(self):
        ctx_files = {
            "joe_direction": os.path.join(CONTEXT_DIR, "joe_direction.md"),
            "business_principles": os.path.join(CONTEXT_DIR, "business_principles.md")
        }
        res = {}
        for key, p in ctx_files.items():
            if os.path.exists(p):
                with open(p, "r", encoding="utf-8") as f:
                    res[key] = f.read()
            else:
                res[key] = ""
        self.send_json(200, {
            "success": True,
            "context": res
        })

    def handle_update_context(self, data):
        target = data.get("target", "")
        content = data.get("content", "")
        if target not in ["joe_direction", "business_principles"]:
            self.send_json(400, {"error": "Invalid target", "allowed": ["joe_direction", "business_principles"]})
            return
        if not content:
            self.send_json(400, {"error": "Empty content"})
            return

        fpath = os.path.join(CONTEXT_DIR, f"{target}.md")
        with open(fpath, "w", encoding="utf-8") as f:
            f.write(content)

        self.send_json(200, {
            "success": True,
            "target": target,
            "message": f"已成功更新 {target}.md"
        })

def main():
    server_address = ("127.0.0.1", PORT)
    httpd = HTTPServer(server_address, BridgeHandler)
    sys.stderr.write(f"Shannie Taskflow Bridge listening on http://127.0.0.1:{PORT}\n")
    httpd.serve_forever()

if __name__ == "__main__":
    main()
