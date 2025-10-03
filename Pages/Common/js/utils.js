/**
 * NISA Welcome System - 通用JavaScript工具库
 * 提供系统中通用的功能和工具函数
 */

// 系统配置
const NISA_CONFIG = {
    API_BASE_URL: '/api',
    ASSETS_BASE_URL: '/Pages',
    ANIMATION_DURATION: 300,
    DEBOUNCE_DELAY: 300,
    TOAST_DURATION: 3000
};

/**
 * 工具函数库
 */
class NISAUtils {
    /**
     * 防抖函数
     * @param {Function} func 要防抖的函数
     * @param {number} delay 延迟时间（毫秒）
     * @returns {Function} 防抖后的函数
     */
    static debounce(func, delay = NISA_CONFIG.DEBOUNCE_DELAY) {
        let timeoutId;
        return function (...args) {
            clearTimeout(timeoutId);
            timeoutId = setTimeout(() => func.apply(this, args), delay);
        };
    }

    /**
     * 节流函数
     * @param {Function} func 要节流的函数
     * @param {number} delay 间隔时间（毫秒）
     * @returns {Function} 节流后的函数
     */
    static throttle(func, delay = NISA_CONFIG.DEBOUNCE_DELAY) {
        let lastCall = 0;
        return function (...args) {
            const now = Date.now();
            if (now - lastCall >= delay) {
                lastCall = now;
                return func.apply(this, args);
            }
        };
    }

    /**
     * 深拷贝对象
     * @param {any} obj 要拷贝的对象
     * @returns {any} 拷贝后的对象
     */
    static deepClone(obj) {
        if (obj === null || typeof obj !== 'object') return obj;
        if (obj instanceof Date) return new Date(obj.getTime());
        if (obj instanceof Array) return obj.map(item => this.deepClone(item));
        if (typeof obj === 'object') {
            const cloned = {};
            Object.keys(obj).forEach(key => {
                cloned[key] = this.deepClone(obj[key]);
            });
            return cloned;
        }
    }

    /**
     * 格式化日期
     * @param {Date|string|number} date 日期
     * @param {string} format 格式字符串
     * @returns {string} 格式化后的日期字符串
     */
    static formatDate(date, format = 'YYYY-MM-DD HH:mm:ss') {
        const d = new Date(date);
        const year = d.getFullYear();
        const month = String(d.getMonth() + 1).padStart(2, '0');
        const day = String(d.getDate()).padStart(2, '0');
        const hours = String(d.getHours()).padStart(2, '0');
        const minutes = String(d.getMinutes()).padStart(2, '0');
        const seconds = String(d.getSeconds()).padStart(2, '0');

        return format
            .replace('YYYY', year)
            .replace('MM', month)
            .replace('DD', day)
            .replace('HH', hours)
            .replace('mm', minutes)
            .replace('ss', seconds);
    }

    /**
     * 生成随机ID
     * @param {number} length ID长度
     * @returns {string} 随机ID
     */
    static generateId(length = 8) {
        const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
        let result = '';
        for (let i = 0; i < length; i++) {
            result += chars.charAt(Math.floor(Math.random() * chars.length));
        }
        return result;
    }

    /**
     * 验证学号格式
     * @param {string} stuId 学号
     * @returns {boolean} 是否有效
     */
    static validateStuId(stuId) {
        // 学号应该是6-20位数字和字母的组合
        const pattern = /^[a-zA-Z0-9]{6,20}$/;
        return pattern.test(stuId);
    }

    /**
     * 验证密码强度
     * @param {string} password 密码
     * @returns {object} 验证结果
     */
    static validatePassword(password) {
        const result = {
            valid: true,
            strength: 0,
            messages: []
        };

        if (!password) {
            result.valid = false;
            result.messages.push('密码不能为空');
            return result;
        }

        if (password.length < 6) {
            result.valid = false;
            result.messages.push('密码长度至少6位');
        }

        if (password.length >= 8) result.strength += 1;
        if (/[a-z]/.test(password)) result.strength += 1;
        if (/[A-Z]/.test(password)) result.strength += 1;
        if (/[0-9]/.test(password)) result.strength += 1;
        if (/[^a-zA-Z0-9]/.test(password)) result.strength += 1;

        return result;
    }

    /**
     * 获取URL参数
     * @param {string} name 参数名
     * @returns {string|null} 参数值
     */
    static getUrlParam(name) {
        const urlParams = new URLSearchParams(window.location.search);
        return urlParams.get(name);
    }

    /**
     * 设置URL参数
     * @param {string} name 参数名
     * @param {string} value 参数值
     */
    static setUrlParam(name, value) {
        const url = new URL(window.location);
        url.searchParams.set(name, value);
        window.history.replaceState({}, '', url);
    }
}

/**
 * HTTP请求工具类
 */
class NISAHttp {
    /**
     * 发送GET请求
     * @param {string} url 请求URL
     * @param {object} options 请求选项
     * @returns {Promise} 请求Promise
     */
    static async get(url, options = {}) {
        return this.request(url, { ...options, method: 'GET' });
    }

