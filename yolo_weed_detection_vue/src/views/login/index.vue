<template>
	<div class="login-page" @mousemove="onMouseMove" @click="onPageClick">
		<div class="starry-bg" aria-hidden="true">
			<div class="stars-layer" ref="starsLayerRef"></div>
			<div class="meteors-layer" ref="meteorsLayerRef"></div>
		</div>

		<div class="container">
			<div class="left-panel">
				<div class="left-content">
					<h3 class="left-title">基于YOLOV11的杂草检测系统</h3>
					<div class="cartoon-group">
						<div :class="['character', 'orange', characterClass]">
							<div class="arms">
								<div class="arm left"></div>
								<div class="arm right"></div>
							</div>
							<div class="eyes">
								<div class="eye"><div class="pupil" :style="{ transform: pupilTransform }"></div></div>
								<div class="eye"><div class="pupil" :style="{ transform: pupilTransform }"></div></div>
							</div>
							<div class="mouth smile"></div>
						</div>

						<div :class="['character', 'purple', characterClass]">
							<div class="arms">
								<div class="arm left"></div>
								<div class="arm right"></div>
							</div>
							<div class="eyes">
								<div class="eye"><div class="pupil" :style="{ transform: pupilTransform }"></div></div>
								<div class="eye"><div class="pupil" :style="{ transform: pupilTransform }"></div></div>
							</div>
							<div class="mouth smile"></div>
						</div>

						<div :class="['character', 'black', characterClass]">
							<div class="arms">
								<div class="arm left"></div>
								<div class="arm right"></div>
							</div>
							<div class="eyes">
								<div class="eye"><div class="pupil" :style="{ transform: pupilTransform }"></div></div>
								<div class="eye"><div class="pupil" :style="{ transform: pupilTransform }"></div></div>
							</div>
							<div class="mouth smile"></div>
						</div>

						<div :class="['character', 'yellow', characterClass]">
							<div class="arms">
								<div class="arm left"></div>
								<div class="arm right"></div>
							</div>
							<div class="eye single"><div class="pupil" :style="{ transform: pupilTransform }"></div></div>
							<div class="mouth flat"></div>
						</div>
					</div>
				</div>
			</div>

			<div class="login">
				<div class="login-card">
					<svg class="logo" viewBox="0 0 24 24" fill="none" aria-hidden="true">
						<path
							d="M12 2c1.8 0 3.2 1.5 3.2 3.3S13.8 8.6 12 8.6 8.8 7.1 8.8 5.3 10.2 2 12 2Zm0 13.4c1.8 0 3.2 1.5 3.2 3.3S13.8 22 12 22s-3.2-1.5-3.2-3.3 1.4-3.3 3.2-3.3ZM2 12c0-1.8 1.5-3.2 3.3-3.2S8.6 10.2 8.6 12s-1.5 3.2-3.3 3.2S2 13.8 2 12Zm13.4 0c0-1.8 1.5-3.2 3.3-3.2S22 10.2 22 12s-1.5 3.2-3.3 3.2-3.3-1.4-3.3-3.2Z"
							fill="#17171f"
						/>
					</svg>
					<h2>欢迎访问！</h2>

					<div class="field-group account-field">
						<label class="field-label" for="login-username">账号</label>
						<input
							id="login-username"
							ref="usernameInputRef"
							v-model.trim="ruleForm.username"
							class="text-input"
							type="text"
							autocomplete="username"
							@focus="lookAtForm"
							@blur="onFieldBlur"
						/>
					</div>

					<div class="field-group">
						<label class="field-label" for="login-password">密码</label>
						<div class="password-box">
							<input
								id="login-password"
								ref="passwordInputRef"
								v-model.trim="ruleForm.password"
								class="text-input"
								:type="isPasswordVisible ? 'text' : 'password'"
								autocomplete="current-password"
								@focus="lookAtForm"
								@blur="onFieldBlur"
								@keydown.enter="submitForm"
							/>
							<span id="toggle" @click="togglePassword">{{ isPasswordVisible ? '🙈' : '👁' }}</span>
						</div>
					</div>

					<div class="aux-row">
						<label class="remember"><input v-model="rememberMe" type="checkbox" />30天内记住我</label>
						<a class="forgot" href="javascript:void(0)">忘记密码？</a>
					</div>

					<button class="primary-btn" type="button" :disabled="isSubmitting" @click="submitForm">登录</button>
					<router-link class="google-btn" to="/register">注册</router-link>

					<p class="bottom-note">还没有账号？<router-link class="signup" to="/register">立即注册</router-link></p>
				</div>
			</div>
		</div>
	</div>
</template>

