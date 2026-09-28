#!/usr/bin/env python3

import hashlib
import json
import os
import subprocess
import sys
import time
import traceback
import urllib.error
import urllib.request
from pathlib import Path


# ============================================================
# 配置
# ============================================================

def load_codex_env():
    path = Path.home() / ".codex" / "codex.env"
    if not path.exists():
        return

    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip())


load_codex_env()

LONG_TASK_SECONDS = int(
    os.environ.get("CODEX_REMINDER_TASK_SECONDS", "600")
)

REMIND_AFTER_SECONDS = int(
    os.environ.get("CODEX_REMINDER_IDLE_SECONDS", "300")
)

FEISHU_WEBHOOK = os.environ.get("FEISHU_WEBHOOK", "")

STATE_ROOT = Path.home() / ".codex" / "reminder-state"
LOG_FILE = Path.home() / ".codex" / "reminder.log"


# ============================================================
# 日志
# ============================================================

def log(msg: str):
    try:
        LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")

        with LOG_FILE.open("a", encoding="utf-8") as f:
            f.write(f"[{timestamp}] pid={os.getpid()} {msg}\n")
            f.flush()
    except Exception:
        pass


def log_exception(prefix: str):
    log(
        f"{prefix}\n"
        f"{traceback.format_exc()}"
    )


# ============================================================
# 状态管理
# ============================================================

def safe_id(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:24]


def session_dir(session_id: str) -> Path:
    path = STATE_ROOT / safe_id(session_id)
    path.mkdir(parents=True, exist_ok=True)
    return path


def generation_file(session_id: str) -> Path:
    return session_dir(session_id) / "generation"


def start_file(session_id: str, turn_id: str) -> Path:
    return session_dir(session_id) / f"turn-{safe_id(turn_id)}.start"


def sent_file(session_id: str, turn_id: str) -> Path:
    return session_dir(session_id) / f"turn-{safe_id(turn_id)}.sent"


def get_generation(session_id: str) -> int:
    path = generation_file(session_id)

    try:
        return int(path.read_text(encoding="utf-8").strip())
    except Exception:
        return 0


def bump_generation(session_id: str) -> int:
    current = get_generation(session_id)
    new_value = current + 1

    generation_file(session_id).write_text(
        str(new_value),
        encoding="utf-8",
    )

    log(
        f"generation bumped "
        f"session={session_id} "
        f"{current}->{new_value}"
    )

    return new_value


# ============================================================
# 飞书
# ============================================================

def send_feishu(message: str):
    webhook = os.environ.get("FEISHU_WEBHOOK", FEISHU_WEBHOOK)

    if not webhook:
        raise RuntimeError(
            "FEISHU_WEBHOOK is not set"
        )

    body = json.dumps(
        {
            "msg_type": "text",
            "content": {
                "text": message
            },
        },
        ensure_ascii=False,
    ).encode("utf-8")

    req = urllib.request.Request(
        webhook,
        data=body,
        headers={
            "Content-Type": "application/json",
        },
        method="POST",
    )

    log("sending feishu request")

    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            response_body = resp.read().decode(
                "utf-8",
                errors="replace",
            )

            log(
                f"feishu response "
                f"status={resp.status} "
                f"body={response_body}"
            )

    except urllib.error.HTTPError as e:
        body = e.read().decode(
            "utf-8",
            errors="replace",
        )

        log(
            f"feishu HTTP error "
            f"status={e.code} "
            f"body={body}"
        )

        raise

    except Exception:
        log_exception("feishu request failed")
        raise


# ============================================================
# UserPromptSubmit
# ============================================================

def handle_user_prompt(payload: dict):
    session_id = payload.get("session_id")
    turn_id = payload.get("turn_id")

    if not session_id or not turn_id:
        log(
            f"UserPromptSubmit missing ids "
            f"payload={payload}"
        )
        return

    prompt = payload.get("prompt", "")
    cwd = payload.get("cwd", "")

    log(
        f"UserPromptSubmit "
        f"session={session_id} "
        f"turn={turn_id} "
        f"cwd={cwd} "
        f"prompt={prompt[:200]!r}"
    )

    # 新用户输入意味着：
    # 同 session 之前任何尚未触发的 reminder 都失效。
    bump_generation(session_id)

    started_at = time.time()

    start_file(session_id, turn_id).write_text(
        str(started_at),
        encoding="utf-8",
    )

    log(
        f"turn start recorded "
        f"session={session_id} "
        f"turn={turn_id} "
        f"timestamp={started_at}"
    )


# ============================================================
# Stop
# ============================================================

