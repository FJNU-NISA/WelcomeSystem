/**
 * NISA Welcome System - 统一导航栏组件
 * 提供页面导航、用户信息显示、权限控制等功能
 */

class NavigationBar {
    constructor() {
        this.currentUser = null;
        this.currentPage = this.getCurrentPage();
        this.init();
    }

    /**
     * 初始化导航栏
     */
    async init() {
        await this.loadUserInfo();
        this.render();
        this.bindEvents();
    }

    /**
     * 获取当前页面标识
     */
    getCurrentPage() {
        const path = window.location.pathname;
        if (path === '/info') return 'info';
        if (path === '/lottery') return 'lottery';
        if (path === '/levelintroduction') return 'levelintroduction';
        if (path === '/modifypoints') return 'modifypoints';
        if (path.startsWith('/admin/membermanagement')) return 'membermanagement';
        if (path.startsWith('/admin/levelmanagement')) return 'levelmanagement';
        if (path.startsWith('/admin/prizemanagement')) return 'prizemanagement';
        return 'unknown';
    }

    /**
     * 加载用户信息
     */
    async loadUserInfo() {
        try {
            const response = await fetch('/api/debug/session', {
                credentials: 'include'
            });
            
            if (response.ok) {
                const data = await response.json();
                if (data.session_valid && data.user_info) {
                    this.currentUser = data.user_info;
                }
            }
        } catch (error) {
            console.warn('无法获取用户信息:', error);
        }
    }

    /**
     * 获取导航配置
     */
    getNavigationConfig() {
        const userRole = this.currentUser?.role || 'user';
        const userPermissions = this.currentUser?.permissions || {};
        const allowedPages = userPermissions.pages || [];
        
        // 定义所有可能的导航项
        const allNavigationItems = [
            {
                id: 'info',
                label: '个人信息',
                icon: 'fas fa-user',
                href: '/info',
                requiredPage: 'info'
            },
            {
                id: 'lottery',
                label: '抽奖',
                icon: 'fas fa-gift',
                href: '/lottery',
                requiredPage: 'lottery'
            },
            {
                id: 'levelintroduction',
                label: '关卡查看',
                icon: 'fas fa-trophy',
                href: '/levelintroduction',
                requiredPage: 'levelintroduction'
            },
            {
                id: 'modifypoints',
                label: '分发积分',
                icon: 'fas fa-coins',
                href: '/modifypoints',
                requiredPage: 'modifypoints'
            },
            {
                id: 'membermanagement',
                label: '成员管理',
                icon: 'fas fa-users-cog',
                href: '/admin/membermanagement',
                requiredPage: 'membermanagement'
            },
            {
                id: 'levelmanagement',
                label: '关卡管理',
                icon: 'fas fa-tasks',
                href: '/admin/levelmanagement',
                requiredPage: 'levelmanagement'
            },
            {
                id: 'prizemanagement',
                label: '奖品管理',
                icon: 'fas fa-trophy',
                href: '/admin/prizemanagement',
                requiredPage: 'prizemanagement'
            }
        ];

        // 根据后端返回的权限页面列表过滤可见的导航项
        return allNavigationItems.map(item => {
            // 检查该页面是否在用户的权限列表中
            const visible = allowedPages.includes(item.requiredPage);
            
            return {
                ...item,
                visible: visible
            };
        });
    }

    /**
     * 渲染导航栏
     */
    render() {
        const navConfig = this.getNavigationConfig();
        const visibleNavs = navConfig.filter(nav => nav.visible);
        
        // 生成导航项HTML
        const navItemsHTML = visibleNavs.map(nav => `
            <li class="nav-item">
                <a href="${nav.href}" class="nav-link ${nav.id === this.currentPage ? 'active' : ''}" data-page="${nav.id}">
                    <i class="${nav.icon}"></i>
                    <span>${nav.label}</span>
                </a>
            </li>
        `).join('');

        // 生成用户信息HTML
        const userInfoHTML = this.currentUser ? `
            <div class="user-info">
                <div class="user-avatar">
                    ${this.currentUser.stuId ? this.currentUser.stuId.charAt(0).toUpperCase() : 'U'}
                </div>
                <span>欢迎，${this.currentUser.stuId || '用户'}</span>
            </div>
        ` : '';

        // 生成移动端菜单项HTML
        const mobileNavItemsHTML = visibleNavs.map(nav => `
            <a href="${nav.href}" class="mobile-nav-item ${nav.id === this.currentPage ? 'active' : ''}" data-page="${nav.id}">
                <i class="${nav.icon}"></i>
                <span>${nav.label}</span>
            </a>
        `).join('');

        // 生成完整导航栏HTML
        const navbarHTML = `
            <nav class="main-navbar">
                <a href="/info" class="navbar-brand">
                    <i class="fas fa-users"></i>
                    <span>NISA Welcome System</span>
                </a>
                
                <button class="mobile-menu-toggle" onclick="navigationBar.toggleMobileMenu()">
                    <i class="fas fa-bars"></i>
                </button>
                
                <ul class="navbar-nav">
                    ${navItemsHTML}
                </ul>
                
                <div class="navbar-user">
                    ${userInfoHTML}
                    <button class="logout-btn" onclick="navigationBar.logout()">
                        <i class="fas fa-sign-out-alt"></i>
                        <span>退出登录</span>
                    </button>
                </div>
            </nav>
            
            <div class="mobile-nav-menu" id="mobileNavMenu">
                ${mobileNavItemsHTML}
                <div style="border-top: 1px solid var(--border-primary); margin-top: var(--spacing-md); padding-top: var(--spacing-md);">
                    <button class="mobile-nav-item" onclick="navigationBar.logout()" style="width: 100%; text-align: left; background: none; border: none; color: inherit; font: inherit; cursor: pointer;">
                        <i class="fas fa-sign-out-alt"></i>
                        <span>退出登录</span>
                    </button>
                </div>
            </div>
        `;

        // 检查是否已经存在导航栏，如果存在则替换，否则插入到body顶部
        const existingNavbar = document.querySelector('.main-navbar');
        if (existingNavbar) {
            existingNavbar.outerHTML = navbarHTML;
        } else {
            document.body.insertAdjacentHTML('afterbegin', navbarHTML);
        }

        // 确保页面内容有适当的上边距
        this.adjustPageLayout();
    }

