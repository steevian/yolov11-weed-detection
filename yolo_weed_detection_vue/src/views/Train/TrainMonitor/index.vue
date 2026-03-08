<template>
	<div class="system-role-container layout-padding">
		<div class="system-role-padding layout-padding-auto layout-padding-view workbench-page-body">
			<div class="workbench-title-row">
				<div>
					<h3 class="workbench-title">训练监控</h3>
					<p class="workbench-subtitle">监控杂草检测训练任务进度与核心指标。当前数据为接口占位输出。</p>
				</div>
			</div>

			<el-card class="mb15">
				<el-form inline>
					<el-form-item label="任务">
						<el-select v-model="currentTaskId" placeholder="请选择任务" style="width: 280px" filterable>
							<el-option v-for="item in taskOptions" :key="item.taskId" :label="item.taskName" :value="item.taskId" />
						</el-select>
					</el-form-item>
					<el-form-item>
						<el-checkbox v-model="showMetrics">指标卡</el-checkbox>
						<el-checkbox v-model="showProgress" class="ml10">进度条</el-checkbox>
						<el-checkbox v-model="showEpochTable" class="ml10">轮次表格</el-checkbox>
					</el-form-item>
					<el-form-item>
						<el-button type="primary" @click="loadMonitor">刷新监控</el-button>
					</el-form-item>
				</el-form>
			</el-card>

			<div class="monitor-cards mb15" v-if="showMetrics">
				<el-card>
					<div class="metric-title">训练状态</div>
					<div class="metric-value">{{ overview.status || '-' }}</div>
				</el-card>
				<el-card>
					<div class="metric-title">当前轮次</div>
					<div class="metric-value">{{ overview.currentEpoch || 0 }} / {{ overview.totalEpoch || 0 }}</div>
				</el-card>
				<el-card>
					<div class="metric-title">mAP50</div>
					<div class="metric-value">{{ formatDecimal(overview.map50) }}</div>
				</el-card>
				<el-card>
					<div class="metric-title">Precision</div>
					<div class="metric-value">{{ formatDecimal(overview.precision) }}</div>
				</el-card>
			</div>

			<el-card class="mb15" v-if="showProgress">
				<template #header>
					<span>整体进度</span>
				</template>
				<el-progress :percentage="overview.progress || 0" :stroke-width="18" status="success" />
			</el-card>

			<el-card v-if="showEpochTable">
				<template #header>
					<div class="card-header-row">
						<span>轮次指标</span>
						<el-tag type="warning">placeholder</el-tag>
					</div>
				</template>
				<el-table :data="epochs" v-loading="loading" style="width: 100%">
					<el-table-column prop="epoch" label="Epoch" width="100" />
					<el-table-column prop="loss" label="Loss" min-width="120" />
					<el-table-column prop="precision" label="Precision" min-width="120" />
					<el-table-column prop="recall" label="Recall" min-width="120" />
					<el-table-column prop="map50" label="mAP50" min-width="120" />
				</el-table>
			</el-card>

			<el-card class="mt15">
				<template #header>最近 3 轮快照</template>
				<el-descriptions :column="3" border>
					<el-descriptions-item v-for="item in recentEpochs" :key="item.epoch" :label="`Epoch ${item.epoch}`">
						P {{ formatDecimal(item.precision) }} / R {{ formatDecimal(item.recall) }} / mAP {{ formatDecimal(item.map50) }}
					</el-descriptions-item>
				</el-descriptions>
			</el-card>
		</div>
	</div>
</template>

<script setup lang="ts" name="trainMonitorPage">
import { computed, onMounted, ref } from 'vue';
import { ElMessage } from 'element-plus';
import { useTrainApi } from '@/api/train';

const trainApi = useTrainApi();
const loading = ref(false);
const taskOptions = ref<any[]>([]);
const currentTaskId = ref('');
const overview = ref<Record<string, any>>({});
const epochs = ref<any[]>([]);
const showMetrics = ref(true);
const showProgress = ref(true);
const showEpochTable = ref(true);

const recentEpochs = computed(() => {
	if (!epochs.value.length) return [];
	return [...epochs.value].slice(-3).reverse();
});

const formatDecimal = (val: number | string | undefined) => {
	if (val === undefined || val === null || val === '') return '-';
	return Number(val).toFixed(3);
};

const loadTasks = async () => {
	try {
		const res = await trainApi.getTrainTasks();
		taskOptions.value = res?.data?.tasks || [];
		if (!currentTaskId.value && taskOptions.value.length > 0) {
			currentTaskId.value = taskOptions.value[0].taskId;
		}
	} catch (error) {
		ElMessage.error('获取任务列表失败');
	}
};

const loadMonitor = async () => {
	loading.value = true;
	try {
		const res = await trainApi.getTrainMonitor({ taskId: currentTaskId.value });
		overview.value = res?.data?.overview || {};
		epochs.value = res?.data?.epochs || [];
	} catch (error) {
		ElMessage.error('加载训练监控失败');
	} finally {
		loading.value = false;
	}
};

onMounted(async () => {
	await loadTasks();
	await loadMonitor();
});
</script>

<style scoped lang="scss">
.monitor-cards {
	display: grid;
	grid-template-columns: repeat(4, minmax(0, 1fr));
	gap: 12px;
}

.metric-title {
	font-size: 12px;
	color: #909399;
}

.metric-value {
	margin-top: 8px;
	font-size: 22px;
	font-weight: 600;
	color: #303133;
}

.card-header-row {
	display: flex;
	justify-content: space-between;
	align-items: center;
}

@media (max-width: 1200px) {
	.monitor-cards {
		grid-template-columns: repeat(2, minmax(0, 1fr));
	}
}
</style>
