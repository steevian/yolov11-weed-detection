<template>
	<div class="system-role-container layout-padding">
		<div class="system-role-dialog-container">
			<div class="profile-title-row">
				<div>
					<h3 class="profile-title">个人中心</h3>
					<p class="profile-subtitle">维护头像与基础信息，提交后立即生效</p>
				</div>
			</div>

			<el-card shadow="never" class="cards">
				<el-form ref="roleDialogFormRef" :model="state.form" size="default" label-width="92px" class="profile-form">
					<div class="avatar-row">
						<el-form-item label="头像">
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
						</el-form-item>
					</div>

					<el-row :gutter="16">
						<el-col :xs="24" :sm="24" :md="12" :lg="12" :xl="12" class="mb20">
							<el-form-item label="账号">
								<el-input v-model="state.form.username" placeholder="请输入账号" clearable></el-input>
							</el-form-item>
						</el-col>
						<el-col :xs="24" :sm="24" :md="12" :lg="12" :xl="12" class="mb20">
							<el-form-item label="密码">
								<el-input v-model="state.form.password" placeholder="请输入密码" clearable></el-input>
							</el-form-item>
						</el-col>
						<el-col :xs="24" :sm="24" :md="12" :lg="12" :xl="12" class="mb20">
							<el-form-item label="姓名">
								<el-input v-model="state.form.name" placeholder="请输入姓名" clearable></el-input>
							</el-form-item>
						</el-col>
						<el-col :xs="24" :sm="24" :md="12" :lg="12" :xl="12" class="mb20">
							<el-form-item label="性别">
								<el-input v-model="state.form.sex" placeholder="请输入性别" clearable></el-input>
							</el-form-item>
						</el-col>
						<el-col :xs="24" :sm="24" :md="12" :lg="12" :xl="12" class="mb20">
							<el-form-item label="Email">
								<el-input v-model="state.form.email" placeholder="请输入Email" clearable></el-input>
							</el-form-item>
						</el-col>
						<el-col :xs="24" :sm="24" :md="12" :lg="12" :xl="12" class="mb20">
							<el-form-item label="手机号码">
								<el-input v-model="state.form.tel" placeholder="请输入手机号码" clearable></el-input>
							</el-form-item>
						</el-col>
						<el-col :xs="24" :sm="24" :md="12" :lg="12" :xl="12" class="mb20">
							<el-form-item label="角色">
								<el-input v-model="state.form.role" disabled placeholder="请输入角色" clearable></el-input>
							</el-form-item>
						</el-col>
					</el-row>
				</el-form>
				<div class="form-footer">
					<el-button type="primary" @click="upData" size="default">确认修改</el-button>
				</div>
			</el-card>
		</div>
	</div>
</template>

<script setup lang="ts" name="personal">
import { reactive, ref, onMounted } from 'vue';
import type { UploadInstance, UploadProps } from 'element-plus';
import { ElMessage } from 'element-plus';
import request from '@/utils/request';
import { useUserInfo } from '@/utils/stores/userInfo';
import { storeToRefs } from 'pinia';
import { Plus } from '@element-plus/icons-vue';

const imageUrl = ref('');
const uploadFile = ref<UploadInstance>();

const toAvatarUrl = (avatarPath?: string) => {
	if (!avatarPath) return '';
	if (avatarPath.startsWith('http://') || avatarPath.startsWith('https://')) return avatarPath;
	return avatarPath;
};

// 头像上传成功后的处理
const handleAvatarSuccessone: UploadProps['onSuccess'] = (response, uploadFile) => {
	imageUrl.value = toAvatarUrl(response.data);
  state.form.avatar = response.data; // 后端存储用相对路径
};

// 定义变量
const state = reactive({
	form: {} as any,
});
const stores = useUserInfo();
const { userInfos } = storeToRefs(stores);

// 合并后的初始化数据函数（删除了重复声明）
const getTableData = () => {
  // 统一请求/flask前缀的接口
  request.get('/flask/user/' + userInfos.value.userName).then((res) => {
    if (res.code == 0) {
      state.form = res.data;
      // 角色文字转换（后端存的是英文，前端显示中文）
      if (state.form['role'] == 'admin') {
        state.form['role'] = '管理员';
      } else if (state.form['role'] == 'common') {
        state.form['role'] = '普通用户';
      } else if (state.form['role'] == 'others') {
        state.form['role'] = '其他用户';
      }
      // 拼接完整头像URL
	imageUrl.value = toAvatarUrl(state.form.avatar);
    } else {
      ElMessage({
        type: 'error',
        message: res.msg,
      });
    }
  });
};

// 修改信息提交函数
const upData = () => {
  // 角色转换为后端需要的英文
  if (state.form['role'] == '管理员') state.form['role'] = 'admin';
  else if (state.form['role'] == '普通用户') state.form['role'] = 'common';
  else if (state.form['role'] == '其他用户') state.form['role'] = 'others';
  
  // 获取用户ID（从Pinia的登录信息中读取）
  const userId = userInfos.value.id;
  if (!userId) {
    ElMessage.error('用户ID不存在，请重新登录');
    return;
  }
  
  // 提交修改请求（路径拼接user_id）
  request.post(`/flask/user/${userId}`, state.form).then((res) => {
    if (res.code == 0) {
      ElMessage.success('修改成功！');
      // 重新拉取数据更新页面
      getTableData();
    } else {
      ElMessage.error(res.msg);
    }
  });
};

// 页面加载时初始化数据
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
}

.system-role-dialog-container {
	width: min(1100px, 100%);
	display: flex;
	flex-direction: column;
	gap: 12px;
}

.profile-title-row {
	width: 100%;
	display: flex;
	align-items: center;
}

.profile-title {
	font-size: 24px;
	line-height: 1.25;
	font-weight: 700;
	color: var(--app-text-1, #111827);
}

.profile-subtitle {
	margin-top: 6px;
	font-size: 13px;
	color: var(--app-text-2, #6b7280);
}

.cards {
	background: #fff;
	border-radius: 14px;
	border: 1px solid var(--el-border-color-light);
	box-shadow: 0 10px 28px rgba(17, 24, 39, 0.06);
}

.profile-form {
	width: 100%;
}

.imgs {
	font-size: 28px;
	color: hsl(215, 8%, 58%);
	width: 120px;
	height: 120px;
	display: flex;
	justify-content: center;
	align-items: center;
	border: 2px dashed #d1d5db;
	border-radius: 10px;
	cursor: pointer;
	margin-bottom: 4px;
}

.avatar-row {
	display: flex;
	justify-content: flex-start;
}

.form-footer {
	display: flex;
	justify-content: flex-end;
	margin-top: 6px;
}

.avatar-uploader .el-upload:hover {
	border-color: #6366f1;
}
.avatar {
	width: 120px;
	height: 120px;
	border-radius: 10px;
	display: block;
}

@media (max-width: 900px) {
	.system-role-dialog-container {
		width: 100%;
	}

	.form-footer {
		justify-content: stretch;
	}

	.form-footer .el-button {
		width: 100%;
	}
}
</style>
