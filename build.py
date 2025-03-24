"""
アシックス公式ストア巡回ツールのUI.exeビルドスクリプト
"""
import os
import sys
import PyInstaller.__main__

def build_exe():
    # アイコンファイルのパス
    icon_path = os.path.join('assets', 'icon.ico')
    
    # PyInstallerの引数
    args = [
        'asics_scraper_ui.py',  # メインスクリプト
        '--name=ASICS巡回ツール',  # 実行ファイル名
        '--onefile',  # 単一のexeファイルに
        '--noconsole',  # コンソールウィンドウを表示しない
        '--clean',  # ビルド前にキャッシュをクリア
        '--add-data=README.md;.',  # READMEファイルを含める
        '--hidden-import=PyQt5',
        '--hidden-import=PyQt5.QtCore',
        '--hidden-import=PyQt5.QtGui',
        '--hidden-import=PyQt5.QtWidgets',
        '--hidden-import=selenium',
        '--hidden-import=requests',
        '--hidden-import=beautifulsoup4',
        '--hidden-import=pandas',
        '--hidden-import=numpy',
        '--hidden-import=tqdm',
        '--hidden-import=lxml',
        '--collect-all=numpy',
        '--collect-all=pandas',
        '--collect-all=pytz',
        '--collect-all=dateutil',
        '--collect-all=six',
        '--collect-all=python-dateutil',
        '--collect-all=et_xmlfile',
        '--collect-all=openpyxl',
        '--collect-all=pyarrow',
        '--collect-all=pyreadstat',
        '--collect-all=sas_kernel',
        '--collect-all=scipy',
        '--collect-all=statsmodels',
        '--collect-all=xlrd',
        '--collect-all=xlwt',
        '--collect-all=xlsxwriter',
        '--collect-all=zipp',
        '--collect-all=markupsafe',
        '--collect-all=jinja2',
        '--collect-all=pygments',
        '--collect-all=pyparsing',
        '--collect-all=cycler',
        '--collect-all=kiwisolver',
        '--collect-all=matplotlib',
        '--collect-all=packaging',
        '--collect-all=pytz',
        '--collect-all=six',
        '--collect-all=python-dateutil',
        '--collect-all=et_xmlfile',
        '--collect-all=openpyxl',
        '--collect-all=pyarrow',
        '--collect-all=pyreadstat',
        '--collect-all=sas_kernel',
        '--collect-all=scipy',
        '--collect-all=statsmodels',
        '--collect-all=xlrd',
        '--collect-all=xlwt',
        '--collect-all=xlsxwriter',
        '--collect-all=zipp',
        '--collect-all=markupsafe',
        '--collect-all=jinja2',
        '--collect-all=pygments',
        '--collect-all=pyparsing',
        '--collect-all=cycler',
        '--collect-all=kiwisolver',
        '--collect-all=matplotlib',
        '--collect-all=packaging',
    ]
    
    # アイコンファイルが存在する場合は追加
    if os.path.exists(icon_path):
        args.append(f'--icon={icon_path}')
    
    # PyInstallerを実行
    PyInstaller.__main__.run(args)
    
    print('ビルドが完了しました。')
    print('実行ファイルは dist/ASICS巡回ツール.exe にあります。')

if __name__ == '__main__':
    build_exe() 