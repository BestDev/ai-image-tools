#!/usr/bin/env python3
"""
Z-Image Tools - Web UI
Flask 기반 통합 웹 인터페이스

실행: python3 web_ui.py [--port 7860]
접속: http://localhost:7860
"""
import sys
import os
from pathlib import Path

_VENV_DIR = Path(__file__).resolve().parent / "venv-prompt"
if _VENV_DIR.exists() and Path(sys.prefix) != _VENV_DIR:
    os.execv(str(_VENV_DIR / "bin" / "python3"),
             [str(_VENV_DIR / "bin" / "python3")] + sys.argv)

import argparse
import io
import json
import queue
import re
import socket
import subprocess
import threading
import time
import uuid
from datetime import datetime

import psutil
from flask import Flask, Response, jsonify, request, send_file

app = Flask(__name__)
BASE_DIR = Path(__file__).resolve().parent
VENV_PY = str(_VENV_DIR / "bin" / "python3")

IMAGE_EXT = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tiff", ".tif", ".heic", ".heif"}
HEIC_EXT  = {".heic", ".heif"}

runs: dict = {}
runs_lock = threading.Lock()
_current_port = 7860

# 배치 큐
job_queue: list = []
queue_lock = threading.Lock()


def _queue_worker():
    """배치 큐 순차 처리 스레드"""
    while True:
        job = None
        # 직접 실행(/api/run) 포함, 현재 실행 중인 작업이 있으면 대기
        with runs_lock:
            any_active = any(not r["finished"] for r in runs.values())
        if not any_active:
            with queue_lock:
                # 큐 내에서도 이미 running인 항목이 없을 때만 새 작업 시작
                queue_busy = any(j["status"] == "running" for j in job_queue)
                if not queue_busy:
                    for j in job_queue:
                        if j["status"] == "pending":
                            j["status"] = "running"
                            job = j
                            break
        if job is None:
            time.sleep(1)
            continue
        try:
            cmd, total, output_dir = build_cmd(job["tool"], job["params"])
            run_id = str(uuid.uuid4())[:8]
            with runs_lock:
                runs[run_id] = {
                    "run_id": run_id, "tool": job["tool"],
                    "output_dir": output_dir,
                    "started_at": time.time(), "finished": False,
                    "process": None, "queue": queue.Queue(),
                    "total": total, "current_file": "",
                }
            with queue_lock:
                job["run_id"] = run_id
                job["output_dir"] = output_dir
            run_process(run_id, cmd, total)   # blocking until done
            with runs_lock:
                proc = runs[run_id].get("process")
                rc = proc.returncode if proc else -1
            with queue_lock:
                job["status"] = "done" if rc == 0 else "error"
        except Exception as e:
            with queue_lock:
                job["status"] = "error"
                job["error"] = str(e)


threading.Thread(target=_queue_worker, daemon=True).start()


# ---------------------------------------------------------------------------
# 시스템 통계
# ---------------------------------------------------------------------------

def gpu_stats() -> dict:
    try:
        r = subprocess.run(
            ["nvidia-smi",
             "--query-gpu=utilization.gpu,memory.used,memory.free,memory.total",
             "--format=csv,noheader,nounits"],
            capture_output=True, text=True, timeout=3)
        if r.returncode == 0:
            p = [x.strip() for x in r.stdout.strip().split(",")]
            if len(p) >= 4:
                return {
                    "gpu_pct":    int(p[0]),
                    "vram_used":  int(p[1]),
                    "vram_free":  int(p[2]),
                    "vram_total": int(p[3]),
                }
    except Exception:
        pass
    return {}


def ram_stats() -> dict:
    vm = psutil.virtual_memory()
    return {"ram_used": vm.used >> 20, "ram_total": vm.total >> 20}


# ---------------------------------------------------------------------------
# 커맨드 빌더
# ---------------------------------------------------------------------------

