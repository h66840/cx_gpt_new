/**
 * 无人机操控应用UI修复 - 控制面板交互逻辑
 * 解决按钮重叠问题并提供动态布局调整
 */

class DroneControlPanelManager {
    constructor() {
        this.isInitialized = false;
        this.currentOrientation = this.getOrientation();
        this.deviceType = this.detectDeviceType();
        this.touchSupport = this.detectTouchSupport();
        
        this.init();
    }

    /**
     * 初始化控制面板管理器
     */
    init() {
        if (this.isInitialized) return;
        
        this.setupEventListeners();
        this.adjustLayoutForDevice();
        this.preventButtonOverlap();
        this.setupAccessibility();
        
        this.isInitialized = true;
        console.log('无人机控制面板UI修复已初始化');
    }

    /**
     * 设置事件监听器
     */
    setupEventListeners() {
        // 监听屏幕方向变化
        window.addEventListener('orientationchange', () => {
            setTimeout(() => {
                this.handleOrientationChange();
            }, 100);
        });

        // 监听窗口大小变化
        window.addEventListener('resize', this.debounce(() => {
            this.adjustLayoutForDevice();
            this.preventButtonOverlap();
        }, 250));

        // 监听控制按钮点击
        this.setupControlButtonListeners();
    }

    /**
     * 设置控制按钮监听器
     */
    setupControlButtonListeners() {
        // 起飞按钮
        const takeoffBtn = document.querySelector('.takeoff-btn');
        if (takeoffBtn) {
            takeoffBtn.addEventListener('click', this.handleTakeoffClick.bind(this));
            takeoffBtn.addEventListener('touchstart', this.handleTouchFeedback.bind(this));
        }

        // 紧急停止按钮
        const emergencyBtn = document.querySelector('.emergency-stop-btn');
        if (emergencyBtn) {
            emergencyBtn.addEventListener('click', this.handleEmergencyStopClick.bind(this));
            emergencyBtn.addEventListener('touchstart', this.handleTouchFeedback.bind(this));
        }

        // 相机控制按钮
        const photoBtn = document.querySelector('.photo-btn');
        const videoBtn = document.querySelector('.video-btn');
        
        if (photoBtn) {
            photoBtn.addEventListener('click', this.handlePhotoClick.bind(this));
            photoBtn.addEventListener('touchstart', this.handleTouchFeedback.bind(this));
        }
        
        if (videoBtn) {
            videoBtn.addEventListener('click', this.handleVideoClick.bind(this));
            videoBtn.addEventListener('touchstart', this.handleTouchFeedback.bind(this));
        }

        // 参数滑块
        const sliders = document.querySelectorAll('.parameter-slider');
        sliders.forEach(slider => {
            slider.addEventListener('input', this.handleSliderChange.bind(this));
            slider.addEventListener('touchmove', this.preventSliderOverlap.bind(this));
        });
    }

    /**
     * 处理屏幕方向变化
     */
    handleOrientationChange() {
        const newOrientation = this.getOrientation();
        if (newOrientation !== this.currentOrientation) {
            this.currentOrientation = newOrientation;
            this.adjustLayoutForDevice();
            this.preventButtonOverlap();
            
            // 重新计算按钮位置
            this.recalculateButtonPositions();
        }
    }

    /**
     * 根据设备调整布局
     */
    adjustLayoutForDevice() {
        const controlPanel = document.querySelector('.drone-control-panel');
        if (!controlPanel) return;

        // 移除所有设备类型类名
        controlPanel.classList.remove('mobile-portrait', 'mobile-landscape', 'tablet-portrait', 'tablet-landscape', 'desktop');

        // 根据设备类型和方向添加相应类名
        const deviceClass = this.getDeviceLayoutClass();
        controlPanel.classList.add(deviceClass);

        // 调整触控区域大小
        if (this.touchSupport) {
            this.adjustTouchTargets();
        }
    }

    /**
     * 防止按钮重叠
     */
    preventButtonOverlap() {
        this.preventTakeoffButtonOverlap();
        this.preventCameraButtonOverlap();
        this.preventSliderOverlap();
    }

