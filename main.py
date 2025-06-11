import requests
from bs4 import BeautifulSoup
import sqlite3
from datetime import datetime, timedelta
import argparse

# 데이터베이스 초기화 함수
def init_database(conn=None):
    if conn is None:
        conn = sqlite3.connect('stocks.db')
    cursor = conn.cursor()
    
    # 기존 테이블이 있으면 삭제 (스키마 변경을 위해)
    #cursor.execute('DROP TABLE IF EXISTS stock_rankings')
    
    # 검색순위 테이블 생성 (없는 경우에만 생성)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS stock_rankings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT NOT NULL,          -- 날짜 (YYYY-MM-DD)
        time TEXT NOT NULL,          -- 시간 (HH:MM:SS)
        datetime TEXT NOT NULL,      -- 날짜+시간 (YYYY-MM-DD HH:MM:SS)
        rank INTEGER NOT NULL,
        name TEXT NOT NULL,
        search_ratio REAL,
        current_price INTEGER,
        change_price INTEGER,
        change_rate TEXT,
        volume INTEGER,
        open_price INTEGER,
        high_price INTEGER,
        low_price INTEGER,
        per REAL,
        roe REAL,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(datetime, rank, name)  -- 중복 데이터 방지
    )
    ''')
    
    # 인덱스 생성 (검색 성능 향상을 위해) - 이미 존재하면 생성하지 않음
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_datetime ON stock_rankings(datetime)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_name ON stock_rankings(name)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_date ON stock_rankings(date)')
    
    conn.commit()
    return conn

# 데이터베이스에 주식 데이터 저장
def save_to_database(conn, stocks):
    cursor = conn.cursor()
    now = datetime.now()
    today = now.strftime('%Y-%m-%d')
    current_time = now.strftime('%H:%M:%S')
    datetime_str = now.strftime('%Y-%m-%d %H:%M:%S')
    
    for stock in stocks:
        cursor.execute('''
        INSERT OR IGNORE INTO stock_rankings 
        (date, time, datetime, rank, name, search_ratio, current_price, change_price, 
         change_rate, volume, open_price, high_price, low_price, per, roe)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            today,
            current_time,
            datetime_str,
            int(stock['순위']) if stock['순위'] and str(stock['순위']).strip().isdigit() else 0,
            stock['종목명'],
            float(stock['검색비율'].replace('%', '').replace(',', '')) if stock['검색비율'] and stock['검색비율'].replace('%', '').replace(',', '').replace('.', '').lstrip('-').isdigit() else 0.0,
            int(stock['현재가'].replace(',', '')) if stock['현재가'] and stock['현재가'].replace(',', '').lstrip('-').isdigit() else 0,
            int(stock['전일비'].replace(',', '')) if stock['전일비'] and stock['전일비'].replace(',', '').lstrip('-').replace('.', '').isdigit() else 0,
            stock['등락률'].replace('%', '') if stock['등락률'] else '0',
            int(stock['거래량'].replace(',', '')) if stock['거래량'] and stock['거래량'].replace(',', '').isdigit() else 0,
            int(stock['시가'].replace(',', '')) if stock['시가'] and stock['시가'].replace(',', '').isdigit() else 0,
            int(stock['고가'].replace(',', '')) if stock['고가'] and stock['고가'].replace(',', '').isdigit() else 0,
            int(stock['저가'].replace(',', '')) if stock['저가'] and stock['저가'].replace(',', '').isdigit() else 0,
            float(stock['PER'].replace(',', '')) if stock['PER'] and stock['PER'].replace(',', '').replace('.', '').lstrip('-').isdigit() else 0.0,
            float(stock['ROE'].replace(',', '')) if stock['ROE'] and stock['ROE'].replace(',', '').replace('.', '').lstrip('-').isdigit() else 0.0
        ))
    
    conn.commit()

# 데이터베이스에서 주식 데이터 조회
def get_stock_data(conn, date=None, stock_name=None, limit=100):
    cursor = conn.cursor()
    
    if date and stock_name:
        # 특정 날짜와 종목명으로 조회 (시간순 정렬)
        cursor.execute('''
        SELECT * FROM stock_rankings 
        WHERE date = ? AND name = ?
        ORDER BY datetime
        LIMIT ?
        ''', (date, stock_name, limit))
    elif date:
        # 특정 날짜의 모든 데이터 조회 (시간순 정렬)
        cursor.execute('''
        SELECT * FROM stock_rankings 
        WHERE date = ?
        ORDER BY datetime, rank
        LIMIT ?
        ''', (date, limit))
    elif stock_name:
        # 특정 종목의 모든 데이터 조회 (최신순)
        cursor.execute('''
        SELECT * FROM stock_rankings 
        WHERE name = ?
        ORDER BY datetime DESC
        LIMIT ?
        ''', (stock_name, limit))
    else:
        # 최근 데이터 조회 (최신순)
        cursor.execute('''
        SELECT * FROM stock_rankings 
        ORDER BY datetime DESC, rank
        LIMIT ?
        ''', (limit,))
    
    columns = [column[0] for column in cursor.description]
    results = []
    
    for row in cursor.fetchall():
        results.append(dict(zip(columns, row)))
    
    return results

