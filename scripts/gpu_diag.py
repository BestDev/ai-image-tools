#!/usr/bin/env python3
import ctypes
import json
import os
import platform
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
VENV_CLASSIFIER = ROOT.parent / "venv-classifier" / "bin" / "python"
VENV_PROMPT = ROOT.parent / "venv-prompt" / "bin" / "python"


def run(cmd):
    proc = subprocess.run(cmd, text=True, capture_output=True)
    return {
        "cmd": cmd,
        "returncode": proc.returncode,
        "stdout": proc.stdout.strip(),
        "stderr": proc.stderr.strip(),
    }


def cuinit_status():
    try:
        lib = ctypes.CDLL("/usr/lib/wsl/lib/libcuda.so.1")
        cu_init = lib.cuInit
        cu_init.argtypes = [ctypes.c_uint]
        cu_init.restype = ctypes.c_int
        return {"ok": True, "cuInit": cu_init(0)}
    except Exception as exc:
        return {"ok": False, "error": repr(exc)}


def python_cuda_status(python_bin):
    code = r"""
import ctypes
import json
out = {}
try:
    lib = ctypes.CDLL("/usr/lib/wsl/lib/libcuda.so.1")
    cuInit = lib.cuInit
    cuInit.argtypes = [ctypes.c_uint]
    cuInit.restype = ctypes.c_int
    out["cuInit"] = cuInit(0)
except Exception as e:
    out["cuInit_error"] = repr(e)

try:
    import torch
    out["torch"] = torch.__version__
    out["torch_cuda"] = torch.version.cuda
    out["cuda_available"] = torch.cuda.is_available()
    out["device_count"] = torch.cuda.device_count()
    if out["cuda_available"]:
        out["device_name"] = torch.cuda.get_device_name(0)
except Exception as e:
    out["torch_error"] = repr(e)

print(json.dumps(out, ensure_ascii=True))
"""
    return run([str(python_bin), "-c", code])


def main():
    report = {
        "cwd": str(ROOT),
        "user": os.environ.get("USER"),
        "home": os.environ.get("HOME"),
        "wsl_distro_name": os.environ.get("WSL_DISTRO_NAME"),
        "ld_library_path": os.environ.get("LD_LIBRARY_PATH"),
        "python": sys.executable,
        "python_version": sys.version,
        "platform": platform.platform(),
        "uname": " ".join(platform.uname()),
        "system_cuinit": cuinit_status(),
        "nvidia_smi_L": run(["nvidia-smi", "-L"]),
        "nvidia_smi": run(["nvidia-smi"]),
        "venv_classifier": python_cuda_status(VENV_CLASSIFIER),
        "venv_prompt": python_cuda_status(VENV_PROMPT),
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