def build_cmd(tool: str, params: dict):
    """Returns (cmd, total_images, output_dir)"""

    if tool == "prompt":
        folder = params.get("input_folder", "image/dataset")
        path = (BASE_DIR / folder).resolve()

        # UI 파라미터 → method 번호 매핑
        # model: qwen3vl | qwen35 | huihui_vl | huihui_35 | joycaption
        # two_pass: bool (JoyCaption → 선택 모델 정제)
        model    = params.get("model", "qwen3vl")
        two_pass = bool(params.get("two_pass", False))
        METHOD_MAP = {
            ("joycaption",    False): 1,
            ("qwen3vl",       False): 2,
            ("qwen35",        False): 3,
            ("qwen3vl",       True):  4,
            ("qwen35",        True):  5,
            ("huihui_vl",     False): 6,
            ("huihui_35",     False): 7,
            ("huihui_vl",     True):  8,
            ("huihui_35",     True):  9,
            ("gemini3flash",  False): 10,
            ("gemini31lite",  False): 11,
        }
        method = METHOD_MAP.get((model, two_pass), 2)

        ts = datetime.now().strftime("%Y-%m-%d-%H%M%S")
        output_dir = params.get("output_dir") or f"output/{ts}-m{method}"

        accumulate = bool(params.get("accumulate", False))

        # 기존 JoyCaption 파일 사용: output_dir에 복사 후 --accumulate
        if two_pass and params.get("raw_source") == "existing":
            raw_path = params.get("raw_path", "").strip()
            if raw_path:
                import shutil
                src = Path(raw_path) if Path(raw_path).is_absolute() else (BASE_DIR / raw_path)
                if src.exists():
                    out_path = BASE_DIR / output_dir
                    out_path.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(str(src), str(out_path / "prompts_raw.txt"))
                    accumulate = True

        cmd = [
            VENV_PY, "-u", str(BASE_DIR / "scripts" / "prompt_generator_v2.py"),
            str(path),
            "--output-dir", output_dir,
            "--method", str(method),
            "--quant", params.get("quant", "bf16"),
            "--lang", params.get("lang", "en"),
        ]
        if accumulate:
            cmd.append("--accumulate")
        if bool(params.get("uncensored", False)):
            cmd.append("--uncensored")
        gemini_key = params.get("gemini_key", "").strip()
        if gemini_key:
            cmd += ["--gemini-key", gemini_key]

        imgs = (len([p for p in path.iterdir() if p.suffix.lower() in IMAGE_EXT])
                if path.is_dir() else 1)
        total_steps = imgs * 2 if method in (4, 5, 8, 9) else imgs
        return cmd, total_steps, output_dir

    elif tool == "heic":
        folder = params.get("input_dir", "image/dataset")
        path = (BASE_DIR / folder).resolve()
        cmd = [
            VENV_PY, "-u", str(BASE_DIR / "scripts" / "heic_to_jpeg.py"), str(path),
            "--quality", str(params.get("quality", 95)),
        ]
        if params.get("keep"):      cmd.append("--keep")
        if params.get("recursive"): cmd.append("--recursive")
        if params.get("dry_run"):   cmd.append("--dry-run")
        glob_fn = path.rglob if params.get("recursive") else path.iterdir
        imgs = (len([p for p in glob_fn("*") if p.suffix.lower() in HEIC_EXT])
                if path.is_dir() else 1)
        return cmd, imgs, str(path)

    elif tool == "classifier":
        folder = params.get("input_dir", "image/dataset")
        path = (BASE_DIR / folder).resolve()
        by = params.get("by", "style")
        cmd = [VENV_PY, "-u", str(BASE_DIR / "scripts" / "image_classifier.py"), str(path), "--by", by]
        if params.get("file_op") == "move":    cmd.append("--move")
        elif params.get("file_op") == "copy":  cmd.append("--copy")
        if params.get("output_dir"): cmd += ["--output-dir", params["output_dir"]]
        if by == "style":
            cmd += ["--model", params.get("model", "openai/clip-vit-large-patch14")]
            if params.get("verbose"): cmd.append("--verbose")
        elif by == "background":
            cmd += ["--bg-threshold", str(params.get("bg_threshold", 15.0))]
        imgs = (len([p for p in path.iterdir() if p.suffix.lower() in IMAGE_EXT])
                if path.is_dir() else 1)
        return cmd, imgs, str(path)

    elif tool == "clothing":
        mode = params.get("mode", "spacy")
        inp  = params.get("input_path", "prompts")
        out  = params.get("output_path", "output")
        cmd = [
            VENV_PY, "-u", str(BASE_DIR / "scripts" / "extract_clothing.py"),
            "--mode", mode,
            "--input", inp,
            "--output", out,
        ]
        if mode == "ollama":
            cmd += ["--model",      params.get("ollama_model", "huihui_ai/qwen3.5-abliterated:35b")]
            cmd += ["--batch",      str(params.get("ollama_batch", 5))]
            cmd += ["--ollama-url", params.get("ollama_url", "http://host.docker.internal:11434")]
        return cmd, 0, out

    elif tool == "gemini_batch":
        folder = params.get("input_dir", "image/dataset")
        path = (BASE_DIR / folder).resolve()
        GEMINI_BATCH_EXT = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tiff", ".tif"}

        output_dir = (params.get("output_dir") or "").strip()
        if not output_dir:
            ts = datetime.now().strftime("%Y-%m-%d-%H%M%S")
            output_dir = f"output/{ts}-gemini"
        cmd = [
            VENV_PY, "-u", str(BASE_DIR / "scripts" / "gemini_batch.py"), str(path),
            "-o", output_dir,
        ]

        cmd += [
            "--lang",         params.get("lang", "en"),
            "-m",             params.get("model", "flash"),
            "--delay",        str(params.get("delay", 3.0)),
            "--timeout",      str(params.get("timeout", 120)),
            "--output-mode",  params.get("output_mode", "both"),
            "--reset-every",  str(params.get("reset_every", 100)),
        ]
        collect_file = params.get("collect_file", "prompts.txt")
        if collect_file is not None:
            cmd += ["--collect-file", str(collect_file)]
        if params.get("skip_existing"): cmd.append("--skip-existing")
        if params.get("no_session"):    cmd.append("--no-session")
        if params.get("dry_run"):       cmd.append("--dry-run")

        imgs = (len([p for p in path.iterdir() if p.suffix.lower() in GEMINI_BATCH_EXT])
                if path.is_dir() else 1)
        return cmd, imgs, output_dir

    raise ValueError(f"알 수 없는 tool: {tool}")


