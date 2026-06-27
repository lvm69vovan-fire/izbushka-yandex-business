# -*- coding: utf-8 -*-
from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

PACKAGE_DIR = Path(__file__).resolve().parent
WORK_DIR = PACKAGE_DIR.parent
LOG_FILE = WORK_DIR / "v9-run-log.txt"
URLS_FILE = WORK_DIR / "izbushka-product-urls.txt"

os.environ["PYTHONUTF8"] = "1"
os.environ["PYTHONIOENCODING"] = "utf-8"


def write_log(text: str = "") -> None:
    print(text, flush=True)
    with LOG_FILE.open("a", encoding="utf-8-sig") as f:
        f.write(text + "\n")


def run_live(command: list[str], cwd: Path) -> int:
    process = subprocess.Popen(
        command,
        cwd=str(cwd),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=os.environ.copy(),
    )
    assert process.stdout is not None
    for line in process.stdout:
        line = line.rstrip("\r\n")
        write_log(line)
    return process.wait()


def ensure_packages() -> None:
    missing = []
    checks = {
        "requests": "requests",
        "bs4": "beautifulsoup4",
        "lxml": "lxml",
    }
    for module, package in checks.items():
        try:
            __import__(module)
        except ImportError:
            missing.append(package)

    if not missing:
        write_log("Библиотеки Python уже установлены.")
        return

    write_log("Устанавливаю библиотеки Python: " + ", ".join(missing))
    code = run_live(
        [sys.executable, "-m", "pip", "install", *missing],
        WORK_DIR,
    )
    if code != 0:
        raise RuntimeError("Не удалось установить библиотеки Python.")


def clean_old_results() -> None:
    for name in (
        "izbushka-yandex-in-stock.xml",
        "izbushka-skipped.csv",
        "izbushka-yml-by-category.zip",
    ):
        path = WORK_DIR / name
        if path.exists():
            path.unlink()

    category_dir = WORK_DIR / "yml_by_category"
    if category_dir.exists():
        shutil.rmtree(category_dir)


def main() -> int:
    LOG_FILE.write_text("", encoding="utf-8-sig")

    write_log("==========================================")
    write_log("IZBUSHKA YML GENERATOR V9.5")
    write_log(f"Рабочая папка: {WORK_DIR}")
    write_log("==========================================")
    write_log()

    if not URLS_FILE.exists():
        write_log(f"ОШИБКА: не найден файл {URLS_FILE}")
        return 1

    write_log(f"Python: {sys.version.split()[0]}")
    ensure_packages()
    clean_old_results()

    write_log()
    write_log("Запускаю проверку товаров...")
    code = run_live(
        [sys.executable, "-X", "utf8", "-u", str(PACKAGE_DIR / "izbushka_to_yml_v9.py")],
        WORK_DIR,
    )
    if code != 0:
        write_log(f"ОШИБКА: генератор завершился с кодом {code}")
        return code

    write_log()
    write_log("Разбиваю выгрузку по категориям...")
    code = run_live(
        [sys.executable, "-X", "utf8", "-u", str(PACKAGE_DIR / "split_yml_by_category.py")],
        WORK_DIR,
    )
    if code != 0:
        write_log(f"ОШИБКА: разбивка завершилась с кодом {code}")
        return code

    write_log()
    write_log("ГОТОВО.")
    write_log(f"Результаты находятся в {WORK_DIR}")
    write_log(f"Журнал: {LOG_FILE}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        write_log(f"КРИТИЧЕСКАЯ ОШИБКА: {exc}")
        raise