    /**
     * 发送POST请求
     * @param {string} url 请求URL
     * @param {any} data 请求数据
     * @param {object} options 请求选项
     * @returns {Promise} 请求Promise
     */
    static async post(url, data, options = {}) {
        return this.request(url, {
            ...options,
            method: 'POST',
            body: JSON.stringify(data),
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            }
        });
    }

    /**
     * 发送PUT请求
     * @param {string} url 请求URL
     * @param {any} data 请求数据
     * @param {object} options 请求选项
     * @returns {Promise} 请求Promise
     */
    static async put(url, data, options = {}) {
        return this.request(url, {
            ...options,
            method: 'PUT',
            body: JSON.stringify(data),
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            }
        });
    }

    /**
     * 发送DELETE请求
     * @param {string} url 请求URL
     * @param {object} options 请求选项
     * @returns {Promise} 请求Promise
     */
    static async delete(url, options = {}) {
        return this.request(url, { ...options, method: 'DELETE' });
    }

    /**
     * 通用请求方法
     * @param {string} url 请求URL
     * @param {object} options 请求选项
     * @returns {Promise} 请求Promise
     */
    static async request(url, options = {}) {
        // 添加基础URL
        const fullUrl = url.startsWith('http') ? url : `${NISA_CONFIG.API_BASE_URL}${url}`;
        
        try {
            const response = await fetch(fullUrl, {
                ...options,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    ...options.headers
                }
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const contentType = response.headers.get('content-type');
            if (contentType && contentType.includes('application/json')) {
                return await response.json();
            } else {
                return await response.text();
            }
        } catch (error) {
            console.error('请求失败:', error);
            throw error;
        }
    }
}

/**
 * 本地存储工具类
 */
class NISAStorage {
    /**
     * 设置本地存储
     * @param {string} key 键名
     * @param {any} value 值
     * @param {number} expires 过期时间（毫秒）
     */
    static set(key, value, expires = null) {
        const item = {
            value,
            expires: expires ? Date.now() + expires : null
        };
        localStorage.setItem(`nisa_${key}`, JSON.stringify(item));
    }

    /**
     * 获取本地存储
     * @param {string} key 键名
     * @returns {any} 值
     */
    static get(key) {
        const item = localStorage.getItem(`nisa_${key}`);
        if (!item) return null;

        try {
            const parsed = JSON.parse(item);
            if (parsed.expires && Date.now() > parsed.expires) {
                this.remove(key);
                return null;
            }
            return parsed.value;
        } catch {
            return null;
        }
    }

    /**
     * 删除本地存储
     * @param {string} key 键名
     */
    static remove(key) {
        localStorage.removeItem(`nisa_${key}`);
    }

    /**
     * 清空本地存储
     */
    static clear() {
        const keys = Object.keys(localStorage);
        keys.forEach(key => {
            if (key.startsWith('nisa_')) {
                localStorage.removeItem(key);
            }
        });
    }
}

/**
 * 消息提示工具类
 */
class NISAToast {
    /**
     * 显示成功消息
     * @param {string} message 消息内容
     * @param {number} duration 显示时长
     */
    static success(message, duration = NISA_CONFIG.TOAST_DURATION) {
        this.show(message, 'success', duration);
    }

    /**
     * 显示错误消息
     * @param {string} message 消息内容
     * @param {number} duration 显示时长
     */
    static error(message, duration = NISA_CONFIG.TOAST_DURATION) {
        this.show(message, 'error', duration);
    }

    /**
     * 显示警告消息
     * @param {string} message 消息内容
     * @param {number} duration 显示时长
     */
    static warning(message, duration = NISA_CONFIG.TOAST_DURATION) {
        this.show(message, 'warning', duration);
    }

    /**
     * 显示信息消息
     * @param {string} message 消息内容
     * @param {number} duration 显示时长
     */
    static info(message, duration = NISA_CONFIG.TOAST_DURATION) {
        this.show(message, 'info', duration);
    }

    /**
     * 显示消息提示
     * @param {string} message 消息内容
     * @param {string} type 消息类型
     * @param {number} duration 显示时长
     */
    static show(message, type = 'info', duration = NISA_CONFIG.TOAST_DURATION) {
        // 创建toast容器（如果不存在）
        let container = document.getElementById('nisa-toast-container');
        if (!container) {
            container = document.createElement('div');
            container.id = 'nisa-toast-container';
            container.className = 'nisa-toast-container';
            document.body.appendChild(container);
        }

        // 创建toast元素
        const toast = document.createElement('div');
        toast.className = `nisa-toast nisa-toast-${type}`;
        toast.innerHTML = `
            <div class="nisa-toast-content">
                <i class="nisa-toast-icon fas ${this.getIcon(type)}"></i>
                <span class="nisa-toast-message">${message}</span>
                <button class="nisa-toast-close" onclick="this.parentElement.parentElement.remove()">
                    <i class="fas fa-times"></i>
                </button>
            </div>
        `;

        container.appendChild(toast);

        // 添加显示动画
        setTimeout(() => toast.classList.add('show'), 10);

        // 自动移除
        setTimeout(() => {
            toast.classList.remove('show');
            setTimeout(() => toast.remove(), 300);
        }, duration);
    }

