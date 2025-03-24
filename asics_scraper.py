"""
アシックス公式ストアの製品ページ巡回ツール
製品ページのURLを指定して、ページの存在確認と基本情報の取得を行います。
"""
import os
import time
import random
import argparse
import re
import json
import pandas as pd
from tqdm import tqdm
from datetime import datetime
from urllib.parse import urljoin

# Selenium imports
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException

# Requests imports
import requests
from bs4 import BeautifulSoup
from requests.exceptions import RequestException, Timeout, ConnectionError, HTTPError

class AsicsScraper:
    def __init__(self, method='selenium', headless=True, chromedriver_path=None):
        """
        アシックススクレイパーを初期化します。
        
        引数:
            method (str): スクレイピング方法 - 'selenium' または 'requests'
            headless (bool): ブラウザをヘッドレスモードで実行（Seleniumのみ）
            chromedriver_path (str): ローカルのchromedriver実行ファイルへのパス
        """
        self.method = method.lower()
        self.headless = headless
        self.chromedriver_path = chromedriver_path
        self.driver = None
        self.session = None
        self.results = []
        
        if self.method == 'selenium':
            self._setup_selenium(headless)
        elif self.method == 'requests':
            self._setup_requests()
        else:
            raise ValueError("指定された方法は 'selenium' または 'requests' でなければなりません")
    
    def _setup_selenium(self, headless):
        """Selenium WebDriverを設定します"""
        options = Options()
        if headless:
            options.add_argument('--headless=new')
        
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--window-size=1920,1080')
        options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        options.add_argument('--lang=ja')
        
        try:
            # 指定されたchromedriverパスがある場合はそれを使用
            if self.chromedriver_path and os.path.exists(self.chromedriver_path):
                print(f"ChromeDriverを使用: {self.chromedriver_path}")
                service = Service(executable_path=self.chromedriver_path)
                self.driver = webdriver.Chrome(service=service, options=options)
            else:
                # ChromeDriverManagerを使わずに直接初期化を試みる
                print("Chromeの直接初期化を試みています...")
                self.driver = webdriver.Chrome(options=options)
        except Exception as e:
            print(f"Chrome初期化失敗: {str(e)}")
            print("代わりにrequests方式を使用します...")
            self.method = 'requests'
            self._setup_requests()
            return
            
        self.driver.set_page_load_timeout(30)
    
    def _setup_requests(self):
        """requestsセッションを設定します"""
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept-Language': 'ja,en-US;q=0.9,en;q=0.8',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Referer': 'https://www.asics.com/jp/ja-jp/',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache'
        })
    
    def scrape_urls(self, urls, output_file=None, delay_range=(1.5, 4.0), timeout=30, max_retries=3):
        """
        アシックスストアから複数の製品URLをスクレイピングします。
        
        引数:
            urls (list): スクレイピングする製品URLのリスト
            output_file (str): CSVのオプション出力ファイルパス
            delay_range (tuple): リクエスト間の遅延範囲（秒）
            timeout (int): リクエストタイムアウト（秒）
            max_retries (int): 失敗時の最大再試行回数
            
        戻り値:
            pd.DataFrame: 結果のデータフレーム
        """
        # 各URLをスクレイピング
        for url in tqdm(urls, desc=f"{self.method}でスクレイピング中"):
            result = {
                'url': url,
                'status': 'エラー' if self.method == 'requests' else 'ERROR',
                'title': '',
                'product_id': '',
                'price': '',
                'availability': '',
                'color': '',
                'category': '',
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            # URL形式を修正
            if not url.startswith(('http://', 'https://')):
                url = 'https://www.asics.com' + ('' if url.startswith('/') else '/') + url
            
            # 製品IDと色コードをURLから抽出
            product_info = self._extract_product_info_from_url(url)
            if product_info:
                result.update(product_info)
            
            # URLをスクレイピング（最大再試行回数まで）
            success = False
            retry_count = 0
            
            while not success and retry_count < max_retries:
                try:
                    # ブロックされないよう、ランダムな遅延を追加
                    time.sleep(random.uniform(delay_range[0], delay_range[1]))
                    
                    # 選択したメソッドでスクレイピング
                    if self.method == 'selenium':
                        self._scrape_with_selenium(url, result, timeout)
                    else:
                        self._scrape_with_requests(url, result, timeout)
                    
                    success = True
                
                except Timeout:
                    retry_count += 1
                    error_msg = f"タイムアウト - 再試行 {retry_count}/{max_retries}"
                    result['title'] = error_msg
                except ConnectionError:
                    retry_count += 1
                    error_msg = f"接続エラー - 再試行 {retry_count}/{max_retries}"
                    result['title'] = error_msg
                except (HTTPError, WebDriverException) as e:
                    # HTTPエラーとWebDriverエラーを処理
                    status_code = getattr(e, 'response', None)
                    if status_code and hasattr(status_code, 'status_code'):
                        status_code = status_code.status_code
                        
                        if status_code == 404:
                            result['title'] = "ページが見つかりません（404）"
                            break  # 404の場合は再試行しない
                        elif status_code == 403:
                            result['title'] = "アクセスが拒否されました（403）"
                            # 403の場合は少し長めに待機してから再試行
                            time.sleep(random.uniform(5.0, 10.0))
                            retry_count += 1
                        else:
                            retry_count += 1
                            result['title'] = f"HTTPエラー: {status_code} - 再試行 {retry_count}/{max_retries}"
                    else:
                        retry_count += 1
                        result['title'] = f"ブラウザエラー: {str(e)} - 再試行 {retry_count}/{max_retries}"
                except (RequestException, TimeoutException) as e:
                    retry_count += 1
                    result['title'] = f"リクエストエラー: {str(e)} - 再試行 {retry_count}/{max_retries}"
                except Exception as e:
                    retry_count += 1
                    result['title'] = f"予期しないエラー: {str(e)} - 再試行 {retry_count}/{max_retries}"
            
            # 結果を保存
            self.results.append(result)
            
            # 一定間隔で中間結果を保存
            if output_file and len(self.results) % 10 == 0:
                self._save_results(output_file)
        
        # 結果をデータフレームに変換
        results_df = pd.DataFrame(self.results)
        
        # CSVに保存
        if output_file:
            self._save_results(output_file)
        
        # 結果サマリーを表示
        success_value = '成功' if self.method == 'requests' else 'SUCCESS'
        success_count = sum(results_df['status'] == success_value)
        print(f"\nスクレイピング結果サマリー:")
        print(f"合計URL数: {len(urls)}")
        print(f"成功: {success_count} ({success_count/len(urls)*100:.2f}%)")
        print(f"失敗: {len(urls) - success_count} ({(len(urls) - success_count)/len(urls)*100:.2f}%)")
        
        return results_df
    
    def _scrape_with_selenium(self, url, result, timeout=30):
        """
        URLをSeleniumでスクレイピングします
        
        引数:
            url (str): スクレイピングするURL
            result (dict): 結果を格納する辞書
            timeout (int): タイムアウト（秒）
        """
        try:
            # ページを読み込む
            self.driver.get(url)
            self.driver.set_page_load_timeout(timeout)
            
            # ページの読み込みを待機
            WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((By.TAG_NAME, "title"))
            )
            
            # 基本情報を取得
            result['title'] = self.driver.title
            result['status'] = 'SUCCESS'
            
            # 詳細情報を取得
            try:
                # 価格情報を取得
                price_elem = self.driver.find_element(By.CSS_SELECTOR, '.product-price, .price, [data-test-id="product-price"]')
                if price_elem:
                    result['price'] = price_elem.text.strip()
                
                # 在庫状況を取得
                availability_elem = self.driver.find_element(By.CSS_SELECTOR, '.stock-status, .availability, [data-test-id="availability"]')
                if availability_elem:
                    result['availability'] = availability_elem.text.strip()
                
                # JSON-LDから構造化データを抽出
                json_ld_scripts = self.driver.find_elements(By.CSS_SELECTOR, 'script[type="application/ld+json"]')
                for script in json_ld_scripts:
                    try:
                        ld_data = json.loads(script.get_attribute('innerHTML'))
                        if isinstance(ld_data, list):
                            ld_data = next((item for item in ld_data if item.get('@type') == 'Product'), {})
                        
                        if ld_data.get('@type') == 'Product':
                            if not result.get('price') and 'offers' in ld_data:
                                result['price'] = ld_data['offers'].get('price', '')
                            
                            if not result.get('availability') and 'offers' in ld_data:
                                availability = ld_data['offers'].get('availability', '')
                                if availability:
                                    # 「在庫あり」などの形式に変換
                                    availability = availability.replace('http://schema.org/InStock', '在庫あり')
                                    availability = availability.replace('http://schema.org/OutOfStock', '在庫切れ')
                                    availability = availability.replace('http://schema.org/LimitedAvailability', '在庫残りわずか')
                                    result['availability'] = availability
                    except json.JSONDecodeError:
                        continue
            except Exception as e:
                print(f"詳細情報抽出エラー (Selenium): {str(e)}")
                
        except TimeoutException:
            raise Timeout("ページの読み込みがタイムアウトしました")
        except WebDriverException as e:
            raise
    
    def _scrape_with_requests(self, url, result, timeout=30):
        """
        URLをrequestsでスクレイピングします
        
        引数:
            url (str): スクレイピングするURL
            result (dict): 結果を格納する辞書
            timeout (int): タイムアウト（秒）
        """
        try:
            # リクエスト送信
            response = self.session.get(url, timeout=timeout)
            response.raise_for_status()
            
            # HTMLの解析
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 基本情報を取得
            result['title'] = soup.title.text.strip() if soup.title else 'タイトルが見つかりません'
            result['status'] = '成功'
            
            # 詳細情報を抽出
            self._extract_product_details(soup, result)
            
            # ページの存在確認
            if '404' in result['title'].lower() or 'ページが見つかりません' in result['title']:
                result['status'] = 'ページなし'
                result['title'] = 'ページが見つかりません'
            
            # 商品情報の存在確認
            if not result.get('price') and not result.get('availability'):
                result['status'] = '商品情報なし'
                result['title'] = '商品情報が見つかりません'
                
        except HTTPError as e:
            if e.response.status_code == 404:
                result['status'] = 'ページなし'
                result['title'] = 'ページが見つかりません（404）'
            elif e.response.status_code == 403:
                result['status'] = 'アクセス拒否'
                result['title'] = 'アクセスが拒否されました（403）'
            else:
                result['status'] = 'エラー'
                result['title'] = f'HTTPエラー: {e.response.status_code}'
        except Exception as e:
            result['status'] = 'エラー'
            result['title'] = f'予期しないエラー: {str(e)}'
    
    def _extract_product_info_from_url(self, url):
        """URLから製品情報を抽出します"""
        info = {}
        
        # 日本のアシックス製品URLパターンに合わせて正規表現を更新
        patterns = [
            # 標準的な製品ページパターン
            r'/jp/ja-jp/([^/]+)/p/([A-Z0-9]+)-([0-9]{3})\.html',
            # カテゴリページからの製品パターン
            r'/jp/ja-jp/([^/]+)/products/([A-Z0-9]+)-([0-9]{3})\.html',
            # セールページのパターン
            r'/jp/ja-jp/sale/([^/]+)/p/([A-Z0-9]+)-([0-9]{3})\.html'
        ]
        
        for pattern in patterns:
            product_match = re.search(pattern, url)
            if product_match:
                info['category'] = product_match.group(1)
                info['product_id'] = product_match.group(2)
                info['color'] = product_match.group(3)
                break
        
        return info
    
    def _extract_product_details(self, soup, result):
        """HTMLから製品の詳細情報を抽出します"""
        try:
            # 価格情報を取得
            price_elem = soup.select_one('.product-price, .price, [data-test-id="product-price"]')
            if price_elem:
                result['price'] = price_elem.text.strip()
            
            # 在庫状況を取得
            availability_elem = soup.select_one('.stock-status, .availability, [data-test-id="availability"]')
            if availability_elem:
                result['availability'] = availability_elem.text.strip()
            
            # JSON-LDから構造化データを抽出
            json_ld = soup.find('script', type='application/ld+json')
            if json_ld:
                try:
                    ld_data = json.loads(json_ld.string)
                    if isinstance(ld_data, list):
                        ld_data = next((item for item in ld_data if item.get('@type') == 'Product'), {})
                    
                    if ld_data.get('@type') == 'Product':
                        if not result.get('price') and 'offers' in ld_data:
                            result['price'] = ld_data['offers'].get('price', '')
                        
                        if not result.get('availability') and 'offers' in ld_data:
                            availability = ld_data['offers'].get('availability', '')
                            if availability:
                                # 「在庫あり」などの形式に変換
                                availability = availability.replace('http://schema.org/InStock', '在庫あり')
                                availability = availability.replace('http://schema.org/OutOfStock', '在庫切れ')
                                availability = availability.replace('http://schema.org/LimitedAvailability', '在庫残りわずか')
                                result['availability'] = availability
                except json.JSONDecodeError:
                    pass
        except Exception as e:
            print(f"詳細情報抽出エラー: {str(e)}")
    
    def _save_results(self, output_file):
        """結果をCSVファイルに保存します"""
        try:
            results_df = pd.DataFrame(self.results)
            results_df.to_csv(output_file, index=False, encoding='utf-8-sig')
            print(f"結果を {output_file} に保存しました")
        except Exception as e:
            print(f"結果保存エラー: {str(e)}")
    
    def close(self):
        """リソースをクリーンアップします"""
        if self.method == 'selenium' and self.driver:
            self.driver.quit()
        elif self.method == 'requests' and self.session:
            self.session.close()

