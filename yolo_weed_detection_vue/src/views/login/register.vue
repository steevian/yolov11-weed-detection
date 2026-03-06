<template>
	<div class="register-page">
		<div class="starry-bg" aria-hidden="true">
			<div class="stars-layer" ref="starsLayerRef"></div>
			<div class="meteors-layer" ref="meteorsLayerRef"></div>
		</div>

		<div class="container">
			<div class="left-panel">
				<div class="left-content">
					<h3 class="left-title">基于YOLOV11的杂草检测系统</h3>
					<div class="cartoon-group">
						<div class="character orange">
							<div class="arms">
								<div class="arm left"></div>
								<div class="arm right"></div>
							</div>
							<div class="eyes">
								<div class="eye"><div class="pupil"></div></div>
								<div class="eye"><div class="pupil"></div></div>
							</div>
							<div class="mouth smile"></div>
						</div>

						<div class="character purple">
							<div class="arms">
								<div class="arm left"></div>
								<div class="arm right"></div>
							</div>
							<div class="eyes">
								<div class="eye"><div class="pupil"></div></div>
								<div class="eye"><div class="pupil"></div></div>
							</div>
							<div class="mouth smile"></div>
						</div>

						<div class="character black">
							<div class="arms">
								<div class="arm left"></div>
								<div class="arm right"></div>
							</div>
							<div class="eyes">
								<div class="eye"><div class="pupil"></div></div>
								<div class="eye"><div class="pupil"></div></div>
							</div>
							<div class="mouth smile"></div>
						</div>

						<div class="character yellow">
							<div class="arms">
								<div class="arm left"></div>
								<div class="arm right"></div>
							</div>
							<div class="eye single"><div class="pupil"></div></div>
							<div class="mouth flat"></div>
						</div>
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
import { onMounted, onUnmounted, reactive, ref } from 'vue';
import { useRouter } from 'vue-router';
import { ElMessage } from 'element-plus';
import type { FormInstance, FormRules } from 'element-plus';
import request from '@/utils/request';

const router = useRouter();
const ruleFormRef = ref<FormInstance>();
const starsLayerRef = ref<HTMLElement | null>(null);
const meteorsLayerRef = ref<HTMLElement | null>(null);

let meteorTimer: number | null = null;
let resizeTimer: number | null = null;

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

const createStars = () => {
	const starsLayer = starsLayerRef.value;
	if (!starsLayer) return;
	const width = window.innerWidth;
	const height = window.innerHeight;
	const area = width * height;
	const count = Math.max(140, Math.min(320, Math.floor(area / 7800)));

	starsLayer.innerHTML = '';
	for (let index = 0; index < count; index++) {
		const star = document.createElement('span');
		const size = 1 + Math.random() * 4.3;
		const minOpacity = 0.4 + Math.random() * 0.3;
		const maxOpacity = 0.82 + Math.random() * 0.18;
		const duration = 2 + Math.random() * 4;
		const delay = -Math.random() * 6;

		star.className = 'star';
		if (size >= 3.3 && Math.random() > 0.35) {
			star.classList.add('glow');
		}
		star.style.left = `${Math.random() * 100}%`;
		star.style.top = `${Math.random() * 100}%`;
		star.style.width = `${size.toFixed(2)}px`;
		star.style.height = `${size.toFixed(2)}px`;
		star.style.animationName = Math.random() > 0.5 ? 'twinkleA' : 'twinkleB';
		star.style.animationDuration = `${duration.toFixed(2)}s`;
		star.style.animationDelay = `${delay.toFixed(2)}s`;
		star.style.setProperty('--twinkle-min', minOpacity.toFixed(2));
		star.style.setProperty('--twinkle-max', Math.min(1, maxOpacity).toFixed(2));
		starsLayer.appendChild(star);
	}
};

const spawnMeteor = () => {
	const meteorsLayer = meteorsLayerRef.value;
	if (!meteorsLayer) return;

	const meteor = document.createElement('span');
	const startX = -100 + Math.random() * (window.innerWidth * 0.52);
	const startY = window.innerHeight * (0.52 + Math.random() * 0.44);
	const distance = 280 + Math.random() * 460;
	const angle = -28 - Math.random() * 30;
	const duration = 2 + Math.random();
	const length = 120 + Math.random() * 150;

	meteor.className = 'meteor';
	meteor.style.left = `${startX}px`;
	meteor.style.top = `${startY}px`;
	meteor.style.setProperty('--meteor-dx', `${distance.toFixed(1)}px`);
	meteor.style.setProperty('--meteor-dy', `${(-distance).toFixed(1)}px`);
	meteor.style.setProperty('--meteor-angle', `${angle.toFixed(1)}deg`);
	meteor.style.setProperty('--meteor-duration', `${duration.toFixed(2)}s`);
	meteor.style.setProperty('--meteor-length', `${length.toFixed(1)}px`);

	meteorsLayer.appendChild(meteor);
	window.setTimeout(() => meteor.remove(), duration * 1000 + 120);
};

const scheduleMeteor = () => {
	if (meteorTimer) {
		window.clearTimeout(meteorTimer);
	}
	const delay = 3000 + Math.random() * 5000;
	meteorTimer = window.setTimeout(() => {
		spawnMeteor();
		scheduleMeteor();
	}, delay);
};

const onResize = () => {
	if (resizeTimer) {
		window.clearTimeout(resizeTimer);
	}
	resizeTimer = window.setTimeout(() => {
		createStars();
	}, 220);
};

