<template>
	<div class="system-role-container layout-padding">
		<div class="system-role-padding layout-padding-auto layout-padding-view">
			<div class="system-user-search mb15">
				<el-input v-model="state.tableData.param.search1" size="default" placeholder="请输入用户名" style="max-width: 180px"> </el-input>
				<el-input v-model="state.tableData.param.search3" size="default" placeholder="请输入最低置信度阈值" style="max-width: 180px; margin-left: 15px"></el-input>
				<el-button size="default" type="primary" class="ml10" @click="getTableData()">
					<el-icon>
						<ele-Search />
					</el-icon>
					查询
				</el-button>
				<el-button size="default" type="success" class="ml10" @click="refreshTableData()">
					<el-icon>
						<ele-Refresh />
					</el-icon>
					刷新
				</el-button>
			</div>
			
			<!-- 状态提示 -->
			<el-alert
				v-if="statusMessage"
				:title="statusMessage"
				:type="statusType"
				show-icon
				closable
				@close="statusMessage = ''"
				style="margin-bottom: 15px;"
			/>
			
			<el-table :data="state.tableData.data" v-loading="state.tableData.loading" style="width: 100%">
				<el-table-column prop="num" label="序号" width="100" align="center" />
				<el-table-column prop="input_video" label="原视频" width="200" align="center">
					<template #default="scope">
						<div v-if="scope.row.input_video">
							<video 
								class="video" 
								controls 
								preload="metadata" 
								:poster="getVideoPoster(scope.row.input_video)"
								:key="scope.row.input_video + uniqueKey"
								@error="onVideoError(scope.row.input_video, '原视频')"
							>
								<source :src="getVideoUrl(scope.row.input_video)" type="video/mp4" />
								您的浏览器不支持视频播放
							</video>
							<div class="video-info">
								<el-tag size="small" type="info" style="margin-top: 5px;">原始视频</el-tag>
							</div>
						</div>
						<span v-else class="empty-tag">无原始视频</span>
					</template>
				</el-table-column>
				<el-table-column prop="out_video" label="处理结果" width="200" align="center">
					<template #default="scope">
						<div v-if="scope.row.out_video">
							<video 
								class="video" 
								controls 
								preload="metadata" 
								:poster="getVideoPoster(scope.row.out_video)"
								:key="scope.row.out_video + uniqueKey"
								@error="onVideoError(scope.row.out_video, '结果视频')"
							>
								<source :src="getVideoUrl(scope.row.out_video)" type="video/mp4" />
								您的浏览器不支持视频播放
							</video>
							<div class="video-info">
								<el-tag size="small" type="success" style="margin-top: 5px;">检测结果</el-tag>
							</div>
						</div>
						<span v-else class="empty-tag">无结果视频</span>
					</template>
				</el-table-column>
				<el-table-column prop="username" label="识别用户" show-overflow-tooltip align="center"></el-table-column>
				<el-table-column prop="conf" label="置信度阈值" show-overflow-tooltip width="120" align="center">
					<template #default="{ row }">
						<el-tag size="small" :type="getConfTagType(row.conf)">
							{{ (row.conf * 100).toFixed(0) }}%
						</el-tag>
					</template>
				</el-table-column>
				<el-table-column prop="start_time" label="识别时间" width="180" align="center">
					<template #default="{ row }">
						<el-tooltip :content="row.start_time" placement="top">
							<span>{{ formatDate(row.start_time) }}</span>
						</el-tooltip>
					</template>
				</el-table-column>
				<el-table-column prop="created_at" label="创建时间" width="180" align="center">
					<template #default="{ row }">
				<!-- 格式化显示，并强制显示占位符 -->
				<span>{{ formatDateTime(row.created_at || row.createdAt) || '--' }}</span>
					<!-- 调试标记 -->
					<span style="font-size:10px;color:#bbb;">[{{row.created_at}}|{{row.createdAt}}]</span>
					</template>
				</el-table-column>
				<el-table-column label="操作" width="180" align="center" fixed="right">
					<template #default="scope">
						<el-button-group>
							<el-button size="small" type="primary" @click="onRowDel(scope.row)" plain>删除</el-button>
							<el-button size="small" type="success" @click="showVideoDetail(scope.row)" plain>详情</el-button>
						</el-button-group>
					</template>
				</el-table-column>
			</el-table>
			
			<!-- 分页 -->
			<el-pagination 
				@size-change="onHandleSizeChange" 
				@current-change="onHandleCurrentChange" 
				class="mt15"
				:pager-count="5" 
				:page-sizes="[5, 10, 20, 30]" 
				v-model:current-page="state.tableData.param.pageNum"
				background 
				v-model:page-size="state.tableData.param.pageSize"
				:layout="state.tableData.total > 0 ? 'total, sizes, prev, pager, next, jumper' : ''" 
				:total="state.tableData.total"
				:hide-on-single-page="state.tableData.total <= state.tableData.param.pageSize"
				:disabled="state.tableData.loading"
			></el-pagination>
			
			<!-- 空数据提示 -->
			<el-empty 
				v-if="state.tableData.data.length === 0 && !state.tableData.loading" 
				description="暂无视频检测记录" 
				:image-size="200"
			>
				<template #image>
					<el-icon size="100" color="#c0c4cc">
						<ele-VideoCamera />
					</el-icon>
				</template>
				<template #description>
					<p style="margin-bottom: 10px; color: #909399;">还没有视频检测记录</p>
					<p style="font-size: 14px; color: #c0c4cc;">去 <router-link to="/videoPredict" style="color: #409eff;">视频检测页面</router-link> 进行检测吧</p>
				</template>
			</el-empty>
		</div>
	</div>
