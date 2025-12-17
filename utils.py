"""Вспомогательные утилиты проекта.

Модуль содержит функции для чтения/записи текстовых файлов и проверки
ключа шифрования. Ключ проверяется на принадлежность символов к
поддерживаемому алфавиту :data:`LETTERS`.

Все операции ввода-вывода выполняются в кодировке UTF-8.
"""

from __future__ import annotations

import os

#: Поддерживаемый алфавит для шифра Виженера (латиница + кириллица + часть
#: расширенных символов).
LETTERS = (
    "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    "АБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЬЪЫЭЮЯ"
    "ҐЄІЎЇÜÖÄẞÅÆØ"
)


def read_file(filepath: str) -> str:
    """Прочитать текстовый файл целиком.

    Args:
        filepath: Путь к файлу.

    Returns:
        Содержимое файла как строка.

    Raises:
        OSError: Любая ошибка, возникающая при открытии/чтении файла.
            (Например, файл не найден, нет прав доступа и т.п.)
    """
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as exc:
        print(f"Ошибка чтения файла: {exc}")
        raise


def write_file(filepath: str, content: str) -> None:
    """Записать строку в текстовый файл.

    Если директория в пути отсутствует, она будет создана.

    Args:
        filepath: Путь к файлу назначения.
        content: Текст, который будет записан в файл.

    Raises:
        OSError: Любая ошибка, возникающая при создании директорий или
            записи файла (например, путь указывает на директорию).
    """
    try:
        directory = os.path.dirname(filepath)
        if directory:
            os.makedirs(directory, exist_ok=True)

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
    except Exception as exc:
        print(f"Ошибка записи файла: {exc}")
        raise


def validate_key(key: str) -> bool:
    """Проверить, что ключ шифрования валиден.

    Ключ считается валидным, если он не пуст и *все* его символы после
    приведения к верхнему регистру входят в :data:`LETTERS`.

    Args:
        key: Ключ шифрования.

    Returns:
        ``True``, если ключ валиден, иначе ``False``.
    """
    if not key:
        return False

    key = key.upper()
    return all(ch in LETTERS for ch in key)
