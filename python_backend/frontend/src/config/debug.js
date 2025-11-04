// 调试模式配置
export const DEBUG_CONFIG = {
  // 从URL参数获取调试模式
  getDebugModeFromURL() {
    const urlParams = new URLSearchParams(window.location.search);
    return urlParams.get('debug') === 'true';
  },
  
  // 从localStorage获取调试模式
  getDebugModeFromStorage() {
    return localStorage.getItem('DEBUG_MODE') === 'true';
  },
  
  // 设置调试模式
  setDebugMode(enabled) {
    if (enabled) {
      localStorage.setItem('DEBUG_MODE', 'true');
      console.log('🔧 调试模式已启用');
    } else {
      localStorage.removeItem('DEBUG_MODE');
      console.log('🔧 调试模式已禁用');
    }
  },
  
  // 检查是否启用调试模式
  isDebugModeEnabled() {
    return this.getDebugModeFromURL() || this.getDebugModeFromStorage();
  },
  
  // 初始化调试模式
  init() {
    const debugFromURL = this.getDebugModeFromURL();
    if (debugFromURL) {
      this.setDebugMode(true);
      console.log('🔧 从URL参数启用调试模式');
    }
    
    return this.isDebugModeEnabled();
  }
};

// 导出单例
export default DEBUG_CONFIG;