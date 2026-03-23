<template>
	<div class="system-predict-container layout-padding">
		<div class="system-predict-padding layout-padding-auto layout-padding-view">
			<div class="detect-title-row">
				<div>
					<h3 class="detect-title">图像检测</h3>
					<p class="detect-subtitle">上传图片后执行 YOLOv11 检测，结果与检测框实时展示</p>
				</div>
			</div>

			<el-card shadow="never" class="action-card">
				<div class="action-row">
					<div class="conf">
						<div class="conf-label">设置最小置信度阈值</div>
						<el-slider v-model="conf" :format-tooltip="formatTooltip" class="conf-slider" :min="0" :max="100" :step="1" />
						<el-select v-model="state.selectedModel" class="model-select" placeholder="选择模型" @change="onModelChange">
							<el-option v-for="item in state.modelOptions" :key="item.name" :label="item.name" :value="item.name" />
						</el-select>
					</div>
					<div class="button-section">
						<el-upload
							ref="quickUploadRef"
							class="quick-uploader"
							:action="uploadAction"
							:show-file-list="false"
							:on-success="handleAvatarSuccessone"
							:before-upload="beforeUpload"
						>
							<el-button type="info" class="predict-button" :disabled="state.isDetecting">上传杂草检测图片</el-button>
						</el-upload>
					</div>
					<div class="button-section">
						<el-button type="primary" @click="upData" class="predict-button" :disabled="state.isDetecting">
							{{ state.isDetecting ? '正在检测中' : '开始杂草检测' }}
						</el-button>
					</div>
				</div>
			</el-card>

			<el-card shadow="never" class="card preview-card">
				<div class="img-container" ref="imgContainer">
					<img :src="currentImageUrl" class="avatar" alt="检测图片" ref="imageRef" @load="onImageLoad" v-show="currentImageUrl" />
					<canvas ref="canvasRef" class="detection-canvas" v-show="currentImageUrl" @click="handleCanvasClick"></canvas>

					<el-upload
						v-if="!currentImageUrl"
						v-model="state.img"
						ref="uploadFile"
						class="avatar-uploader"
						:action="uploadAction"
						:show-file-list="false"
						:on-success="handleAvatarSuccessone"
						:before-upload="beforeUpload"
					>
						<div class="upload-panel">
							<el-icon class="avatar-uploader-icon">
								<Plus />
							</el-icon>
							<div class="upload-title">点击上传杂草图片</div>
							<div class="upload-note">支持 JPG / PNG，单张 ≤ 50MB</div>
						</div>
					</el-upload>
				</div>
			</el-card>

			<el-card class="result-section" shadow="never" v-if="state.predictionResult.label || detections.length > 0">
				<div class="bottom">
					<div class="metric-item">
						<div class="metric-label">识别结果</div>
						<div class="metric-value">{{ state.predictionResult.label || '未识别' }}</div>
					</div>
					<div class="metric-item">
						<div class="metric-label">预测概率</div>
						<div class="metric-value">{{ state.predictionResult.confidence || '0%' }}</div>
					</div>
					<div class="metric-item">
						<div class="metric-label">总时间</div>
						<div class="metric-value">{{ state.predictionResult.allTime || '0秒' }}</div>
					</div>
				</div>

				<div class="detections-detail" v-if="detections.length > 0">
					<div class="detection-count">共检测到 {{ detections.length }} 个目标</div>
					<el-table :data="detections" style="width: 100%; margin-top: 10px;" size="small" :max-height="300">
						<el-table-column prop="weed_name" label="类别名称" width="120"></el-table-column>
						<el-table-column prop="confidence" label="置信度" width="100">
							<template #default="{ row }">
								{{ (row.confidence * 100).toFixed(2) }}%
							</template>
						</el-table-column>
						<el-table-column prop="bbox" label="位置" width="200">
							<template #default="{ row }">
								({{ row.bbox.x }}, {{ row.bbox.y }}) - 
								宽:{{ row.bbox.width }}px, 高:{{ row.bbox.height }}px
							</template>
						</el-table-column>
						<el-table-column label="操作" width="100">
							<template #default="{ row, $index }">
								<el-button
									size="small"
									@click="highlightDetection($index)"
									:type="highlightedIndex === $index ? 'primary' : 'default'"
								>
									{{ highlightedIndex === $index ? '已高亮' : '高亮' }}
								</el-button>
							</template>
						</el-table-column>
					</el-table>
				</div>
			</el-card>
		</div>
	</div>
