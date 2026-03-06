<template>
	<div class="system-predict-container layout-padding">
		<div class="system-predict-padding layout-padding-auto layout-padding-view">
      <div class="detect-title-row">
        <div>
          <h3 class="detect-title">摄像检测</h3>
          <p class="detect-subtitle">开启摄像头后执行 YOLOv11 实时检测，结果与检测框同步展示</p>
        </div>
      </div>

      <el-card shadow="never" class="action-card">
        <div class="header action-row">
				<div class="conf" style="display: flex; flex-direction: row; align-items: center;">
					<div style="font-size: 14px; margin-right: 20px; color: #909399;">
						设置最小置信度阈值
					</div>
					<el-slider 
						v-model="conf" 
						:format-tooltip="formatTooltip" 
						style="width: 280px;" 
						:min="0" 
						:max="100" 
						:step="1" 
					/>
				</div>
				<div class="button-section" style="margin-left: 20px">
					<el-button 
						type="primary" 
						@click="handleStartCamera" 
						class="predict-button" 
						:disabled="isCameraActive || isStopping"
					>
						{{ isCameraActive ? '检测中' : '开启摄像头检测' }}
					</el-button>
				</div>
                <div class="button-section" style="margin-left: 20px">
					<el-button 
						type="warning" 
						@click="handleStopCamera" 
						class="predict-button" 
						:disabled="!isCameraActive || isStopping"
					>
						关闭摄像头检测
					</el-button>
				</div>
				<div class="demo-progress" v-if="isProcessing">
					<el-progress 
						:text-inside="true" 
						:stroke-width="20" 
						:percentage="progressPercentage" 
						style="width: 380px; margin-left: 20px;"
					>
						<span>{{ progressText }} {{ progressPercentage }}%</span>
					</el-progress>
				</div>
        </div>
      </el-card>
			<div class="cards" ref="cardsContainer">
				<!-- 使用img标签显示MJPEG流，绑定ref和加载事件 -->
				<img 
					v-if="isCameraActive && cameraStreamUrl" 
					class="video-stream" 
					:src="cameraStreamUrl" 
					alt="杂草检测摄像头实时流"
					ref="cameraStreamImgRef"
					@error="handleStreamError"
					@load="handleStreamLoad"
					@abort="handleStreamAbort"
				/>
				<div v-else class="empty-tip">
					<el-icon class="empty-icon"><VideoCamera /></el-icon>
					<div>请点击「开启摄像头检测」启动实时杂草检测</div>
					<div class="empty-sub">摄像头检测不会自动录制，仅实时预览</div>
				</div>
			</div>
			
			<!-- 状态提示 -->
			<el-alert
				v-if="cameraStatusMessage"
				:title="cameraStatusMessage"
				:type="cameraStatusType"
				show-icon
				closable
				@close="cameraStatusMessage = ''"
				style="margin-top: 15px;"
			/>
		</div>
	</div>
</template>

<script setup lang="ts">
import { ref, onMounted, onActivated, onDeactivated, onUnmounted, watch } from 'vue';
import { ElMessage, ElMessageBox } from 'element-plus';
import { VideoCamera } from '@element-plus/icons-vue';
import request from '@/utils/request';
import { useUserInfo } from '@/utils/stores/userInfo';
import { storeToRefs } from 'pinia';
import { formatDate } from '@/utils/formatTime';

// ============================ 类型定义 ============================
type CameraStatusType = 'success' | 'info' | 'warning' | 'error';
interface FormData {
  username: string;
  conf: number;
  startTime: string;
}

// ============================ 状态管理 ============================
// 置信度阈值(0-100)
const conf = ref<number>(50);
// 摄像头状态
const isCameraActive = ref<boolean>(false);      // 摄像头是否激活
const isStopping = ref<boolean>(false);          // 是否正在停止操作
const isProcessing = ref<boolean>(false);        // 是否在处理中
// 进度条相关
const progressPercentage = ref<number>(0);       // 进度百分比
const progressText = ref<string>("正在处理视频");
// 摄像头流相关
const cameraStreamUrl = ref<string>('');         // 摄像头流URL
const cameraStreamImgRef = ref<HTMLImageElement | null>(null); // 视频流img元素引用
// 提示消息相关
const cameraStatusMessage = ref<string>('');     // 状态消息
const cameraStatusType = ref<CameraStatusType>('info'); // 状态类型

