# StockScraper

**StockScraper** is a Python script that collects real-time popular stock data from Naver Finance and stores it in an SQLite database for further analysis.

## Project Purpose
This project was developed to collect data on top-searched stocks, which is not available through standard stock APIs. The collected data can be used in further analyses to explore the correlation between search interest and stock price movements, providing insights that may support investment strategies.

## Key Features
- **Real-time Data Collection**: Automatically scrapes the top 30 most searched stocks from Naver Finance
- **Comprehensive Stock Data**: Tracks rank, stock name, search ratio, current price, price change, change rate, volume, open/high/low prices, PER, and ROE
- **Time-based Queries**: View data by specific date and time slots
- **Interactive CLI**: Easy-to-use command line interface with interactive time selection
- **Persistent Storage**: Data is stored in an SQLite database with timestamps
- **Duplicate Prevention**: Automatically skips duplicate entries
- **Cross-platform**: Works on Windows and macOS

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/StockScraper.git
   cd StockScraper
   ```

2. Install required packages:
   ```bash
   pip install requests beautifulsoup4
   ```

3. Initialize the database (this will create the necessary tables):
   ```bash
   # Just run the script once, it will create the database automatically
   python main.py
   
   # If you want to reset the database (WARNING: deletes all data):
   python main.py --init
   ```

## Usage

### Basic Usage (Scraping + Show Top 5 Stocks)
```bash
# Run the scraper and show top 5 stocks
python main.py
```

### Query Specific Stock
```bash
# Show recent data for a specific stock (default: 10 most recent entries)
python main.py --name "삼성전자"

# Show specific number of entries
python main.py --name "삼성전자" --limit 5
```

### Query Data by Date and Time
```bash
# View available time slots for a specific date
python main.py --date "2025-06-11"
# Then select a time from the list to view all 30 stocks for that time

# View data for a specific stock on a specific date
python main.py --name "삼성전자" --date "2025-06-11"
```

### Force New Data Scraping
```bash
# Scrape new data and save to database
python main.py --scrape
```

### Reset Database (WARNING: Deletes all data)
```bash
python main.py --init
```

## Automation Setup

The script can be scheduled to run automatically every hour using Windows Task Scheduler:

1. Open PowerShell as Administrator
2. Run the following commands:
   ```powershell
   Set-ExecutionPolicy RemoteSigned -Scope CurrentUser
   cd C:\Users\user\IdeaProjects\StockScraper
   .\schedule_windows.ps1
   ```

This will create a scheduled task named "StockScraperHourly" that runs the scraper:
- Every hour automatically
- Using your Python virtual environment
- With administrator privileges

To verify the task is running:
1. Open Task Scheduler
2. Look for "StockScraperHourly" in Task Scheduler Library
3. Check the "Last Run Time" and "Next Run Time" columns


## Data Management

### Viewing Data
- When querying by date, you'll see a list of available time slots
- Select a time slot to view all 30 stocks for that specific time
- Stock data is sorted by search rank

### Database Schema
The `stock_rankings` table includes the following columns:

- `id`: Unique identifier (auto-increment)
- `date`: Date (YYYY-MM-DD)
- `time`: Time (HH:MM:SS)
- `datetime`: Combined date and time (YYYY-MM-DD HH:MM:SS)
- `rank`: Search ranking
- `name`: Stock name
- `search_ratio`: Search ratio (%)
- `current_price`: Current price
- `change_price`: Price change from previous day
- `change_rate`: Rate of change
- `volume`: Trading volume
- `open_price`: Opening price
- `high_price`: Highest price
- `low_price`: Lowest price
- `per`: Price-Earnings Ratio
- `roe`: Return on Equity
- `created_at`: Record creation timestamp

## License

This project is licensed under the MIT License - see the LICENSE file for details.
