// 汇总看板页面JavaScript逻辑
let charts = {};

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', function() {
    checkAuth();
    initCharts();
    loadAllData();
});

// 检查用户权限
async function checkAuth() {
    try {
        const response = await fetch('/api/user/info');
        if (!response.ok) {
            window.location.href = '/login';
            return;
        }
        
        const userData = await response.json();
        if (userData.role !== 'super_admin') {
            alert('权限不足，只有超级管理员可以访问此页面');
            window.location.href = '/info';
            return;
        }
    } catch (error) {
        console.error('权限检查失败:', error);
        window.location.href = '/login';
    }
}

// 初始化所有图表
function initCharts() {
    // 学院分布饼图
    charts.membersDistribution = echarts.init(document.getElementById('membersDistributionChart'));
    
    // 关卡完成情况饼图
    charts.levelCompletion = echarts.init(document.getElementById('levelCompletionChart'));
    
    // 奖品抽奖统计饼图
    charts.prizeDraw = echarts.init(document.getElementById('prizeDrawChart'));
    
    // 人流量分布折线图
    charts.registrationTimeline = echarts.init(document.getElementById('registrationTimelineChart'));
    
    // 响应窗口大小变化
    window.addEventListener('resize', function() {
        Object.values(charts).forEach(chart => chart.resize());
    });
}

// 加载所有数据
async function loadAllData() {
    showLoading();
    
    try {
        await Promise.all([
            loadOverviewStats(),
            loadMembersDistribution(),
            loadLevelCompletion(),
            loadPrizeDrawStats(),
            loadRegistrationTimeline()
        ]);
    } catch (error) {
        console.error('加载数据失败:', error);
        showMessage('加载数据失败，请刷新页面重试', 'error');
    } finally {
        hideLoading();
    }
}

// 加载总览统计数据
async function loadOverviewStats() {
    try {
        const response = await fetch('/api/admin/dashboard/stats/overview');
        if (!response.ok) throw new Error('获取总览数据失败');
        
        const data = await response.json();
        document.getElementById('totalUsers').textContent = data.totalUsers || 0;
        document.getElementById('totalLevels').textContent = data.totalLevels || 0;
        document.getElementById('totalPrizeTypes').textContent = data.totalPrizeTypes || 0;
        document.getElementById('totalDrawn').textContent = data.totalDrawn || 0;
    } catch (error) {
        console.error('加载总览数据失败:', error);
    }
}

// 加载学院分布数据
async function loadMembersDistribution() {
    try {
        const response = await fetch('/api/admin/dashboard/stats/members-distribution');
        if (!response.ok) throw new Error('获取学院分布数据失败');
        
        const data = await response.json();
        
        const option = {
            tooltip: {
                trigger: 'item',
                formatter: '{b}: {c}人 ({d}%)'
            },
            legend: {
                orient: 'horizontal',
                bottom: '0%',
                left: 'center'
            },
            color: ['#667eea', '#43e97b'],
            series: [
                {
                    name: '学院分布',
                    type: 'pie',
                    radius: ['40%', '70%'],
                    avoidLabelOverlap: true,
                    itemStyle: {
                        borderRadius: 10,
                        borderColor: '#fff',
                        borderWidth: 2
                    },
                    label: {
                        show: true,
                        formatter: '{b}\n{c}人'
                    },
                    emphasis: {
                        label: {
                            show: true,
                            fontSize: 16,
                            fontWeight: 'bold'
                        }
                    },
                    labelLine: {
                        show: true
                    },
                    data: [
                        { value: data.jiwang, name: '计网学院' },
                        { value: data.other, name: '其他学院' }
                    ]
                }
            ]
        };
        
        charts.membersDistribution.setOption(option);
    } catch (error) {
        console.error('加载学院分布数据失败:', error);
        showEmptyChart(charts.membersDistribution, '暂无学院分布数据');
    }
}

// 加载关卡完成情况数据
async function loadLevelCompletion() {
    try {
        const response = await fetch('/api/admin/dashboard/stats/level-completion');
        if (!response.ok) throw new Error('获取关卡完成数据失败');
        
        const data = await response.json();
        
        if (!data || data.length === 0) {
            showEmptyChart(charts.levelCompletion, '暂无关卡数据');
            return;
        }
        
        const option = {
            tooltip: {
                trigger: 'item',
                formatter: '{b}: {c}人 ({d}%)'
            },
            legend: {
                orient: 'horizontal',
                bottom: '0%',
                left: 'center',
                type: 'scroll'
            },
            color: ['#667eea', '#764ba2', '#f093fb', '#f5576c', '#4facfe', '#00f2fe', '#43e97b', '#38f9d7', '#fa709a', '#fee140'],
            series: [
                {
                    name: '关卡闯关',
                    type: 'pie',
                    radius: ['40%', '70%'],
                    avoidLabelOverlap: true,
                    itemStyle: {
                        borderRadius: 10,
                        borderColor: '#fff',
                        borderWidth: 2
                    },
                    label: {
                        show: true,
                        formatter: '{b}\n{c}人'
                    },
                    emphasis: {
                        label: {
                            show: true,
                            fontSize: 16,
                            fontWeight: 'bold'
                        }
                    },
                    labelLine: {
                        show: true
                    },
                    data: data.map(item => ({
                        value: item.count,
                        name: item.name
                    }))
                }
            ]
        };
        
        charts.levelCompletion.setOption(option);
    } catch (error) {
        console.error('加载关卡完成数据失败:', error);
        showEmptyChart(charts.levelCompletion, '暂无关卡完成数据');
    }
}