</template>

<script setup lang="ts" name="imgPredict">
import { reactive, ref, onMounted, onActivated, onDeactivated, computed, nextTick, onUnmounted } from 'vue';
import type { UploadInstance, UploadProps } from 'element-plus';
import { ElMessage } from 'element-plus';
import request from '@/utils/request';
import { Plus } from '@element-plus/icons-vue';
import { useUserInfo } from '@/utils/stores/userInfo';
import { storeToRefs } from 'pinia';
import { formatDate } from '@/utils/formatTime';

// 核心变量：分离原图和检测结果图
const imageUrl = ref(''); // 上传的原图临时地址
const detectedImageUrl = ref(''); // 后端返回的带检测框图片地址（相对路径，走代理）
const conf = ref(50); // 置信度默认50%
const uploadFile = ref<UploadInstance>();
const quickUploadRef = ref<UploadInstance>();
const stores = useUserInfo();
const { userInfos } = storeToRefs(stores);

// 新增：检测框相关变量
const imageRef = ref<HTMLImageElement | null>(null);
const canvasRef = ref<HTMLCanvasElement | null>(null);
const imgContainer = ref<HTMLElement | null>(null);
const detections = ref<any[]>([]); // 存储检测框数据
const highlightedIndex = ref<number | null>(null); // 当前高亮的检测框索引

// 计算当前显示的图片URL（直接使用相对路径，Vite代理自动转发）
const currentImageUrl = computed(() => {
	return detectedImageUrl.value || imageUrl.value;
});

// 上传地址：走Vite代理/flask（和vite.config.ts的/flask代理匹配，后端上传接口是/flask/upload）
const uploadAction = ref('/flask/upload');

const state = reactive({
	img: '', // 上传图片的后端标识
	predictionResult: { label: '', confidence: '', allTime: '' },
	form: { username: '', inputImg: '', conf: 0, startTime: '' }, // inputImg: string, conf: number
	isDetecting: false, // 检测状态锁，防止重复请求
	modelOptions: [] as Array<{ name: string; path?: string; selected?: boolean }>,
	selectedModel: '',
});

const getDetectionColor = (det: any, index: number) => {
	const name = String(det?.weed_name || `cls-${index}`);
	let hash = 0;
	for (let i = 0; i < name.length; i++) hash = (hash * 31 + name.charCodeAt(i)) >>> 0;
	const hue = hash % 360;
	return {
		stroke: `hsl(${hue}, 90%, 45%)`,
		fill: `hsla(${hue}, 90%, 45%, 0.14)`,
		label: `hsl(${hue}, 90%, 38%)`,
	};
};

const getScaledBox = (bbox: any) => {
	if (!canvasRef.value || !imageRef.value) return null;
	const canvas = canvasRef.value;
	const img = imageRef.value;
	const naturalW = img.naturalWidth || canvas.width;
	const naturalH = img.naturalHeight || canvas.height;
	const sx = canvas.width / naturalW;
	const sy = canvas.height / naturalH;

	let x = 0;
	let y = 0;
	let width = 0;
	let height = 0;
	if (bbox.x !== undefined && bbox.y !== undefined && bbox.width !== undefined && bbox.height !== undefined) {
		x = bbox.x;
		y = bbox.y;
		width = bbox.width;
		height = bbox.height;
	} else if (bbox.x1 !== undefined && bbox.y1 !== undefined && bbox.x2 !== undefined && bbox.y2 !== undefined) {
		x = bbox.x1;
		y = bbox.y1;
		width = bbox.x2 - bbox.x1;
		height = bbox.y2 - bbox.y1;
	}
	return {
		x: x * sx,
		y: y * sy,
		width: width * sx,
		height: height * sy,
	};
};

// 置信度滑块格式化
const formatTooltip = (val: number) => val / 100;