# 네이버 파이낸스에서 주식 데이터 스크래핑
def get_top_searched_stocks():
    # 네이버 증권 인기검색종목 페이지 URL
    url = "https://finance.naver.com/sise/lastsearch2.naver"
    
    # 브라우저처럼 보이기 위한 헤더 설정
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        # 웹페이지 요청
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # 오류가 발생하면 예외 발생
        
        # HTML 파싱
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 주식 테이블 찾기
        table = soup.find('table', {'class': 'type_5'})
        if not table:
            print("주식 테이블을 찾을 수 없습니다.")
            return []
        
        # 주식 데이터를 저장할 리스트
        stocks = []
        
        # 테이블의 모든 행 가져오기 (헤더 행 제외)
        rows = table.find_all('tr')[2:]  # 헤더 행 2개 건너뜀
        
        for row in rows:
            # 빈 행 건너뛰기
            if 'blank_08' in row.get('class', []):
                continue
                
            # 각 셀의 데이터 추출
            cols = row.find_all('td')
            if len(cols) < 12:  # 유효한 데이터가 있는 행인지 확인
                continue
                
            # 데이터 파싱
            rank = cols[0].text.strip()
            name = cols[1].text.strip()
            search_ratio = cols[2].text.strip()
            current_price = cols[3].text.strip().replace(',', '')
            change = cols[4].find('span', {'class': 'tah'}).text.strip() if cols[4].find('span', {'class': 'tah'}) else ''
            change_rate = cols[5].text.strip().replace('%', '')
            volume = cols[6].text.strip().replace(',', '')
            open_price = cols[7].text.strip().replace(',', '')
            high = cols[8].text.strip().replace(',', '')
            low = cols[9].text.strip().replace(',', '')
            per = cols[10].text.strip()
            roe = cols[11].text.strip()
            
            # 주식 데이터를 딕셔너리로 저장
            stocks.append({
                '순위': rank,
                '종목명': name,
                '검색비율': search_ratio,
                '현재가': current_price,
                '전일비': change,
                '등락률': change_rate,
                '거래량': volume,
                '시가': open_price,
                '고가': high,
                '저가': low,
                'PER': per,
                'ROE': roe
            })
            
            # 상위 30개 종목까지만 수집
            if len(stocks) >= 30:
                break
        
        return stocks
        
    except Exception as e:
        print(f"오류가 발생했습니다: {e}")
        return []

