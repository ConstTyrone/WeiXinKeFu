#!/usr/bin/env python3
# db_viewer_sqlite.py
"""
SQLite 用户画像数据库查看和管理工具
每个微信用户拥有独立的画像表
"""

import sys
import json
from datetime import datetime
from database_sqlite_v2 import database_manager
from typing import Optional

class SQLiteUserProfileViewer:
    def __init__(self):
        self.db = database_manager
        self.current_user_id = None
    
    def print_header(self):
        """打印头部信息"""
        print("\n" + "="*60)
        print("🔍 SQLite 用户画像数据库管理工具 (多用户版)")
        print("="*60)
    
    def print_menu(self):
        """打印菜单"""
        print("\n请选择操作：")
        print("1. 设置当前用户 (输入微信用户ID)")
        print("2. 查看用户画像列表")
        print("3. 搜索用户画像")
        print("4. 查看画像详情")
        print("5. 删除用户画像")
        print("6. 查看用户统计信息")
        print("7. 查看所有用户列表")
        print("8. 查看数据库信息")
        print("0. 退出")
        
        if self.current_user_id:
            print(f"\n📌 当前用户: {self.current_user_id}")
            table_name = self.db._get_user_table_name(self.current_user_id)
            print(f"📋 用户表: {table_name}")
    
    def set_current_user(self):
        """设置当前用户"""
        user_id = input("\n请输入微信用户ID: ").strip()
        if user_id:
            self.current_user_id = user_id
            # 确保用户存在
            self.db.get_or_create_user(user_id)
            print(f"✅ 当前用户已设置为: {user_id}")
        else:
            print("❌ 用户ID不能为空")
    
    def check_current_user(self) -> bool:
        """检查是否设置了当前用户"""
        if not self.current_user_id:
            print("❌ 请先设置当前用户（选择1）")
            return False
        return True
    
    def view_profiles(self):
        """查看用户画像列表"""
        if not self.check_current_user():
            return
        
        try:
            page = 1
            page_size = 10
            
            while True:
                offset = (page - 1) * page_size
                profiles, total = self.db.get_user_profiles(
                    self.current_user_id, 
                    limit=page_size, 
                    offset=offset
                )
                
                if not profiles:
                    print("\n📭 暂无用户画像数据")
                    return
                
                print(f"\n📊 用户画像列表 (第{page}页，共{(total-1)//page_size + 1}页，总计{total}条)：")
                print("-" * 80)
                
                for i, profile in enumerate(profiles, 1):
                    print(f"\n{i + offset}. ID: {profile['id']}")
                    print(f"   姓名: {profile['profile_name']}")
                    print(f"   性别: {profile.get('gender', '未知')}")
                    print(f"   年龄: {profile.get('age', '未知')}")
                    print(f"   职位: {profile.get('position', '未知')}")
                    print(f"   公司: {profile.get('company', '未知')}")
                    print(f"   地址: {profile.get('location', '未知')}")
                    print(f"   置信度: {profile.get('confidence_score', 0):.0%}")
                    print(f"   来源: {profile.get('source_type', '未知')}")
                    print(f"   创建时间: {profile.get('created_at', '未知')}")
                
                print("\n" + "-" * 80)
                print("n: 下一页 | p: 上一页 | r: 返回")
                choice = input("请选择: ").strip().lower()
                
                if choice == 'n' and page * page_size < total:
                    page += 1
                elif choice == 'p' and page > 1:
                    page -= 1
                elif choice == 'r':
                    break
                    
        except Exception as e:
            print(f"❌ 查看失败: {e}")
    
    def search_profiles(self):
        """搜索用户画像"""
        if not self.check_current_user():
            return
        
        keyword = input("\n请输入搜索关键词（姓名/公司/职位）: ").strip()
        if not keyword:
            print("❌ 搜索关键词不能为空")
            return
        
        try:
            profiles, total = self.db.get_user_profiles(
                self.current_user_id,
                search=keyword,
                limit=20
            )
            
            if not profiles:
                print(f"\n📭 未找到包含 '{keyword}' 的用户画像")
                return
            
            print(f"\n🔍 搜索结果 (共{total}条)：")
            print("-" * 80)
            
            for i, profile in enumerate(profiles, 1):
                print(f"\n{i}. ID: {profile['id']}")
                print(f"   姓名: {profile['profile_name']}")
                print(f"   公司: {profile.get('company', '未知')}")
                print(f"   职位: {profile.get('position', '未知')}")
                personality = profile.get('personality', '未知')
                if personality and len(personality) > 50:
                    personality = personality[:50] + "..."
                print(f"   性格: {personality}")
                
        except Exception as e:
            print(f"❌ 搜索失败: {e}")
    
    def view_profile_detail(self):
        """查看画像详情"""
        if not self.check_current_user():
            return
        
        try:
            profile_id = int(input("\n请输入画像ID: ").strip())
            profile = self.db.get_user_profile_detail(self.current_user_id, profile_id)
            
            if not profile:
                print(f"❌ 未找到ID为 {profile_id} 的画像")
                return
            
            print(f"\n📋 用户画像详情 (ID: {profile_id})：")
            print("="*60)
            
            # 基本信息
            print("\n【基本信息】")
            print(f"姓名: {profile.get('profile_name', '未知')}")
            print(f"性别: {profile.get('gender', '未知')}")
            print(f"年龄: {profile.get('age', '未知')}")
            print(f"电话: {profile.get('phone', '未知')}")
            print(f"所在地: {profile.get('location', '未知')}")
            
            # 家庭状况
            print("\n【家庭状况】")
            print(f"婚育: {profile.get('marital_status', '未知')}")
            
            # 教育背景
            print("\n【教育背景】")
            print(f"学历: {profile.get('education', '未知')}")
            
            # 工作信息
            print("\n【工作信息】")
            print(f"公司: {profile.get('company', '未知')}")
            print(f"职位: {profile.get('position', '未知')}")
            
            # 其他信息
            print("\n【其他信息】")
            print(f"资产水平: {profile.get('asset_level', '未知')}")
            print(f"性格: {profile.get('personality', '未知')}")
            
            # AI分析信息
            print("\n【AI分析信息】")
            print(f"消息总结: {profile.get('ai_summary', '无')}")
            confidence = profile.get('confidence_score', 0)
            print(f"置信度: {confidence:.0%}" if confidence else "置信度: 0%")
            print(f"消息类型: {profile.get('source_type', '未知')}")
            
            # 时间信息
            print("\n【时间信息】")
            print(f"创建时间: {profile.get('created_at', '未知')}")
            print(f"更新时间: {profile.get('updated_at', '未知')}")
            
            # 原始消息
            print("\n【原始消息】")
            raw_msg = profile.get('raw_message_content', '')
            if raw_msg:
                print(f"{raw_msg[:500]}{'...' if len(raw_msg) > 500 else ''}")
            
            # AI原始响应
            if input("\n是否查看AI原始响应？(y/n): ").strip().lower() == 'y':
                print("\n【AI原始响应】")
                ai_response = profile.get('raw_ai_response', {})
                if isinstance(ai_response, dict):
                    print(json.dumps(ai_response, ensure_ascii=False, indent=2))
                else:
                    print(ai_response)
                
        except ValueError:
            print("❌ 请输入有效的数字ID")
        except Exception as e:
            print(f"❌ 查看失败: {e}")
    
    def delete_profile(self):
        """删除用户画像"""
        if not self.check_current_user():
            return
        
        try:
            profile_id = int(input("\n请输入要删除的画像ID: ").strip())
            
            # 先查看详情
            profile = self.db.get_user_profile_detail(self.current_user_id, profile_id)
            if not profile:
                print(f"❌ 未找到ID为 {profile_id} 的画像")
                return
            
            print(f"\n即将删除: {profile['profile_name']} (ID: {profile_id})")
            if input("确认删除？(y/n): ").strip().lower() == 'y':
                if self.db.delete_user_profile(self.current_user_id, profile_id):
                    print("✅ 删除成功")
                else:
                    print("❌ 删除失败")
                    
        except ValueError:
            print("❌ 请输入有效的数字ID")
        except Exception as e:
            print(f"❌ 删除失败: {e}")
    
    def view_user_stats(self):
        """查看用户统计信息"""
        if not self.check_current_user():
            return
        
        try:
            stats = self.db.get_user_stats(self.current_user_id)
            
            print(f"\n📊 用户统计信息 ({self.current_user_id})：")
            print("="*60)
            print(f"画像总数: {stats.get('total_profiles', 0)}")
            print(f"不同姓名数: {stats.get('unique_names', 0)}")
            print(f"今日新增: {stats.get('today_profiles', 0)}")
            print(f"最后更新: {stats.get('last_profile_at', '无')}")
            print(f"\n配额信息:")
            print(f"已使用: {stats.get('used_profiles', 0)} / {stats.get('max_profiles', 1000)}")
            print(f"每日消息限制: {stats.get('max_daily_messages', 100)}")
            
            # 显示用户表名
            table_name = self.db._get_user_table_name(self.current_user_id)
            print(f"\n数据表: {table_name}")
            
        except Exception as e:
            print(f"❌ 获取统计信息失败: {e}")
    
    def view_all_users(self):
        """查看所有用户列表"""
        try:
            users = self.db.get_all_users()
            
            if not users:
                print("\n📭 暂无用户数据")
                return
            
            print(f"\n👥 用户列表 (总计{len(users)}个用户)：")
            print("-" * 80)
            
            for user in users:
                print(f"\nID: {user['id']}")
                print(f"微信ID: {user['wechat_user_id']}")
                print(f"昵称: {user.get('nickname', '未设置')}")
                print(f"画像数: {user.get('total_profiles', 0)}")
                print(f"表名: {self.db._get_user_table_name(user['wechat_user_id'])}")
                print(f"创建时间: {user.get('created_at', '未知')}")
                
        except Exception as e:
            print(f"❌ 获取用户列表失败: {e}")
    
    def view_database_info(self):
        """查看数据库信息"""
        try:
            print(f"\n💾 数据库信息：")
            print("="*60)
            print(f"数据库文件: {self.db.db_path}")
            print(f"数据库类型: SQLite")
            print(f"数据库大小: {self._get_file_size(self.db.db_path)}")
            
            # 获取所有表信息
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = cursor.fetchall()
                
                print(f"\n📋 数据表列表 (共{len(tables)}个表)：")
                for table in tables:
                    table_name = table['name']
                    cursor.execute(f"SELECT COUNT(*) as count FROM {table_name}")
                    count = cursor.fetchone()['count']
                    print(f"  {table_name}: {count} 条记录")
            
        except Exception as e:
            print(f"❌ 获取数据库信息失败: {e}")
    
    def _get_file_size(self, file_path: str) -> str:
        """获取文件大小"""
        try:
            import os
            size = os.path.getsize(file_path)
            if size < 1024:
                return f"{size} B"
            elif size < 1024 * 1024:
                return f"{size / 1024:.1f} KB"
            else:
                return f"{size / (1024 * 1024):.1f} MB"
        except:
            return "未知"
    
    def run(self):
        """运行主程序"""
        self.print_header()
        
        while True:
            self.print_menu()
            choice = input("\n请选择 (0-8): ").strip()
            
            if choice == '0':
                print("\n👋 再见！")
                break
            elif choice == '1':
                self.set_current_user()
            elif choice == '2':
                self.view_profiles()
            elif choice == '3':
                self.search_profiles()
            elif choice == '4':
                self.view_profile_detail()
            elif choice == '5':
                self.delete_profile()
            elif choice == '6':
                self.view_user_stats()
            elif choice == '7':
                self.view_all_users()
            elif choice == '8':
                self.view_database_info()
            else:
                print("❌ 无效选择，请重试")

if __name__ == "__main__":
    try:
        viewer = SQLiteUserProfileViewer()
        viewer.run()
    except KeyboardInterrupt:
        print("\n\n👋 程序已退出")
    except Exception as e:
        print(f"\n❌ 程序错误: {e}")
        sys.exit(1)