// 上传前验证
const beforeUpload = (file: File) => {
	// 检查文件类型
	const isImage = file.type.startsWith('image/');
	if (!isImage) {
		ElMessage.error('只能上传图片文件！');
		return false;
	}
	
	// 检查文件大小（限制5MB）
	const isLt5M = file.size / 1024 / 1024 < 50;
	if (!isLt5M) {
		ElMessage.error('图片大小不能超过50MB！');
		return false;
	}
	
	return true;
};

// 图片上传成功回调
const handleAvatarSuccessone: UploadProps['onSuccess'] = (response, uploadFile) => {
	// 上传新图时，清空之前的检测结果和带框图
	clearCanvas(); // 清理画布
	detectedImageUrl.value = '';
	detections.value = [];
	highlightedIndex.value = null;
	state.predictionResult = { label: '', confidence: '', allTime: '' };
	
	// 释放旧的图片URL（避免内存泄漏）
	if (imageUrl.value && imageUrl.value.startsWith('blob:')) {
		URL.revokeObjectURL(imageUrl.value);
	}
	
	// 生成原图临时预览地址（本地blob，无需代理）
	imageUrl.value = URL.createObjectURL(uploadFile.raw!);
	// 强制回到顶部，保证操作控件始终可见
	nextTick(() => {
		const host = document.querySelector('.system-predict-padding') as HTMLElement | null;
		if (host) host.scrollTop = 0;
	});
	// 适配后端上传响应格式，获取图片标识
	state.img = response.data || response.fileName || '';
	ElMessage.success('杂草检测图片上传成功！');
};

// 清理画布
const clearCanvas = () => {
	if (canvasRef.value) {
		const canvas = canvasRef.value;
		const ctx = canvas.getContext('2d');
		if (ctx) {
			ctx.clearRect(0, 0, canvas.width, canvas.height);
		}
	}
};

// 图片加载完成事件
const onImageLoad = () => {
	nextTick(() => {
		// 等待DOM更新后绘制检测框
		drawDetections();
	});
};

// 绘制检测框（原有逻辑不变，保留所有绘制功能）
const drawDetections = () => {
	if (!canvasRef.value || !imageRef.value || detections.value.length === 0) {
		return;
	}
	
	const canvas = canvasRef.value;
	const ctx = canvas.getContext('2d');
	const img = imageRef.value;
	
	if (!ctx) return;
	
	// 设置canvas尺寸与图片一致
	canvas.width = img.width;
	canvas.height = img.height;
	
	// 清空画布
	ctx.clearRect(0, 0, canvas.width, canvas.height);
	
	// 绘制每个检测框
	detections.value.forEach((det, index) => {
		const bbox = det.bbox;
		const scaled = getScaledBox(bbox);
		if (!scaled) {
			// 坐标格式不支持
			console.warn('不支持的bbox格式:', bbox);
			return;
		}
		const { x, y, width, height } = scaled;
		
		// 判断是否高亮
		const isHighlighted = highlightedIndex.value === index;
		const color = getDetectionColor(det, index);
		
		// 设置绘制样式
		ctx.strokeStyle = isHighlighted ? '#ff2d55' : color.stroke;
		ctx.lineWidth = isHighlighted ? 4 : 2;
		ctx.fillStyle = isHighlighted ? 'rgba(255, 45, 85, 0.20)' : color.fill;
		
		// 绘制矩形框
		ctx.strokeRect(x, y, width, height);
		ctx.fillRect(x, y, width, height);
		if (isHighlighted) {
			ctx.shadowColor = 'rgba(255, 45, 85, 0.55)';
			ctx.shadowBlur = 12;
			ctx.strokeRect(x, y, width, height);
			ctx.shadowBlur = 0;
		}
		
		// 绘制标签背景
		ctx.fillStyle = isHighlighted ? '#ff2d55' : color.label;
		ctx.font = '14px Arial';
		const text = `${det.weed_name} ${(det.confidence * 100).toFixed(1)}%`;
		const textWidth = ctx.measureText(text).width;
		
		// 标签背景位置（避免超出图片边界）
		const labelX = Math.max(0, Math.min(x, canvas.width - textWidth - 10));
		const labelY = Math.max(20, y);
		
		ctx.fillRect(labelX, labelY - 20, textWidth + 10, 20);
		
		// 绘制文字
		ctx.fillStyle = '#ffffff';
		ctx.fillText(text, labelX + 5, labelY - 5);
		
		// 绘制角标（可选）
		ctx.strokeStyle = isHighlighted ? '#ff0000' : '#00ff00';
		ctx.lineWidth = 2;
		
		// 左上角
		const cornerSize = 15;
		ctx.beginPath();
		ctx.moveTo(x, y + cornerSize);
		ctx.lineTo(x, y);
		ctx.lineTo(x + cornerSize, y);
		ctx.stroke();
		
		// 右上角
		ctx.beginPath();
		ctx.moveTo(x + width - cornerSize, y);
		ctx.lineTo(x + width, y);
		ctx.lineTo(x + width, y + cornerSize);
		ctx.stroke();
		
		// 左下角
		ctx.beginPath();
		ctx.moveTo(x, y + height - cornerSize);
		ctx.lineTo(x, y + height);
		ctx.lineTo(x + cornerSize, y + height);
		ctx.stroke();
		
		// 右下角
		ctx.beginPath();
		ctx.moveTo(x + width - cornerSize, y + height);
		ctx.lineTo(x + width, y + height);
		ctx.lineTo(x + width, y + height - cornerSize);
		ctx.stroke();
	});
};