    /**
     * 防止起飞控制按钮重叠
     */
    preventTakeoffButtonOverlap() {
        const takeoffBtn = document.querySelector('.takeoff-btn');
        const emergencyBtn = document.querySelector('.emergency-stop-btn');
        
        if (!takeoffBtn || !emergencyBtn) return;

        const takeoffRect = takeoffBtn.getBoundingClientRect();
        const emergencyRect = emergencyBtn.getBoundingClientRect();

        // 检查是否重叠
        if (this.isOverlapping(takeoffRect, emergencyRect)) {
            console.warn('检测到起飞按钮重叠，正在修复...');
            
            // 强制使用网格布局
            const container = takeoffBtn.closest('.takeoff-controls');
            if (container) {
                container.style.display = 'grid';
                container.style.gridTemplateColumns = this.currentOrientation === 'landscape' ? '1fr' : '1fr 1fr';
                container.style.gap = '16px';
            }
        }
    }

    /**
     * 防止相机控制按钮重叠
     */
    preventCameraButtonOverlap() {
        const photoBtn = document.querySelector('.photo-btn');
        const videoBtn = document.querySelector('.video-btn');
        
        if (!photoBtn || !videoBtn) return;

        const photoRect = photoBtn.getBoundingClientRect();
        const videoRect = videoBtn.getBoundingClientRect();

        if (this.isOverlapping(photoRect, videoRect)) {
            console.warn('检测到相机按钮重叠，正在修复...');
            
            const container = photoBtn.closest('.camera-controls');
            if (container) {
                container.style.justifyContent = 'space-around';
                container.style.gap = '24px';
                
                // 在小屏幕上垂直排列
                if (window.innerWidth < 768) {
                    container.style.flexDirection = 'column';
                    container.style.alignItems = 'center';
                }
            }
        }
    }

    /**
     * 防止参数滑块重叠
     */
    preventSliderOverlap() {
        const sliders = document.querySelectorAll('.parameter-slider');
        if (sliders.length < 2) return;

        const container = document.querySelector('.flight-parameters');
        if (!container) return;

        // 检查滑块是否重叠
        let hasOverlap = false;
        for (let i = 0; i < sliders.length - 1; i++) {
            const rect1 = sliders[i].getBoundingClientRect();
            const rect2 = sliders[i + 1].getBoundingClientRect();
            
            if (this.isOverlapping(rect1, rect2)) {
                hasOverlap = true;
                break;
            }
        }

        if (hasOverlap) {
            console.warn('检测到参数滑块重叠，正在修复...');
            
            // 强制垂直布局
            container.style.flexDirection = 'column';
            container.style.gap = '24px';
            
            // 为每个参数组添加间距
            const paramGroups = container.querySelectorAll('.parameter-group');
            paramGroups.forEach(group => {
                group.style.marginBottom = '20px';
            });
        }
    }

    /**
     * 检查两个矩形是否重叠
     */
    isOverlapping(rect1, rect2) {
        return !(rect1.right < rect2.left || 
                rect2.right < rect1.left || 
                rect1.bottom < rect2.top || 
                rect2.bottom < rect1.top);
    }

    /**
     * 重新计算按钮位置
     */
    recalculateButtonPositions() {
        // 强制重新渲染
        const controlPanel = document.querySelector('.drone-control-panel');
        if (controlPanel) {
            controlPanel.style.display = 'none';
            controlPanel.offsetHeight; // 触发重排
            controlPanel.style.display = '';
        }
    }

    /**
     * 调整触控目标大小
     */
    adjustTouchTargets() {
        const buttons = document.querySelectorAll('.takeoff-btn, .emergency-stop-btn, .photo-btn, .video-btn');
        const minTouchSize = 44; // iOS人机界面指南推荐的最小触控尺寸

        buttons.forEach(button => {
            const rect = button.getBoundingClientRect();
            if (rect.width < minTouchSize || rect.height < minTouchSize) {
                button.style.minWidth = `${minTouchSize}px`;
                button.style.minHeight = `${minTouchSize}px`;
            }
        });
    }

