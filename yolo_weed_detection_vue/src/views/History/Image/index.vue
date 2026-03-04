<template>
	<div class="system-role-container layout-padding">
		<div class="system-role-padding layout-padding-auto layout-padding-view">
			<div class="history-title-row">
				<div>
					<h3 class="history-title">图像检测记录</h3>
					<p class="history-subtitle">查看历史图像检测结果，支持按用户和识别结果筛选</p>
				</div>
			</div>

			<div class="system-user-search action-card mb15">
				<el-input v-model="state.tableData.param.search1" size="default" placeholder="请输入用户名"
					style="max-width: 180px"> </el-input>
				<el-input v-model="state.tableData.param.search2" size="default" placeholder="请输入识别结果"
					style="max-width: 180px; margin-left: 15px">
				</el-input>
				<el-button size="default" type="primary" class="ml10" @click="getTableData()">
					<el-icon>
						<ele-Search />
					</el-icon>
					查询
				</el-button>
				<el-button 
					size="small" 
					type="info" 
					@click="showDebugPanel = !showDebugPanel"
					style="margin-left: 10px;"
				>
					{{ showDebugPanel ? '隐藏调试' : '显示调试' }}
				</el-button>
			</div>
			
			<!-- 调试面板 -->
			<el-collapse v-model="activeDebugPanel" v-if="showDebugPanel" class="mt15 debug-collapse">
				<el-collapse-item title="路径转换调试" name="1">
					<el-table :data="state.tableData.data.slice(0, 3)" size="small">
						<el-table-column prop="input_img" label="原始路径" width="200">
							<template #default="{ row }">
								<div style="font-size: 10px; word-break: break-all;">{{ row.input_img }}</div>
							</template>
						</el-table-column>
						<el-table-column label="转换后URL" width="200">
							<template #default="{ row }">
								<div style="font-size: 10px; word-break: break-all;">{{ getImageUrl(row.input_img) }}</div>
							</template>
						</el-table-column>
						<el-table-column label="预览" width="100">
							<template #default="{ row }">
								<el-image 
									:src="getImageUrl(row.input_img)"
									style="width: 80px; height: 60px;"
									fit="cover"
								/>
							</template>
						</el-table-column>
					</el-table>
				</el-collapse-item>
			</el-collapse>
			
			<el-table :data="state.tableData.data" v-loading="state.tableData.loading" style="width: 100%" class="history-table">
				<el-table-column type="expand">
					<template #default="props">
						<div m="4">
							<p style="margin-left: 20px; font-size: 16px; font-weight: 800;">详细识别结果：</p>
							<el-table :data="props.row.family" v-if="props.row.family && props.row.family.length > 0">
								<el-table-column prop="label" label="识别结果" align="center" />
								<el-table-column prop="confidence" label="置信度" show-overflow-tooltip
									align="center">
									<template #default="{ row }">
										{{ formatConfidence(row.confidence) }}
									</template>
								</el-table-column>
								<el-table-column prop="detectionTime" label="识别时间" align="center" />
							</el-table>
							<div v-else style="text-align: center; padding: 20px; color: #999;">
								无详细检测结果
							</div>
						</div>
					</template>
				</el-table-column>
				<el-table-column prop="num" label="序号" width="80" align="center" />
				<el-table-column prop="input_img" label="原始图片" width="120" align="center">
					<template #default="scope">
						<el-image 
							:src="getImageUrl(scope.row.input_img)" 
							:preview-src-list="[getImageUrl(scope.row.input_img)]"
							fit="cover"
							style="width: 120px; height: 80px; border-radius: 4px;"
							hide-on-click-modal
						>
							<template #placeholder>
								<div class="image-placeholder">
									<el-icon><ele-Loading /></el-icon>
									<div>加载中...</div>
								</div>
							</template>
							<template #error>
								<div class="image-error">
									<el-icon><ele-Picture /></el-icon>
									<div>加载失败</div>
									<small>{{ getImageError(scope.row.input_img) }}</small>
								</div>
							</template>
						</el-image>
					</template>
				</el-table-column>
				<el-table-column prop="out_img" label="预测图片" width="120" align="center">
					<template #default="scope">
						<el-image 
							v-if="scope.row.out_img"
							:src="getImageUrl(scope.row.out_img)" 
							:preview-src-list="[getImageUrl(scope.row.out_img)]"
							fit="cover"
							style="width: 120px; height: 80px; border-radius: 4px;"
							lazy
							hide-on-click-modal
						>
							<template #placeholder>
								<div class="image-placeholder">
									<el-icon><ele-Loading /></el-icon>
									<div>加载中...</div>
								</div>
							</template>
							<template #error>
								<div class="image-error">
									<el-icon><ele-Picture /></el-icon>
									<div>加载失败</div>
								</div>
							</template>
						</el-image>
						<span v-else class="no-image">无结果图</span>
					</template>
				</el-table-column>
				<el-table-column prop="confidence" label="置信度" show-overflow-tooltip align="center">
					<template #default="{ row }">
						{{ formatConfidence(row.confidence) }}
					</template>
				</el-table-column>
				<el-table-column prop="conf" label="最小阈值" show-overflow-tooltip align="center">
					<template #default="{ row }">
						{{ (parseFloat(row.conf || 0.5) * 100).toFixed(0) }}%
					</template>
				</el-table-column>
				<el-table-column prop="all_time" label="总用时" show-overflow-tooltip align="center">
					<template #default="{ row }">
						{{ formatTime(row.all_time) }}
					</template>
				</el-table-column>
				<el-table-column prop="start_time" label="识别时间" width="200" align="center">
					<template #default="{ row }">
						{{ formatDateTime(row.start_time) }}
					</template>
				</el-table-column>
				<el-table-column prop="username" label="识别用户" show-overflow-tooltip align="center"></el-table-column>
				<el-table-column label="操作" width="80">
					<template #default="scope">
						<el-button size="small" text type="primary" @click="onRowDel(scope.row)">删除</el-button>
					</template>
				</el-table-column>
			</el-table>
			<el-pagination 
				@size-change="onHandleSizeChange" 
				@current-change="onHandleCurrentChange" 
				class="mt15 history-pagination"
				:pager-count="5" 
				:page-sizes="[10, 20, 30]" 
				v-model:current-page="state.tableData.param.pageNum"
				background 
				v-model:page-size="state.tableData.param.pageSize"
				:layout="state.tableData.total > 0 ? 'total, sizes, prev, pager, next, jumper' : ''" 
				:total="state.tableData.total"
				:hide-on-single-page="state.tableData.total <= state.tableData.param.pageSize">
			</el-pagination>
			
			<!-- 空数据提示 -->
			<el-empty v-if="state.tableData.data.length === 0 && !state.tableData.loading" class="history-empty" description="暂无检测记录" :image-size="200">
				<template #image>
					<el-icon size="100" color="#c0c4cc">
						<ele-Picture />
					</el-icon>
				</template>
			</el-empty>
		</div>
	</div>