def handle_stop(payload: dict):
    session_id = payload.get("session_id")
    turn_id = payload.get("turn_id")

    if not session_id or not turn_id:
        log(
            f"Stop missing ids "
            f"payload={payload}"
        )
        return

    cwd = payload.get("cwd", "")
    last_message = (
        payload.get("last_assistant_message")
        or ""
    )

    log(
        f"Stop "
        f"session={session_id} "
        f"turn={turn_id} "
        f"cwd={cwd}"
    )

    sf = start_file(session_id, turn_id)

    if not sf.exists():
        log(
            f"no start file; ignoring Stop "
            f"session={session_id} "
            f"turn={turn_id} "
            f"path={sf}"
        )
        return

    try:
        started_at = float(
            sf.read_text(encoding="utf-8").strip()
        )
    except Exception:
        log_exception(
            f"failed reading start file "
            f"session={session_id} "
            f"turn={turn_id}"
        )
        return

    duration = time.time() - started_at

    log(
        f"task duration "
        f"session={session_id} "
        f"turn={turn_id} "
        f"duration={duration:.2f}s "
        f"threshold={LONG_TASK_SECONDS}s"
    )

    if duration < LONG_TASK_SECONDS:
        log(
            f"short task ignored "
            f"session={session_id} "
            f"turn={turn_id}"
        )
        return

    # 防止同一个 turn 的 Stop 重复触发后重复提醒。
    sf_sent = sent_file(session_id, turn_id)

    if sf_sent.exists():
        log(
            f"reminder already sent/scheduled "
            f"session={session_id} "
            f"turn={turn_id}"
        )
        return

    generation = get_generation(session_id)

    log(
        f"scheduling reminder "
        f"session={session_id} "
        f"turn={turn_id} "
        f"generation={generation} "
        f"wait={REMIND_AFTER_SECONDS}s"
    )

    args = [
        sys.executable,
        str(Path(__file__).resolve()),
        "--wait",
        session_id,
        turn_id,
        str(generation),
        str(int(duration)),
        cwd,
        last_message[:1000],
    ]

    try:
        proc = subprocess.Popen(
            args,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
            env=os.environ.copy(),
        )

        log(
            f"waiter spawned "
            f"pid={proc.pid} "
            f"session={session_id} "
            f"turn={turn_id}"
        )

    except Exception:
        log_exception(
            f"failed spawning waiter "
            f"session={session_id} "
            f"turn={turn_id}"
        )


# ============================================================
# 后台 waiter
# ============================================================

def wait_and_remind():
    if len(sys.argv) < 7:
        log(
            f"invalid --wait args: "
            f"{sys.argv}"
        )
        return

    session_id = sys.argv[2]
    turn_id = sys.argv[3]
    expected_generation = int(sys.argv[4])
    duration = int(sys.argv[5])
    cwd = sys.argv[6]

    last_message = (
        sys.argv[7]
        if len(sys.argv) > 7
        else ""
    )

    log(
        f"waiter started "
        f"session={session_id} "
        f"turn={turn_id} "
        f"expected_generation={expected_generation} "
        f"sleep={REMIND_AFTER_SECONDS}s"
    )

    time.sleep(REMIND_AFTER_SECONDS)

    current_generation = get_generation(session_id)

    log(
        f"waiter woke "
        f"session={session_id} "
        f"turn={turn_id} "
        f"expected_generation={expected_generation} "
        f"current_generation={current_generation}"
    )

    # 用户期间发过新消息。
    if current_generation != expected_generation:
        log(
            f"reminder cancelled due to new prompt "
            f"session={session_id} "
            f"turn={turn_id} "
            f"{expected_generation}->{current_generation}"
        )
        return

    sf_sent = sent_file(session_id, turn_id)

    # 双重保险，确保最多发送一次。
    if sf_sent.exists():
        log(
            f"reminder already sent, skipping "
            f"session={session_id} "
            f"turn={turn_id}"
        )
        return

    duration_minutes = duration / 60

    message = (
        "✅ Codex 长任务已经完成\n\n"
        f"耗时：约 {duration_minutes:.1f} 分钟\n"
    )

    if cwd:
        message += f"目录：{cwd}\n"

    message += (
        f"任务完成后 {REMIND_AFTER_SECONDS / 60:.1f} 分钟内"
        "没有检测到你的新指令。\n"
    )

    if last_message:
        message += (
            "\nCodex 最后回复：\n"
            f"{last_message}"
        )

    try:
        log(
            f"about to send reminder "
            f"session={session_id} "
            f"turn={turn_id}"
        )

        send_feishu(message)

        # 标记发送成功。
        sf_sent.write_text(
            str(time.time()),
            encoding="utf-8",
        )

        log(
            f"reminder sent successfully "
            f"session={session_id} "
            f"turn={turn_id}"
        )

        # 使所有同 generation 的残余 waiter 自动失效。
        bump_generation(session_id)

    except Exception:
        log_exception(
            f"failed to send reminder "
            f"session={session_id} "
            f"turn={turn_id}"
        )


# ============================================================
# 主入口
# ============================================================

def main():
    STATE_ROOT.mkdir(
        parents=True,
        exist_ok=True,
    )

    log(
        f"script invoked "
        f"argv={sys.argv} "
        f"task_threshold={LONG_TASK_SECONDS}s "
        f"idle_threshold={REMIND_AFTER_SECONDS}s "
        f"feishu_configured={bool(os.environ.get('FEISHU_WEBHOOK', FEISHU_WEBHOOK))}"
    )

    if len(sys.argv) > 1 and sys.argv[1] == "--wait":
        try:
            wait_and_remind()
        except Exception:
            log_exception("waiter crashed")
        return

    try:
        payload = json.load(sys.stdin)
    except Exception:
        log_exception("failed reading hook JSON from stdin")
        return

    event = payload.get("hook_event_name")

    log(
        f"hook event received "
        f"event={event}"
    )

    try:
        if event == "UserPromptSubmit":
            handle_user_prompt(payload)

        elif event == "Stop":
            handle_stop(payload)

        else:
            log(
                f"unknown hook event ignored "
                f"event={event} "
                f"payload={payload}"
            )

    except Exception:
        log_exception(
            f"hook handler crashed "
            f"event={event}"
        )


if __name__ == "__main__":
    main()
