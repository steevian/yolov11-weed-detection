html, body, #app {
	margin-top: 0 !important;
	padding-top: 0 !important;
}

.dashboard-container, .dashboard-inner, .top-strip {
	margin-top: 0 !important;
	padding-top: 0 !important;
}

.dashboard-container {
	padding-top: 0 !important;
	margin-top: 0 !important;
}

.dashboard-inner {
	padding-top: 0 !important;
	margin-top: 0 !important;
}

.top-strip {
	padding-top: 0 !important;
	margin-top: 0 !important;
	margin-bottom: 18px;
}
<template>
	<div class="dashboard-container layout-padding">
		<div class="dashboard-inner layout-padding-auto">
			<section class="top-strip dashboard-card">
				<div class="fake-search" @click="onWorkbenchSearchClick">
					<el-icon><ele-Search /></el-icon>
					<span>Search...</span>
				</div>
				<div class="top-actions">
					<User ref="workbenchUserRef" class="workbench-toolbar" />
				</div>
			</section>

			<section class="hero-card dashboard-card">
				<div class="hero-text">
					<h2>YOLOv11 杂草检测工作台</h2>
					<p>统一入口 · 快速检测 · 数据可视</p>
				</div>
				<div class="hero-actions">
					<el-button type="primary" @click="goTo('/imgPredict')">
						<el-icon><ele-PictureFilled /></el-icon>
						图像检测
					</el-button>
					<el-button @click="goTo('/videoPredict')">
						<el-icon><ele-VideoPlay /></el-icon>
						视频检测
					</el-button>
				</div>
			</section>

			<section class="stats-grid">
				<article class="dashboard-card stat-item stat-purple">
					<div class="stat-label">活跃用户</div>
					<div class="stat-value">{{ stats.activeUsers }}</div>
					<div class="stat-foot">系统用户总数</div>
				</article>
				<article class="dashboard-card stat-item stat-blue">
					<div class="stat-label">检测总量</div>
					<div class="stat-value">{{ stats.totalDetections }}</div>
					<div class="stat-foot">图像 + 视频 + 摄像</div>
				</article>
				<article class="dashboard-card stat-item stat-yellow">
					<div class="stat-label">图像检测记录</div>
					<div class="stat-value">{{ stats.imageDetections }}</div>
					<div class="stat-foot">累计记录数</div>
				</article>
				<article class="dashboard-card stat-item stat-dark">
					<div class="stat-label">视频检测记录</div>
					<div class="stat-value">{{ stats.videoDetections }}</div>
					<div class="stat-foot">累计记录数</div>
				</article>
			</section>

			<section class="panel-grid">
				<article class="dashboard-card panel-card">
					<div class="panel-title">快捷入口</div>
					<div class="quick-grid">
						<button class="quick-item" @click="goTo('/imgPredict')">
							<el-icon><ele-Picture /></el-icon>
							<span>图像检测</span>
						</button>
						<button class="quick-item" @click="goTo('/videoPredict')">
							<el-icon><ele-Film /></el-icon>
							<span>视频检测</span>
						</button>
						<button class="quick-item" @click="goTo('/imgRecord')">
							<el-icon><ele-DataAnalysis /></el-icon>
							<span>图像检测记录</span>
						</button>
						<button v-if="isAdmin" class="quick-item" @click="goTo('/usermanage')">
							<el-icon><ele-UserFilled /></el-icon>
							<span>用户管理</span>
						</button>
					</div>
				</article>

				<article class="dashboard-card panel-card">
					<div class="panel-title">最近检测记录</div>
					<el-table :data="recentRecords" size="small" class="record-table" v-loading="loading">
						<el-table-column prop="type" label="类型" width="120" />
						<el-table-column prop="username" label="用户" width="120" />
						<el-table-column prop="created_at" label="时间" min-width="170" />
						<el-table-column prop="summary" label="检测结果" min-width="180" show-overflow-tooltip />
					</el-table>
				</article>
			</section>
		</div>
	</div>
</template>

<script setup lang="ts" name="dashboardIndex">
import { defineAsyncComponent, onMounted, reactive, ref } from 'vue';
import { useRouter } from 'vue-router';
import request from '@/utils/request';
import { useUserInfo } from '@/utils/stores/userInfo';

const User = defineAsyncComponent(() => import('@/components/layout/navBars/breadcrumb/user.vue'));

interface DashboardRecord {
	type: string;
	username: string;
	created_at: string;
	summary: string;
}

const router = useRouter();
const userInfoStore = useUserInfo();
const loading = ref(false);
const workbenchUserRef = ref<any>(null);
const recentRecords = ref<DashboardRecord[]>([]);
const isAdmin = userInfoStore.userInfos.roles?.includes('admin');

