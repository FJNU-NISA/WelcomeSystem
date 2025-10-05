// 奖品管理页面JavaScript逻辑
let currentPage = 1;
let pageSize = 10;
let totalPrizes = 0;
let currentFilter = 'all';
let currentSearch = '';
let editingPrizeId = null;
let deletingPrizeId = null;
let prizesData = [];
let selectedPrizes = [];

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', function() {
    checkAuth();
    loadPrizesStats();
    loadPrizes();
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

// 加载奖品统计信息
async function loadPrizesStats() {
    try {
        const response = await fetch('/api/admin/prizes/stats');
        if (!response.ok) throw new Error('获取统计信息失败');
        
        const stats = await response.json();
        
        // 安全地设置统计数据，避免null错误
        const totalElement = document.getElementById('totalPrizes');
        const availableElement = document.getElementById('availablePrizes');
        const drawnElement = document.getElementById('totalDrawn');
        const redeemedElement = document.getElementById('totalRedeemed');
        
        const activeElement = document.getElementById('activePrizes');
        const unredeemedElement = document.getElementById('unredeemedPrizes');
        
        if (totalElement) {
            totalElement.textContent = stats.total || 0;
        }
        if (activeElement) {
            activeElement.textContent = stats.active || 0;
        }
        if (unredeemedElement) {
            unredeemedElement.textContent = stats.unredeemed || 0;
        }
        if (drawnElement) {
            drawnElement.textContent = stats.totalDrawn || 0;
        }
        
    } catch (error) {
        console.error('加载统计信息失败:', error);
        if (typeof showMessage === 'function') {
            showMessage('加载统计信息失败', 'error');
        }
    }
}

// 加载奖品列表
async function loadPrizes() {
    try {
        showLoading();
        
        const params = new URLSearchParams({
            page: currentPage,
            limit: pageSize
        });
        
        
        if (currentSearch) {
            params.append('search', currentSearch);
        }
        
        const response = await fetch(`/api/admin/prizes?${params}`);
        if (!response.ok) throw new Error('获取奖品列表失败');
        
        const data = await response.json();
        prizesData = data.prizes || [];
        totalPrizes = data.total || 0;
        
        hideLoading();
        renderPrizesTable();
        renderPagination();
        
    } catch (error) {
        console.error('加载奖品列表失败:', error);
        hideLoading();
        showMessage('加载奖品列表失败', 'error');
        showEmptyState();
    }
}

// 渲染奖品表格
function renderPrizesTable() {
    const tbody = document.getElementById('prizesTableBody');
    
    // 根据当前筛选条件在客户端过滤数据
    let filtered = prizesData.slice();
    if (currentFilter === 'available') {
        // 可用：激活且 (默认奖品 OR 数量>0)
        filtered = filtered.filter(p => {
            const totalNum = Number(p.total || 0);
            return (p.isActive !== false) && (p.isDefault === true || totalNum > 0);
        });
    } else if (currentFilter === 'out_of_stock') {
        // 缺货：数量严格等于0
        filtered = filtered.filter(p => {
            const totalNum = Number(p.total || 0);
            return totalNum === 0;
        });
    }

    if (filtered.length === 0) {
        showEmptyState();
        return;
    }

    tbody.innerHTML = filtered.map(prize => {
        const isDefault = prize.isDefault || false;
        const isActive = prize.isActive !== undefined ? prize.isActive : true;
        const deleteDisabled = isDefault ? 'disabled' : '';
        const deleteTitle = isDefault ? '默认奖品不能删除' : '删除奖品';
        
        return `
        <tr>
            <td>
                ${prize.photo ? 
                    `<img src="/Assest/Prize/${prize.photo}" alt="${prize.Name}" class="prize-image">` :
                    `<div class="no-image"><i class="fas fa-image"></i></div>`
                }
            </td>
            <td>
                <strong>${prize.Name || ''}</strong>
                ${isDefault ? '<span class="default-badge">默认</span>' : ''}
            </td>
            <td>
                <span class="${Number(prize.total || 0) === 0 ? 'total-badge zero-stock' : 'total-badge'}">${Number(prize.total || 0) > 999000 ? '∞' : (prize.total || 0)}</span>
            </td>
            <td>
                <span class="weight-badge">${(prize.weight || 0).toFixed(1)}%</span>
            </td>
            <td class="activation-controls">
                <div class="activation-row">
                    <label class="switch">
                        <input type="checkbox" ${isActive ? 'checked' : ''} 
                               onchange="togglePrizeActive('${prize._id}', this.checked)">
                        <span class="slider round"></span>
                    </label>
                    <div class="action-buttons">
                        <button class="action-btn edit" onclick="editPrize('${prize._id}')" title="编辑奖品">
                            <i class="fas fa-edit"></i>
                        </button>
                        <button class="action-btn delete" ${deleteDisabled} onclick="deletePrize('${prize._id}', '${prize.Name}')" title="${deleteTitle}">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                </div>
            </td>
        </tr>
        `;
    }).join('');
}