const handleCanvasClick = (e: MouseEvent) => {
	if (!canvasRef.value || detections.value.length === 0) return;
	const rect = canvasRef.value.getBoundingClientRect();
	const x = e.clientX - rect.left;
	const y = e.clientY - rect.top;

	for (let i = detections.value.length - 1; i >= 0; i--) {
		const scaled = getScaledBox(detections.value[i].bbox);
		if (!scaled) continue;
		if (x >= scaled.x && x <= scaled.x + scaled.width && y >= scaled.y && y <= scaled.y + scaled.height) {
			highlightDetection(i);
			return;
		}
	}
	highlightedIndex.value = null;
	drawDetections();
};

// 高亮指定检测框（原有逻辑不变）
const highlightDetection = (index: number) => {
	if (highlightedIndex.value === index) {
		highlightedIndex.value = null; // 取消高亮
	} else {
		highlightedIndex.value = index; // 设置高亮
	}
	
	// 重新绘制检测框
	drawDetections();
};

// 开始杂草检测

const upData = async () => {
	// 多重校验：防重复请求、防无图、防非法置信度
	if (state.isDetecting) return ElMessage.warning('正在检测中，请勿重复点击！');
	if (!state.img) return ElMessage.warning('请先上传杂草检测图片！');
	if (isNaN(Number(conf.value)) || conf.value < 0 || conf.value > 100) return ElMessage.warning('请设置0-100的有效置信度！');

	// 组装参数：修复类型为Number，适配后端接收
	state.isDetecting = true;
	state.form.conf = conf.value / 100; // number
	state.form.username = userInfos.value.userName || 'default_user';
	state.form.inputImg = state.img; // string
	state.form.startTime = formatDate(new Date(), 'YYYY-MM-DD HH:mm:ss'); // 修复时间格式符
	if (state.selectedModel) {
		(state.form as any).model_name = state.selectedModel;
	}

	try {
		// 🔥 核心修改1：检测接口改为/predict，匹配后端main.py和vite代理配置
		const res = await request.post('/predict', state.form);
		let result = res.data || res;
		result = typeof result === 'string' ? JSON.parse(result) : result;

		if (result.status === 200 || result.code === 0) {
			// 处理检测结果，兼容后端两种响应码（200/0）
			let label = result.label || '未识别到杂草';
			label = Array.isArray(label) ? label.join('、') : label;
			const confidence = result.confidence ? `${(Number(result.confidence) * 100).toFixed(2)}%` : '0%';
			const allTime = result.allTime ? `${Number(result.allTime).toFixed(2)}秒` : '0秒';

			// 更新页面：渲染带检测框的图片
			state.predictionResult = { label, confidence, allTime };
			
			// 存储检测框数据
			if (result.detections && Array.isArray(result.detections)) {
				detections.value = result.detections;
				highlightedIndex.value = null;
			} else {
				detections.value = [];
			}
			
			// 渲染后端返回的带检测框图片
			if (result.outImg) {
				detectedImageUrl.value = result.outImg; // 直接赋值相对路径，代理自动转发
				
				// 等待图片加载完成后绘制检测框
				nextTick(() => {
					if (imageRef.value) {
						// 移除之前的load事件监听器，避免重复绑定
						imageRef.value.onload = null;
						imageRef.value.onload = () => {
							drawDetections();
						};
					}
				});
			} else {
				// 如果没有检测后图片，使用原图并绘制检测框
				detectedImageUrl.value = '';
				if (imageRef.value) {
					imageRef.value.onload = () => {
						drawDetections();
					};
				}
			}
			
			// 检测成功提示，兼容后端detection_count字段
			ElMessage.success(`杂草检测成功！共检测到 ${result.detection_count || detections.value.length} 个目标`);
		} else {
			ElMessage.error(result.message || result.msg || '杂草检测失败，请重试');
		}
	} catch (error) {
		console.error('检测接口请求失败:', error);
		// 错误提示适配代理配置
		ElMessage.error('检测接口调用失败！请检查Flask是否启动+接口路径是否正确！');
	} finally {
		// 无论成功失败，释放检测锁
		state.isDetecting = false;
	}
};