def generate_test_urls(base_url, count=100):
    """
    アシックス製品のテストURLを生成します。
    実際の製品URLがない場合のヘルパー関数です。
    
    引数:
        base_url (str): アシックスストアのベースURL
        count (int): 生成するURL数
        
    戻り値:
        list: 生成されたURLのリスト
    """
    # 末尾のスラッシュがある場合は削除
    if base_url.endswith('/'):
        base_url = base_url[:-1]
    
    # アシックスの一般的な製品カテゴリ（日本向け）
    categories = [
        'running', 'training', 'tennis', 'sportsstyle', 
        'volleyball', 'track-and-field', 'walking',
        'basketball', 'football', 'golf'
    ]
    
    # 日本の製品ID構造（より現実的なパターン）
    jp_product_ids = [
        '1011A', '1011B', '1012A', '1012B', '1013A', 
        '1071A', '1071B', '1072A', '1072B', '1073A',
        '1081A', '1081B', '1082A', '1082B', '1083A',
        '1091A', '1091B', '1092A', '1092B', '1093A'
    ]
    
    urls = []
    
    # カテゴリに基づいたランダムURLの生成
    for _ in range(count):
        category = random.choice(categories)
        product_id = f"{random.choice(jp_product_ids)}{random.randint(100, 999)}"
        color_code = f"{random.randint(100, 999)}"
        
        # 日本のURLフォーマット（複数のパターン）
        url_patterns = [
            f"{base_url}/jp/ja-jp/{category}/p/{product_id}-{color_code}.html",
            f"{base_url}/jp/ja-jp/{category}/products/{product_id}-{color_code}.html",
            f"{base_url}/jp/ja-jp/sale/{category}/p/{product_id}-{color_code}.html"
        ]
        
        url = random.choice(url_patterns)
        urls.append(url)
    
    return urls