</template>

<script setup lang="ts" name="videoRecord">
import { reactive, ref, onMounted, computed, nextTick } from 'vue';
import { ElMessageBox, ElMessage } from 'element-plus';
import { Search, Refresh, VideoCamera } from '@element-plus/icons-vue';
import request from '/@/utils/request';
import { useUserInfo } from '/@/stores/userInfo';
import { storeToRefs } from 'pinia';
import { useRouter } from 'vue-router';

// 路由
const router = useRouter();

// 用户信息
const stores = useUserInfo();
const { userInfos } = storeToRefs(stores);

// 状态管理
const uniqueKey = ref(0);
const statusMessage = ref('');
const statusType = ref('info');

// 自动获取当前页面IP，解决跨域问题
const currentHost = window.location.hostname;

// 表格数据
const state = reactive({
	tableData: {
		data: [] as any[],
		total: 0,
		loading: false,
		param: {
			search1: '', // 用户名搜索
			search3: '', // 置信度阈值搜索
			pageNum: 1,
			pageSize: 10,
		},
	},
});

// 获取视频URL（处理跨域和路径问题）
// 改进的视频URL获取函数
const getVideoUrl = (videoPath: string): string => {
  if (!videoPath) return '';
  
  console.log('原始视频路径:', videoPath);
  
  // 1. 如果是完整的HTTP/HTTPS URL，直接返回
  if (videoPath.startsWith('http://') || videoPath.startsWith('https://')) {
    return videoPath;
  }
  
  // 2. 处理Windows绝对路径
  if (videoPath.includes('D:/') || videoPath.includes('d:/') || videoPath.includes('D:\\') || videoPath.includes('d:\\')) {
    // 提取uploads/results之后的部分
    const normalized = videoPath.replace(/\\/g, '/');
    
    const uploadsIndex = normalized.indexOf('/uploads/');
    const resultsIndex = normalized.indexOf('/results/');
    const runsIndex = normalized.indexOf('/runs/');
    
    if (uploadsIndex !== -1) {
      const relativePath = normalized.substring(uploadsIndex);
      return `http://${currentHost}:5000${relativePath}`;
    }
    if (resultsIndex !== -1) {
      const relativePath = normalized.substring(resultsIndex);
      return `http://${currentHost}:5000${relativePath}`;
    }
    if (runsIndex !== -1) {
      const relativePath = normalized.substring(runsIndex);
      return `http://${currentHost}:5000${relativePath}`;
    }
    
    // 尝试直接返回，让代理处理
    return `http://${currentHost}:5000/${normalized}`;
  }
  
  // 3. 处理相对路径
  if (videoPath.startsWith('/')) {
    return `http://${currentHost}:5000${videoPath}`;
  }
  
  // 4. 默认添加基础路径
  return `http://${currentHost}:5000/${videoPath}`;
};

const getVideoPoster = (videoPath: string) => {
	// 这里可以替换为实际的封面图生成逻辑
	// 暂时返回空，浏览器会自动生成
	return '';
};

