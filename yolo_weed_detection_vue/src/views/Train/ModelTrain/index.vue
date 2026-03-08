<template>
	<div class="system-role-container layout-padding">
		<div class="system-role-padding layout-padding-auto layout-padding-view workbench-page-body">
			<div class="workbench-title-row">
				<div>
					<h3 class="workbench-title">模型训练</h3>
					<p class="workbench-subtitle">管理员配置杂草检测训练任务。当前为接口预留阶段，不执行真实训练。</p>
				</div>
			</div>

			<el-card class="mb15">
				<el-form :model="form" label-width="110px" inline>
					<el-form-item label="任务名称">
						<el-input v-model="form.taskName" placeholder="例如：weed-train-v1" style="width: 220px" />
					</el-form-item>
					<el-form-item label="模型类型">
						<el-select v-model="form.modelType" style="width: 180px">
							<el-option label="YOLO11n" value="yolo11n" />
							<el-option label="YOLO11s" value="yolo11s" />
							<el-option label="自定义模型" value="custom" />
						</el-select>
					</el-form-item>
					<el-form-item label="数据集">
						<el-input v-model="form.datasetName" placeholder="例如：weed_dataset_v1" style="width: 220px" />
					</el-form-item>
					<el-form-item label="训练轮次">
						<el-input-number v-model="form.epochs" :min="1" :max="2000" />
					</el-form-item>
					<el-form-item label="批量大小">
						<el-input-number v-model="form.batchSize" :min="1" :max="256" />
					</el-form-item>
					<el-form-item label="图像尺寸">
						<el-input-number v-model="form.imageSize" :min="64" :max="2048" :step="32" />
					</el-form-item>
					<el-form-item label="备注">
						<el-input v-model="form.remark" placeholder="训练目的说明" style="width: 320px" />
					</el-form-item>
				</el-form>
				<div>
					<el-button type="primary" :loading="submitting" @click="onSubmit">提交训练任务（预留）</el-button>
					<el-button @click="loadTasks">刷新任务列表</el-button>
				</div>
			</el-card>

			<el-card>
				<template #header>
					<div class="card-header-row">
						<span>训练任务记录</span>
						<el-tag type="warning">placeholder</el-tag>
					</div>
				</template>
				<el-table :data="tasks" v-loading="loading" style="width: 100%" @row-click="onSelectTask" row-key="taskId" highlight-current-row>
					<el-table-column prop="taskId" label="任务ID" min-width="140" />
					<el-table-column prop="taskName" label="任务名称" min-width="180" />
					<el-table-column prop="modelType" label="模型" min-width="100" />
					<el-table-column prop="datasetName" label="数据集" min-width="140" />
					<el-table-column prop="status" label="状态" min-width="100" />
					<el-table-column prop="createdAt" label="创建时间" min-width="180" />
				</el-table>
			</el-card>

			<el-card class="mt15" v-if="selectedTask">
				<template #header>
					<div class="card-header-row">
						<span>任务详情 - {{ selectedTask.taskName }}</span>
						<el-tag type="info">{{ selectedTask.status || 'unknown' }}</el-tag>
					</div>
				</template>
				<div class="detail-metrics">
					<el-card>
						<div class="metric-title">当前轮次</div>
						<div class="metric-value">{{ monitorOverview.currentEpoch || 0 }} / {{ monitorOverview.totalEpoch || 0 }}</div>
					</el-card>
					<el-card>
						<div class="metric-title">mAP50</div>
						<div class="metric-value">{{ toFixedSafe(monitorOverview.map50) }}</div>
					</el-card>
					<el-card>
						<div class="metric-title">Precision</div>
						<div class="metric-value">{{ toFixedSafe(monitorOverview.precision) }}</div>
					</el-card>
					<el-card>
						<div class="metric-title">Recall</div>
						<div class="metric-value">{{ toFixedSafe(monitorOverview.recall) }}</div>
					</el-card>
				</div>
				<el-progress class="mt15" :percentage="monitorOverview.progress || 0" :stroke-width="16" />
			</el-card>
		</div>
	</div>
</template>

<script setup lang="ts" name="trainModelPage">
import { onMounted, reactive, ref } from 'vue';
import { ElMessage } from 'element-plus';
import { useTrainApi } from '@/api/train';
import { toFixedSafe } from '@/views/Train/utils';

const trainApi = useTrainApi();
const loading = ref(false);
const submitting = ref(false);
const tasks = ref<any[]>([]);
const selectedTask = ref<any>(null);
const monitorOverview = ref<Record<string, any>>({});

const form = reactive({
	taskName: 'weed-train-v1',
	modelType: 'yolo11n',
	datasetName: 'weed_dataset_v1',
	epochs: 100,
	batchSize: 16,
	imageSize: 640,
	remark: '',
});

const loadTasks = async () => {
	loading.value = true;
	try {
		const res = await trainApi.getTrainTasks();
		tasks.value = res?.data?.tasks || [];
		if (!selectedTask.value && tasks.value.length > 0) {
			await onSelectTask(tasks.value[0]);
		}
	} catch (error) {
		ElMessage.error('获取训练任务失败');
	} finally {
		loading.value = false;
	}
};

const onSelectTask = async (row: any) => {
	selectedTask.value = row;
	try {
		const res = await trainApi.getTrainMonitor({ taskId: row.taskId });
		monitorOverview.value = res?.data?.overview || {};
	} catch (error) {
		monitorOverview.value = {};
	}
};

const onSubmit = async () => {
	submitting.value = true;
	try {
		const payload = {
			taskName: form.taskName,
			modelType: form.modelType,
			datasetName: form.datasetName,
			epochs: form.epochs,
			batchSize: form.batchSize,
			imageSize: form.imageSize,
			remark: form.remark,
		};
		const res = await trainApi.createTrainTask(payload);
		ElMessage.success(res?.msg || '训练任务已创建（占位）');
		loadTasks();
	} catch (error) {
		ElMessage.error('创建训练任务失败');
	} finally {
		submitting.value = false;
	}
};

onMounted(() => {
	loadTasks();
});
</script>

<style scoped lang="scss">
.card-header-row {
	display: flex;
	justify-content: space-between;
	align-items: center;
}

.detail-metrics {
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

@media (max-width: 1200px) {
	.detail-metrics {
		grid-template-columns: repeat(2, minmax(0, 1fr));
	}
}
</style>
