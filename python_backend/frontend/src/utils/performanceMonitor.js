/**
 * 性能监控工具 - 用于监控房间加载性能
 */

class PerformanceMonitor {
  constructor() {
    this.metrics = new Map();
    this.startTimes = new Map();
  }

  /**
   * 开始计时
   * @param {string} metricName - 指标名称
   */
  start(metricName) {
    this.startTimes.set(metricName, Date.now());
    console.log(`⏱️ [${metricName}] 开始计时`);
  }

  /**
   * 结束计时并记录指标
   * @param {string} metricName - 指标名称
   * @param {object} additionalData - 附加数据
   */
  end(metricName, additionalData = {}) {
    const startTime = this.startTimes.get(metricName);
    if (!startTime) {
      console.warn(`⚠️ 未找到指标 "${metricName}" 的开始时间`);
      return null;
    }

    const duration = Date.now() - startTime;
    this.metrics.set(metricName, {
      duration,
      timestamp: Date.now(),
      ...additionalData
    });

    console.log(`✅ [${metricName}] 完成，耗时: ${duration}ms`);
    this.startTimes.delete(metricName);
    
    return duration;
  }

  /**
   * 获取所有指标
   */
  getMetrics() {
    return Object.fromEntries(this.metrics);
  }

  /**
   * 清空所有指标
   */
  clear() {
    this.metrics.clear();
    this.startTimes.clear();
  }

  /**
   * 监控页面加载性能
   */
  monitorPageLoad() {
    if (typeof window !== 'undefined') {
      window.addEventListener('load', () => {
        const loadTime = Date.now() - performance.timing.navigationStart;
        this.metrics.set('page_load', {
          duration: loadTime,
          timestamp: Date.now()
        });
        console.log(`🌐 页面加载完成，耗时: ${loadTime}ms`);
      });
    }
  }

  /**
   * 监控API请求性能
   * @param {string} url - API地址
   * @param {function} originalFetch - 原始的fetch函数
   */
  monitorAPICalls() {
    if (typeof window !== 'undefined') {
      const originalFetch = window.fetch;
      
      window.fetch = async (...args) => {
        const startTime = Date.now();
        const url = args[0];
        
        try {
          const response = await originalFetch(...args);
          const duration = Date.now() - startTime;
          
          this.metrics.set(`api_${url}`, {
            duration,
            timestamp: Date.now(),
            status: response.status,
            url
          });
          
          console.log(`📡 API调用 [${url}] 完成，耗时: ${duration}ms, 状态: ${response.status}`);
          
          return response;
        } catch (error) {
          const duration = Date.now() - startTime;
          console.error(`❌ API调用 [${url}] 失败，耗时: ${duration}ms`, error);
          throw error;
        }
      };
    }
  }
}

// 创建全局性能监控实例
const performanceMonitor = new PerformanceMonitor();

// 自动开始监控
if (typeof window !== 'undefined') {
  performanceMonitor.monitorPageLoad();
  performanceMonitor.monitorAPICalls();
}

export default performanceMonitor;