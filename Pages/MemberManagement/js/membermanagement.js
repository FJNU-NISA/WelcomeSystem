// 成员管理页面JavaScript逻辑
let currentPage = 1;
let pageSize = 10;
let totalMembers = 0;
let currentFilter = 'all';
let currentSearch = '';
let editingMemberId = null;
let deletingMemberId = null;
let membersData = [];

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', function() {
    checkAuth();
    loadMembersStats();
    loadMembers();
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

// 加载成员统计信息
async function loadMembersStats() {
    try {
        const response = await fetch('/api/admin/members/stats');
        if (!response.ok) throw new Error('获取统计信息失败');
        
        const stats = await response.json();
        document.getElementById('totalMembers').textContent = stats.total || 0;
        document.getElementById('regularMembers').textContent = stats.user || 0;
        document.getElementById('adminMembers').textContent = stats.admin || 0;
        document.getElementById('superAdminMembers').textContent = stats.super_admin || 0;
    } catch (error) {
        console.error('加载统计信息失败:', error);
        showMessage('加载统计信息失败', 'error');
    }
}

// 加载成员列表
async function loadMembers() {
    try {
        showLoading();
        
        const params = new URLSearchParams({
            page: currentPage,
            limit: pageSize
        });
        
        if (currentFilter !== 'all') {
            params.append('role', currentFilter);
        }
        
        if (currentSearch) {
            params.append('search', currentSearch);
        }
        
        const response = await fetch(`/api/admin/members?${params}`);
        if (!response.ok) throw new Error('获取成员列表失败');
        
        const data = await response.json();
        membersData = data.members || [];
        totalMembers = data.total || 0;
        
        renderMembersTable();
        renderPagination();
        
    } catch (error) {
        console.error('加载成员列表失败:', error);
        showMessage('加载成员列表失败', 'error');
        showEmptyState();
    }
}

// 渲染成员表格
function renderMembersTable() {
    const tbody = document.getElementById('membersTableBody');
    
    if (membersData.length === 0) {
        showEmptyState();
        return;
    }
    
    tbody.innerHTML = membersData.map(member => `
        <tr>
            <td>${member.stuId}</td>
            <td>
                <span class="role-badge ${member.role}">
                    ${getRoleText(member.role)}
                </span>
            </td>
            <td>${member.points || 0}</td>
            <td>
                <div class="passed-levels">
                    ${member.passedLevelNames && member.passedLevelNames.length > 0 
                        ? member.passedLevelNames.join(', ') 
                        : '无'}
                </div>
            </td>
            <td>${formatDate(member.creatTime)}</td>
            <td>
                <button class="action-btn view" onclick="viewMemberDetail('${member._id}')" title="查看详情">
                    <i class="fas fa-eye"></i>
                </button>
                <button class="action-btn edit" onclick="editMember('${member._id}')" title="编辑成员">
                    <i class="fas fa-edit"></i>
                </button>
                <button class="action-btn delete" onclick="deleteMember('${member._id}', '${member.stuId}')" title="删除成员">
                    <i class="fas fa-trash"></i>
                </button>
            </td>
        </tr>
    `).join('');
}

// 渲染分页控件
function renderPagination() {
    const totalPages = Math.ceil(totalMembers / pageSize);
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
    if (page < 1 || page > Math.ceil(totalMembers / pageSize)) return;
    currentPage = page;
    loadMembers();
}

// 搜索成员
function searchMembers() {
    currentSearch = document.getElementById('searchInput').value.trim();
    currentPage = 1;
    loadMembers();
}

// 清空搜索
function clearSearch() {
    document.getElementById('searchInput').value = '';
    currentSearch = '';
    currentPage = 1;
    loadMembers();
}

// 筛选成员
function filterMembers() {
    currentFilter = document.getElementById('roleFilter').value;
    currentPage = 1;
    loadMembers();
}

// 显示添加成员模态框
function showAddMemberModal() {
    editingMemberId = null;
    document.getElementById('modalTitle').textContent = '添加成员';
    document.getElementById('memberForm').reset();
    document.getElementById('studentId').disabled = false;
    
    // 添加模式下恢复密码字段的原始提示文本
    const passwordField = document.getElementById('password');
    const passwordHelp = passwordField.parentElement.querySelector('.form-help');
    passwordField.placeholder = '留空则默认密码为学号';
    passwordHelp.textContent = '如果不设置密码，默认密码将设置为用户的学号';
    
    document.getElementById('memberModal').style.display = 'block';
}