def load_urls_from_file(file_path):
    """ファイルからURLを読み込みます"""
    urls = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                url = line.strip()
                if url and not url.startswith('#'):  # コメント行をスキップ
                    urls.append(url)
        print(f"{file_path} から {len(urls)} 個のURLを読み込みました")
    except Exception as e:
        print(f"URLファイル読み込みエラー: {str(e)}")
    
    return urls

def main():
    """スクリプトのメインエントリーポイント"""
    parser = argparse.ArgumentParser(description='アシックス公式ストア製品ページ巡回ツール')
    parser.add_argument('--method', choices=['selenium', 'requests'], default='requests',
                        help='スクレイピング方法（selenium または requests）')
    parser.add_argument('--headless', action='store_true', help='ブラウザをヘッドレスモードで実行（Seleniumのみ）')
    parser.add_argument('--input', type=str, help='URLリストの入力ファイル（1行に1つのURL）')
    parser.add_argument('--output', type=str, default='asics_results.csv', help='出力CSVファイルのパス')
    parser.add_argument('--count', type=int, default=100, help='入力ファイルがない場合のテストURL数')
    parser.add_argument('--base-url', type=str, default='https://www.asics.com', 
                        help='テストURL生成のためのベースURL')
    parser.add_argument('--chromedriver', type=str, help='chromedriver実行ファイルへのパス（Selenium用）')
    parser.add_argument('--min-delay', type=float, default=2.0, 
                        help='リクエスト間の最小遅延時間（秒）')
    parser.add_argument('--max-delay', type=float, default=5.0, 
                        help='リクエスト間の最大遅延時間（秒）')
    parser.add_argument('--timeout', type=int, default=30, 
                        help='リクエストタイムアウト（秒）')
    parser.add_argument('--retries', type=int, default=3, 
                        help='失敗時の最大再試行回数')
    
    args = parser.parse_args()
    
    # ファイルからURLを取得またはテストURLを生成
    if args.input and os.path.exists(args.input):
        urls = load_urls_from_file(args.input)
    else:
        print(f"入力ファイルが提供されていないか、見つかりませんでした。{args.count} 個のテストURLを生成します...")
        urls = generate_test_urls(args.base_url, args.count)
    
    if not urls:
        print("巡回するURLがありません。")
        return
    
    print(f"\n巡回設定:")
    print(f"URL数: {len(urls)}")
    print(f"メソッド: {args.method}")
    print(f"遅延: {args.min_delay}秒 - {args.max_delay}秒")
    print(f"タイムアウト: {args.timeout}秒")
    print(f"最大再試行回数: {args.retries}")
    
    # スクレイパーを初期化
    scraper = AsicsScraper(method=args.method, headless=args.headless, chromedriver_path=args.chromedriver)
    
    try:
        # スクレイピング実行
        results = scraper.scrape_urls(
            urls, 
            args.output,
            delay_range=(args.min_delay, args.max_delay),
            timeout=args.timeout, 
            max_retries=args.retries
        )
        
        # 結果の詳細なサマリーを表示
        print("\n巡回結果サマリー:")
        print(f"合計URL数: {len(urls)}")
        print(f"成功: {sum(results['status'] == '成功')} ({sum(results['status'] == '成功')/len(urls)*100:.2f}%)")
        print(f"ページなし: {sum(results['status'] == 'ページなし')} ({sum(results['status'] == 'ページなし')/len(urls)*100:.2f}%)")
        print(f"商品情報なし: {sum(results['status'] == '商品情報なし')} ({sum(results['status'] == '商品情報なし')/len(urls)*100:.2f}%)")
        print(f"アクセス拒否: {sum(results['status'] == 'アクセス拒否')} ({sum(results['status'] == 'アクセス拒否')/len(urls)*100:.2f}%)")
        print(f"エラー: {sum(results['status'] == 'エラー')} ({sum(results['status'] == 'エラー')/len(urls)*100:.2f}%)")
        
    finally:
        # リソースをクリーンアップ
        scraper.close()

if __name__ == "__main__":
    main() 