    /**
     * 调整页面布局
     */
    adjustPageLayout() {
        // 为页面添加顶部margin，避免内容被导航栏遮挡
        const isMobile = window.innerWidth <= 768;
        const topOffset = isMobile ? '60px' : '70px';
        
        if (!document.querySelector('.page-container')) {
            // 如果没有page-container，为body添加padding-top
            document.body.style.paddingTop = topOffset;
        }

        // 监听窗口大小变化
        window.addEventListener('resize', () => {
            const newIsMobile = window.innerWidth <= 768;
            const newTopOffset = newIsMobile ? '60px' : '70px';
            
            if (!document.querySelector('.page-container')) {
                document.body.style.paddingTop = newTopOffset;
            }
            
            // 如果从移动端切换到桌面端，关闭移动菜单
            if (!newIsMobile) {
                this.closeMobileMenu();
            }
        });
    }

    /**
     * 绑定事件
     */
    bindEvents() {
        // 导航链接点击事件（用于SPA路由，如果需要的话）
        document.querySelectorAll('.nav-link').forEach(link => {
            link.addEventListener('click', (e) => {
                // 这里可以添加SPA路由逻辑，目前使用传统的页面跳转
                console.log('导航到:', e.currentTarget.dataset.page);
            });
        });

        // 移动端菜单项点击事件
        document.querySelectorAll('.mobile-nav-item').forEach(link => {
            link.addEventListener('click', () => {
                this.closeMobileMenu();
            });
        });

        // 点击页面其他区域关闭移动端菜单
        document.addEventListener('click', (e) => {
            const mobileMenu = document.getElementById('mobileNavMenu');
            const mobileToggle = document.querySelector('.mobile-menu-toggle');
            
            if (mobileMenu && mobileMenu.classList.contains('show') && 
                !mobileMenu.contains(e.target) && !mobileToggle.contains(e.target)) {
                this.closeMobileMenu();
            }
        });
    }

    /**
     * 切换移动端菜单
     */
    toggleMobileMenu() {
        const mobileMenu = document.getElementById('mobileNavMenu');
        if (mobileMenu) {
            mobileMenu.classList.toggle('show');
        }
    }

    /**
     * 关闭移动端菜单
     */
    closeMobileMenu() {
        const mobileMenu = document.getElementById('mobileNavMenu');
        if (mobileMenu) {
            mobileMenu.classList.remove('show');
        }
    }

    /**
     * 用户登出
     */
    async logout() {
        if (!confirm('确定要退出登录吗？')) {
            return;
        }

        try {
            const response = await fetch('/api/logout', {
                method: 'POST',
                credentials: 'include'
            });

            if (response.ok) {
                // 登出成功，跳转到登录页面
                window.location.href = '/login';
            } else {
                console.error('登出失败');
                alert('登出失败，请重试');
            }
        } catch (error) {
            console.error('登出错误:', error);
            alert('网络错误，请重试');
        }
    }

    /**
     * 更新活动导航项
     */
    updateActiveNav(pageId) {
        document.querySelectorAll('.nav-link').forEach(link => {
            link.classList.remove('active');
        });

        const activeLink = document.querySelector(`.nav-link[data-page="${pageId}"]`);
        if (activeLink) {
            activeLink.classList.add('active');
        }
        
        this.currentPage = pageId;
    }

    /**
     * 刷新用户信息
     */
    async refreshUserInfo() {
        await this.loadUserInfo();
        this.render();
    }
}

// 全局实例
let navigationBar;

/**
 * 初始化导航栏
 * 在页面加载完成后自动调用
 */
function initNavigationBar() {
    // 只在非登录页面初始化导航栏
    if (!window.location.pathname.includes('/login') && !window.location.pathname.includes('/setpassword')) {
        navigationBar = new NavigationBar();
    }
}

// 页面加载完成后初始化
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initNavigationBar);
} else {
    initNavigationBar();
}

// 导出供其他脚本使用
window.NavigationBar = NavigationBar;
window.navigationBar = navigationBar;