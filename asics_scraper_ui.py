"""
アシックス公式ストア巡回ツールのGUIインターフェース
"""
import sys
import os
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                           QHBoxLayout, QLabel, QLineEdit, QPushButton, 
                           QTextEdit, QFileDialog, QSpinBox, QDoubleSpinBox,
                           QComboBox, QProgressBar, QMessageBox)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from asics_scraper import AsicsScraper, generate_test_urls, load_urls_from_file

class ScraperThread(QThread):
    """スクレイピング処理を実行するスレッド"""
    progress = pyqtSignal(dict)
    finished = pyqtSignal()
    error = pyqtSignal(str)

    def __init__(self, urls, settings):
        super().__init__()
        self.urls = urls
        self.settings = settings

    def run(self):
        try:
            scraper = AsicsScraper(
                method=self.settings['method'],
                headless=True,
                chromedriver_path=self.settings.get('chromedriver')
            )

            results = scraper.scrape_urls(
                self.urls,
                self.settings['output_file'],
                delay_range=(self.settings['min_delay'], self.settings['max_delay']),
                timeout=self.settings['timeout'],
                max_retries=self.settings['retries']
            )

            self.finished.emit()
        except Exception as e:
            self.error.emit(str(e))

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('アシックス公式ストア巡回ツール')
        self.setMinimumSize(800, 600)
        
        # メインウィジェットとレイアウト
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)
        
        # 設定セクション
        settings_group = QWidget()
        settings_layout = QVBoxLayout(settings_group)
        
        # メソッド選択
        method_layout = QHBoxLayout()
        method_layout.addWidget(QLabel('スクレイピング方法:'))
        self.method_combo = QComboBox()
        self.method_combo.addItems(['requests', 'selenium'])
        method_layout.addWidget(self.method_combo)
        settings_layout.addLayout(method_layout)
        
        # 遅延設定
        delay_layout = QHBoxLayout()
        delay_layout.addWidget(QLabel('遅延時間 (秒):'))
        self.min_delay = QDoubleSpinBox()
        self.min_delay.setRange(1.0, 10.0)
        self.min_delay.setValue(2.0)
        self.min_delay.setSingleStep(0.5)
        delay_layout.addWidget(self.min_delay)
        delay_layout.addWidget(QLabel('-'))
        self.max_delay = QDoubleSpinBox()
        self.max_delay.setRange(1.0, 20.0)
        self.max_delay.setValue(5.0)
        self.max_delay.setSingleStep(0.5)
        delay_layout.addWidget(self.max_delay)
        settings_layout.addLayout(delay_layout)
        
        # タイムアウト設定
        timeout_layout = QHBoxLayout()
        timeout_layout.addWidget(QLabel('タイムアウト (秒):'))
        self.timeout = QSpinBox()
        self.timeout.setRange(10, 120)
        self.timeout.setValue(30)
        timeout_layout.addWidget(self.timeout)
        settings_layout.addLayout(timeout_layout)
        
        # 再試行回数設定
        retries_layout = QHBoxLayout()
        retries_layout.addWidget(QLabel('最大再試行回数:'))
        self.retries = QSpinBox()
        self.retries.setRange(1, 10)
        self.retries.setValue(3)
        retries_layout.addWidget(self.retries)
        settings_layout.addLayout(retries_layout)
        
        # URL数設定
        count_layout = QHBoxLayout()
        count_layout.addWidget(QLabel('URL数:'))
        self.url_count = QSpinBox()
        self.url_count.setRange(1, 1000)
        self.url_count.setValue(100)
        count_layout.addWidget(self.url_count)
        settings_layout.addLayout(count_layout)
        
        layout.addWidget(settings_group)
        
        # ファイル選択セクション
        file_group = QWidget()
        file_layout = QVBoxLayout(file_group)
        
        # 入力ファイル選択
        input_layout = QHBoxLayout()
        input_layout.addWidget(QLabel('URLリストファイル:'))
        self.input_file = QLineEdit()
        input_layout.addWidget(self.input_file)
        input_browse = QPushButton('参照')
        input_browse.clicked.connect(self.browse_input_file)
        input_layout.addWidget(input_browse)
        file_layout.addLayout(input_layout)
        
        # 出力ファイル選択
        output_layout = QHBoxLayout()
        output_layout.addWidget(QLabel('出力CSVファイル:'))
        self.output_file = QLineEdit('asics_results.csv')
        output_layout.addWidget(self.output_file)
        output_browse = QPushButton('参照')
        output_browse.clicked.connect(self.browse_output_file)
        output_layout.addWidget(output_browse)
        file_layout.addLayout(output_layout)
        
        layout.addWidget(file_group)
        
        # 実行ボタン
        self.run_button = QPushButton('巡回開始')
        self.run_button.clicked.connect(self.start_scraping)
        layout.addWidget(self.run_button)
        
        # 進捗バー
        self.progress_bar = QProgressBar()
        layout.addWidget(self.progress_bar)
        
        # ログ表示
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        layout.addWidget(self.log_text)
        
        # スレッド
        self.scraper_thread = None

    def browse_input_file(self):
        file_name, _ = QFileDialog.getOpenFileName(
            self, 'URLリストファイルを選択', '',
            'Text Files (*.txt);;All Files (*)'
        )
        if file_name:
            self.input_file.setText(file_name)

    def browse_output_file(self):
        file_name, _ = QFileDialog.getSaveFileName(
            self, '出力CSVファイルを選択', 'asics_results.csv',
            'CSV Files (*.csv);;All Files (*)'
        )
        if file_name:
            self.output_file.setText(file_name)

    def log(self, message):
        self.log_text.append(message)

    def start_scraping(self):
        # 設定を収集
        settings = {
            'method': self.method_combo.currentText(),
            'min_delay': self.min_delay.value(),
            'max_delay': self.max_delay.value(),
            'timeout': self.timeout.value(),
            'retries': self.retries.value(),
            'output_file': self.output_file.text()
        }
        
        # URLリストを取得
        input_file = self.input_file.text()
        if input_file and os.path.exists(input_file):
            urls = load_urls_from_file(input_file)
        else:
            urls = generate_test_urls('https://www.asics.com', self.url_count.value())
        
        if not urls:
            QMessageBox.warning(self, 'エラー', '巡回するURLがありません。')
            return
        
        # UIを更新
        self.run_button.setEnabled(False)
        self.progress_bar.setMaximum(len(urls))
        self.progress_bar.setValue(0)
        self.log_text.clear()
        self.log(f'巡回を開始します。URL数: {len(urls)}')
        
        # スレッドを開始
        self.scraper_thread = ScraperThread(urls, settings)
        self.scraper_thread.finished.connect(self.scraping_finished)
        self.scraper_thread.error.connect(self.scraping_error)
        self.scraper_thread.start()

    def scraping_finished(self):
        self.run_button.setEnabled(True)
        self.log('巡回が完了しました。')
        QMessageBox.information(self, '完了', '巡回が完了しました。')

    def scraping_error(self, error_message):
        self.run_button.setEnabled(True)
        self.log(f'エラーが発生しました: {error_message}')
        QMessageBox.critical(self, 'エラー', f'巡回中にエラーが発生しました:\n{error_message}')

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main() 