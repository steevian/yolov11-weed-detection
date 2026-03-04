<template>
	<div class="register-page">
		<div class="starry-bg" aria-hidden="true">
			<div class="stars-layer"></div>
			<div class="stars-layer stars-layer-2"></div>
			<div class="meteor meteor-a"></div>
			<div class="meteor meteor-b"></div>
		</div>

		<div class="container">
			<div class="left-panel">
				<div class="left-content">
					<h3 class="left-title">基于YOLOV11的杂草检测系统</h3>
					<div class="cartoon-group">
						<div class="character orange"></div>
						<div class="character purple"></div>
						<div class="character black"></div>
						<div class="character yellow"></div>
					</div>
				</div>
			</div>

			<div class="register-panel">
				<div class="register-card">
					<svg class="logo" viewBox="0 0 24 24" fill="none" aria-hidden="true">
						<path
							d="M12 2c1.8 0 3.2 1.5 3.2 3.3S13.8 8.6 12 8.6 8.8 7.1 8.8 5.3 10.2 2 12 2Zm0 13.4c1.8 0 3.2 1.5 3.2 3.3S13.8 22 12 22s-3.2-1.5-3.2-3.3 1.4-3.3 3.2-3.3ZM2 12c0-1.8 1.5-3.2 3.3-3.2S8.6 10.2 8.6 12s-1.5 3.2-3.3 3.2S2 13.8 2 12Zm13.4 0c0-1.8 1.5-3.2 3.3-3.2S22 10.2 22 12s-1.5 3.2-3.3 3.2-3.3-1.4-3.3-3.2Z"
							fill="#17171f"
						/>
					</svg>
					<h2>欢迎注册！</h2>

					<el-form :model="ruleForm" :rules="registerRules" ref="ruleFormRef" class="register-form">
						<el-form-item prop="username">
							<el-input v-model="ruleForm.username" placeholder="请输入用户名" prefix-icon="User" class="custom-input" />
						</el-form-item>

						<el-form-item prop="password">
							<el-input v-model="ruleForm.password" type="password" placeholder="请输入密码" prefix-icon="Lock" show-password class="custom-input" />
						</el-form-item>

						<el-form-item prop="confirm">
							<el-input v-model="ruleForm.confirm" type="password" placeholder="请确认密码" prefix-icon="Lock" show-password class="custom-input" />
						</el-form-item>

						<el-form-item>
							<el-button type="primary" class="register-btn" @click="submitForm(ruleFormRef)">注册</el-button>
						</el-form-item>
					</el-form>

					<div class="options">
						<router-link to="/login">已有账号？登录</router-link>
					</div>
				</div>
			</div>
		</div>
	</div>
</template>

<script lang="ts" setup>
import { reactive, ref } from 'vue';
import { useRouter } from 'vue-router';
import { ElMessage } from 'element-plus';
import type { FormInstance, FormRules } from 'element-plus';
import request from '@/utils/request';

const router = useRouter();
const ruleFormRef = ref<FormInstance>();

const ruleForm = reactive({
	username: '',
	password: '',
	confirm: '',
});

const registerRules = reactive<FormRules>({
	username: [
		{ required: true, message: '请输入账号', trigger: 'blur' },
		{ min: 3, max: 20, message: '长度在3-20个字符', trigger: 'blur' },
	],
	password: [
		{ required: true, message: '请输入密码', trigger: 'blur' },
		{ min: 3, max: 20, message: '长度在3-20个字符', trigger: 'blur' },
	],
	confirm: [
		{ required: true, message: '请确认密码', trigger: 'blur' },
		{
			validator: (rule, value, callback) => {
				if (value !== ruleForm.password) {
					callback(new Error('两次密码不一致!'));
				} else {
					callback();
				}
			},
			trigger: 'blur',
		},
	],
});

const submitForm = (formEl: FormInstance | undefined) => {
	if (!formEl) return;
	formEl.validate((valid) => {
		if (valid) {
			request.post('/flask/register', ruleForm).then((res) => {
				if (res.code == 0) {
					router.push('/login');
					ElMessage.success('注册成功！');
				} else {
					ElMessage.error(res.msg || '注册失败');
				}
			});
		} else {
			console.log('error submit!');
			return false;
		}
	});
};
</script>

<style scoped>
.register-page {
	min-height: 100vh;
	display: flex;
	align-items: center;
	justify-content: center;
	background: transparent;
	padding: 24px;
	position: relative;
	overflow: hidden;
	isolation: isolate;
}

