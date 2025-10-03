// 粒子效果
class ParticleSystem {
    constructor(canvas) {
        this.canvas = canvas;
        this.ctx = canvas.getContext('2d');
        this.particles = [];
        this.maxParticles = 100;
        
        this.resize();
        this.createParticles();
        this.animate();
        
        window.addEventListener('resize', () => this.resize());
    }
    
    resize() {
        this.canvas.width = window.innerWidth;
        this.canvas.height = window.innerHeight;
    }
    
    createParticles() {
        for (let i = 0; i < this.maxParticles; i++) {
            this.particles.push({
                x: Math.random() * this.canvas.width,
                y: Math.random() * this.canvas.height,
                size: Math.random() * 2 + 1,
                speedX: (Math.random() - 0.5) * 0.5,
                speedY: (Math.random() - 0.5) * 0.5,
                opacity: Math.random() * 0.5 + 0.2,
                hue: Math.random() * 60 + 180 // 青色到蓝色范围
            });
        }
    }
    
    animate() {
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
        
        // 更新和绘制粒子
        this.particles.forEach((particle, index) => {
            // 更新位置
            particle.x += particle.speedX;
            particle.y += particle.speedY;
            
            // 边界检查
            if (particle.x < 0 || particle.x > this.canvas.width) particle.speedX *= -1;
            if (particle.y < 0 || particle.y > this.canvas.height) particle.speedY *= -1;
            
            // 绘制粒子
            this.ctx.beginPath();
            this.ctx.arc(particle.x, particle.y, particle.size, 0, Math.PI * 2);
            this.ctx.fillStyle = `hsla(${particle.hue}, 100%, 50%, ${particle.opacity})`;
            this.ctx.fill();
            
            // 绘制连线
            this.particles.forEach((otherParticle, otherIndex) => {
                if (index !== otherIndex) {
                    const dx = particle.x - otherParticle.x;
                    const dy = particle.y - otherParticle.y;
                    const distance = Math.sqrt(dx * dx + dy * dy);
                    
                    if (distance < 100) {
                        this.ctx.beginPath();
                        this.ctx.moveTo(particle.x, particle.y);
                        this.ctx.lineTo(otherParticle.x, otherParticle.y);
                        this.ctx.strokeStyle = `hsla(${particle.hue}, 100%, 50%, ${0.1 * (1 - distance / 100)})`;
                        this.ctx.lineWidth = 1;
                        this.ctx.stroke();
                    }
                }
            });
        });
        
        requestAnimationFrame(() => this.animate());
    }
}

// 登录表单处理
class LoginHandler {
    constructor() {
        this.form = document.getElementById('loginForm');
        this.stuIdInput = document.getElementById('stuId');
        this.passwordInput = document.getElementById('password');
        this.loginBtn = document.getElementById('loginBtn');
        this.errorMessage = document.getElementById('errorMessage');
        this.errorText = document.getElementById('errorText');
        
        this.initEventListeners();
        this.initInputAnimations();
    }
    
    initEventListeners() {
        this.form.addEventListener('submit', (e) => this.handleLogin(e));
        
        // 输入框焦点效果
        [this.stuIdInput, this.passwordInput].forEach(input => {
            input.addEventListener('focus', () => this.handleInputFocus(input));
            input.addEventListener('blur', () => this.handleInputBlur(input));
            input.addEventListener('input', () => this.handleInputChange(input));
        });
    }
    
    initInputAnimations() {
        // 添加输入动画
        [this.stuIdInput, this.passwordInput].forEach(input => {
            input.addEventListener('keydown', (e) => {
                // 添加键盘按下效果
                input.style.transform = 'scale(0.98)';
                setTimeout(() => {
                    input.style.transform = 'scale(1)';
                }, 100);
            });
        });
    }
    
    handleInputFocus(input) {
        input.parentElement.classList.add('focused');
        // 添加聚焦动画
        input.style.transition = 'all 0.3s ease';
    }
    
    handleInputBlur(input) {
        if (!input.value) {
            input.parentElement.classList.remove('focused');
        }
    }
    
