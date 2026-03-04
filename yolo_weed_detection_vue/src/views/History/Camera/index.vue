<template>
	<div class="system-role-container layout-padding">
		<div class="system-role-padding layout-padding-auto layout-padding-view workbench-page-body">
			<div class="history-title-row workbench-title-row">
				<div>
					<h3 class="history-title workbench-title">摄像检测记录</h3>
					<p class="history-subtitle workbench-subtitle">查看摄像头检测历史，支持用户与阈值筛选、快速预览</p>
				</div>
			</div>

			<div class="system-user-search action-card workbench-action-card mb15">
				<el-input v-model="state.tableData.param.search1" size="default" placeholder="请输入用户名" 
					style="max-width: 200px"> </el-input>
				<el-input v-model="state.tableData.param.search2" size="default" placeholder="请输入最小阈值" 
					style="max-width: 200px; margin-left: 15px"></el-input>
				<el-button size="default" type="primary" class="ml10" @click="getTableData()">
					<el-icon>
						<ele-Search />
					</el-icon>
					查询
				</el-button>
				<el-button size="default" type="info" class="ml10" @click="resetSearch()">
					<el-icon>
						<ele-Refresh />
					</el-icon>
					重置
				</el-button>
			</div>
			
			<!-- 记录统计信息 -->
			<el-row :gutter="14" class="stats-row">
				<el-col :span="6">
					<el-statistic title="总记录数" :value="state.stats.totalRecords" />
				</el-col>
				<el-col :span="6">
					<el-statistic title="今日记录" :value="state.stats.todayRecords" />
				</el-col>
				<el-col :span="6">
					<el-statistic title="当前用户记录" :value="state.stats.userRecords" />
				</el-col>
				<el-col :span="6">
					<el-statistic title="总检测时长" :value="state.stats.totalDuration" suffix="秒" />
				</el-col>
			</el-row>
			
			<el-table :data="state.tableData.data" v-loading="state.tableData.loading" class="history-table workbench-table-card workbench-table-main" style="width: 100%; margin-top: 6px;">
				<el-table-column prop="num" label="序号" width="80" align="center" />
				<el-table-column prop="out_video" label="处理结果" width="200" align="center">
					<template #default="scope">
						<div class="video-container">
							<video class="video-preview" preload="auto" controls :key="scope.row.out_video + uniqueKey">
								<source :src="getVideoUrl(scope.row.out_video)" type="video/mp4" />
								您的浏览器不支持视频标签。
							</video>
							<div class="video-info">
								<el-tag size="small" type="success">摄像头检测</el-tag>
								<span class="video-time">{{ formatDate(scope.row.start_time) }}</span>
							</div>
						</div>
					</template>
				</el-table-column>
				<el-table-column prop="conf" label="置信度阈值" width="120" align="center">
					<template #default="{ row }">
						<el-tag :type="getConfTagType(row.conf)">
							{{ (row.conf * 100).toFixed(0) }}%
						</el-tag>
					</template>
				</el-table-column>
				<el-table-column prop="username" label="识别用户" width="120" align="center"></el-table-column>
				<el-table-column prop="start_time" label="识别时间" width="180" align="center">
					<template #default="{ row }">
						{{ formatDateTime(row.start_time) }}
					</template>
				</el-table-column>
				<el-table-column prop="created_at" label="创建时间" width="180" align="center">
										<template #default="{ row }">
											<span>{{ formatDateTime(row.created_at || row.createdAt) || '--' }}</span>
										</template>
				</el-table-column>
				<el-table-column label="操作" width="120" align="center" fixed="right">
					<template #default="scope">
						<div class="action-buttons">
							<el-button size="small" text type="primary" @click="previewVideo(scope.row)">
								<el-icon><ele-VideoPlay /></el-icon>
								播放
							</el-button>
							<el-button size="small" text type="danger" @click="onRowDel(scope.row)">
								<el-icon><ele-Delete /></el-icon>
								删除
							</el-button>
						</div>
					</template>
				</el-table-column>
			</el-table>
			
			<!-- 分页 -->
			<el-pagination 
				@size-change="onHandleSizeChange" 
				@current-change="onHandleCurrentChange" 
				class="mt15 history-pagination workbench-pagination"
				:pager-count="5" 
				:page-sizes="[10, 20, 30, 50]" 
				v-model:current-page="state.tableData.param.pageNum"
				background 
				v-model:page-size="state.tableData.param.pageSize"
				:layout="state.tableData.total > 0 ? 'total, sizes, prev, pager, next, jumper' : ''" 
				:total="state.tableData.total"
				:hide-on-single-page="state.tableData.total <= state.tableData.param.pageSize">
			</el-pagination>
			
			<!-- 空数据提示 -->
			<el-empty v-if="state.tableData.data.length === 0 && !state.tableData.loading" class="history-empty"
				description="暂无摄像头检测记录" :image-size="200">
				<template #image>
					<el-icon size="100" color="#c0c4cc">
						<ele-VideoCamera />
					</el-icon>
				</template>
				<el-button type="primary" @click="goToCameraPredict">前往摄像头检测</el-button>
			</el-empty>
			
			<!-- 视频预览对话框 -->
			<el-dialog v-model="state.dialog.visible" :title="state.dialog.title" width="70%">
				<div class="video-dialog">
					<video v-if="state.dialog.videoUrl" controls autoplay style="width: 100%;">
						<source :src="state.dialog.videoUrl" type="video/mp4" />
					</video>
					<div v-else class="no-video">视频加载中...</div>
				</div>
				<template #footer>
					<span class="dialog-footer">
						<el-button @click="state.dialog.visible = false">关闭</el-button>
					</span>
				</template>
			</el-dialog>
		</div>
	</div>
