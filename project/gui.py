"""Графический интерфейс (Tkinter) для стеганографии и шифра Виженера.

Модуль содержит GUI-приложение на Tkinter, которое позволяет:

1) зашифровать секретный текст шифром Виженера;
2) закодировать его в биты;
3) спрятать биты в текстовом контейнере с помощью zero-width символов;
4) извлечь и расшифровать сообщение из стего-файла.

Точка входа: :func:`run_gui`.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk

from steganography import (
    binary_to_text,
    extract_text_from_container,
    hide_text_in_container,
    text_to_binary,
)
from utils import read_file, validate_key, write_file
from vigenere import vigenere_decrypt, vigenere_encrypt


class SteganographyApp:
    """Главное окно приложения.

    Args:
        root: Корневое окно Tkinter (:class:`tkinter.Tk`).

    Attributes:
        root: Корневое окно приложения.
        notebook: Виджет вкладок.
        status_var: Переменная состояния (текст в строке статуса).
        hide_key: Ключ для шифрования на вкладке «Скрыть сообщение».
        container_path: Путь к файлу-контейнеру.
        secret_path: Путь к секретному файлу.
        output_path: Путь к выходному стего-файлу.
        extract_key: Ключ для дешифрования на вкладке «Извлечь сообщение».
        stego_path: Путь к стего-файлу для извлечения.
        extract_output: Путь к выходному файлу с извлечённым текстом.
        preview: Поле предпросмотра извлечённого текста.
    """

    def __init__(self, root: tk.Tk) -> None:
        """Создать окно приложения и построить интерфейс."""
        self.root = root
        self.root.title("Стеганография + шифр Виженера")
        self.root.geometry("800x600")

        style = ttk.Style()
        style.theme_use("clam")

        self._build_ui()

    # -------------------------------------------------
    # UI construction
    # -------------------------------------------------

    def _build_ui(self) -> None:
        """Построить основной интерфейс (вкладки, формы и строку статуса)."""
        main = ttk.Frame(self.root, padding=10)
        main.grid(sticky="nsew")

        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main.columnconfigure(1, weight=1)

        title = ttk.Label(
            main,
            text="Стеганография с использованием шифра Виженера",
            font=("Arial", 16, "bold"),
        )
        title.grid(row=0, column=0, columnspan=3, pady=(0, 20))

        self.notebook = ttk.Notebook(main)
        self.notebook.grid(
            row=1,
            column=0,
            columnspan=3,
            sticky="nsew",
        )

        self._build_hide_tab()
        self._build_extract_tab()
        self._build_about_tab()

        self.status_var = tk.StringVar(value="Готов")
        status = ttk.Label(
            main,
            textvariable=self.status_var,
            relief=tk.SUNKEN,
            anchor=tk.W,
        )
        status.grid(row=2, column=0, columnspan=3, sticky="ew", pady=(10, 0))

    # -------------------------------------------------
    # Hide tab
    # -------------------------------------------------

    def _build_hide_tab(self) -> None:
        """Создать вкладку для сокрытия сообщения."""
        frame = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(frame, text="Скрыть сообщение")

        ttk.Label(frame, text="Ключ шифрования:").grid(row=0, column=0, sticky="w")
        self.hide_key = tk.StringVar()
        ttk.Entry(frame, textvariable=self.hide_key).grid(
            row=0, column=1, sticky="ew", pady=5
        )

        ttk.Label(frame, text="Файл-контейнер:").grid(row=1, column=0, sticky="w")
        self.container_path = tk.StringVar()
        self._file_picker(frame, self.container_path, 1)

        ttk.Label(frame, text="Секретный файл:").grid(row=2, column=0, sticky="w")
        self.secret_path = tk.StringVar()
        self._file_picker(frame, self.secret_path, 2)

        ttk.Label(frame, text="Выходной файл:").grid(row=3, column=0, sticky="w")
        self.output_path = tk.StringVar(value="stego_container.txt")
        self._file_saver(frame, self.output_path, 3)

        ttk.Button(
            frame,
            text="Скрыть сообщение",
            command=self._hide_message,
        ).grid(row=4, column=0, columnspan=2, pady=15)

        frame.columnconfigure(1, weight=1)

    # -------------------------------------------------
    # Extract tab
    # -------------------------------------------------

    def _build_extract_tab(self) -> None:
        """Создать вкладку для извлечения сообщения."""
        frame = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(frame, text="Извлечь сообщение")

        ttk.Label(frame, text="Ключ шифрования:").grid(row=0, column=0, sticky="w")
        self.extract_key = tk.StringVar()
        ttk.Entry(frame, textvariable=self.extract_key).grid(
            row=0, column=1, sticky="ew", pady=5
        )

        ttk.Label(frame, text="Стего-файл:").grid(row=1, column=0, sticky="w")
        self.stego_path = tk.StringVar()
        self._file_picker(frame, self.stego_path, 1)

        ttk.Label(frame, text="Выходной файл:").grid(row=2, column=0, sticky="w")
        self.extract_output = tk.StringVar(value="extracted_secret.txt")
        self._file_saver(frame, self.extract_output, 2)

        ttk.Button(
            frame,
            text="Извлечь сообщение",
            command=self._extract_message,
        ).grid(row=3, column=0, columnspan=2, pady=10)

        preview = scrolledtext.ScrolledText(frame, height=12, wrap=tk.WORD)
        preview.grid(row=4, column=0, columnspan=2, sticky="nsew", pady=10)
        self.preview = preview

        frame.columnconfigure(1, weight=1)
        frame.rowconfigure(4, weight=1)

    # -------------------------------------------------
    # About tab
    # -------------------------------------------------

    def _build_about_tab(self) -> None:
        """Создать вкладку «О программе»."""
        frame = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(frame, text="О программе")

        text = scrolledtext.ScrolledText(frame, wrap=tk.WORD, state=tk.NORMAL)
        text.insert(
            tk.END,
            """Программа для стеганографии с шифром Виженера

        Функции:
        1. Шифрование текста шифром Виженера
        2. Скрытие зашифрованного текста в контейнере
           с использованием невидимых символов
        3. Извлечение и дешифрование скрытого текста

        Используемые технологии:
        • Шифр Виженера для шифрования
        • Zero-Width символы для стеганографии
        • Двоичное кодирование текста

        Как использовать:
        1. На вкладке 'Скрыть сообщение':
           - Введите ключ шифрования
           - Выберите файл-контейнер
           - Выберите файл с секретным текстом
           - Укажите выходной файл
           - Нажмите 'Скрыть сообщение'

        2. На вкладке 'Извлечь сообщение':
           - Введите ключ дешифрования
           - Выберите файл со скрытым текстом
           - Нажмите 'Извлечь сообщение'

        Автор: Глижинский Вячеслав БИБ252, МИЭМ ВШЭ
        Версия: 1.0
        """
        )
        text.configure(state=tk.DISABLED)
        text.pack(fill=tk.BOTH, expand=True)

    # -------------------------------------------------
    # Helpers
    # -------------------------------------------------

    def _file_picker(self, parent, var: tk.StringVar, row: int) -> None:
        """Добавить элемент выбора файла (поле + кнопка «Обзор…»).

        Args:
            parent: Родительский виджет.
            var: Tk-переменная, в которую будет записан выбранный путь.
            row: Номер строки grid-разметки.
        """
        frame = ttk.Frame(parent)
        frame.grid(row=row, column=1, sticky="ew")

        ttk.Entry(frame, textvariable=var).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(
            frame,
            text="Обзор…",
            command=lambda: self._browse(var),
        ).pack(side=tk.LEFT, padx=5)

    def _file_saver(self, parent, var: tk.StringVar, row: int) -> None:
        """Добавить элемент сохранения файла (поле + кнопка «Сохранить…»).

        Args:
            parent: Родительский виджет.
            var: Tk-переменная, содержащая путь сохранения.
            row: Номер строки grid-разметки.
        """
        frame = ttk.Frame(parent)
        frame.grid(row=row, column=1, sticky="ew")

        ttk.Entry(frame, textvariable=var).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(
            frame,
            text="Сохранить…",
            command=lambda: self._save_as(var),
        ).pack(side=tk.LEFT, padx=5)

    def _browse(self, var: tk.StringVar) -> None:
        """Открыть диалог выбора файла и записать путь в переменную.

        Args:
            var: Tk-переменная для сохранения результата.
        """
        path = filedialog.askopenfilename()
        if path:
            var.set(path)

    def _save_as(self, var: tk.StringVar) -> None:
        """Открыть диалог «Сохранить как…» и записать путь в переменную.

        Args:
            var: Tk-переменная для сохранения результата.
        """
        path = filedialog.asksaveasfilename(defaultextension=".txt")
        if path:
            var.set(path)

    # -------------------------------------------------
    # Actions
    # -------------------------------------------------

    def _hide_message(self) -> None:
        """Скрыть сообщение: шифрование -> биты -> внедрение -> запись файла.

        Raises:
            ValueError: Если ключ некорректен или контейнер слишком мал.
            OSError: Если возникли ошибки ввода-вывода при чтении/записи файлов.
        """
        try:
            if not validate_key(self.hide_key.get()):
                raise ValueError("Недопустимый ключ")

            container = read_file(self.container_path.get())
            secret = read_file(self.secret_path.get())

            encrypted = vigenere_encrypt(secret, self.hide_key.get())
            bits = text_to_binary(encrypted)
            stego = hide_text_in_container(bits, container)

            write_file(self.output_path.get(), stego)
            self.status_var.set("Сообщение успешно скрыто")
            messagebox.showinfo("Готово", "Сообщение скрыто успешно")

        except Exception as exc:
            self.status_var.set("Ошибка")
            messagebox.showerror("Ошибка", str(exc))

    def _extract_message(self) -> None:
        """Извлечь сообщение: извлечение битов -> декодирование -> дешифрование.

        Результат сохраняется в файл, а первые 1000 символов показываются
        в области предпросмотра.

        Raises:
            ValueError: Если ключ некорректен или формат скрытых данных неверный.
            OSError: Если возникли ошибки ввода-вывода при чтении/записи файлов.
        """
        try:
            if not validate_key(self.extract_key.get()):
                raise ValueError("Недопустимый ключ")

            stego = read_file(self.stego_path.get())
            bits = extract_text_from_container(stego)
            encrypted = binary_to_text(bits)
            text = vigenere_decrypt(encrypted, self.extract_key.get())

            write_file(self.extract_output.get(), text)

            self.preview.delete("1.0", tk.END)
            self.preview.insert(tk.END, text[:1000])

            self.status_var.set("Сообщение извлечено")
            messagebox.showinfo("Готово", "Сообщение извлечено успешно")

        except Exception as exc:
            self.status_var.set("Ошибка")
            messagebox.showerror("Ошибка", str(exc))


def run_gui() -> None:
    """Запустить графическое приложение.

    Создаёт корневое окно Tkinter, инициализирует :class:`SteganographyApp`
    и запускает главный цикл обработки событий.
    """
    root = tk.Tk()
    SteganographyApp(root)
    root.mainloop()


if __name__ == "__main__":
    run_gui()
