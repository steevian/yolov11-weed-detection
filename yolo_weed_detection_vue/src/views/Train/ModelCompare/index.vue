<template>
	<div class="system-role-container layout-padding">
		<div class="system-role-padding layout-padding-auto layout-padding-view workbench-page-body">
			<div class="workbench-title-row">
				<div>
					<h3 class="workbench-title">模型比较</h3>
					<p class="workbench-subtitle">对比不同杂草检测模型在精度和速度上的差异，用于训练决策。</p>
				</div>
			</div>

			<el-card class="mb15">
				<el-form inline>
					<el-form-item label="模型A">
						<el-select v-model="modelA" filterable style="width: 300px">
							<el-option v-for="item in modelOptions" :key="item.modelId" :label="item.name" :value="item.modelId" />
						</el-select>
					</el-form-item>
					<el-form-item label="模型B">
						<el-select v-model="modelB" filterable style="width: 300px">
							<el-option v-for="item in modelOptions" :key="item.modelId" :label="item.name" :value="item.modelId" />
						</el-select>
					</el-form-item>
					<el-form-item>
						<el-checkbox v-model="showMetrics">性能指标</el-checkbox>
						<el-checkbox v-model="showSpeed" class="ml10">推理速度</el-checkbox>
					</el-form-item>
					<el-form-item>
						<el-button type="primary" @click="loadCompare">开始比较</el-button>
					</el-form-item>
				</el-form>
			</el-card>

			<el-card class="mb15" v-if="showMetrics">
				<template #header>
					<div class="card-header-row">
						<span>比较结果</span>
						<el-tag type="warning">placeholder</el-tag>
					</div>
				</template>
				<el-table :data="metricRows" v-loading="loading" style="width: 100%">
					<el-table-column prop="metric" label="指标" min-width="180" />
					<el-table-column prop="modelAValue" label="模型A" min-width="150" />
					<el-table-column prop="modelBValue" label="模型B" min-width="150" />
					<el-table-column prop="diffText" label="差异" min-width="150" />
					<el-table-column prop="winner" label="较优模型" min-width="160" />
				</el-table>
			</el-card>

			<el-card class="mb15" v-if="showSpeed">
				<template #header>速度比较</template>
				<el-descriptions :column="2" border>
					<el-descriptions-item label="模型A 推理耗时">{{ speedSummary.modelA }}</el-descriptions-item>
					<el-descriptions-item label="模型B 推理耗时">{{ speedSummary.modelB }}</el-descriptions-item>
					<el-descriptions-item label="速度优势">{{ speedSummary.winner }}</el-descriptions-item>
					<el-descriptions-item label="差异">{{ speedSummary.diff }}</el-descriptions-item>
				</el-descriptions>
			</el-card>

			<el-alert :title="summary" type="success" :closable="false" show-icon />
		</div>
	</div>
</template>

<script setup lang="ts" name="trainModelComparePage">
import { computed, onMounted, ref } from 'vue';
import { ElMessage } from 'element-plus';
import { useTrainApi } from '@/api/train';
import { calcDiff, pickWinner, toFixedSafe } from '@/views/Train/utils';

const trainApi = useTrainApi();
const loading = ref(false);
const modelOptions = ref<any[]>([]);
const modelA = ref('');
const modelB = ref('');
const compareData = ref<Record<string, any>>({});
const showMetrics = ref(true);
const showSpeed = ref(true);

const summary = computed(() => compareData.value.summary || '请选择两个模型进行比较');

const metricRows = computed(() => {
	const metrics = compareData.value.metrics || [];
	return metrics.map((item: any) => ({
		metric: item.metric,
		modelAValue: toFixedSafe(item.modelA),
		modelBValue: toFixedSafe(item.modelB),
		diffText: (() => {
			const { diff, diffPercent } = calcDiff(Number(item.modelA), Number(item.modelB));
			const diffText = `${diff >= 0 ? '+' : ''}${toFixedSafe(diff)}`;
			const percentText = diffPercent === null ? 'N/A' : `${diffPercent >= 0 ? '+' : ''}${diffPercent.toFixed(1)}%`;
			return `${diffText} (${percentText})`;
		})(),
		winner: item.winner || pickWinner(item.metric, Number(item.modelA), Number(item.modelB), modelA.value, modelB.value),
	}));
});

const speedSummary = computed(() => {
	const row = (compareData.value.metrics || []).find((item: any) => /耗时|latency|ms/i.test(item.metric));
	if (!row) {
		return { modelA: '-', modelB: '-', winner: '暂无', diff: '-' };
	}
	const a = Number(row.modelA);
	const b = Number(row.modelB);
	const { diff } = calcDiff(a, b);
	return {
		modelA: `${toFixedSafe(a)} ms/img`,
		modelB: `${toFixedSafe(b)} ms/img`,
		winner: pickWinner(row.metric, a, b, modelA.value, modelB.value),
		diff: `${diff >= 0 ? '+' : ''}${toFixedSafe(diff)} ms/img`,
	};
});

const loadCompare = async () => {
	if (!modelA.value || !modelB.value) {
		ElMessage.warning('请选择模型A和模型B');
		return;
	}
	if (modelA.value === modelB.value) {
		ElMessage.warning('模型A和模型B不能相同');
		return;
	}
	loading.value = true;
	try {
		const res = await trainApi.getTrainModelCompare({ modelA: modelA.value, modelB: modelB.value });
		compareData.value = res?.data || {};
	} catch (error) {
		ElMessage.error('模型比较失败');
	} finally {
		loading.value = false;
	}
};

const initModelOptions = async () => {
	try {
		const res = await trainApi.getTrainModelCompare();
		modelOptions.value = res?.data?.modelOptions || [];
		if (modelOptions.value.length >= 2) {
			modelA.value = modelOptions.value[0].modelId;
			modelB.value = modelOptions.value[1].modelId;
		}
	} catch (error) {
		ElMessage.error('加载模型列表失败');
	}
};

onMounted(async () => {
	await initModelOptions();
	if (modelA.value && modelB.value) {
		await loadCompare();
	}
});
</script>

<style scoped lang="scss">
.card-header-row {
	display: flex;
	justify-content: space-between;
	align-items: center;
}
</style>