    /**
     * 获取消息类型对应的图标
     * @param {string} type 消息类型
     * @returns {string} 图标类名
     */
    static getIcon(type) {
        const icons = {
            success: 'fa-check-circle',
            error: 'fa-exclamation-circle',
            warning: 'fa-exclamation-triangle',
            info: 'fa-info-circle'
        };
        return icons[type] || icons.info;
    }
}

/**
 * DOM操作工具类
 */
class NISADom {
    /**
     * 查询元素
     * @param {string} selector 选择器
     * @param {Element} context 上下文元素
     * @returns {Element} 元素
     */
    static $(selector, context = document) {
        return context.querySelector(selector);
    }

    /**
     * 查询所有元素
     * @param {string} selector 选择器
     * @param {Element} context 上下文元素
     * @returns {NodeList} 元素列表
     */
    static $$(selector, context = document) {
        return context.querySelectorAll(selector);
    }

    /**
     * 创建元素
     * @param {string} tag 标签名
     * @param {object} attributes 属性对象
     * @param {string} content 内容
     * @returns {Element} 元素
     */
    static create(tag, attributes = {}, content = '') {
        const element = document.createElement(tag);
        Object.entries(attributes).forEach(([key, value]) => {
            if (key === 'className') {
                element.className = value;
            } else if (key === 'innerHTML') {
                element.innerHTML = value;
            } else {
                element.setAttribute(key, value);
            }
        });
        if (content) element.textContent = content;
        return element;
    }

    /**
     * 添加CSS类
     * @param {Element} element 元素
     * @param {string} className 类名
     */
    static addClass(element, className) {
        element.classList.add(className);
    }

    /**
     * 移除CSS类
     * @param {Element} element 元素
     * @param {string} className 类名
     */
    static removeClass(element, className) {
        element.classList.remove(className);
    }

    /**
     * 切换CSS类
     * @param {Element} element 元素
     * @param {string} className 类名
     */
    static toggleClass(element, className) {
        element.classList.toggle(className);
    }

    /**
     * 检查是否包含CSS类
     * @param {Element} element 元素
     * @param {string} className 类名
     * @returns {boolean} 是否包含
     */
    static hasClass(element, className) {
        return element.classList.contains(className);
    }
}

// 全局暴露工具类
window.NISA = {
    Config: NISA_CONFIG,
    Utils: NISAUtils,
    Http: NISAHttp,
    Storage: NISAStorage,
    Toast: NISAToast,
    Dom: NISADom
};

// DOM加载完成后的初始化
document.addEventListener('DOMContentLoaded', () => {
    console.log('NISA Welcome System - 通用工具库已加载');
    
    // 添加toast样式（如果不存在）
    if (!document.getElementById('nisa-toast-styles')) {
        const style = document.createElement('style');
        style.id = 'nisa-toast-styles';
        style.textContent = `
            .nisa-toast-container {
                position: fixed;
                top: 20px;
                right: 20px;
                z-index: 10000;
                pointer-events: none;
            }
            
            .nisa-toast {
                margin-bottom: 10px;
                pointer-events: auto;
                opacity: 0;
                transform: translateX(100%);
                transition: all 0.3s ease-out;
            }
            
            .nisa-toast.show {
                opacity: 1;
                transform: translateX(0);
            }
            
            .nisa-toast-content {
                display: flex;
                align-items: center;
                background: rgba(0, 0, 0, 0.9);
                backdrop-filter: blur(10px);
                border-radius: 8px;
                padding: 12px 16px;
                min-width: 300px;
                box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
                border: 1px solid rgba(255, 255, 255, 0.1);
            }
            
            .nisa-toast-success .nisa-toast-content {
                border-color: #00ff88;
            }
            
            .nisa-toast-error .nisa-toast-content {
                border-color: #ff6b6b;
            }
            
            .nisa-toast-warning .nisa-toast-content {
                border-color: #ffa726;
            }
            
            .nisa-toast-info .nisa-toast-content {
                border-color: #00ffff;
            }
            
            .nisa-toast-icon {
                margin-right: 12px;
                font-size: 16px;
            }
            
            .nisa-toast-success .nisa-toast-icon {
                color: #00ff88;
            }
            
            .nisa-toast-error .nisa-toast-icon {
                color: #ff6b6b;
            }
            
            .nisa-toast-warning .nisa-toast-icon {
                color: #ffa726;
            }
            
            .nisa-toast-info .nisa-toast-icon {
                color: #00ffff;
            }
            
            .nisa-toast-message {
                flex: 1;
                color: #ffffff;
                font-size: 14px;
            }
            
            .nisa-toast-close {
                background: none;
                border: none;
                color: rgba(255, 255, 255, 0.6);
                cursor: pointer;
                margin-left: 12px;
                padding: 0;
                font-size: 12px;
                transition: color 0.2s ease;
            }
            
            .nisa-toast-close:hover {
                color: #ffffff;
            }
        `;
        document.head.appendChild(style);
    }
});