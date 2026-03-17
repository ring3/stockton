/**
 * Stockton Cloud - Cloudflare Workers 主入口
 */
import { Router, jsonResponse, corsPreflight } from './router';
import { Env, StockPrice, MarketStats } from './types';

export { Env } from './types';

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
        message: 'Stockton Cloud is running',
        timestamp: new Date().toISOString()
      });
    });

    // ===== 查询股票历史数据 =====
    router.get('/api/stock/:code', async (context, env) => {
      const { code } = context.params;
      const start = context.query.get('start');
      const end = context.query.get('end');
      const limit = parseInt(context.query.get('limit') || '100');

      // 检查缓存
      const cacheKey = `stock:${code}:${start || ''}:${end || ''}:${limit}`;
      const cached = await env.CACHE.get(cacheKey);
      
      if (cached) {
        return jsonResponse({
          success: true,
          data: JSON.parse(cached),
          cached: true
        });
      }

      try {
        let sql = `
          SELECT code, date, open, high, low, close, volume, amount,
                 ma5, ma10, ma20, ma60, change_pct, turnover_rate
          FROM stock_prices 
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
          data: results.results
        });
      } catch (error) {
        console.error('Query error:', error);
        return jsonResponse({ success: false, error: 'Database error' }, 500);
      }
    });

    // ===== 查询最新数据 =====
    router.get('/api/stock/:code/latest', async (context, env) => {
      const { code } = context.params;

      try {
        const stmt = env.DB.prepare(`
          SELECT code, date, open, high, low, close, volume, amount,
                 ma5, ma10, ma20, ma60, change_pct, turnover_rate
          FROM stock_prices 
          WHERE code = ? 
          ORDER BY date DESC 
          LIMIT 1
        `).bind(code);

        const result = await stmt.first();

        if (!result) {
          return jsonResponse({ success: false, error: 'Stock not found' }, 404);
        }

        return jsonResponse({ success: true, data: result });
      } catch (error) {
        console.error('Query error:', error);
        return jsonResponse({ success: false, error: 'Database error' }, 500);
      }
    });

    // ===== 查询市场概览 =====
    router.get('/api/market/overview', async (_, env) => {
      const cacheKey = 'market:overview';
      const cached = await env.CACHE.get(cacheKey);
      
      if (cached) {
        return jsonResponse({
          success: true,
          data: JSON.parse(cached),
          cached: true
        });
      }

      try {
        const today = new Date().toISOString().split('T')[0];
        
        // 获取最新市场统计
        const statsStmt = env.DB.prepare(`
          SELECT * FROM market_stats 
          WHERE date <= ? 
          ORDER BY date DESC 
          LIMIT 1
        `).bind(today);
        
        const stats = await statsStmt.first();

        // 获取主要指数最新数据
        const indicesStmt = env.DB.prepare(`
          SELECT code, close, change_pct 
          FROM stock_prices 
          WHERE code IN ('000001', '399001', '399006') 
          AND date = (SELECT MAX(date) FROM stock_prices)
        `);
        
        const indices = await indicesStmt.all();

        const data = {
          date: stats?.date || today,
          stats: stats || null,
          indices: indices.results || []
        };

        // 缓存1分钟
        ctx.waitUntil(
          env.CACHE.put(cacheKey, JSON.stringify(data), { expirationTtl: 60 })
        );

        return jsonResponse({ success: true, data });
      } catch (error) {
        console.error('Query error:', error);
        return jsonResponse({ success: false, error: 'Database error' }, 500);
      }
    });

    // ===== 批量更新接口 (内部使用) =====
    router.post('/api/batch_update', async (context, env, request) => {
      // 验证 API Key
      const authHeader = request.headers.get('Authorization');
      if (!authHeader || authHeader !== `Bearer ${env.API_KEY}`) {
        return jsonResponse({ success: false, error: 'Unauthorized' }, 401);
      }

      try {
        const body = await request.json() as { prices?: any[], stats?: MarketStats };
        const { prices, stats } = body;

        const results = { pricesInserted: 0, statsUpdated: 0 };

        // 批量插入价格数据
        if (prices && prices.length > 0) {
          // D1 限制每批最多 100 条
          const batchSize = 100;
          const batches = [];

          for (let i = 0; i < prices.length; i += batchSize) {
            const batch = prices.slice(i, i + batchSize);
            const statements = batch.map(p => {
              return env.DB.prepare(`
                INSERT OR REPLACE INTO stock_prices 
                (code, date, open, high, low, close, volume, amount, 
                 ma5, ma10, ma20, ma60, change_pct, turnover_rate)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
              `).bind(
                p.code, p.date, p.open, p.high, p.low, p.close,
                p.volume, p.amount, p.ma5, p.ma10, p.ma20, p.ma60,
                p.change_pct, p.turnover_rate
              );
            });
            
            batches.push(statements);
          }

          // 执行所有批次
          for (const statements of batches) {
            await env.DB.batch(statements);
          }

          results.pricesInserted = prices.length;

          // 清除相关缓存
          const affectedCodes = [...new Set(prices.map(p => p.code))];
          ctx.waitUntil(clearStockCache(env, affectedCodes));
        }

        // 更新市场统计
        if (stats) {
          await env.DB.prepare(`
            INSERT OR REPLACE INTO market_stats 
            (date, up_count, down_count, flat_count, limit_up_count, limit_down_count, total_amount)
            VALUES (?, ?, ?, ?, ?, ?, ?)
          `).bind(
            stats.date, stats.up_count, stats.down_count, stats.flat_count,
            stats.limit_up_count, stats.limit_down_count, stats.total_amount || 0
          ).run();

          results.statsUpdated = 1;
          
          // 清除市场概览缓存
          await env.CACHE.delete('market:overview');
        }

        return jsonResponse({ 
          success: true, 
          message: `Inserted ${results.pricesInserted} prices, updated ${results.statsUpdated} stats`
        });

      } catch (error) {
        console.error('Batch update error:', error);
        return jsonResponse({ success: false, error: 'Update failed' }, 500);
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

      const result = await env.DB.prepare(`
        DELETE FROM stock_prices WHERE date < ?
      `).bind(cutoffDate).run();

      console.log(`Cleaned up ${result.meta?.changes || 0} old records before ${cutoffDate}`);
    } catch (error) {
      console.error('Cleanup error:', error);
    }
  }
};

// 清除股票缓存
async function clearStockCache(env: Env, codes: string[]) {
  // 清除相关缓存键
  const keys = await env.CACHE.list();
  for (const key of keys.keys) {
    if (codes.some(code => key.name.includes(`stock:${code}:`))) {
      await env.CACHE.delete(key.name);
    }
  }
}
