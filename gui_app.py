#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TS文件翻译工具 - 图形界面
基于PyQt5实现的用户友好界面
"""

import sys
import os
import logging
from pathlib import Path
from typing import List, Dict

# PyQt5导入
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QLineEdit, QPushButton, 
                             QTextEdit, QProgressBar, QFileDialog, QMessageBox,
                             QGroupBox, QComboBox, QCheckBox, QTabWidget,
                             QListWidget, QListWidgetItem, QSplitter, QDesktopWidget)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont, QPalette, QColor

# 项目模块导入
from main import TsTranslator
from batch_translator import BatchTranslator


class TranslationThread(QThread):
    """翻译线程类，用于后台执行翻译任务"""
    
    # 信号定义
    progress_updated = pyqtSignal(int, str)  # 进度值, 状态信息
    translation_finished = pyqtSignal(dict)  # 翻译结果
    error_occurred = pyqtSignal(str)  # 错误信息
    
    def __init__(self, translator: TsTranslator, input_file: str, 
                 output_file: str, skip_translated: bool = True):
        super().__init__()
        self.translator = translator
        self.input_file = input_file
        self.output_file = output_file
        self.skip_translated = skip_translated
    
    def run(self):
        """执行翻译任务"""
        try:
            # 更新进度
            self.progress_updated.emit(10, "正在解析TS文件...")
            
            # 执行翻译
            self.progress_updated.emit(30, "正在翻译文本...")
            # 获取语言设置（需要从主窗口获取）
            from_lang = "en"  # 默认源语言
            to_lang = "zh"     # 默认目标语言
            stats = self.translator.translate_ts_file(
                self.input_file, 
                self.output_file, 
                from_lang,
                to_lang,
                self.skip_translated
            )
            
            self.progress_updated.emit(100, "翻译完成!")
            self.translation_finished.emit(stats)
            
        except Exception as e:
            self.error_occurred.emit(str(e))


class BatchTranslationThread(QThread):
    """批量翻译线程类"""
    
    progress_updated = pyqtSignal(int, str, str)  # 进度值, 状态信息, 当前文件
    batch_finished = pyqtSignal(dict)  # 批量翻译结果
    error_occurred = pyqtSignal(str, str)  # 错误信息, 文件路径
    
    def __init__(self, batch_translator: BatchTranslator, input_paths: List[str], 
                 output_dir: str = None, skip_translated: bool = True):
        super().__init__()
        self.batch_translator = batch_translator
        self.input_paths = input_paths
        self.output_dir = output_dir
        self.skip_translated = skip_translated
    
    def run(self):
        """执行批量翻译"""
        try:
            results = {}
            all_ts_files = []
            
            # 收集所有TS文件
            for path in self.input_paths:
                path_obj = Path(path)
                if path_obj.is_file() and path_obj.suffix.lower() == '.ts':
                    all_ts_files.append(path_obj)
                elif path_obj.is_dir():
                    all_ts_files.extend(self.batch_translator.find_ts_files(str(path_obj)))
            
            total_files = len(all_ts_files)
            
            for i, ts_file in enumerate(all_ts_files):
                current_file = str(ts_file)
                
                # 更新进度
                progress = int((i / total_files) * 100)
                self.progress_updated.emit(progress, f"处理文件 {i+1}/{total_files}", current_file)
                
                try:
                    # 确定输出路径
                    if self.output_dir:
                        output_path = Path(self.output_dir) / ts_file.name
                    else:
                        output_path = ts_file.parent / f"{ts_file.stem}_{self.batch_translator.target_lang}.ts"
                    
                    # 执行翻译
                    stats = self.batch_translator.translator.translate_ts_file(
                        str(ts_file), 
                        str(output_path), 
                        self.batch_translator.source_lang,
                        self.batch_translator.target_lang,
                        self.skip_translated
                    )
                    
                    results[current_file] = {
                        'output_file': str(output_path),
                        'stats': stats,
                        'status': 'success'
                    }
                    
                except Exception as e:
                    results[current_file] = {
                        'output_file': None,
                        'stats': None,
                        'status': 'failed',
                        'error': str(e)
                    }
                    self.error_occurred.emit(str(e), current_file)
            
            self.batch_finished.emit(results)
            
        except Exception as e:
            self.error_occurred.emit(str(e), "批量处理")


class TranslationApp(QMainWindow):
    """主应用程序窗口"""
    
    def __init__(self):
        super().__init__()
        self.translator = None
        self.batch_translator = None
        self.translation_thread = None
        self.batch_thread = None
        self.first_time_enter_settings = True  # 标记首次进入设置
        
        self.init_ui()
        self.setup_translator()
    
    def center(self):
        """将窗口居中显示"""
        # 获取屏幕的几何信息
        screen = QDesktopWidget().screenGeometry()
        # 获取窗口的几何信息
        window = self.geometry()
        # 计算居中的位置
        x = (screen.width() - window.width()) // 2
        y = (screen.height() - window.height()) // 2
        # 移动窗口到居中位置
        self.move(x, y)
    
    def apply_styles(self):
        """应用QSS样式"""
        try:
            # 读取QSS样式文件
            stylesheet_path = Path(__file__).parent / "styles.qss"
            if stylesheet_path.exists():
                with open(stylesheet_path, 'r', encoding='utf-8') as f:
                    stylesheet = f.read()
                self.setStyleSheet(stylesheet)
                print("QSS样式应用成功")
            else:
                # 如果样式文件不存在，使用内置的默认样式
                self.apply_default_styles()
        except Exception as e:
            print(f"应用样式失败: {e}")
            # 使用内置的默认样式作为备选
            self.apply_default_styles()
    
    def apply_default_styles(self):
        """应用内置的默认样式"""
        default_styles = """
        QMainWindow {
            background-color: #f5f7fa;
            font-family: "Microsoft YaHei", sans-serif;
        }
        QTabWidget::pane {
            border: 1px solid #d1d9e6;
            border-radius: 8px;
        }
        QTabBar::tab {
            background-color: #e8ecef;
            padding: 8px 16px;
            border-radius: 6px;
        }
        QTabBar::tab:selected {
            background-color: #3498db;
            color: white;
        }
        QPushButton {
            background-color: #3498db;
            color: white;
            border-radius: 6px;
            padding: 8px 16px;
        }
        QPushButton:hover {
            background-color: #2980b9;
        }
        QGroupBox {
            border: 2px solid #d1d9e6;
            border-radius: 8px;
            margin-top: 10px;
        }
        QLineEdit, QComboBox, QTextEdit, QListWidget {
            border: 2px solid #d1d9e6;
            border-radius: 6px;
            padding: 8px;
        }
        QProgressBar {
            border: 2px solid #d1d9e6;
            border-radius: 6px;
        }
        QProgressBar::chunk {
            background-color: #3498db;
            border-radius: 4px;
        }
        """
        self.setStyleSheet(default_styles)

    def init_ui(self):
        """初始化用户界面"""
        self.setWindowTitle("TS文件翻译工具")
        # 设置窗口大小
        self.resize(300, 700)
        
        # 让窗口居中显示
        self.center()
        
        # 应用QSS样式
        self.apply_styles()
        
        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 创建主布局
        main_layout = QVBoxLayout(central_widget)
        
        # 创建标签页
        tab_widget = QTabWidget()
        main_layout.addWidget(tab_widget)
        
        # 单文件翻译标签页
        single_tab = self.create_single_translation_tab()
        tab_widget.addTab(single_tab, "单文件翻译")
        
        # 批量翻译标签页
        batch_tab = self.create_batch_translation_tab()
        tab_widget.addTab(batch_tab, "批量翻译")
        
        # 设置标签页
        settings_tab = self.create_settings_tab()
        tab_widget.addTab(settings_tab, "设置")
        
        # 连接标签页切换事件
        tab_widget.currentChanged.connect(self.on_tab_changed)
        
        # 保存标签页组件引用
        self.tab_widget = tab_widget
        
        # 状态栏
        self.statusBar().showMessage("就绪")
    
    def create_single_translation_tab(self) -> QWidget:
        """创建单文件翻译标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # 文件选择组
        file_group = QGroupBox("文件选择")
        file_layout = QVBoxLayout(file_group)
        
        # 输入文件
        input_layout = QHBoxLayout()
        input_layout.addWidget(QLabel("输入文件:"))
        self.input_file_edit = QLineEdit()
        self.input_file_edit.setPlaceholderText("选择TS文件...")
        input_layout.addWidget(self.input_file_edit)
        self.input_file_btn = QPushButton("浏览...")
        self.input_file_btn.clicked.connect(self.select_input_file)
        input_layout.addWidget(self.input_file_btn)
        file_layout.addLayout(input_layout)
        
        # 输出文件
        output_layout = QHBoxLayout()
        output_layout.addWidget(QLabel("输出文件:"))
        self.output_file_edit = QLineEdit()
        self.output_file_edit.setPlaceholderText("输出文件路径...")
        output_layout.addWidget(self.output_file_edit)
        self.output_file_btn = QPushButton("浏览...")
        self.output_file_btn.clicked.connect(self.select_output_file)
        output_layout.addWidget(self.output_file_btn)
        file_layout.addLayout(output_layout)
        
        layout.addWidget(file_group)
        
        # 翻译设置组
        settings_group = QGroupBox("翻译设置")
        settings_layout = QHBoxLayout(settings_group)
        
        settings_layout.addWidget(QLabel("源语言:"))
        self.source_lang_combo = QComboBox()
        self.source_lang_combo.addItems(["en", "ja", "ko", "fr", "de", "es"])
        settings_layout.addWidget(self.source_lang_combo)
        
        settings_layout.addWidget(QLabel("目标语言:"))
        self.target_lang_combo = QComboBox()
        self.target_lang_combo.addItems(["zh", "en", "ja", "ko", "fr", "de", "es"])
        self.target_lang_combo.setCurrentText("zh")
        settings_layout.addWidget(self.target_lang_combo)
        
        self.skip_translated_check = QCheckBox("跳过已有翻译")
        self.skip_translated_check.setChecked(True)
        settings_layout.addWidget(self.skip_translated_check)
        
        layout.addWidget(settings_group)
        
        # 进度显示
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        self.status_text = QTextEdit()
        self.status_text.setMaximumHeight(100)
        self.status_text.setReadOnly(True)
        layout.addWidget(self.status_text)
        
        # 按钮
        button_layout = QHBoxLayout()
        self.translate_btn = QPushButton("开始翻译")
        self.translate_btn.clicked.connect(self.start_translation)
        button_layout.addWidget(self.translate_btn)
        
        self.clear_btn = QPushButton("清空日志")
        self.clear_btn.clicked.connect(self.clear_log)
        button_layout.addWidget(self.clear_btn)
        
        layout.addLayout(button_layout)
        
        # 添加垂直弹簧，优化布局
        layout.addStretch(1)
        
        return widget
    
    def create_batch_translation_tab(self) -> QWidget:
        """创建批量翻译标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # 文件列表组
        file_group = QGroupBox("文件列表")
        file_layout = QVBoxLayout(file_group)
        
        # 文件列表
        list_layout = QHBoxLayout()
        self.file_list = QListWidget()
        list_layout.addWidget(self.file_list)
        
        # 按钮组
        button_layout = QVBoxLayout()
        self.add_files_btn = QPushButton("添加文件")
        self.add_files_btn.clicked.connect(self.add_files)
        button_layout.addWidget(self.add_files_btn)
        
        self.add_folder_btn = QPushButton("添加文件夹")
        self.add_folder_btn.clicked.connect(self.add_folder)
        button_layout.addWidget(self.add_folder_btn)
        
        self.remove_file_btn = QPushButton("移除选中")
        self.remove_file_btn.clicked.connect(self.remove_file)
        button_layout.addWidget(self.remove_file_btn)
        
        self.clear_list_btn = QPushButton("清空列表")
        self.clear_list_btn.clicked.connect(self.clear_file_list)
        button_layout.addWidget(self.clear_list_btn)
        
        list_layout.addLayout(button_layout)
        file_layout.addLayout(list_layout)
        
        layout.addWidget(file_group)
        
        # 输出设置
        output_group = QGroupBox("输出设置")
        output_layout = QHBoxLayout(output_group)
        
        output_layout.addWidget(QLabel("输出目录:"))
        self.batch_output_edit = QLineEdit()
        self.batch_output_edit.setPlaceholderText("选择输出目录...")
        output_layout.addWidget(self.batch_output_edit)
        self.batch_output_btn = QPushButton("浏览...")
        self.batch_output_btn.clicked.connect(self.select_batch_output_dir)
        output_layout.addWidget(self.batch_output_btn)
        
        layout.addWidget(output_group)
        
        # 批量进度
        self.batch_progress_bar = QProgressBar()
        self.batch_progress_bar.setVisible(False)
        layout.addWidget(self.batch_progress_bar)
        
        self.batch_status_text = QTextEdit()
        self.batch_status_text.setMaximumHeight(100)
        self.batch_status_text.setReadOnly(True)
        layout.addWidget(self.batch_status_text)
        
        # 批量翻译按钮
        batch_button_layout = QHBoxLayout()
        self.batch_translate_btn = QPushButton("开始批量翻译")
        self.batch_translate_btn.clicked.connect(self.start_batch_translation)
        batch_button_layout.addWidget(self.batch_translate_btn)
        
        layout.addLayout(batch_button_layout)
        
        # 添加垂直弹簧，优化布局
        layout.addStretch(1)
        
        return widget
    
    def create_settings_tab(self) -> QWidget:
        """创建设置标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # 翻译包管理组
        package_group = QGroupBox("翻译包管理")
        package_layout = QVBoxLayout(package_group)
        
        # 已安装翻译包
        installed_group = QGroupBox("已安装翻译包")
        installed_layout = QVBoxLayout(installed_group)
        
        installed_info = QLabel("当前已安装的翻译包:")
        installed_layout.addWidget(installed_info)
        
        self.package_list = QListWidget()
        installed_layout.addWidget(self.package_list)
        
        refresh_btn = QPushButton("刷新已安装包列表")
        refresh_btn.clicked.connect(self.refresh_packages)
        installed_layout.addWidget(refresh_btn)
        
        package_layout.addWidget(installed_group)
        
        # 可安装翻译包
        available_group = QGroupBox("可安装翻译包")
        available_layout = QVBoxLayout(available_group)
        
        available_info = QLabel("可安装的翻译包:")
        available_layout.addWidget(available_info)
        
        # 语言选择区域
        lang_selection_layout = QHBoxLayout()
        
        lang_selection_layout.addWidget(QLabel("源语言:"))
        self.available_source_combo = QComboBox()
        self.available_source_combo.addItems(["", "en", "zh", "ja", "ko", "fr", "de", "es", "ru", "pt", "it"])
        lang_selection_layout.addWidget(self.available_source_combo)
        
        lang_selection_layout.addWidget(QLabel("目标语言:"))
        self.available_target_combo = QComboBox()
        self.available_target_combo.addItems(["", "zh", "en", "ja", "ko", "fr", "de", "es", "ru", "pt", "it"])
        lang_selection_layout.addWidget(self.available_target_combo)
        
        available_layout.addLayout(lang_selection_layout)
        
        # 包列表和安装按钮
        self.available_package_list = QListWidget()
        self.available_package_list.setSelectionMode(QListWidget.MultiSelection)
        available_layout.addWidget(self.available_package_list)

        install_buttons_layout = QHBoxLayout()

        self.refresh_available_btn = QPushButton("刷新可用包")
        self.refresh_available_btn.clicked.connect(self.refresh_available_packages)
        install_buttons_layout.addWidget(self.refresh_available_btn)

        self.install_selected_btn = QPushButton("安装选中包")
        self.install_selected_btn.clicked.connect(self.install_selected_package)
        install_buttons_layout.addWidget(self.install_selected_btn)

        available_layout.addLayout(install_buttons_layout)
        
        # 连接语言选择改变信号
        self.available_source_combo.currentTextChanged.connect(self.on_language_selection_changed)
        self.available_target_combo.currentTextChanged.connect(self.on_language_selection_changed)
        
        package_layout.addWidget(available_group)
        
        layout.addWidget(package_group)
        
        # 关于信息
        about_group = QGroupBox("关于")
        about_layout = QVBoxLayout(about_group)
        
        about_text = QLabel("""
        <b>TS文件翻译工具</b><br>
        版本: 1.0.0<br>
        基于Argos Translate实现本地翻译<br>
        支持多种语言间的TS文件翻译<br>
        """)
        about_text.setAlignment(Qt.AlignLeft)
        about_layout.addWidget(about_text)
        
        layout.addWidget(about_group)
        
        return widget
    
    def on_tab_changed(self, index):
        """标签页切换事件处理"""
        # 获取当前标签页的文本
        current_tab_text = self.tab_widget.tabText(index)
        
        # 如果是设置标签页且是首次进入
        if current_tab_text == "设置" and self.first_time_enter_settings:
            # 标记为已进入过设置标签页
            self.first_time_enter_settings = False
            # 不再自动刷新，避免卡顿
            self.statusBar().showMessage("请手动点击'刷新可用包'按钮查看翻译包列表")
    
    def setup_translator(self):
        """设置翻译器"""
        try:
            source_lang = self.source_lang_combo.currentText()
            target_lang = self.target_lang_combo.currentText()
            self.translator = TsTranslator()
            self.batch_translator = BatchTranslator(source_lang, target_lang)
            self.statusBar().showMessage("翻译器初始化成功")
        except Exception as e:
            QMessageBox.warning(self, "错误", f"翻译器初始化失败: {str(e)}")
    
    def select_input_file(self):
        """选择输入文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择TS文件", "", "TS Files (*.ts)"
        )
        if file_path:
            self.input_file_edit.setText(file_path)
            # 自动生成输出文件名
            input_path = Path(file_path)
            output_path = input_path.parent / f"{input_path.stem}_{self.target_lang_combo.currentText()}.ts"
            self.output_file_edit.setText(str(output_path))
    
    def select_output_file(self):
        """选择输出文件"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "保存翻译文件", "", "TS Files (*.ts)"
        )
        if file_path:
            self.output_file_edit.setText(file_path)
    
    def select_batch_output_dir(self):
        """选择批量输出目录"""
        dir_path = QFileDialog.getExistingDirectory(self, "选择输出目录")
        if dir_path:
            self.batch_output_edit.setText(dir_path)
    
    def add_files(self):
        """添加文件到列表"""
        files, _ = QFileDialog.getOpenFileNames(
            self, "选择TS文件", "", "TS Files (*.ts)"
        )
        for file_path in files:
            self.file_list.addItem(file_path)
    
    def add_folder(self):
        """添加文件夹到列表"""
        dir_path = QFileDialog.getExistingDirectory(self, "选择文件夹")
        if dir_path:
            self.file_list.addItem(f"[目录] {dir_path}")
    
    def remove_file(self):
        """移除选中文件"""
        current_row = self.file_list.currentRow()
        if current_row >= 0:
            self.file_list.takeItem(current_row)
    
    def clear_file_list(self):
        """清空文件列表"""
        self.file_list.clear()
    
    def refresh_packages(self):
        """刷新翻译包列表"""
        try:
            self.package_list.clear()
            if self.translator:
                packages = self.translator.get_installed_packages()
                for pkg in packages:
                    self.package_list.addItem(f"{pkg.from_code} -> {pkg.to_code}")
        except Exception as e:
            QMessageBox.warning(self, "错误", f"刷新包列表失败: {str(e)}")
    
    def show_install_dialog(self):
        """显示安装包对话框"""
        QMessageBox.information(self, "信息", "请在下方选择语言包并点击安装按钮") 
    
    def refresh_available_packages(self):
        """刷新可用翻译包列表"""
        try:
            self.available_package_list.clear()
            if self.translator:
                packages = self.translator.get_available_packages()
                installed_packages = self.translator.get_installed_packages()
                
                # 过滤包，只显示与当前选择语言相关的包
                source_lang = self.available_source_combo.currentText()
                target_lang = self.available_target_combo.currentText()
                
                filtered_packages = []
                for pkg in packages:
                    # 如果选择了特定语言，只显示匹配的包
                    if source_lang and target_lang:
                        if pkg.from_code == source_lang and pkg.to_code == target_lang:
                            filtered_packages.append(pkg)
                    else:
                        # 如果没有选择特定语言，显示所有包
                        filtered_packages.append(pkg)
                
                # 获取已安装包的标识
                installed_package_ids = set()
                for installed_pkg in installed_packages:
                    if hasattr(installed_pkg, 'from_code') and hasattr(installed_pkg, 'to_code'):
                        installed_package_ids.add(f"{installed_pkg.from_code}->{installed_pkg.to_code}")
                
                for pkg in filtered_packages:
                    item_text = f"{pkg.from_code} -> {pkg.to_code}"
                    if hasattr(pkg, 'package_name'):
                        item_text += f" ({pkg.package_name})"
                    
                    item = QListWidgetItem(item_text)
                    
                    # 检查是否已安装
                    package_id = f"{pkg.from_code}->{pkg.to_code}"
                    if package_id in installed_package_ids:
                        # 已安装的包：置灰且不可勾选
                        item.setFlags(item.flags() & ~Qt.ItemIsEnabled)
                        item.setForeground(QColor(128, 128, 128))  # 灰色
                        item.setCheckState(Qt.Unchecked)  # 未勾选
                    else:
                        # 未安装的包：正常显示且默认不勾选
                        item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
                        item.setCheckState(Qt.Unchecked)  # 默认不勾选
                    
                    self.available_package_list.addItem(item)
                
                self.statusBar().showMessage(f"找到 {len(filtered_packages)} 个可用翻译包")
        except Exception as e:
            QMessageBox.warning(self, "错误", f"刷新可用包列表失败: {str(e)}")
    
    def on_language_selection_changed(self):
        """当语言选择改变时启用/禁用刷新按钮"""
        # 只有当两个语言都选择了才启用刷新按钮
        source_lang = self.available_source_combo.currentText()
        target_lang = self.available_target_combo.currentText()
        
        if source_lang and target_lang:
            self.refresh_available_btn.setEnabled(True)
        else:
            self.refresh_available_btn.setEnabled(False)
    
    def install_selected_package(self):
        """安装勾选的翻译包"""
        try:
            # 获取所有勾选的包
            selected_packages = []
            for i in range(self.available_package_list.count()):
                item = self.available_package_list.item(i)
                if item.checkState() == Qt.Checked and item.isEnabled():
                    # 从列表项文本中提取语言代码
                    item_text = item.text()
                    parts = item_text.split(" -> ")
                    if len(parts) >= 2:
                        from_lang = parts[0].strip()
                        to_lang_parts = parts[1].split(" (")
                        to_lang = to_lang_parts[0].strip()
                        selected_packages.append((from_lang, to_lang))
            
            if not selected_packages:
                QMessageBox.warning(self, "警告", "请先勾选要安装的翻译包")
                return
            
            # 显示确认对话框
            package_list = "\n".join([f"{from_lang} -> {to_lang}" for from_lang, to_lang in selected_packages])
            reply = QMessageBox.question(self, "确认安装", 
                                       f"确定要安装以下 {len(selected_packages)} 个翻译包吗？\n\n{package_list}\n\n这可能需要一些时间，请耐心等待。",
                                       QMessageBox.Yes | QMessageBox.No)
            
            if reply == QMessageBox.Yes:
                # 批量安装包
                if self.translator:
                    success_count = 0
                    failed_packages = []
                    
                    for from_lang, to_lang in selected_packages:
                        try:
                            success = self.translator.install_package_by_codes(from_lang, to_lang)
                            if success:
                                success_count += 1
                            else:
                                failed_packages.append(f"{from_lang} -> {to_lang}")
                        except Exception as e:
                            failed_packages.append(f"{from_lang} -> {to_lang} (错误: {str(e)})")
                    
                    # 显示安装结果
                    if failed_packages:
                        failed_list = "\n".join(failed_packages)
                        QMessageBox.information(self, "安装完成", 
                                              f"成功安装 {success_count} 个包，失败 {len(failed_packages)} 个包:\n{failed_list}")
                    else:
                        QMessageBox.information(self, "成功", f"所有 {success_count} 个翻译包安装成功！")
                    
                    # 刷新包列表
                    self.refresh_packages()
                    self.refresh_available_packages()
        except Exception as e:
            QMessageBox.critical(self, "错误", f"安装翻译包失败: {str(e)}") 
    
    def start_translation(self):
        """开始翻译"""
        input_file = self.input_file_edit.text()
        output_file = self.output_file_edit.text()
        
        if not input_file or not output_file:
            QMessageBox.warning(self, "警告", "请选择输入和输出文件")
            return
        
        if not Path(input_file).exists():
            QMessageBox.warning(self, "错误", "输入文件不存在")
            return
        
        # 更新翻译器设置
        self.setup_translator()
        
        # 创建并启动翻译线程
        self.translation_thread = TranslationThread(
            self.translator,
            input_file,
            output_file,
            self.skip_translated_check.isChecked()
        )
        
        self.translation_thread.progress_updated.connect(self.update_progress)
        self.translation_thread.translation_finished.connect(self.translation_completed)
        self.translation_thread.error_occurred.connect(self.translation_error)
        
        self.progress_bar.setVisible(True)
        self.translate_btn.setEnabled(False)
        self.status_text.append("开始翻译...")
        
        self.translation_thread.start()
    
    def start_batch_translation(self):
        """开始批量翻译"""
        if self.file_list.count() == 0:
            QMessageBox.warning(self, "警告", "请添加要翻译的文件或文件夹")
            return
        
        # 收集文件路径
        input_paths = []
        for i in range(self.file_list.count()):
            item_text = self.file_list.item(i).text()
            if item_text.startswith("[目录]"):
                input_paths.append(item_text[6:])  # 移除"[目录] "前缀
            else:
                input_paths.append(item_text)
        
        # 更新翻译器设置
        self.setup_translator()
        
        # 创建并启动批量翻译线程
        output_dir = self.batch_output_edit.text() or None
        self.batch_thread = BatchTranslationThread(
            self.batch_translator,
            input_paths,
            output_dir,
            True
        )
        
        self.batch_thread.progress_updated.connect(self.update_batch_progress)
        self.batch_thread.batch_finished.connect(self.batch_translation_completed)
        self.batch_thread.error_occurred.connect(self.batch_translation_error)
        
        self.batch_progress_bar.setVisible(True)
        self.batch_translate_btn.setEnabled(False)
        self.batch_status_text.append("开始批量翻译...")
        
        self.batch_thread.start()
    
    def update_progress(self, value: int, message: str):
        """更新进度"""
        self.progress_bar.setValue(value)
        self.status_text.append(message)
        self.statusBar().showMessage(message)
    
    def update_batch_progress(self, value: int, message: str, current_file: str):
        """更新批量进度"""
        self.batch_progress_bar.setValue(value)
        self.batch_status_text.append(f"{message}: {current_file}")
    
    def translation_completed(self, stats: dict):
        """翻译完成"""
        self.progress_bar.setValue(100)
        self.translate_btn.setEnabled(True)
        
        if stats.get('success'):
            message = f"翻译完成! 总条目: {stats['total_count']}, 翻译: {stats['translated_count']}, 跳过: {stats['skipped_count']}"
        else:
            message = f"翻译失败: {stats.get('error', '未知错误')}"
        
        self.status_text.append(message)
        QMessageBox.information(self, "完成", message)
    
    def batch_translation_completed(self, results: dict):
        """批量翻译完成"""
        self.batch_progress_bar.setValue(100)
        self.batch_translate_btn.setEnabled(True)
        
        success_count = sum(1 for r in results.values() if r['status'] == 'success')
        failed_count = sum(1 for r in results.values() if r['status'] == 'failed')
        
        message = f"批量翻译完成! 成功: {success_count}, 失败: {failed_count}"
        self.batch_status_text.append(message)
        QMessageBox.information(self, "完成", message)
    
    def translation_error(self, error_message: str):
        """翻译错误"""
        self.translate_btn.setEnabled(True)
        self.status_text.append(f"错误: {error_message}")
        QMessageBox.critical(self, "错误", f"翻译失败: {error_message}")
    
    def batch_translation_error(self, error_message: str, file_path: str):
        """批量翻译错误"""
        self.batch_status_text.append(f"错误 ({file_path}): {error_message}")
    
    def clear_log(self):
        """清空日志"""
        self.status_text.clear()


def main():
    """主函数"""
    app = QApplication(sys.argv)
    
    # 设置应用程序样式
    app.setStyle('Fusion')
    
    # 创建主窗口
    window = TranslationApp()
    window.show()
    
    # 运行应用程序
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()