.starry-bg {
	position: fixed;
	inset: 0;
	z-index: 0;
	pointer-events: none;
	overflow: hidden;
	background: linear-gradient(to bottom, #0a0a1a 0%, #12122b 100%);
}

.stars-layer {
	position: absolute;
	inset: -20%;
	background-image: radial-gradient(2px 2px at 20% 30%, rgba(255, 255, 255, 0.92), rgba(255, 255, 255, 0)), radial-gradient(1.6px 1.6px at 72% 22%, rgba(255, 255, 255, 0.75), rgba(255, 255, 255, 0)), radial-gradient(2.3px 2.3px at 38% 78%, rgba(255, 255, 255, 0.88), rgba(255, 255, 255, 0)), radial-gradient(1.4px 1.4px at 82% 67%, rgba(255, 255, 255, 0.72), rgba(255, 255, 255, 0)), radial-gradient(2px 2px at 52% 48%, rgba(255, 255, 255, 0.95), rgba(255, 255, 255, 0));
	background-size: 460px 460px;
	animation: twinkle 8.5s ease-in-out infinite alternate;
}

.stars-layer-2 {
	opacity: 0.7;
	filter: blur(0.4px);
	animation-duration: 11s;
	animation-direction: alternate-reverse;
}

.meteor {
	position: absolute;
	width: 180px;
	height: 2px;
	border-radius: 999px;
	background: linear-gradient(90deg, rgba(255, 255, 255, 0) 0%, rgba(243, 244, 255, 0.8) 58%, #ffffff 100%);
	filter: drop-shadow(0 0 4px rgba(255, 255, 255, 0.52));
	transform: rotate(-38deg);
	opacity: 0;
	animation: meteorFly 6.2s linear infinite;
}

.meteor-a {
	left: 12%;
	top: 72%;
}

.meteor-b {
	left: 38%;
	top: 86%;
	animation-delay: 2.8s;
}

.container {
	width: min(980px, 94vw);
	min-height: 620px;
	display: grid;
	grid-template-columns: 1fr 1fr;
	border-radius: 28px;
	overflow: hidden;
	box-shadow: 0 30px 70px rgba(8, 12, 30, 0.5);
	background: #ffffff;
	border: 1px solid rgba(255, 255, 255, 0.46);
	position: relative;
	z-index: 2;
}

.left-panel {
	background: linear-gradient(165deg, #f5f6ff 0%, #eef1ff 54%, #f8f9ff 100%);
	position: relative;
	display: flex;
	align-items: center;
	justify-content: center;
	padding: 24px;
	overflow: hidden;
}

.left-content {
	display: flex;
	flex-direction: column;
	align-items: center;
	gap: 20px;
	transform: translateY(-18px);
}

.left-title {
	margin: 0;
	color: #222;
	font-size: 28px;
	font-weight: 700;
	text-align: center;
	line-height: 1.2;
	letter-spacing: 0.5px;
}

.cartoon-group {
	position: relative;
	display: flex;
	align-items: flex-end;
	gap: 15px;
	transform: translateY(88px);
}

.character {
	animation: idleFloat 3.6s ease-in-out infinite;
}

.orange {
	width: 160px;
	height: 120px;
	border-radius: 80px 80px 0 0;
	background: #ff8c1a;
}

.purple {
	width: 90px;
	height: 180px;
	border-radius: 10px;
	background: #7d3cff;
	animation-delay: 0.12s;
}

.black {
	width: 60px;
	height: 150px;
	border-radius: 10px;
	background: #1e1e1e;
	animation-delay: 0.18s;
}

.yellow {
	width: 70px;
	height: 140px;
	border-radius: 35px;
	background: #ffd000;
	animation-delay: 0.28s;
}

.register-panel {
	background: linear-gradient(180deg, #ffffff 0%, #fbfcff 100%);
	display: flex;
	align-items: center;
	justify-content: center;
	padding: 32px 40px;
}

.register-card {
	width: min(360px, 100%);
	display: flex;
	flex-direction: column;
	align-items: flex-start;
	gap: 16px;
	padding: 4px 0;
}

.logo {
	width: 24px;
	height: 24px;
	display: block;
	margin: 0;
}

.register-card h2 {
	margin: 0;
	text-align: left;
	color: #1a1a21;
	font-family: 'Ma Shan Zheng', 'ZCOOL KuaiLe', cursive;
	font-size: 24px;
	line-height: 1.2;
	letter-spacing: 0.2px;
}

.register-form {
	width: 100%;
	margin-top: 8px;
}

:deep(.register-form .el-form-item) {
	margin-bottom: 16px;
}

:deep(.custom-input .el-input__wrapper) {
	box-shadow: none;
	border-radius: 10px;
	padding: 10px 12px;
	background: #f6f7fd;
	border: 1px solid #e6e8f4;
}

:deep(.custom-input .el-input__wrapper:hover) {
	border-color: #cfd4ff;
}

:deep(.custom-input .el-input__wrapper.is-focus) {
	box-shadow: 0 0 0 2px rgba(92, 100, 255, 0.15);
	border-color: #5c64ff;
	background: #fff;
}

.register-btn {
	width: 100%;
	height: 46px;
	font-size: 15px;
	font-weight: 700;
	letter-spacing: 0.5px;
	border-radius: 24px;
	background: linear-gradient(90deg, #1f2240, #4d54ff);
	border: none;
	box-shadow: 0 10px 20px rgba(77, 84, 255, 0.3);
}

.register-btn:hover {
	filter: brightness(1.03);
}

.options {
	margin-top: 2px;
	text-align: center;
	width: 100%;
}

.options a {
	color: #3a448f;
	text-decoration: none;
	font-size: 14px;
	font-weight: 600;
}

.options a:hover {
	color: #1e2355;
}

@keyframes twinkle {
	0% {
		opacity: 0.48;
	}
	50% {
		opacity: 0.96;
	}
	100% {
		opacity: 0.56;
	}
}

@keyframes meteorFly {
	0% {
		opacity: 0;
		transform: translate3d(0, 0, 0) rotate(-38deg) scaleX(0.72);
	}
	12% {
		opacity: 0;
	}
	20% {
		opacity: 1;
	}
	80% {
		opacity: 0.94;
	}
	100% {
		opacity: 0;
		transform: translate3d(340px, -320px, 0) rotate(-38deg) scaleX(1);
	}
}

@keyframes idleFloat {
	0%,
	100% {
		translate: 0 0;
	}
	50% {
		translate: 0 -7px;
	}
}

@media (max-width: 900px) {
	.container {
		grid-template-columns: 1fr;
		width: min(560px, 95vw);
	}

	.left-panel {
		min-height: 320px;
	}

	.left-content {
		transform: none;
	}

	.cartoon-group {
		transform: translate(0, 20px);
	}

	.register-panel {
		padding: 30px;
	}
}
</style>
