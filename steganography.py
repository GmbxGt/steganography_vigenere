"""Стеганография на основе zero-width символов.

Модуль позволяет скрывать битовую строку (``'0'``/``'1'``) внутри текста-
контейнера. Скрытие происходит после пробелов: сразу после пробела
вставляется один из невидимых Unicode-символов:

- :data:`ZWS_0` (U+200B, Zero Width Space) кодирует бит ``0``;
- :data:`ZWNJ_1` (U+200C, Zero Width Non-Joiner) кодирует бит ``1``.

Также модуль содержит упаковку/распаковку текста в двоичный формат с
заголовком, чтобы при извлечении можно было восстановить исходный UTF‑8
текст и проверить целостность.

Формат полезной нагрузки (payload):
- MAGIC (4 байта) + длина payload (4 байта, big-endian) + payload (UTF‑8).
"""

from __future__ import annotations

from dataclasses import dataclass

#: Символ, кодирующий бит 0 (Zero Width Space).
ZWS_0 = "\u200B"
#: Символ, кодирующий бит 1 (Zero Width Non-Joiner).
ZWNJ_1 = "\u200C"

#: Магические байты для проверки формата извлечённых данных.
MAGIC = b"ZWST"
#: Размер заголовка в битах (MAGIC 4 байта + длина 4 байта = 8 байт = 64 бита).
HEADER_BITS = 64


@dataclass(frozen=True)
class CapacityInfo:
    """Информация о ёмкости контейнера.

    Attributes:
        spaces: Количество пробелов в контейнере.
        bits_capacity: Сколько бит можно спрятать (в текущей реализации равно
            ``spaces``).
    """

    spaces: int
    bits_capacity: int


def _bytes_to_bits(data: bytes) -> str:
    """Преобразовать байты в строку битов.

    Args:
        data: Исходные байты.

    Returns:
        Строка из символов ``'0'`` и ``'1'`` длиной ``len(data) * 8``.
    """
    return "".join(f"{b:08b}" for b in data)


def _bits_to_bytes(bits: str) -> bytes:
    """Преобразовать строку битов в байты.

    Args:
        bits: Строка битов. Длина должна быть кратна 8.

    Returns:
        Байтовая последовательность.

    Raises:
        ValueError: Если длина ``bits`` не кратна 8.
    """
    if len(bits) % 8 != 0:
        raise ValueError("Количество битов не кратно 8")

    out = bytearray()
    for i in range(0, len(bits), 8):
        out.append(int(bits[i : i + 8], 2))
    return bytes(out)


def text_to_binary(text: str) -> str:
    """Закодировать текст в двоичную строку с заголовком.

    Args:
        text: Текст для сокрытия (любой Unicode).

    Returns:
        Битовая строка, содержащая заголовок и полезную нагрузку, готовая к
        передаче в :func:`hide_text_in_container`.
    """
    payload = text.encode("utf-8")
    header = MAGIC + len(payload).to_bytes(4, "big")
    return _bytes_to_bits(header + payload)


def binary_to_text(binary: str) -> str:
    """Декодировать двоичную строку, созданную :func:`text_to_binary`.

    Args:
        binary: Битовая строка, содержащая заголовок и payload.

    Returns:
        Восстановленный текст (UTF‑8).

    Raises:
        ValueError: Если заголовок некорректен: недостаточная длина,
            несовпадение MAGIC, невозможность декодирования payload.
    """
    header = _bits_to_bytes(binary[:HEADER_BITS])
    if header[:4] != MAGIC:
        raise ValueError("Неверный формат данных")

    length = int.from_bytes(header[4:], "big")
    payload_bits = binary[HEADER_BITS : HEADER_BITS + length * 8]
    return _bits_to_bytes(payload_bits).decode("utf-8")


def get_capacity(container: str) -> CapacityInfo:
    """Посчитать ёмкость текстового контейнера.

    В текущей реализации 1 пробел == 1 бит.

    Args:
        container: Текст-контейнер.

    Returns:
        Объект :class:`CapacityInfo` с количеством пробелов и битовой ёмкостью.
    """
    spaces = container.count(" ")
    return CapacityInfo(spaces, spaces)


def hide_text_in_container(secret: str, container: str) -> str:
    """Спрятать битовую строку в контейнере.

    Биты скрываются по порядку: после каждого пробела добавляется один
    zero-width символ, пока не закончатся биты.

    Args:
        secret: Битовая строка из ``'0'`` и ``'1'``.
        container: Текст-контейнер. В нём должно быть достаточно пробелов.

    Returns:
        Стего-текст (контейнер с вставленными невидимыми символами).

    Raises:
        ValueError: Если контейнер не вмещает ``secret``.
    """
    cap = get_capacity(container)
    if len(secret) > cap.bits_capacity:
        raise ValueError("Контейнер слишком мал")

    out = []
    i = 0
    for ch in container:
        if ch == " " and i < len(secret):
            out.append(" ")
            out.append(ZWS_0 if secret[i] == "0" else ZWNJ_1)
            i += 1
        else:
            out.append(ch)

    return "".join(out)


def extract_text_from_container(container: str) -> str:
    """Извлечь скрытую битовую строку из контейнера.

    Функция ищет шаблоны вида ``' ' + ZWS_0`` и ``' ' + ZWNJ_1`` и собирает
    соответствующие биты в порядке следования по строке.

    Args:
        container: Стего-текст.

    Returns:
        Извлечённая строка битов. Может быть пустой, если скрытых данных нет.
    """
    bits = []
    i = 0
    while i < len(container) - 1:
        if container[i] == " ":
            if container[i + 1] == ZWS_0:
                bits.append("0")
                i += 2
                continue
            if container[i + 1] == ZWNJ_1:
                bits.append("1")
                i += 2
                continue
        i += 1
    return "".join(bits)