# ---------------------------------------------------------------------------
# 프로세스 실행 (백그라운드 스레드)
# ---------------------------------------------------------------------------

RE_IMG_START      = re.compile(r"^\[(\d+)/(\d+)\]\s+(.+)$")
RE_IMG_DONE       = re.compile(r"완료\s+\(([0-9.]+)초\)\s+\|\s+(\d+)단어")
RE_IMG_DONE_NOWD  = re.compile(r"^\s+완료\s+\(([0-9.]+)초\)\s*$")   # Pass 1: 단어 수 없음
RE_HEIC_DONE  = re.compile(r"[✓→]\s|변환\s+완료|저장")
RE_CLASS_DONE = re.compile(r"→\s+\w+|분류\s+완료")
RE_HF_DOWN    = re.compile(r'(\d+)%\|')
RE_GEMINI_DONE = re.compile(r"^\[\s*(\d+)/(\d+)\]\s+(OK|FAIL|SKIP)\s+(\S+)")


def run_process(run_id: str, cmd: list, total: int):
    state = runs[run_id]
    env = {**os.environ, "TORCHINDUCTOR_DISABLED": "1", "TORCH_COMPILE_DISABLE": "1"}
    timings: list[float] = []

    def emit(t, d):
        state["queue"].put({"type": t, "data": d})

    try:
        proc = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            text=True, bufsize=1, env=env, cwd=str(BASE_DIR))
        state["process"] = proc

        # 주기적 시스템 통계
        stop_evt = threading.Event()
        def _poll():
            while not stop_evt.wait(2.0):
                emit("stats", {**gpu_stats(), **ram_stats()})
        threading.Thread(target=_poll, daemon=True).start()

        generic_done = 0  # 상세 파싱 불가 도구용 카운터
        pass_offset  = 0  # 2-pass 방식: Pass 2 시작 시 Pass 1 완료 수 보정
        _gem_prev_time = [time.time()]  # gemini_batch: 이전 이미지 완료 시각

        for line in proc.stdout:
            line = line.rstrip()
            # \r 인플레이스 덮어쓰기 처리 (gemini_batch 등)
            if '\r' in line:
                line = line.rsplit('\r', 1)[-1]
            emit("log", {"text": line})

            # 프롬프트 생성: [N/M] filename
            m = RE_IMG_START.match(line.strip())
            if m:
                cur, _tot, fname = int(m.group(1)), int(m.group(2)), m.group(3)
                # 새 패스 감지: cur가 1로 리셋되고 이미 완료된 이미지가 있으면 패스 오프셋 갱신
                if cur == 1 and timings:
                    pass_offset = len(timings)
                state["current_file"] = fname
                effective = pass_offset + cur - 1
                avg = sum(timings) / len(timings) if timings else None
                emit("progress", {
                    "current": effective, "total": total, "filename": fname,
                    "avg_sec": avg,
                    "eta_sec": (total - effective) * avg if avg else None,
                })
                continue

            # 프롬프트 생성: 완료 줄 (단어 수 있음 — Pass 2 / 단일 패스)
            m2 = RE_IMG_DONE.search(line)
            if m2:
                elapsed = float(m2.group(1))
                timings.append(elapsed)
                done = len(timings)
                avg  = sum(timings) / done
                emit("progress", {
                    "current": done, "total": total,
                    "filename": state.get("current_file", ""),
                    "elapsed_last": elapsed, "avg_sec": avg,
                    "eta_sec": max(0, (total - done) * avg),
                })
                continue

            # 프롬프트 생성: 완료 줄 (단어 수 없음 — Pass 1 JoyCaption)
            m2b = RE_IMG_DONE_NOWD.match(line)
            if m2b:
                elapsed = float(m2b.group(1))
                timings.append(elapsed)
                done = len(timings)
                avg  = sum(timings) / done
                emit("progress", {
                    "current": done, "total": total,
                    "filename": state.get("current_file", ""),
                    "elapsed_last": elapsed, "avg_sec": avg,
                    "eta_sec": max(0, (total - done) * avg),
                })
                continue

            # HuggingFace 다운로드 진행률 (log도 함께 emit)
            m3 = RE_HF_DOWN.search(line)
            if m3 and any(k in line for k in ('Fetching', 'Downloading', '.safetensors', '.bin', '.json', 'model')):
                pct = int(m3.group(1))
                emit("download", {"pct": pct, "label": line.strip()[:100]})

            # gemini_batch 진행 파싱
            mg = RE_GEMINI_DONE.match(line)
            if mg and state.get("tool") == "gemini_batch":
                cur = int(mg.group(1))
                tot_line = int(mg.group(2))
                status = mg.group(3)
                fname = mg.group(4)
                state["current_file"] = fname
                if status in ("OK", "FAIL"):
                    now = time.time()
                    elapsed = now - _gem_prev_time[0]
                    _gem_prev_time[0] = now
                    generic_done += 1
                    eff_total = total or tot_line
                    avg = (now - state["started_at"]) / generic_done
                    emit("progress", {
                        "current": cur, "total": eff_total, "filename": fname,
                        "elapsed_last": round(elapsed, 1), "avg_sec": round(avg, 1),
                        "eta_sec": max(0, (eff_total - cur) * avg),
                    })
                elif status == "SKIP":
                    emit("progress", {"current": cur, "total": total or tot_line, "filename": fname})
                continue

            # 기타 도구: 단순 카운팅
            if RE_HEIC_DONE.search(line) or RE_CLASS_DONE.search(line):
                generic_done += 1
                if total > 0:
                    emit("progress", {"current": generic_done, "total": total,
                                      "filename": line[:60]})

        proc.wait()
        stop_evt.set()
        state["finished"] = True
        success = proc.returncode == 0
        emit("done", {
            "success": success,
            "output_dir": state["output_dir"],
            "completed": len(timings) or generic_done,
            "total": total,
            **({"returncode": proc.returncode} if not success else {}),
        })

    except Exception as e:
        state["finished"] = True
        emit("done", {"success": False, "error": str(e)})


