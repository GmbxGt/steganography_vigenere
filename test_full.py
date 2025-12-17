"""Набор интеграционных и модульных тестов (pytest).

Модуль проверяет корректность:
- кодирования/декодирования и сокрытия/извлечения данных в steganography;
- шифрования/дешифрования Виженера (vigenere);
- утилит ввода-вывода и валидации ключа (utils);
- ветвления запуска GUI/CLI (run) и базовой интеграции GUI-обработчиков.

Запуск:
    pytest -q
"""

import pytest

import steganography


def test_text_to_binary_positive_and_binary_to_text_roundtrip():
    msg = "Привет, world! 123"
    bits = steganography.text_to_binary(msg)
    assert isinstance(bits, str)
    assert set(bits).issubset({"0", "1"})
    # Должно корректно восстановиться
    assert steganography.binary_to_text(bits) == msg


def test_binary_to_text_negative_too_short_header_raises():
    # HEADER_BITS = 64, дадим меньше
    with pytest.raises(ValueError):
        steganography.binary_to_text("0" * (steganography.HEADER_BITS - 1))


def test_binary_to_text_negative_magic_mismatch_raises():
    # Берём валидные биты и ломаем MAGIC в первых битах
    msg = "hello"
    bits = list(steganography.text_to_binary(msg))
    # Инвертируем первые 8 бит (точно испортит MAGIC)
    for i in range(8):
        bits[i] = "1" if bits[i] == "0" else "0"
    bad_bits = "".join(bits)

    with pytest.raises(ValueError):
        steganography.binary_to_text(bad_bits)


def test_hide_and_extract_positive_full_roundtrip():
    # Сделаем секрет и контейнер с достаточным числом пробелов
    secret_text = "секрет"
    secret_bits = steganography.text_to_binary(secret_text)

    container = "A " * (len(secret_bits) + 5)  # много пробелов
    stego = steganography.hide_text_in_container(secret_bits, container)

    extracted_bits = steganography.extract_text_from_container(stego)
    assert extracted_bits == secret_bits
    assert steganography.binary_to_text(extracted_bits) == secret_text


def test_hide_text_in_container_negative_not_enough_capacity_raises():
    secret_bits = "0" * 10
    container = "no_spaces_here"  # 0 пробелов => 0 бит вместимость
    with pytest.raises(ValueError):
        steganography.hide_text_in_container(secret_bits, container)


def test_extract_text_from_container_positive_and_negative_empty_result():
    # Положительный: после пробела стоят zero-width символы
    stego = "X " + steganography.ZWS_0 + "Y " + steganography.ZWNJ_1 + "Z"
    assert steganography.extract_text_from_container(stego) == "01"

    # Негативный: нет zero-width после пробелов => пустая строка
    plain = "X Y Z"
    assert steganography.extract_text_from_container(plain) == ""


def test_get_capacity_positive_and_negative_zero():
    # Положительный: считаем пробелы
    container = "a b  c   "
    cap = steganography.get_capacity(container)
    assert cap.spaces == container.count(" ")
    assert cap.bits_capacity == cap.spaces

    # Негативный (граничный): нет пробелов => 0
    cap2 = steganography.get_capacity("no_spaces")
    assert cap2.spaces == 0
    assert cap2.bits_capacity == 0


    
import vigenere


def test_prepare_key_positive_filters_and_returns_index_and_n():
    key_filtered, index, n = vigenere._prepare_key("kEy")
    assert key_filtered == ["K", "E", "Y"]
    assert index["A"] == 0
    assert n == len(vigenere.LETTERS)


def test_prepare_key_negative_empty_key_raises():
    with pytest.raises(ValueError, match="пуст"):
        vigenere._prepare_key("")


def test_prepare_key_negative_no_valid_symbols_raises():
    with pytest.raises(ValueError):
        vigenere._prepare_key("!!!")