// 加载奖品抽奖统计数据
async function loadPrizeDrawStats() {
    try {
        const response = await fetch('/api/admin/dashboard/stats/prize-draw');
        if (!response.ok) throw new Error('获取奖品抽奖数据失败');
        
        const data = await response.json();
        
        if (!data || data.length === 0) {
            showEmptyChart(charts.prizeDraw, '暂无抽奖数据');
            return;
        }
        
        const option = {
            tooltip: {
                trigger: 'item',
                formatter: '{b}: {c}次 ({d}%)'
            },
            legend: {
                orient: 'horizontal',
                bottom: '0%',
                left: 'center',
                type: 'scroll'
            },
            color: ['#667eea', '#764ba2', '#f093fb', '#f5576c', '#4facfe', '#00f2fe', '#43e97b', '#38f9d7', '#fa709a', '#fee140'],
            series: [
                {
                    name: '奖品抽奖',
                    type: 'pie',
                    radius: ['40%', '70%'],
                    avoidLabelOverlap: true,
                    itemStyle: {
                        borderRadius: 10,
                        borderColor: '#fff',
                        borderWidth: 2
                    },
                    label: {
                        show: true,
                        formatter: '{b}\n{c}次'
                    },
                    emphasis: {
                        label: {
                            show: true,
                            fontSize: 16,
                            fontWeight: 'bold'
                        }
                    },
                    labelLine: {
                        show: true
                    },
                    data: data.map(item => ({
                        value: item.count,
                        name: item.name
                    }))
                }
            ]
        };
        
        charts.prizeDraw.setOption(option);
    } catch (error) {
        console.error('加载奖品抽奖数据失败:', error);
        showEmptyChart(charts.prizeDraw, '暂无奖品抽奖数据');
    }
}

// 加载人流量分布数据
async function loadRegistrationTimeline() {
    try {
        const response = await fetch('/api/admin/dashboard/stats/registration-timeline');
        if (!response.ok) throw new Error('获取人流量分布数据失败');
        
        const data = await response.json();
        
        const option = {
            tooltip: {
                trigger: 'axis',
                formatter: '{b}:00 - {c}人'
            },
            xAxis: {
                type: 'category',
                data: data.map(item => `${item.hour}:00`),
                name: '时间（小时）',
                nameLocation: 'middle',
                nameGap: 30,
                axisLabel: {
                    rotate: 45,
                    interval: 0
                }
            },
            yAxis: {
                type: 'value',
                name: '人数',
                nameLocation: 'middle',
                nameGap: 40,
                minInterval: 1
            },
            grid: {
                left: '10%',
                right: '5%',
                bottom: '15%',
                top: '10%',
                containLabel: true
            },
            series: [
                {
                    name: '人数',
                    type: 'line',
                    smooth: true,
                    symbol: 'circle',
                    symbolSize: 8,
                    lineStyle: {
                        width: 3,
                        color: '#667eea'
                    },
                    itemStyle: {
                        color: '#667eea',
                        borderColor: '#fff',
                        borderWidth: 2
                    },
                    areaStyle: {
                        color: {
                            type: 'linear',
                            x: 0,
                            y: 0,
                            x2: 0,
                            y2: 1,
                            colorStops: [
                                { offset: 0, color: 'rgba(102, 126, 234, 0.5)' },
                                { offset: 1, color: 'rgba(102, 126, 234, 0.1)' }
                            ]
                        }
                    },
                    data: data.map(item => item.count),
                    label: {
                        show: false  // 不显示数据标签
                    }
                }
            ]
        };
        
        charts.registrationTimeline.setOption(option);
    } catch (error) {
        console.error('加载人流量分布数据失败:', error);
        showEmptyChart(charts.registrationTimeline, '暂无人流量数据');
    }
}

// 显示空图表提示
function showEmptyChart(chart, message) {
    const option = {
        title: {
            text: message,
            left: 'center',
            top: 'center',
            textStyle: {
                color: '#999',
                fontSize: 16
            }
        }
    };
    chart.setOption(option);
}

// 显示加载提示
function showLoading() {
    const indicator = document.getElementById('loadingIndicator');
    if (indicator) {
        indicator.style.display = 'block';
    }
}

// 隐藏加载提示
function hideLoading() {
    const indicator = document.getElementById('loadingIndicator');
    if (indicator) {
        indicator.style.display = 'none';
    }
}

// 显示消息提示（如果utils.js中有，可以使用那个）
function showMessage(message, type = 'info') {
    // 简单的消息提示实现
    const alertType = type === 'error' ? 'danger' : type;
    alert(message);
}
