// 关卡管理页面JavaScript逻辑
let currentPage = 1;
let pageSize = 10;
let totalLevels = 0;
let currentFilter = 'all';
let currentSearch = '';
let editingLevelId = null;
let deletingLevelId = null;
let levelsData = [];
let currentLevelForParticipants = null;

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM加载完成，开始初始化...');
    
    // 检查关键元素是否存在
    const totalElement = document.getElementById('totalLevels');
    const activeElement = document.getElementById('activeLevels');
    const inactiveElement = document.getElementById('inactiveLevels');
    
    console.log('统计元素检查:', {
        totalElement: totalElement !== null,
        activeElement: activeElement !== null,
        inactiveElement: inactiveElement !== null
    });
    
    checkAuth();
    loadLevelsStats();
    loadLevels();
});

// 检查用户权限
async function checkAuth() {
    try {
        const response = await fetch('/api/user/info');
        if (!response.ok) {
            window.location.href = '../../Login/html/login.html';
            return;
        }
        
        const userData = await response.json();
        if (userData.role !== 'super_admin') {
            alert('权限不足，只有超级管理员可以访问此页面');
            window.location.href = '../../Info/html/info.html';
            return;
        }
    } catch (error) {
        console.error('权限检查失败:', error);
        window.location.href = '../../Login/html/login.html';
    }
}

// 登出功能
async function logout() {
    try {
        await fetch('/api/user/logout', { method: 'POST' });
        window.location.href = '../../Login/html/login.html';
    } catch (error) {
        console.error('登出失败:', error);
        window.location.href = '../../Login/html/login.html';
    }
}

// 加载关卡统计信息
async function loadLevelsStats() {
    try {
        console.log('开始加载关卡统计信息...');
        const response = await fetch('/api/admin/levels/stats');
        if (!response.ok) throw new Error('获取统计信息失败');
        
        const stats = await response.json();
        console.log('获取到的统计数据:', stats);
        
        // 安全地设置统计数据，避免null错误
        const totalElement = document.getElementById('totalLevels');
        const activeElement = document.getElementById('activeLevels');
        const inactiveElement = document.getElementById('inactiveLevels');
        
        console.log('元素检查结果:', {
            totalElement: totalElement,
            activeElement: activeElement, 
            inactiveElement: inactiveElement
        });
        
        if (totalElement) {
            totalElement.textContent = stats.total || 0;
            console.log('设置总关卡数:', stats.total || 0);
        }
        if (activeElement) {
            activeElement.textContent = stats.active || 0;
            console.log('设置已激活关卡数:', stats.active || 0);
        }
        if (inactiveElement) {
            inactiveElement.textContent = stats.inactive || 0;
            console.log('设置未激活关卡数:', stats.inactive || 0);
        }
        
    } catch (error) {
        console.error('加载统计信息失败:', error);
        if (typeof showMessage === 'function') {
            showMessage('加载统计信息失败', 'error');
        }
    }
}

// 加载关卡列表
async function loadLevels() {
    try {
        showLoading();
        
        const params = new URLSearchParams({
            page: currentPage,
            limit: pageSize
        });
        
        if (currentFilter !== 'all') {
            params.append('status', currentFilter);
        }
        
        if (currentSearch) {
            params.append('search', currentSearch);
        }
        
        const response = await fetch(`/api/admin/levels?${params}`);
        if (!response.ok) throw new Error('获取关卡列表失败');
        
        const data = await response.json();
        levelsData = data.levels || [];
        totalLevels = data.total || 0;
        
        renderLevelsTable();
        renderPagination();
        
    } catch (error) {
        console.error('加载关卡列表失败:', error);
        showMessage('加载关卡列表失败', 'error');
        showEmptyState();
    }
}

