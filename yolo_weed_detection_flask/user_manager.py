import sqlite3
import hashlib
import json
from datetime import datetime, timedelta
import jwt
import os
import secrets
import base64
import time

class UserManager:
    def __init__(self, db_path='weed_detection.db'):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        self.db_path = db_path if os.path.isabs(db_path) else os.path.join(base_dir, db_path)
        # 使用固定密钥，避免每次启动变化导致token失效
        self.secret_key = "my_very_long_and_secure_jwt_secret_key_1234567890_abcd"
        print(f"JWT 密钥已设置，长度: {len(self.secret_key)}")
        self.init_user_table()
        self.create_default_admin()
    
    def init_user_table(self):
        """初始化用户表"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                name TEXT,
                sex TEXT,
                email TEXT,
                tel TEXT,
                avatar TEXT,
                role TEXT DEFAULT 'common',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                last_login DATETIME
            )
        ''')
        
        conn.commit()
        conn.close()
        print("✅ 用户表初始化完成")
    
    def create_default_admin(self):
        """创建默认管理员用户（如果不存在）"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM users WHERE username = ?', ('admin',))
            if not cursor.fetchone():
                hashed_password = self.hash_password('admin123')
                cursor.execute('''
                    INSERT INTO users (username, password, name, email, role)
                    VALUES (?, ?, ?, ?, ?)
                ''', ('admin', hashed_password, '系统管理员', 'admin@example.com', 'admin'))
                conn.commit()
                print("✅ 创建默认管理员用户：admin/admin123")
            
            conn.close()
        except Exception as e:
            print(f"❌ 创建默认用户失败: {e}")
    
    def hash_password(self, password):
        """密码哈希处理"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def verify_password(self, password, hashed):
        """验证密码"""
        return self.hash_password(password) == hashed
    
    def register_user(self, username, password, confirm_password, **kwargs):
        """用户注册"""
        try:
            # 验证参数
            if not username or not password:
                return {"code": 400, "msg": "用户名和密码不能为空"}
            
            if password != confirm_password:
                return {"code": 400, "msg": "两次密码不一致"}
            
            if len(username) < 3 or len(username) > 20:
                return {"code": 400, "msg": "用户名长度需在3-20个字符之间"}
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 检查用户名是否已存在
            cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
            if cursor.fetchone():
                conn.close()
                return {"code": 400, "msg": "用户名已存在"}
            
            # 插入新用户
            hashed_password = self.hash_password(password)
            
            user_data = {
                'username': username,
                'password': hashed_password,
                'name': kwargs.get('name', username),
                'sex': kwargs.get('sex', ''),
                'email': kwargs.get('email', ''),
                'tel': kwargs.get('tel', ''),
                'avatar': kwargs.get('avatar', '/uploads/images/default_avatar.png'),
                'role': kwargs.get('role', 'common'),
                'created_at': datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
            }
            
            columns = ', '.join(user_data.keys())
            placeholders = ', '.join(['?' for _ in user_data])
            
            cursor.execute(f'''
                INSERT INTO users ({columns}) 
                VALUES ({placeholders})
            ''', list(user_data.values()))
            
            conn.commit()
            user_id = cursor.lastrowid
            
            # 获取创建的用户信息
            cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
            user_row = cursor.fetchone()
            
            conn.close()
            
            if user_row:
                user_info = self.format_user_data(user_row)
                return {
                    "code": 0,
                    "msg": "注册成功",
                    "data": user_info
                }
            else:
                return {"code": 500, "msg": "注册失败"}
            
        except Exception as e:
            print(f"❌ 用户注册失败: {e}")
            return {"code": 500, "msg": f"注册失败: {str(e)}"}
    
    def login_user(self, username, password):
        """用户登录"""
        try:
            print(f"[DEBUG] 尝试登录用户: {username}")
            
            if not username or not password:
                return {"code": 400, "msg": "用户名和密码不能为空"}
            
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM users WHERE username = ?
            ''', (username,))
            
            user_row = cursor.fetchone()
            
            if not user_row:
                conn.close()
                print(f"[DEBUG] 用户 {username} 不存在")
                return {"code": 400, "msg": "用户不存在"}
            
            # 将 Row 对象转换为字典以便访问
            user_dict = dict(user_row)
            print(f"[DEBUG] 查询到的用户信息: {user_dict}")
            
            # 验证密码
            stored_password_hash = user_dict['password']
            input_password_hash = self.hash_password(password)
            
            print(f"[DEBUG] 存储的密码哈希: {stored_password_hash[:20]}...")
            print(f"[DEBUG] 输入的密码哈希: {input_password_hash[:20]}...")
            
            if not self.verify_password(password, stored_password_hash):
                conn.close()
                print(f"[DEBUG] 密码验证失败")
                return {"code": 400, "msg": "密码错误"}
            
            # 更新最后登录时间
            cursor.execute('''
                UPDATE users SET last_login = ? WHERE id = ?
            ''', (datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"), user_dict['id']))
            conn.commit()
            
            # 生成JWT token
            user_info = self.format_user_data(user_row)
            print(f"[DEBUG] 格式化后的用户信息: {user_info}")
            
            # 生成 token payload
            payload = {
                'user_id': user_info['id'],
                'username': user_info['username'],
                'role': user_info['role'],
                'exp': datetime.utcnow() + timedelta(hours=24)  # 24小时过期
            }
            
            token = jwt.encode(payload, self.secret_key, algorithm='HS256')
            
            # 如果是字符串类型，直接使用
            if isinstance(token, bytes):
                token = token.decode('utf-8')
            
            print(f"[DEBUG] 生成的token: {token[:30]}...")
            
            conn.close()
            
            return {
                "code": 0,
                "msg": "登录成功",
                "data": {
                    "token": token,
                    "userInfo": user_info
                }
            }
            
        except Exception as e:
            print(f"❌ 用户登录失败: {e}")
            import traceback
            traceback.print_exc()
            return {"code": 500, "msg": f"登录失败: {str(e)}"}
    
    def get_user_by_id(self, user_id):
        """根据ID获取用户"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
            user = cursor.fetchone()
            
            conn.close()
            
            if user:
                return {"code": 0, "data": self.format_user_data(user)}
            else:
                return {"code": 400, "msg": "用户不存在"}
                
        except Exception as e:
            return {"code": 500, "msg": str(e)}
    
    def get_user_by_username(self, username):
        """根据用户名获取用户"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
            user = cursor.fetchone()
            
            conn.close()
            
            if user:
                return {"code": 0, "data": self.format_user_data(user)}
            else:
                return {"code": 400, "msg": "用户不存在"}
                
        except Exception as e:
            return {"code": 500, "msg": str(e)}
    
    def get_all_users(self, page=1, page_size=10, search=None):
        """获取所有用户（分页）"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # 构建查询条件
            conditions = []
            params = []
            
            if search:
                conditions.append("(username LIKE ? OR name LIKE ?)")
                params.extend([f"%{search}%", f"%{search}%"])
            
            where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
            
            # 计算总数
            cursor.execute(f"SELECT COUNT(*) as total FROM users {where_clause}", params)
            total = cursor.fetchone()['total']
            
            # 获取分页数据
            offset = (page - 1) * page_size
            
            query = f'''
                SELECT * FROM users 
                {where_clause}
                ORDER BY created_at DESC 
                LIMIT ? OFFSET ?
            '''
            cursor.execute(query, params + [page_size, offset])
            
            users = [self.format_user_data(row) for row in cursor.fetchall()]
            
            conn.close()
            
            return {
                "code": 0,
                "data": {
                    "records": users,
                    "total": total,
                    "page": page,
                    "page_size": page_size
                }
            }
            
        except Exception as e:
            return {"code": 500, "msg": str(e)}
    
    def update_user(self, user_id, update_data):
        """更新用户信息"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 构建更新语句
            set_clause = ', '.join([f"{key} = ?" for key in update_data.keys()])
            values = list(update_data.values())
            values.append(user_id)
            
            cursor.execute(f'''
                UPDATE users SET {set_clause} WHERE id = ?
            ''', values)
            
            conn.commit()
            affected = cursor.rowcount
            conn.close()
            
            if affected > 0:
                return {"code": 0, "msg": "更新成功"}
            else:
                return {"code": 400, "msg": "用户不存在"}
                
        except Exception as e:
            return {"code": 500, "msg": str(e)}
    
    def delete_user(self, user_id):
        """删除用户"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('DELETE FROM users WHERE id = ?', (user_id,))
            
            conn.commit()
            affected = cursor.rowcount
            conn.close()
            
            if affected > 0:
                return {"code": 0, "msg": "删除成功"}
            else:
                return {"code": 400, "msg": "用户不存在"}
                
        except Exception as e:
            return {"code": 500, "msg": str(e)}
    
    def format_user_data(self, user_row):
        """格式化用户数据为字典"""
        if not user_row:
            return None
            
        # 如果已经是字典，直接处理
        if isinstance(user_row, dict):
            user_dict = user_row.copy()
        else:
            # 如果是Row对象或元组，转换为字典
            if hasattr(user_row, '_fields'):  # sqlite3.Row对象
                user_dict = dict(zip(user_row._fields, user_row))
            else:  # 元组
                columns = ['id', 'username', 'password', 'name', 'sex', 'email', 
                          'tel', 'avatar', 'role', 'created_at', 'last_login']
                user_dict = dict(zip(columns, user_row))
        
        # 移除敏感信息
        if 'password' in user_dict:
            user_dict.pop('password', None)
        
        # 确保id是整数
        if 'id' in user_dict:
            user_dict['id'] = int(user_dict['id'])
        
        # 处理角色显示
        role_mapping = {
            'admin': '管理员',
            'common': '普通用户',
            'others': '其他用户'
        }
        user_dict['role_display'] = role_mapping.get(user_dict.get('role', 'common'), user_dict.get('role', 'common'))
        
        # 确保有userId字段（前端需要）
        if 'id' in user_dict and 'userId' not in user_dict:
            user_dict['userId'] = user_dict['id']
        
        # 确保有userName字段（前端需要）
        if 'username' in user_dict and 'userName' not in user_dict:
            user_dict['userName'] = user_dict['username']
        
        # 确保有roles字段（前端需要）
        if 'role' in user_dict and 'roles' not in user_dict:
            user_dict['roles'] = [user_dict['role']]
        
        return user_dict
    
    def verify_token(self, token):
        """验证JWT token"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=['HS256'])
            return {"code": 0, "data": payload}
        except jwt.ExpiredSignatureError:
            return {"code": 401, "msg": "Token已过期"}
        except jwt.InvalidTokenError:
            return {"code": 401, "msg": "无效的Token"}
        except Exception as e:
            return {"code": 500, "msg": f"Token验证失败: {str(e)}"}