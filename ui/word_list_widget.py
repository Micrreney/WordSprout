"""词库管理界面：列表管理 + 单词增删改查 + 导入导出。"""

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QComboBox, QFileDialog, QGroupBox, QHBoxLayout, QHeaderView, QInputDialog,
    QLabel, QLineEdit, QListWidget, QListWidgetItem, QMessageBox, QPushButton,
    QSplitter, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget,
)

from database.models import Word, WordList
from ui.add_word_dialog import AddWordDialog
from utils.import_export import (
    export_words_csv, export_words_json, import_words_csv, import_words_json,
)


class WordListWidget(QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._current_list_id: int | None = None

        layout = QVBoxLayout(self)

        # --- 顶部工具栏 ---
        toolbar = QHBoxLayout()

        self.cmb_lists = QComboBox()
        self.cmb_lists.setMinimumWidth(160)
        self.cmb_lists.currentIndexChanged.connect(self._on_list_changed)
        toolbar.addWidget(QLabel("单词列表:"))
        toolbar.addWidget(self.cmb_lists)

        self.btn_new_list = QPushButton("+ 新建列表")
        self.btn_new_list.clicked.connect(self._new_list)
        toolbar.addWidget(self.btn_new_list)

        self.btn_rename = QPushButton("重命名")
        self.btn_rename.clicked.connect(self._rename_list)
        toolbar.addWidget(self.btn_rename)

        self.btn_delete_list = QPushButton("删除列表")
        self.btn_delete_list.clicked.connect(self._delete_list)
        toolbar.addWidget(self.btn_delete_list)

        toolbar.addStretch()
        layout.addLayout(toolbar)

        # --- 搜索栏 ---
        search_bar = QHBoxLayout()
        search_bar.addWidget(QLabel("搜索:"))
        self.edit_search = QLineEdit()
        self.edit_search.setPlaceholderText("搜索单词或释义...")
        self.edit_search.textChanged.connect(self._refresh_word_table)
        search_bar.addWidget(self.edit_search)
        layout.addLayout(search_bar)

        # --- 主体：表格 + 操作按钮 ---
        body = QHBoxLayout()

        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["单词", "释义", "音标"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.cellDoubleClicked.connect(self._on_word_double_clicked)
        body.addWidget(self.table, 1)

        btn_panel = QVBoxLayout()
        self.btn_add = QPushButton("➕ 添加单词")
        self.btn_add.clicked.connect(self._add_word)
        self.btn_batch = QPushButton("📝 批量添加")
        self.btn_batch.clicked.connect(self._batch_add)
        self.btn_edit = QPushButton("✏️ 编辑")
        self.btn_edit.clicked.connect(self._edit_word)
        self.btn_delete = QPushButton("🗑️ 删除")
        self.btn_delete.clicked.connect(self._delete_word)
        self.btn_import = QPushButton("📥 导入")
        self.btn_import.clicked.connect(self._import_words)
        self.btn_export = QPushButton("📤 导出")
        self.btn_export.clicked.connect(self._export_words)

        for b in [self.btn_add, self.btn_batch, self.btn_edit, self.btn_delete,
                  self.btn_import, self.btn_export]:
            b.setMinimumWidth(100)
            btn_panel.addWidget(b)

        btn_panel.addStretch()
        body.addLayout(btn_panel)
        layout.addLayout(body)

        # --- 列表信息 ---
        self.lbl_info = QLabel("")
        layout.addWidget(self.lbl_info)

        # 初始化列表
        self._refresh_lists()

    def _refresh_lists(self) -> None:
        current_name = self.cmb_lists.currentText()
        self.cmb_lists.blockSignals(True)
        self.cmb_lists.clear()
        for wl in WordList.get_all():
            self.cmb_lists.addItem(wl.name, wl.id)
        idx = self.cmb_lists.findText(current_name)
        if idx >= 0:
            self.cmb_lists.setCurrentIndex(idx)
        self.cmb_lists.blockSignals(False)
        self._on_list_changed()

    def _on_list_changed(self) -> None:
        lid = self.cmb_lists.currentData()
        self._current_list_id = lid
        self._refresh_word_table()

    def _refresh_word_table(self) -> None:
        self.table.setRowCount(0)
        if self._current_list_id is None:
            self.lbl_info.setText("")
            return
        search = self.edit_search.text().strip()
        words = Word.get_by_list(self._current_list_id, search)
        self.table.setRowCount(len(words))
        for i, w in enumerate(words):
            self.table.setItem(i, 0, QTableWidgetItem(w.word))
            self.table.setItem(i, 1, QTableWidgetItem(w.definition))
            self.table.setItem(i, 2, QTableWidgetItem(w.phonetic))
            self.table.item(i, 0).setData(Qt.UserRole, w.id)
        self.lbl_info.setText(f"共 {len(words)} 个单词")

    def _new_list(self) -> None:
        name, ok = QInputDialog.getText(self, "新建列表", "列表名称:")
        if ok and name.strip():
            wl = WordList(name=name.strip())
            wl.save()
            self._refresh_lists()
            self.cmb_lists.setCurrentIndex(self.cmb_lists.findText(name.strip()))

    def _rename_list(self) -> None:
        if self._current_list_id is None:
            return
        wl = WordList.get_by_id(self._current_list_id)
        if wl is None:
            return
        name, ok = QInputDialog.getText(self, "重命名列表", "新名称:", text=wl.name)
        if ok and name.strip():
            wl.name = name.strip()
            wl.save()
            self._refresh_lists()

    def _delete_list(self) -> None:
        if self._current_list_id is None:
            return
        wl = WordList.get_by_id(self._current_list_id)
        if wl is None:
            return
        count = Word.count_by_list(self._current_list_id)
        reply = QMessageBox.question(
            self, "删除列表",
            f"确定删除列表「{wl.name}」及其 {count} 个单词吗？此操作不可恢复。",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            wl.delete()
            self._refresh_lists()

    def _add_word(self) -> None:
        if self._current_list_id is None:
            QMessageBox.warning(self, "提示", "请先选择一个单词列表。")
            return
        dlg = AddWordDialog(self)
        if dlg.exec_():
            word, definition, phonetic = dlg.get_data()
            if word:
                w = Word(list_id=self._current_list_id, word=word, definition=definition, phonetic=phonetic)
                w.save()
                self._refresh_word_table()

    def _batch_add(self) -> None:
        if self._current_list_id is None:
            QMessageBox.warning(self, "提示", "请先选择一个单词列表。")
            return
        text, ok = QInputDialog.getMultiLineText(
            self, "批量添加单词", "每行一个单词，格式: 单词,释义,音标\n例如:\nhello,你好,həˈloʊ\nworld,世界,wɜːrld"
        )
        if ok and text.strip():
            count = 0
            for line in text.strip().split("\n"):
                parts = [p.strip() for p in line.split(",", 2)]
                if not parts or not parts[0]:
                    continue
                w = Word(
                    list_id=self._current_list_id,
                    word=parts[0],
                    definition=parts[1] if len(parts) > 1 else "",
                    phonetic=parts[2] if len(parts) > 2 else "",
                )
                w.save()
                count += 1
            self._refresh_word_table()
            QMessageBox.information(self, "批量添加", f"成功添加 {count} 个单词。")

    def _edit_word(self) -> None:
        row = self.table.currentRow()
        if row < 0:
            return
        word_id = self.table.item(row, 0).data(Qt.UserRole)
        w = Word.get_by_id(word_id)
        if w is None:
            return
        dlg = AddWordDialog(self, w.word, w.definition, w.phonetic)
        if dlg.exec_():
            word, definition, phonetic = dlg.get_data()
            if word:
                w.word = word
                w.definition = definition
                w.phonetic = phonetic
                w.save()
                self._refresh_word_table()

    def _delete_word(self) -> None:
        row = self.table.currentRow()
        if row < 0:
            return
        word_id = self.table.item(row, 0).data(Qt.UserRole)
        w = Word.get_by_id(word_id)
        if w is None:
            return
        reply = QMessageBox.question(
            self, "删除单词", f"确定删除「{w.word}」吗？",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            w.delete()
            self._refresh_word_table()

    def _on_word_double_clicked(self, row: int, col: int) -> None:
        self._edit_word()

    def _import_words(self) -> None:
        if self._current_list_id is None:
            QMessageBox.warning(self, "提示", "请先选择一个单词列表。")
            return
        path, _ = QFileDialog.getOpenFileName(
            self, "导入单词", "", "CSV/JSON 文件 (*.csv *.json);;CSV (*.csv);;JSON (*.json)"
        )
        if not path:
            return
        ext = path.rsplit(".", 1)[-1].lower()
        try:
            if ext == "csv":
                count = import_words_csv(self._current_list_id, path)
            elif ext == "json":
                count = import_words_json(self._current_list_id, path)
            else:
                QMessageBox.warning(self, "错误", f"不支持的文件格式: {ext}")
                return
            self._refresh_word_table()
            QMessageBox.information(self, "导入完成", f"成功导入 {count} 个单词。")
        except Exception as e:
            QMessageBox.critical(self, "导入失败", str(e))

    def _export_words(self) -> None:
        if self._current_list_id is None:
            QMessageBox.warning(self, "提示", "请先选择一个单词列表。")
            return
        wl = WordList.get_by_id(self._current_list_id)
        path, _ = QFileDialog.getSaveFileName(
            self, "导出单词", f"{wl.name}.json" if wl else "words.json",
            "JSON (*.json);;CSV (*.csv)"
        )
        if not path:
            return
        ext = path.rsplit(".", 1)[-1].lower()
        try:
            if ext == "csv":
                count = export_words_csv(self._current_list_id, path)
            elif ext == "json":
                count = export_words_json(self._current_list_id, path)
            else:
                QMessageBox.warning(self, "错误", f"不支持的文件格式: {ext}")
                return
            QMessageBox.information(self, "导出完成", f"成功导出 {count} 个单词。")
        except Exception as e:
            QMessageBox.critical(self, "导出失败", str(e))