// 格式化日期
const formatDate = (dateString: string) => {
	if (!dateString) return '--';
	
	try {
		const date = new Date(dateString);
		if (isNaN(date.getTime())) {
			// 解析失败，返回原始字符串
			return dateString || '--';
		}
		const now = new Date();
		const diffTime = Math.abs(now.getTime() - date.getTime());
		const diffDays = Math.floor(diffTime / (1000 * 60 * 60 * 24));
		
		// 如果是今天，只显示时间
		if (diffDays === 0) {
			return date.toLocaleTimeString('zh-CN', { 
				hour: '2-digit', 
				minute: '2-digit',
				second: '2-digit'
			});
		}
		
		// 如果是昨天
		if (diffDays === 1) {
			return '昨天 ' + date.toLocaleTimeString('zh-CN', { 
				hour: '2-digit', 
				minute: '2-digit'
			});
		}
		
		// 其他情况显示日期和时间
		return date.toLocaleDateString('zh-CN', { 
			month: '2-digit', 
			day: '2-digit'
		}) + ' ' + date.toLocaleTimeString('zh-CN', { 
			hour: '2-digit', 
			minute: '2-digit'
		});
	} catch (error) {
		console.error('日期格式化失败:', error);
		return dateString || '--';
	}
};

// 通用格式化日期时间（和 cameraRecord 共用逻辑）
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
		console.error('日期格式化失败:', error);
		return dateString || '--';
	}
};
// 获取置信度标签类型
const getConfTagType = (conf: number) => {
	if (conf >= 0.7) return 'danger';     // 高阈值：红色
	if (conf >= 0.5) return 'warning';    // 中阈值：黄色
	return 'success';                      // 低阈值：绿色
};

// 视频加载错误处理
const onVideoError = (videoUrl: string, videoType: string) => {
	console.error(`${videoType}加载失败:`, videoUrl);
	
	// 可以在这里添加重试逻辑或显示替代内容
	if (videoType === '结果视频' && videoUrl) {
		// 尝试重新加载
		setTimeout(() => {
			uniqueKey.value++;
		}, 1000);
	}
};

// 刷新表格数据
const refreshTableData = () => {
	uniqueKey.value++;
	getTableData();
	ElMessage.success('数据已刷新');
};

// 获取表格数据
const getTableData = () => {
	state.tableData.loading = true;
	statusMessage.value = '';
	
	// 构建查询参数
	const params: any = {
		page: state.tableData.param.pageNum,
		page_size: state.tableData.param.pageSize,
	};
	
	// 添加搜索条件
	if (state.tableData.param.search1) {
		params.username = state.tableData.param.search1;
	}
	
	if (state.tableData.param.search3) {
		const confValue = parseFloat(state.tableData.param.search3);
		if (!isNaN(confValue)) {
			params.conf = confValue / 100; // 转换为0-1范围
		}
	}
	
	// 如果不是管理员，只显示当前用户的记录
	if (userInfos.value.userName !== 'admin') {
		params.username = userInfos.value.userName;
	}
	
	console.log('查询视频记录参数:', params);
	
	// 请求Flask服务的视频记录接口
	request.get('/flask/video_records', { params })
		.then((res) => {
			console.log('获取视频记录响应:', res);
			const data = res.data || res;
			
			if (res.status === 200 || res.code === 200) {
				
				state.tableData.data = [];
				state.tableData.total = data.total || 0;
				
				// 处理每一条记录
				if (data.records && Array.isArray(data.records)) {
					data.records.forEach((record: any, index: number) => {
						// 计算创建时间值并打印调试
						const createdVal = record.created_at ?? record.createdAt ?? '';
						console.log('video record raw', record, 'mapped created_at', createdVal);
						// 修复：先声明recordData变量，再赋值
						const recordData = {
							id: record.id,
							num: (state.tableData.param.pageNum - 1) * state.tableData.param.pageSize + index + 1,
							input_video: record.input_video || record.inputVideo,
							out_video: record.out_video || record.outVideo,
							conf: record.conf || 0.5,
							start_time: record.start_time || record.startTime,
							username: record.username,
							created_at: createdVal,
						}; // 修复：闭合recordData对象的大括号
						// 修复：push语句移到对象外部
						state.tableData.data.push(recordData);
					});
				}
				
				if (state.tableData.data.length === 0) {
					statusMessage.value = '没有找到匹配的视频检测记录';
					statusType.value = 'info';
				} else {
					statusMessage.value = `已加载 ${state.tableData.data.length} 条视频检测记录`;
					statusType.value = 'success';
				}
			} else {
				statusMessage.value = data.message || '获取记录失败';
				statusType.value = 'error';
				ElMessage.error(statusMessage.value);
			}
		})
		.catch((error) => {
			console.error('获取视频记录失败:', error);
			statusMessage.value = '获取记录失败，请检查Flask服务';
			statusType.value = 'error';
			ElMessage.error(statusMessage.value);
		})
		.finally(() => {
			state.tableData.loading = false;
		});
};