const stats = reactive({
	activeUsers: 0,
	totalDetections: 0,
	imageDetections: 0,
	videoDetections: 0,
	cameraDetections: 0,
});

const getTotal = (response: any) => {
	const payload = response?.data || response || {};
	return Number(payload.total || 0);
};

const normalizeRecord = (record: any, type: string): DashboardRecord => {
	const createdAt = record.created_at || record.createdAt || record.recognition_time || record.start_time || '-';
	const summary = record.label || record.labels || record.detections || '已完成检测';
	return {
		type,
		username: record.username || '-',
		created_at: String(createdAt),
		summary: typeof summary === 'string' ? summary : JSON.stringify(summary),
	};
};

const fetchStats = async () => {
	loading.value = true;
	try {
		const [imgRes, videoRes, cameraRes, userRes] = await Promise.all([
			request.get('/flask/img_records', { params: { pageNum: 1, pageSize: 6 } }),
			request.get('/flask/video_records', { params: { pageNum: 1, pageSize: 6 } }),
			request.get('/flask/camera_records', { params: { pageNum: 1, pageSize: 6 } }),
			request.get('/flask/user', { params: { pageNum: 1, pageSize: 1 } }),
		]);

		stats.imageDetections = getTotal(imgRes);
		stats.videoDetections = getTotal(videoRes);
		stats.cameraDetections = getTotal(cameraRes);
		stats.totalDetections = stats.imageDetections + stats.videoDetections + stats.cameraDetections;
		stats.activeUsers = getTotal(userRes);

		const imgRecords = ((imgRes?.data || imgRes)?.records || []).slice(0, 3).map((item: any) => normalizeRecord(item, '图像'));
		const videoRecords = ((videoRes?.data || videoRes)?.records || []).slice(0, 3).map((item: any) => normalizeRecord(item, '视频'));
		recentRecords.value = [...imgRecords, ...videoRecords].slice(0, 6);
	} finally {
		loading.value = false;
	}
};

const goTo = (path: string) => {
	router.push(path);
};

const onWorkbenchSearchClick = () => {
	workbenchUserRef.value?.openSearch?.();
};

onMounted(() => {
	fetchStats();
});
</script>

<style scoped lang="scss">

.dashboard-container {
	height: 100%;
	overflow: auto;
	margin-top: 0 !important;
	padding-top: 0 !important;
}

.dashboard-inner {
	margin-top: 0 !important;
	padding-top: 0 !important;
}

.top-strip {
	margin-top: 0 !important;
	padding-top: 0 !important;
}

body {
	margin-top: 0 !important;
}


.dashboard-inner {
	display: flex;
	flex-direction: column;
	gap: 14px;
}

.top-strip {
	margin-top: 0 !important;
	padding-top: 0 !important;
	border-top: none !important;
	box-shadow: none !important;
}

body, .dashboard-container {
	margin-top: 0 !important;
	padding-top: 0 !important;
}

.dashboard-container {
	padding-top: 0 !important;
}

/* 去除顶部所有空白，贴顶 */
.dashboard-container, .dashboard-inner, .top-strip {
	margin-top: 0 !important;
	padding-top: 0 !important;
}

/* 保持下方蓝色banner间距正常 */
.top-strip {
	margin-bottom: 18px;
}

/* 圆形按钮间距优化 */

/* 顶部三个小圆按钮间距均匀美观 */
.workbench-toolbar :deep(.layout-navbars-breadcrumb-user-icon) {
	margin-right: 0;
}
.workbench-toolbar :deep(.layout-navbars-breadcrumb-user-icon) {
	/* 默认间距为0，后面用nth-child精确分配 */
}
.workbench-toolbar :deep(.layout-navbars-breadcrumb-user-icon:nth-child(1)),
.workbench-toolbar :deep(.layout-navbars-breadcrumb-user-icon:nth-child(2)),
.workbench-toolbar :deep(.layout-navbars-breadcrumb-user-icon:nth-child(3)) {
	margin-right: 18px;
}
.workbench-toolbar :deep(.layout-navbars-breadcrumb-user-icon:nth-child(4)) {
	margin-right: 0;
}