# ---------------------------------------------------------------------------
# Flask 라우트
# ---------------------------------------------------------------------------

@app.route("/")
def index():
    return send_file(BASE_DIR / "html" / "web_ui.html")


@app.route("/api/scan")
def scan_folder():
    """폴더 내 파일 수 스캔"""
    folder   = request.args.get("folder", "")
    ext_type = request.args.get("type", "image")   # image | heic | txt
    if not folder:
        return jsonify({"count": 0, "exists": False})
    path = (BASE_DIR / folder).resolve()
    if not path.exists():
        return jsonify({"count": 0, "exists": False})
    if path.is_file():
        return jsonify({"count": 1, "exists": True})
    if ext_type == "heic":
        exts = HEIC_EXT
    elif ext_type == "txt":
        files = sorted(p.name for p in path.iterdir() if p.suffix == ".txt")
        return jsonify({"count": len(files), "exists": True, "sample": files[:5]})
    else:
        exts = IMAGE_EXT
    imgs = sorted(p.name for p in path.iterdir() if p.suffix.lower() in exts)
    return jsonify({"count": len(imgs), "exists": True, "sample": imgs[:5]})


@app.route("/api/run", methods=["POST"])
def start_run():
    data = request.json or {}
    tool = data.get("tool", "prompt")
    try:
        cmd, total, output_dir = build_cmd(tool, data)
    except Exception as e:
        return jsonify({"error": str(e)}), 400

    run_id = str(uuid.uuid4())[:8]
    with runs_lock:
        runs[run_id] = {
            "run_id": run_id, "tool": tool, "output_dir": output_dir,
            "started_at": time.time(), "finished": False,
            "process": None, "queue": queue.Queue(),
            "total": total, "current_file": "",
        }
    threading.Thread(target=run_process, args=(run_id, cmd, total), daemon=True).start()
    return jsonify({"run_id": run_id, "output_dir": output_dir, "total": total})