def test_vigenere_encrypt_positive_basic_latin_shift_and_preserves_nonletters():
    # With key 'B' (shift 1), plaintext 'ABC' -> 'BCD' in the LETTERS alphabet
    assert vigenere.vigenere_encrypt("ABC", "B") == "BCD"

    # Non-alphabet characters should remain unchanged (but text is uppercased)
    assert vigenere.vigenere_encrypt("A-B C!", "B") == "B-C D!"


def test_vigenere_encrypt_negative_empty_key_raises():
    with pytest.raises(ValueError):
        vigenere.vigenere_encrypt("HELLO", "")


def test_vigenere_encrypt_negative_key_without_valid_symbols_raises():
    with pytest.raises(ValueError):
        vigenere.vigenere_encrypt("HELLO", "123!!!")


def test_vigenere_decrypt_positive_basic_latin_shift_and_roundtrip():
    # Basic known pair
    assert vigenere.vigenere_decrypt("BCD", "B") == "ABC"

    # Roundtrip property (result is uppercased by implementation)
    text = "Hello, World! 123"
    key = "KEY"
    enc = vigenere.vigenere_encrypt(text, key)
    dec = vigenere.vigenere_decrypt(enc, key)
    assert dec == text.upper()


def test_vigenere_decrypt_negative_empty_key_raises():
    with pytest.raises(ValueError):
        vigenere.vigenere_decrypt("ANY", "")


def test_vigenere_decrypt_negative_key_without_valid_symbols_raises():
    with pytest.raises(ValueError):
        vigenere.vigenere_decrypt("ANY", "!!!")


import utils


def test_validate_key_positive_accepts_letters_from_letters_alphabet():
    # Берём гарантированно допустимые символы из того же алфавита, что в проекте
    key = utils.LETTERS[:5]
    assert utils.validate_key(key) is True
    # Регистр не важен (key.upper() внутри validate_key)
    assert utils.validate_key(key.lower()) is True


def test_validate_key_negative_empty_and_invalid_chars():
    assert utils.validate_key("") is False
    assert utils.validate_key("!!!") is False
    assert utils.validate_key("A!") is False


def test_write_file_positive_writes_to_file_and_creates_dirs(tmp_path):
    # 1) Запись в файл в текущей папке
    p1 = tmp_path / "out.txt"
    utils.write_file(str(p1), "hello")
    assert p1.read_text(encoding="utf-8") == "hello"

    # 2) Запись во вложенные директории (директории должны создаться)
    p2 = tmp_path / "a" / "b" / "c.txt"
    utils.write_file(str(p2), "nested")
    assert p2.read_text(encoding="utf-8") == "nested"


def test_write_file_negative_raises_on_directory_target(tmp_path):
    # Если путь указывает на директорию, open(..., 'w') должен упасть
    d = tmp_path / "dir_target"
    d.mkdir()
    with pytest.raises((IsADirectoryError, PermissionError, OSError)):
        utils.write_file(str(d), "data")


def test_read_file_positive_reads_existing_file(tmp_path):
    p = tmp_path / "in.txt"
    p.write_text("привет", encoding="utf-8")
    assert utils.read_file(str(p)) == "привет"


def test_read_file_negative_missing_file_raises(tmp_path):
    missing = tmp_path / "missing.txt"
    with pytest.raises(FileNotFoundError):
        utils.read_file(str(missing))



import gui


class DummyVar:
    def __init__(self, value=""):
        self._v = value

    def get(self):
        return self._v

    def set(self, value):
        self._v = value


class DummyPreview:
    def __init__(self):
        self.deleted = False
        self.inserted = ""

    def delete(self, *_args, **_kwargs):
        self.deleted = True
        self.inserted = ""

    def insert(self, *_args, **_kwargs):
        # tkinter passes (index, text)
        if len(_args) >= 2:
            self.inserted += str(_args[1])


