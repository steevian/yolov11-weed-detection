<template>
  <!-- 仅保留1个template根标签 -->
	<div v-if="isShowBreadcrumb" class="layout-navbars-breadcrumb">
		<!-- 左侧展开/收起按钮（保留） -->
		<SvgIcon
			class="layout-navbars-breadcrumb-icon"
			:name="themeConfig.isCollapse ? 'ele-Expand' : 'ele-Fold'"
			:size="16"
			@click="onThemeConfigChange"
		/>
		<!-- 替换原面包屑文字：显示系统标题 -->
		<div class="system-breadcrumb-title">
			基于YOLOV11的杂草识别系统
		</div>
	</div>
</template>

<script setup lang="ts" name="layoutBreadcrumb">
import { reactive, computed, onMounted } from 'vue';
import { onBeforeRouteUpdate, useRoute, useRouter } from 'vue-router';
import { Local } from '/@/utils/storage';
import other from '/@/utils/other';
import { storeToRefs } from 'pinia';
import { useThemeConfig } from '/@/stores/themeConfig';
import { useRoutesList } from '/@/stores/routesList';

// 原逻辑保留（不影响功能）
const stores = useRoutesList();
const storesThemeConfig = useThemeConfig();
const { themeConfig } = storeToRefs(storesThemeConfig);
const { routesList } = storeToRefs(stores);
const route = useRoute();
const router = useRouter();
const state = reactive<BreadcrumbState>({
	breadcrumbList: [],
	routeSplit: [],
	routeSplitFirst: '',
	routeSplitIndex: 1,
});

const isShowBreadcrumb = computed(() => {
	initRouteSplit(route.path);
	const { layout, isBreadcrumb } = themeConfig.value;
	if (layout === 'classic' || layout === 'transverse') return false;
	else return isBreadcrumb ? true : false;
});
const onBreadcrumbClick = (v: RouteItem) => {
	const { redirect, path } = v;
	if (redirect) router.push(redirect);
	else router.push(path);
};
const onThemeConfigChange = () => {
	themeConfig.value.isCollapse = !themeConfig.value.isCollapse;
	setLocalThemeConfig();
};
const setLocalThemeConfig = () => {
	Local.remove('themeConfig');
	Local.set('themeConfig', themeConfig.value);
};
const getBreadcrumbList = (arr: RouteItems) => {
	arr.forEach((item: RouteItem) => {
		state.routeSplit.forEach((v: string, k: number, arrs: string[]) => {
			if (state.routeSplitFirst === item.path) {
				state.routeSplitFirst += `/${arrs[state.routeSplitIndex]}`;
				state.breadcrumbList.push(item);
				state.routeSplitIndex++;
				if (item.children) getBreadcrumbList(item.children);
			}
		});
	});
};
const initRouteSplit = (path: string) => {
	if (!themeConfig.value.isBreadcrumb) return false;
	state.breadcrumbList = [routesList.value[0]];
	state.routeSplit = path.split('/');
	state.routeSplit.shift();
	state.routeSplitFirst = `/${state.routeSplit[0]}`;
	state.routeSplitIndex = 1;
	getBreadcrumbList(routesList.value);
	if (route.name === 'home' || (route.name === 'notFound' && state.breadcrumbList.length > 1)) state.breadcrumbList.shift();
	if (state.breadcrumbList.length > 0)
		state.breadcrumbList[state.breadcrumbList.length - 1].meta.tagsViewName = other.setTagsViewNameI18n(<RouteToFrom>route);
};
onMounted(() => {
	initRouteSplit(route.path);
});
onBeforeRouteUpdate((to) => {
	initRouteSplit(to.path);
});
</script>

<style scoped lang="scss">
.layout-navbars-breadcrumb {
	flex: 1;
	height: inherit;
	display: flex;
	align-items: center; /* 按钮与标题垂直居中 */
	gap: 10px; /* 按钮和标题的间距 */
	padding-left: 10px; /* 左侧留边，避免贴边 */
}

/* 展开按钮样式 */
.layout-navbars-breadcrumb-icon {
	cursor: pointer;
	font-size: 18px;
	color: var(--next-bg-topBarColor);
	opacity: 0.8;
	&:hover {
		opacity: 1;
	}
}

/* 系统标题样式（替换原面包屑文字） */
.system-breadcrumb-title {
	font-size: 16px;
	color: var(--next-bg-topBarColor);
	opacity: 0.9;
}
</style>