.dashboard-card {
	border-radius: 18px;
	border: 1px solid rgba(148, 163, 184, 0.22);
	background: linear-gradient(180deg, #ffffff 0%, #fbfcff 100%);
	box-shadow: 0 14px 30px rgba(17, 24, 39, 0.08);
}

.top-strip {
	height: 62px;
	padding: 0 18px;
	display: flex;
	align-items: center;
	justify-content: space-between;
}

.fake-search {
	width: min(360px, 56%);
	height: 40px;
	border-radius: 20px;
	background: #f2f4fb;
	border: 1px solid #e1e5f2;
	display: flex;
	align-items: center;
	gap: 8px;
	padding: 0 14px;
	color: #a1a9bc;
	font-size: 13px;
	cursor: pointer;
}

.top-actions {
	display: inline-flex;
	align-items: center;
	margin-left: auto;
}

.dot {
	width: 28px;
	height: 28px;
	border-radius: 50%;
	background: #f4f6fd;
	border: 1px solid #e2e8f4;
}

.workbench-toolbar {
	:deep(.layout-navbars-breadcrumb-user) {
		padding-right: 0;
		flex: none !important;
		gap: 10px;
	}

	:deep(.layout-navbars-breadcrumb-user-icon) {
		width: 28px;
		height: 28px;
		padding: 0;
		border-radius: 50%;
		background: #f4f6fd;
		border: 1px solid #e2e8f4;
		line-height: 28px;
		justify-content: center;
		color: #556079 !important;
	}

	:deep(.layout-navbars-breadcrumb-user-icon:hover) {
		background: #ebf0fb !important;
	}

	:deep(.toolbar-search-icon) {
		display: none;
	}

	:deep(.layout-navbars-breadcrumb-user-link) {
		height: 38px;
		padding: 0 12px;
		border-radius: 20px;
		background: #f4f6fd;
		border: 1px solid #e2e8f4;
		color: #44506a;
		display: inline-flex;
		align-items: center;
		gap: 6px;
	}

	:deep(.layout-navbars-breadcrumb-user-link-photo) {
		width: 28px;
		height: 28px;
		margin-right: 0 !important;
	}
}

.hero-card {
	padding: 24px;
	display: flex;
	justify-content: space-between;
	align-items: center;
	gap: 16px;
	background: linear-gradient(130deg, #5b3cf0 0%, #4453ff 62%, #6f8dff 100%);
	border-color: rgba(99, 102, 241, 0.42);

	h2 {
		font-size: 24px;
		line-height: 1.25;
		color: #ffffff;
	}

	p {
		margin-top: 6px;
		font-size: 14px;
		color: rgba(237, 239, 255, 0.9);
	}
}

.hero-actions {
	display: flex;
	gap: 10px;
	flex-wrap: wrap;
}

.stats-grid {
	display: grid;
	grid-template-columns: repeat(4, minmax(0, 1fr));
	gap: 12px;
}

.stat-item {
	padding: 16px 18px;
}

.stat-purple {
	background: linear-gradient(145deg, #f2eeff 0%, #e9e5ff 100%);
}

.stat-blue {
	background: linear-gradient(145deg, #eaf2ff 0%, #dfebff 100%);
}

.stat-yellow {
	background: linear-gradient(145deg, #fff8dd 0%, #ffefb5 100%);
}

.stat-dark {
	background: linear-gradient(145deg, #1f2436 0%, #2a2f47 100%);

	.stat-label,
	.stat-value,
	.stat-foot {
		color: #f3f4f6;
	}
}

.stat-label {
	font-size: 13px;
	color: #6b7280;
}

.stat-value {
	margin-top: 8px;
	font-size: 28px;
	font-weight: 700;
	line-height: 1;
	color: #111827;
}

.stat-foot {
	margin-top: 6px;
	font-size: 12px;
	color: #9ca3af;
}

.panel-grid {
	display: grid;
	grid-template-columns: 1fr 2fr;
	gap: 12px;
}

.panel-card {
	padding: 16px;
}

.panel-title {
	font-size: 15px;
	font-weight: 600;
	color: #111827;
	margin-bottom: 12px;
}

.quick-grid {
	display: grid;
	grid-template-columns: repeat(2, minmax(0, 1fr));
	gap: 10px;
}

.quick-item {
	height: 72px;
	border-radius: 12px;
	border: 1px solid #dbe2f2;
	background: #f6f8ff;
	display: flex;
	flex-direction: column;
	align-items: center;
	justify-content: center;
	gap: 6px;
	font-size: 13px;
	color: #111827;
	cursor: pointer;
	transition: all 0.2s ease;

	&:hover {
		transform: translateY(-2px);
		border-color: #aebdff;
		background: #eaf0ff;
	}
}

.record-table {
	:deep(.el-table__inner-wrapper::before) {
		height: 0;
	}
}

@media (max-width: 1200px) {
	.stats-grid {
		grid-template-columns: repeat(2, minmax(0, 1fr));
	}

	.panel-grid {
		grid-template-columns: 1fr;
	}
}

@media (max-width: 768px) {
	.top-strip {
		height: auto;
		padding: 12px;
		flex-direction: column;
		align-items: stretch;
		gap: 10px;
	}

	.fake-search {
		width: 100%;
	}

	.top-actions {
		justify-content: flex-end;
	}

	.hero-card {
		flex-direction: column;
		align-items: flex-start;
	}

	.stats-grid {
		grid-template-columns: 1fr;
	}
}
</style>
