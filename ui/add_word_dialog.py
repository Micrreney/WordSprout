"""添加/编辑单词对话框。"""

from PyQt5.QtWidgets import (
    QDialog, QDialogButtonBox, QFormLayout, QLineEdit, QVBoxLayout,
)


class AddWordDialog(QDialog):
    def __init__(self, parent=None, word: str = "", definition: str = "", phonetic: str = "") -> None:
        super().__init__(parent)
        self.setWindowTitle("添加单词" if not word else "编辑单词")
        self.resize(400, 220)

        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.edit_word = QLineEdit(word)
        self.edit_definition = QLineEdit(definition)
        self.edit_phonetic = QLineEdit(phonetic)

        self.edit_word.setPlaceholderText("输入单词...")
        self.edit_definition.setPlaceholderText("输入释义...")
        self.edit_phonetic.setPlaceholderText("输入音标（可选）...")

        form.addRow("单词:", self.edit_word)
        form.addRow("释义:", self.edit_definition)
        form.addRow("音标:", self.edit_phonetic)
        layout.addLayout(form)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def get_data(self) -> tuple[str, str, str]:
        return (
            self.edit_word.text().strip(),
            self.edit_definition.text().strip(),
            self.edit_phonetic.text().strip(),
        )
