/**
 * 迷宫解码器JavaScript版本
 * 适用于Vue前端项目
 */

export class SimpleMazeDecoder {
  /**
   * 从比特序列解码maze_data
   * @param {Uint8Array|Array} encodedBytes - 编码的字节数据
   * @returns {Object} 解码后的迷宫数据对象
   */
  decode(encodedBytes) {
    // 验证输入类型
    if (!Array.isArray(encodedBytes) && !(encodedBytes instanceof Uint8Array)) {
      throw new TypeError('输入必须是Uint8Array或Array类型');
    }
    
    // 初始化解码状态
    let byteIndex = 0;
    let bitOffset = 0;
    const totalBytes = encodedBytes.length;
    
    /**
     * 从字节序列中获取单个位
     * @private
     * @returns {number} 单个位的值(0或1)
     */
    const getBit = () => {
      if (byteIndex >= totalBytes) {
        // 如果数据不足，抛出异常
        throw new Error(`解码失败: 数据不足，需要更多位来完成解码`);
      }
      
      // 从当前字节中提取指定位（从最高位开始读取）
      const byte = encodedBytes[byteIndex];
      const bit = (byte >> (7 - bitOffset)) & 1;
      
      // 更新位置
      bitOffset += 1;
      if (bitOffset >= 8) {
        byteIndex += 1;
        bitOffset = 0;
      }
      
      return bit;
    };
    
    /**
     * 从字节序列中获取指定数量的位
     * @private
     * @param {number} numBits - 需要获取的位数
     * @returns {number} 组合后的整数值
     */
    const getBits = (numBits) => {
      let result = 0;
      for (let i = 0; i < numBits; i++) {
        result = (result << 1) | getBit();
      }
      return result;
    };
    
    // 1. 解码rownum (4 bits)
    const rownum = getBits(4);
    if (rownum <= 0) {
      throw new Error(`解码失败: 无效的行数 ${rownum}`);
    }
    const totalCells = rownum * rownum;
    
    // 2. 解码green_index (6 bits)
    const greenIndex = getBits(6);
    if (greenIndex >= totalCells) {
      throw new Error(`解码失败: 绿色起点索引 ${greenIndex} 超出迷宫范围 [0-${totalCells-1}]`);
    }
    
    // 3. 解码red_index (6 bits)
    const redIndex = getBits(6);
    if (redIndex >= totalCells) {
      throw new Error(`解码失败: 红色终点索引 ${redIndex} 超出迷宫范围 [0-${totalCells-1}]`);
    }
    
    // 4. 解码路径长度 (各6 bits)
    const roadlength1 = getBits(6);
    const roadlength2 = getBits(6);
    const pathLength = getBits(6);
    
    // 5. 解码墙壁数据（每个格子4 bits，分别表示上、左、右、下）
    const wall = [];
    try {
      for (let i = 0; i < totalCells; i++) {
        const cell = [
          getBit(),  // 上
          getBit(),  // 左
          getBit(),  // 右
          getBit()   // 下
        ];
        wall.push(cell);
      }
    } catch (error) {
      throw new Error(`解码失败: 在解析第${i+1}个格子的墙壁数据时出现错误 - ${error.message}`);
    }
    
    // 验证墙壁数据完整性
    if (wall.length !== totalCells) {
      throw new Error(`解码失败: 墙壁数据不完整，预期${totalCells}个格子，实际解析到${wall.length}个格子`);
    }
    
    // 构建mazeData对象
    const mazeData = {
      wall: wall,
      rownum: rownum,
      greenIndex: greenIndex,
      redIndex: redIndex,
      roadlength1: roadlength1,
      roadlength2: roadlength2,
      pathLength: pathLength
    };
    
    // 最终验证：确保所有必需字段都被正确解码
    const requiredFields = ['wall', 'rownum', 'greenIndex', 'redIndex', 'roadlength1', 'roadlength2', 'pathLength'];
    for (const field of requiredFields) {
      if (!(field in mazeData)) {
        throw new Error(`解码失败: 缺少必需字段 ${field}`);
      }
    }
    
    return mazeData;
  }
  
  /**
   * 辅助方法：将十六进制字符串转换为字节数组
   * @param {string} hexString - 十六进制字符串
   * @returns {Uint8Array} 转换后的字节数组
   */
  hexToBytes(hexString) {
    // 移除可能存在的空格
    hexString = hexString.replace(/\s/g, '');
    
    if (hexString.length % 2 !== 0) {
      throw new Error('无效的十六进制字符串：长度必须是偶数');
    }
    
    const bytes = new Uint8Array(hexString.length / 2);
    for (let i = 0; i < hexString.length; i += 2) {
      bytes[i / 2] = parseInt(hexString.substr(i, 2), 16);
    }
    return bytes;
  }
}

/**
 * 导出默认的解码器实例
 */
export default SimpleMazeDecoder;