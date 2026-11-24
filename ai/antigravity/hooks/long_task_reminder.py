#!/usr/bin/env python3
"""Send a Feishu reminder when a long Antigravity task finishes and stays idle."""

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


def load_env_file() -> None:
    path = Path.home() / ".codex" / "codex.env"
    if not path.exists():
        return

    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip())


load_env_file()

LONG_TASK_SECONDS = int(
    os.environ.get("AGY_REMINDER_TASK_SECONDS")
    or os.environ.get("CODEX_REMINDER_TASK_SECONDS", "600")
)
REMIND_AFTER_SECONDS = int(
    os.environ.get("AGY_REMINDER_IDLE_SECONDS")
    or os.environ.get("CODEX_REMINDER_IDLE_SECONDS", "300")
)
FEISHU_WEBHOOK = os.environ.get("FEISHU_WEBHOOK", "")

STATE_ROOT = Path.home() / ".gemini" / "config" / "reminder-state"
LOG_FILE = Path.home() / ".gemini" / "config" / "reminder.log"


def log(msg: str) -> None:
    try:
        LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        with LOG_FILE.open("a", encoding="utf-8") as f:
            f.write(f"[{timestamp}] pid={os.getpid()} {msg}\n")
    except Exception:
        pass


def log_exception(prefix: str) -> None:
    log(f"{prefix}\n{traceback.format_exc()}")


def safe_id(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:24]


def conv_dir(conversation_id: str) -> Path:
    path = STATE_ROOT / safe_id(conversation_id)
    path.mkdir(parents=True, exist_ok=True)
    return path


def generation_file(conversation_id: str) -> Path:
    return conv_dir(conversation_id) / "generation"


def active_turn_file(conversation_id: str) -> Path:
    return conv_dir(conversation_id) / "active-turn.json"


def get_generation(conversation_id: str) -> int:
    try:
        return int(generation_file(conversation_id).read_text(encoding="utf-8").strip())
    except Exception:
        return 0


def bump_generation(conversation_id: str) -> int:
    new_value = get_generation(conversation_id) + 1
    generation_file(conversation_id).write_text(str(new_value), encoding="utf-8")
    return new_value


def send_feishu(message: str) -> None:
    webhook = os.environ.get("FEISHU_WEBHOOK", FEISHU_WEBHOOK)
    if not webhook:
        raise RuntimeError("FEISHU_WEBHOOK is not set")

    body = json.dumps(
        {"msg_type": "text", "content": {"text": message}},
        ensure_ascii=False,
    ).encode("utf-8")
    req = urllib.request.Request(
        webhook,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        log(f"feishu response status={resp.status}")


def handle_pre_invocation(payload: dict) -> None:
    conv_id = payload.get("conversationId")
    if not conv_id:
        return

    turn_path = active_turn_file(conv_id)
    if turn_path.exists():
        return

    bump_generation(conv_id)
    started_at = time.time()
    turn_id = f"{started_at:.6f}"
    turn_path.write_text(
        json.dumps({"turnId": turn_id, "startedAt": started_at}),
        encoding="utf-8",
    )
    log(f"turn started conversation={conv_id} turn={turn_id}")


def handle_stop(payload: dict) -> None:
    conv_id = payload.get("conversationId")
    if not conv_id:
        return

    turn_path = active_turn_file(conv_id)
    if not turn_path.exists():
        return

    try:
        turn_data = json.loads(turn_path.read_text(encoding="utf-8"))
        started_at = float(turn_data["startedAt"])
        turn_id = str(turn_data["turnId"])
    except Exception:
        log_exception(f"failed reading active turn conversation={conv_id}")
        turn_path.unlink(missing_ok=True)
        return

    turn_path.unlink(missing_ok=True)
    duration = time.time() - started_at
    log(f"turn stopped conversation={conv_id} duration={duration:.2f}s threshold={LONG_TASK_SECONDS}s")

    if duration < LONG_TASK_SECONDS:
        return

    generation = get_generation(conv_id)
    cwd = payload.get("cwd", "")
    last_input = payload.get("lastUserInput", "")[:300]

    args = [
        sys.executable,
        str(Path(__file__).resolve()),
        "--wait",
        conv_id,
        turn_id,
        str(generation),
        str(int(duration)),
        cwd,
        last_input,
    ]
    subprocess.Popen(
        args,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
        env=os.environ.copy(),
    )


def wait_and_remind() -> None:
    if len(sys.argv) < 7:
        return

    conv_id = sys.argv[2]
    turn_id = sys.argv[3]
    expected_generation = int(sys.argv[4])
    duration = int(sys.argv[5])
    cwd = sys.argv[6]
    last_input = sys.argv[7] if len(sys.argv) > 7 else ""

    time.sleep(REMIND_AFTER_SECONDS)

    if get_generation(conv_id) != expected_generation:
        log(f"reminder cancelled conversation={conv_id} turn={turn_id}")
        return

    sent_marker = conv_dir(conv_id) / f"sent-{safe_id(turn_id)}"
    if sent_marker.exists():
        return

    message = (
        "✅ Antigravity 长任务已经完成\n\n"
        f"耗时：约 {duration / 60:.1f} 分钟\n"
    )
    if cwd:
        message += f"目录：{cwd}\n"
    message += f"任务完成后 {REMIND_AFTER_SECONDS / 60:.1f} 分钟内没有检测到你的新指令。\n"
    if last_input:
        message += f"\n触发指令：\n{last_input}"

    try:
        send_feishu(message)
        sent_marker.write_text(str(time.time()), encoding="utf-8")
        bump_generation(conv_id)
    except urllib.error.HTTPError as e:
        log(f"feishu HTTP error status={e.code}")
    except Exception:
        log_exception(f"failed sending reminder conversation={conv_id}")


def main() -> None:
    STATE_ROOT.mkdir(parents=True, exist_ok=True)

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

    event = payload.get("hookEventName")
    try:
        if event == "PreInvocation":
            handle_pre_invocation(payload)
        elif event == "Stop":
            handle_stop(payload)
    except Exception:
        log_exception(f"hook handler crashed event={event}")
    finally:
        print("{}")


if __name__ == "__main__":
    main()