</template>

<script setup lang="ts" name="systemRole">
import { reactive, onMounted, watch, ref } from 'vue';
import { ElMessageBox, ElMessage } from 'element-plus';
import { Picture, Loading as EleLoading } from '@element-plus/icons-vue';
import request from '@/utils/request';
import { useUserInfo } from '@/utils/stores/userInfo';
import { storeToRefs } from 'pinia';

const stores = useUserInfo();
const { userInfos } = storeToRefs(stores);

const state = reactive({
	tableData: {
		data: [] as any[],
		total: 0,
		loading: false,
		param: {
			search1: '', // 用户名搜索
			search2: '', // 标签搜索
			pageNum: 1,
			pageSize: 10,
		},
	},
});

// 调试面板状态
const showDebugPanel = ref(false);
const activeDebugPanel = ref(['1']);

// ====================== 工具函数 ======================

// 工具函数：格式化置信度
const formatConfidence = (confidence: any): string => {
	if (confidence === null || confidence === undefined || confidence === '') {
		return '0%';
	}
	
	try {
		// 如果是字符串，尝试解析
		if (typeof confidence === 'string') {
			// 尝试解析为JSON
			try {
				const parsed = JSON.parse(confidence);
				if (Array.isArray(parsed)) {
					// 取数组第一个值或平均值
					if (parsed.length > 0) {
						const avg = parsed.reduce((a: number, b: number) => a + b, 0) / parsed.length;
						return (avg * 100).toFixed(2) + '%';
					}
					return '0%';
				}
				// 如果是数字
				return (parseFloat(parsed) * 100).toFixed(2) + '%';
			} catch {
				// 如果不是JSON，直接转为数字
				const num = parseFloat(confidence);
				return !isNaN(num) ? (num * 100).toFixed(2) + '%' : '0%';
			}
		}
		
		// 如果是数组
		if (Array.isArray(confidence)) {
			if (confidence.length > 0) {
				const avg = confidence.reduce((a: number, b: number) => a + b, 0) / confidence.length;
				return (avg * 100).toFixed(2) + '%';
			}
			return '0%';
		}
		
		// 如果是数字
		if (typeof confidence === 'number') {
			return (confidence * 100).toFixed(2) + '%';
		}
		
		return '0%';
	} catch (error) {
		console.error('格式化置信度失败:', error, confidence);
		return '0%';
	}
};