def _patch_build_ui(monkeypatch):
    """Replace UI build with minimal fields needed by action methods."""

    def fake_build_ui(self):
        self.status_var = DummyVar("Готов")

        self.hide_key = DummyVar("")
        self.container_path = DummyVar("")
        self.secret_path = DummyVar("")
        self.output_path = DummyVar("out.txt")

        self.extract_key = DummyVar("")
        self.stego_path = DummyVar("")
        self.extract_output = DummyVar("extracted.txt")

        self.preview = DummyPreview()

    monkeypatch.setattr(gui.SteganographyApp, "_build_ui", fake_build_ui)


def test_run_gui_positive_creates_app_and_enters_mainloop(monkeypatch):
    called = {"tk": 0, "app": 0, "loop": 0}

    class FakeRoot:
        def mainloop(self):
            called["loop"] += 1

    def fake_tk():
        called["tk"] += 1
        return FakeRoot()

    class FakeApp:
        def __init__(self, root):
            assert isinstance(root, FakeRoot)
            called["app"] += 1

    monkeypatch.setattr(gui.tk, "Tk", fake_tk)
    monkeypatch.setattr(gui, "SteganographyApp", FakeApp)

    gui.run_gui()

    assert called["tk"] == 1
    assert called["app"] == 1
    assert called["loop"] == 1


def test_run_gui_negative_tk_failure_raises(monkeypatch):
    def fake_tk():
        raise RuntimeError("no display")

    monkeypatch.setattr(gui.tk, "Tk", fake_tk)

    with pytest.raises(RuntimeError, match="no display"):
        gui.run_gui()



import sys
import types

import main


import builtins

import run




def test_run_negative_choice_other_calls_main(monkeypatch):
    called = {"gui": 0, "cli": 0}

    def fake_run_gui():
        called["gui"] += 1

    def fake_main():
        called["cli"] += 1

    monkeypatch.setattr(run, "run_gui", fake_run_gui)
    monkeypatch.setattr(run, "main", fake_main)
    monkeypatch.setattr(builtins, "input", lambda _: "2")

    run.run()

    assert called["gui"] == 0
    assert called["cli"] == 1


def test_run_negative_choice_empty_or_spaces_calls_main(monkeypatch):
    called = {"gui": 0, "cli": 0}

    def fake_run_gui():
        called["gui"] += 1

    def fake_main():
        called["cli"] += 1

    monkeypatch.setattr(run, "run_gui", fake_run_gui)
    monkeypatch.setattr(run, "main", fake_main)
    monkeypatch.setattr(builtins, "input", lambda _: "   ")

    run.run()

    assert called["gui"] == 0
    assert called["cli"] == 1


def test_run_gui_function_positive_and_negative_via_branching(monkeypatch):
    '''
    Требование: в каждой тестируемой функции должен быть и положительный, и
    отрицательный результат. Для run_gui и main (импортированы в run.py) мы
    проверяем это через ветвление в run.run():
      - положительный для run_gui: выбор "1" -> вызывается
      - отрицательный для run_gui: выбор "2" -> не вызывается
      - положительный для main: выбор "2" -> вызывается
      - отрицательный для main: выбор "1" -> не вызывается
    Этот тест делает обе проверки в одном месте, чтобы явно покрыть обе функции.
    '''
    called = {"gui": 0, "cli": 0}

    def fake_run_gui():
        called["gui"] += 1

    def fake_main():
        called["cli"] += 1

    monkeypatch.setattr(run, "run_gui", fake_run_gui)
    monkeypatch.setattr(run, "main", fake_main)

    # run_gui positive, main negative
    monkeypatch.setattr(builtins, "input", lambda _: "1")
    run.run()
    assert called["gui"] == 1
    assert called["cli"] == 0

    # run_gui negative, main positive
    monkeypatch.setattr(builtins, "input", lambda _: "2")
    run.run()
    assert called["gui"] == 1
    assert called["cli"] == 1