// 编辑成员
async function editMember(memberId) {
    try {
        const response = await fetch(`/api/admin/members/${memberId}`);
        if (!response.ok) throw new Error('获取成员信息失败');
        
        const member = await response.json();
        
        editingMemberId = memberId;
        document.getElementById('modalTitle').textContent = '编辑成员';
        document.getElementById('studentId').value = member.stuId;
        document.getElementById('studentId').disabled = true;
        document.getElementById('role').value = member.role;
        document.getElementById('points').value = member.points || 0;
        
        // 编辑模式下修改密码字段的提示文本
        const passwordField = document.getElementById('password');
        const passwordHelp = passwordField.parentElement.querySelector('.form-help');
        passwordField.value = '';
        passwordField.placeholder = '留空表示不修改密码';
        passwordHelp.textContent = '留空表示不修改当前密码，如需修改请输入新密码';
        
        document.getElementById('memberModal').style.display = 'block';
    } catch (error) {
        console.error('编辑成员失败:', error);
        showMessage('获取成员信息失败', 'error');
    }
}

// 保存成员
async function saveMember() {
    const form = document.getElementById('memberForm');
    const formData = new FormData(form);
    
    // 调试信息
    console.log('saveMember调用 - editingMemberId:', editingMemberId);
    console.log('formData studentId:', formData.get('studentId'));
    console.log('formData role:', formData.get('role'));
    
    const memberData = {
        role: formData.get('role'),
        points: parseInt(formData.get('points')) || 0
    };
    
    // 只有在添加成员模式下才需要学号
    if (!editingMemberId) {
        console.log('添加成员模式 - 需要验证学号');
        const stuId = formData.get('studentId');
        if (!stuId) {
            console.log('学号为空，显示错误');
            showMessage('请填写所有必填字段', 'error');
            return;
        }
        memberData.stuId = stuId;
    } else {
        console.log('编辑成员模式 - 跳过学号验证');
    }
    
    const password = formData.get('password');
    if (password) {
        memberData.password = password;
    }
    
    // 验证必填字段
    if (!memberData.role) {
        showMessage('请填写所有必填字段', 'error');
        return;
    }
    
    try {
        let response;
        if (editingMemberId) {
            // 更新成员
            response = await fetch(`/api/admin/members/${editingMemberId}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(memberData)
            });
        } else {
            // 添加成员
            response = await fetch('/api/admin/members', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(memberData)
            });
        }
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || '操作失败');
        }
        
        showMessage(editingMemberId ? '成员信息更新成功' : '成员添加成功', 'success');
        closeMemberModal();
        loadMembers();
        loadMembersStats();
    } catch (error) {
        console.error('保存成员失败:', error);
        showMessage(error.message, 'error');
    }
}

// 关闭成员模态框
function closeMemberModal() {
    document.getElementById('memberModal').style.display = 'none';
    editingMemberId = null;
    
    // 重置密码字段的提示文本为默认状态
    const passwordField = document.getElementById('password');
    const passwordHelp = passwordField.parentElement.querySelector('.form-help');
    passwordField.placeholder = '留空则默认密码为学号';
    passwordHelp.textContent = '如果不设置密码，默认密码将设置为用户的学号';
}

// 查看成员详情
async function viewMemberDetail(memberId) {
    try {
        // 从已加载的数据中查找成员信息
        const member = membersData.find(m => m._id === memberId);
        if (!member) {
            showMessage('未找到成员信息', 'error');
            return;
        }
        
        const detailHTML = `
            <div class="member-detail">
                <div class="detail-section">
                    <h4><i class="fas fa-user"></i> 基本信息</h4>
                    <div class="detail-grid">
                        <div class="detail-item">
                            <label>学号:</label>
                            <span>${member.stuId || '-'}</span>
                        </div>
                        <div class="detail-item">
                            <label>权限:</label>
                            <span class="role-badge ${member.role}">${getRoleText(member.role)}</span>
                        </div>
                        <div class="detail-item">
                            <label>积分:</label>
                            <span>${member.points || 0}</span>
                        </div>
                        <div class="detail-item">
                            <label>注册时间:</label>
                            <span>${formatDate(member.creatTime)}</span>
                        </div>
                        <div class="detail-item">
                            <label>创建者:</label>
                            <span>${member.createdBy || '-'}</span>
                        </div>
                        <div class="detail-item">
                            <label>最后更新:</label>
                            <span>${member.updatedBy ? '由 ' + member.updatedBy + ' 更新' : '-'}</span>
                        </div>
                    </div>
                </div>
                
                <div class="detail-section">
                    <h4><i class="fas fa-trophy"></i> 关卡进度</h4>
                    <div class="level-progress">
                        <p>已通过关卡: ${member.passedLevelNames ? member.passedLevelNames.length : 0} 个</p>
                        ${member.passedLevelNames && member.passedLevelNames.length > 0 ? `
                            <div class="passed-levels">
                                ${member.passedLevelNames.map(levelName => `
                                    <span class="level-tag">${levelName}</span>
                                `).join('')}
                            </div>
                        ` : '<p class="no-data">暂无通过的关卡</p>'}
                    </div>
                </div>
                
                <div class="detail-section">
                    <h4><i class="fas fa-info-circle"></i> 其他信息</h4>
                    <div class="other-info">
                        <div class="detail-item">
                            <label>通过关卡ID列表:</label>
                            <span>${(member.completedLevels || []).length}</span>
                        </div>
                        ${member._id ? `
                            <div class="detail-item">
                                <label>用户ID:</label>
                                <span class="user-id">${member._id}</span>
                            </div>
                        ` : ''}
                    </div>
                </div>
            </div>
        `;
        
        document.getElementById('memberDetailContent').innerHTML = detailHTML;
        document.getElementById('memberDetailModal').style.display = 'block';
        
    } catch (error) {
        console.error('查看成员详情失败:', error);
        showMessage('获取成员详情失败', 'error');
    }
}

// 关闭成员详情模态框
function closeMemberDetailModal() {
    document.getElementById('memberDetailModal').style.display = 'none';
}

// 删除成员
function deleteMember(memberId, memberName) {
    deletingMemberId = memberId;
    document.getElementById('deleteMessage').textContent = `确定要删除成员 "${memberName}" 吗？此操作不可恢复！`;
    document.getElementById('deleteModal').style.display = 'block';
}

// 确认删除
async function confirmDelete() {
    if (!deletingMemberId) return;
    
    try {
        const response = await fetch(`/api/admin/members/${deletingMemberId}`, {
            method: 'DELETE'
        });
        
        if (!response.ok) {
            // 获取详细错误信息
            const errorData = await response.json();
            const errorMessage = errorData.detail || '删除失败';
            throw new Error(errorMessage);
        }
        
        showMessage('成员删除成功', 'success');
        closeDeleteModal();
        loadMembers();
        loadMembersStats();
    } catch (error) {
        console.error('删除成员失败:', error);
        showMessage(error.message || '删除成员失败', 'error');
    }
}

// 关闭删除确认模态框
function closeDeleteModal() {
    document.getElementById('deleteModal').style.display = 'none';
    deletingMemberId = null;
}

// 辅助函数
function getRoleText(role) {
    const roleMap = {
        'user': '普通成员',
        'admin': '管理员',
        'super_admin': '超级管理员'
    };
    return roleMap[role] || role;
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
    const tbody = document.getElementById('membersTableBody');
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
    const tbody = document.getElementById('membersTableBody');
    tbody.innerHTML = `
        <tr>
            <td colspan="8" class="empty-state">
                <i class="fas fa-users"></i>
                <p>暂无成员数据</p>
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
        closeMemberModal();
        closeMemberDetailModal();
        closeDeleteModal();
    }
    
    // 回车键搜索
    if (e.key === 'Enter' && e.target.id === 'searchInput') {
        searchMembers();
    }
});

// 点击模态框外部关闭
window.addEventListener('click', function(e) {
    if (e.target.classList.contains('modal')) {
        if (e.target.id === 'memberModal') closeMemberModal();
        if (e.target.id === 'memberDetailModal') closeMemberDetailModal();
        if (e.target.id === 'deleteModal') closeDeleteModal();
    }
});