// 删除记录
const onRowDel = (row: any) => {
	ElMessageBox.confirm(
		`确定要永久删除这条视频检测记录吗？`,
		'删除确认',
		{
			confirmButtonText: '确定删除',
			cancelButtonText: '取消',
			type: 'warning',
			dangerouslyUseHTMLString: false,
			distinguishCancelAndClose: true,
			lockScroll: false,
			beforeClose: (action, instance, done) => {
				if (action === 'confirm') {
					instance.confirmButtonLoading = true;
					instance.confirmButtonText = '删除中...';
					
					request.delete(`/flask/video_records/${row.id}`)
						.then((res) => {
							console.log('删除响应:', res);
							
							if (res.code === 200 || res.status === 200) {
								ElMessage.success('删除成功！');
								done();
								
								// 重新获取数据
								setTimeout(() => {
									getTableData();
								}, 500);
							} else {
								ElMessage.error(res.message || '删除失败');
								done();
							}
						})
						.catch((error) => {
							console.error('删除失败:', error);
							ElMessage.error('删除失败，请检查Flask服务');
							done();
						})
						.finally(() => {
							instance.confirmButtonLoading = false;
						});
				} else {
					done();
				}
			}
		}
	).catch(() => {
		// 用户取消操作
	});
};

// 查看视频详情
const showVideoDetail = (row: any) => {
	const detailContent = `
		<div style="line-height: 1.8;">
			<p><strong>用户：</strong>${row.username}</p>
			<p><strong>置信度阈值：</strong>${(row.conf * 100).toFixed(0)}%</p>
			<p><strong>检测时间：</strong>${row.start_time}</p>
			<p><strong>创建时间：</strong>${row.created_at || '未知'}</p>
			<p><strong>原始视频：</strong>${row.input_video ? '✓ 已上传' : '✗ 无'}</p>
			<p><strong>检测结果：</strong>${row.out_video ? '✓ 已生成' : '✗ 无'}</p>
		</div>
	`;
	
	ElMessageBox.alert(detailContent, '视频检测详情', {
		confirmButtonText: '关闭',
		dangerouslyUseHTMLString: true,
		customClass: 'video-detail-dialog',
	});
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
	background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);

	.system-role-padding {
		padding: 15px;
		height: 100%;
		display: flex;
		flex-direction: column;
	}
}

.system-user-search {
	display: flex;
	align-items: center;
	flex-wrap: wrap;
	gap: 10px;
	padding: 15px;
	background: white;
	border-radius: 8px;
	box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
	margin-bottom: 20px;
	
	.el-input {
		flex: 1;
		min-width: 200px;
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
	border-radius: 8px;
	overflow: hidden;
	box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
	
	:deep(.el-table__row) {
		&:hover {
			background-color: #f5f7fa;
		}
	}
	
	:deep(.el-table__cell) {
		padding: 12px 0;
	}
}

.video {
	width: 100%;
	height: 120px;
	object-fit: cover;
	border-radius: 4px;
	background: #000;
	border: 1px solid #e0e0e0;
	transition: transform 0.3s ease, box-shadow 0.3s ease;
	
	&:hover {
		transform: scale(1.02);
		box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
	}
}

.video-info {
	display: flex;
	justify-content: center;
	align-items: center;
	margin-top: 5px;
}

.empty-tag {
	color: #909399;
	font-size: 12px;
	font-style: italic;
}

// 详情对话框样式
:deep(.video-detail-dialog) {
	.el-message-box__content {
		padding: 15px 20px;
	}
	
	.el-message-box__title {
		font-size: 18px;
		font-weight: 600;
		color: #333;
	}
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
	
	.el-table {
		:deep(.el-table__cell) {
			padding: 8px 0;
		}
		
		:deep(.video) {
			height: 80px;
		}
	}
}

@media (max-width: 992px) {
	.video {
		height: 100px;
	}
}
</style>