// ============================ 用户信息与环境 ============================
const userStore = useUserInfo();
const { userInfos } = storeToRefs(userStore);
// 防抖标识
let isRequesting = ref<boolean>(false);

const runOptionalGC = (): void => {
  const maybeGc = (window as Window & { gc?: () => void }).gc;
  if (typeof maybeGc === 'function') {
    maybeGc();
  }
};

// ============================ 表单数据 ============================
const formData = ref<FormData>({
  username: userInfos.value?.userName || 'default_user',
  conf: conf.value / 100,
  startTime: ''
});

// ============================ 工具方法 ============================
/**
 * 格式化置信度滑块提示文本
 * @param val 滑块值(0-100)
 * @returns 格式化后的值(0-1)
 */
const formatTooltip = (val: number): number => val / 100;

/**
 * 重置摄像头所有状态
 */
const resetCameraState = (): void => {
  // 清除视频流URL
  cameraStreamUrl.value = '';
  
  // 重置状态变量
  isCameraActive.value = false;
  isStopping.value = false;
  isProcessing.value = false;
  progressPercentage.value = 0;
  isRequesting.value = false;
  
  // 释放img元素资源
  if (cameraStreamImgRef.value) {
    cameraStreamImgRef.value.src = '';
    cameraStreamImgRef.value.removeAttribute('src');
    cameraStreamImgRef.value = null;
  }
  
  // 提示垃圾回收
  runOptionalGC();
};

// ============================ 权限检查 ============================
/**
 * 检查摄像头权限
 * @returns 是否有权限
 */
const checkCameraPermission = async (): Promise<boolean> => {
  // 在HTTPS环境下，浏览器支持摄像头API
  if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
    // 如果是HTTPS环境但浏览器不支持，可能是过时浏览器
    if (window.location.protocol === 'https:') {
      cameraStatusMessage.value = '当前浏览器版本过旧，请更新浏览器或使用Chrome/Edge最新版';
      cameraStatusType.value = 'error';
    } else {
      cameraStatusMessage.value = '请使用HTTPS访问以获取摄像头权限';
      cameraStatusType.value = 'warning';
    }
    return false;
  }

  try {
    // 测试摄像头权限（仅测试，不真正打开流）
    const stream = await navigator.mediaDevices.getUserMedia({ 
      video: { 
        width: { ideal: 640 }, 
        height: { ideal: 480 },
        facingMode: 'environment' // 优先使用后置摄像头
      } 
    });
    
    // 立即释放测试流
    stream.getTracks().forEach(track => {
      track.stop();
      track.removeEventListener('ended', () => {});
    });
    
    return true;
  } catch (error: any) {
    console.error('摄像头权限检查失败:', error);
    
    // 更友好的错误提示
    if (error.name === 'NotAllowedError') {
      cameraStatusMessage.value = '摄像头权限被拒绝，请点击地址栏的摄像头图标并选择"允许"';
    } else if (error.name === 'NotFoundError') {
      cameraStatusMessage.value = '未检测到可用的摄像头设备，请检查硬件连接';
    } else if (error.name === 'NotReadableError') {
      cameraStatusMessage.value = '摄像头被其他应用占用，请关闭其他使用摄像头的应用';
    } else if (error.name === 'OverconstrainedError') {
      cameraStatusMessage.value = '摄像头参数不匹配，请尝试使用其他分辨率';
    } else {
      cameraStatusMessage.value = `摄像头访问失败: ${error.message || '未知错误'}`;
    }
    
    cameraStatusType.value = 'error';
    
    // 提供解决方案
    if (error.name === 'NotAllowedError') {
      setTimeout(() => {
        ElMessageBox.confirm(
          '摄像头权限被拒绝，请按以下步骤操作：\n\n' +
          '1. 点击地址栏左侧的摄像头图标\n' +
          '2. 选择"始终允许"或"允许"\n' +
          '3. 刷新页面后重试\n\n' +
          '需要帮助吗？',
          '摄像头权限设置',
          {
            confirmButtonText: '已设置权限，重试',
            cancelButtonText: '取消',
            type: 'warning'
          }
        ).then(() => {
          window.location.reload();
        });
      }, 1500);
    }
    
    return false;
  }
};

