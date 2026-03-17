/**
 * Stockton Cloud V2 - 支持分表的 Cloudflare Workers 主入口
 * 
 * 表结构：
 * - stock_prices_000300: 沪深300成分股
 * - stock_prices_000905: 中证500成分股
 * - etf_data_table: 所有ETF统一存储
 */
import { Router, jsonResponse, corsPreflight } from './router';
import { Env, StockPrice, MarketStats } from './types';

export { Env } from './types';

// 表名映射：本地表名 -> Workers D1 表名（简化命名）
const TABLE_NAME_MAP: Record<string, string> = {
  // 指数成分股表
  'data_if300': 'data_if300',
  'data_ic500': 'data_ic500',
  // ETF统一表
  'data_etf': 'data_etf',
};

// 支持的ETF代码（用于查询验证）
const ETF_CODES = ['510050', '510300', '588000', '159915', '510500'];

export default {
  async fetch(request: Request, env: Env, ctx: ExecutionContext): Promise<Response> {
    // CORS 预检
    if (request.method === 'OPTIONS') {
      return corsPreflight();
    }

    const router = new Router();

    // ===== 健康检查 =====
    router.get('/health', () => {
      return jsonResponse({ 
        success: true, 
        message: 'Stockton Cloud V2 is running',
        version: '2.1.0',
        timestamp: new Date().toISOString()
      });
    });

    // ===== 查询股票历史数据（指数成分股） =====
    router.get('/api/stock/:code', async (context, env) => {
      const { code } = context.params;
      const start = context.query.get('start');
      const end = context.query.get('end');
      const limit = parseInt(context.query.get('limit') || '100');
      const table = context.query.get('table') || 'data_if300';

      // 验证表名
      if (!TABLE_NAME_MAP[table]) {
        return jsonResponse({ success: false, error: 'Invalid table name' }, 400);
      }

      // 检查缓存
      const cacheKey = `${table}:${code}:${start || ''}:${end || ''}:${limit}`;
      const cached = await env.CACHE.get(cacheKey);
      
      if (cached) {
        return jsonResponse({
          success: true,
          data: JSON.parse(cached),
          cached: true
        });
      }

      try {
        const tableName = TABLE_NAME_MAP[table];
        
        let sql = `
          SELECT code, date, open, high, low, close, volume, amount,
                 ma5, ma10, ma20, ma60, change_pct, turnover_rate
          FROM ${tableName} 
          WHERE code = ? 
        `;
        const bindings: any[] = [code];

        if (start) {
          sql += ' AND date >= ?';
          bindings.push(start);
        }
        if (end) {
          sql += ' AND date <= ?';
          bindings.push(end);
        }

        sql += ' ORDER BY date DESC LIMIT ?';
        bindings.push(limit);

        const stmt = env.DB.prepare(sql).bind(...bindings);
        const results = await stmt.all();

        // 写入缓存 (5分钟)
        ctx.waitUntil(
          env.CACHE.put(cacheKey, JSON.stringify(results.results), { expirationTtl: 300 })
        );

        return jsonResponse({
          success: true,
          data: results.results,
          table: tableName
        });
      } catch (error) {
        console.error('Query error:', error);
        return jsonResponse({ success: false, error: 'Database error' }, 500);
      }
    });

    // ===== 查询最新数据 =====
    router.get('/api/stock/:code/latest', async (context, env) => {
      const { code } = context.params;
      const table = context.query.get('table') || 'data_if300';

      if (!TABLE_NAME_MAP[table]) {
        return jsonResponse({ success: false, error: 'Invalid table name' }, 400);
      }

      try {
        const tableName = TABLE_NAME_MAP[table];
        
        const stmt = env.DB.prepare(`
          SELECT code, date, open, high, low, close, volume, amount,
                 ma5, ma10, ma20, ma60, change_pct, turnover_rate
          FROM ${tableName} 
          WHERE code = ? 
          ORDER BY date DESC 
          LIMIT 1
        `).bind(code);

        const result = await stmt.first();

        if (!result) {
          return jsonResponse({ success: false, error: 'Stock not found' }, 404);
        }

        return jsonResponse({ 
          success: true, 
          data: result,
          table: tableName
        });
      } catch (error) {
        console.error('Query error:', error);
        return jsonResponse({ success: false, error: 'Database error' }, 500);
      }
    });

    // ===== 查询ETF列表 =====
    router.get('/api/etfs', async (context, env) => {
      try {
        // 从ETF表中获取所有不同的ETF代码
        const stmt = env.DB.prepare(`
          SELECT DISTINCT code, name 
          FROM data_etf 
          ORDER BY code
        `);
        
        const results = await stmt.all();
        
        return jsonResponse({
          success: true,
          data: results.results
        });
      } catch (error) {
        console.error('Query error:', error);
        return jsonResponse({ success: false, error: 'Database error' }, 500);
      }
    });

    // ===== 批量更新接口 V2 (分表支持) =====
    router.post('/api/batch_update_v2', async (context, env, request) => {
      // 验证 API Key
      const authHeader = request.headers.get('Authorization');
      if (!authHeader || authHeader !== `Bearer ${env.API_KEY}`) {
        return jsonResponse({ success: false, error: 'Unauthorized' }, 401);
      }

      try {
        const body = await request.json() as { 
          table?: string,
          code?: string,
          code_type?: string,
          prices?: any[], 
          stats?: MarketStats 
        };
        
        const { table, code, code_type, prices, stats } = body;

        // 验证表名
        if (!table || !TABLE_NAME_MAP[table]) {
          return jsonResponse({ 
            success: false, 
            error: `Invalid or missing table name. Supported: ${Object.keys(TABLE_NAME_MAP).join(', ')}` 
          }, 400);
        }

        const tableName = TABLE_NAME_MAP[table];
        const results = { pricesInserted: 0, statsUpdated: 0 };

        // 批量插入价格数据
        if (prices && prices.length > 0) {
          // D1 限制每批最多 100 条
          const batchSize = 100;
          const batches = [];

          for (let i = 0; i < prices.length; i += batchSize) {
            const batch = prices.slice(i, i + batchSize);
            
            // 根据表类型构建不同的插入语句
            let statements;
            if (tableName === 'etf_data_table') {
              // ETF表有name字段
              statements = batch.map(p => {
                return env.DB.prepare(`
                  INSERT OR REPLACE INTO ${tableName} 
                  (code, name, date, open, high, low, close, volume, amount, 
                   ma5, ma10, ma20, ma60, change_pct, turnover_rate)
                  VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                `).bind(
                  p.code, p.name || '', p.date, p.open, p.high, p.low, p.close,
                  p.volume, p.amount, p.ma5, p.ma10, p.ma20, p.ma60,
                  p.change_pct, p.turnover_rate
                );
              });
            } else {
              // 指数成分股表没有name字段
              statements = batch.map(p => {
                return env.DB.prepare(`
                  INSERT OR REPLACE INTO ${tableName} 
                  (code, date, open, high, low, close, volume, amount, 
                   ma5, ma10, ma20, ma60, change_pct, turnover_rate)
                  VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                `).bind(
                  p.code, p.date, p.open, p.high, p.low, p.close,
                  p.volume, p.amount, p.ma5, p.ma10, p.ma20, p.ma60,
                  p.change_pct, p.turnover_rate
                );
              });
            }
            
            batches.push(statements);
          }

          // 执行所有批次
          for (const statements of batches) {
            await env.DB.batch(statements);
          }

          results.pricesInserted = prices.length;

          // 清除相关缓存
          const affectedCodes = [...new Set(prices.map(p => p.code))];
          ctx.waitUntil(clearStockCache(env, affectedCodes, table));
        }

        return jsonResponse({ 
          success: true, 
          table: tableName,
          code: code,
          code_type: code_type,
          message: `Inserted ${results.pricesInserted} prices into ${tableName}`
        });

      } catch (error) {
        console.error('Batch update error:', error);
        return jsonResponse({ success: false, error: 'Update failed: ' + String(error) }, 500);
      }
    });

    // ===== 查询数据库状态 =====
    router.get('/api/db_status', async (context, env) => {
      // 验证 API Key
      const authHeader = context.headers?.get('Authorization');
      if (!authHeader || authHeader !== `Bearer ${env.API_KEY}`) {
        return jsonResponse({ success: false, error: 'Unauthorized' }, 401);
      }

      try {
        const stats: Record<string, number> = {};
        
        // 查询各表记录数
        for (const [localName, dbName] of Object.entries(TABLE_NAME_MAP)) {
          try {
            const result = await env.DB.prepare(`
              SELECT COUNT(*) as count FROM ${dbName}
            `).first();
            stats[localName] = result?.count || 0;
          } catch (e) {
            stats[localName] = -1; // 表可能不存在
          }
        }

        // 查询ETF列表
        let etfList: any[] = [];
        try {
          const etfResult = await env.DB.prepare(`
            SELECT DISTINCT code, name FROM etf_data_table ORDER BY code
          `).all();
          etfList = etfResult.results || [];
        } catch (e) {
          // ETF表可能为空
        }

        return jsonResponse({
          success: true,
          tables: stats,
          etfs: etfList,
          timestamp: new Date().toISOString()
        });
      } catch (error) {
        console.error('DB status error:', error);
        return jsonResponse({ success: false, error: 'Query failed' }, 500);
      }
    });

    // 处理请求
    const response = await router.handle(request, env);
    
    if (response) {
      return response;
    }

    // 404
    return jsonResponse({ success: false, error: 'Not found' }, 404);
  },

  // 定时任务：清理旧数据
  async scheduled(event: ScheduledEvent, env: Env, ctx: ExecutionContext) {
    console.log('Running scheduled cleanup task...');
    
    try {
      // 删除2年前的数据
      const twoYearsAgo = new Date();
      twoYearsAgo.setFullYear(twoYearsAgo.getFullYear() - 2);
      const cutoffDate = twoYearsAgo.toISOString().split('T')[0];

      let totalDeleted = 0;

      // 清理所有表
      for (const tableName of Object.values(TABLE_NAME_MAP)) {
        try {
          const result = await env.DB.prepare(`
            DELETE FROM ${tableName} WHERE date < ?
          `).bind(cutoffDate).run();
          
          const deleted = result.meta?.changes || 0;
          totalDeleted += deleted;
          console.log(`Cleaned ${deleted} old records from ${tableName}`);
        } catch (e) {
          console.error(`Failed to clean ${tableName}:`, e);
        }
      }

      console.log(`Total cleaned: ${totalDeleted} records before ${cutoffDate}`);
    } catch (error) {
      console.error('Cleanup error:', error);
    }
  }
};

// 清除股票缓存
async function clearStockCache(env: Env, codes: string[], table: string) {
  // 清除相关缓存键
  const keys = await env.CACHE.list();
  for (const key of keys.keys) {
    if (codes.some(code => key.name.includes(`${table}:${code}:`))) {
      await env.CACHE.delete(key.name);
    }
  }
}
