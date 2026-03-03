import { defineStore } from 'pinia';
import Cookies from 'js-cookie';
import { Session } from '/@/utils/storage';

// 扩展用户信息类型（匹配后端返回的userInfo结构）
interface UserInfosState {
  userInfos: {
    userName: string;
    role: string;
    photo: string;
    time: number;
    roles: Array<string>;
    authBtnList: Array<string>;
    id?: number;
    avatar?: string;
  };
}

/**
 * 用户信息
 * @methods setUserInfos 设置用户信息
 * @methods setRealUserInfos 从后端真实数据设置用户信息（新增）
 */
export const useUserInfo = defineStore('userInfo', {
  state: (): UserInfosState => ({
    userInfos: {
      userName: '',
      role: '',
      photo: '',
      time: 0,
      roles: [],
      authBtnList: [],
    },
  }),
  actions: {
    async setUserInfos() {
      // 优先从Session读取（后端真实数据），无则走原有模拟逻辑
      if (Session.get('userInfo')) {
        this.userInfos = Session.get('userInfo');
      } else {
        const userInfos: any = await this.getApiUserInfo();
        this.userInfos = userInfos;
      }
    },
    // 新增：从后端返回的真实数据设置用户信息，并写入Cookies/Session（核心）
    setRealUserInfos(realUserInfo: any) {
      // 整理后端数据，适配前端状态结构
      const userInfos = {
        userName: realUserInfo.userName || realUserInfo.username, // 兼容后端的username/前端的userName
        role: realUserInfo.role, // 后端返回的common/admin
        photo: realUserInfo.avatar || '/uploads/avatar/default_avatar.png', // 用后端默认头像
        time: new Date().getTime(),
        roles: [realUserInfo.role], // 前端roles是数组，适配路由meta.roles
        authBtnList: realUserInfo.role === 'admin' 
          ? ['btn.add', 'btn.del', 'btn.edit', 'btn.link'] 
          : ['btn.add', 'btn.link'], // 按后端角色分配按钮权限
        id: realUserInfo.id, // 保留后端用户ID
      };
      // 写入Pinia状态
      this.userInfos = userInfos;
      // 写入Cookies（适配原有模拟逻辑，防止冲突）
      Cookies.set('userName', userInfos.userName);
      Cookies.set('role', userInfos.role);
      // 写入Session（核心：让setUserInfos能读取到）
      Session.set('userInfo', userInfos);
    },
    // 原有模拟接口逻辑（保留，无需修改）
    async getApiUserInfo() {
      return new Promise((resolve) => {
        setTimeout(() => {
          const role = Cookies.get('role');
          let defaultRoles: Array<string> = [];
          let defaultAuthBtnList: Array<string> = [];
          let adminRoles: Array<string> = ['admin'];
          let adminAuthBtnList: Array<string> = ['btn.add', 'btn.del', 'btn.edit', 'btn.link'];
          let commonRoles: Array<string> = ['common'];
          let commonAuthBtnList: Array<string> = ['btn.add', 'btn.link'];
          if (role === 'admin') {
            defaultRoles = adminRoles;
            defaultAuthBtnList = adminAuthBtnList;
          } else if (role === 'common') {
            defaultRoles = commonRoles;
            defaultAuthBtnList = commonAuthBtnList;
          }
          const userInfos = {
            userName: Cookies.get('userName'),
            role: role,
            photo:
              role === 'admin'
                ? 'https://img2.baidu.com/it/u=1978192862,2048448374&fm=253&fmt=auto&app=138&f=JPEG?w=504&h=500'
                : 'https://img2.baidu.com/it/u=2370931438,70387529&fm=253&fmt=auto&app=138&f=JPEG?w=500&h=500',
            time: new Date().getTime(),
            roles: defaultRoles,
            authBtnList: defaultAuthBtnList,
          };
          resolve(userInfos);
        }, 0);
      });
    },
  },
});