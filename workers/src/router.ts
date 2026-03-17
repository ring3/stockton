/**
 * 简单路由实现
 */
import { Handler, Context } from './types';

interface Route {
  method: string;
  pattern: RegExp;
  paramNames: string[];
  handler: Handler;
}

export class Router {
  private routes: Route[] = [];

  get(path: string, handler: Handler) {
    this.addRoute('GET', path, handler);
    return this;
  }

  post(path: string, handler: Handler) {
    this.addRoute('POST', path, handler);
    return this;
  }

  private addRoute(method: string, path: string, handler: Handler) {
    // 将 :param 转换为正则
    const paramNames: string[] = [];
    const pattern = path.replace(/:([^/]+)/g, (_, name) => {
      paramNames.push(name);
      return '([^/]+)';
    });

    this.routes.push({
      method,
      pattern: new RegExp(`^${pattern}$`),
      paramNames,
      handler
    });
  }

  async handle(request: Request, env: any): Promise<Response | null> {
    const url = new URL(request.url);
    const pathname = url.pathname;
    const method = request.method;

    for (const route of this.routes) {
      if (route.method !== method) continue;

      const match = pathname.match(route.pattern);
      if (!match) continue;

      // 提取参数
      const params: Record<string, string> = {};
      route.paramNames.forEach((name, i) => {
        params[name] = match[i + 1];
      });

      const ctx: Context = {
        params,
        query: url.searchParams
      };

      try {
        return await route.handler(ctx, env);
      } catch (error) {
        console.error('Route handler error:', error);
        return jsonResponse({ success: false, error: 'Internal error' }, 500);
      }
    }

    return null; // 没有匹配的路由
  }
}

export function jsonResponse(data: any, status = 200, headers: Record<string, string> = {}) {
  return new Response(JSON.stringify(data), {
    status,
    headers: {
      'Content-Type': 'application/json',
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type, Authorization',
      ...headers
    }
  });
}

export function corsPreflight() {
  return new Response(null, {
    status: 204,
    headers: {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type, Authorization',
      'Access-Control-Max-Age': '86400'
    }
  });
}
