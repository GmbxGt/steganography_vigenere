"""Командная строка (CLI) для стеганографии и шифра Виженера.

Модуль реализует интерфейс командной строки на базе :mod:`argparse`.

Команды:
- ``hide`` — скрыть секретный файл в контейнере;
- ``extract`` — извлечь скрытое сообщение из стего-файла.

Точка входа: :func:`main`.
"""

from __future__ import annotations

import argparse

from steganography import (
    binary_to_text,
    extract_text_from_container,
    hide_text_in_container,
    text_to_binary,
)
from utils import read_file, write_file, validate_key
from vigenere import vigenere_encrypt, vigenere_decrypt


def main() -> None:
    """Запустить CLI и выполнить выбранную команду.

    Raises:
        SystemExit: Если ключ шифрования некорректен.
        ValueError: Если контейнер слишком мал или формат скрытых данных неверный.
        OSError: При ошибках чтения/записи файлов.
    """
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd", required=True)

    hide = sub.add_parser("hide")
    hide.add_argument("-c", "--container", required=True, help="Файл-контейнер (txt).")
    hide.add_argument("-s", "--secret", required=True, help="Файл с секретным текстом.")
    hide.add_argument("-k", "--key", required=True, help="Ключ шифра Виженера.")

    ext = sub.add_parser("extract")
    ext.add_argument("-i", "--input", required=True, help="Стего-файл (txt).")
    ext.add_argument("-k", "--key", required=True, help="Ключ дешифрования.")

    args = parser.parse_args()

    if not validate_key(args.key):
        raise SystemExit("Неверный ключ")

    if args.cmd == "hide":
        container = read_file(args.container)
        secret = read_file(args.secret)

        encrypted = vigenere_encrypt(secret, args.key)
        bits = text_to_binary(encrypted)
        result = hide_text_in_container(bits, container)

        write_file("stego_container.txt", result)

    elif args.cmd == "extract":
        data = read_file(args.input)
        bits = extract_text_from_container(data)
        encrypted = binary_to_text(bits)
        decrypted = vigenere_decrypt(encrypted, args.key)

        write_file("extracted_secret.txt", decrypted)


if __name__ == "__main__":
    main()
