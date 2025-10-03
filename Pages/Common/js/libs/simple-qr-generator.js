/**
 * 简单可靠的QR码生成器 v2.0.0
 * 基于 QRCode.js (davidshimjs/qrcodejs)
 * 
 * 特性:
 * - 纯JavaScript，无依赖
 * - 支持Canvas和图片输出
 * - 高容错率
 * - 移动端兼容
 */

(function(global) {
    'use strict';
    
    // 版本信息
    var VERSION = '2.0.0';
    
    console.log('🔄 加载简单QR码生成器 v' + VERSION);
    
    /**
     * 简单QR码生成器构造函数
     */
    function SimpleQRCodeGenerator() {
        this.name = 'SimpleQRCodeGenerator';
        this.version = VERSION;
        
        // 检查QRCode库是否可用
        if (typeof global.QRCode === 'undefined') {
            console.error('❌ QRCode库未找到，请先加载qrcode.js');
            return null;
        }
        
        console.log('✅ SimpleQRCodeGenerator v' + VERSION + ' 初始化成功');
    }
    
    /**
     * 生成QR码并返回Data URL
     * @param {string} text - 要编码的文本
     * @param {object} options - 生成选项
     * @returns {Promise<string>} - 返回图片的Data URL
     */
    SimpleQRCodeGenerator.prototype.generate = function(text, options) {
        return new Promise(function(resolve, reject) {
            try {
                // 检查QRCode库
                if (typeof global.QRCode === 'undefined') {
                    throw new Error('QRCode库未加载');
                }
                
                // 默认选项
                var defaultOptions = {
                    size: 256,
                    level: 'H', // 高容错率 (L, M, Q, H)
                    background: '#ffffff',
                    foreground: '#000000'
                };
                
                // 合并选项
                var config = {};
                for (var key in defaultOptions) {
                    config[key] = (options && options[key] !== undefined) ? options[key] : defaultOptions[key];
                }
                
                console.log('🚀 开始生成QR码:', {
                    text: text.substring(0, 50) + (text.length > 50 ? '...' : ''),
                    size: config.size,
                    level: config.level
                });
                
                // 创建临时DOM元素
                var tempDiv = document.createElement('div');
                tempDiv.style.position = 'absolute';
                tempDiv.style.left = '-9999px';
                tempDiv.style.top = '-9999px';
                document.body.appendChild(tempDiv);
                
                // 创建QRCode实例
                var qrcode = new global.QRCode(tempDiv, {
                    text: text,
                    width: config.size,
                    height: config.size,
                    colorDark: config.foreground,
                    colorLight: config.background,
                    correctLevel: global.QRCode.CorrectLevel[config.level]
                });
                
                // 等待生成完成
                setTimeout(function() {
                    try {
                        // 查找生成的canvas或img元素
                        var canvas = tempDiv.querySelector('canvas');
                        var img = tempDiv.querySelector('img');
                        
                        if (canvas) {
                            // 从canvas获取数据
                            var dataUrl = canvas.toDataURL('image/png');
                            document.body.removeChild(tempDiv);
                            console.log('✅ QR码生成成功 (Canvas)');
                            resolve(dataUrl);
                        } else if (img) {
                            // 从img获取数据
                            var dataUrl = img.src;
                            document.body.removeChild(tempDiv);
                            console.log('✅ QR码生成成功 (Image)');
                            resolve(dataUrl);
                        } else {
                            throw new Error('未找到生成的QR码元素');
                        }
                    } catch (error) {
                        document.body.removeChild(tempDiv);
                        console.error('❌ QR码数据提取失败:', error);
                        reject(error);
                    }
                }, 100); // 给一点时间让QR码生成
                
            } catch (error) {
                console.error('❌ QR码生成异常:', error);
                reject(error);
            }
        });
    };
    
    /**
     * 生成QR码到指定的Canvas元素
     * @param {HTMLCanvasElement} canvas - 目标canvas元素
     * @param {string} text - 要编码的文本
     * @param {object} options - 生成选项
     */
    SimpleQRCodeGenerator.prototype.generateToCanvas = function(canvas, text, options) {
        var self = this;
        return self.generate(text, options).then(function(dataUrl) {
            return new Promise(function(resolve, reject) {
                var img = new Image();
                img.onload = function() {
                    var ctx = canvas.getContext('2d');
                    canvas.width = options && options.size ? options.size : 256;
                    canvas.height = canvas.width;
                    ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
                    console.log('✅ QR码已绘制到Canvas');
                    resolve(canvas);
                };
                img.onerror = function() {
                    reject(new Error('QR码图片加载失败'));
                };
                img.src = dataUrl;
            });
        });
    };
    
    /**
     * 快速生成QR码 (简化版API)
     * @param {string} text - 要编码的文本
     * @param {number} size - 尺寸 (可选，默认256)
     */
    SimpleQRCodeGenerator.prototype.quick = function(text, size) {
        return this.generate(text, {
            size: size || 256,
            level: 'H'
        });
    };
    
    // 创建全局实例
    var simpleQRGenerator = new SimpleQRCodeGenerator();
    
    // 全局暴露
    global.SimpleQRCodeGenerator = SimpleQRCodeGenerator;
    global.simpleQRGenerator = simpleQRGenerator;
    
    // 兼容性函数
    global.simpleQRGenerate = function(text, options) {
        if (simpleQRGenerator) {
            return simpleQRGenerator.generate(text, options);
        } else {
            return Promise.reject(new Error('SimpleQRCodeGenerator初始化失败'));
        }
    };
    
    // 更新ReliableQRCode以使用新的生成器
    global.ReliableQRCode = {
        generate: function(text, options) {
            console.log('📡 ReliableQRCode调用转发到SimpleQRCodeGenerator');
            return global.simpleQRGenerate(text, options);
        },
        version: VERSION,
        name: 'ReliableQRCode (powered by QRCode.js)'
    };
    
    console.log('✅ SimpleQRCodeGenerator v' + VERSION + ' 已加载完成');
    console.log('📋 可用方法:');
    console.log('  - simpleQRGenerator.generate(text, options)');
    console.log('  - simpleQRGenerator.generateToCanvas(canvas, text, options)');
    console.log('  - simpleQRGenerator.quick(text, size)');
    console.log('  - simpleQRGenerate(text, options) // 快捷函数');
    console.log('  - ReliableQRCode.generate(text, options) // 兼容接口');
    
})(window);