// 彻底清理所有资源（原有逻辑不变）
const cleanupAllResources = () => {
	// 1. 释放图片URL（避免内存泄漏）
	if (imageUrl.value && imageUrl.value.startsWith('blob:')) {
		URL.revokeObjectURL(imageUrl.value);
	}
	
	// 2. 清除远程图片URL（避免缓存）
	if (detectedImageUrl.value) {
		// 强制浏览器清理图片缓存
		const img = new Image();
		img.src = detectedImageUrl.value + '?t=' + Date.now();
		setTimeout(() => {
			img.src = '';
		}, 100);
	}
	
	// 3. 清理画布
	clearCanvas();
	
	// 4. 重置所有状态
	imageUrl.value = '';
	detectedImageUrl.value = '';
	detections.value = [];
	highlightedIndex.value = null;
	state.img = '';
	state.isDetecting = false;
	state.predictionResult = { label: '', confidence: '', allTime: '' };
	
	// 5. 清除上传组件
	if (uploadFile.value) {
		uploadFile.value.clearFiles();
	}
	
	// 6. 清理图片元素引用
	if (imageRef.value) {
		imageRef.value.src = '';
		imageRef.value.removeAttribute('src');
	}
	
	// 7. 清理canvas引用
	if (canvasRef.value) {
		const canvas = canvasRef.value;
		canvas.width = 0;
		canvas.height = 0;
	}
	
	console.log('图片检测页面资源已彻底清理');
};

// 页面激活时：重置状态，重新初始化（原有逻辑不变）
onActivated(() => {
	console.log('图片检测页面激活 - 重置状态');
	
	// 重置检测状态和结果，防止路由切换后状态残留
	state.isDetecting = false;
	state.predictionResult = { label: '', confidence: '', allTime: '' };
	detections.value = [];
	highlightedIndex.value = null;
	
	// 重置上传组件（清空未完成的上传）
	if (uploadFile.value) uploadFile.value.clearFiles();
	
	// 重新绘制检测框（如果有）
	if (detections.value.length > 0) {
		drawDetections();
	}
});

// 页面失活时：彻底清理所有资源（原有逻辑不变）
onDeactivated(() => {
	console.log('图片检测页面失活 - 彻底清理资源');
	cleanupAllResources();
});

// Flask连通性检测
const checkFlaskConnection = async () => {
  try {
    // 🔥 核心修改2：连通性检测接口改为/predict，匹配后端和vite代理
    const response = await fetch('/predict', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({})
    });
    if (response.ok) {
      console.log('Flask服务正常（代理转发成功）');
			// 直接定位页面顶部的提示元素（根据页面结构）
			const tipElement = document.querySelector('.system-predict-container .NOT-FOUND');
			if (tipElement && tipElement instanceof HTMLElement) {
				tipElement.style.display = 'none'; // 强制隐藏
			}
    }
  } catch (error) {
    ElMessage.warning('Flask服务未启动或代理配置错误！');
  }
};