    handleInputChange(input) {
        // 实时验证
        if (input.value) {
            input.parentElement.classList.add('has-value');
        } else {
            input.parentElement.classList.remove('has-value');
        }
        
        // 清除错误状态
        if (this.errorMessage.style.display !== 'none') {
            this.hideError();
        }
    }
    
    async handleLogin(e) {
        e.preventDefault();
        
        const stuId = this.stuIdInput.value.trim();
        const password = this.passwordInput.value;
        
        // 表单验证
        if (!this.validateForm(stuId, password)) {
            return;
        }
        
        // 显示加载状态
        this.showLoading(true);
        
        try {
            // 发送登录请求
            const response = await fetch('/api/login', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    stuId: stuId,
                    password: password
                })
            });
            
            const result = await response.json();
            
            if (response.ok) {
                // 登录成功
                this.showSuccess();
                
                // 检查是否需要修改密码
                if (result.requirePasswordChange) {
                    setTimeout(() => {
                        window.location.href = '/setpassword?required=true';
                    }, 1500);
                    return;
                }
                
                // 获取重定向URL，所有用户默认跳转到个人信息页面
                const urlParams = new URLSearchParams(window.location.search);
                const redirectUrl = urlParams.get('redirect') || '/info';
                
                setTimeout(() => {
                    window.location.href = decodeURIComponent(redirectUrl);
                }, 1500);
            } else {
                // 登录失败
                this.showError(result.detail || result.message || '登录失败，请检查学号和密码');
            }
        } catch (error) {
            console.error('登录错误:', error);
            this.showError('网络连接错误，请稍后重试');
        } finally {
            this.showLoading(false);
        }
    }
    
    validateForm(stuId, password) {
        console.log('验证表单:', { stuId, password: password ? '***' : '' });
        
        if (!stuId) {
            console.log('学号为空');
            this.showError('请输入学号');
            this.stuIdInput.focus();
            return false;
        }
        
        if (!password) {
            console.log('密码为空');
            this.showError('请输入密码');
            this.passwordInput.focus();
            return false;
        }
        
        console.log('验证通过');
        return true;
    }
    
    showLoading(show) {
        const btnText = this.loginBtn.querySelector('.btn-text');
        const btnLoader = this.loginBtn.querySelector('.btn-loader');
        
        if (show) {
            btnText.style.display = 'none';
            btnLoader.style.display = 'inline-block';
            this.loginBtn.disabled = true;
            this.loginBtn.style.opacity = '0.7';
        } else {
            btnText.style.display = 'inline';
            btnLoader.style.display = 'none';
            this.loginBtn.disabled = false;
            this.loginBtn.style.opacity = '1';
        }
    }
    
    showError(message) {
        this.errorText.textContent = message;
        this.errorMessage.style.display = 'block';
        this.errorMessage.style.animation = 'shake 0.5s ease-in-out';
        
        // 添加错误状态样式
        [this.stuIdInput, this.passwordInput].forEach(input => {
            input.style.borderColor = 'rgba(255, 107, 107, 0.5)';
            input.style.boxShadow = '0 0 10px rgba(255, 107, 107, 0.3)';
        });
        
        // 3秒后自动隐藏错误消息
        setTimeout(() => {
            this.hideError();
        }, 3000);
    }
    
    hideError() {
        this.errorMessage.style.display = 'none';
        
        // 移除错误状态样式
        [this.stuIdInput, this.passwordInput].forEach(input => {
            input.style.borderColor = '';
            input.style.boxShadow = '';
        });
    }
    
    showSuccess() {
        // 显示成功动画
        this.loginBtn.innerHTML = `
            <i class="fas fa-check"></i>
            <span>登录成功</span>
        `;
        this.loginBtn.style.background = 'linear-gradient(45deg, #00ff88, #00ffff)';
        
        // 添加成功动画效果
        document.querySelector('.login-card').style.animation = 'pulse 0.5s ease-in-out';
    }
}

// 实用工具函数
function togglePassword() {
    const passwordInput = document.getElementById('password');
    const toggleIcon = document.getElementById('passwordToggleIcon');
    
    if (passwordInput.type === 'password') {
        passwordInput.type = 'text';
        toggleIcon.className = 'fas fa-eye-slash';
    } else {
        passwordInput.type = 'password';
        toggleIcon.className = 'fas fa-eye';
    }
}

