"""Tkinter GUI wrapper for ``prompt_generator.py``.

This module provides a graphical interface that lets users pass
arguments to the existing ``prompt_generator.py`` script and view the
command output within the window.
"""

from __future__ import annotations

import shlex
import subprocess
import sys
import threading
from pathlib import Path
import tkinter as tk
from tkinter import messagebox
from tkinter import scrolledtext


class PromptGeneratorGUI:
    """Graphical front-end for ``prompt_generator.py``.

    The GUI lets users type the same command-line arguments they would
    normally pass to ``prompt_generator.py``. When the "Generate" button
    is pressed the script is executed in a background thread and the
    resulting output is rendered inside the text area.
    """

    def __init__(self) -> None:
        self.root = tk.Tk()
        self.root.title("Prompt Generator")
        self._script_path = Path(__file__).resolve().parent / "prompt_generator.py"

        self._build_widgets()

    def _build_widgets(self) -> None:
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(1, weight=1)

        instructions = (
            "prompt_generator.py に渡すコマンドライン引数を入力してください。\n"
            "例: --input data.json --count 5"
        )
        self.instructions_label = tk.Label(self.root, text=instructions, anchor="w", justify="left")
        self.instructions_label.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 5))

        self.input_entry = tk.Entry(self.root)
        self.input_entry.grid(row=1, column=0, sticky="ew", padx=10)
        self.input_entry.bind("<Return>", lambda event: self.execute())

        self.run_button = tk.Button(self.root, text="Generate", command=self.execute)
        self.run_button.grid(row=2, column=0, sticky="ew", padx=10, pady=5)

        self.output_text = scrolledtext.ScrolledText(self.root, wrap=tk.WORD, height=15)
        self.output_text.grid(row=3, column=0, sticky="nsew", padx=10, pady=(0, 10))
        self.output_text.configure(state=tk.DISABLED)

    def execute(self) -> None:
        """Start executing prompt_generator.py with the provided arguments."""
        if not self._script_path.exists():
            messagebox.showerror(
                "Error",
                f"prompt_generator.py が見つかりませんでした。\n{self._script_path}"
            )
            return

        raw_args = self.input_entry.get().strip()
        try:
            args = shlex.split(raw_args)
        except ValueError as error:
            messagebox.showerror("引数エラー", f"引数の解析に失敗しました: {error}")
            return

        self.run_button.configure(state=tk.DISABLED)
        self._set_output("実行中...\n")

        thread = threading.Thread(target=self._run_script, args=(args,), daemon=True)
        thread.start()

    def _run_script(self, args: list[str]) -> None:
        command = [sys.executable, str(self._script_path), *args]
        try:
            completed = subprocess.run(
                command,
                capture_output=True,
                text=True,
                check=False,
            )
        except OSError as error:
            self._append_output(f"実行に失敗しました: {error}\n")
            self._on_execution_finished()
            return

        output_parts = []
        if completed.stdout:
            output_parts.append(completed.stdout)
        if completed.stderr:
            output_parts.append("[stderr]\n" + completed.stderr)
        if not output_parts:
            output_parts.append("出力はありませんでした。\n")
        output_parts.append(f"\n終了コード: {completed.returncode}\n")

        self._set_output("".join(output_parts))
        self._on_execution_finished()

    def _set_output(self, text: str) -> None:
        self.output_text.configure(state=tk.NORMAL)
        self.output_text.delete("1.0", tk.END)
        self.output_text.insert(tk.END, text)
        self.output_text.configure(state=tk.DISABLED)

    def _append_output(self, text: str) -> None:
        self.output_text.configure(state=tk.NORMAL)
        self.output_text.insert(tk.END, text)
        self.output_text.configure(state=tk.DISABLED)

    def _on_execution_finished(self) -> None:
        self.run_button.configure(state=tk.NORMAL)

    def run(self) -> None:
        """Start the Tkinter main loop."""
        self.root.mainloop()


if __name__ == "__main__":
    gui = PromptGeneratorGUI()
    gui.run()
