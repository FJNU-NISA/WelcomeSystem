// 关卡查看页面脚本

// 使用var避免重复声明错误,或检查是否已存在
var allLevels = [];
var levelIntroNavigationBar = null;

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', async function() {
    console.log('关卡查看页面加载完成');
    
    // 加载导航栏
    levelIntroNavigationBar = new NavigationBar();
    
    // 加载关卡列表
    await loadLevels();
});

/**
 * 加载所有关卡信息
 */
async function loadLevels() {
    const loadingIndicator = document.getElementById('loadingIndicator');
    const levelsContainer = document.getElementById('levelsContainer');
    const emptyState = document.getElementById('emptyState');
    
    try {
        loadingIndicator.style.display = 'block';
        levelsContainer.style.display = 'none';
        emptyState.style.display = 'none';
        
        // 调用API获取所有关卡（包括未激活的）
        const response = await fetch('/api/levels/public', {
            method: 'GET',
            credentials: 'include'
        });
        
        if (!response.ok) {
            throw new Error('获取关卡列表失败');
        }
        
        const data = await response.json();
        allLevels = data.levels || [];
        
        if (allLevels.length === 0) {
            emptyState.style.display = 'block';
        } else {
            renderLevels(allLevels);
            levelsContainer.style.display = 'grid';
        }
        
    } catch (error) {
        console.error('加载关卡失败:', error);
        showToast('加载关卡列表失败，请刷新重试', 'error');
        emptyState.style.display = 'block';
    } finally {
        loadingIndicator.style.display = 'none';
    }
}

/**
 * 渲染关卡列表
 */
function renderLevels(levels) {
    const levelsContainer = document.getElementById('levelsContainer');
    levelsContainer.innerHTML = '';
    
    levels.forEach(level => {
        const levelCard = createLevelCard(level);
        levelsContainer.appendChild(levelCard);
    });
}

/**
 * 创建关卡卡片
 */
function createLevelCard(level) {
    const card = document.createElement('div');
    card.className = `level-card ${!level.isActive ? 'inactive' : ''}`;
    
    const isActive = level.isActive !== false;
    const statusClass = isActive ? 'active' : 'inactive';
    const statusText = isActive ? '进行中' : '未开放';
    
    // 优先使用info字段，其次使用description字段
    const levelInfo = level.info || level.description || '暂无关卡说明';
    
    card.innerHTML = `
        <div class="level-header">
            <h3 class="level-name">${escapeHtml(level.name)}</h3>
            <div class="level-points">
                <i class="fas fa-coins"></i>
                ${level.points || 0} 积分
            </div>
        </div>
        <div class="level-description">
            ${escapeHtml(levelInfo)}
        </div>
        <div class="level-status ${statusClass}">
            ${statusText}
        </div>
        <button class="view-detail-btn" onclick="viewLevelDetail('${level._id}')">
            <i class="fas fa-info-circle"></i> 查看详情
        </button>
    `;
    
    return card;
}

/**
 * 查看关卡详情
 */
function viewLevelDetail(levelId) {
    const level = allLevels.find(l => l._id === levelId);
    if (!level) {
        showToast('关卡信息不存在', 'error');
        return;
    }
    
    const modal = document.getElementById('levelDetailModal');
    const content = document.getElementById('levelDetailContent');
    
    const isActive = level.isActive !== false;
    const statusClass = isActive ? 'active' : 'inactive';
    const statusText = isActive ? '🎯 关卡进行中' : '🔒 关卡未开放';
    
    // 优先使用info字段，其次使用description字段
    const levelInfo = level.info || level.description || '暂无详细说明';
    
    content.innerHTML = `
        <div class="detail-header">
            <h2>${escapeHtml(level.name)}</h2>
            <div class="detail-points">
                <i class="fas fa-coins"></i>
                完成可获得 ${level.points || 0} 积分
            </div>
        </div>
        <div class="detail-info">
            <h3><i class="fas fa-info-circle"></i> 关卡说明</h3>
            <p>${escapeHtml(levelInfo)}</p>
        </div>
        <div class="detail-status ${statusClass}">
            ${statusText}
        </div>
    `;
    
    modal.style.display = 'block';
}

/**
 * 关闭详情弹窗
 */
function closeLevelDetail() {
    const modal = document.getElementById('levelDetailModal');
    modal.style.display = 'none';
}

/**
 * 转义HTML特殊字符
 */
function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

/**
 * 显示提示消息
 */
function showToast(message, type = 'info') {
    // 创建toast元素
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.textContent = message;
    toast.style.cssText = `
        position: fixed;
        top: 100px;
        right: 20px;
        padding: 15px 20px;
        border-radius: 8px;
        color: white;
        font-weight: 600;
        z-index: 10000;
        animation: slideInRight 0.3s ease;
        box-shadow: 0 5px 20px rgba(0,0,0,0.2);
    `;
    
    // 根据类型设置背景色
    const colors = {
        'success': '#28a745',
        'error': '#dc3545',
        'warning': '#ffc107',
        'info': '#17a2b8'
    };
    toast.style.background = colors[type] || colors['info'];
    
    document.body.appendChild(toast);
    
    // 3秒后自动移除
    setTimeout(() => {
        toast.style.animation = 'slideOutRight 0.3s ease';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

// 点击弹窗外部关闭
window.onclick = function(event) {
    const modal = document.getElementById('levelDetailModal');
    if (event.target === modal) {
        closeLevelDetail();
    }
};
