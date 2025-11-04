import { describe, it, before, after } from 'node:test';
import assert from 'node:assert';

// Mock localStorage for Node.js environment
const mockLocalStorage = {
  _storage: {},
  getItem: function(key) {
    return this._storage[key] || null;
  },
  setItem: function(key, value) {
    this._storage[key] = value;
  },
  removeItem: function(key) {
    delete this._storage[key];
  },
  clear: function() {
    this._storage = {};
  }
};

describe('重连功能测试', () => {
  let originalLocalStorage;

  before(() => {
    // Mock localStorage
    originalLocalStorage = global.localStorage;
    global.localStorage = mockLocalStorage;
  });

  after(() => {
    global.localStorage = originalLocalStorage;
    mockLocalStorage.clear();
  });

  it('应该能够保存和恢复连接信息', () => {
    // 模拟保存连接信息
    const connectionInfo = {
      roomId: 'test_room',
      player_info: { id: 'player1', name: 'Test' },
      gameType: 'o2SPH'
    };
    
    localStorage.setItem('SPH_LAST_CONNECTION', JSON.stringify(connectionInfo));
    
    // 验证保存成功
    const savedInfo = JSON.parse(localStorage.getItem('SPH_LAST_CONNECTION'));
    assert.ok(savedInfo, '连接信息应该保存到localStorage');
    assert.strictEqual(savedInfo.roomId, 'test_room');
    assert.strictEqual(savedInfo.player_info.id, 'player1');
    
    // 模拟恢复连接
    const restoredInfo = JSON.parse(localStorage.getItem('SPH_LAST_CONNECTION'));
    assert.ok(restoredInfo, '应该能够恢复连接信息');
    assert.strictEqual(restoredInfo.roomId, 'test_room');
  });

  it('应该处理空的连接信息', () => {
    localStorage.removeItem('SPH_LAST_CONNECTION');
    const info = localStorage.getItem('SPH_LAST_CONNECTION');
    assert.strictEqual(info, null, '应该返回null当连接信息不存在时');
  });
});