// 2.3替换原有的 getImageUrl 函数
const getImageUrl = (path: string): string => {
  if (!path || path.trim() === '') {
    return '/src/assets/images/placeholder.jpg';
  }
  
  console.log('原始路径:', path);
  
  // 统一斜杠
  const normalized = path.replace(/\\/g, '/');
  
  // 情况1：已经是HTTP URL
  if (normalized.startsWith('http://') || normalized.startsWith('https://')) {
    return normalized;
  }
  
	// 情况2：包含历史绝对路径
	if (normalized.includes(':/')) {
    // 提取uploads/results之后的部分
    const uploadsIndex = normalized.indexOf('/uploads/');
    const resultsIndex = normalized.indexOf('/results/');
    const runsIndex = normalized.indexOf('/runs/');
    
    if (uploadsIndex !== -1) {
      return normalized.substring(uploadsIndex);
    }
    if (resultsIndex !== -1) {
      return normalized.substring(resultsIndex);
    }
    if (runsIndex !== -1) {
      return normalized.substring(runsIndex);
    }
    
		return `/${normalized}`;
  }
  
  // 情况3：以/uploads等开头的相对路径
  if (normalized.startsWith('/uploads/') || 
      normalized.startsWith('/results/') || 
      normalized.startsWith('/runs/')) {
    return normalized;
  }
  
  // 情况4：普通的相对路径
  if (normalized.startsWith('/')) {
    return normalized;
  }
  
  // 情况5：只有文件名
  return `/uploads/images/${normalized}`;
};

// 辅助函数：获取图片错误信息
const getImageError = (path: string): string => {
	if (path.startsWith('file://')) {
		return 'file://协议被阻止';
	}
	if (/^[A-Za-z]:\\/.test(path)) {
		return 'Windows路径需转换';
	}
	return '路径无效';
};

// 工具函数：格式化时间（秒）
const formatTime = (seconds: any): string => {
	if (!seconds && seconds !== 0) return '0秒';
	
	const num = parseFloat(seconds);
	if (isNaN(num)) return '0秒';
	
	if (num < 1) {
		return (num * 1000).toFixed(0) + '毫秒';
	} else if (num < 60) {
		return num.toFixed(3) + '秒';
	} else {
		const mins = Math.floor(num / 60);
		const secs = (num % 60).toFixed(3);
		return `${mins}分${secs}秒`;
	}
};