// ============================ 摄像头操作 ============================
/**
 * 处理开启摄像头检测（防抖包装）
 */
const handleStartCamera = async (): Promise<void> => {
  // 防抖：避免重复请求
  if (isRequesting.value || isCameraActive.value) {
    ElMessage.warning(isCameraActive.value ? '摄像头检测已在运行中' : '操作中，请稍候');
    return;
  }

  isRequesting.value = true;
  
  try {
    await startCamera();
  } finally {
    isRequesting.value = false;
  }
};

/**
 * 开启摄像头检测核心逻辑
 */
// 修改 startCamera 函数中的URL生成部分
const startCamera = async (): Promise<void> => {
  // 1. 检查摄像头权限（HTTPS环境下可用）
  const hasPermission = await checkCameraPermission();
  if (!hasPermission) return;
  
  // 2. 校验置信度阈值
  if (isNaN(conf.value) || conf.value < 0 || conf.value > 100) {
    ElMessage.warning("请设置0-100之间的有效置信度阈值！");
    return;
  }
  
  try {
    // 3. 更新状态
    isCameraActive.value = true;
    isProcessing.value = false;
    progressPercentage.value = 0;
    
    // 4. 组装请求参数
    formData.value = {
      username: userInfos.value?.userName || 'default_user',
      conf: conf.value / 100,
      startTime: formatDate(new Date(), 'YYYY-MM-DD HH:mm:ss')
    };
    
    // 5. 构建MJPEG流URL
    const queryParams = new URLSearchParams({
      username: formData.value.username,
      conf: formData.value.conf.toString(),
      startTime: formData.value.startTime,
      t: Date.now().toString()
    }).toString();
    
    // 🔥 关键修改：使用相对路径，通过Vite代理
    cameraStreamUrl.value = `/predictCamera?${queryParams}`;
    
    // 6. 提示用户
    ElMessage.success('摄像头检测已开启');
    cameraStatusMessage.value = '摄像头检测已启动，正在实时检测杂草...';
    cameraStatusType.value = 'success';
    
  } catch (error: any) {
    console.error('开启摄像头检测失败:', error);
    ElMessage.error('开启摄像头检测失败');
    cameraStatusMessage.value = `开启失败：${error.message || '请检查Flask服务是否正常运行'}`;
    cameraStatusType.value = 'error';
    resetCameraState();
  }
};
/**
 * 处理关闭摄像头检测（防抖包装）
 */
const handleStopCamera = async (): Promise<void> => {
  if (isStopping.value || !isCameraActive.value) {
    ElMessage.warning(isStopping.value ? '正在停止中，请稍候' : '摄像头检测未运行');
    return;
  }

  try {
    await stopCamera();
  } catch (error) {
    console.error('停止摄像头异常:', error);
    resetCameraState();
    ElMessage.error('停止摄像头检测失败');
  }
};

/**
 * 关闭摄像头检测核心逻辑
 */

const stopCamera = async (): Promise<void> => {
  isStopping.value = true;
  
  try {
    // 1. 确认停止操作
    await ElMessageBox.confirm(
      '确定要停止摄像头检测吗？',
      '操作确认',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
        closeOnClickModal: false,
      }
    );
    
    // 2. 先本地停止流显示
    resetCameraState();
    
    // 3. 发送停止请求到后端（尝试多个路径）
    let stopSuccess = false;
    const stopPaths = ['/flask/stopCamera', '/stopCamera'];
    
    for (const path of stopPaths) {
      try {
        console.log(`尝试停止摄像头路径: ${path}`);
        const response = await request.get(path, {
          timeout: 3000
        });
        
        if (response.code === 0 || response.status === 200) {
          stopSuccess = true;
          console.log(`摄像头停止成功: ${path}`);
          break;
        }
      } catch (requestError: any) {
        console.warn(`路径 ${path} 停止失败:`, requestError);
        // 继续尝试下一个路径
      }
    }
    
    // 4. 反馈结果
    if (stopSuccess) {
      ElMessage.success('摄像头检测已停止');
      cameraStatusMessage.value = '摄像头检测已停止，资源已释放';
      cameraStatusType.value = 'success';
    } else {
      ElMessage.warning('后端停止请求失败，已本地停止摄像头显示');
      cameraStatusMessage.value = '摄像头显示已停止（后端连接异常，请检查服务状态）';
      cameraStatusType.value = 'warning';
    }
    
    // 5. 延迟清理
    setTimeout(() => {
      // 确保状态完全重置
      resetCameraState();
      // 清理内存
      runOptionalGC();
    }, 500);
    
  } catch (error: any) {
    // 用户取消操作
    if (error === 'cancel' || error === 'close') {
      ElMessage.info('已取消停止操作');
      isStopping.value = false;
      return;
    }
    
    // 其他错误
    console.error('停止摄像头检测异常:', error);
    ElMessage.error('停止摄像头检测失败');
    
    // 强制重置状态
    resetCameraState();
  }
};

