<template>
	<div class="system-predict-container layout-padding">
		<div class="system-predict-padding layout-padding-auto layout-padding-view">
			<div class="header">
				<div class="conf" style="display: flex; flex-direction: row; align-items: center;">
					<div
						style="font-size: 14px;margin-right: 20px;display: flex;justify-content: start;align-items: center;color: #909399;">
						设置最小置信度阈值
					</div>
					<el-slider v-model="conf" :format-tooltip="formatTooltip" style="width: 280px;" 
					  :min="0" :max="100" :step="1" />
				</div>
				<el-upload v-model="state.form.inputVideo" ref="uploadFile" class="avatar-uploader"
					:action="uploadAction" :show-file-list="false" :on-success="handleAvatarSuccessone"
					:disabled="state.isDetecting" :before-upload="beforeUpload">
					<div class="button-section" style="margin-left: 20px">
						<el-button type="info" class="predict-button" :disabled="state.isDetecting">上传杂草检测视频</el-button>
					</div>
				</el-upload>
				<div class="button-section" style="margin-left: 20px">
					<el-button type="primary" @click="upData" class="predict-button" :disabled="!state.form.inputVideo || state.isDetecting">
						{{ state.isDetecting ? '正在检测中' : '开始杂草检测' }}
					</el-button>
				</div>
				<div class="demo-progress" v-if="state.isShow">
					<el-progress :text-inside="true" :stroke-width="20" :percentage="state.percentage" style="width: 380px;">
						<span>{{ state.type_text }} {{ state.percentage }}%</span>
					</el-progress>
				</div>
			</div>
			<div class="cards" ref="cardsContainer">
				<!-- 关键修改1：调整视频播放器显示逻辑 -->
				<template v-if="state.video_path">
					<video 
						v-show="isVideoActive"
						ref="videoPlayer"
						class="video" 
						:src="state.video_path" 
						controls 
						autoplay 
						muted 
						loop 
						alt="杂草检测视频结果"
						@loadedmetadata="onVideoLoaded"
						@error="onVideoError"
						@canplay="onVideoCanPlay"
					></video>
					<div v-if="!isVideoActive && state.video_path" class="loading-tip">
						<el-icon class="loading-icon"><Loading /></el-icon>
						<div>视频加载中...</div>
					</div>
				</template>
				<div v-else class="empty-tip">
					<el-icon class="empty-icon"><VideoCamera /></el-icon>
					<div>请上传视频并点击「开始杂草检测」查看结果</div>
					<div class="empty-sub">支持MP4、AVI等常见视频格式</div>
				</div>
			</div>
			
			<el-alert
				v-if="statusMessage"
				:title="statusMessage"
				:type="statusType"
				show-icon
				closable
				@close="statusMessage = ''"
				style="margin-top: 15px;"
			/>
			
			<!-- 调试信息面板（仅在开发环境显示） -->
			<div v-if="showDebugInfo" class="debug-panel">
				<el-collapse>
					<el-collapse-item title="调试信息">
						<div class="debug-content">
							<p><strong>视频路径:</strong> {{ state.video_path || '无' }}</p>
							<p><strong>视频状态:</strong> {{ isVideoActive ? '已激活' : '未激活' }}</p>
							<p><strong>检测状态:</strong> {{ state.isDetecting ? '进行中' : '未进行' }}</p>
							<p><strong>进度:</strong> {{ state.percentage }}%</p>
							<p><strong>Socket连接:</strong> {{ socketService.isConnected ? '已连接' : '未连接' }}</p>
							<el-button size="small" @click="testVideoAccess" type="primary">测试视频访问</el-button>
						</div>
					</el-collapse-item>
				</el-collapse>
			</div>
		</div>
	</div>
</template>

<script setup lang="ts">
import { reactive, ref, onMounted, onActivated, onDeactivated, onUnmounted } from 'vue';
import { ElMessage } from 'element-plus';
import { VideoCamera, Loading } from '@element-plus/icons-vue';
import request from '/@/utils/request';
import { useUserInfo } from '/@/stores/userInfo';
import { storeToRefs } from 'pinia';
import type { UploadInstance, UploadProps } from 'element-plus';
import { socketService } from '/@/utils/socket';