// 渲染关卡表格
function renderLevelsTable() {
    const tbody = document.getElementById('levelsTableBody');
    
    if (levelsData.length === 0) {
        showEmptyState();
        return;
    }
    
    tbody.innerHTML = levelsData.map(level => `
        <tr>
            <td>
                <strong>${level.name}</strong>
            </td>
            <td>
                <div style="max-width: 300px; overflow: hidden; text-overflow: ellipsis;">
                    ${level.info || '-'}
                </div>
            </td>
            <td>
                <span class="points-badge">${level.points || 0} 积分</span>
            </td>
            <td class="activation-controls">
                <div class="activation-row">
                    <label class="switch">
                        <input type="checkbox" ${level.isActive ? 'checked' : ''} 
                               onchange="toggleLevelActive('${level._id}', this.checked)">
                        <span class="slider round"></span>
                    </label>
                    <div class="action-buttons">
                        <button class="action-btn edit" onclick="editLevel('${level._id}')" title="编辑关卡">
                            <i class="fas fa-edit"></i>
                        </button>
                        <button class="action-btn delete" onclick="deleteLevel('${level._id}', '${level.name}')" title="删除关卡">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                </div>
            </td>
        </tr>
    `).join('');
}

// 渲染分页控件
function renderPagination() {
    const totalPages = Math.ceil(totalLevels / pageSize);
    const pagination = document.getElementById('pagination');
    
    if (totalPages <= 1) {
        pagination.innerHTML = '';
        return;
    }
    
    let paginationHTML = '';
    
    // 上一页按钮
    paginationHTML += `
        <button ${currentPage === 1 ? 'disabled' : ''} onclick="changePage(${currentPage - 1})">
            <i class="fas fa-chevron-left"></i>
        </button>
    `;
    
    // 页码按钮
    for (let i = 1; i <= totalPages; i++) {
        if (i === 1 || i === totalPages || (i >= currentPage - 2 && i <= currentPage + 2)) {
            paginationHTML += `
                <button class="${i === currentPage ? 'active' : ''}" onclick="changePage(${i})">
                    ${i}
                </button>
            `;
        } else if (i === currentPage - 3 || i === currentPage + 3) {
            paginationHTML += '<span>...</span>';
        }
    }
    
    // 下一页按钮
    paginationHTML += `
        <button ${currentPage === totalPages ? 'disabled' : ''} onclick="changePage(${currentPage + 1})">
            <i class="fas fa-chevron-right"></i>
        </button>
    `;
    
    pagination.innerHTML = paginationHTML;
}

// 改变页面
function changePage(page) {
    if (page < 1 || page > Math.ceil(totalLevels / pageSize)) return;
    currentPage = page;
    loadLevels();
}

// 搜索关卡
function searchLevels() {
    currentSearch = document.getElementById('searchInput').value.trim();
    currentPage = 1;
    loadLevels();
}

// 清空搜索
function clearSearch() {
    document.getElementById('searchInput').value = '';
    currentSearch = '';
    currentPage = 1;
    loadLevels();
}

// 筛选关卡
function filterLevels() {
    currentFilter = document.getElementById('statusFilter').value;
    currentPage = 1;
    loadLevels();
}

// 显示添加关卡模态框
function showAddLevelModal() {
    editingLevelId = null;
    document.getElementById('modalTitle').textContent = '添加关卡';
    document.getElementById('levelForm').reset();
    document.getElementById('levelModal').style.display = 'block';
}

// 编辑关卡
async function editLevel(levelId) {
    try {
        const response = await fetch(`/api/admin/levels/${levelId}`);
        if (!response.ok) throw new Error('获取关卡信息失败');
        
        const level = await response.json();
        
        editingLevelId = levelId;
        document.getElementById('modalTitle').textContent = '编辑关卡';
        document.getElementById('levelName').value = level.name || '';
        document.getElementById('levelInfo').value = level.info || '';
        document.getElementById('pointsReward').value = level.points || 0;
        
        document.getElementById('levelModal').style.display = 'block';
    } catch (error) {
        console.error('编辑关卡失败:', error);
        showMessage('获取关卡信息失败', 'error');
    }
}