const loadModelOptions = async () => {
	try {
		let res: any;
		try {
			res = await request.get('/flask/file_names');
		} catch {
			res = await request.get('/file_names');
		}
		const data = res?.data || res || {};
		state.modelOptions = data.weight_items || [];
		const selected = state.modelOptions.find((x) => x.selected);
		state.selectedModel = selected?.name || data.current_model || state.modelOptions[0]?.name || '';
		if (!state.modelOptions.length) {
			ElMessage.warning('weights 目录未找到可用 .pt 模型');
		}
	} catch (error) {
		state.modelOptions = [];
		state.selectedModel = '';
		ElMessage.warning('模型列表加载失败，默认使用当前部署模型');
	}
};

const onModelChange = async (modelName: string) => {
	if (!modelName) return;
	try {
		let res: any;
		try {
			res = await request.post('/flask/set_model', { model_name: modelName });
		} catch {
			res = await request.post('/set_model', { model_name: modelName });
		}
		const data = res?.data || res || {};
		if (data.status === 200 || data.code === 0) {
			ElMessage.success(data.message || `已切换模型: ${modelName}`);
		} else {
			ElMessage.error(data.message || '模型切换失败');
		}
	} catch (error) {
		ElMessage.error('模型切换失败，请检查后端服务');
	}
};


// 保证置信度滑块和state.form.conf实时同步
import { watch } from 'vue';

onMounted(() => {
	// 优先检查Flask服务（走代理）
	checkFlaskConnection();

	// 监听窗口大小变化，重新绘制检测框
	window.addEventListener('resize', drawDetections);

	// 确保页面加载时清理旧状态
	cleanupAllResources();

	// 预加载用户信息
	if (stores && userInfos.value.userName) {
		state.form.username = userInfos.value.userName;
	}
	// 初始化置信度
	state.form.conf = conf.value / 100;
	loadModelOptions();
});

// 保证置信度滑块和state.form.conf实时同步
watch(conf, (val) => {
	state.form.conf = val / 100;
});

// 组件卸载前清理（原有逻辑不变）
onUnmounted(() => {
	window.removeEventListener('resize', drawDetections);
	cleanupAllResources();
});
</script>

<style scoped lang="scss">
.system-predict-container {
	width: 100%;
	height: 100%;
	display: flex;
	flex-direction: column;
	position: relative;
	isolation: isolate;

	.system-predict-padding {
		padding: 16px;
		height: 100%;
		min-height: 0;
		display: flex;
		flex-direction: column;
		gap: 12px;
		overflow-y: auto;
		overflow-x: hidden;
	}
}

.detect-title-row {
	width: 100%;
	display: flex;
	align-items: center;
}

