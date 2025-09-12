#!/usr/bin/env python3
import sys
import re
from datetime import datetime

def parse_customer_info(email_body):
    """Parse customer information from email body"""
    customer_info = {}
    
    # Define regex patterns for extracting information
    patterns = {
        'event_name': r'イベント名\s*:\s*(.+?)(?=\n|開催日)',
        'event_date': r'開催日\s*:\s*(.+?)(?=\n|時間)',
        'event_time': r'時間\s*:\s*(.+?)(?=\n|会場)',
        'venue': r'会場\s*:\s*(.+?)(?=\n|URL)',
        'url': r'URL\s*:\s*(https?://[^\s]+)',
        'reservation_date': r'ご希望日\s*[：:]\s*(.+?)(?=\n|ご希望時間)',
        'reservation_time': r'ご希望時間\s*[：:]\s*(.+?)(?=\n)',
        'name': r'お名前\s*:\s*(.+?)(?=\n|フリガナ)',
        'furigana': r'フリガナ\s*:\s*(.+?)(?=\n|メール)',
        'email': r'メールアドレス\s*:\s*(.+?)(?=\n|電話)',
        'phone': r'電話番号\s*:\s*(.+?)(?=\n|年齢)',
        'age': r'年齢\s*:\s*(.+?)(?=\n|毎月)',
        'monthly_rent': r'毎月の家賃\s*:\s*(.+?)(?=\n|月々)',
        'monthly_payment': r'月々の返済額\s*:\s*(.+?)(?=\n|郵便)',
        'postal_code': r'郵便番号\s*:\s*(.+?)(?=\n|ご住所)',
        'address': r'ご住所\s*:\s*(.+?)(?=\n|ご意見)',
        'comments': r'ご意見・ご質問等\s*:\s*(.+?)(?=\n|ご予約のきっかけ)',
        'trigger': r'ご予約のきっかけ\s*:\s*(.+?)(?=\n|=)',
        'store_name': r'展示場名\s*:\s*(.+?)(?=\n|所在地)',
        'store_address': r'所在地\s*:\s*(.+?)(?=\n|営業時間)',
        'business_hours': r'営業時間\s*:\s*(.+?)(?=\n|定休日)',
        'closed_days': r'定休日\s*:\s*(.+?)(?=\n)'
    }
    
    for key, pattern in patterns.items():
        match = re.search(pattern, email_body, re.MULTILINE | re.DOTALL)
        if match:
            customer_info[key] = match.group(1).strip()
        else:
            customer_info[key] = ""
    
    # Clean up the data
    for key, value in customer_info.items():
        if value:
            customer_info[key] = value.replace('\n', ' ').strip()
    
    return customer_info

# Sample email data from your console output
sample_email = """[STYLE HOUSE] イベントの参加お申し込みがありました。 2025-09-03 06:39:19 ======================================== イベント情報 ======================================== イベント名      : 【西宮住宅展示場】見つけよう、理想のお家！AUTUMN FAIR開催? 9月も大人気「JIBのトートバッグ」をプレゼント♪ 開催日          : 2025年9月1日(月) - 9月15日(月) 時間            : 09：30～18：00(水曜定休日) 会場            : 兵庫県西宮市鞍掛町5-5 URL             : https://www.taniue.jp/event/details_111.html ======================================== ご予約情報 ======================================== ご希望日     ： 2025年9月6日 ご希望時間   ： 9:30～11:00 ======================================== お客様情報 ======================================== お名前            : 向山　隆志 フリガナ          : ムカイヤマ　タカシ メールアドレス    : k884maria@gmail.com 電話番号          : 08043947558 年齢              : 35歳 毎月の家賃       : 20万円 月々の返済額      : 20万円 郵便番号          : 〒662-0027 ご住所            : 兵庫県2-37　夙川苦楽園口レジデンス302 夙川苦楽園口レジデンス308夙川苦楽園口レジデンス302 ご意見・ご質問等 : ご予約のきっかけ    : インスタグラム ======================================== ======================================== 取り扱い店舗 ======================================== 展示場名 : 西宮・酒蔵通り住宅公園店 所在地 : 〒662-0926 兵庫県西宮市鞍掛町５－５ 営業時間 : 9:30～17:30　※予約制 定休日 : 水曜日"""

def main():
    print("Testing Email Parser...")
    print("=" * 50)
    
    # Parse the sample email
    parsed_data = parse_customer_info(sample_email)
    
    print("Extracted Customer Information:")
    print("=" * 50)
    
    for key, value in parsed_data.items():
        if value:  # Only print non-empty values
            print(f"{key:20}: {value}")
    
    print("\n" + "=" * 50)
    print(f"Total fields extracted: {len([v for v in parsed_data.values() if v])}")
    print("=" * 50)

if __name__ == "__main__":
    main()