</template>

<script setup lang="ts" name="systemRole">
import { reactive, onMounted, ref } from 'vue';
import { ElMessageBox, ElMessage } from 'element-plus';
import { 
	Search, 
	Refresh, 
	Delete, 
	VideoPlay, 
	VideoCamera 
} from '@element-plus/icons-vue';
import { useRouter } from 'vue-router';
import request from '@/utils/request';
import { useUserInfo } from '@/utils/stores/userInfo';
import { storeToRefs } from 'pinia';

const router = useRouter();
const stores = useUserInfo();
const { userInfos } = storeToRefs(stores);

// 唯一标识符，动态刷新
const uniqueKey = ref(0);

const state = reactive({
	tableData: {
		data: [] as any[],
		total: 0,
		loading: false,
		param: {
			search1: '', // 用户名搜索
			search2: '', // 置信度阈值搜索
			pageNum: 1,
			pageSize: 10,
		},
	},
	stats: {
		totalRecords: 0,
		todayRecords: 0,
		userRecords: 0,
		totalDuration: 0,
	},
	dialog: {
		visible: false,
		title: '视频预览',
		videoUrl: '',
	},
});

// 获取视频URL
const getVideoUrl = (videoPath: string) => {
	if (!videoPath) return '';
	
	// 如果已经是完整URL，直接返回
	if (videoPath.startsWith('http')) {
		return videoPath;
	}
	
	// 历史绝对路径兼容处理
	if (videoPath.includes(':/') || videoPath.includes(':\\')) {
		const normalized = videoPath.replace(/\\/g, '/');
		const uploadsIndex = normalized.indexOf('/uploads/');
		const resultsIndex = normalized.indexOf('/results/');
		const runsIndex = normalized.indexOf('/runs/');
		if (uploadsIndex !== -1) return normalized.substring(uploadsIndex);
		if (resultsIndex !== -1) return normalized.substring(resultsIndex);
		if (runsIndex !== -1) return normalized.substring(runsIndex);
		return `/${normalized}`;
	}

	// 如果是相对路径，直接返回
	if (videoPath.startsWith('/')) {
		return videoPath;
	}

	return `/${videoPath}`;
};

