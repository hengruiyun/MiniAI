#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Ollama Settings Application
Author: 267278466@qq.com
Version: 1.0.0
"""

import os
import sys
import json
import time
import threading
import subprocess
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, filedialog
import requests
from pathlib import Path
import winreg
from datetime import datetime
import webbrowser
import locale
import tkinter.font as tkFont
import argparse

class OllamaSettings:
    @staticmethod
    def get_icon_path():
        """Get the correct icon path for both dev and PyInstaller environments"""
        try:
            # Check if running in PyInstaller bundle
            if getattr(sys, 'frozen', False):
                # PyInstaller bundle
                base_path = getattr(sys, '_MEIPASS', '')
                icon_path = Path(base_path) / "mrcai.ico"
            else:
                # Normal Python script
                icon_path = Path("mrcai.ico")
            
            return icon_path if icon_path.exists() else None
        except Exception:
            return None
    
    @staticmethod
    def start_ollama_hidden():
        """Start Ollama service with completely hidden window (command line mode)"""
        # Find ollama path
        ollama_path = None
        possible_paths = [
            Path("File/ollama.exe"),
            Path("ollama.exe"),
            Path.home() / "AppData/Local/Programs/Ollama/ollama.exe"
        ]
        
        for path in possible_paths:
            if path.exists():
                ollama_path = path
                break
        
        if not ollama_path:
            print("Error: Ollama executable not found")
            return False
        
        try:
            print(f"Starting Ollama service from: {ollama_path}")
            
            # Start ollama serve with completely hidden window
            if sys.platform == "win32":
                # Use multiple flags to ensure complete window hiding
                CREATE_NO_WINDOW = 0x08000000
                DETACHED_PROCESS = 0x00000008
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                startupinfo.wShowWindow = 0  # SW_HIDE
                
                subprocess.Popen(
                    [str(ollama_path), "serve"],
                    cwd=str(ollama_path.parent),
                    creationflags=CREATE_NO_WINDOW | DETACHED_PROCESS,
                    startupinfo=startupinfo,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    stdin=subprocess.DEVNULL
                )
            else:
                subprocess.Popen(
                    [str(ollama_path), "serve"],
                    cwd=str(ollama_path.parent),
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    stdin=subprocess.DEVNULL
                )
            
            print("Ollama service started successfully in hidden mode")
            
            # Wait a moment to verify startup
            time.sleep(3)
            
            # Check if service is running
            try:
                response = requests.get("http://localhost:11434/api/tags", timeout=5)
                if response.status_code == 200:
                    print("Ollama service is running and responding")
                    return True
                else:
                    print(f"Ollama service may not be ready (status: {response.status_code})")
                    return True  # Still return True as process started
            except requests.exceptions.RequestException:
                print("Ollama service started but not yet responding to API calls")
                return True  # Process started, just not ready yet
            
        except Exception as e:
            print(f"Error starting Ollama service: {e}")
            return False
    
    def __init__(self):
        # Detect system language
        self.detect_language()
        
        self.root = tk.Tk()
        
        # Hide window initially to prevent flicker
        self.root.withdraw()
        
        self.root.title(self.get_text("window_title"))
        
        # Set window icon
        try:
            icon_path = self.get_icon_path()
            if icon_path:
                self.root.iconbitmap(str(icon_path))
        except Exception:
            pass  # Ignore if icon file not found or cannot be loaded
        
        self.root.geometry("1024x768")
        self.root.resizable(True, True)
        
        # Set larger font for all widgets
        self.setup_fonts()
        
        # Configuration
        self.config_file = Path("ollama_config.json")
        self.config = self.load_config()
        
        # Ollama paths
        self.ollama_path = self.find_ollama_path()
        self.models_path = Path.home() / ".ollama" / "models"
        
        # Variables
        self.chat_history = []
        self.current_model = tk.StringVar()
        self.auto_start_var = tk.BooleanVar()
        
        # Environment variables - load from environment first, show empty if not set
        self.ollama_host = tk.StringVar(value=os.environ.get('OLLAMA_HOST', ''))
        self.ollama_port = tk.StringVar(value=os.environ.get('OLLAMA_PORT', ''))
        self.ollama_models = tk.StringVar(value=os.environ.get('OLLAMA_MODELS', ''))
        self.ollama_keep_alive = tk.StringVar(value=os.environ.get('OLLAMA_KEEP_ALIVE', ''))
        
        # Store original values for comparison
        self.original_values = {
            'auto_start': False,
            'ollama_host': self.ollama_host.get(),
            'ollama_port': self.ollama_port.get(),
            'ollama_models': self.ollama_models.get(),
            'ollama_keep_alive': self.ollama_keep_alive.get()
        }
        
        # Initialize GUI
        self.setup_gui()
        self.load_settings()
        self.refresh_models() # Auto-refresh models on startup
    
    def detect_language(self):
        """Detect system language and set interface language"""
        try:
            # Get system locale
            system_locale = locale.getdefaultlocale()[0]
            if system_locale and system_locale.startswith('zh'):
                self.language = 'zh'
            else:
                self.language = 'en'
        except:
            self.language = 'en'  # Default to English
        
        # Text dictionary for bilingual support
        self.texts = {
            'en': {
                'window_title': 'Mini Ollama - 267278466@qq.com',
                'tab_autostart': 'Auto Start',
                'tab_models': 'Model Management',
                'tab_environment': 'Environment Variables',
                'tab_chat': 'Chat Interface',
                'autostart_title': 'Auto Start Settings',
                'autostart_checkbox': 'Auto start Ollama service on boot',
                'status_enabled': 'Status: Auto start enabled',
                'status_disabled': 'Status: Auto start disabled',
                'status_unknown': 'Status: Unknown',
                'start_service': 'Start Ollama Service',
                'stop_service': 'Stop Ollama Service',
                'check_status': 'Check Service Status',
                'path_info': 'Ollama Path Information',
                'ollama_path': 'Ollama Path',
                'models_path': 'Models Path',
                'ollama_not_found': 'Ollama executable not found',
                'available_models': 'Available Models (Online)',
                'local_models': 'Local Models',
                'model_name': 'Name',
                'model_size': 'Size',
                'model_description': 'Description',
                'download_model': 'Download Selected Model',
                'refresh_online': 'Refresh Online Models',
                'delete_model': 'Delete Selected Model',
                'refresh_local': 'Refresh Local Models',
                'select_model': 'Select Model:',
                'refresh': 'Refresh',
                'clear_chat': 'Clear Chat',
                'save_chat': 'Save Chat',
                'show_verbose': 'Show Verbose Info',
                'send': 'Send',
                'env_variables': 'Ollama Environment Variables Settings',
                'host_address': 'Server Address (OLLAMA_HOST)',
                'host_label': 'Host Address:',
                'host_default': 'Default: localhost (local server)',
                'port_number': 'Port Number (OLLAMA_PORT)',
                'port_label': 'Port Number:',
                'port_default': 'Default: 11434',
                'models_storage': 'Models Storage Path (OLLAMA_MODELS)',
                'models_path_label': 'Models Storage Path:',
                'browse': 'Browse',
                'models_default': 'Leave empty to use default path: ~/.ollama/models',
                'keep_alive': 'Model Keep Alive Time (OLLAMA_KEEP_ALIVE)',
                'keep_alive_label': 'Keep Alive Time:',
                'keep_alive_format': 'Format: 5m (minutes), 1h (hours), 0 (unload immediately)',
                'reset_defaults': 'Reset to Defaults',
                'test_connection': 'Test Connection',
                'current_env': 'Current Environment Information',
                'save_settings': 'Save Settings',
                'exit': 'Exit',
                'ready': 'Ready',
                'success': 'Success',
                'error': 'Error',
                'warning': 'Warning',
                'confirm': 'Confirm',
                'settings_saved': 'Settings saved successfully',
                'save_failed': 'Failed to save settings',
                'connection_success': 'Successfully connected to Ollama server',
                'connection_failed': 'Connection test failed',
                'service_started': 'Starting Ollama service...',
                'service_stopped': 'Ollama service stopped',
                'service_running': 'Ollama service is running normally',
                'service_not_running': 'Ollama service is not running',
                'env_applied': 'Environment variables applied',
                'env_reset': 'Environment variables reset to defaults',
                'select_model_warning': 'Please select a model',
                'select_download_warning': 'Please select a model to download',
                'service_not_running_error': 'Ollama service is not running, please start the service first',
                'delete_confirm': 'Are you sure you want to delete model',
                'no_chat_history': 'No chat history to save',
                'clear_chat_confirm': 'Are you sure you want to clear the chat history?',
                'downloading_model': 'Downloading model',
                'download_complete': 'Model download complete',
                'download_failed': 'Download failed',
                'generating_reply': 'Generating reply...',
                'reply_complete': 'Reply complete',
                'reply_failed': 'Reply failed',
                'system_message': 'Welcome to Ollama Chat Interface! Please select a model to start chatting.',
                'chat_cleared': 'Chat history cleared',
                'chat_saved': 'Chat history saved to',
                'system': 'System',
                'user': 'User',
                'assistant': 'Assistant',
                'config_save_failed': 'Failed to save configuration',
                'connection_testing': 'Testing connection...',
                'connection_success_detail': 'Successfully connected to Ollama server\nAddress',
                'connection_failed_status': 'Connection failed, status code',
                'connection_test_failed': 'Connection test failed',
                'ollama_not_found_error': 'Ollama executable not found',
                'autostart_setup_failed': 'Failed to set up auto start',
                'service_start_failed': 'Failed to start Ollama service',
                'service_stop_failed': 'Failed to stop Ollama service',
                'autostart_added': 'Added to auto start',
                'autostart_removed': 'Removed from auto start',
                'getting_models_failed': 'Failed to get model list',
                'getting_online_models': 'Getting online model list...',
                'getting_online_models_failed': 'Failed to get online models',
                'online_models_updated': 'Online model list updated',
                'downloading_model_status': 'Downloading model',
                'model_download_complete': 'Model download complete',
                'model_deleted': 'Model deleted',
                'delete_model_confirm': 'Are you sure you want to delete model',
                'delete_model_failed': 'Failed to delete model',
                'save_failed_error': 'Save failed',
                'request_failed': 'Request failed',
                'generate_reply_failed': 'Failed to generate reply',
                'service_not_responding': 'Ollama service not responding',
                'service_starting': 'Starting Ollama service...',
                'verbose_info': 'Verbose Info',
                'model_info': 'Model',
                'total_time': 'Total Time',
                'load_time': 'Load Time',
                'prompt_eval': 'Prompt Eval',
                'generate_eval': 'Generate Eval',
                'tokens': 'tokens',
                'current_env_info': 'Current Environment Variables',
                'not_set': 'Not Set',
                'server_address': 'Server Address',
                'hengruiyun_link': 'HengruiYun'
            },
            'zh': {
                'window_title': '迷你Ollama - 267278466@qq.com',
                'tab_autostart': '开机启动',
                'tab_models': '模型管理',
                'tab_environment': '环境变量',
                'tab_chat': '聊天界面',
                'autostart_title': '开机自动启动设置',
                'autostart_checkbox': '开机自动启动 Ollama 服务',
                'status_enabled': '状态: 已启用开机启动',
                'status_disabled': '状态: 未启用开机启动',
                'status_unknown': '状态: 无法检查',
                'start_service': '启动 Ollama 服务',
                'stop_service': '停止 Ollama 服务',
                'check_status': '检查服务状态',
                'path_info': 'Ollama 路径信息',
                'ollama_path': 'Ollama 路径',
                'models_path': '模型路径',
                'ollama_not_found': '未找到 Ollama 可执行文件',
                'available_models': '可用模型 (在线)',
                'local_models': '本地模型',
                'model_name': '名称',
                'model_size': '大小',
                'model_description': '描述',
                'download_model': '下载模型',
                'refresh_online': '刷新在线模型',
                'delete_model': '删除模型',
                'refresh_local': '刷新本地模型',
                'select_model': '选择模型:',
                'refresh': '刷新',
                'clear_chat': '清空聊天',
                'save_chat': '保存聊天',
                'show_verbose': '显示详细信息',
                'send': '发送',
                'env_variables': 'Ollama 环境变量设置',
                'host_address': '服务器地址 (OLLAMA_HOST)',
                'host_label': '主机地址:',
                'host_default': '默认: localhost (本地服务器)',
                'port_number': '端口号 (OLLAMA_PORT)',
                'port_label': '端口号:',
                'port_default': '默认: 11434',
                'models_storage': '模型存储路径 (OLLAMA_MODELS)',
                'models_path_label': '模型存储路径:',
                'browse': '浏览',
                'models_default': '留空使用默认路径: ~/.ollama/models',
                'keep_alive': '模型保持活跃时间 (OLLAMA_KEEP_ALIVE)',
                'keep_alive_label': '保持活跃时间:',
                'keep_alive_format': '格式: 5m (分钟), 1h (小时), 0 (立即卸载)',
                'reset_defaults': '重置为默认',
                'test_connection': '测试连接',
                'current_env': '当前环境信息',
                'save_settings': '保存设置',
                'exit': '退出',
                'ready': '就绪',
                'success': '成功',
                'error': '错误',
                'warning': '警告',
                'confirm': '确认',
                'settings_saved': '设置已保存',
                'save_failed': '保存设置失败',
                'connection_success': '成功连接到 Ollama 服务器',
                'connection_failed': '连接测试失败',
                'service_started': '正在启动 Ollama 服务...',
                'service_stopped': 'Ollama 服务已停止',
                'service_running': 'Ollama 服务运行正常',
                'service_not_running': 'Ollama 服务未运行',
                'env_applied': '环境变量已应用',
                'env_reset': '环境变量已重置为默认值',
                'select_model_warning': '请选择一个模型',
                'select_download_warning': '请选择要下载的模型',
                'service_not_running_error': 'Ollama 服务未运行，请先启动服务',
                'delete_confirm': '确定要删除模型',
                'no_chat_history': '没有聊天记录可保存',
                'clear_chat_confirm': '确定要清空聊天记录吗？',
                'downloading_model': '正在下载模型',
                'download_complete': '模型下载完成',
                'download_failed': '下载失败',
                'generating_reply': '正在生成回复...',
                'reply_complete': '回复完成',
                'reply_failed': '回复失败',
                'system_message': '欢迎使用 迷你Ollama 聊天界面! 请选择一个模型开始对话。没有模型请先下载模型',
                'chat_cleared': '聊天记录已清空',
                'chat_saved': '聊天记录已保存到',
                'system': '系统',
                'user': '用户',
                'assistant': '助手',
                'config_save_failed': '保存配置失败',
                'connection_testing': '正在测试连接...',
                'connection_success_detail': '成功连接到 Ollama 服务器\n地址',
                'connection_failed_status': '连接失败，状态码',
                'connection_test_failed': '连接测试失败',
                'ollama_not_found_error': '未找到 Ollama 可执行文件',
                'autostart_setup_failed': '设置开机启动失败',
                'service_start_failed': '启动 Ollama 服务失败',
                'service_stop_failed': '停止 Ollama 服务失败',
                'autostart_added': '已添加到开机启动',
                'autostart_removed': '已从开机启动移除',
                'getting_models_failed': '获取模型列表失败',
                'getting_online_models': '正在获取在线模型列表...',
                'getting_online_models_failed': '获取在线模型失败',
                'online_models_updated': '在线模型列表已更新',
                'downloading_model_status': '正在下载模型',
                'model_download_complete': '模型下载完成',
                'model_deleted': '模型已删除',
                'delete_model_confirm': '确定要删除模型',
                'delete_model_failed': '删除模型失败',
                'save_failed_error': '保存失败',
                'request_failed': '请求失败',
                'generate_reply_failed': '生成回复失败',
                'service_not_responding': 'Ollama 服务未响应',
                'service_starting': '正在启动 Ollama 服务...',
                'verbose_info': '详细信息',
                'model_info': '模型',
                'total_time': '总时间',
                'load_time': '加载时间',
                'prompt_eval': '提示评估',
                'generate_eval': '生成评估',
                'tokens': 'tokens',
                'current_env_info': '当前环境变量',
                'not_set': '未设置',
                'server_address': '服务器地址',
                'hengruiyun_link': 'HengruiYun'
            }
        }
    
    def get_text(self, key):
        """Get text in current language"""
        text = self.texts[self.language].get(key, key)
        return text if text is not None else key
        
    def find_ollama_path(self):
        """Find Ollama executable path"""
        possible_paths = [
            Path.home() / "AppData/Local/Programs/Ollama/ollama.exe",
            Path("ollama.exe"),
            Path("ollama.exe")
        ]
        
        for path in possible_paths:
            if path.exists():
                return path
        
        # Try PATH
        try:
            if sys.platform == "win32":
                CREATE_NO_WINDOW = 0x08000000
                result = subprocess.run(["where", "ollama"], capture_output=True, text=True, encoding='utf-8', errors='ignore', creationflags=CREATE_NO_WINDOW)
            else:
                result = subprocess.run(["which", "ollama"], capture_output=True, text=True, encoding='utf-8', errors='ignore')
            if result.returncode == 0:
                return Path(result.stdout.strip().split('\n')[0])
        except:
            pass
        
        return None
    
    def center_window(self):
        """Center the window on screen"""
        self.root.update_idletasks()
        
        # Get window dimensions
        window_width = self.root.winfo_width()
        window_height = self.root.winfo_height()
        
        # Get screen dimensions
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        
        # Calculate center position
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        
        # Set window position
        self.root.geometry(f"{window_width}x{window_height}+{x}+{y}")
    
    def setup_fonts(self):
        """Setup fonts"""
        # Default font
        self.default_font = tkFont.Font(family="Microsoft YaHei", size=10)
        
        # Bold font
        self.bold_font = tkFont.Font(family="Microsoft YaHei", size=10, weight="bold")
        
        # Title font
        self.title_font = tkFont.Font(family="Microsoft YaHei", size=11, weight="bold")
        
        # Button font
        self.button_font = tkFont.Font(family="Microsoft YaHei", size=10)
        
        # Label font
        self.label_font = tkFont.Font(family="Microsoft YaHei", size=10)
        
        # Entry font
        self.entry_font = tkFont.Font(family="Microsoft YaHei", size=10)
        
        # Standard control sizes
        self.button_width = 18
        self.entry_width = 35
        self.label_width = 20
        self.small_button_width = 12
        self.large_button_width = 25
    
    def load_config(self):
        """Load configuration from file"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
        return {
            "auto_start": False,
            "selected_model": "",
            "chat_history": [],
            "window_geometry": "1024x768",
            "ollama_host": "localhost",
            "ollama_port": "11434",
            "ollama_models": "",
            "ollama_keep_alive": "5m"
        }
    
    def save_config(self):
        """Save configuration to file"""
        self.config["auto_start"] = self.auto_start_var.get()
        self.config["selected_model"] = self.current_model.get()
        self.config["window_geometry"] = self.root.geometry()
        self.config["ollama_host"] = self.ollama_host.get()
        self.config["ollama_port"] = self.ollama_port.get()
        self.config["ollama_models"] = self.ollama_models.get()
        self.config["ollama_keep_alive"] = self.ollama_keep_alive.get()
        
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            messagebox.showerror(self.get_text("error"), f"{self.get_text('config_save_failed')}: {e}")
    
    def setup_gui(self):
        """Setup the GUI"""
        self.root.title(self.get_text("window_title"))
        self.root.geometry("1024x768")
        
        # Set icon
        try:
            icon_path = self.get_icon_path()
            if icon_path:
                self.root.iconbitmap(str(icon_path))
        except Exception as e:
            print(f"Failed to set icon: {e}")
        
        # Configure ttk styles
        style = ttk.Style()
        style.configure("TLabel", font=self.label_font)
        style.configure("TButton", font=self.button_font)
        style.configure("TCheckbutton", font=self.label_font)
        style.configure("TEntry", font=self.entry_font)
        style.configure("TCombobox", font=self.entry_font)
        style.configure("TNotebook", font=self.title_font)
        style.configure("TNotebook.Tab", font=self.label_font)
        style.configure("TLabelFrame", font=self.bold_font)
        
        # Center window
        self.center_window()
        
        # Create main frame
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        # Create notebook for tabs
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True, pady=(0, 15))
        
        # Setup tabs
        self.setup_chat_tab(self.notebook)
        self.setup_model_tab(self.notebook)
        self.setup_autostart_tab(self.notebook)
        self.setup_env_tab(self.notebook)
        
        # Create button frame
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        # Create HengruiYun link (bottom left)
        self.hengruiyun_label = ttk.Label(button_frame, text=self.get_text("hengruiyun_link"), 
                                         foreground="blue", cursor="hand2", font=self.label_font)
        self.hengruiyun_label.pack(side=tk.LEFT, padx=(0, 15))
        self.hengruiyun_label.bind("<Button-1>", self.open_hengruiyun_link)
        
        # Create status bar
        self.status_label = ttk.Label(button_frame, text=self.get_text("ready"), 
                                     relief=tk.SUNKEN, anchor=tk.W, font=self.label_font)
        self.status_label.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 15))
        
        # Create buttons with uniform size
        self.exit_btn = ttk.Button(button_frame, text=self.get_text("exit"), 
                                  command=self.exit_application, width=self.button_width)
        self.exit_btn.pack(side=tk.RIGHT, padx=(10, 0))
        
        self.save_btn = ttk.Button(button_frame, text=self.get_text("save_settings"), 
                                  command=self.save_settings, width=self.button_width)
        self.save_btn.pack(side=tk.RIGHT)
        
        # Load settings
        self.load_settings()
        
        # Center window and show it after everything is set up
        self.center_window()
        self.root.deiconify()  # Show the window
        
        # Auto-refresh online models on startup
        self.root.after(1000, self.refresh_online_models)
        
        # Update status
        self.update_status(self.get_text("ready"))
    
    def setup_autostart_tab(self, notebook):
        """Setup auto-start tab"""
        frame = ttk.Frame(notebook)
        notebook.add(frame, text=self.get_text("tab_autostart"))
        
        # Auto-start frame
        autostart_frame = ttk.LabelFrame(frame, text=self.get_text("autostart_title"), padding=20)
        autostart_frame.pack(fill=tk.X, padx=20, pady=20)
        
        # Auto-start checkbox
        self.auto_start_var = tk.BooleanVar()
        autostart_cb = ttk.Checkbutton(autostart_frame, text=self.get_text("autostart_checkbox"), 
                                      variable=self.auto_start_var, command=self.toggle_autostart)
        autostart_cb.pack(anchor=tk.W, pady=(0, 15))
        
        # Status label
        self.autostart_status = ttk.Label(autostart_frame, text=self.get_text("status_unknown"))
        self.autostart_status.pack(anchor=tk.W, pady=(0, 20))
        
        # Service control frame
        service_frame = ttk.Frame(autostart_frame)
        service_frame.pack(fill=tk.X, pady=(15, 0))
        
        # Service buttons with uniform size
        start_btn = ttk.Button(service_frame, text=self.get_text("start_service"), 
                              command=self.start_ollama_service, width=self.button_width)
        start_btn.pack(side=tk.LEFT, padx=(0, 15))
        
        stop_btn = ttk.Button(service_frame, text=self.get_text("stop_service"), 
                             command=self.stop_ollama_service, width=self.button_width)
        stop_btn.pack(side=tk.LEFT, padx=(0, 15))
        
        check_btn = ttk.Button(service_frame, text=self.get_text("check_status"), 
                              command=self.check_ollama_status, width=self.button_width)
        check_btn.pack(side=tk.LEFT)
        
        # Path info frame
        path_frame = ttk.LabelFrame(frame, text=self.get_text("path_info"), padding=20)
        path_frame.pack(fill=tk.X, padx=20, pady=20)
        
        # Ollama path
        path_label = ttk.Label(path_frame, text=self.get_text("ollama_path"), font=self.bold_font)
        path_label.pack(anchor=tk.W, pady=(0, 5))
        
        ollama_path_text = self.ollama_path if self.ollama_path else self.get_text("ollama_not_found")
        path_value = ttk.Label(path_frame, text=str(ollama_path_text), foreground="blue")
        path_value.pack(anchor=tk.W, pady=(0, 15))
        
        # Models path
        models_label = ttk.Label(path_frame, text=self.get_text("models_path"), font=self.bold_font)
        models_label.pack(anchor=tk.W, pady=(0, 5))
        
        models_path = os.path.expanduser("~/.ollama/models")
        models_value = ttk.Label(path_frame, text=models_path, foreground="blue")
        models_value.pack(anchor=tk.W)
    
    def setup_model_tab(self, notebook):
        """Setup model management tab"""
        frame = ttk.Frame(notebook)
        notebook.add(frame, text=self.get_text("tab_models"))
        
        # Split into two panes
        paned = ttk.PanedWindow(frame, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Left pane - Available models
        left_frame = ttk.LabelFrame(paned, text=self.get_text("available_models"), padding=15)
        paned.add(left_frame, weight=1)
        
        # Online models tree with consistent column widths
        self.online_models_tree = ttk.Treeview(left_frame, columns=("size", "description"), 
                                              show="tree headings", height=12)
        self.online_models_tree.heading("#0", text=self.get_text("model_name"))
        self.online_models_tree.heading("size", text=self.get_text("model_size"))
        self.online_models_tree.heading("description", text=self.get_text("model_description"))
        
        # Set consistent column widths
        self.online_models_tree.column("#0", width=200, minwidth=150)
        self.online_models_tree.column("size", width=80, minwidth=60)
        self.online_models_tree.column("description", width=250, minwidth=200)
        
        # Scrollbar for online models
        scrollbar1 = ttk.Scrollbar(left_frame, orient=tk.VERTICAL, command=self.online_models_tree.yview)
        self.online_models_tree.configure(yscrollcommand=scrollbar1.set)
        
        self.online_models_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar1.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Online model buttons with uniform size
        online_btn_frame = ttk.Frame(left_frame)
        online_btn_frame.pack(fill=tk.X, pady=(15, 0))
        
        download_btn = ttk.Button(online_btn_frame, text=self.get_text("download_model"), 
                                 command=self.download_model, width=self.button_width)
        download_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        refresh_online_btn = ttk.Button(online_btn_frame, text=self.get_text("refresh_online"), 
                                       command=self.refresh_online_models, width=self.button_width)
        refresh_online_btn.pack(side=tk.LEFT)
        
        # Right pane - Local models
        right_frame = ttk.LabelFrame(paned, text=self.get_text("local_models"), padding=15)
        paned.add(right_frame, weight=1)
        
        # Local models listbox
        self.local_models_listbox = tk.Listbox(right_frame, font=self.default_font, height=12)
        scrollbar2 = ttk.Scrollbar(right_frame, orient=tk.VERTICAL, command=self.local_models_listbox.yview)
        self.local_models_listbox.configure(yscrollcommand=scrollbar2.set)
        
        self.local_models_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar2.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Local model buttons with uniform size
        local_btn_frame = ttk.Frame(right_frame)
        local_btn_frame.pack(fill=tk.X, pady=(15, 0))
        
        delete_btn = ttk.Button(local_btn_frame, text=self.get_text("delete_model"), 
                               command=self.delete_model, width=self.button_width)
        delete_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        refresh_local_btn = ttk.Button(local_btn_frame, text=self.get_text("refresh_local"), 
                                      command=self.refresh_models, width=self.button_width)
        refresh_local_btn.pack(side=tk.LEFT)
        
        # Progress bar and label (always visible but initially empty)
        progress_frame = ttk.Frame(frame)
        progress_frame.pack(fill=tk.X, padx=20, pady=(0, 20))
        
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(progress_frame, variable=self.progress_var, maximum=100)
        self.progress_bar.pack(fill=tk.X, pady=(0, 10))
        
        self.progress_label = ttk.Label(progress_frame, text="", font=self.label_font)
        self.progress_label.pack()
    
    def setup_chat_tab(self, notebook):
        """Setup chat interface tab"""
        frame = ttk.Frame(notebook)
        notebook.add(frame, text=self.get_text("tab_chat"))
        
        # Model selection frame
        model_frame = ttk.Frame(frame)
        model_frame.pack(fill=tk.X, padx=20, pady=20)
        
        model_label = ttk.Label(model_frame, text=self.get_text("select_model"), font=self.label_font)
        model_label.pack(side=tk.LEFT, padx=(0, 15))
        
        self.current_model = tk.StringVar()
        self.model_combo = ttk.Combobox(model_frame, textvariable=self.current_model, 
                                       state="readonly", width=self.entry_width)
        self.model_combo.pack(side=tk.LEFT, padx=(0, 15))
        
        refresh_btn = ttk.Button(model_frame, text=self.get_text("refresh"), 
                               command=self.refresh_models, width=self.small_button_width)
        refresh_btn.pack(side=tk.LEFT)
        
        # Chat display with consistent font
        self.chat_display = scrolledtext.ScrolledText(frame, wrap=tk.WORD, height=18, 
                                                     font=self.default_font, state=tk.DISABLED)
        self.chat_display.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 15))
        
        # Configure text tags
        self.chat_display.tag_configure("sender", font=self.bold_font)
        self.chat_display.tag_configure("message", font=self.default_font)
        
        # Input frame
        input_frame = ttk.Frame(frame)
        input_frame.pack(fill=tk.X, padx=20, pady=(0, 15))
        
        # Message input with consistent font
        self.message_entry = tk.Text(input_frame, height=4, wrap=tk.WORD, font=self.default_font)
        self.message_entry.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 15))
        
        # Send button
        send_button = ttk.Button(input_frame, text=self.get_text("send"), 
                               command=self.send_message, width=self.small_button_width)
        send_button.pack(side=tk.RIGHT)
        
        # Bind Enter key
        self.message_entry.bind("<Control-Return>", lambda e: self.send_message())
        
        # Control buttons frame
        control_frame = ttk.Frame(frame)
        control_frame.pack(fill=tk.X, padx=20, pady=(0, 20))
        
        # Control buttons with uniform size
        clear_btn = ttk.Button(control_frame, text=self.get_text("clear_chat"), 
                             command=self.clear_chat, width=self.button_width)
        clear_btn.pack(side=tk.LEFT, padx=(0, 15))
        
        save_btn = ttk.Button(control_frame, text=self.get_text("save_chat"), 
                            command=self.save_chat, width=self.button_width)
        save_btn.pack(side=tk.LEFT, padx=(0, 15))
        
        # Verbose mode checkbox
        self.verbose_var = tk.BooleanVar()
        verbose_cb = ttk.Checkbutton(control_frame, text=self.get_text("show_verbose"), 
                                   variable=self.verbose_var)
        verbose_cb.pack(side=tk.LEFT)
        
        # Initialize chat history
        self.chat_history = []
        
        # Initialize verbose window reference
        self.verbose_window = None
        
        # Initialize chat
        self.add_chat_message(self.get_text("system"), self.get_text("system_message"))
    
    def setup_env_tab(self, notebook):
        """Setup environment variables tab"""
        frame = ttk.Frame(notebook)
        notebook.add(frame, text=self.get_text("tab_environment"))
        
        # Main frame
        main_frame = ttk.LabelFrame(frame, text=self.get_text("env_variables"))
        main_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        # Create a scrollable frame
        canvas = tk.Canvas(main_frame)
        scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # OLLAMA_HOST setting
        host_frame = ttk.LabelFrame(scrollable_frame, text=self.get_text("host_address"))
        host_frame.pack(fill=tk.X, padx=15, pady=10)
        
        ttk.Label(host_frame, text=self.get_text("host_label")).pack(anchor=tk.W, padx=15, pady=8)
        host_entry = ttk.Entry(host_frame, textvariable=self.ollama_host, width=40)
        host_entry.pack(anchor=tk.W, padx=15, pady=5)
        ttk.Label(host_frame, text=self.get_text("host_default"), foreground="gray").pack(anchor=tk.W, padx=15, pady=5)
        
        # OLLAMA_PORT setting
        port_frame = ttk.LabelFrame(scrollable_frame, text=self.get_text("port_number"))
        port_frame.pack(fill=tk.X, padx=15, pady=10)
        
        ttk.Label(port_frame, text=self.get_text("port_label")).pack(anchor=tk.W, padx=15, pady=8)
        port_entry = ttk.Entry(port_frame, textvariable=self.ollama_port, width=40)
        port_entry.pack(anchor=tk.W, padx=15, pady=5)
        ttk.Label(port_frame, text=self.get_text("port_default"), foreground="gray").pack(anchor=tk.W, padx=15, pady=5)
        
        # OLLAMA_MODELS setting
        models_frame = ttk.LabelFrame(scrollable_frame, text=self.get_text("models_storage"))
        models_frame.pack(fill=tk.X, padx=15, pady=10)
        
        ttk.Label(models_frame, text=self.get_text("models_path_label")).pack(anchor=tk.W, padx=15, pady=8)
        models_entry_frame = ttk.Frame(models_frame)
        models_entry_frame.pack(fill=tk.X, padx=15, pady=5)
        
        models_entry = ttk.Entry(models_entry_frame, textvariable=self.ollama_models)
        models_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        ttk.Button(models_entry_frame, text=self.get_text("browse"), width=12,
                  command=lambda: self.browse_folder(self.ollama_models)).pack(side=tk.RIGHT, padx=10)
        
        ttk.Label(models_frame, text=self.get_text("models_default"), foreground="gray").pack(anchor=tk.W, padx=15, pady=5)
        
        # OLLAMA_KEEP_ALIVE setting
        keep_alive_frame = ttk.LabelFrame(scrollable_frame, text=self.get_text("keep_alive"))
        keep_alive_frame.pack(fill=tk.X, padx=15, pady=10)
        
        ttk.Label(keep_alive_frame, text=self.get_text("keep_alive_label")).pack(anchor=tk.W, padx=15, pady=8)
        keep_alive_entry = ttk.Entry(keep_alive_frame, textvariable=self.ollama_keep_alive, width=40)
        keep_alive_entry.pack(anchor=tk.W, padx=15, pady=5)
        ttk.Label(keep_alive_frame, text=self.get_text("keep_alive_format"), foreground="gray").pack(anchor=tk.W, padx=15, pady=5)
        
        # Control buttons
        button_frame = ttk.Frame(scrollable_frame)
        button_frame.pack(fill=tk.X, padx=15, pady=15)
        
        ttk.Button(button_frame, text=self.get_text("reset_defaults"), width=15,
                  command=self.reset_env_vars).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(button_frame, text=self.get_text("test_connection"), width=15,
                  command=self.test_connection).pack(side=tk.LEFT, padx=(0, 10))
        
        # Current environment info
        info_frame = ttk.LabelFrame(scrollable_frame, text=self.get_text("current_env"))
        info_frame.pack(fill=tk.X, padx=15, pady=10)
        
        self.env_info_text = tk.Text(info_frame, height=6, font=("Consolas", 9), wrap=tk.WORD)
        env_scrollbar = ttk.Scrollbar(info_frame, orient=tk.VERTICAL, command=self.env_info_text.yview)
        self.env_info_text.configure(yscrollcommand=env_scrollbar.set)
        
        self.env_info_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        env_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Pack canvas and scrollbar
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Update environment info
        self.update_env_info()
    
    def browse_folder(self, var):
        """Browse for folder"""
        from tkinter import filedialog
        folder = filedialog.askdirectory()
        if folder:
            var.set(folder)
    

    
    def reset_env_vars(self):
        """Reset environment variables to defaults"""
        self.ollama_host.set("localhost")
        self.ollama_port.set("11434")
        self.ollama_models.set("")
        self.ollama_keep_alive.set("5m")
        self.update_status(self.get_text("env_reset"))
    
    def test_connection(self):
        """Test connection to Ollama server"""
        try:
            host = self.ollama_host.get()
            port = self.ollama_port.get()
            url = f"http://{host}:{port}/api/tags"
            
            self.update_status(self.get_text("connection_testing"))
            response = requests.get(url, timeout=5)
            
            if response.status_code == 200:
                self.update_status(self.get_text("connection_success"))
                messagebox.showinfo(self.get_text("success"), f"{self.get_text('connection_success_detail')}: {host}:{port}")
            else:
                self.update_status(self.get_text("connection_failed"))
                messagebox.showerror(self.get_text("error"), f"{self.get_text('connection_failed_status')}: {response.status_code}")
                
        except Exception as e:
            self.update_status(self.get_text("connection_failed"))
            messagebox.showerror(self.get_text("error"), f"{self.get_text('connection_test_failed')}: {e}")
    
    def update_env_info(self):
        """Update environment information display"""
        self.env_info_text.delete("1.0", tk.END)
        
        env_info = f"{self.get_text('current_env_info')}:\n"
        env_info += f"OLLAMA_HOST = {os.environ.get('OLLAMA_HOST', self.get_text('not_set'))}\n"
        env_info += f"OLLAMA_PORT = {os.environ.get('OLLAMA_PORT', self.get_text('not_set'))}\n"
        env_info += f"OLLAMA_MODELS = {os.environ.get('OLLAMA_MODELS', self.get_text('not_set'))}\n"
        env_info += f"OLLAMA_KEEP_ALIVE = {os.environ.get('OLLAMA_KEEP_ALIVE', self.get_text('not_set'))}\n"
        env_info += f"\n{self.get_text('server_address')}: {self.ollama_host.get()}:{self.ollama_port.get()}"
        
        self.env_info_text.insert("1.0", env_info)
    
    def load_settings(self):
        """Load settings from config"""
        self.auto_start_var.set(self.config.get("auto_start", False))
        self.current_model.set(self.config.get("selected_model", ""))
        
        # Load environment variables from environment first, then config as fallback
        self.ollama_host.set(os.environ.get('OLLAMA_HOST', self.config.get("ollama_host", "localhost")))
        self.ollama_port.set(os.environ.get('OLLAMA_PORT', self.config.get("ollama_port", "11434")))
        self.ollama_models.set(os.environ.get('OLLAMA_MODELS', self.config.get("ollama_models", "")))
        self.ollama_keep_alive.set(os.environ.get('OLLAMA_KEEP_ALIVE', self.config.get("ollama_keep_alive", "5m")))
        
        # Update original values after loading
        self.original_values = {
            'auto_start': self.auto_start_var.get(),
            'ollama_host': self.ollama_host.get(),
            'ollama_port': self.ollama_port.get(),
            'ollama_models': self.ollama_models.get(),
            'ollama_keep_alive': self.ollama_keep_alive.get()
        }
        
        # Set window geometry
        geometry = self.config.get("window_geometry", "1024x768")
        self.root.geometry(geometry)
        
        self.update_autostart_status()
    
    def toggle_autostart(self):
        """Toggle auto-start setting"""
        try:
            key_path = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run"
            app_name = "OllamaService"
            
            if self.auto_start_var.get():
                # Add to startup
                if self.ollama_path:
                    startup_command = f'"{self.ollama_path.parent / "MiniOllama.exe -start"}"'
                    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE) as key:
                        winreg.SetValueEx(key, app_name, 0, winreg.REG_SZ, startup_command)
                    self.update_status(self.get_text("autostart_added"))
                else:
                    messagebox.showerror(self.get_text("error"), self.get_text("ollama_not_found_error"))
                    self.auto_start_var.set(False)
                    return
            else:
                # Remove from startup
                try:
                    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE) as key:
                        winreg.DeleteValue(key, app_name)
                    self.update_status(self.get_text("autostart_removed"))
                except FileNotFoundError:
                    pass
            
            self.update_autostart_status()
            self.save_config()
            
        except Exception as e:
            messagebox.showerror(self.get_text("error"), f"{self.get_text('autostart_setup_failed')}: {e}")
            self.auto_start_var.set(not self.auto_start_var.get())
    
    def update_autostart_status(self):
        """Update auto-start status display"""
        try:
            key_path = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run"
            app_name = "OllamaService"
            
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_READ) as key:
                try:
                    value, _ = winreg.QueryValueEx(key, app_name)
                    self.autostart_status.config(text=self.get_text("status_enabled"), foreground="green")
                except FileNotFoundError:
                    self.autostart_status.config(text=self.get_text("status_disabled"), foreground="red")
        except Exception:
            self.autostart_status.config(text=self.get_text("status_unknown"), foreground="orange")
    
    def start_ollama_service(self):
        """Start Ollama service with completely hidden window"""
        if not self.ollama_path:
            messagebox.showerror(self.get_text("error"), self.get_text("ollama_not_found_error"))
            return
        
        try:
            # Try to start using batch file first
            batch_file = self.ollama_path.parent / "start_ollama.bat"
            if batch_file.exists():
                # Start batch file with completely hidden window
                if sys.platform == "win32":
                    CREATE_NO_WINDOW = 0x08000000
                    DETACHED_PROCESS = 0x00000008
                    startupinfo = subprocess.STARTUPINFO()
                    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                    startupinfo.wShowWindow = 0  # SW_HIDE
                    
                    subprocess.Popen(
                        [str(batch_file)], 
                        creationflags=CREATE_NO_WINDOW | DETACHED_PROCESS,
                        startupinfo=startupinfo,
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                        stdin=subprocess.DEVNULL
                    )
                else:
                    subprocess.Popen(
                        [str(batch_file)], 
                        stdout=subprocess.DEVNULL, 
                        stderr=subprocess.DEVNULL,
                        stdin=subprocess.DEVNULL
                    )
            else:
                # Start directly with completely hidden window
                if sys.platform == "win32":
                    CREATE_NO_WINDOW = 0x08000000
                    DETACHED_PROCESS = 0x00000008
                    startupinfo = subprocess.STARTUPINFO()
                    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                    startupinfo.wShowWindow = 0  # SW_HIDE
                    
                    subprocess.Popen(
                        [str(self.ollama_path), "serve"], 
                        creationflags=CREATE_NO_WINDOW | DETACHED_PROCESS,
                        startupinfo=startupinfo,
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                        stdin=subprocess.DEVNULL
                    )
                else:
                    subprocess.Popen(
                        [str(self.ollama_path), "serve"], 
                        stdout=subprocess.DEVNULL, 
                        stderr=subprocess.DEVNULL,
                        stdin=subprocess.DEVNULL
                    )
            
            self.update_status(self.get_text("service_starting"))
            self.root.after(2000, self.check_ollama_status)
            
        except Exception as e:
            messagebox.showerror(self.get_text("error"), f"{self.get_text('service_start_failed')}: {e}")
    
    def stop_ollama_service(self):
        """Stop Ollama service"""
        try:
            # Try to stop using batch file first
            if self.ollama_path:
                batch_file = self.ollama_path.parent / "stop_ollama.bat"
                if batch_file.exists():
                    if sys.platform == "win32":
                        CREATE_NO_WINDOW = 0x08000000
                        subprocess.run([str(batch_file)], shell=True, creationflags=CREATE_NO_WINDOW)
                    else:
                        subprocess.run([str(batch_file)], shell=True)
                else:
                    # Kill process directly
                    if sys.platform == "win32":
                        CREATE_NO_WINDOW = 0x08000000
                        subprocess.run(["taskkill", "/f", "/im", "ollama.exe"], shell=True, creationflags=CREATE_NO_WINDOW)
                    else:
                        subprocess.run(["pkill", "ollama"], shell=True)
            else:
                # Kill process directly
                if sys.platform == "win32":
                    CREATE_NO_WINDOW = 0x08000000
                    subprocess.run(["taskkill", "/f", "/im", "ollama.exe"], shell=True, creationflags=CREATE_NO_WINDOW)
                else:
                    subprocess.run(["pkill", "ollama"], shell=True)
            
            self.update_status(self.get_text("service_stopped"))
            
        except Exception as e:
            messagebox.showerror(self.get_text("error"), f"{self.get_text('service_stop_failed')}: {e}")
    
    def check_ollama_status(self):
        """Check if Ollama service is running"""
        try:
            host = self.ollama_host.get()
            port = self.ollama_port.get()
            url = f"http://{host}:{port}/api/tags"
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                self.update_status(self.get_text("service_running"))
                return True
            else:
                self.update_status(self.get_text("service_not_running"))
                return False
        except Exception:
            self.update_status(self.get_text("service_not_running"))
            return False
    
    def refresh_models(self):
        """Refresh local models list"""
        self.local_models_listbox.delete(0, tk.END)
        models = []
        
        try:
            if self.check_ollama_status():
                host = self.ollama_host.get()
                port = self.ollama_port.get()
                url = f"http://{host}:{port}/api/tags"
                response = requests.get(url, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    models = [model['name'] for model in data.get('models', [])]
        except Exception as e:
            self.update_status(f"{self.get_text('getting_models_failed')}: {e}")
        
        for model in models:
            self.local_models_listbox.insert(tk.END, model)
        
        # Update combo box
        self.model_combo['values'] = models
        if models and not self.current_model.get():
            self.current_model.set(models[0])
    
    def refresh_online_models(self):
        """Refresh online models list"""
        self.update_status(self.get_text("getting_online_models"))
        
        def fetch_models():
            try:
                # Simulated online models (< 1.5GB)
                online_models = [
                    {"name": "llama3.2:1b", "size": "1.3GB", "description": "Llama 3.2 1B "},
                    {"name": "deepseek-r1:1.5b", "size": "1.1GB", "description": "DeepSeek R1 1.5B"},
                    {"name": "gemma3:1b", "size": "0.8GB", "description": "Gemma 3 1B "},
                    {"name": "qwen3:0.6b", "size": "0.5GB", "description": "Qwen3 0.6B "},
                    {"name": "tinyllama:1.1b", "size": "0.6GB", "description": "TinyLlama 1.1B "},
                ]
                
                # Filter models < 1.5GB
                filtered_models = []
                for model in online_models:
                    size_str = model["size"]
                    size_gb = float(size_str.replace("GB", ""))
                    if size_gb < 1.5:
                        filtered_models.append(model)
                
                # Update UI in main thread
                self.root.after(0, self.update_online_models, filtered_models)
                
            except Exception as e:
                self.root.after(0, self.update_status, f"{self.get_text('getting_online_models_failed')}: {e}")
        
        threading.Thread(target=fetch_models, daemon=True).start()
    
    def update_online_models(self, models):
        """Update online models display"""
        # Clear existing items
        for item in self.online_models_tree.get_children():
            self.online_models_tree.delete(item)
        
        # Add new items
        for model in models:
            self.online_models_tree.insert("", tk.END, text=model["name"], 
                                         values=(model["size"], model["description"]))
        
        self.update_status(self.get_text("online_models_updated"))
    
    def download_model(self):
        """Download selected model"""
        selection = self.online_models_tree.selection()
        if not selection:
            messagebox.showwarning(self.get_text("warning"), self.get_text("select_download_warning"))
            return
        
        item = self.online_models_tree.item(selection[0])
        model_name = item["text"]
        
        if not self.check_ollama_status():
            messagebox.showerror(self.get_text("error"), self.get_text("service_not_running_error"))
            return
        
        def download_thread():
            try:
                self.root.after(0, self.update_status, f"{self.get_text('downloading_model_status')}: {model_name}")
                
                # Reset progress
                self.root.after(0, self.progress_var.set, 0)
                self.root.after(0, lambda: self.progress_label.config(text="0% - 准备下载..."))
                
                # Use ollama pull command
                process = subprocess.Popen(
                    [str(self.ollama_path), "pull", model_name],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,  # Redirect stderr to stdout
                    text=True,
                    encoding='utf-8',
                    errors='ignore',  # Ignore encoding errors
                    universal_newlines=True,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
                
                import re
                
                # Read output line by line
                if process.stdout:
                    for line in iter(process.stdout.readline, ''):
                        try:
                            line = line.strip()
                            if not line:
                                continue
                            
                            # Debug output to console
                            print(f"DEBUG ollama output: {line}")
                            
                            # Try to extract progress information from various formats
                            progress_updated = False
                            
                            # Pattern 1: Look for percentage anywhere in the line
                            percent_match = re.search(r'(\d+)%', line)
                            if percent_match:
                                percentage = int(percent_match.group(1))
                                self.root.after(0, lambda p=percentage: self.progress_var.set(p))
                                progress_updated = True
                            
                            # Pattern 2: Look for size information (GB/MB/KB)
                            size_match = re.search(r'(\d+(?:\.\d+)?)\s*(GB|MB|KB)', line, re.IGNORECASE)
                            if size_match:
                                size_value = float(size_match.group(1))
                                size_unit = size_match.group(2).upper()
                                
                                if progress_updated:
                                    progress_text = f"{percentage}% - {size_value} {size_unit}"
                                else:
                                    progress_text = f"下载中 - {size_value} {size_unit}"
                                self.root.after(0, lambda txt=progress_text: self.progress_label.config(text=txt))
                            
                            # Pattern 3: Look for specific ollama status messages
                            elif "pulling manifest" in line.lower():
                                self.root.after(0, lambda: self.progress_label.config(text="正在获取模型信息..."))
                            elif "pulling" in line.lower() and "fs layer" in line.lower():
                                self.root.after(0, lambda: self.progress_label.config(text="正在下载模型层..."))
                            elif "verifying sha256 digest" in line.lower():
                                self.root.after(0, lambda: self.progress_var.set(95))
                                self.root.after(0, lambda: self.progress_label.config(text="95% - 验证模型完整性..."))
                            elif "writing manifest" in line.lower():
                                self.root.after(0, lambda: self.progress_var.set(98))
                                self.root.after(0, lambda: self.progress_label.config(text="98% - 写入模型清单..."))
                            elif "removing any unused layers" in line.lower():
                                self.root.after(0, lambda: self.progress_var.set(99))
                                self.root.after(0, lambda: self.progress_label.config(text="99% - 清理缓存..."))
                            elif "success" in line.lower():
                                self.root.after(0, lambda: self.progress_var.set(100))
                                self.root.after(0, lambda: self.progress_label.config(text="100% - 下载完成！"))
                            
                            # Pattern 4: If no specific pattern matched, show the line directly
                            elif not progress_updated:
                                # Clean up the line for display
                                display_line = line
                                if len(display_line) > 50:
                                    display_line = display_line[:47] + "..."
                                self.root.after(0, lambda txt=display_line: self.progress_label.config(text=txt))
                                
                        except (UnicodeDecodeError, UnicodeError) as e:
                            # Skip lines that can't be decoded
                            print(f"DEBUG: Skipping line due to encoding error: {e}")
                            continue
                        except Exception as e:
                            # Handle other parsing errors
                            print(f"DEBUG: Error processing line: {e}")
                            continue
                
                # Wait for process to complete
                process.wait()
                
                if process.returncode == 0:
                    self.root.after(0, lambda: self.progress_var.set(100))
                    self.root.after(0, lambda: self.progress_label.config(text="100% - 下载完成！"))
                    self.root.after(0, self.update_status, f"{self.get_text('model_info')} {model_name} {self.get_text('model_download_complete')}")
                    self.root.after(0, self.refresh_models)
                else:
                    error = ""
                    if process.stderr:
                        error = process.stderr.read()
                    self.root.after(0, self.update_status, f"{self.get_text('download_failed')}: {error}")
                
            except Exception as e:
                self.root.after(0, self.update_status, f"{self.get_text('download_failed')}: {e}")
            finally:
                # Clear progress after completion
                self.root.after(3000, lambda: self.progress_var.set(0))
                self.root.after(3000, lambda: self.progress_label.config(text=""))
        
        threading.Thread(target=download_thread, daemon=True).start()
    
    def delete_model(self):
        """Delete selected local model"""
        selection = self.local_models_listbox.curselection()
        if not selection:
            messagebox.showwarning(self.get_text("warning"), self.get_text("select_model_warning"))
            return
        
        model_name = self.local_models_listbox.get(selection[0])
        
        if messagebox.askyesno(self.get_text("confirm"), f"{self.get_text('delete_model_confirm')} {model_name}?"):
            try:
                if self.ollama_path:
                    if sys.platform == "win32":
                        CREATE_NO_WINDOW = 0x08000000
                        subprocess.run([str(self.ollama_path), "rm", model_name], check=True, encoding='utf-8', errors='ignore', creationflags=CREATE_NO_WINDOW)
                    else:
                        subprocess.run([str(self.ollama_path), "rm", model_name], check=True, encoding='utf-8', errors='ignore')
                    self.refresh_models()
                    self.update_status(f"{self.get_text('model_info')} {model_name} {self.get_text('model_deleted')}")
                else:
                    messagebox.showerror(self.get_text("error"), self.get_text("ollama_not_found_error"))
            except Exception as e:
                messagebox.showerror(self.get_text("error"), f"{self.get_text('delete_model_failed')}: {e}")
    
    def send_message(self):
        """Send message to selected model"""
        if not self.current_model.get():
            messagebox.showwarning(self.get_text("warning"), self.get_text("select_model_warning"))
            return
        
        message = self.message_entry.get("1.0", tk.END).strip()
        if not message:
            return
        
        if not self.check_ollama_status():
            messagebox.showerror(self.get_text("error"), self.get_text("service_not_running_error"))
            return
        
        # Clear input
        self.message_entry.delete("1.0", tk.END)
        
        # Add user message to chat
        self.add_chat_message(self.get_text("user"), message)
        
        # Send to model
        def chat_thread():
            try:
                self.root.after(0, self.update_status, self.get_text("generating_reply"))
                
                host = self.ollama_host.get()
                port = self.ollama_port.get()
                url = f"http://{host}:{port}/api/generate"
                
                payload = {
                    "model": self.current_model.get(),
                    "prompt": message,
                    "stream": False
                }
                
                response = requests.post(url, json=payload, timeout=60)
                
                if response.status_code == 200:
                    data = response.json()
                    reply = data.get("response", "")
                    
                    # Add assistant message
                    self.root.after(0, self.add_chat_message, self.get_text("assistant"), reply)
                    
                    # Show verbose info if enabled
                    if self.verbose_var.get():
                        self.root.after(0, self.show_verbose_info, data)
                    
                    self.root.after(0, self.update_status, self.get_text("reply_complete"))
                else:
                    self.root.after(0, self.add_chat_message, self.get_text("error"), f"{self.get_text('request_failed')}: {response.status_code}")
                    
            except Exception as e:
                self.root.after(0, self.add_chat_message, self.get_text("error"), f"{self.get_text('generate_reply_failed')}: {e}")
                self.root.after(0, self.update_status, self.get_text("reply_failed"))
        
        threading.Thread(target=chat_thread, daemon=True).start()
    
    def add_chat_message(self, sender, message):
        """Add message to chat display"""
        self.chat_display.config(state=tk.NORMAL)
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # Add sender and timestamp
        self.chat_display.insert(tk.END, f"[{timestamp}] {sender}:\n", "sender")
        self.chat_display.insert(tk.END, f"{message}\n\n", "message")
        
        self.chat_display.config(state=tk.DISABLED)
        self.chat_display.see(tk.END)
        
        # Save to history
        self.chat_history.append({
            "timestamp": timestamp,
            "sender": sender,
            "message": message
        })
    
    def show_verbose_info(self, data):
        """Show verbose information in a popup"""
        # Close existing verbose window if it exists
        if self.verbose_window:
            try:
                if self.verbose_window.winfo_exists():
                    self.verbose_window.destroy()
            except tk.TclError:
                pass
            self.verbose_window = None
        
        # Create new verbose window
        self.verbose_window = tk.Toplevel(self.root)
        self.verbose_window.title(self.get_text("verbose_info"))
        self.verbose_window.geometry("500x400")
        
        # Set icon for popup window
        try:
            icon_path = self.get_icon_path()
            if icon_path:
                self.verbose_window.iconbitmap(str(icon_path))
        except Exception:
            pass
        
        # Make window stay on top but don't grab focus
        self.verbose_window.transient(self.root)
        # Don't use grab_set() to avoid focus issues
        
        # Create text widget with scrollbar
        text_frame = ttk.Frame(self.verbose_window)
        text_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        text_widget = tk.Text(text_frame, wrap=tk.WORD, font=("Consolas", 10))
        scrollbar = ttk.Scrollbar(text_frame, orient=tk.VERTICAL, command=text_widget.yview)
        text_widget.configure(yscrollcommand=scrollbar.set)
        
        text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Format verbose info
        formatted_info = f"{self.get_text('model_info')}: {data.get('model', 'N/A')}\n"
        formatted_info += f"{self.get_text('total_time')}: {data.get('total_duration', 0) / 1e9:.2f}s\n"
        formatted_info += f"{self.get_text('load_time')}: {data.get('load_duration', 0) / 1e9:.2f}s\n"
        formatted_info += f"{self.get_text('prompt_eval')}: {data.get('prompt_eval_count', 0)} {self.get_text('tokens')}\n"
        formatted_info += f"{self.get_text('generate_eval')}: {data.get('eval_count', 0)} {self.get_text('tokens')}\n"
        formatted_info += f"Prompt评估时间: {data.get('prompt_eval_duration', 0) / 1e9:.2f}s\n"
        formatted_info += f"生成评估时间: {data.get('eval_duration', 0) / 1e9:.2f}s\n"
        formatted_info += f"生成速度: {data.get('eval_count', 0) / max(data.get('eval_duration', 1) / 1e9, 0.001):.1f} tokens/s\n"
        
        # Add raw response data for debugging
        formatted_info += "\n" + "="*50 + "\n"
        formatted_info += "原始响应数据:\n"
        formatted_info += "="*50 + "\n"
        for key, value in data.items():
            formatted_info += f"{key}: {value}\n"
        
        text_widget.insert(tk.END, formatted_info)
        text_widget.config(state=tk.DISABLED)
        
        # Add close button
        button_frame = ttk.Frame(self.verbose_window)
        button_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        close_button = ttk.Button(button_frame, text="关闭", 
                                 command=self.verbose_window.destroy)
        close_button.pack(side=tk.RIGHT)
        
        # Handle window close
        def on_close():
            if self.verbose_window:
                self.verbose_window.destroy()
            self.verbose_window = None
            
        self.verbose_window.protocol("WM_DELETE_WINDOW", on_close)
    

    
    def clear_chat(self):
        """Clear chat history"""
        if messagebox.askyesno(self.get_text("confirm"), self.get_text("clear_chat_confirm")):
            self.chat_display.config(state=tk.NORMAL)
            self.chat_display.delete("1.0", tk.END)
            self.chat_display.config(state=tk.DISABLED)
            self.add_chat_message(self.get_text("system"), self.get_text("chat_cleared"))
    
    def save_chat(self):
        """Save chat history to file"""
        chat_content = self.chat_display.get("1.0", tk.END).strip()
        if not chat_content:
            messagebox.showwarning(self.get_text("warning"), self.get_text("no_chat_history"))
            return
        
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"chat_history_{timestamp}.txt"
            
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(chat_content)
            
            self.update_status(f"{self.get_text('chat_saved')}: {filename}")
            
        except Exception as e:
            messagebox.showerror(self.get_text("error"), f"{self.get_text('save_failed_error')}: {e}")
    
    def update_status(self, message):
        """Update status bar"""
        self.status_label.config(text=message)
        self.root.update_idletasks()
    
    def save_settings(self):
        """Save all settings"""
        try:
            # Apply environment variables
            self.apply_env_vars()
            
            # Save configuration
            self.config["auto_start"] = self.auto_start_var.get()
            self.config["selected_model"] = self.current_model.get()
            self.config["ollama_host"] = self.ollama_host.get()
            self.config["ollama_port"] = self.ollama_port.get()
            self.config["ollama_models"] = self.ollama_models.get()
            self.config["ollama_keep_alive"] = self.ollama_keep_alive.get()
            self.config["window_geometry"] = self.root.geometry()
            
            self.save_config()
            
            # Update original values
            self.original_values = {
                'auto_start': self.auto_start_var.get(),
                'ollama_host': self.ollama_host.get(),
                'ollama_port': self.ollama_port.get(),
                'ollama_models': self.ollama_models.get(),
                'ollama_keep_alive': self.ollama_keep_alive.get()
            }
            
            messagebox.showinfo(self.get_text("success"), self.get_text("settings_saved"))
            
        except Exception as e:
            messagebox.showerror(self.get_text("error"), f"{self.get_text('save_failed')}: {e}")
    
    def exit_application(self):
        """Exit the application"""
        self.root.quit()
        
    def apply_env_vars(self):
        """Apply environment variables"""
        # OLLAMA_HOST
        host_value = self.ollama_host.get().strip()
        if host_value:
            os.environ['OLLAMA_HOST'] = host_value
        else:
            os.environ.pop('OLLAMA_HOST', None)
        
        # OLLAMA_PORT
        port_value = self.ollama_port.get().strip()
        if port_value:
            os.environ['OLLAMA_PORT'] = port_value
        else:
            os.environ.pop('OLLAMA_PORT', None)
        
        # OLLAMA_MODELS
        models_value = self.ollama_models.get().strip()
        if models_value:
            os.environ['OLLAMA_MODELS'] = models_value
        else:
            os.environ.pop('OLLAMA_MODELS', None)
        
        # OLLAMA_KEEP_ALIVE
        keep_alive_value = self.ollama_keep_alive.get().strip()
        if keep_alive_value:
            os.environ['OLLAMA_KEEP_ALIVE'] = keep_alive_value
        else:
            os.environ.pop('OLLAMA_KEEP_ALIVE', None)
        
        self.update_env_info()
    
    def open_hengruiyun_link(self, event):
        """Open HengruiYun GitHub link in browser"""
        webbrowser.open("https://github.com/hengruiyun")
    
    def on_closing(self):
        """Handle window closing"""
        self.root.destroy()
    
    def run(self):
        """Run the application"""
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.mainloop()

def main():
    """Main function to handle command line arguments"""
    parser = argparse.ArgumentParser(description='Ollama Settings Application')
    parser.add_argument('-start', '--start', action='store_true', 
                       help='Start Ollama service in hidden mode and exit')
    
    args = parser.parse_args()
    
    if args.start:
        # Start Ollama service in hidden mode
        success = OllamaSettings.start_ollama_hidden()
        sys.exit(0 if success else 1)
    else:
        # Run GUI application
        app = OllamaSettings()
        app.run()

if __name__ == "__main__":
    main() 