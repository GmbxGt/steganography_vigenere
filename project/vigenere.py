"""Реализация шифра Виженера.

Модуль реализует классический шифр Виженера над расширенным алфавитом
:data:`LETTERS`. Шифрование и дешифрование выполняются в верхнем регистре.
Символы, которые не входят в алфавит, сохраняются без изменений.

Основные функции:
- :func:`vigenere_encrypt` — шифрование.
- :func:`vigenere_decrypt` — дешифрование.
"""

from __future__ import annotations

from typing import Dict, List, Tuple

#: Поддерживаемый алфавит (должен совпадать с алфавитом в других модулях).
LETTERS = (
    "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    "АБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЬЪЫЭЮЯ"
    "ҐЄІЎЇÜÖÄẞÅÆØ"
)


def _prepare_key(key: str) -> Tuple[List[str], Dict[str, int], int]:
    """Подготовить ключ и структуру индексации алфавита.

    Функция:
    1) проверяет, что ключ не пуст;
    2) переводит ключ в верхний регистр;
    3) отбрасывает символы, не входящие в :data:`LETTERS`;
    4) строит словарь ``символ -> индекс`` для быстрого доступа.

    Args:
        key: Пользовательский ключ шифрования.

    Returns:
        Кортеж из трёх элементов:

        - ``key_filtered``: список символов ключа, отфильтрованных по алфавиту;
        - ``index``: словарь индексов алфавита;
        - ``n``: размер алфавита.

    Raises:
        ValueError: Если ключ пуст или после фильтрации не осталось допустимых
            символов.
    """
    if not key:
        raise ValueError("Ключ не может быть пустым")

    index = {ch: i for i, ch in enumerate(LETTERS)}
    key_upper = key.upper()
    key_filtered = [ch for ch in key_upper if ch in index]

    if not key_filtered:
        raise ValueError("Ключ не содержит допустимых символов")

    return key_filtered, index, len(LETTERS)


def vigenere_encrypt(text: str, key: str) -> str:
    """Зашифровать текст шифром Виженера.

    Входной текст приводится к верхнему регистру. Символы, которых нет в
    :data:`LETTERS`, добавляются в результат без изменений и не сдвигают
    позицию ключа.

    Args:
        text: Открытый текст (любой Unicode).
        key: Ключ шифрования.

    Returns:
        Зашифрованный текст в верхнем регистре.

    Raises:
        ValueError: Если ключ некорректен (см. :func:`_prepare_key`).
    """
    key_filtered, index, n = _prepare_key(key)
    out: List[str] = []
    key_i = 0

    for ch in text.upper():
        if ch in index:
            shift = index[key_filtered[key_i % len(key_filtered)]]
            out.append(LETTERS[(index[ch] + shift) % n])
            key_i += 1
        else:
            out.append(ch)

    return "".join(out)


def vigenere_decrypt(text: str, key: str) -> str:
    """Расшифровать текст, зашифрованный шифром Виженера.

    Входной текст приводится к верхнему регистру. Символы, которых нет в
    :data:`LETTERS`, сохраняются без изменений и не сдвигают позицию ключа.

    Args:
        text: Зашифрованный текст.
        key: Ключ дешифрования (должен совпадать с ключом шифрования).

    Returns:
        Расшифрованный текст в верхнем регистре.

    Raises:
        ValueError: Если ключ некорректен (см. :func:`_prepare_key`).
    """
    key_filtered, index, n = _prepare_key(key)
    out: List[str] = []
    key_i = 0

    for ch in text.upper():
        if ch in index:
            shift = index[key_filtered[key_i % len(key_filtered)]]
            out.append(LETTERS[(index[ch] - shift) % n])
            key_i += 1
        else:
            out.append(ch)

    return "".join(out)