// 渲染分页控件
function renderPagination() {
    const totalPages = Math.ceil(totalPrizes / pageSize);
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
    if (page < 1 || page > Math.ceil(totalPrizes / pageSize)) return;
    currentPage = page;
    loadPrizes();
}

// 搜索奖品
function searchPrizes() {
    currentSearch = document.getElementById('searchInput').value.trim();
    currentPage = 1;
    loadPrizes();
}

// 清空搜索
function clearSearch() {
    document.getElementById('searchInput').value = '';
    currentSearch = '';
    currentPage = 1;
    loadPrizes();
}

// 全选/取消全选
function toggleSelectAll() {
    const selectAll = document.getElementById('selectAll');
    const checkboxes = document.querySelectorAll('.prize-checkbox');
    
    checkboxes.forEach(checkbox => {
        checkbox.checked = selectAll.checked;
    });
    
    updateSelectedPrizes();
}

// 更新选中的奖品
function updateSelectedPrizes() {
    const checkboxes = document.querySelectorAll('.prize-checkbox:checked');
    selectedPrizes = Array.from(checkboxes).map(cb => cb.value);
    
    // 更新全选状态
    const selectAll = document.getElementById('selectAll');
    const allCheckboxes = document.querySelectorAll('.prize-checkbox');
    selectAll.checked = selectedPrizes.length === allCheckboxes.length;
    selectAll.indeterminate = selectedPrizes.length > 0 && selectedPrizes.length < allCheckboxes.length;
}

// 显示添加奖品模态框
function showAddPrizeModal() {
    editingPrizeId = null;
    document.getElementById('modalTitle').textContent = '添加奖品';
    document.getElementById('prizeForm').reset();
    document.getElementById('prizeModal').style.display = 'block';
}

// 编辑奖品
async function editPrize(prizeId) {
    try {
        const response = await fetch(`/api/admin/prizes/${prizeId}`);
        if (!response.ok) {
            // 尝试读取服务器返回的详细信息
            let errText = '';
            try {
                const errJson = await response.json();
                errText = errJson.detail || JSON.stringify(errJson);
            } catch (e) {
                errText = await response.text();
            }
            console.error('服务器返回错误：', response.status, errText);
            throw new Error('获取奖品信息失败: ' + (errText || response.statusText));
        }

        const prize = await response.json();
        
        editingPrizeId = prizeId;
        document.getElementById('modalTitle').textContent = '编辑奖品';
        document.getElementById('prizeName').value = prize.Name || '';
        document.getElementById('total').value = prize.total || 0;
        document.getElementById('weight').value = prize.weight || 0;
        document.getElementById('photo').value = prize.photo || '';
        
        document.getElementById('prizeModal').style.display = 'block';
    } catch (error) {
        console.error('编辑奖品失败:', error);
        showMessage(error.message || '获取奖品信息失败', 'error');
    }
}