    /**
     * 设置无障碍支持
     */
    setupAccessibility() {
        // 为按钮添加ARIA标签
        const takeoffBtn = document.querySelector('.takeoff-btn');
        const emergencyBtn = document.querySelector('.emergency-stop-btn');
        const photoBtn = document.querySelector('.photo-btn');
        const videoBtn = document.querySelector('.video-btn');

        if (takeoffBtn) {
            takeoffBtn.setAttribute('aria-label', '无人机起飞');
            takeoffBtn.setAttribute('role', 'button');
        }
        
        if (emergencyBtn) {
            emergencyBtn.setAttribute('aria-label', '紧急停止');
            emergencyBtn.setAttribute('role', 'button');
        }
        
        if (photoBtn) {
            photoBtn.setAttribute('aria-label', '拍照');
            photoBtn.setAttribute('role', 'button');
        }
        
        if (videoBtn) {
            videoBtn.setAttribute('aria-label', '录像');
            videoBtn.setAttribute('role', 'button');
        }

        // 为滑块添加标签
        const sliders = document.querySelectorAll('.parameter-slider');
        sliders.forEach((slider, index) => {
            slider.setAttribute('role', 'slider');
            slider.setAttribute('aria-valuemin', '0');
            slider.setAttribute('aria-valuemax', '100');
            slider.setAttribute('aria-valuenow', slider.value || '50');
        });
    }

    /**
     * 按钮点击处理函数
     */
    handleTakeoffClick(event) {
        console.log('起飞按钮被点击');
        this.showFeedback(event.target, '起飞指令已发送');
    }

    handleEmergencyStopClick(event) {
        console.log('紧急停止按钮被点击');
        this.showFeedback(event.target, '紧急停止指令已发送');
    }

    handlePhotoClick(event) {
        console.log('拍照按钮被点击');
        this.showFeedback(event.target, '照片已拍摄');
    }

    handleVideoClick(event) {
        console.log('录像按钮被点击');
        this.showFeedback(event.target, '录像已开始');
    }

    handleSliderChange(event) {
        const slider = event.target;
        const value = slider.value;
        slider.setAttribute('aria-valuenow', value);
        
        // 更新显示值
        const valueDisplay = slider.parentNode.querySelector('.parameter-value');
        if (valueDisplay) {
            valueDisplay.textContent = value;
        }
    }

    handleTouchFeedback(event) {
        event.target.style.transform = 'scale(0.95)';
        setTimeout(() => {
            event.target.style.transform = '';
        }, 150);
    }

    /**
     * 显示操作反馈
     */
    showFeedback(element, message) {
        // 创建反馈提示
        const feedback = document.createElement('div');
        feedback.textContent = message;
        feedback.style.cssText = `
            position: absolute;
            background: rgba(0, 0, 0, 0.8);
            color: white;
            padding: 8px 12px;
            border-radius: 4px;
            font-size: 12px;
            z-index: 1000;
            pointer-events: none;
        `;
        
        document.body.appendChild(feedback);
        
        // 定位到按钮附近
        const rect = element.getBoundingClientRect();
        feedback.style.left = `${rect.left + rect.width / 2 - feedback.offsetWidth / 2}px`;
        feedback.style.top = `${rect.top - feedback.offsetHeight - 10}px`;
        
        // 自动移除
        setTimeout(() => {
            document.body.removeChild(feedback);
        }, 2000);
    }

    /**
     * 工具函数
     */
    getOrientation() {
        return window.innerWidth > window.innerHeight ? 'landscape' : 'portrait';
    }

    detectDeviceType() {
        const width = window.innerWidth;
        if (width < 768) return 'mobile';
        if (width < 1024) return 'tablet';
        return 'desktop';
    }

    detectTouchSupport() {
        return 'ontouchstart' in window || navigator.maxTouchPoints > 0;
    }

    getDeviceLayoutClass() {
        return `${this.deviceType}-${this.currentOrientation}`;
    }

    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }
}

// 当DOM加载完成后初始化
document.addEventListener('DOMContentLoaded', () => {
    window.droneControlManager = new DroneControlPanelManager();
});

// 导出类以供测试使用
if (typeof module !== 'undefined' && module.exports) {
    module.exports = DroneControlPanelManager;
}