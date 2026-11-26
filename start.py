import subprocess
import sys
from pathlib import Path


def run_bot_as_module(project_dir: str, module_name: str = "bot") -> int:
    """
    Запускает bot.py как модуль: python -m bot
    из указанной директории проекта.

    :param project_dir: путь к папке, где лежит bot.py (и где его видно как модуль)
    :param module_name: имя модуля без .py, по умолчанию "bot"
    :return: код возврата процесса
    """
    project_path = Path(project_dir).resolve()

    if not (project_path / f"{module_name}.py").exists():
        raise FileNotFoundError(f"Не найден {module_name}.py в {project_path}")

    cmd = [sys.executable, "-m", module_name]
    print("Запуск:", " ".join(cmd), "в", project_path)

    try:
        result = subprocess.run(cmd, cwd=project_path)
        return result.returncode
    except KeyboardInterrupt:
        print("Остановлено пользователем")
        return 130


if __name__ == "__main__":
    # укажите путь к папке, где лежит bot.py
    PROJECT_DIR = r" "
    raise SystemExit(run_bot_as_module(PROJECT_DIR))