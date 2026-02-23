import vue from '@vitejs/plugin-vue';
import { resolve } from 'path';
import { defineConfig, loadEnv, ConfigEnv } from 'vite';
import vueSetupExtend from 'vite-plugin-vue-setup-extend';
import mkcert from 'vite-plugin-mkcert'; // 引入mkcert

// 路径解析方法
const pathResolve = (dir: string) => {
  return resolve(__dirname, '.', dir);
};

// 别名配置
const alias: Record<string, string> = {
  '/@': pathResolve('./src/'),
  'vue-i18n': 'vue-i18n/dist/vue-i18n.cjs.js',
};

// 🔥 修正：Flask实际IP为192.168.0.102（原101），同时抽离SpringBoot地址便于维护
const FLASK_BASE_URL = 'http://192.168.0.102:5000';
const SPRINGBOOT_BASE_URL = 'http://192.168.0.102:9999'; // 假设SpringBoot与Flask同IP，若不同则修改

const viteConfig = defineConfig((mode: ConfigEnv) => {
  const env = loadEnv(mode.mode, process.cwd());
  return {
    plugins: [
      vue(), 
      vueSetupExtend(),
      mkcert() // 启用mkcert插件（支持HTTPS）
    ],
    root: process.cwd(),
    resolve: { alias },
    base: mode.command === 'serve' ? '/' : env.VITE_PUBLIC_PATH || './', // 修复开发环境base路径（原./可能导致路由404）
    optimizeDeps: {
      include: [
        'element-plus/lib/locale/lang/zh-cn',
        'element-plus/lib/locale/lang/en',
        'element-plus/lib/locale/lang/zh-tw'
      ],
    },
    server: {
      host: '0.0.0.0',
      port: (env.VITE_PORT as unknown as number) || 5173,
      open: env.VITE_OPEN === 'true' || false,
      hmr: true,
      https: true, // 启用HTTPS（前端）
      proxy: {
        // 🔥 Flask代理（修正IP为102，保持原有规则）
        '/flask': {
          target: FLASK_BASE_URL,
          ws: true, // 支持WebSocket（视频进度推送、摄像头流）
          changeOrigin: true, // 跨域必备
          secure: false, // 允许目标为HTTP（Flask未启用HTTPS）
        },
        '/uploads': {
          target: FLASK_BASE_URL,
          changeOrigin: true,
          secure: false,
        },
        '/results': {
          target: FLASK_BASE_URL,
          changeOrigin: true,
          secure: false,
        },
        '/runs': {
          target: FLASK_BASE_URL,
          changeOrigin: true,
          secure: false,
        },
        '/socket.io': {
          target: FLASK_BASE_URL,
          ws: true,
          changeOrigin: true,
          secure: false,
        },
        '/stopCamera': {
          target: FLASK_BASE_URL,
          changeOrigin: true,
          secure: false,
        },
        '/upload': { // 兼容前端上传组件的action="/upload"
          target: FLASK_BASE_URL,
          changeOrigin: true,
          secure: false,
        },
        '/predict': {
          target: FLASK_BASE_URL,
          changeOrigin: true,
          secure: false,
          ws: true,
        },
        '/predictVideo': {
          target: FLASK_BASE_URL,
          changeOrigin: true,
          secure: false,
        },
        '/predictCamera': {
          target: FLASK_BASE_URL,
          changeOrigin: true,
          secure: false,
        },
        '/api': {
          target: FLASK_BASE_URL,
          changeOrigin: true,
          secure: false,
          rewrite: (path) => path.replace(/^\/api/, '/flask'), // 旧/api请求自动转为/flask前缀
        },

        // 🔥 新增：SpringBoot服务代理（9999端口），按实际接口前缀调整
        '/springboot': {
          target: SPRINGBOOT_BASE_URL,
          changeOrigin: true,
          secure: false, // SpringBoot若未启用HTTPS则设为false
          // 可选：若SpringBoot接口无统一前缀，可添加rewrite
          // rewrite: (path) => path.replace(/^\/springboot/, ''),
        },
        // 若SpringBoot有特定接口前缀（如/api），补充代理
        '/spring-api': {
          target: SPRINGBOOT_BASE_URL,
          changeOrigin: true,
          secure: false,
          rewrite: (path) => path.replace(/^\/spring-api/, '/api'),
        },
      },
    },
    build: {
      outDir: 'dist',
      chunkSizeWarningLimit: 1500,
      rollupOptions: {
        output: {
          entryFileNames: `assets/[name].[hash].js`,
          chunkFileNames: `assets/[name].[hash].js`,
          assetFileNames: `assets/[name].[hash].[ext]`,
          compact: true,
          manualChunks: {
            vue: ['vue', 'vue-router', 'pinia'],
            echarts: ['echarts'],
            elementPlus: ['element-plus'],
          },
        },
      },
    },
    css: {
      preprocessorOptions: {
        css: { charset: false },
      },
    },
    define: {
      __VUE_I18N_LEGACY_API__: JSON.stringify(false),
      __VUE_I18N_FULL_INSTALL__: JSON.stringify(false),
      __INTLIFY_PROD_DEVTOOLS__: JSON.stringify(false),
      __VERSION__: JSON.stringify(process.env.npm_package_version || '1.0.0'),
    },
  };
});

export default viteConfig;