const parseUtcToDate = (value: string): Date | null => {
	if (!value) return null;
	const normalized = value.includes('T') ? value : value.replace(' ', 'T');
	const hasTimezone = /Z$|[+-]\d{2}:?\d{2}$/.test(normalized);
	const date = new Date(hasTimezone ? normalized : `${normalized}Z`);
	return isNaN(date.getTime()) ? null : date;
};

const formatChinaDateTime = (value: string) => {
	const date = parseUtcToDate(value);
	if (!date) return value || '--';
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
};


// 格式化日期（仅日期部分）
const formatDate = (dateStr: string) => {
	if (!dateStr) return '';
	const formatted = formatChinaDateTime(dateStr);
	return formatted.split(' ')[0] || formatted;
};

// ----- 新增通用时间格式化函数 -----
// 处理显示最近时间、昨天和日期+时间的逻辑
const formatDateTime = (dateString: string) => {
	if (!dateString) return '--';
	return formatChinaDateTime(dateString);
};

// 根据置信度返回标签样式
const getConfTagType = (conf: number) => {
    if (conf >= 0.8) return 'success';
    if (conf >= 0.5) return 'warning';
    return 'danger';
};

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
		const confValue = parseFloat(state.tableData.param.search2);
		if (!isNaN(confValue)) {
			params.conf = confValue / 100; // 转换为0-1范围
		}
	}
	
	// 如果不是管理员，只显示当前用户的记录
	if (userInfos.value.userName !== 'admin') {
		params.username = userInfos.value.userName;
	}
	
	console.log('查询摄像头记录参数:', params);
	
	// 请求Flask服务的摄像头记录接口
	request.get('/flask/camera_records', { params })
		.then((res) => {
			console.log('获取摄像头记录响应:', res);
			if (res.status === 200 || res.code === 200) {
				const data = res.data || res;
				state.tableData.total = data.total || 0;
				// 修复：正确填充表格数据，兼容字段
				if (data.records && Array.isArray(data.records)) {
					state.tableData.data = data.records.map((record: any, idx: number) => ({
						...record,
						num: idx + 1 + (state.tableData.param.pageNum - 1) * state.tableData.param.pageSize,
						created_at: record.created_at || record.createdAt,
						start_time: record.start_time || record.startTime,
						out_video: record.out_video || record.outVideo,
						username: record.username,
						conf: record.conf,
					}));
				} else {
					state.tableData.data = [];
				}
				updateStats();
				uniqueKey.value++;
				ElMessage.success(`获取到 ${state.tableData.data.length} 条记录`);
			} else {
				state.tableData.data = [];
				state.tableData.total = 0;
				ElMessage.error((res && res.data && res.data.message) || res.message || '获取记录失败');
			}
		})
		.catch((error) => {
			console.error('获取摄像头记录失败:', error);
			ElMessage.error('获取记录失败，请检查Flask服务');
		})
		.finally(() => {
			state.tableData.loading = false;
		});
};

// 更新统计信息
const updateStats = () => {
	// 这里可以添加统计信息的计算逻辑
	state.stats.totalRecords = state.tableData.total;
	state.stats.userRecords = state.tableData.data.length;
	
	// 计算今日记录数
	const today = new Date().toLocaleDateString('zh-CN');
	const todayCount = state.tableData.data.filter(record => {
		const recordDate = formatDate(record.start_time);
		return recordDate === today;
	}).length;
	state.stats.todayRecords = todayCount;
	
	// 这里可以添加总检测时长的计算（如果有相关数据）
	state.stats.totalDuration = state.tableData.data.length * 10; // 假设每条记录10秒
};

// 重置搜索
const resetSearch = () => {
	state.tableData.param.search1 = '';
	state.tableData.param.search2 = '';
	state.tableData.param.pageNum = 1;
	getTableData();
};

