-- Stockton Cloud Database Schema V2
-- 支持分表：指数成分股分表，ETF统一表

-- ============================================
-- 指数成分股数据表
-- ============================================

-- 沪深300成分股数据表
CREATE TABLE IF NOT EXISTS data_if300 (
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

-- 中证500成分股数据表
CREATE TABLE IF NOT EXISTS data_ic500 (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT NOT NULL,
    date TEXT NOT NULL,
    open REAL,
    high REAL,
    low REAL,
    close REAL,
    volume INTEGER,
    amount REAL,
    ma5 REAL,
    ma10 REAL,
    ma20 REAL,
    ma60 REAL,
    change_pct REAL,
    turnover_rate REAL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(code, date)
);

-- ============================================
-- ETF统一数据表（所有ETF存于此表）
-- ============================================

CREATE TABLE IF NOT EXISTS etf_data_table (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT NOT NULL,              -- ETF代码
    name TEXT,                       -- ETF名称
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

-- ============================================
-- 索引优化
-- ============================================

-- 沪深300索引
CREATE INDEX IF NOT EXISTS idx_if300_code_date ON data_if300(code, date);
CREATE INDEX IF NOT EXISTS idx_if300_date ON data_if300(date);

-- 中证500索引
CREATE INDEX IF NOT EXISTS idx_ic500_code_date ON data_ic500(code, date);
CREATE INDEX IF NOT EXISTS idx_ic500_date ON data_ic500(date);

-- ETF统一表索引
CREATE INDEX IF NOT EXISTS idx_etf_code_date ON data_etf(code, date);
CREATE INDEX IF NOT EXISTS idx_etf_date ON data_etf(date);
CREATE INDEX IF NOT EXISTS idx_etf_code ON data_etf(code);

-- ============================================
-- 元数据表
-- ============================================

-- 表信息记录
CREATE TABLE IF NOT EXISTS table_metadata (
    table_name TEXT PRIMARY KEY,
    code TEXT NOT NULL,              -- 指数/ETF代码
    code_type TEXT NOT NULL,         -- 'index' 或 'etf'
    name TEXT,                       -- 名称
    description TEXT,
    record_count INTEGER DEFAULT 0,
    last_sync_at DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 初始化元数据
INSERT OR IGNORE INTO table_metadata (table_name, code, code_type, name, description) VALUES
('data_if300', '000300', 'index', '沪深300', '沪深300指数成分股'),
('data_ic500', '000905', 'index', '中证500', '中证500指数成分股'),
('data_etf', 'ETF', 'etf', 'ETF数据', 'ETF统一存储');