// ============================ 流处理 ============================
/**
 * 处理视频流加载错误
 * @param error 错误事件
 */
const handleStreamError = (error: Event): void => {
  console.error('摄像头流加载失败:', error);
  
  if (isCameraActive.value) {
    cameraStatusMessage.value = '摄像头流加载失败，可能原因：\n1. Flask服务未启动\n2. 摄像头被其他应用占用\n3. 网络连接异常';
    cameraStatusType.value = 'error';
    
    // 自动重置状态
    setTimeout(() => {
      resetCameraState();
    }, 3000);
  }
};

/**
 * 处理视频流加载成功
 */
const handleStreamLoad = (): void => {
  console.log('摄像头流加载成功');
  cameraStatusMessage.value = '摄像头流已连接，正在实时检测杂草（置信度阈值：' + conf.value + '%）';
  cameraStatusType.value = 'success';
};

/**
 * 处理视频流加载中断
 */
const handleStreamAbort = (): void => {
  console.warn('摄像头流加载被中断');
  if (isCameraActive.value) {
    cameraStatusMessage.value = '摄像头流连接被中断';
    cameraStatusType.value = 'warning';
  }
};

// ============================ 后端连接检查 ============================
/**
 * 检查Flask后端连接状态
 */
const checkFlaskConnection = async (): Promise<void> => {
  try {
    const response = await request.get('/flask/test', {
      timeout: 3000 // 3秒超时
    });
    console.log('Flask连接正常:', response);
  } catch (error) {
    console.error('Flask连接失败:', error);
    ElMessage.warning('Flask服务未启动或连接异常，部分功能可能无法使用');
    cameraStatusMessage.value = 'Flask服务未启动，请先启动后端服务再进行检测';
    cameraStatusType.value = 'warning';
  }
};

// ============================ 生命周期 ============================
/**
 * 页面挂载时初始化
 */
onMounted(async () => {
  // 初始化表单数据
  formData.value = {
    username: userInfos.value?.userName || 'default_user',
    conf: conf.value / 100,
    startTime: ''
  };
  
  // 检查Flask连接
  await checkFlaskConnection();
});

/**
 * 页面激活时重置状态（如路由切换回来）
 */
onActivated(() => {
  console.log('摄像头检测页面激活 - 重置状态');
  
  // 强制重置所有状态
  resetCameraState();
  
  // 重新初始化表单数据
  formData.value = {
    username: userInfos.value?.userName || 'default_user',
    conf: conf.value / 100,
    startTime: ''
  };
  
  // 清除状态消息
  cameraStatusMessage.value = '';
});

/**
 * 页面失活时清理资源（如路由切换离开）
 */
onDeactivated(async () => {
  console.log('摄像头检测页面失活 - 清理资源');
  
  // 如果摄像头正在运行，强制停止
  if (isCameraActive.value) {
    console.log('强制停止摄像头检测');
    
    // 发送停止请求（不等待响应）
    try {
      await request.get('/flask/stopCamera', { timeout: 2000 });
    } catch (error) {
      console.warn('停止请求失败，继续清理本地资源');
    }
    
    // 立即重置状态
    resetCameraState();
    ElMessage.info('摄像头检测已自动停止（页面已离开）');
  }
  
  // 清理缓存
  if ('caches' in window) {
    try {
      const cacheNames = await caches.keys();
      await Promise.all(
        cacheNames.filter(name => name.includes('image')).map(name => caches.delete(name))
      );
    } catch (cacheError) {
      console.warn('清理缓存失败:', cacheError);
    }
  }
});

/**
 * 页面卸载时最终清理
 */