// 工具函数：格式化日期时间（增强版）
// 替换原有的复杂逻辑
const formatDateTime = (dateTime: string | Date): string => {
  if (!dateTime) return '未知时间';
  
  try {
		let date: Date;
		if (typeof dateTime === 'string') {
			const normalized = dateTime.includes('T') ? dateTime : dateTime.replace(' ', 'T');
			const hasTimezone = /Z$|[+-]\d{2}:?\d{2}$/.test(normalized);
			date = new Date(normalized);

			if (hasTimezone) {
				return new Intl.DateTimeFormat('zh-CN', {
					timeZone: 'Asia/Shanghai',
					year: 'numeric',
					month: '2-digit',
					day: '2-digit',
					hour: '2-digit',
					minute: '2-digit',
					second: '2-digit',
					hour12: false,
				}).format(date).replace(/\//g, '-');
			}

			if (isNaN(date.getTime())) {
				return typeof dateTime === 'string' ? dateTime.substring(0, 19) : '无效时间';
			}

			const pad = (n: number) => String(n).padStart(2, '0');
			return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())} ${pad(date.getHours())}:${pad(date.getMinutes())}:${pad(date.getSeconds())}`;
		} else {
			date = dateTime;
		}

    if (isNaN(date.getTime())) {
      return typeof dateTime === 'string' ? dateTime.substring(0, 19) : '无效时间';
    }

		return new Intl.DateTimeFormat('zh-CN', {
			timeZone: 'Asia/Shanghai',
			year: 'numeric',
			month: '2-digit',
			day: '2-digit',
			hour: '2-digit',
			minute: '2-digit',
			second: '2-digit',
			hour12: false,
		}).format(date).replace(/\//g, '-');
  } catch (error) {
    console.error('格式化日期失败:', error, dateTime);
    return typeof dateTime === 'string' ? dateTime : '时间格式错误';
  }
};

// ====================== 数据获取和处理 ======================

// 获取表格数据
const getTableData = () => {
	state.tableData.loading = true;
	
	// 构建查询参数
	const params: any = {
		page: state.tableData.param.pageNum,
		page_size: state.tableData.param.pageSize,
	};
	
	// 添加搜索条件
	if (state.tableData.param.search1) {
		params.username = state.tableData.param.search1;
	}
	if (state.tableData.param.search2) {
		params.search_label = state.tableData.param.search2;
	}
	
	// 如果不是管理员，只显示当前用户的记录
	if (userInfos.value.userName !== 'admin') {
		params.username = userInfos.value.userName;
	}
	
	console.log('查询图片记录参数:', params);
	
	// 请求Flask服务的图片记录接口
	request.get('/flask/img_records', { params })
		.then((res) => {
			console.log('获取图片记录响应:', res);
			
			if (res.status === 200 || res.code === 200) {
				const data = res.data || res;
				
				state.tableData.data = [];
				state.tableData.total = data.total || 0;
				
				// 处理每一条记录
				if (data.records && Array.isArray(data.records)) {
					data.records.forEach((record: any, index: number) => {
						// 解析detections字段
						let detections = [];
						try {
							if (record.detections && record.detections !== '') {
								detections = typeof record.detections === 'string' 
									? JSON.parse(record.detections) 
									: record.detections;
							}
						} catch (error) {
							console.warn('解析detections失败:', error, record.detections);
						}
						
						// 解析label字段
						let labels = [];
						try {
							if (record.label && record.label !== '') {
								labels = typeof record.label === 'string'
									? JSON.parse(record.label)
									: record.label;
								
								// 确保labels是数组
								if (!Array.isArray(labels)) {
									labels = [labels];
								}
							}
						} catch (error) {
							console.warn('解析label失败:', error, record.label);
							labels = record.label ? [record.label] : [];
						}
						
						// 解析confidence字段
						let confidences = [];
						try {
							if (record.confidence && record.confidence !== '') {
								confidences = typeof record.confidence === 'string'
									? JSON.parse(record.confidence)
									: record.confidence;
								
								// 确保confidences是数组
								if (!Array.isArray(confidences)) {
									confidences = [confidences];
								}
							}
						} catch (error) {
							console.warn('解析confidence失败:', error, record.confidence);
							confidences = record.confidence ? [parseFloat(record.confidence) || 0] : [];
						}
						
						// 构建family数据
						const family = labels.map((label: string, idx: number) => ({
							label: label || '未识别',
							confidence: confidences[idx] || 0,
							detectionTime: formatDateTime(record.start_time || record.startTime)
						}));
						
						// 计算平均置信度（用于表格显示）
						let avgConfidence = 0;
						if (confidences.length > 0) {
							avgConfidence = confidences.reduce((a: number, b: number) => a + b, 0) / confidences.length;
						}
						
						// 构建表格行数据（提前格式化时间）
						const transformedData = {
							id: record.id,
							num: (state.tableData.param.pageNum - 1) * state.tableData.param.pageSize + index + 1,
							input_img: record.input_img || record.inputImg || '',
							out_img: record.out_img || record.outImg || '',
							confidence: avgConfidence,
							all_time: record.all_time || record.allTime || 0,
							conf: record.conf || 0.5,
							start_time: formatDateTime(record.start_time || record.startTime || ''), // 提前格式化
							username: record.username || '未知用户',
							label: Array.isArray(labels) ? labels.join(', ') : labels,
							family: family,
							detections: detections
						};
						
						// 调试：检查图片路径
						if (transformedData.input_img) {
							console.log(`记录 ${transformedData.id} 原始图片路径: ${transformedData.input_img}`);
							console.log(`记录 ${transformedData.id} 转换后URL: ${getImageUrl(transformedData.input_img)}`);
						}
						
						state.tableData.data.push(transformedData);
					});
				}
				
				if (state.tableData.data.length > 0) {
					ElMessage.success(`获取到 ${state.tableData.data.length} 条记录`);
				}
			} else {
				ElMessage.error(data.message || '获取记录失败');
			}
		})
		.catch((error) => {
			console.error('获取图片记录失败:', error);
			ElMessage.error('获取图片记录失败，请检查Flask服务');
		})
		.finally(() => {
			state.tableData.loading = false;
		});
};

// 删除记录
const onRowDel = (row: any) => {
	ElMessageBox.confirm(`此操作将永久删除该检测记录，是否继续?`, '提示', {
		confirmButtonText: '确认',
		cancelButtonText: '取消',
		type: 'warning',
	})
		.then(() => {
			console.log('删除图片记录:', row);
			
			request.delete(`/flask/img_records/${row.id}`)
				.then((res) => {
					console.log('删除图片记录响应:', res);
					
					if (res.code === 200 || res.status === 200) {
						ElMessage.success('删除成功！');
						
						// 重新获取数据
						setTimeout(() => {
							getTableData();
						}, 500);
					} else {
						ElMessage.error(res.message || '删除失败');
					}
				})
				.catch((error) => {
					console.error('删除图片记录失败:', error);
					ElMessage.error('删除失败，请检查Flask服务');
				});
		})
		.catch(() => { });
};

// 分页大小改变
const onHandleSizeChange = (val: number) => {
	state.tableData.param.pageSize = val;
	state.tableData.param.pageNum = 1; // 重置到第一页
	getTableData();
};

// 分页页码改变
const onHandleCurrentChange = (val: number) => {
	state.tableData.param.pageNum = val;
	getTableData();
};

// 监听搜索条件变化，自动搜索
watch(
	() => [state.tableData.param.search1, state.tableData.param.search2],
	() => {
		// 防抖处理，避免频繁请求
		clearTimeout((window as any).searchTimer);
		(window as any).searchTimer = setTimeout(() => {
			state.tableData.param.pageNum = 1; // 搜索时回到第一页
			getTableData();
		}, 500);
	}
);

// 页面加载时
onMounted(() => {
	getTableData();
});
</script>

<style scoped lang="scss">
.system-role-container {
	width: 100%;
	height: 100%;
	display: flex;
	flex-direction: column;

	.system-role-padding {
		padding: 16px;
		height: 100%;
		display: flex;
		flex-direction: column;
		gap: 12px;
		overflow: auto;
	}
}

.history-title-row {
	width: 100%;
	display: flex;
	align-items: center;
}

.history-title {
	font-size: 24px;
	line-height: 1.25;
	font-weight: 700;
	color: var(--app-text-1, #111827);
}

.history-subtitle {
	margin-top: 6px;
	font-size: 13px;
	color: var(--app-text-2, #6b7280);
}

.system-user-search {
	display: flex;
	align-items: center;
	flex-wrap: wrap;
	gap: 10px;
	padding: 14px;
	
	.el-input {
		flex: 1;
		min-width: 180px;
	}
}

.action-card {
	background: #fff;
	border: 1px solid var(--el-border-color-light);
	border-radius: 14px;
	box-shadow: 0 8px 24px rgba(17, 24, 39, 0.06);
}

.debug-collapse {
	padding: 10px 12px;
	background: #fff;
	border: 1px solid var(--el-border-color-light);
	border-radius: 12px;
}

.mb15 {
	margin-bottom: 15px;
}

.ml10 {
	margin-left: 10px;
}

.mt15 {
	margin-top: 15px;
}

.history-table {
	flex: 1;
	background: #fff;
	border-radius: 12px;
	overflow: hidden;
	box-shadow: 0 8px 24px rgba(17, 24, 39, 0.06);
	border: 1px solid var(--el-border-color-light);
	
	:deep(.el-table__row) {
		&:hover {
			background-color: #eef2ff;
		}
	}

	:deep(.el-table__cell) {
		padding: 12px 0;
	}
	
	:deep(.el-image) {
		border-radius: 4px;
		transition: transform 0.3s ease;
		
		&:hover {
			transform: scale(1.05);
			cursor: pointer;
		}
	}
	
	.image-placeholder {
		width: 120px;
		height: 80px;
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		background: #f5f5f5;
		border-radius: 4px;
		color: #999;
		
		.el-icon {
			font-size: 24px;
			margin-bottom: 5px;
			animation: rotate 2s linear infinite;
		}
		
		div {
			font-size: 12px;
		}
	}
	
	.image-error {
		width: 120px;
		height: 80px;
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		background: #fef0f0;
		border-radius: 4px;
		color: #f56c6c;
		padding: 5px;
		
		.el-icon {
			font-size: 24px;
			margin-bottom: 5px;
		}
		
		div {
			font-size: 12px;
			margin-bottom: 2px;
		}
		
		small {
			font-size: 10px;
			color: #999;
			text-align: center;
			word-break: break-all;
			max-width: 100%;
			overflow: hidden;
			text-overflow: ellipsis;
		}
	}
	
	.no-image {
		color: #c0c4cc;
		font-size: 12px;
		display: inline-block;
		padding: 10px;
		background: #f5f5f5;
		border-radius: 4px;
	}
}

.history-pagination {
	padding: 8px 0 2px;
}

.history-empty {
	padding: 18px 0 8px;
}

// 响应式适配
@media (max-width: 768px) {
	.system-user-search {
		flex-direction: column;
		align-items: stretch;
		
		.el-input {
			width: 100%;
			min-width: unset;
			margin-bottom: 10px;
			
			&:last-child {
				margin-bottom: 0;
			}
		}
		
		.el-button {
			width: 100%;
			margin-left: 0 !important;
		}
	}
	
	.history-table {
		:deep(.el-table__cell) {
			padding: 8px 0;
		}
	}
}

@keyframes rotate {
	from { transform: rotate(0deg); }
	to { transform: rotate(360deg); }
}
</style>
