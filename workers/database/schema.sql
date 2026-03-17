-- Stockton Cloud Database Schema
-- 在 Cloudflare D1 中执行

-- 股票基本信息表
CREATE TABLE IF NOT EXISTS stocks (
    code TEXT PRIMARY KEY,           -- 股票代码
    name TEXT,                       -- 股票名称
    market TEXT CHECK (market IN ('sh', 'sz')),  -- 市场
    industry TEXT,                   -- 行业
    list_date TEXT,                  -- 上市日期
    is_active INTEGER DEFAULT 1 CHECK (is_active IN (0, 1)),
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 股票日K数据表
-- 注意：为了节省空间，只保存核心字段
CREATE TABLE IF NOT EXISTS stock_prices (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT NOT NULL,              -- 股票代码
    date TEXT NOT NULL,              -- 日期 (YYYY-MM-DD)
    open REAL,                       -- 开盘价
    high REAL,                       -- 最高价
    low REAL,                        -- 最低价
    close REAL,                      -- 收盘价
    volume INTEGER,                  -- 成交量
    amount REAL,                     -- 成交额
    ma5 REAL,                        -- 5日均线
    ma10 REAL,                       -- 10日均线
    ma20 REAL,                       -- 20日均线
    ma60 REAL,                       -- 60日均线
    change_pct REAL,                 -- 涨跌幅 (%)
    turnover_rate REAL,              -- 换手率 (%)
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(code, date)
);

-- 市场统计表（每天一条）
CREATE TABLE IF NOT EXISTS market_stats (
    date TEXT PRIMARY KEY,           -- 日期
    up_count INTEGER DEFAULT 0,      -- 上涨家数
    down_count INTEGER DEFAULT 0,    -- 下跌家数
    flat_count INTEGER DEFAULT 0,    -- 平盘家数
    limit_up_count INTEGER DEFAULT 0,   -- 涨停家数
    limit_down_count INTEGER DEFAULT 0, -- 跌停家数
    total_amount REAL DEFAULT 0,     -- 总成交额（亿元）
    sh_index REAL,                   -- 上证指数收盘
    sz_index REAL,                   -- 深证成指收盘
    cy_index REAL,                   -- 创业板指收盘
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 指数成分股表
CREATE TABLE IF NOT EXISTS index_components (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    index_code TEXT NOT NULL,        -- 指数代码
    index_name TEXT,                 -- 指数名称
    stock_code TEXT NOT NULL,        -- 成分股代码
    stock_name TEXT,                 -- 成分股名称
    weight REAL,                     -- 权重
    update_date DATE DEFAULT CURRENT_DATE,
    UNIQUE(index_code, stock_code)
);

-- 创建索引优化查询性能
CREATE INDEX IF NOT EXISTS idx_stock_prices_code_date ON stock_prices(code, date);
CREATE INDEX IF NOT EXISTS idx_stock_prices_date ON stock_prices(date);
CREATE INDEX IF NOT EXISTS idx_index_components_index ON index_components(index_code);
CREATE INDEX IF NOT EXISTS idx_index_components_stock ON index_components(stock_code);

-- 初始化一些常用数据

-- 主要指数
INSERT OR IGNORE INTO stocks (code, name, market, industry) VALUES
('000001', '上证指数', 'sh', '指数'),
('000300', '沪深300', 'sh', '指数'),
('000905', '中证500', 'sh', '指数'),
('000016', '上证50', 'sh', '指数'),
('399001', '深证成指', 'sz', '指数'),
('399006', '创业板指', 'sz', '指数'),
('000852', '中证1000', 'sh', '指数');