function updateTime() {
    const now = new Date();
    const timeString = now.toLocaleString('zh-CN', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
    });
    
    const timeElement = document.getElementById('currentTime');
    if (timeElement) {
        timeElement.textContent = timeString;
    }
}

function updateOnlineUsers() {
    // 获取实际的用户总数
    const onlineUsersElement = document.getElementById('onlineUsers');
    if (onlineUsersElement) {
        // 先显示加载状态
        onlineUsersElement.textContent = '...';
        
        // 调用API获取用户统计信息
        fetch('/api/user-stats')
            .then(response => response.json())
            .then(data => {
                onlineUsersElement.textContent = data.totalUsers || 0;
            })
            .catch(error => {
                console.error('获取用户统计失败:', error);
                // 出错时显示一个默认值
                onlineUsersElement.textContent = '未知';
            });
    }
}

// 键盘事件处理
function handleKeyboardShortcuts(e) {
    // Ctrl + Enter 快速登录
    if (e.ctrlKey && e.key === 'Enter') {
        document.getElementById('loginForm').dispatchEvent(new Event('submit'));
    }
    
    // ESC 清除表单
    if (e.key === 'Escape') {
        document.getElementById('stuId').value = '';
        document.getElementById('password').value = '';
        document.getElementById('stuId').focus();
    }
}

// 添加脉冲动画样式
function addPulseAnimation() {
    const style = document.createElement('style');
    style.textContent = `
        @keyframes pulse {
            0% { transform: scale(1); }
            50% { transform: scale(1.05); }
            100% { transform: scale(1); }
        }
    `;
    document.head.appendChild(style);
}

// 检查是否已经登录
async function checkExistingSession() {
    try {
        // 尝试获取当前用户信息
        const response = await fetch('/api/current-user', {
            method: 'GET',
            credentials: 'include' // 包含cookies
        });
        
        if (response.ok) {
            const data = await response.json();
            console.log('✅ 检测到已登录的会话:', data.user);
            
            // 检查是否有redirect参数
            const urlParams = new URLSearchParams(window.location.search);
            const redirectUrl = urlParams.get('redirect') || '/info'; // 所有用户默认跳转到个人信息页面
            
            // 显示提示信息
            console.log(`🔄 已登录，正在跳转到: ${redirectUrl}`);
            
            // 跳转
            window.location.href = decodeURIComponent(redirectUrl);
            return true;
        }
    } catch (error) {
        console.log('ℹ️ 未检测到有效会话，显示登录界面');
    }
    return false;
}

// DOM加载完成后初始化
document.addEventListener('DOMContentLoaded', async () => {
    // 先检查是否已经登录
    const isLoggedIn = await checkExistingSession();
    
    // 如果已经登录，就不需要初始化登录界面了
    if (isLoggedIn) {
        return;
    }
    
    // 初始化粒子系统
    const canvas = document.getElementById('particleCanvas');
    if (canvas) {
        new ParticleSystem(canvas);
    }
    
    // 初始化登录处理器
    new LoginHandler();
    
    // 添加动画样式
    addPulseAnimation();
    
    // 更新时间显示
    updateTime();
    setInterval(updateTime, 1000);
    
    // 更新在线用户数
    updateOnlineUsers();
    setInterval(updateOnlineUsers, 30000);
    
    // 键盘快捷键
    document.addEventListener('keydown', handleKeyboardShortcuts);
    
    // 焦点管理
    document.getElementById('stuId').focus();
    
    // 添加页面加载动画
    setTimeout(() => {
        document.body.style.opacity = '1';
    }, 100);
});

// 页面可见性变化处理
document.addEventListener('visibilitychange', () => {
    if (document.hidden) {
        // 页面隐藏时暂停动画
        console.log('页面隐藏，暂停动画');
    } else {
        // 页面显示时恢复动画
        console.log('页面显示，恢复动画');
        updateTime();
        updateOnlineUsers();
    }
});