<template>
	<div class="dashboard-container layout-padding">
		<div class="dashboard-inner layout-padding-auto">
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
				<article class="dashboard-card stat-item">
					<div class="stat-label">活跃用户</div>
					<div class="stat-value">{{ stats.activeUsers }}</div>
					<div class="stat-foot">系统用户总数</div>
				</article>
				<article class="dashboard-card stat-item">
					<div class="stat-label">检测总量</div>
					<div class="stat-value">{{ stats.totalDetections }}</div>
					<div class="stat-foot">图像 + 视频 + 摄像</div>
				</article>
				<article class="dashboard-card stat-item">
					<div class="stat-label">图像检测记录</div>
					<div class="stat-value">{{ stats.imageDetections }}</div>
					<div class="stat-foot">累计记录数</div>
				</article>
				<article class="dashboard-card stat-item">
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
import { onMounted, reactive, ref } from 'vue';
import { useRouter } from 'vue-router';
import request from '@/utils/request';
import { useUserInfo } from '@/utils/stores/userInfo';

interface DashboardRecord {
	type: string;
	username: string;
	created_at: string;
	summary: string;
}

const router = useRouter();
const userInfoStore = useUserInfo();
const loading = ref(false);
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

onMounted(() => {
	fetchStats();
});
</script>

<style scoped lang="scss">
.dashboard-container {
	height: 100%;
	overflow: auto;
}

.dashboard-inner {
	display: flex;
	flex-direction: column;
	gap: 16px;
}

.dashboard-card {
	border-radius: 16px;
	border: 1px solid var(--el-border-color-light);
	background: var(--el-bg-color);
	box-shadow: 0 10px 28px rgba(17, 24, 39, 0.06);
}

.hero-card {
	padding: 22px;
	display: flex;
	justify-content: space-between;
	align-items: center;
	gap: 16px;

	h2 {
		font-size: 24px;
		line-height: 1.25;
		color: #111827;
	}

	p {
		margin-top: 6px;
		font-size: 14px;
		color: #6b7280;
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
	border: 1px solid var(--el-border-color-light);
	background: #f9fafb;
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
		border-color: #c7d2fe;
		background: #eef2ff;
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
	.hero-card {
		flex-direction: column;
		align-items: flex-start;
	}

	.stats-grid {
		grid-template-columns: 1fr;
	}
}
</style>
