"""Запуск проекта (выбор GUI или CLI).

Модуль показывает пользователю простое меню в консоли и запускает либо
графический интерфейс (:func:`gui.run_gui`), либо CLI (:func:`main.main`).

Точка входа: :func:`run`.
"""

from __future__ import annotations

from main import main
from gui import run_gui


def run() -> None:
    """Показать меню запуска и выполнить выбранный режим.

    Пользователь вводит ``"1"`` для запуска GUI. Любой другой ввод
    (включая пустую строку) запускает CLI.

    Returns:
        ``None``.
    """
    print("1 — GUI")
    print("1 — CLI")
    
    choice = input("Выбор: ").strip()

    if choice == "1":
        run_gui()
    else:
        main()


if __name__ == "__main__":
    run()