<script lang="ts" setup>
import { computed, onMounted, onUnmounted, reactive, ref } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { ElMessage } from 'element-plus';
import { useI18n } from 'vue-i18n';
import Cookies from 'js-cookie';
import { storeToRefs } from 'pinia';
import { useThemeConfig } from '@/utils/stores/themeConfig';
import { useUserInfo } from '@/utils/stores/userInfo';
import { initFrontEndControlRoutes } from '@/router/frontEnd';
import { initBackEndControlRoutes } from '@/router/backEnd';
import { Session } from '@/utils/storage';
import { formatAxis } from '@/utils/formatTime';
import { NextLoading } from '@/utils/loading';
import request from '@/utils/request';

const { t } = useI18n();
const storesThemeConfig = useThemeConfig();
const { themeConfig } = storeToRefs(storesThemeConfig);
const userInfoStore = useUserInfo();
const route = useRoute();
const router = useRouter();

const starsLayerRef = ref<HTMLElement | null>(null);
const meteorsLayerRef = ref<HTMLElement | null>(null);
const usernameInputRef = ref<HTMLInputElement | null>(null);
const passwordInputRef = ref<HTMLInputElement | null>(null);

const rememberMe = ref(false);
const isSubmitting = ref(false);
const isPasswordVisible = ref(false);
const characterMode = ref<'normal' | 'look-form' | 'cover'>('normal');
const pupilTransform = ref('translate(0,0)');

const ruleForm = reactive({
	username: '',
	password: '',
});

const characterClass = computed(() => {
	if (characterMode.value === 'look-form') return 'look-form';
	if (characterMode.value === 'cover') return 'look-away cover';
	return '';
});

const currentTime = computed(() => formatAxis(new Date()));

let meteorTimer: number | null = null;
let resizeTimer: number | null = null;

const lookAtForm = () => {
	if (isPasswordVisible.value) return;
	characterMode.value = 'look-form';
	pupilTransform.value = 'translate(4px,0)';
};

const coverEyes = () => {
	characterMode.value = 'cover';
	pupilTransform.value = 'translate(-8px,0)';
};

const resetCharacters = () => {
	if (isPasswordVisible.value) return;
	characterMode.value = 'normal';
	pupilTransform.value = 'translate(0,0)';
};

const onFieldBlur = () => {
	window.setTimeout(() => {
		const activeElement = document.activeElement;
		if (activeElement !== usernameInputRef.value && activeElement !== passwordInputRef.value) {
			resetCharacters();
		}
	}, 60);
};

const onMouseMove = (event: MouseEvent) => {
	if (isPasswordVisible.value) return;
	const target = event.target as HTMLElement;
	if (!target.classList?.contains('pupil') && !target.closest('.container')) return;
	const offsetX = Math.max(-4, Math.min(4, (event.clientX / window.innerWidth) * 8 - 4));
	const offsetY = Math.max(-3, Math.min(3, (event.clientY / window.innerHeight) * 6 - 3));
	pupilTransform.value = `translate(${offsetX.toFixed(1)}px,${offsetY.toFixed(1)}px)`;
};

const onPageClick = (event: MouseEvent) => {
	const target = event.target as HTMLElement;
	if (!target.closest('.password-box') && !target.closest('#login-username') && !target.closest('#login-password')) {
		resetCharacters();
	}
};