// 核心变量定义
const uploadFile = ref<UploadInstance>();
const conf = ref(50);
const stores = useUserInfo();
const { userInfos } = storeToRefs(stores);
const videoPlayer = ref<HTMLVideoElement | null>(null);

// 状态管理
const isVideoActive = ref(false);
const statusMessage = ref('');
const statusType = ref('info');
const videoLoadAttempts = ref(0);
const showDebugInfo = ref(false); // 调试面板开关

// 使用Flask统一处理所有后端服务
const uploadAction = ref('/upload');
const flaskPredictUrl = ref('/predictVideo');

const state = reactive({
	video_path: '',
	type_text: "正在处理杂草检测视频",
	percentage: 0,
	isShow: false,
	isDetecting: false,
	form: {
		username: '',
		inputVideo: null as any,
		conf: 0.5,
		startTime: ''
	},
});

// 关键修改2：修复WebSocket视频结果监听
const initSocketListener = () => {
	try {
		// 使用新的off方法移除原有监听器
		if (typeof socketService.off === 'function') {
			socketService.off('message');
			socketService.off('progress');
			socketService.off('error');
			socketService.off('video_result');
		} else {
			console.warn('socketService.off 方法不存在，跳过移除监听器');
		}

		// Socket普通消息监听
		socketService.on('message', (data) => {
			console.log('Socket接收消息:', data);
			const msg = typeof data === 'object' ? (data.data || JSON.stringify(data)) : data;
			if (msg && !msg.includes('Connected')) {
				ElMessage.success(msg);
			}
		});

		// 进度条监听
		socketService.on('progress', (data) => {
			// 兼容后端直接传数字或对象格式
			let progress = 0;
			if (typeof data === 'object') {
				progress = data.percentage || data.data || 0;
			} else {
				progress = parseInt(data) || 0;
			}
			
			// 确保进度在0-100范围内
			progress = Math.max(0, Math.min(100, progress));
			
			state.percentage = progress;
			state.isShow = true;
			console.log('视频处理进度:', state.percentage);

			// 处理完成逻辑
			if (state.percentage >= 100) {
				ElMessage.success("杂草检测视频处理完成！");
				setTimeout(() => {
					state.isShow = false;
					state.percentage = 0;
					state.isDetecting = false;
					statusMessage.value = '视频检测完成，可以播放结果';
					statusType.value = 'success';
				}, 2000);
			}
		});

		// 关键修改3：修复视频结果监听，构建正确的视频URL
		socketService.on('video_result', (data) => {
			let resultVideo = '';
			if (typeof data === 'object') {
				resultVideo = data.video_path || data.data || '';
			} else {
				resultVideo = data;
			}
			if (resultVideo) {
				// 只用相对路径，避免拼接 http://192.168.0.101:5000
				let videoUrl = resultVideo;
				// 添加时间戳防止缓存
				const url = new URL(videoUrl, window.location.origin);
				url.searchParams.set('t', Date.now().toString());
				state.video_path = url.toString();
				videoLoadAttempts.value = 0;
				// 强制触发视频播放器重新加载
				isVideoActive.value = false;
				// 给视频一点时间加载
				setTimeout(() => {
					if (videoPlayer.value) {
						videoPlayer.value.src = state.video_path;
						videoPlayer.value.load();
					}
				}, 100);
				ElMessage.success('检测结果视频已生成，正在加载...');
				statusMessage.value = '视频已生成，正在加载中...';
				statusType.value = 'info';
			}
		});

		// Socket错误监听
		socketService.on('error', (err) => {
			console.error('Socket连接错误:', err);
			ElMessage.error('实时进度通知连接失败，进度条将无法更新！');
			state.isDetecting = false;
			statusMessage.value = '实时通知连接失败，但视频检测仍在进行';
			statusType.value = 'warning';
		});
		
		// 连接成功监听
		socketService.on('connect', () => {
			console.log('Socket连接成功');
			ElMessage.success('实时进度连接已建立');
		});
		
	} catch (error) {
		console.error('初始化Socket监听器失败:', error);
		ElMessage.warning('Socket监听器初始化失败，但可以继续使用');
	}
};

