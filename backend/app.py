import sqlite3, time, requests, json
from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

DB_PATH = "/monitor/events.db"
ACE_STEP_URL = "http://host.docker.internal:8001"

TYPE_LABELS = {
    "zh": {
        "music":        "音樂生成",
        "design":       "圖片設計",
        "claude":       "Claude 開發",
        "orchestrator": "排程任務",
        "workflow":     "工作流",
        "cron":         "Cron 排程",
        "discord":      "Discord",
        "line":         "LINE",
    },
    "en": {
        "music":        "Music Gen",
        "design":       "Image Design",
        "claude":       "Claude Dev",
        "orchestrator": "Orchestrator",
        "workflow":     "Workflow",
        "cron":         "Cron Job",
        "discord":      "Discord",
        "line":         "LINE",
    },
}

STATUS_LABELS = {
    "zh": {"start": "執行中", "progress": "進行中", "done": "完成", "error": "失敗"},
    "en": {"start": "Running", "progress": "Progress", "done": "Done",  "error": "Error"},
}


def get_db():
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn
    except Exception:
        return None


@app.route("/api/events")
def events():
    lang = request.args.get("lang", "zh")
    limit = int(request.args.get("limit", 50))
    conn = get_db()
    if not conn:
        return jsonify([])
    # 每個 (type, name) 只顯示最新狀態
    rows = conn.execute("""
        SELECT * FROM events e1
        WHERE e1.id = (
            SELECT MAX(e2.id) FROM events e2
            WHERE e2.type = e1.type AND e2.name = e1.name
        )
        ORDER BY e1.id DESC LIMIT ?
    """, (limit,)).fetchall()
    conn.close()
    result = []
    for r in rows:
        t = r["type"]
        s = r["status"]
        result.append({
            "id":         r["id"],
            "type":       t,
            "type_label": TYPE_LABELS.get(lang, TYPE_LABELS["zh"]).get(t, t),
            "name":       r["name"],
            "status":     s,
            "status_label": STATUS_LABELS.get(lang, STATUS_LABELS["zh"]).get(s, s),
            "message":    r["message"],
            "created_at": r["created_at"],
        })
    return jsonify(result)


@app.route("/api/stats")
def stats():
    lang = request.args.get("lang", "zh")
    conn = get_db()
    if not conn:
        return jsonify({})
    rows = conn.execute("""
        SELECT type, status, COUNT(*) as cnt
        FROM events GROUP BY type, status
    """).fetchall()
    conn.close()
    data = {}
    labels = TYPE_LABELS.get(lang, TYPE_LABELS["zh"])
    for r in rows:
        t = r["type"]
        if t not in data:
            data[t] = {"label": labels.get(t, t), "done": 0, "error": 0, "running": 0}
        if r["status"] == "done":
            data[t]["done"] += r["cnt"]
        elif r["status"] == "error":
            data[t]["error"] += r["cnt"]
        elif r["status"] == "start":
            data[t]["running"] += r["cnt"]
    return jsonify(data)


@app.route("/api/active")
def active():
    lang = request.args.get("lang", "zh")
    conn = get_db()
    if not conn:
        return jsonify([])
    # 取最新狀態為 start/progress 的任務（done 後自動消失）
    since = int(time.time()) - 600
    rows = conn.execute("""
        SELECT * FROM events e1
        WHERE e1.id = (
            SELECT MAX(e2.id) FROM events e2
            WHERE e2.type = e1.type AND e2.name = e1.name
        )
        AND e1.status IN ('start', 'progress')
        AND e1.created_at > ?
        ORDER BY e1.id DESC LIMIT 10
    """, (since,)).fetchall()
    conn.close()
    labels = TYPE_LABELS.get(lang, TYPE_LABELS["zh"])
    result = []
    for r in rows:
        t = r["type"]
        result.append({
            "type":       t,
            "type_label": labels.get(t, t),
            "name":       r["name"],
            "message":    r["message"],
            "started_at": r["created_at"],
            "elapsed":    int(time.time()) - r["created_at"],
        })
    return jsonify(result)


@app.route("/api/music/status")
def music_status():
    # 讀取由 orchestrator 寫入的 ACE-Step 狀態檔
    status_file = "/monitor/acestep_status.json"
    try:
        with open(status_file) as f:
            data = json.load(f)
        # 超過 2 分鐘沒更新視為離線
        online = (time.time() - data.get("checked_at", 0)) < 120 and data.get("online", False)
        return jsonify({"online": online, "checked_at": data.get("checked_at")})
    except Exception:
        return jsonify({"online": False})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
