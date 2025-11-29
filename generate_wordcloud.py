#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""词云生成器 - GUI版本"""

import os
import sys
import glob
from wordcloud import WordCloud
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QLabel, QLineEdit, QPushButton,
                             QTextEdit, QFileDialog, QMessageBox, QProgressBar)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QPixmap, QFont
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

def read_all_txt_files(txt_dir):
    """读取指定目录下的所有txt文件并合并文本"""
    if not os.path.exists(txt_dir):
        print(f"错误: 目录不存在 {txt_dir}")
        return ""

    txt_files = glob.glob(os.path.join(txt_dir, "*.txt"))
    all_text = ""

    print(f"找到 {len(txt_files)} 个txt文件")

    for txt_file in txt_files:
        print(f"读取: {os.path.basename(txt_file)}")
        try:
            with open(txt_file, 'r', encoding='utf-8') as f:
                content = f.read()
                all_text += content + "\n"
        except Exception as e:
            print(f"读取文件 {txt_file} 时出错: {e}")

    return all_text

def generate_wordcloud(text, output_path, width=1920, height=1080):
    """生成词云并保存"""
    print("\n正在生成词云...")

    # 尝试使用系统字体，如果失败则使用默认字体
    font_paths = [
        '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
        '/System/Library/Fonts/Arial.ttf',
        '/Windows/Fonts/arial.ttf',
        '/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf',
    ]

    font_path = None
    for fp in font_paths:
        if os.path.exists(fp):
            font_path = fp
            print(f"使用字体: {font_path}")
            break

    if not font_path:
        print("警告: 未找到合适的字体，使用默认字体（可能不支持中文）")

    # 配置词云参数
    wordcloud_kwargs = {
        'width': width,
        'height': height,
        'background_color': 'white',
        'max_words': 500,
        'colormap': 'viridis',
        'relative_scaling': 0.5,
        'random_state': 42
    }

    if font_path:
        wordcloud_kwargs['font_path'] = font_path

    wordcloud = WordCloud(**wordcloud_kwargs).generate(text)

    # 确保输出目录存在
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # 保存词云图片
    wordcloud.to_file(output_path)
    print(f"词云已保存到: {output_path}")

    # 显示词云（可选）
    plt.figure(figsize=(16, 9))
    plt.imshow(wordcloud, interpolation='bilinear')
    plt.axis('off')
    plt.tight_layout(pad=0)

    # 不显示图片，只保存文件
    # plt.show()

    return wordcloud

class WordCloudWorker(QThread):
    """词云生成工作线程"""
    progress = pyqtSignal(int)
    finished = pyqtSignal(object, str)
    error = pyqtSignal(str)

    def __init__(self, txt_dir, output_path):
        super().__init__()
        self.txt_dir = txt_dir
        self.output_path = output_path

    def run(self):
        try:
            self.progress.emit(10)
            all_text = read_all_txt_files(self.txt_dir)
            self.progress.emit(50)

            if not all_text.strip():
                self.error.emit("没有读取到任何文本内容")
                return

            wordcloud = generate_wordcloud(all_text, self.output_path)
            self.progress.emit(100)
            self.finished.emit(wordcloud, all_text)
        except Exception as e:
            self.error.emit(str(e))

class MainWindow(QMainWindow):
    """主窗口"""
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("词云生成器 - Ghost博客分析")
        self.setGeometry(100, 100, 1200, 800)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # 标题
        title_label = QLabel("词云生成器")
        title_label.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)

        # 输入目录选择
        dir_layout = QHBoxLayout()
        dir_label = QLabel("文本目录:")
        self.dir_input = QLineEdit("/home/bakamake/dev/homework/ghost_posts/txt")
        self.dir_button = QPushButton("浏览...")
        self.dir_button.clicked.connect(self.select_directory)
        dir_layout.addWidget(dir_label)
        dir_layout.addWidget(self.dir_input)
        dir_layout.addWidget(self.dir_button)
        layout.addLayout(dir_layout)

        # 输出文件选择
        output_layout = QHBoxLayout()
        output_label = QLabel("输出文件:")
        self.output_input = QLineEdit("/home/bakamake/dev/homework/wordcloud.png")
        self.output_button = QPushButton("浏览...")
        self.output_button.clicked.connect(self.select_output_file)
        output_layout.addWidget(output_label)
        output_layout.addWidget(self.output_input)
        output_layout.addWidget(self.output_button)
        layout.addLayout(output_layout)

        # 生成按钮
        self.generate_button = QPushButton("生成词云")
        self.generate_button.clicked.connect(self.generate_wordcloud)
        self.generate_button.setMinimumHeight(40)
        layout.addWidget(self.generate_button)

        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        # 状态文本
        self.status_text = QTextEdit()
        self.status_text.setMaximumHeight(150)
        self.status_text.setReadOnly(True)
        layout.addWidget(self.status_text)

        # 词云显示区域
        self.wordcloud_canvas = None
        layout.addWidget(QLabel("生成的词云:"))

    def select_directory(self):
        directory = QFileDialog.getExistingDirectory(self, "选择文本目录")
        if directory:
            self.dir_input.setText(directory)

    def select_output_file(self):
        filename, _ = QFileDialog.getSaveFileName(
            self, "保存词云图片", "/home/bakamake/dev/homework/wordcloud.png",
            "PNG Files (*.png);;All Files (*)"
        )
        if filename:
            self.output_input.setText(filename)

    def generate_wordcloud(self):
        txt_dir = self.dir_input.text().strip()
        output_path = self.output_input.text().strip()

        if not txt_dir or not output_path:
            QMessageBox.warning(self, "警告", "请选择文本目录和输出文件")
            return

        if not os.path.exists(txt_dir):
            QMessageBox.warning(self, "警告", f"目录不存在: {txt_dir}")
            return

        self.generate_button.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.status_text.append("开始生成词云...")

        self.worker = WordCloudWorker(txt_dir, output_path)
        self.worker.progress.connect(self.progress_bar.setValue)
        self.worker.finished.connect(self.on_finished)
        self.worker.error.connect(self.on_error)
        self.worker.start()

    def on_finished(self, wordcloud, all_text):
        self.progress_bar.setVisible(False)
        self.generate_button.setEnabled(True)
        self.status_text.append("词云生成完成！")

        # 显示词频统计
        words = wordcloud.words_
        self.status_text.append("\n高频词汇统计:")
        for i, (word, freq) in enumerate(list(words.items())[:20], 1):
            self.status_text.append(f"{i:2d}. {word:20s} - {freq:.3f}")

        # 显示词云图片
        self.display_wordcloud(wordcloud)

        QMessageBox.information(self, "完成", "词云生成成功！")

    def on_error(self, error_msg):
        self.progress_bar.setVisible(False)
        self.generate_button.setEnabled(True)
        self.status_text.append(f"错误: {error_msg}")
        QMessageBox.critical(self, "错误", error_msg)

    def display_wordcloud(self, wordcloud):
        if self.wordcloud_canvas:
            self.wordcloud_canvas.setParent(None)

        fig = Figure(figsize=(12, 8))
        self.wordcloud_canvas = FigureCanvas(fig)
        self.wordcloud_canvas.figure.clear()
        ax = self.wordcloud_canvas.figure.add_subplot(111)
        ax.imshow(wordcloud, interpolation='bilinear')
        ax.axis('off')
        self.wordcloud_canvas.figure.tight_layout(pad=0)

        central_widget = self.centralWidget()
        layout = central_widget.layout()
        layout.addWidget(self.wordcloud_canvas)

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()