onUnmounted(() => {
  console.log('摄像头检测页面卸载 - 最终清理');
  resetCameraState();
});

// ============================ 监听置信度变化 ============================
// 监听置信度变化，实时更新表单数据
watch(conf, () => {
  formData.value.conf = conf.value / 100;
});
</script>

<style scoped lang="scss">
.system-predict-container {
  width: 100%;
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);

  .system-predict-padding {
    padding: 15px;
    height: 100%;
    display: flex;
    flex-direction: column;
  }
}

.detect-title-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;

  .detect-title {
    margin: 0;
    font-size: 20px;
    color: #1f2937;
  }

  .detect-subtitle {
    margin: 6px 0 0;
    color: #64748b;
    font-size: 14px;
  }
}

.action-card {
  margin-bottom: 12px;
  border-radius: 12px;
}

.header {
  width: 100%;
  display: flex;
  justify-content: flex-start;
  align-items: center;
  font-size: 20px;
  flex-wrap: wrap;
  gap: 15px;
  padding: 15px;
  border-bottom: 2px solid #e5e7eb;
  margin-bottom: 20px;
  background: white;
  border-radius: 10px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.cards {
  width: 100%;
  flex: 1;
  border-radius: 12px;
  padding: 20px;
  overflow: hidden;
  display: flex;
  justify-content: center;
  align-items: center;
  background: white;
  position: relative;
  min-height: 500px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);

  .empty-tip {
    color: #606266;
    font-size: 18px;
    text-align: center;
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 15px;
    
    .empty-icon {
      font-size: 64px;
      color: #c0c4cc;
      margin-bottom: 10px;
    }
    
    .empty-sub {
      font-size: 14px;
      color: #909399;
      margin-top: 5px;
    }
  }
}

.video-stream {
  width: 100%;
  max-height: 75vh;
  height: auto;
  object-fit: contain;
  border-radius: 8px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
  border: 2px solid #409eff;
  background: #000;
  transition: all 0.3s ease;
}

// 流加载中的骨架屏效果
.video-stream[src=""] {
  background: linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%);
  background-size: 200% 100%;
  animation: loading 1.5s infinite;
}

@keyframes loading {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}

.button-section {
  display: flex;
  justify-content: center;
  min-width: 180px;
  
  .predict-button {
    width: 100%;
    padding: 10px 20px;
    font-size: 14px;
    border-radius: 6px;
    transition: all 0.3s ease;
    
    &:hover:not(:disabled) {
      transform: translateY(-2px);
      box-shadow: 0 4px 12px rgba(64, 158, 255, 0.3);
    }
    
    &:disabled {
      opacity: 0.6;
      cursor: not-allowed;
      transform: none;
      box-shadow: none;
    }
  }
}

.demo-progress {
  min-width: 300px;
  background: white;
  padding: 10px;
  border-radius: 6px;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.1);
}

// 响应式适配
@media (max-width: 1400px) {
  .header {
    gap: 12px;
  }
  
  .demo-progress {
    width: 100%;
    margin-left: 0 !important;
    min-width: unset;
  }
  
  .button-section {
    min-width: 160px;
  }
}

@media (max-width: 992px) {
  .header {
    flex-direction: column;
    align-items: stretch;
    gap: 15px;
  }
  
  .conf {
    width: 100%;
    justify-content: space-between;
  }
  
  .el-slider {
    width: 100% !important;
  }
  
  .button-section {
    width: 100%;
    margin-left: 0 !important;
    min-width: unset;
  }
  
  .cards {
    min-height: 400px;
    padding: 15px;
  }
  
  .video-stream {
    max-height: 65vh;
  }
}

@media (max-width: 768px) {
  .system-predict-padding {
    padding: 10px;
  }
  
  .cards {
    min-height: 350px;
    padding: 10px;
    
    .empty-tip {
      font-size: 16px;
      
      .empty-icon {
        font-size: 48px;
      }
    }
  }
  
  .video-stream {
    max-height: 60vh;
  }
}

// 移动端优化
@media (max-width: 480px) {
  .header {
    padding: 10px;
  }
  
  .cards {
    min-height: 300px;
    padding: 5px;
  }
  
  .empty-tip {
    font-size: 14px !important;
  }
  
  .empty-icon {
    font-size: 40px !important;
  }
}
</style>
