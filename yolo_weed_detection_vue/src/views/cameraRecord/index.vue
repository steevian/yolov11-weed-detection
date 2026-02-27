<template>
	<div class="system-role-container layout-padding">
		<div class="system-role-padding layout-padding-auto layout-padding-view">
			<div class="system-user-search mb15">
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
			<el-row :gutter="20" class="stats-row">
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
			
			<el-table :data="state.tableData.data" v-loading="state.tableData.loading" style="width: 100%; margin-top: 20px;">
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
				class="mt15"
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
			<el-empty v-if="state.tableData.data.length === 0 && !state.tableData.loading" 
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
import { reactive, onMounted, ref, computed } from 'vue';
import { ElMessageBox, ElMessage } from 'element-plus';
import { 
	Search, 
	Refresh, 
	Delete, 
	VideoPlay, 
	VideoCamera 
} from '@element-plus/icons-vue';
import { useRouter } from 'vue-router';
import request from '/@/utils/request';
import { useUserInfo } from '/@/stores/userInfo';
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

// 获取当前主机地址
const currentHost = computed(() => window.location.hostname);

// 获取视频URL
const getVideoUrl = (videoPath: string) => {
	if (!videoPath) return '';
	
	// 如果已经是完整URL，直接返回
	if (videoPath.startsWith('http')) {
		return videoPath;
	}
	
	// 如果是相对路径，添加主机和端口
	if (videoPath.startsWith('/')) {
		return `http://${currentHost.value}:5000${videoPath}`;
	}
	
	return videoPath;
};


// 格式化日期（仅日期部分）
const formatDate = (dateStr: string) => {
	if (!dateStr) return '';
	
	try {
		const date = new Date(dateStr);
		return date.toLocaleDateString('zh-CN');
	} catch (error) {
		return dateStr;
	}
};

// ----- 新增通用时间格式化函数 -----
// 处理显示最近时间、昨天和日期+时间的逻辑
const formatDateTime = (dateString: string) => {
	if (!dateString) return '--';
	try {
		const date = new Date(dateString);
		if (isNaN(date.getTime())) {
			return dateString || '--';
		}
		const now = new Date();
		const diffTime = Math.abs(now.getTime() - date.getTime());
		const diffDays = Math.floor(diffTime / (1000 * 60 * 60 * 24));
		if (diffDays === 0) {
			return date.toLocaleTimeString('zh-CN', {
				hour: '2-digit',
				minute: '2-digit',
				second: '2-digit'
			});
		}
		if (diffDays === 1) {
			return '昨天 ' + date.toLocaleTimeString('zh-CN', {
				hour: '2-digit',
				minute: '2-digit'
			});
		}
		return date.toLocaleDateString('zh-CN', {
			month: '2-digit',
			day: '2-digit'
		}) + ' ' + date.toLocaleTimeString('zh-CN', {
			hour: '2-digit',
			minute: '2-digit'
		});
	} catch (error) {
		console.error('formatDateTime error', error);
		return dateString || '--';
	}
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
	height: 100vh;
	display: flex;
	flex-direction: column;

	.system-role-padding {
		padding: 20px;
		height: 100%;
		display: flex;
		flex-direction: column;
		background: linear-gradient(135deg, #f5f7fa 0%, #e4efe9 100%);
	}
}

.system-user-search {
	display: flex;
	align-items: center;
	flex-wrap: wrap;
	gap: 15px;
	padding: 20px;
	background: white;
	border-radius: 10px;
	box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
	margin-bottom: 20px;
	
	.el-input {
		flex: 1;
		min-width: 200px;
	}
}

.stats-row {
	margin-bottom: 20px;
	
	.el-col {
		display: flex;
		justify-content: center;
	}
	
	:deep(.el-statistic) {
		background: white;
		padding: 20px;
		border-radius: 10px;
		box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
		text-align: center;
		width: 100%;
		
		.el-statistic__number {
			font-size: 24px;
			font-weight: bold;
			color: #409eff;
		}
	}
}

.video-container {
	display: flex;
	flex-direction: column;
	gap: 8px;
	padding: 10px;
	background: #f8f9fa;
	border-radius: 8px;
	border: 1px solid #e9ecef;
	
	.video-preview {
		width: 100%;
		height: 120px;
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

.el-table {
	flex: 1;
	background: white;
	border-radius: 10px;
	overflow: hidden;
	box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
	
	:deep(.el-table__row) {
		&:hover {
			background-color: #f8f9fa;
		}
	}
	
	:deep(.el-table__cell) {
		padding: 12px 0;
	}
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
			height: 100px;
		}
	}
}

@media (max-width: 768px) {
	.system-role-padding {
		padding: 15px;
	}
	
	.el-table {
		:deep(.el-table__cell) {
			padding: 8px 0;
		}
	}
}
</style>