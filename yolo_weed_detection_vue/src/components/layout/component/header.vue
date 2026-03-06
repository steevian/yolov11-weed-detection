<template>
	<el-header class="layout-header" v-if="!isTagsViewCurrenFull && !isDashboard">
		<NavBarsIndex />
	</el-header>
</template>

<script setup lang="ts" name="layoutHeader">
import { defineAsyncComponent } from 'vue';
import { storeToRefs } from 'pinia';
import { useTagsViewRoutes } from '@/utils/stores/tagsViewRoutes';

import { useRoute } from 'vue-router';
// 引入组件
const NavBarsIndex = defineAsyncComponent(() => import('@/components/layout/navBars/index.vue'));

// 定义变量内容
const storesTagsViewRoutes = useTagsViewRoutes();
const { isTagsViewCurrenFull } = storeToRefs(storesTagsViewRoutes);
const route = useRoute();
const isDashboard = computed(() => route.path === '/dashboard');
</script>