# 메인 함수
def main():
    def parse_arguments():
        parser = argparse.ArgumentParser(description='네이버 파이낸스에서 주식 데이터를 스크래핑하고 조회합니다.')
        parser.add_argument('--name', type=str, help='조회할 종목명 (예: 삼성전자)')
        parser.add_argument('--date', type=str, nargs='?', const=datetime.now().strftime('%Y-%m-%d'),
                            help='조회할 날짜 (YYYY-MM-DD 형식, 생략 시 오늘 날짜 사용)')
        parser.add_argument('--limit', type=int, nargs='?', const=10, default=10,
                            help='조회할 레코드 수 (기본값: 10)')
        parser.add_argument('--scrape', action='store_true', help='새 데이터를 스크래핑하여 저장')
        parser.add_argument('--init', action='store_true', help='데이터베이스 초기화 (기존 데이터 삭제됨)')
        return parser.parse_args()

    def display_stock_data(data):
        if not data:
            print("조회된 데이터가 없습니다.")
            return
        
        # 데이터가 딕셔너리 리스트인지 확인 (스크래핑 결과)
        if isinstance(data, list) and data and isinstance(data[0], dict):
            # 데이터베이스 조회 결과 처리 (컬럼명이 있는 딕셔너리)
            if 'name' in data[0]:
                current_stock = None
                for stock in data:
                    if current_stock != stock['name']:
                        if current_stock is not None:
                            print()
                        current_stock = stock['name']
                        print(f"=== {current_stock}의 최근 변동사항 ===")
                    
                    print(f"[{stock['date']} {stock['time']}] {stock['rank']}위 - ", end='')
                    print(f"현재가: {stock['current_price']:,}원, ", end='')
                    print(f"전일대비: {stock['change_price']:+,}원 ({stock['change_rate']}%)")
            # 스크래핑 결과 처리 (한글 키를 가진 딕셔너리)
            elif '종목명' in data[0]:
                for stock in data[:5]:  # 상위 5개만 표시
                    print(f"=== {stock['종목명']} ===")
                    print(f"순위: {stock['순위']}위")
                    print(f"현재가: {stock['현재가']:,}원")
                    print(f"전일대비: {stock['전일대비']} ({stock['등락률']})")
                    print(f"거래량: {stock['거래량']:,}주")
                    print()
            return
            
        # 기존 데이터베이스 조회 결과 처리 (튜플 리스트)
        if isinstance(data, list) and data and isinstance(data[0], (list, tuple)):
            current_stock = None
            for row in data:
                if current_stock != row[5]:  # 종목명이 변경된 경우
                    if current_stock is not None:
                        print()  # 구분을 위해 빈 줄 추가
                    current_stock = row[5]
                    print(f"=== {current_stock}의 최근 변동사항 ===")
            
                print(f"[{row[2]} {row[3]}] {row[4]}위 - ", end='')
                print(f"현재가: {row[7]:,}원, ", end='')
                print(f"전일대비: {row[8]:+,}원 ({row[9]}%)")

    args = parse_arguments()
    
    # 데이터베이스 초기화
    conn = sqlite3.connect('stocks.db')
    
    # --init 플래그가 있으면 테이블 삭제 후 재생성
    if args.init:
        print("데이터베이스를 초기화합니다. 기존 데이터가 모두 삭제됩니다.")
        confirm = input("계속하시려면 'y'를 입력하세요: ")
        if confirm.lower() == 'y':
            cursor = conn.cursor()
            cursor.execute('DROP TABLE IF EXISTS stock_rankings')
            conn.commit()
            print("기존 테이블이 삭제되었습니다.")
        else:
            print("초기화를 취소했습니다.")
            return
    
    # 테이블이 없으면 생성
    init_database()
    
    try:
        if args.scrape or not (args.name or args.date):
            print("네이버 파이낸스에서 주식 데이터를 가져오는 중...")
            # 최다 검색 종목 스크래핑
            stocks = get_top_searched_stocks()
            
            if stocks:
                # 데이터베이스에 저장
                save_to_database(conn, stocks)
                print(f"\n총 {len(stocks)}개의 주식 데이터를 데이터베이스에 저장했습니다.")
                
                if not args.name and not args.date:
                    # 스크래핑만 한 경우 상위 5개 종목의 변동사항 출력
                    print("\n최근 저장된 상위 5개 종목의 시간대별 변동사항:")
                    top_stocks = [stock['종목명'] for stock in stocks[:5]]
                    for stock_name in top_stocks:
                        data = get_stock_data(conn, stock_name=stock_name, limit=3)
                        display_stock_data(data)
                        print()
                
                return  # 스크래핑만 한 경우 여기서 종료
        
        # 데이터 조회
        if args.name or args.date:
            print("\n주식 데이터를 조회합니다...")
            
            # 날짜만 지정된 경우 해당 날짜의 저장된 시간대 조회
            if args.date and not args.name:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT DISTINCT time, datetime 
                    FROM stock_rankings 
                    WHERE date = ? 
                    ORDER BY datetime DESC
                ''', (args.date,))
                
                times = cursor.fetchall()
                
                if not times:
                    print(f"{args.date}에 저장된 데이터가 없습니다.")
                    return
                    
                print(f"\n{args.date}에 저장된 시간대:")
                for idx, (time, _) in enumerate(times, 1):
                    print(f"{idx}. {time}")
                
                # 시간대 선택
                while True:
                    try:
                        choice = input("\n확인할 시간대를 선택하세요 (1-{}), 종료하려면 q: ".format(len(times)))
                        if choice.lower() == 'q':
                            return
                        choice_idx = int(choice) - 1
                        if 0 <= choice_idx < len(times):
                            selected_time = times[choice_idx][0]
                            break
                        print("잘못된 선택입니다. 다시 시도해주세요.")
                    except (ValueError, IndexError):
                        print("숫자를 입력해주세요.")
                
                # 선택된 시간대의 전체 데이터 조회
                cursor.execute('''
                    SELECT * FROM stock_rankings 
                    WHERE date = ? AND time = ?
                    ORDER BY rank
                ''', (args.date, selected_time))
                
                columns = [column[0] for column in cursor.description]
                data = [dict(zip(columns, row)) for row in cursor.fetchall()]
                
            else:
                # 기존 조회 로직 (이름이나 이름+날짜로 조회)
                data = get_stock_data(
                    conn,
                    date=args.date,
                    stock_name=args.name,
                    limit=args.limit
                )
            
            display_stock_data(data)
        else:
            print("주식 데이터를 가져오지 못했습니다.")
            
    except Exception as e:
        print(f"프로그램 실행 중 오류가 발생했습니다: {e}")
        
    finally:
        # 데이터베이스 연결 종료
        conn.close()
        print("\n프로그램을 종료합니다.")

if __name__ == "__main__":
    main()