@app.route("/api/stream/<run_id>")
def stream(run_id):
    if run_id not in runs:
        return jsonify({"error": "not found"}), 404
    state = runs[run_id]

    def generate():
        # 시작 즉시 초기 stats 전송
        yield f"data: {json.dumps({'type': 'stats', 'data': {**gpu_stats(), **ram_stats()}})}\n\n"
        while True:
            try:
                ev = state["queue"].get(timeout=1.0)
                yield f"data: {json.dumps(ev)}\n\n"
                if ev["type"] == "done":
                    break
            except queue.Empty:
                if state["finished"]:
                    break
                yield ": keepalive\n\n"

    return Response(generate(), mimetype="text/event-stream",
                    headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


@app.route("/api/stop/<run_id>", methods=["POST"])
def stop_run(run_id):
    state = runs.get(run_id)
    if not state:
        return jsonify({"error": "not found"}), 404
    proc = state.get("process")
    if proc and proc.poll() is None:
        proc.terminate()
        time.sleep(0.3)
        if proc.poll() is None:
            proc.kill()
    state["finished"] = True
    return jsonify({"ok": True})


@app.route("/api/history")
def get_history():
    logs_dir = BASE_DIR / "output"
    if not logs_dir.exists():
        return jsonify({"runs": []})
    result = []
    for d in sorted(logs_dir.iterdir(), reverse=True):
        if not d.is_dir():
            continue
        pt = d / "prompts.txt"
        count = 0
        if pt.exists():
            with open(pt) as f:
                count = sum(1 for ln in f if ln.strip())
        result.append({"name": d.name, "has_prompts": pt.exists(), "count": count})
    return jsonify({"runs": result[:50]})


@app.route("/api/ls")
def list_dir():
    """폴더 브라우저용 디렉토리 목록"""
    path_str = request.args.get("path", "")
    if not path_str:
        path = BASE_DIR
    else:
        p = Path(path_str)
        path = p.resolve() if p.is_absolute() else (BASE_DIR / path_str).resolve()

    if not path.exists() or not path.is_dir():
        return jsonify({"error": "not found", "dirs": []}), 404

    try:
        rel = str(path.relative_to(BASE_DIR))
        if rel == ".":
            rel = ""
    except ValueError:
        rel = str(path)

    parent = None
    if path != BASE_DIR:
        try:
            parent_rel = str(path.parent.relative_to(BASE_DIR))
            parent = "" if parent_rel == "." else parent_rel
        except ValueError:
            pass

    dirs = []
    try:
        for d in sorted(path.iterdir(), key=lambda x: x.name.lower()):
            if d.is_dir() and not d.name.startswith("."):
                try:
                    dir_rel = str(d.relative_to(BASE_DIR))
                except ValueError:
                    dir_rel = str(d)
                dirs.append({"name": d.name, "path": dir_rel})
    except PermissionError:
        pass

    return jsonify({"path": rel, "parent": parent, "dirs": dirs})


@app.route("/api/read")
def read_file():
    """텍스트 파일 내용 반환 (history viewer용)"""
    path_str = request.args.get("path", "")
    if not path_str:
        return jsonify({"error": "path required"}), 400
    path = (BASE_DIR / path_str).resolve()
    # 보안: BASE_DIR 하위만 허용
    try:
        path.relative_to(BASE_DIR)
    except ValueError:
        return jsonify({"error": "접근 불가"}), 403
    if not path.exists() or not path.is_file():
        return jsonify({"error": "파일 없음"}), 404
    with open(path, encoding="utf-8") as f:
        lines = [ln.rstrip() for ln in f]
    return jsonify({"lines": lines, "count": len(lines)})


@app.route("/api/image")
def serve_image():
    """이미지 파일 반환 (썸네일 지원)"""
    path_str = request.args.get("path", "")
    thumb = request.args.get("thumb", "0") == "1"
    if not path_str:
        return jsonify({"error": "path required"}), 400
    path = (BASE_DIR / path_str).resolve()
    try:
        path.relative_to(BASE_DIR)
    except ValueError:
        return jsonify({"error": "접근 불가"}), 403
    if not path.exists() or path.suffix.lower() not in IMAGE_EXT:
        return jsonify({"error": "이미지 없음"}), 404
    if thumb:
        try:
            from PIL import Image as PILImage
            img = PILImage.open(path)
            img.thumbnail((160, 160))
            buf = io.BytesIO()
            fmt = "JPEG" if path.suffix.lower() in {".jpg", ".jpeg", ".heic", ".heif"} else "PNG"
            if img.mode in ("RGBA", "P") and fmt == "JPEG":
                img = img.convert("RGB")
            img.save(buf, format=fmt, quality=80)
            buf.seek(0)
            mime = "image/jpeg" if fmt == "JPEG" else "image/png"
            return Response(buf.read(), mimetype=mime)
        except Exception:
            pass
    return send_file(path)


@app.route("/api/images-list")
def images_list():
    """폴더 내 이미지 목록 반환"""
    folder = request.args.get("folder", "")
    if not folder:
        return jsonify({"images": [], "folder": folder})
    path = (BASE_DIR / folder).resolve()
    if not path.exists() or not path.is_dir():
        return jsonify({"images": [], "folder": folder})
    imgs = sorted(p.name for p in path.iterdir() if p.suffix.lower() in IMAGE_EXT)
    return jsonify({"images": imgs, "folder": folder})


@app.route("/api/info")
def get_info():
    """WSL IP 및 포트 정보 반환 (eth0 우선)"""
    ip = "127.0.0.1"
    try:
        # WSL2의 실제 eth0 IP 우선 (172.x 또는 192.168.x 대역)
        r = subprocess.run(["ip", "addr", "show", "eth0"],
                           capture_output=True, text=True, timeout=2)
        if r.returncode == 0:
            import re as _re
            m = _re.search(r'inet (\d+\.\d+\.\d+\.\d+)', r.stdout)
            if m:
                ip = m.group(1)
        if ip == "127.0.0.1":
            ip = socket.gethostbyname(socket.gethostname())
    except Exception:
        pass
    return jsonify({"wsl_ip": ip, "port": _current_port})


@app.route("/api/queue/add", methods=["POST"])
def queue_add():
    data = request.json or {}
    tool = data.get("tool", "prompt")
    try:
        build_cmd(tool, data)   # validate params
    except Exception as e:
        return jsonify({"error": str(e)}), 400
    job_id = str(uuid.uuid4())[:8]
    with queue_lock:
        job_queue.append({
            "id": job_id, "tool": tool, "params": data,
            "status": "pending", "added_at": time.time(),
            "run_id": None, "output_dir": None,
        })
    return jsonify({"job_id": job_id})


@app.route("/api/queue/list")
def queue_list_route():
    with queue_lock:
        return jsonify({"jobs": list(job_queue)})


@app.route("/api/queue/clear", methods=["POST"])
def queue_clear():
    with queue_lock:
        job_queue[:] = [j for j in job_queue if j["status"] == "running"]
    return jsonify({"ok": True})


@app.route("/api/queue/remove/<job_id>", methods=["POST"])
def queue_remove(job_id):
    with queue_lock:
        for j in job_queue:
            if j["id"] == job_id and j["status"] == "pending":
                j["status"] = "cancelled"
                break
    return jsonify({"ok": True})


# ---------------------------------------------------------------------------
# 엔트리포인트
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    p = argparse.ArgumentParser(description="Z-Image Tools Web UI")
    p.add_argument("--port", type=int, default=7860)
    p.add_argument("--host", default="0.0.0.0")
    a = p.parse_args()
    _current_port = a.port

    print(f"\n{'='*40}")
    print(f"  Z-Image Tools Web UI")
    print(f"  http://localhost:{a.port}")
    print(f"{'='*40}\n")

    try:
        import webbrowser
        threading.Timer(1.2, lambda: webbrowser.open(f"http://localhost:{a.port}")).start()
    except Exception:
        pass

    app.run(host=a.host, port=a.port, threaded=True, debug=False)
