<template>
	<div class="system-role-container layout-padding">
		<div class="system-role-padding layout-padding-auto layout-padding-view">
			<div class="manage-title-row">
				<div>
					<h3 class="manage-title">用户管理</h3>
					<p class="manage-subtitle">管理系统用户信息，支持筛选、添加、修改与删除</p>
				</div>
			</div>

			<div class="system-user-search action-card mb15">
				<el-input v-model="state.tableData.param.search" size="default" placeholder="请输入用户名" style="max-width: 180px"> </el-input>
				<el-button size="default" type="primary" class="ml10" @click="getTableData()">
					<el-icon>
						<ele-Search />
					</el-icon>
					查询
				</el-button>
				<el-button size="default" type="success" class="ml10" @click="onOpenAddRole">
					<el-icon>
						<ele-FolderAdd />
					</el-icon>
					添加
				</el-button>
			</div>
			<el-table :data="state.tableData.data" v-loading="state.tableData.loading" style="width: 100%" class="manage-table">
				<el-table-column prop="num" label="序号" width="80" align="center" />
				<el-table-column prop="username" label="账号" show-overflow-tooltip width="100" align="center"></el-table-column>
				<el-table-column prop="password" label="密码" width="100" align="center" />
				<el-table-column prop="name" label="姓名" show-overflow-tooltip width="100" align="center"></el-table-column>
				<el-table-column prop="sex" label="性别" show-overflow-tooltip width="80" align="center"></el-table-column>
				<el-table-column prop="email" label="邮箱" align="center" />
				<el-table-column prop="tel" label="手机号码" show-overflow-tooltip align="center"></el-table-column>
				<el-table-column prop="role" label="角色" show-overflow-tooltip align="center"></el-table-column>
				<el-table-column prop="avatar" label="头像" align="center">
					<template #default="scope">
						<img class="avatar-img" :src="scope.row.avatar || ''" width="70" height="70" />
					</template>
				</el-table-column>
				<el-table-column label="操作" width="150">
					<template #default="scope">
						<el-button size="small" text type="primary" @click="onOpenEditRole(scope.row)">修改</el-button>
						<el-button size="small" text type="primary" @click="onRowDel(scope.row)">删除</el-button>
					</template>
				</el-table-column>
			</el-table>
			<el-pagination
				@size-change="onHandleSizeChange"
				@current-change="onHandleCurrentChange"
				class="mt15 manage-pagination"
				:pager-count="5"
				:page-sizes="[10, 20, 30]"
				v-model:current-page="state.tableData.param.pageNum"
				background
				v-model:page-size="state.tableData.param.pageSize"
				layout="total, sizes, prev, pager, next, jumper"
				:total="state.tableData.total"
			>
			</el-pagination>
		</div>
		<RoleDialog ref="roleDialogRef" @refresh="getTableData" />
	</div>
</template>

<script setup lang="ts" name="systemRole">
import { defineAsyncComponent, reactive, onMounted, ref } from 'vue';
import { ElMessageBox, ElMessage } from 'element-plus';
import request from '@/utils/request';
// 引入Element图标
import { Search as eleSearch, FolderAdd as eleFolderAdd } from '@element-plus/icons-vue';

// 定义类型
type SysRoleState = {
	tableData: {
		data: Record<string, any>[];
		total: number;
		loading: boolean;
		param: {
			search: string;
			pageNum: number;
			pageSize: number;
		};
	};
};

// 引入弹窗组件
const RoleDialog = defineAsyncComponent(() => import('@/views/UserCenter/UserManage/dialog.vue'));

// 弹窗组件引用
const roleDialogRef = ref();

// 页面状态
const state = reactive<SysRoleState>({
	tableData: {
		data: [],
		total: 0,
		loading: false,
		param: {
			search: '',
			pageNum: 1,
			pageSize: 10,
		},
	},
});

// 获取用户列表
const getTableData = () => {
	state.tableData.loading = true;
	request
		.get('/flask/user', {
			params: state.tableData.param,
		})
		.then((res) => {
			state.tableData.loading = false;
			if (res.code === 0) {
				// 处理列表数据（序号、角色文字转换）
				state.tableData.data = res.data.records.map((item: any, index: number) => ({
					...item,
					num: index + 1,
					role: item.role === 'admin' ? '管理员' : '普通用户'
				}));
				state.tableData.total = res.data.total;
			} else {
				ElMessage.error(res.msg);
			}
		})
		.catch(() => {
			state.tableData.loading = false;
			ElMessage.error('获取用户列表失败');
		});
};

// 打开新增弹窗
const onOpenAddRole = () => {
	roleDialogRef.value?.openDialog('add');
};

// 打开修改弹窗
const onOpenEditRole = (row: Record<string, any>) => {
	roleDialogRef.value?.openDialog('edit', row);
};

// 删除用户
const onRowDel = (row: Record<string, any>) => {
	ElMessageBox.confirm('此操作将永久删除该用户，是否继续?', '提示', {
		type: 'warning'
	})
		.then(() => {
			request.delete(`/flask/user/${row.id}`).then((res) => {
				if (res.code === 0) {
					ElMessage.success('删除成功！');
					getTableData();
				} else {
					ElMessage.error(res.msg);
				}
			});
		})
		.catch(() => {});
};

// 分页-每页条数改变
const onHandleSizeChange = (val: number) => {
	state.tableData.param.pageSize = val;
	getTableData();
};

// 分页-当前页改变
const onHandleCurrentChange = (val: number) => {
	state.tableData.param.pageNum = val;
	getTableData();
};

// 页面加载初始化
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
		padding: 16px;
		height: 100%;
		display: flex;
		flex-direction: column;
		gap: 12px;
		overflow: auto;
	}
}

.manage-title-row {
	width: 100%;
	display: flex;
	align-items: center;
}

.manage-title {
	font-size: 24px;
	line-height: 1.25;
	font-weight: 700;
	color: var(--app-text-1, #111827);
}

.manage-subtitle {
	margin-top: 6px;
	font-size: 13px;
	color: var(--app-text-2, #6b7280);
}

.system-user-search {
	display: flex;
	align-items: center;
	flex-wrap: wrap;
	gap: 10px;
	padding: 14px;

	.el-input {
		flex: 1;
		min-width: 180px;
	}
}

.action-card {
	background: #fff;
	border: 1px solid var(--el-border-color-light);
	border-radius: 14px;
	box-shadow: 0 8px 24px rgba(17, 24, 39, 0.06);
}

.manage-table {
	flex: 1;
	background: #fff;
	border-radius: 12px;
	overflow: hidden;
	box-shadow: 0 8px 24px rgba(17, 24, 39, 0.06);
	border: 1px solid var(--el-border-color-light);

	:deep(.el-table__row:hover) {
		background-color: #eef2ff;
	}

	:deep(.el-table__cell) {
		padding: 12px 0;
	}
}

.avatar-img {
	border-radius: 10px;
	border: 1px solid #e5e7eb;
	object-fit: cover;
}

.manage-pagination {
	padding: 8px 0 2px;
}

@media (max-width: 900px) {
	.system-user-search {
		flex-direction: column;
		align-items: stretch;
	}

	.system-user-search .el-button {
		width: 100%;
		margin-left: 0 !important;
	}

	.manage-table :deep(.el-table__cell) {
		padding: 8px 0;
	}
}
</style>