// 置信度滑块格式化
const formatTooltip = (val: number) => {
	return (val / 100).toFixed(2);
};

// 上传前验证
const beforeUpload = (file: File) => {
	// 检查文件类型
	const allowedTypes = ['video/mp4', 'video/avi', 'video/mpeg', 'video/quicktime', 'video/x-msvideo'];
	const isVideo = allowedTypes.some(type => file.type.startsWith('video/') || allowedTypes.includes(file.type));
	
	// 通过文件扩展名二次验证
	const fileExt = file.name.toLowerCase().split('.').pop();
	const allowedExts = ['mp4', 'avi', 'mov', 'mkv', 'flv', 'wmv', 'm4v'];
	const hasValidExt = fileExt && allowedExts.includes(fileExt);
	
	if (!isVideo && !hasValidExt) {
		ElMessage.error('只能上传视频文件（MP4、AVI、MOV、MKV等格式）！');
		return false;
	}
	
	// 检查文件大小（限制100MB）
	const isLt100M = file.size / 1024 / 1024 < 100;
	if (!isLt100M) {
		ElMessage.error('视频大小不能超过100MB！');
		return false;
	}
	
	return true;
};

// 视频上传成功回调
const handleAvatarSuccessone: UploadProps['onSuccess'] = (response, uploadFile) => {
	// 停止当前视频播放
	stopVideoPlayback();
	
	// 上传新视频，清空之前的检测结果
	state.video_path = '';
	isVideoActive.value = false;
	state.percentage = 0;
	state.isShow = false;
	
	// 核心修复：直接使用Flask返回的相对路径
	if (response && response.data) {
		state.form.inputVideo = response.data;
		ElMessage.success('杂草检测视频上传成功！');
		statusMessage.value = '视频上传成功，请点击开始检测';
		statusType.value = 'success';
	} else {
		ElMessage.error('上传响应格式错误，请重试');
		statusMessage.value = '上传失败，服务器响应格式错误';
		statusType.value = 'error';
	}
};

// 停止视频播放
const stopVideoPlayback = () => {
	if (videoPlayer.value) {
		videoPlayer.value.pause();
		videoPlayer.value.src = '';
		videoPlayer.value.load();
	}
	isVideoActive.value = false;
};

// 视频加载完成
const onVideoLoaded = () => {
	console.log('视频加载完成');
	isVideoActive.value = true;
	videoLoadAttempts.value = 0;
	statusMessage.value = '视频加载完成，可以开始播放';
	statusType.value = 'success';
};

// 视频可以播放时触发
const onVideoCanPlay = () => {
	console.log('视频可以播放');
	isVideoActive.value = true;
};

// 视频加载错误
const onVideoError = (error: Event) => {
	console.error('视频加载失败:', error);
	videoLoadAttempts.value++;
	
	if (videoLoadAttempts.value <= 3) {
		// 重试加载
		setTimeout(() => {
			if (videoPlayer.value && state.video_path) {
				const url = new URL(state.video_path);
				url.searchParams.set('retry', videoLoadAttempts.value.toString());
				videoPlayer.value.src = url.toString();
				videoPlayer.value.load();
			}
		}, 1000 * videoLoadAttempts.value);
	} else {
		statusMessage.value = '视频加载失败，请检查Flask服务或重新检测';
		statusType.value = 'error';
		isVideoActive.value = false;
		state.isDetecting = false;
	}
};