// 保存奖品
async function savePrize() {
    const form = document.getElementById('prizeForm');
    const formData = new FormData(form);
    
    const prizeData = {
        Name: formData.get('Name'),
        total: parseInt(formData.get('total')) || 0,
        weight: parseFloat(formData.get('weight')) || 0,
        photo: formData.get('photo')
    };
    
    // 验证必填字段
    if (!prizeData.Name) {
        showMessage('请填写奖品名称', 'error');
        return;
    }
    
    // 验证中奖概率范围
    if (prizeData.weight < 0 || prizeData.weight > 100) {
        showMessage('中奖概率必须在0%到100%之间', 'error');
        return;
    }
    
    // 验证总概率不超过100%
    try {
        const response = await fetch('/api/admin/prizes/validate-probability', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                weight: prizeData.weight,
                excludeId: editingPrizeId // 编辑时排除当前奖品的概率
            })
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || '概率验证失败');
        }
        
        const validationResult = await response.json();
        if (!validationResult.valid) {
            showMessage(`概率验证失败：${validationResult.message}`, 'error');
            return;
        }
        
        // 如果概率验证通过但总和超过100%，给出提示
        if (validationResult.totalProbability > 100) {
            if (!confirm(`添加此奖品后，总概率将达到 ${validationResult.totalProbability.toFixed(1)}%，超过100%。是否继续？`)) {
                return;
            }
        }
    } catch (error) {
        console.error('概率验证失败:', error);
        showMessage('概率验证失败，请稍后重试', 'error');
        return;
    }
    
    try {
        let response;
        if (editingPrizeId) {
            // 更新奖品
            response = await fetch(`/api/admin/prizes/${editingPrizeId}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(prizeData)
            });
        } else {
            // 添加奖品
            response = await fetch('/api/admin/prizes', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(prizeData)
            });
        }
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || '操作失败');
        }
        
        showMessage(editingPrizeId ? '奖品信息更新成功' : '奖品添加成功', 'success');
        closePrizeModal();
        loadPrizes();
        loadPrizesStats();
        
        // 如果抽奖配置模态框是打开的，更新概率信息
        const lotteryModal = document.getElementById('lotteryConfigModal');
        if (lotteryModal && lotteryModal.style.display === 'block') {
            await updateProbabilityInfo();
        }
    } catch (error) {
        console.error('保存奖品失败:', error);
        showMessage(error.message, 'error');
    }
}

// 关闭奖品模态框
function closePrizeModal() {
    document.getElementById('prizeModal').style.display = 'none';
    editingPrizeId = null;
}

// 查看奖品详情
async function viewPrizeDetail(prizeId) {
    try {
        const response = await fetch(`/api/admin/prizes/${prizeId}`);
        if (!response.ok) {
            let errText = '';
            try {
                const errJson = await response.json();
                errText = errJson.detail || JSON.stringify(errJson);
            } catch (e) {
                errText = await response.text();
            }
            console.error('服务器返回错误：', response.status, errText);
            throw new Error('获取奖品详情失败: ' + (errText || response.statusText));
        }

        const prize = await response.json();
        
        const detailHTML = `
            <div class="prize-detail">
                <div class="detail-section">
                    <h4><i class="fas fa-info-circle"></i> 礼品信息</h4>
                    <div class="detail-grid">
                        <div class="detail-item">
                            <label>礼品名称:</label>
                            <span>${prize.Name || ''}</span>
                        </div>
                        <div class="detail-item">
                            <label>数量:</label>
                            <span class="${Number(prize.total || 0) === 0 ? 'total-badge zero-stock' : 'total-badge'}">${prize.total || 0}</span>
                        </div>
                        <div class="detail-item">
                            <label>中奖概率:</label>
                            <span class="weight-badge">${prize.weight || 0}%</span>
                        </div>
                        <div class="detail-item">
                            <label>创建时间:</label>
                            <span>${formatDate(prize.createdAt)}</span>
                        </div>
                    </div>
                </div>
                
                ${prize.photo ? `
                <div class="detail-section">
                    <h4><i class="fas fa-image"></i> 礼品图片</h4>
                    <img src="/Assest/Prize/${prize.photo}" alt="${prize.Name}" style="max-width: 300px; border-radius: 8px;">
                </div>
                ` : ''}
            </div>
        `;
        
        document.getElementById('prizeDetailContent').innerHTML = detailHTML;
        document.getElementById('prizeDetailModal').style.display = 'block';
        
    } catch (error) {
        console.error('查看奖品详情失败:', error);
        showMessage(error.message || '获取奖品详情失败', 'error');
    }
}

// 关闭奖品详情模态框
function closePrizeDetailModal() {
    document.getElementById('prizeDetailModal').style.display = 'none';
}

// 查看兑换记录
async function viewRedemptionHistory(prizeId) {
    try {
        const response = await fetch(`/api/admin/prizes/${prizeId}/redemptions`);
        if (!response.ok) throw new Error('获取兑换记录失败');
        
        const data = await response.json();
        const redemptions = data.redemptions || [];
        
        let redemptionHTML = '';
        if (redemptions.length === 0) {
            redemptionHTML = `
                <div class="empty-state">
                    <i class="fas fa-receipt"></i>
                    <p>暂无兑换记录</p>
                </div>
            `;
        } else {
            redemptionHTML = `
                <div class="redemption-list">
                    <table class="redemption-table">
                        <thead>
                            <tr>
                                <th>兑换用户</th>
                                <th>兑换时间</th>
                                <th>兑换码</th>
                                <th>使用积分</th>
                                <th>状态</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${redemptions.map(redemption => `
                                <tr>
                                    <td>
                                        <div>${redemption.userName || '-'}</div>
                                        <small class="text-muted">${redemption.userStudentId || '-'}</small>
                                    </td>
                                    <td>${formatDate(redemption.redeemedAt)}</td>
                                    <td><code>${redemption.redemptionCode}</code></td>
                                    <td>${redemption.pointsUsed || 0} 积分</td>
                                    <td>
                                        <span class="status-badge ${redemption.isRedeemed ? 'redeemed' : 'pending'}">
                                            ${redemption.isRedeemed ? '已使用' : '未使用'}
                                        </span>
                                    </td>
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                </div>
            `;
        }
        
        document.getElementById('redemptionContent').innerHTML = redemptionHTML;
        document.getElementById('redemptionModal').style.display = 'block';
        
    } catch (error) {
        console.error('查看兑换记录失败:', error);
        showMessage('获取兑换记录失败', 'error');
    }
}

// 关闭兑换记录模态框
function closeRedemptionModal() {
    document.getElementById('redemptionModal').style.display = 'none';
}

// 删除奖品
function deletePrize(prizeId, prizeName) {
    deletingPrizeId = prizeId;
    document.getElementById('deleteMessage').textContent = `确定要删除奖品 "${prizeName}" 吗？此操作不可恢复！`;
    document.getElementById('deleteModal').style.display = 'block';
}

// 确认删除
async function confirmDelete() {
    if (!deletingPrizeId) return;
    
    try {
        const response = await fetch(`/api/admin/prizes/${deletingPrizeId}`, {
            method: 'DELETE'
        });
        
        if (!response.ok) throw new Error('删除失败');
        
        showMessage('奖品删除成功', 'success');
        closeDeleteModal();
        loadPrizes();
        loadPrizesStats();
        
        // 如果抽奖配置模态框是打开的，更新概率信息
        const lotteryModal = document.getElementById('lotteryConfigModal');
        if (lotteryModal && lotteryModal.style.display === 'block') {
            await updateProbabilityInfo();
        }
    } catch (error) {
        console.error('删除奖品失败:', error);
        showMessage('删除奖品失败', 'error');
    }
}

// 关闭删除确认模态框
function closeDeleteModal() {
    document.getElementById('deleteModal').style.display = 'none';
    deletingPrizeId = null;
}

// 辅助函数
function getCategoryText(category) {
    const categoryMap = {
        'electronics': '数码产品',
        'stationery': '文具用品',
        'clothing': '服装配饰',
        'food': '食品饮料',
        'books': '图书资料',
        'other': '其他'
    };
    return categoryMap[category] || category;
}

function getStatusClass(prize) {
    if (!prize.isActive) return 'inactive';
    if (prize.quantity === 0) return 'out-of-stock';
    if (prize.quantity <= 5) return 'low-stock';
    return 'available';
}

function getStatusText(prize) {
    if (!prize.isActive) return '已停用';
    if (prize.quantity === 0) return '缺货';
    if (prize.quantity <= 5) return '库存不足';
    return '可用';
}

function formatDate(dateString, format = 'YYYY-MM-DD HH:mm') {
    if (!dateString) return '-';
    const date = new Date(dateString);
    
    if (format === 'YYYY-MM-DD') {
        return date.toLocaleDateString('zh-CN');
    }
    
    return date.toLocaleString('zh-CN');
}

function showLoading() {
    const tbody = document.getElementById('prizesTableBody');
    tbody.innerHTML = `
        <tr>
            <td colspan="5" class="loading">
                <i class="fas fa-spinner"></i>
                加载中...
            </td>
        </tr>
    `;
}

function hideLoading() {
    // 加载完成后会调用 renderPrizesTable() 或 showEmptyState()
    // 这里不需要特殊处理
}

function showEmptyState() {
    const tbody = document.getElementById('prizesTableBody');
    tbody.innerHTML = `
        <tr>
            <td colspan="5" class="empty-state">
                <i class="fas fa-gift"></i>
                <p>暂无礼品数据</p>
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
        closePrizeModal();
        closePrizeDetailModal();
        closeRedemptionModal();
        closeDeleteModal();
    }
    
    // 回车键搜索
    if (e.key === 'Enter' && e.target.id === 'searchInput') {
        searchPrizes();
    }
});

// 点击模态框外部关闭
window.addEventListener('click', function(e) {
    if (e.target.classList.contains('modal')) {
        if (e.target.id === 'prizeModal') closePrizeModal();
        if (e.target.id === 'prizeDetailModal') closePrizeDetailModal();
        if (e.target.id === 'redemptionModal') closeRedemptionModal();
        if (e.target.id === 'deleteModal') closeDeleteModal();
    }
});

// 批量操作相关功能（简化版）
function showBatchUpdateModal() {
    if (selectedPrizes.length === 0) {
        showMessage('请先选择要操作的奖品', 'warning');
        return;
    }
    
    document.getElementById('selectedCount').textContent = selectedPrizes.length;
    document.getElementById('batchUpdateModal').style.display = 'block';
}

function closeBatchUpdateModal() {
    document.getElementById('batchUpdateModal').style.display = 'none';
}

function toggleBatchFields() {
    const action = document.getElementById('batchAction').value;
    const fieldsDiv = document.getElementById('batchFields');
    
    let fieldsHTML = '';
    switch(action) {
        case 'updateStock':
            fieldsHTML = `
                <div class="form-group">
                    <label for="newStock">新库存数量:</label>
                    <input type="number" id="newStock" min="0" required>
                </div>
            `;
            break;
        case 'updateStatus':
            fieldsHTML = `
                <div class="form-group">
                    <label for="newStatus">新状态:</label>
                    <select id="newStatus" required>
                        <option value="true">启用</option>
                        <option value="false">停用</option>
                    </select>
                </div>
            `;
            break;
        case 'updateCategory':
            fieldsHTML = `
                <div class="form-group">
                    <label for="newCategory">新类别:</label>
                    <select id="newCategory" required>
                        <option value="electronics">数码产品</option>
                        <option value="stationery">文具用品</option>
                        <option value="clothing">服装配饰</option>
                        <option value="food">食品饮料</option>
                        <option value="books">图书资料</option>
                        <option value="other">其他</option>
                    </select>
                </div>
            `;
            break;
        case 'adjustPoints':
            fieldsHTML = `
                <div class="form-group">
                    <label for="pointsAdjustment">积分调整:</label>
                    <select id="adjustmentType">
                        <option value="set">设置为</option>
                        <option value="add">增加</option>
                        <option value="subtract">减少</option>
                    </select>
                    <input type="number" id="pointsValue" min="0" required>
                </div>
            `;
            break;
    }
    
    fieldsDiv.innerHTML = fieldsHTML;
    fieldsDiv.style.display = action ? 'block' : 'none';
}

async function executeBatchUpdate() {
    const action = document.getElementById('batchAction').value;
    if (!action) {
        showMessage('请选择批量操作类型', 'warning');
        return;
    }
    
    // 这里可以根据实际需要实现批量更新逻辑
    showMessage('批量更新功能开发中...', 'info');
    closeBatchUpdateModal();
}

async function exportRedemptions() {
    try {
        showMessage('正在准备导出兑换记录...', 'info');
        
        const response = await fetch('/api/admin/prizes/redemptions/export');
        if (!response.ok) throw new Error('导出失败');
        
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `redemptions_${formatDate(new Date(), 'YYYY-MM-DD')}.csv`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
        
        showMessage('兑换记录导出成功', 'success');
    } catch (error) {
        console.error('导出兑换记录失败:', error);
        showMessage('导出兑换记录失败', 'error');
    }
}

// 抽奖配置相关功能
async function showLotteryConfigModal() {
    try {
        // 尝试拉取当前后端的抽奖配置并展示在模态框中
        const response = await fetch('/api/admin/lottery-config');
        if (response.ok) {
            const config = await response.json();
            // 如果页面中存在对应表单字段则填充
            const pointsEl = document.getElementById('lotteryPoints');
            const timesEl = document.getElementById('lotteryTimes');
            if (pointsEl) pointsEl.value = config.lotteryPoints ?? '';
            if (timesEl) timesEl.value = config.times ?? '';
        }
        
        // 计算和更新概率信息
        await updateProbabilityInfo();
        
        document.getElementById('lotteryConfigModal').style.display = 'block';
    } catch (error) {
        console.error('打开抽奖配置模态框失败:', error);
        showMessage('无法加载抽奖配置，请稍后重试', 'error');
    }
}

// 更新概率信息显示
async function updateProbabilityInfo() {
    try {
        console.log('开始更新概率信息...');
        
        // 获取概率总和信息
        const response = await fetch('/api/admin/prizes/probability-summary');
        
        console.log('API响应状态:', response.status, response.ok);
        
        if (response.ok) {
            const data = await response.json();
            console.log('API返回数据:', data);
            
            // 更新显示
            const totalProbabilityEl = document.getElementById('totalProbability');
            const thanksProbabilityEl = document.getElementById('thanksProbability');
            
            if (totalProbabilityEl) {
                console.log('更新 totalProbability:', data.totalProbability);
                totalProbabilityEl.textContent = `${data.totalProbability.toFixed(1)}%`;
            }
            
            if (thanksProbabilityEl) {
                console.log('更新 thanksProbability:', data.thanksProbability);
                thanksProbabilityEl.textContent = `${data.thanksProbability.toFixed(1)}%`;
            }
        } else {
            const errorText = await response.text();
            console.error('API响应错误:', response.status, errorText);
            throw new Error(`API请求失败: ${response.status} ${errorText}`);
        }
        
    } catch (error) {
        console.error('更新概率信息失败:', error);
        
        // 如果API失败，尝试从本地数据计算
        console.log('使用本地数据计算概率, prizesData:', prizesData);
        let totalProbability = 0;
        if (prizesData && prizesData.length > 0) {
            const filteredPrizes = prizesData.filter(prize => prize.isActive !== false && prize.isDefault !== true);
            console.log('过滤后的奖品:', filteredPrizes);
            
            totalProbability = filteredPrizes.reduce((sum, prize) => {
                const weight = parseFloat(prize.weight) || 0;
                console.log(`奖品 ${prize.Name || 'Unknown'}: weight=${weight}`);
                return sum + weight;
            }, 0);
        }
        
        console.log('计算得到的totalProbability:', totalProbability);
        
        // 更新显示
        const totalProbabilityEl = document.getElementById('totalProbability');
        const thanksProbabilityEl = document.getElementById('thanksProbability');
        
        if (totalProbabilityEl) {
            totalProbabilityEl.textContent = `${totalProbability.toFixed(1)}%`;
        }
        
        if (thanksProbabilityEl) {
            const thanksProb = Math.max(0, 100 - totalProbability);
            thanksProbabilityEl.textContent = `${thanksProb.toFixed(1)}%`;
        }
    }
}

async function saveLotteryConfig() {
    try {
        const pointsEl = document.getElementById('lotteryPoints');
        const timesEl = document.getElementById('lotteryTimes');
        const configData = {
            lotteryPoints: pointsEl ? parseInt(pointsEl.value, 10) || 0 : 0,
            times: timesEl ? parseInt(timesEl.value, 10) || 1 : 1
        };

        if (configData.lotteryPoints < 1) {
            showMessage('抽奖积分必须大于0', 'error');
            return;
        }

        const response = await fetch('/api/admin/lottery-config', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(configData)
        });

        if (!response.ok) {
            let errText = '';
            try {
                const errJson = await response.json();
                errText = errJson.detail || JSON.stringify(errJson);
            } catch (e) {
                errText = await response.text();
            }
            throw new Error(errText || '保存失败');
        }

        const result = await response.json();
        showMessage(result.message || '抽奖配置保存成功', 'success');
        closeLotteryConfigModal();
    } catch (error) {
        console.error('保存抽奖配置失败:', error);
        showMessage(error.message || '保存抽奖配置失败', 'error');
    }
}

function closeLotteryConfigModal() {
    document.getElementById('lotteryConfigModal').style.display = 'none';
}

// 初始化导航栏
document.addEventListener('DOMContentLoaded', function() {
    new NavigationBar();
});

// 图片上传相关功能
let selectedFile = null;
let uploadedFilename = null;

// 处理图片上传
async function handleImageUpload(input) {
    const file = input.files[0];
    if (!file) return;
    
    // 验证文件类型
    if (!file.type.startsWith('image/')) {
        showMessage('请选择图片文件', 'error');
        return;
    }
    
    // 验证文件大小（50MB）
    if (file.size > 50 * 1024 * 1024) {
        showMessage('图片大小不能超过50MB', 'error');
        return;
    }
    
    selectedFile = file;
    
    // 显示预览
    const reader = new FileReader();
    reader.onload = function(e) {
        const preview = document.getElementById('imagePreview');
        preview.innerHTML = `<img src="${e.target.result}" alt="预览图片">`;
        preview.classList.add('has-image');
    };
    reader.readAsDataURL(file);
    
    // 直接上传图片
    await uploadImageDirect();
}

// 直接上传图片
async function uploadImageDirect() {
    if (!selectedFile) {
        showMessage('请先选择图片', 'error');
        return;
    }
    
    try {
        showLoading('正在上传图片...');
        
        const formData = new FormData();
        formData.append('file', selectedFile);
        
        const response = await fetch('/api/admin/prizes/upload-image', {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || '上传失败');
        }
        
        const result = await response.json();
        uploadedFilename = result.filename;
        
        // 更新预览和隐藏字段
        const preview = document.getElementById('imagePreview');
        preview.innerHTML = `<img src="/Assest/Prize/${result.filename}" alt="上传的图片">`;
        document.getElementById('photo').value = result.filename;
        
        hideLoading();
        showMessage('图片上传成功', 'success');
        
    } catch (error) {
        hideLoading();
        console.error('上传图片失败:', error);
        showMessage(error.message || '上传图片失败', 'error');
    }
}

// 切换奖品激活状态
async function togglePrizeActive(prizeId, isActive) {
    try {
        const response = await fetch(`/api/admin/prizes/${prizeId}/toggle-active`, {
            method: 'PATCH',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || '切换状态失败');
        }
        
        const data = await response.json();
        showMessage(data.message, 'success');
        
        // 重新加载数据
        await loadPrizes();
        await loadPrizesStats();
        
        // 如果抽奖配置模态框是打开的，更新概率信息
        const lotteryModal = document.getElementById('lotteryConfigModal');
        if (lotteryModal && lotteryModal.style.display === 'block') {
            await updateProbabilityInfo();
        }
        
    } catch (error) {
        console.error('切换奖品状态失败:', error);
        showMessage(error.message || '切换状态失败', 'error');
        
        // 恢复开关状态
        setTimeout(() => {
            loadPrizes();
        }, 100);
    }
}