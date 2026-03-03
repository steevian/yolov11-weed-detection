<template>
	<div class="system-role-container layout-padding">
	<div class="system-role-dialog-container">
		<el-card shadow="hover" header="个人信息" class="cards">
			<el-form ref="roleDialogFormRef" :model="state.form" size="default" label-width="100px">
				<el-row :gutter="35">
					<el-col :xs="24" :sm="24" :md="24" :lg="24" :xl="24" class="mb20">
						<el-form-item label="头像：">
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
					</el-col>
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
						<el-form-item label="姓名">
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
							<el-input v-model="state.form.role" disabled placeholder="请输入角色" clearable></el-input>
						</el-form-item>
					</el-col>
				</el-row>
			</el-form>
			<el-button type="primary" @click="upData" size="default" style="float: right;margin-right: 15%;">确认修改</el-button>
		</el-card>
	</div>
</div>
</template>

<script setup lang="ts" name="personal">
import { reactive, ref, onMounted } from 'vue';
import type { UploadInstance, UploadProps } from 'element-plus';
import { ElMessage } from 'element-plus';
import request from '/@/utils/request';
import { useUserInfo } from '/@/stores/userInfo';
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
	display: flex;
	align-items: center;
	background: radial-gradient(circle, #d3e3f1 0%, #ffffff 100%);
}
.system-role-dialog-container{
	width: 60%;
}

.cards{
	background: radial-gradient(circle, #d3e3f1 0%, #ffffff 100%);
	border-radius: 10px;
	display: flex;
	flex-direction: column;
	align-items: center;
}

.el-form {
	width: 75%;
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