onMounted(() => {
	createStars();
	scheduleMeteor();
	window.addEventListener('resize', onResize);
});

onUnmounted(() => {
	window.removeEventListener('resize', onResize);
	if (meteorTimer) window.clearTimeout(meteorTimer);
	if (resizeTimer) window.clearTimeout(resizeTimer);
});
</script>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Ma+Shan+Zheng&family=ZCOOL+KuaiLe&display=swap');

.register-page {
	margin: 0;
	min-height: 100vh;
	display: flex;
	align-items: center;
	justify-content: center;
	background: transparent;
	font-family: 'PingFang SC', 'Microsoft YaHei', Arial, sans-serif;
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

.stars-layer,
.meteors-layer {
	position: absolute;
	inset: 0;
	overflow: hidden;
}

:deep(.star) {
	position: absolute;
	border-radius: 50%;
	background: #f0f0f0;
	animation-timing-function: ease-in-out;
	animation-iteration-count: infinite;
	animation-direction: alternate;
	will-change: opacity;
}

:deep(.star.glow) {
	box-shadow: 0 0 12px 4px rgba(255, 255, 255, 0.55), 0 0 32px 8px rgba(255, 255, 255, 0.18);
}

@keyframes twinkleA {
	0%,
	100% {
		opacity: var(--twinkle-min, 0.4);
	}
	50% {
		opacity: var(--twinkle-max, 1);
	}
}

@keyframes twinkleB {
	0%,
	100% {
		opacity: var(--twinkle-max, 1);
	}
	50% {
		opacity: var(--twinkle-min, 0.4);
	}
}

:deep(.meteor) {
	position: absolute;
	width: var(--meteor-length, 170px);
	height: 2px;
	background: linear-gradient(90deg, rgba(255, 255, 255, 0) 0%, rgba(240, 240, 240, 0.75) 58%, #ffffff 100%);
	border-radius: 999px;
	transform-origin: center left;
	filter: drop-shadow(0 0 4px rgba(255, 255, 255, 0.5));
	animation: meteorFly var(--meteor-duration, 1.4s) linear forwards;
	will-change: transform, opacity;
}

:deep(.meteor::after) {
	content: '';
	position: absolute;
	right: -2px;
	top: 50%;
	width: 4px;
	height: 4px;
	border-radius: 50%;
	background: #ffffff;
	transform: translateY(-50%);
	box-shadow: 0 0 6px rgba(255, 255, 255, 0.72);
}

@keyframes meteorFly {
	0% {
		opacity: 0;
		transform: translate3d(0, 0, 0) rotate(var(--meteor-angle, -45deg)) scaleX(0.72);
	}
	10% {
		opacity: 1;
	}
	90% {
		opacity: 0.95;
	}
	100% {
		opacity: 0;
		transform: translate3d(var(--meteor-dx, 320px), var(--meteor-dy, -320px), 0) rotate(var(--meteor-angle, -45deg)) scaleX(1);
	}
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
	--lookX: 0px;
	--lookBend: 0deg;
	position: relative;
	display: flex;
	flex-direction: column;
	align-items: center;
	justify-content: flex-start;
	transform-origin: bottom center;
	transform: translateX(var(--lookX)) skewX(var(--lookBend));
	transition: transform 0.3s ease-out;
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

.arms {
	position: absolute;
	bottom: 0;
	width: 100%;
	display: flex;
	justify-content: space-between;
	padding: 0 8px;
	pointer-events: none;
}

.arm {
	width: 15px;
	height: 50px;
	background: inherit;
	border-radius: 10px;
	transform-origin: top center;
	transition: transform 0.3s ease;
	animation: wave 1.6s ease-in-out infinite;
}

.arm.right {
	animation-direction: reverse;
}

.eyes {
	display: flex;
	gap: 12px;
	margin-top: 25px;
}

.eye {
	width: 14px;
	height: 14px;
	background: #ffffff;
	border-radius: 50%;
	position: relative;
}

.eye.single {
	margin-top: 35px;
	margin-left: 0;
}

.pupil {
	width: 6px;
	height: 6px;
	background: #171717;
	border-radius: 50%;
	position: absolute;
	top: 4px;
	left: 4px;
	transition: transform 0.15s ease;
}

.mouth {
	width: 12px;
	height: 4px;
	margin-top: 12px;
	background: #111;
}

.smile {
	border-radius: 0 0 10px 10px;
}

.flat {
	width: 16px;
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

@keyframes idleFloat {
	0%,
	100% {
		translate: 0 0;
	}
	50% {
		translate: 0 -7px;
	}
}

@keyframes wave {
	0%,
	100% {
		transform: rotate(0deg);
	}
	50% {
		transform: rotate(16deg);
	}
}

@media (max-width: 900px) {
	.container {
		grid-template-columns: 1fr;
		width: min(560px, 95vw);
	}

	.left-panel {
		min-height: 380px;
	}

	.left-content {
		transform: none;
	}

	.cartoon-group {
		transform: translate(0, 12px);
	}

	.register-panel {
		padding: 30px;
	}
}
</style>

<style>
@keyframes twinkleA {
	0%,
	100% {
		opacity: var(--twinkle-min, 0.4);
	}
	50% {
		opacity: var(--twinkle-max, 1);
	}
}

@keyframes twinkleB {
	0%,
	100% {
		opacity: var(--twinkle-max, 1);
	}
	50% {
		opacity: var(--twinkle-min, 0.4);
	}
}
</style>