// 修复时间格式函数 - 确保返回正确的格式
const formatDateTime = (): string => {
	try {
		const now = new Date();
		
		// 直接使用Date方法，确保月份正确（getMonth()返回0-11）
		const year = now.getFullYear();
		const month = String(now.getMonth() + 1).padStart(2, '0');
		const day = String(now.getDate()).padStart(2, '0');
		const hours = String(now.getHours()).padStart(2, '0');
		const minutes = String(now.getMinutes()).padStart(2, '0');
		const seconds = String(now.getSeconds()).padStart(2, '0');
		
		const result = `${year}-${month}-${day} ${hours}:${minutes}:${seconds}`;
		return result;
	} catch (error) {
		console.error('时间格式化错误:', error);
		// 返回当前时间的简单格式作为后备
		const now = new Date();
		return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}-${String(now.getDate()).padStart(2, '0')} ${String(now.getHours()).padStart(2, '0')}:${String(now.getMinutes()).padStart(2, '0')}:${String(now.getSeconds()).padStart(2, '0')}`;
	}
};

// 开始杂草检测
const upData = async () => {
	// 多重参数校验
	if (state.isDetecting) {
		ElMessage.warning('正在处理视频，请勿重复点击！');
		return;
	}
	
	if (!state.form.inputVideo) {
		ElMessage.warning('请先上传杂草检测视频！');
		return;
	}
	
	if (isNaN(Number(conf.value)) || conf.value < 0 || conf.value > 100) {
		ElMessage.warning('请设置0-100之间的有效置信度阈值！');
		return;
	}
	
	try {
		// 组装请求参数
		state.isDetecting = true;
		state.form.conf = parseFloat((conf.value / 100).toFixed(2));
		state.form.username = userInfos.value.userName || 'default_user';
		
		// 使用修复的时间格式函数
		state.form.startTime = formatDateTime();
		console.log('开始视频检测，参数:', JSON.stringify(state.form));
		
		// 停止当前视频播放并清空路径
		stopVideoPlayback();
		state.video_path = '';
		isVideoActive.value = false;

		// 确保Socket已连接
		if (!socketService.isConnected) {
			try {
				socketService.connect();
				// 等待连接建立
				await new Promise(resolve => setTimeout(resolve, 1500));
				ElMessage.info('已建立实时进度连接');
			} catch (error) {
				console.warn('Socket连接失败，将继续检测但不显示进度:', error);
				ElMessage.warning('实时进度连接失败，但视频检测将继续进行');
			}
		}

		// 通过Socket发送处理指令，触发后端视频检测
		socketService.emit('process_video', state.form);
		console.log('已发送process_video指令');
		
		// 显示进度条
		state.isShow = true;
		state.percentage = 0;
		
		ElMessage.info('开始处理杂草检测视频，请稍候...');
		statusMessage.value = '正在处理视频检测，请等待进度完成';
		statusType.value = 'info';
		
		// 设置超时保护
		setTimeout(() => {
			if (state.isDetecting && state.percentage < 100) {
				ElMessage.warning('检测时间较长，请耐心等待...');
			}
		}, 15000);
		
		// 设置超时检查，查看是否收到视频结果
		setTimeout(() => {
			if (!state.video_path && state.isDetecting) {
				console.warn('视频检测超时，未收到结果');
				ElMessage.warning('视频检测时间较长，请稍候...');
			}
		}, 30000);
		
	} catch (error) {
		console.error('开始视频检测失败:', error);
		ElMessage.error(`开始视频检测失败: ${error instanceof Error ? error.message : '未知错误'}`);
		statusMessage.value = '开始视频检测失败，请重试';
		statusType.value = 'error';
		state.isDetecting = false;
		state.isShow = false;
	}
};

// 测试视频访问功能
const testVideoAccess = async () => {
	if (!state.video_path) {
		ElMessage.warning('请先完成视频检测');
		return;
	}
	
	try {
		const response = await fetch(state.video_path, { method: 'HEAD' });
		if (response.ok) {
			ElMessage.success('视频文件可正常访问');
		} else {
			ElMessage.error(`视频访问失败: ${response.status} ${response.statusText}`);
		}
	} catch (error) {
		ElMessage.error(`视频访问失败: ${error}`);
	}
};

// 重置页面状态
const resetPageState = () => {
	// 停止视频播放
	stopVideoPlayback();
	
	// 重置状态
	state.video_path = '';
	state.percentage = 0;
	state.isShow = false;
	state.isDetecting = false;
	state.form.inputVideo = null;
	isVideoActive.value = false;
	statusMessage.value = '';
	videoLoadAttempts.value = 0;
	
	// 清空上传组件的文件
	if (uploadFile.value) {
		uploadFile.value.clearFiles();
	}
	
	console.log('视频检测页面状态已重置');
};

// 检查Flask连接状态
const checkFlaskConnection = async () => {
	try {
		const response = await request.get('/flask/test');
		if (response && response.status === 200) {
			console.log('Flask连接正常:', response);
			statusMessage.value = 'Flask服务连接正常，可以开始检测';
			statusType.value = 'success';
			return true;
		} else {
			statusMessage.value = 'Flask服务异常，请检查后重试';
			statusType.value = 'warning';
			return false;
		}
	} catch (error) {
		console.error('Flask连接失败:', error);
		ElMessage.error('Flask服务未启动，请确保已启动Flask后端服务');
		statusMessage.value = 'Flask服务未启动，无法进行视频检测';
		statusType.value = 'error';
		return false;
	}
};

// 页面激活时：重置状态
onActivated(() => {
	console.log('视频检测页面激活');
	resetPageState();
	state.form.conf = parseFloat((conf.value / 100).toFixed(2));
});

// 页面失活时：销毁资源
onDeactivated(() => {
	console.log('视频检测页面失活');
	resetPageState();
});

// 页面卸载时：最终资源清理
onUnmounted(() => {
	console.log('视频检测页面卸载');
	resetPageState();
	// 断开Socket连接
	socketService.disconnect();
});

// 页面挂载初始化
onMounted(async () => {
	// 初始化置信度
	state.form.conf = parseFloat((conf.value / 100).toFixed(2));
	
	// 初始化Socket监听
	initSocketListener();
	
	// 检查Flask服务是否可用
	const isConnected = await checkFlaskConnection();
	if (isConnected) {
		console.log('Flask检测服务准备就绪');
	} else {
		ElMessage.warning('请确保Flask服务正在运行 (端口5000)');
	}
	
	// 开发环境下显示调试面板
	if (import.meta.env.DEV) {
		showDebugInfo.value = true;
	}
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

.header {
	width: 100%;
	display: flex;
	justify-content: start;
	align-items: center;
	font-size: 20px;
	flex-wrap: wrap;
	gap: 15px;
	padding-bottom: 15px;
	border-bottom: 2px solid #e5e7eb;
	margin-bottom: 20px;
	background: white;
	padding: 15px;
	border-radius: 10px;
	box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.cards {
	width: 100%;
	flex: 1;
	border-radius: 12px;
	margin-top: 15px;
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
	
	.loading-tip {
		color: #606266;
		font-size: 18px;
		text-align: center;
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 15px;
		
		.loading-icon {
			font-size: 48px;
			color: #409eff;
			animation: rotate 2s linear infinite;
			margin-bottom: 10px;
		}
		
		@keyframes rotate {
			from { transform: rotate(0deg); }
			to { transform: rotate(360deg); }
		}
	}
}

.video {
	width: 100%;
	max-height: 75vh;
	height: auto;
	object-fit: contain;
	border-radius: 8px;
	box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
	border: 2px solid #409eff;
	background: #000;
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
		
		&:hover {
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

.debug-panel {
	margin-top: 20px;
	padding: 15px;
	background: white;
	border-radius: 8px;
	box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
	
	.debug-content {
		p {
			margin: 8px 0;
			font-size: 14px;
		}
	}
}

// 响应式适配优化
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
	
	.video {
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
	
	.video {
		max-height: 60vh;
	}
}
</style>