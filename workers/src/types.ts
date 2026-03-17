/**
 * 类型定义
 */

// 股票日K数据
export interface StockPrice {
  code: string;
  date: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
  amount: number;
  ma5?: number;
  ma10?: number;
  ma20?: number;
  ma60?: number;
  change_pct?: number;
  turnover_rate?: number;
}

// 股票基本信息
export interface StockInfo {
  code: string;
  name: string;
  market: 'sh' | 'sz';
  industry?: string;
  list_date?: string;
}

// 市场统计
export interface MarketStats {
  date: string;
  up_count: number;
  down_count: number;
  flat_count: number;
  limit_up_count: number;
  limit_down_count: number;
  total_amount?: number;
  sh_index?: number;
  sz_index?: number;
  cy_index?: number;
}

// API 响应格式
export interface ApiResponse<T> {
  success: boolean;
  data: T;
  cached?: boolean;
  message?: string;
}

// 批量更新请求
export interface BatchUpdateRequest {
  prices?: StockPrice[];
  stocks?: StockInfo[];
  stats?: MarketStats;
}

// Worker 环境变量
export interface Env {
  DB: D1Database;
  CACHE: KVNamespace;
  API_KEY: string;
  ENVIRONMENT: string;
}

// 路由上下文
export interface Context {
  params: Record<string, string>;
  query: URLSearchParams;
}

export type Handler = (ctx: Context, env: Env) => Promise<Response> | Response;