// 保存关卡
async function saveLevel() {
    const form = document.getElementById('levelForm');
    const formData = new FormData(form);
    
    const levelData = {
        name: formData.get('name'),
        info: formData.get('info'),
        points: parseInt(formData.get('points')) || 0
    };
    
    // 验证必填字段
    if (!levelData.name) {
        showMessage('请填写关卡名称', 'error');
        return;
    }
    
    try {
        let response;
        if (editingLevelId) {
            // 更新关卡
            response = await fetch(`/api/admin/levels/${editingLevelId}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(levelData)
            });
        } else {
            // 添加关卡
            response = await fetch('/api/admin/levels', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(levelData)
            });
        }
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || '操作失败');
        }
        
        showMessage(editingLevelId ? '关卡信息更新成功' : '关卡添加成功', 'success');
        closeLevelModal();
        loadLevels();
        loadLevelsStats();
    } catch (error) {
        console.error('保存关卡失败:', error);
        showMessage(error.message, 'error');
    }
}

// 关闭关卡模态框
function closeLevelModal() {
    document.getElementById('levelModal').style.display = 'none';
    editingLevelId = null;
}

// 查看关卡详情
async function viewLevelDetail(levelId) {
    try {
        const response = await fetch(`/api/admin/levels/${levelId}/detail`);
        if (!response.ok) throw new Error('获取关卡详情失败');
        
        const level = await response.json();
        
        const detailHTML = `
            <div class="level-detail">
                <div class="detail-section">
                    <h4><i class="fas fa-info-circle"></i> 基本信息</h4>
                    <div class="detail-grid">
                        <div class="detail-item">
                            <label>关卡名称:</label>
                            <span>${level.name}</span>
                        </div>
                        <div class="detail-item">
                            <label>奖励积分:</label>
                            <span>${level.pointsReward || 0} 积分</span>
                        </div>
                        <div class="detail-item">
                            <label>状态:</label>
                            <span class="status-badge ${getStatusClass(level.isActive)}">
                                ${getStatusText(level.isActive)}
                            </span>
                        </div>

                        <div class="detail-item">
                            <label>创建时间:</label>
                            <span>${formatDate(level.createdAt)}</span>
                        </div>
                        <div class="detail-item">
                            <label>更新时间:</label>
                            <span>${formatDate(level.updatedAt)}</span>
                        </div>
                    </div>
                </div>
                
                <div class="detail-section">
                    <h4><i class="fas fa-align-left"></i> 关卡描述</h4>
                    <p>${level.description || '-'}</p>
                </div>
                
                ${level.requirements ? `
                <div class="detail-section">
                    <h4><i class="fas fa-tasks"></i> 完成条件</h4>
                    <p>${level.requirements}</p>
                </div>
                ` : ''}
                
                ${level.startDate || level.endDate ? `
                <div class="detail-section">
                    <h4><i class="fas fa-calendar"></i> 时间安排</h4>
                    <div class="detail-grid">
                        ${level.startDate ? `
                        <div class="detail-item">
                            <label>开始时间:</label>
                            <span>${formatDate(level.startDate)}</span>
                        </div>
                        ` : ''}
                        ${level.endDate ? `
                        <div class="detail-item">
                            <label>结束时间:</label>
                            <span>${formatDate(level.endDate)}</span>
                        </div>
                        ` : ''}
                    </div>
                </div>
                ` : ''}
                
                <div class="detail-section">
                    <h4><i class="fas fa-chart-bar"></i> 参与统计</h4>
                    <div class="detail-grid">
                        <div class="detail-item">
                            <label>参与人数:</label>
                            <span>${level.participantCount || 0} 人</span>
                        </div>
                        <div class="detail-item">
                            <label>完成率:</label>
                            <span>${level.completionRate ? level.completionRate.toFixed(1) : 0}%</span>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        document.getElementById('levelDetailContent').innerHTML = detailHTML;
        document.getElementById('levelDetailModal').style.display = 'block';
        
    } catch (error) {
        console.error('查看关卡详情失败:', error);
        showMessage('获取关卡详情失败', 'error');
    }
}

// 关闭关卡详情模态框
function closeLevelDetailModal() {
    document.getElementById('levelDetailModal').style.display = 'none';
}

// participants相关功能已移除

// 删除关卡
function deleteLevel(levelId, levelName) {
    deletingLevelId = levelId;
    document.getElementById('deleteMessage').textContent = `确定要删除关卡 "${levelName}" 吗？此操作不可恢复！`;
    document.getElementById('deleteModal').style.display = 'block';
}

// 确认删除
async function confirmDelete() {
    if (!deletingLevelId) return;
    
    try {
        const response = await fetch(`/api/admin/levels/${deletingLevelId}`, {
            method: 'DELETE'
        });
        
        if (!response.ok) throw new Error('删除失败');
        
        showMessage('关卡删除成功', 'success');
        closeDeleteModal();
        loadLevels();
        loadLevelsStats();
    } catch (error) {
        console.error('删除关卡失败:', error);
        showMessage('删除关卡失败', 'error');
    }
}

// 关闭删除确认模态框
function closeDeleteModal() {
    document.getElementById('deleteModal').style.display = 'none';
    deletingLevelId = null;
}

// 辅助函数
function getStatusClass(isActive) {
    return isActive ? 'active' : 'inactive';
}

function getStatusText(isActive) {
    return isActive ? '活跃中' : '未激活';
}

function formatDate(dateString, format = 'YYYY-MM-DD HH:mm') {
    if (!dateString) return '-';
    const date = new Date(dateString);
    
    if (format === 'YYYY-MM-DD') {
        return date.toLocaleDateString('zh-CN');
    }
    
    return date.toLocaleString('zh-CN');
}

function formatDateForInput(dateString) {
    if (!dateString) return '';
    const date = new Date(dateString);
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    const hours = String(date.getHours()).padStart(2, '0');
    const minutes = String(date.getMinutes()).padStart(2, '0');
    return `${year}-${month}-${day}T${hours}:${minutes}`;
}

function showLoading() {
    const tbody = document.getElementById('levelsTableBody');
    tbody.innerHTML = `
        <tr>
            <td colspan="8" class="loading">
                <i class="fas fa-spinner"></i>
                加载中...
            </td>
        </tr>
    `;
}

function showEmptyState() {
    const tbody = document.getElementById('levelsTableBody');
    tbody.innerHTML = `
        <tr>
            <td colspan="8" class="empty-state">
                <i class="fas fa-map-marked-alt"></i>
                <p>暂无关卡数据</p>
            </td>
        </tr>
    `;
}

function showMessage(message, type = 'info') {
    // 创建消息元素
    const messageEl = document.createElement('div');
    messageEl.className = `message message-${type}`;
    messageEl.innerHTML = `
        <i class="fas fa-${getMessageIcon(type)}"></i>
        ${message}
    `;
    
    // 添加到页面
    document.body.appendChild(messageEl);
    
    // 显示动画
    setTimeout(() => messageEl.classList.add('show'), 100);
    
    // 自动隐藏
    setTimeout(() => {
        messageEl.classList.remove('show');
        setTimeout(() => document.body.removeChild(messageEl), 300);
    }, 3000);
}

function getMessageIcon(type) {
    const iconMap = {
        'success': 'check-circle',
        'error': 'exclamation-circle',
        'warning': 'exclamation-triangle',
        'info': 'info-circle'
    };
    return iconMap[type] || 'info-circle';
}

// 键盘事件处理
document.addEventListener('keydown', function(e) {
    // ESC键关闭模态框
    if (e.key === 'Escape') {
        closeLevelModal();
        closeLevelDetailModal();
        closeParticipantsModal();
        closeDeleteModal();
    }
    
    // 回车键搜索
    if (e.key === 'Enter' && e.target.id === 'searchInput') {
        searchLevels();
    }
});

// 点击模态框外部关闭
window.addEventListener('click', function(e) {
    if (e.target.classList.contains('modal')) {
        if (e.target.id === 'levelModal') closeLevelModal();
        if (e.target.id === 'levelDetailModal') closeLevelDetailModal();
        if (e.target.id === 'participantsModal') closeParticipantsModal();
        if (e.target.id === 'deleteModal') closeDeleteModal();
    }
});

// 切换关卡激活状态
async function toggleLevelActive(levelId, isActive) {
    try {
        const response = await fetch(`/api/admin/levels/${levelId}/toggle-active`, {
            method: 'PATCH',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        if (!response.ok) throw new Error('切换状态失败');
        
        const data = await response.json();
        showMessage(data.message, 'success');
        
        // 重新加载数据
        await loadLevels();
        await loadLevelsStats();
        
    } catch (error) {
        console.error('切换关卡状态失败:', error);
        showMessage('切换状态失败', 'error');
        
        // 恢复开关状态
        setTimeout(() => {
            loadLevels();
        }, 100);
    }
}