.detect-title {
	font-size: 24px;
	line-height: 1.25;
	font-weight: 700;
	color: var(--app-text-1, #111827);
}

.detect-subtitle {
	margin-top: 6px;
	font-size: 13px;
	color: var(--app-text-2, #6b7280);
}

.action-card {
	border-radius: 14px;
	border: 1px solid var(--el-border-color-light);
	box-shadow: 0 8px 24px rgba(17, 24, 39, 0.06);
	position: sticky;
	top: 8px;
	z-index: 200;
	background: #fff;
}

.action-row {
	display: flex;
	align-items: center;
	justify-content: space-between;
	gap: 16px;
	flex-wrap: wrap;
}

.conf {
	flex: 1;
	min-width: 260px;
	display: flex;
	align-items: center;
	gap: 14px;
	flex-wrap: wrap;
}

.conf-label {
	font-size: 14px;
	font-weight: 600;
	color: #4b5563;
}

.conf-slider {
	max-width: 360px;
	width: 100%;
}

.model-select {
	width: 220px;
}

.card {
	width: 100%;
	flex: 0 0 auto;
	border-radius: 14px;
	margin-top: 0;
	display: flex;
	justify-content: center;
	align-items: center;
	padding: 16px;
	border: 1px solid var(--el-border-color-light);
	box-shadow: 0 10px 28px rgba(17, 24, 39, 0.06);
	background: linear-gradient(180deg, #fcfcfd 0%, #f8fafc 100%);
}

.preview-card {
	min-height: 420px;
	max-height: 62vh;
	position: relative;
	z-index: 1;
	overflow: hidden;
}

// 图片容器
.img-container {
	position: relative;
	width: 100%;
	height: 100%;
	display: flex;
	justify-content: center;
	align-items: center;
	overflow: hidden;
}

.avatar-uploader {
	width: 100%;
	height: 100%;

	:deep(.el-upload) {
		width: 100%;
		height: 100%;
	}
}

.upload-panel {
	width: 100%;
	height: 100%;
	min-height: 320px;
	display: flex;
	flex-direction: column;
	align-items: center;
	justify-content: center;
	gap: 8px;
	border: 2px dashed #d1d5db;
	border-radius: 12px;
	background: #ffffff;
	transition: all 0.2s ease;

	&:hover {
		border-color: #a5b4fc;
		background: #f8faff;
	}
}

.upload-title {
	font-size: 15px;
	font-weight: 600;
	color: #111827;
}

.upload-note {
	font-size: 12px;
	color: #6b7280;
}

.avatar {
	width: 100%;
	max-height: 58vh;
	height: auto;
	display: block;
	object-fit: contain;
	border-radius: 10px;
	box-shadow: 0 8px 18px rgba(0, 0, 0, 0.08);
	position: relative;
	z-index: 1;
}

// 检测框画布
.detection-canvas {
	position: absolute;
	top: 0;
	left: 0;
	width: 100%;
	height: 100%;
	pointer-events: auto;
	cursor: crosshair;
	z-index: 2;
}

.el-icon.avatar-uploader-icon {
	font-size: 32px;
	color: #6b7280;
}

.button-section {
	display: flex;
	justify-content: center;
	min-width: 180px;
}

.predict-button {
	width: 100%;
	height: 40px;
	border-radius: 12px;
}

.result-section {
	width: 100%;
	text-align: left;
	border-radius: 14px;
	padding: 10px;
	border: 1px solid var(--el-border-color-light);
	box-shadow: 0 10px 28px rgba(17, 24, 39, 0.06);
	overflow: visible;
}

.bottom {
	width: 100%;
	display: grid;
	grid-template-columns: repeat(3, minmax(0, 1fr));
	gap: 10px;
}

.metric-item {
	padding: 12px 14px;
	border-radius: 10px;
	background: #f8fafc;
	border: 1px solid #e5e7eb;
}

.metric-label {
	font-size: 12px;
	color: #6b7280;
}

.metric-value {
	margin-top: 5px;
	font-size: 15px;
	font-weight: 700;
	color: #111827;
}

// 检测框详情区域
.detections-detail {
	margin-top: 15px;
	padding: 0 4px;
	max-height: 360px;
	overflow-y: auto;
	overflow-x: hidden;
	
	.detection-count {
		font-size: 14px;
		font-weight: 700;
		color: #4338ca;
		text-align: left;
		margin-bottom: 10px;
	}
	
	:deep(.el-table) {
		border-radius: 10px;
		overflow: hidden;
		border: 1px solid #e5e7eb;

		.el-table__body-wrapper {
			max-height: 260px;
			overflow-y: auto;
		}

		.el-table__row:hover {
			background-color: #eef2ff;
			cursor: pointer;
		}
	}
}

.quick-uploader {
	:deep(.el-upload) {
		display: block;
	}
}

// 响应式适配
@media (max-width: 1000px) {
	.action-row {
		gap: 10px;
	}

	.conf {
		min-width: unset;
		width: 100%;
		flex-wrap: wrap;
	}

	.conf-slider {
		max-width: 100%;
	}

	.button-section {
		width: 100%;
		min-width: unset;
	}

	.predict-button {
		width: 100%;
	}

	.preview-card {
		min-height: 320px;
	}

	.bottom {
		grid-template-columns: 1fr;
	}
	
	.detections-detail {
		padding: 0;
	}
}
</style>
