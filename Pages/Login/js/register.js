// 粒子效果（复用login.js的代码）
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
                hue: Math.random() * 60 + 180
            });
        }
    }
    
    animate() {
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
        
        this.particles.forEach((particle, index) => {
            particle.x += particle.speedX;
            particle.y += particle.speedY;
            
            if (particle.x < 0 || particle.x > this.canvas.width) particle.speedX *= -1;
            if (particle.y < 0 || particle.y > this.canvas.height) particle.speedY *= -1;
            
            this.ctx.beginPath();
            this.ctx.arc(particle.x, particle.y, particle.size, 0, Math.PI * 2);
            this.ctx.fillStyle = `hsla(${particle.hue}, 100%, 50%, ${particle.opacity})`;
            this.ctx.fill();
            
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

// 注册表单处理
class RegisterHandler {
    constructor() {
        this.form = document.getElementById('registerForm');
        this.stuIdInput = document.getElementById('stuId');
        this.passwordInput = document.getElementById('password');
        this.confirmPasswordInput = document.getElementById('confirmPassword');
        this.registerBtn = document.getElementById('registerBtn');
        this.errorMessage = document.getElementById('errorMessage');
        this.errorText = document.getElementById('errorText');
        this.successMessage = document.getElementById('successMessage');
        this.successText = document.getElementById('successText');
        
        this.initEventListeners();
        this.initInputAnimations();
    }
    
    initEventListeners() {
        this.form.addEventListener('submit', (e) => this.handleRegister(e));
        
        // 输入框焦点效果
        const inputs = [
            this.stuIdInput, 
            this.passwordInput, 
            this.confirmPasswordInput
        ];
        
        inputs.forEach(input => {
            input.addEventListener('focus', () => this.handleInputFocus(input));
            input.addEventListener('blur', () => this.handleInputBlur(input));
            input.addEventListener('input', () => this.handleInputChange(input));
        });
        
        // 实时密码确认验证
        this.confirmPasswordInput.addEventListener('input', () => {
            this.validatePasswordMatch();
        });
    }
    
    initInputAnimations() {
        const inputs = [
            this.stuIdInput, 
            this.passwordInput, 
            this.confirmPasswordInput
        ];
        
        inputs.forEach(input => {
            input.addEventListener('keydown', () => {
                input.style.transform = 'scale(0.98)';
                setTimeout(() => {
                    input.style.transform = 'scale(1)';
                }, 100);
            });
        });
    }
    
    handleInputFocus(input) {
        input.parentElement.classList.add('focused');
        input.style.transition = 'all 0.3s ease';
    }
    
    handleInputBlur(input) {
        if (!input.value) {
            input.parentElement.classList.remove('focused');
        }
    }
    
    handleInputChange(input) {
        if (input.value) {
            input.parentElement.classList.add('has-value');
        } else {
            input.parentElement.classList.remove('has-value');
        }
        
        if (this.errorMessage.style.display !== 'none') {
            this.hideError();
        }
    }
    
    validatePasswordMatch() {
        const password = this.passwordInput.value;
        const confirmPassword = this.confirmPasswordInput.value;
        
        if (confirmPassword && password !== confirmPassword) {
            this.confirmPasswordInput.style.borderColor = 'rgba(255, 107, 107, 0.5)';
        } else {
            this.confirmPasswordInput.style.borderColor = '';
        }
    }
    
    async handleRegister(e) {
        e.preventDefault();
        
        const stuId = this.stuIdInput.value.trim();
        const password = this.passwordInput.value;
        const confirmPassword = this.confirmPasswordInput.value;
        
        // 表单验证
        if (!this.validateForm(stuId, password, confirmPassword)) {
            return;
        }
        
        // 显示加载状态
        this.showLoading(true);
        
        try {
            // 构建请求数据
            const requestData = {
                stuId: stuId,
                password: password
            };
            
            // 发送注册请求
            const response = await fetch('/api/register', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(requestData)
            });
            
            const result = await response.json();
            
            if (response.ok) {
                // 注册成功
                this.showLoading(false);
                this.showSuccess('注册成功！即将跳转到登录页面...');
                
                // 2秒后跳转到登录页面
                setTimeout(() => {
                    window.location.href = '/login';
                }, 2000);
            } else {
                // 注册失败
                this.showLoading(false);
                this.showError(result.detail || result.message || '注册失败，请重试');
            }
        } catch (error) {
            console.error('注册错误:', error);
            this.showLoading(false);
            this.showError('网络连接错误，请稍后重试');
        }
    }
    
    validateForm(stuId, password, confirmPassword) {
        // 验证学号
        if (!stuId) {
            this.showError('请输入学号');
            this.stuIdInput.focus();
            return false;
        }
        
        // 验证学号格式（假设学号为数字）
        if (!/^\d+$/.test(stuId)) {
            this.showError('学号格式不正确，请输入数字');
            this.stuIdInput.focus();
            return false;
        }
        
        // 验证密码
        if (!password) {
            this.showError('请输入密码');
            this.passwordInput.focus();
            return false;
        }
        
        if (password.length < 6) {
            this.showError('密码长度至少为6位');
            this.passwordInput.focus();
            return false;
        }
        
        // 验证密码不能和学号相同
        if (password === stuId) {
            this.showError('密码不能与学号相同');
            this.passwordInput.focus();
            return false;
        }
        
        // 验证确认密码
        if (!confirmPassword) {
            this.showError('请确认密码');
            this.confirmPasswordInput.focus();
            return false;
        }
        
        if (password !== confirmPassword) {
            this.showError('两次输入的密码不一致');
            this.confirmPasswordInput.focus();
            return false;
        }
        
        return true;
    }
    
    showLoading(show) {
        const btnText = this.registerBtn.querySelector('.btn-text');
        const btnLoader = this.registerBtn.querySelector('.btn-loader');
        
        if (show) {
            btnText.style.display = 'none';
            btnLoader.style.display = 'inline-block';
            this.registerBtn.disabled = true;
            this.registerBtn.style.opacity = '0.7';
        } else {
            btnText.style.display = 'inline';
            btnLoader.style.display = 'none';
            this.registerBtn.disabled = false;
            this.registerBtn.style.opacity = '1';
        }
    }
    
    showError(message) {
        this.hideSuccess();
        this.errorText.textContent = message;
        this.errorMessage.style.display = 'block';
        this.errorMessage.style.animation = 'shake 0.5s ease-in-out';
        
        // 添加错误状态样式
        const inputs = [
            this.stuIdInput, 
            this.passwordInput, 
            this.confirmPasswordInput
        ];
        
        inputs.forEach(input => {
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
        const inputs = [
            this.stuIdInput, 
            this.passwordInput, 
            this.confirmPasswordInput
        ];
        
        inputs.forEach(input => {
            input.style.borderColor = '';
            input.style.boxShadow = '';
        });
    }
    
    showSuccess(message) {
        this.hideError();
        this.successText.textContent = message;
        this.successMessage.style.display = 'block';
        
        // 显示成功动画
        this.registerBtn.innerHTML = `
            <i class="fas fa-check"></i>
            <span>注册成功</span>
        `;
        this.registerBtn.style.background = 'linear-gradient(45deg, #00ff88, #00ffff)';
    }
    
    hideSuccess() {
        this.successMessage.style.display = 'none';
    }
}

// 实用工具函数
function togglePassword(inputId, iconId) {
    const passwordInput = document.getElementById(inputId);
    const toggleIcon = document.getElementById(iconId);
    
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
    const onlineUsersElement = document.getElementById('onlineUsers');
    if (onlineUsersElement) {
        onlineUsersElement.textContent = '...';
        
        fetch('/api/user-stats')
            .then(response => response.json())
            .then(data => {
                onlineUsersElement.textContent = data.totalUsers || 0;
            })
            .catch(error => {
                console.error('获取用户统计失败:', error);
                onlineUsersElement.textContent = '未知';
            });
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

// DOM加载完成后初始化
document.addEventListener('DOMContentLoaded', () => {
    // 初始化粒子系统
    const canvas = document.getElementById('particleCanvas');
    if (canvas) {
        new ParticleSystem(canvas);
    }
    
    // 初始化注册处理器
    new RegisterHandler();
    
    // 添加动画样式
    addPulseAnimation();
    
    // 更新时间显示
    updateTime();
    setInterval(updateTime, 1000);
    
    // 更新在线用户数
    updateOnlineUsers();
    setInterval(updateOnlineUsers, 30000);
    
    // 焦点管理
    document.getElementById('stuId').focus();
    
    // 添加页面加载动画
    setTimeout(() => {
        document.body.style.opacity = '1';
    }, 100);
});