const togglePassword = () => {
	isPasswordVisible.value = !isPasswordVisible.value;
	if (isPasswordVisible.value) {
		coverEyes();
	} else {
		characterMode.value = 'normal';
		pupilTransform.value = 'translate(0,0)';
	}
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

const validateForm = () => {
	if (!ruleForm.username || !ruleForm.password) {
		ElMessage.warning('请输入账号和密码');
		return false;
	}
	if (ruleForm.username.length < 3 || ruleForm.username.length > 20) {
		ElMessage.warning('账号长度需在3-20个字符之间');
		return false;
	}
	if (ruleForm.password.length < 3 || ruleForm.password.length > 20) {
		ElMessage.warning('密码长度需在3-20个字符之间');
		return false;
	}
	return true;
};

const signInSuccess = (isNoPower: boolean | undefined) => {
	if (isNoPower) {
		ElMessage.warning('抱歉，您没有登录权限');
		Session.clear();
		return;
	}
	const currentTimeInfo = currentTime.value;
	if (route.query?.redirect) {
		router.push({
			path: String(route.query.redirect),
			query: route.query?.params ? JSON.parse(String(route.query.params)) : {},
		});
	} else {
		router.push('/');
	}
	const signInText = t('message.signInText') || '登录成功';
	ElMessage.success(`${currentTimeInfo}，${signInText}`);
	NextLoading.start();
};

const onSignIn = async (realToken: string, realUserInfo: any) => {
	Session.set('token', realToken);
	userInfoStore.setRealUserInfos(realUserInfo);
	Cookies.set('userName', ruleForm.username);
	Cookies.set('role', realUserInfo.role || 'common');
	if (rememberMe.value) {
		Cookies.set('rememberUserName', ruleForm.username, { expires: 30 });
	} else {
		Cookies.remove('rememberUserName');
	}
	if (!themeConfig.value.isRequestRoutes) {
		const isNoPower = await initFrontEndControlRoutes();
		signInSuccess(isNoPower);
	} else {
		const isNoPower = await initBackEndControlRoutes();
		signInSuccess(isNoPower);
	}
};

const submitForm = async () => {
	if (isSubmitting.value) return;
	if (!validateForm()) return;
	isSubmitting.value = true;
	try {
		const res = await request.post('/flask/login', ruleForm);
		if (res.code === 0 || res.code === 200) {
			const realToken = res.data.token;
			const realUserInfo = res.data.userInfo;
			await onSignIn(realToken, realUserInfo);
		} else {
			ElMessage.error(res.msg || '用户名或密码错误，请重新输入');
		}
	} catch (error: any) {
		if (error.response?.status === 404) {
			ElMessage.error('登录接口不存在，请检查后端接口是否为/flask/login');
		} else if (error.response?.status === 500) {
			ElMessage.error('后端服务出错，请检查后端代码和服务状态');
		} else {
			ElMessage.error('网络错误，请检查后端服务是否启动并正常运行！');
		}
	} finally {
		isSubmitting.value = false;
	}
};

onMounted(() => {
	const rememberedUserName = Cookies.get('rememberUserName');
	if (rememberedUserName) {
		ruleForm.username = rememberedUserName;
		rememberMe.value = true;
	}
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

.login-page {
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

.star {
	position: absolute;
	border-radius: 50%;
	background: #f0f0f0;
	animation-timing-function: ease-in-out;
	animation-iteration-count: infinite;
	animation-direction: alternate;
	will-change: opacity;
}

.star.glow {
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

.meteor {
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

.meteor::after {
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

.look-form {
	--lookX: -6px;
	--lookBend: -4deg;
}

.look-away {
	--lookX: 6px;
	--lookBend: 5deg;
}

.cover .arm.left {
	transform: rotate(-72deg) translate(-8px, -8px);
	animation: none;
}

.cover .arm.right {
	transform: rotate(72deg) translate(8px, -8px);
	animation: none;
}

.login {
	background: linear-gradient(180deg, #ffffff 0%, #fbfcff 100%);
	display: flex;
	align-items: center;
	justify-content: center;
	padding: 32px 40px;
}

.login-card {
	width: min(340px, 100%);
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

.login h2 {
	margin: 0;
	text-align: left;
	color: #1a1a21;
	font-family: 'Ma Shan Zheng', 'ZCOOL KuaiLe', cursive;
	font-size: 24px;
	line-height: 1.2;
	letter-spacing: 0.2px;
}

.field-group {
	width: 100%;
	display: flex;
	flex-direction: column;
	gap: 8px;
}

.account-field {
	margin-top: 16px;
}

.field-label {
	display: block;
	margin: 0;
	color: #2f2f35;
	font-size: clamp(16px, 1.45vw, 25px);
	font-weight: 700;
	line-height: 1;
}

.text-input {
	width: 100%;
	border: none;
	border-bottom: 2px solid #d9d9dd;
	outline: none;
	padding: 8px 4px 10px;
	font-size: 16px;
	color: #15151a;
	margin: 0;
	background: transparent;
}

.text-input:focus {
	border-bottom-color: #5c64ff;
}

.password-box {
	position: relative;
	margin: 0;
	width: 100%;
}

#toggle {
	position: absolute;
	right: 2px;
	top: 10px;
	font-size: 15px;
	color: #777;
	cursor: pointer;
	user-select: none;
}

.aux-row {
	display: flex;
	align-items: center;
	justify-content: space-between;
	width: 100%;
	margin: 0;
	font-size: 12px;
	color: #8c8c94;
}

.remember {
	display: inline-flex;
	align-items: center;
	gap: 6px;
	cursor: pointer;
}

.remember input {
	margin: 0;
	width: 14px;
	height: 14px;
	accent-color: #16161f;
}

.forgot,
.signup {
	text-decoration: none;
	color: #8c8c94;
	font-weight: 600;
}

.forgot:hover,
.signup:hover {
	color: #1d1d26;
}

.primary-btn,
.google-btn {
	width: 100%;
	height: 46px;
	border: none;
	border-radius: 24px;
	cursor: pointer;
	font-size: clamp(14px, 1.1vw, 18px);
	font-weight: 700;
	display: flex;
	align-items: center;
	justify-content: center;
}

.primary-btn {
	background: linear-gradient(90deg, #1f2240, #4d54ff);
	color: #fff;
	margin: 0;
	box-shadow: 0 10px 20px rgba(77, 84, 255, 0.3);
}

.primary-btn:disabled {
	opacity: 0.7;
	cursor: not-allowed;
}

.google-btn {
	background: #f2f4ff;
	color: #2a3054;
	text-decoration: none;
}

.bottom-note {
	margin: 0;
	text-align: left;
	font-size: 12px;
	color: #9b9ba2;
	font-weight: 600;
}

.signup {
	color: #1d1d26;
	margin-left: 6px;
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

	.login {
		padding: 32px;
	}
}
</style>
