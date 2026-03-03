<template>
	<div class="system-role-dialog-container">
		<el-dialog :title="state.dialog.title" v-model="state.dialog.isShowDialog" width="800px" class="dia">
			<div class="imgs">
				<el-upload
					v-model="state.form.avatar"
					ref="uploadFile"
					class="avatar-uploader"
					action="/flask/upload/avatar"
					:show-file-list="false"
					:on-success="handleAvatarSuccessone"
				>
					<img v-if="imageUrl" :src="imageUrl" class="avatar" />
					<el-icon v-if="!imageUrl"><Plus /></el-icon>
				</el-upload>
			</div>
			<el-form ref="roleDialogFormRef" :model="state.form" size="default" label-width="100px">
				<el-row :gutter="35">
					<el-col :xs="24" :sm="24" :md="24" :lg="24" :xl="24" class="mb20">
						<el-form-item label="账号" style="color: #000">
							<el-input v-model="state.form.username" placeholder="请输入账号" clearable></el-input>
						</el-form-item>
					</el-col>
					<el-col :xs="24" :sm="24" :md="24" :lg="24" :xl="24" class="mb20">
						<el-form-item label="密码">
							<el-input v-model="state.form.password" placeholder="请输入密码" clearable></el-input>
						</el-form-item>
					</el-col>
					<el-col :xs="24" :sm="24" :md="24" :lg="24" :xl="24" class="mb20">
						<el-form-item label="姓名" style="color: #000">
							<el-input v-model="state.form.name" placeholder="请输入姓名" clearable></el-input>
						</el-form-item>
					</el-col>
					<el-col :xs="24" :sm="24" :md="24" :lg="24" :xl="24" class="mb20">
						<el-form-item label="性别">
							<el-input v-model="state.form.sex" placeholder="请输入性别" clearable></el-input>
						</el-form-item>
					</el-col>
					<el-col :xs="24" :sm="24" :md="24" :lg="24" :xl="24" class="mb20">
						<el-form-item label="Email">
							<el-input v-model="state.form.email" placeholder="请输入Email" clearable></el-input>
						</el-form-item>
					</el-col>
					<el-col :xs="24" :sm="24" :md="24" :lg="24" :xl="24" class="mb20">
						<el-form-item label="手机号码">
							<el-input v-model="state.form.tel" placeholder="请输入手机号码" clearable></el-input>
						</el-form-item>
					</el-col>
					<el-col :xs="24" :sm="24" :md="24" :lg="24" :xl="24" class="mb20">
						<el-form-item label="角色">
							<el-select v-model="state.form.role" placeholder="请选择注册角色" style="width: 100%">
								<el-option v-for="item in option" :key="item.id" :label="item.label" :value="item.role" />
							</el-select>
						</el-form-item>
					</el-col>
				</el-row>
			</el-form>
			<template #footer>
				<span class="dialog-footer">
					<el-button @click="onCancel" size="default">取 消</el-button>
					<el-button type="primary" @click="onSubmit" size="default">{{ state.dialog.submitTxt }}</el-button>
				</span>
			</template>
		</el-dialog>
	</div>
</template>

<script setup lang="ts" name="systemRoleDialog">
import { nextTick, reactive, ref } from 'vue';
import type { UploadInstance, UploadProps } from 'element-plus';
import { ElMessage } from 'element-plus';
import { Plus } from '@element-plus/icons-vue';
import request from '/@/utils/request';

// 定义类型（补充缺失的类型）
type RowRoleType = Record<string, any>;
type TreeType = Record<string, any>;

// 子组件向父组件传值/事件
const emit = defineEmits(['refresh']);

const imageUrl = ref('');
const uploadFile = ref<UploadInstance>();

const toAvatarUrl = (avatarPath?: string) => {
	if (!avatarPath) return '';
	if (avatarPath.startsWith('http://') || avatarPath.startsWith('https://')) return avatarPath;
	return avatarPath;
};

// 头像上传成功处理
const handleAvatarSuccessone: UploadProps['onSuccess'] = (response) => {
	imageUrl.value = toAvatarUrl(response.data);
  state.form.avatar = response.data;
};

// 角色下拉选项
const option = [
	{ id: 1, label: '管理员', role: 'admin' },
	{ id: 2, label: '普通用户', role: 'common' },
];

// 表单&弹窗状态
const roleDialogFormRef = ref();
const state = reactive({
	form: {} as RowRoleType,
	menuData: [] as TreeType[],
	menuProps: {
		children: 'children',
		label: 'label',
	},
	dialog: {
		isShowDialog: false,
		title: '',
		submitTxt: '',
	},
});

// 打开弹窗（区分新增/修改）
const openDialog = (type: 'add' | 'edit', row: RowRoleType = {}) => {
	state.dialog.isShowDialog = true;
	if (type === 'edit') {
		// 深拷贝避免修改原表格数据
		state.form = { ...row };
		state.dialog.title = '修改信息';
		state.dialog.submitTxt = '修 改';
		// 拼接头像完整URL
		imageUrl.value = toAvatarUrl(state.form.avatar || '');
	} else {
		state.form = {};
		state.dialog.title = '新增信息';
		state.dialog.submitTxt = '新 增';
		// 清空上传记录
		nextTick(() => {
			uploadFile.value?.clearFiles();
			imageUrl.value = '';
		});
	}
};

// 关闭弹窗
const closeDialog = () => {
	state.dialog.isShowDialog = false;
};

// 取消操作
const onCancel = () => {
	closeDialog();
};

// 提交表单
const onSubmit = () => {
	// 角色格式转换（前端中文转后端英文）
	if (state.form.role === '管理员') state.form.role = 'admin';
	else if (state.form.role === '普通用户') state.form.role = 'common';

	if (state.dialog.title === '修改信息') {
		// 修改用户：调用/flask/user/{id}接口
		request.post(`/flask/user/${state.form.id}`, state.form).then((res) => {
			if (res.code === 0) {
				ElMessage.success('修改成功！');
				closeDialog();
				emit('refresh');
			} else {
				ElMessage.error(res.msg);
			}
		});
	} else {
		// 新增用户：调用/flask/user/add接口
		request.post('/flask/user', state.form).then((res) => {
			if (res.code === 0) {
				ElMessage.success('添加成功！');
				closeDialog();
				emit('refresh');
			} else {
				ElMessage.error(res.msg);
			}
		});
	}
};

// 暴露方法给父组件
defineExpose({
	openDialog,
});
</script>

<style scoped lang="scss">
:deep(.dia) {
	width: 800px;
	height: 650px;
	display: flex;
	flex-direction: column;
	justify-content: center;
	align-items: center;
}

.el-form {
	width: 80%;
	margin-left: 10%;
}

.imgs {
	font-size: 28px;
	color: hsl(215, 8%, 58%);
	width: 120px;
	height: 120px;
	display: flex;
	justify-content: center;
	align-items: center;
	border: 1px dashed #d9d9d9;
	border-radius: 6px;
	cursor: pointer;
	margin-left: 320px;
	margin-bottom: 20px;
}

.avatar-uploader .el-upload:hover {
	border-color: #409eff;
}
.avatar {
	width: 120px;
	height: 120px;
	display: block;
}
</style>