// 预览视频
const previewVideo = (row: any) => {
	state.dialog.videoUrl = getVideoUrl(row.out_video);
	state.dialog.title = `视频预览 - ${row.username} - ${formatDateTime(row.start_time)}`;
	state.dialog.visible = true;
};

// 删除记录
const onRowDel = (row: any) => {
	ElMessageBox.confirm(`此操作将永久删除该摄像头检测记录，是否继续?`, '提示', {
		confirmButtonText: '确认',
		cancelButtonText: '取消',
		type: 'warning',
	})
		.then(() => {
			console.log('删除记录:', row);
			
			request.delete(`/flask/camera_records/${row.id}`)
				.then((res) => {
					console.log('删除响应:', res);
					
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
					console.error('删除失败:', error);
					ElMessage.error('删除失败，请检查Flask服务');
				});
		})
		.catch(() => { });
};

// 前往摄像头检测页面
const goToCameraPredict = () => {
	router.push('/cameraPredict');
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
		height: 100%;
		display: flex;
		flex-direction: column;
		overflow: auto;
	}
}

.history-title-row {
	width: 100%;
	display: flex;
	align-items: center;
}

.history-title {
	color: var(--app-text-1);
}

.history-subtitle {
	color: var(--app-text-2);
}

.system-user-search {
	display: flex;
	align-items: center;
	flex-wrap: wrap;
	gap: 15px;
	padding: 14px;
	
	.el-input {
		flex: 1;
		min-width: 200px;
	}
}

.action-card {
	background: transparent;
}

.stats-row {
	margin-bottom: 4px;
	
	.el-col {
		display: flex;
		justify-content: center;
	}
	
	:deep(.el-statistic) {
		background: #fff;
		padding: 16px;
		border-radius: 12px;
		border: 1px solid #e5e7eb;
		box-shadow: 0 8px 24px rgba(17, 24, 39, 0.06);
		text-align: center;
		width: 100%;
		
		.el-statistic__number {
			font-size: 22px;
			font-weight: bold;
			color: #4338ca;
		}
	}
}

.video-container {
	display: flex;
	flex-direction: column;
	gap: 8px;
	padding: 8px;
	background: #f8f9fa;
	border-radius: 8px;
	border: 1px solid #e9ecef;
	
	.video-preview {
		width: 100%;
		height: 112px;
		border-radius: 6px;
		background: #000;
		object-fit: cover;
		
		&:hover {
			transform: scale(1.02);
			transition: transform 0.3s ease;
		}
	}
	
	.video-info {
		display: flex;
		justify-content: space-between;
		align-items: center;
		
		.video-time {
			font-size: 12px;
			color: #666;
		}
	}
}

.action-buttons {
	display: flex;
	justify-content: center;
	gap: 8px;
	
	.el-button {
		padding: 4px 8px;
	}
}

.video-dialog {
	min-height: 400px;
	display: flex;
	justify-content: center;
	align-items: center;
	background: #000;
	border-radius: 8px;
	overflow: hidden;
	
	video {
		max-height: 70vh;
	}
	
	.no-video {
		color: white;
		font-size: 18px;
	}
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
	
	:deep(.el-table__row) {
		&:hover {
			background-color: #eef2ff;
		}
	}
	
	:deep(.el-table__cell) {
		padding: 12px 0;
	}
}

.history-pagination {
	padding: 8px 0 2px;
}

.history-empty {
	padding: 16px 0 8px;
}

// 响应式适配
@media (max-width: 992px) {
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
	
	.stats-row {
		.el-col {
			margin-bottom: 15px;
			
			&:last-child {
				margin-bottom: 0;
			}
		}
	}
	
	.video-container {
		.video-preview {
			height: 96px;
		}
	}
}

@media (max-width: 768px) {
	:deep(.system-role-padding) {
		padding: 15px;
	}
	
	.history-table {
		:deep(.el-table__cell) {
			padding: 8px 0;
		}
	}
}
</style>
