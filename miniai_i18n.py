#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MiniAI Internationalization (i18n) Module
支持中文和英文的国际化文本
合并了mini_i18n.json的完整内容
"""

import locale
import os

class MiniAI_i18n:
    def __init__(self, language=None):
        """
        初始化国际化模块
        Args:
            language: 指定语言 ('zh' 或 'en')，如果为None则自动检测
        """
        if language is None:
            self.language = self.detect_language()
        else:
            self.language = language
    
    def detect_language(self):
        """检测系统语言"""
        try:
            # 首先检查环境变量
            lang_env = os.environ.get('LANG', '')
            if lang_env.startswith('zh'):
                return 'zh'
            
            # 检查系统locale
            system_locale = locale.getdefaultlocale()[0]
            if system_locale and system_locale.startswith('zh'):
                return 'zh'
            else:
                return 'en'  # 非中文系统默认英文
        except:
            return 'en'  # 出错时默认英文
    
    def get_text(self, key, category=None, **kwargs):
        """
        获取指定键的文本
        Args:
            key: 文本键，支持点号分隔的路径如 'ui.tab_chat'
            category: 类别（可选，如果key中没有包含路径）
            **kwargs: 格式化参数
        """
        try:
            # 支持点号分隔的键路径
            if '.' in key:
                parts = key.split('.')
                text_data = self.texts[self.language]
                for part in parts:
                    text_data = text_data.get(part, {})
                # 返回找到的数据，可能是字符串、列表或其他类型
                text = text_data if text_data != {} else key
            elif category:
                # 从指定类别获取文本
                text = self.texts[self.language].get(category, {}).get(key, key)
            else:
                # 直接从根级别获取（向后兼容）
                text = self.texts[self.language].get(key, key)
            
            # 如果支持格式化参数
            if kwargs and isinstance(text, str) and '{}' in text:
                return text.format(**kwargs)
            return text
        except:
            return key
    
    def set_language(self, language):
        """设置语言"""
        if language in ['zh', 'en']:
            self.language = language
    
    # 完整的国际化文本字典（从mini_i18n.json合并）
    texts = {
        'zh': {
            'warnings': {
                'webengine_unavailable': '警告: PyQtWebEngine不可用，将使用备用搜索方法'
            },
            'download': {
                'downloading': '下载中...',
                'getting_model_info': '正在获取模型信息...',
                'verifying_integrity': '验证模型完整性...',
                'writing_manifest': '写入模型清单...',
                'download_complete': '下载完成！',
                'download_success': '下载完成',
                'download_failed': '下载失败',
                'download_failed_with_error': '下载失败: {}'
            },
            'chat': {
                'building_prompt': '构建对话prompt时出错: {}',
                'conversation_history': '以下是最近的对话历史，请基于这些上下文回答用户的新问题：\n\n',
                'history_section': '=== 对话历史 ===\n',
                'current_question': '\n=== 当前问题 ===\n',
                'user_prefix': '用户: {}\n\n',
                'instruction': '请基于上述对话历史，给出恰当的回答：',
                'history_error': '获取对话历史时出错: {}',
                'request_failed': '请求失败: {}',
                'generate_failed': '生成回复失败: {}',
            'user': '用户',
            'assistant': '助手',
            'assistant_enhanced': '助手(联网增强)',
            'system': '系统',
                'welcome_message': '欢迎使用MiniAI！请选择一个模型开始对话。'
            },
            'review': {
                'review_started': '[DEBUG] 审查线程开始运行',
                'original_question': '[DEBUG] 原始问题: {}',
                'answer_length': '[DEBUG] 回答长度: {} 字符',
                'greeting_detected': '检测到简单问候语，直接通过审查。',
                'non_intellectual': '检测到非智力问题（日常对话、情感交流等），可信度设为100%。',
                'uncertainty_result': '[DEBUG] 不确定性检测结果: {}',
                'uncertainty_detected': '检测到AI回答中主动承认不确定或不知道，可信度设置为0。需要联网搜索准确信息。',
                'confidence_zero': '[DEBUG] 设置可信度为0，原因: {}',
                'time_confidence': '[DEBUG] 时间检测结果: {}',
                'time_info_detected': '检测到回答中包含时间信息且与当前日期相差在5年内，可信度设置为0。需要联网搜索最新信息。',
                'review_failed': '审查请求失败: {}',
                'review_error': '答案审查失败: {}',
                'greeting_check_error': '问候语检测出错: {}',
                'intellectual_check_error': '智力问题检测出错: {}',
                'uncertainty_detected_phrases': '[DEBUG] 不确定性检测 - 检测到的短语: {}',
                'uncertainty_excluded': '[DEBUG] 不确定性检测 - 排除后的短语: {}',
                'uncertainty_found': '[DEBUG] ✅ 检测到不确定性表达: {}',
                'uncertainty_all_excluded': '[DEBUG] ❌ 所有检测到的短语都被排除了',
                'uncertainty_none': '[DEBUG] ❌ 未检测到任何不确定性表达',
                'too_many_questions': '检测到过多问号: {}个',
                'too_many_maybe': '检测到过多不确定词汇: {}个',
                'uncertain_ending': '检测到不确定结尾: \'{}\'',
                'uncertainty_check_error': '不确定性检测出错: {}',
                'time_check_started': '[DEBUG] 时间检测开始，当前年份: {}',
                'text_length': '[DEBUG] 检测文本长度: {} 字符',
                'relative_time_detected': '[DEBUG] 检测到相对时间关键词: {}',
                'time_confidence_zero': '[DEBUG] 时间检测返回0（可信度为0）',
                'years_found': '[DEBUG] 检测到年份: {}',
                'year_difference': '[DEBUG] 年份 {} 与当前年份 {} 相差 {} 年',
                'year_within_five': '[DEBUG] 年份 {} 在5年内，时间检测返回0（可信度为0）',
                'years_outside_five': '[DEBUG] 所有检测到的年份都不在5年内，时间检测返回100',
                'no_time_info': '[DEBUG] 没有检测到时间信息，时间检测返回100',
                'time_check_error': '时间检测出错: {}'
            },
            'search': {
                'source_format': '来源{}: {}\n内容: {}...',
                'no_valid_results': '未能获取到有效的搜索结果内容',
                'search_request_failed': '搜索请求失败: {}',
                'search_failed': '网络搜索失败: {}'
            },
            'enhanced': {
                'generation_failed': '增强回答生成失败: {}',
                'generation_error': '增强回答生成失败: {}',
                'enhanced_prompt_base': '基于以下网络搜索结果和对话历史，请回答用户的问题：\n\n',
                'history_section': '=== 对话历史 ===\n',
                'current_question_section': '=== 当前问题 ===\n用户问题：{}\n\n',
                'search_results_section': '=== 网络搜索结果 ===\n{}\n\n',
                'instruction': '请基于上述搜索结果和对话历史，提供一个准确、详细且有用的回答。如果搜索结果中包含相关信息，请优先使用这些信息。请确保回答的准确性和可靠性，并保持与对话历史的连贯性。\n\n回答：',
                'prompt_error': '构建增强prompt时出错: {}',
                'history_error': '获取对话历史时出错: {}'
            },
            'ui': {
                'tab_chat': '聊天',
                'tab_models': '模型管理',
                'tab_autostart': '服务管理',
                'tab_environment': '环境设置',
                'select_model': '选择模型:',
                'clear_chat': '清空对话',
                'save_chat': '保存对话',
                'send': '发送',
                'input_placeholder': '输入您的消息... (Ctrl+Enter发送)',
            'available_models': '可下载模型',
            'local_models': '本地模型',
            'download_model': '下载模型',
            'delete_model': '删除模型',
                'autostart_title': '开机启动设置',
            'autostart_checkbox': '开机自动启动 Ollama 服务',
            'start_service': '启动服务',
            'stop_service': '停止服务',
            'check_status': '检查状态',
                'path_info': '路径信息',
                'ollama_path': 'Ollama 路径:',
                'models_path': '模型路径:',
                'env_variables': '环境变量设置',
                'host_label': 'OLLAMA_HOST:',
                'port_label': 'OLLAMA_PORT:',
                'models_label': 'OLLAMA_MODELS:',
                'current_env_info': '当前环境信息'
            },
            'status': {
                'service_not_running': 'Ollama服务未运行，请先启动服务',
                'models_loaded': '已加载 {} 个本地模型',
                'no_models': '未找到本地模型，请先下载模型',
                'get_models_failed': '获取本地模型列表失败: {}',
                'downloading_model': '正在下载模型: {}',
                'model_deleted': '模型 {} 已删除',
                'delete_failed': '删除模型失败: {}',
                'generating_reply': '正在生成回复...',
                'reviewing_quality': '正在审查回答质量...',
                'checking_network': '检查网络连接...',
                'searching_online': '正在联网搜索...',
                'network_unavailable': '网络连接不可用，显示离线回答',
                'generating_enhanced': '正在基于搜索结果生成更准确的回答...',
                'search_no_results': '搜索未找到相关结果',
                'ready': '就绪',
                'unknown_status': '状态: 未知',
                'autostart_enabled': '状态: 已启用开机启动',
                'autostart_disabled': '状态: 未启用开机启动',
                'autostart_check_failed': '状态: 无法检查',
                'ollama_not_found': '未找到 Ollama',
                'checking_ollama_service': '正在检查Ollama服务...',
                'ollama_service_running': 'Ollama服务已运行',
                'ollama_process_waiting': 'Ollama进程在运行，等待服务就绪...',
                'ollama_service_ready': 'Ollama服务已就绪',
                'ollama_service_not_responding': 'Ollama服务不响应，尝试重启...',
                'starting_ollama_service': '启动Ollama服务...',
                'ollama_service_started': 'Ollama服务启动成功',
                'ollama_service_start_failed': 'Ollama服务启动失败',
                'ollama_not_installed': '未找到Ollama，请先安装',
                'ollama_service_check_failed': 'Ollama服务检查失败'
            },
            'dialogs': {
                'warning': '警告',
                'error': '错误',
                'confirm': '确认',
                'select_model_warning': '请选择要下载的模型',
                'service_not_running': 'Ollama 服务未运行，请先启动服务',
                'ollama_not_found': '未找到 Ollama 可执行文件',
                'select_delete_model': '请选择要删除的模型',
                'confirm_delete': '确定要删除模型 {} 吗？',
                'select_chat_model': '请选择一个模型',
                'config_save_failed': '保存配置失败: {}',
                'no_models_title': '没有找到模型',
                'no_models_message': '您还没有安装任何AI模型。是否现在下载轻量级的qwen3:0.6b模型开始使用？\n\n这个模型只有0.6GB大小，非常适合初次体验。',
                'download_now': '现在下载',
                'download_later': '稍后下载'
            },
            'debug': {
                'init_refresh_failed': '初始化时刷新模型列表失败: {}',
                'webview_link_error': '设置WebView链接处理时出错: {}',
                'simple_link_error': '设置简单链接处理时出错: {}',
                'url_change_error': '处理URL变化时出错: {}',
                'url_intercepted': '拦截URL变化: {}',
                'open_link_error': '打开链接时出错: {}',
                'open_link_success': '在系统浏览器中打开链接: {}',
                'url_convert_error': 'URL转换出错: {}',
                'search_connectivity_failed': '搜索引擎连通性检查失败: HTTP {}',
                'search_connectivity_error': '搜索引擎连通性检查失败: {}',
                'received_reply': '[DEBUG] 收到LLM回复，长度: {} 字符',
                'reply_preview': '[DEBUG] 回复内容预览: {}...',
                'start_review': '[DEBUG] 启动审查线程，问题: {}',
                'review_complete': '[DEBUG] 审查完成 - 需要搜索: {}, 可信度: {}',
                'review_result': '[DEBUG] 审查结果: {}...',
                'filter_reply_error': '过滤LLM回复时出错: {}',
                'conversation_total': '[DEBUG] ChatThread - 对话历史总数: {}, 过滤后: {}, 发送给AI: {}',
                'history_item': '[DEBUG] ChatThread 历史{}: {} - {}',
                'read_models_error': '读取可下载模型数据失败: {}'
            },
            'models': {
                'header_labels': ['模型名称', '大小', '描述'],
                'default_models': [
                    {
                        "name": "qwen3:0.6b",
                        "size": "0.6GB",
                        'description': 'Llama 3.2 1B - 轻量级对话模型'
                    },
                    {
                        "name": "qwen3:1.7b",
                        "size": "1.4GB",
                        "description": "Qwen3 1.7B - 阿里巴巴通义千问"
                     },
                        {
                        "name": "gemma3:4b",
                        "size": "3.3GB",
                        "description": "Gemma3 4B - 大规模Google模型"
                        },
                        {
                        "name": "qwen3:4b",
                        "size": "2.5GB",
                        "description": "Qwen3 4B - 通义千问大模型"
                        },
                        {
                        "name": "gemma3:12b",
                        "size": "8.1GB",
                        "description": "Gemma3 12B - 大规模Google模型"
                        },
                        {
                        "name": "qwen3:14b",
                        "size": "9.3GB",
                        "description": "Qwen3 14B - 通义千问大模型"
                        },
                        {
                        "name": "gpt-oss:20b",
                        "size": "14GB",
                        "description": "OpenAI gpt - OpenAI最新对话模型"
                        }
                ]
            },
            
            # 保留原有的简单键（向后兼容）
            'window_title': 'MiniAI - 267278466@qq.com',
            'refresh': '刷新',
            'browse': '浏览',
            'reset_defaults': '重置默认',
            'test_connection': '测试连接',
            'save_settings': '保存设置',
            'exit': '退出',
            'success': '成功',
            'failed': '失败'
        },
        
        'en': {
            'warnings': {
                'webengine_unavailable': 'Warning: PyQtWebEngine not available, using alternative search method'
            },
            'download': {
                'downloading': 'Downloading...',
                'getting_model_info': 'Getting model information...',
                'verifying_integrity': 'Verifying model integrity...',
                'writing_manifest': 'Writing model manifest...',
                'download_complete': 'Download complete!',
                'download_success': 'Download complete',
                'download_failed': 'Download failed',
                'download_failed_with_error': 'Download failed: {}'
            },
            'chat': {
                'building_prompt': 'Error building conversation prompt: {}',
                'conversation_history': 'Here is the recent conversation history, please answer the user\'s new question based on this context:\n\n',
                'history_section': '=== Conversation History ===\n',
                'current_question': '\n=== Current Question ===\n',
                'user_prefix': 'User: {}\n\n',
                'instruction': 'Please provide an appropriate answer based on the conversation history above:',
                'history_error': 'Error getting conversation history: {}',
                'request_failed': 'Request failed: {}',
                'generate_failed': 'Failed to generate reply: {}',
            'user': 'User',
            'assistant': 'Assistant',
            'assistant_enhanced': 'Assistant (Web Enhanced)',
            'system': 'System',
                'welcome_message': 'Welcome to MiniAI! Please select a model to start chatting.'
            },
            'review': {
                'review_started': '[DEBUG] Review thread started',
                'original_question': '[DEBUG] Original question: {}',
                'answer_length': '[DEBUG] Answer length: {} characters',
                'greeting_detected': 'Simple greeting detected, passing review directly.',
                'non_intellectual': 'Non-intellectual question detected (casual conversation, emotional exchange, etc.), confidence set to 100%.',
                'uncertainty_result': '[DEBUG] Uncertainty detection result: {}',
                'uncertainty_detected': 'AI answer admits uncertainty or not knowing, confidence set to 0. Need to search for accurate information.',
                'confidence_zero': '[DEBUG] Set confidence to 0, reason: {}',
                'time_confidence': '[DEBUG] Time detection result: {}',
                'time_info_detected': 'Answer contains time information within 5 years of current date, confidence set to 0. Need to search for latest information.',
                'review_failed': 'Review request failed: {}',
                'review_error': 'Answer review failed: {}',
                'greeting_check_error': 'Greeting detection error: {}',
                'intellectual_check_error': 'Intellectual question detection error: {}',
                'uncertainty_detected_phrases': '[DEBUG] Uncertainty detection - detected phrases: {}',
                'uncertainty_excluded': '[DEBUG] Uncertainty detection - phrases after exclusion: {}',
                'uncertainty_found': '[DEBUG] ✅ Uncertainty expression detected: {}',
                'uncertainty_all_excluded': '[DEBUG] ❌ All detected phrases were excluded',
                'uncertainty_none': '[DEBUG] ❌ No uncertainty expressions detected',
                'too_many_questions': 'Too many question marks detected: {} count',
                'too_many_maybe': 'Too many uncertain words detected: {} count',
                'uncertain_ending': 'Uncertain ending detected: \'{}\'',
                'uncertainty_check_error': 'Uncertainty detection error: {}',
                'time_check_started': '[DEBUG] Time detection started, current year: {}',
                'text_length': '[DEBUG] Text length for detection: {} characters',
                'relative_time_detected': '[DEBUG] Relative time keyword detected: {}',
                'time_confidence_zero': '[DEBUG] Time detection returns 0 (confidence 0)',
                'years_found': '[DEBUG] Years detected: {}',
                'year_difference': '[DEBUG] Year {} differs from current year {} by {} years',
                'year_within_five': '[DEBUG] Year {} within 5 years, time detection returns 0 (confidence 0)',
                'years_outside_five': '[DEBUG] All detected years outside 5 years, time detection returns 100',
                'no_time_info': '[DEBUG] No time information detected, time detection returns 100',
                'time_check_error': 'Time detection error: {}'
            },
            'search': {
                'source_format': 'Source {}: {}\nContent: {}...',
                'no_valid_results': 'Unable to get valid search result content',
                'search_request_failed': 'Search request failed: {}',
                'search_failed': 'Web search failed: {}'
            },
            'enhanced': {
                'generation_failed': 'Enhanced answer generation failed: {}',
                'generation_error': 'Enhanced answer generation failed: {}',
                'enhanced_prompt_base': 'Based on the following web search results and conversation history, please answer the user\'s question:\n\n',
                'history_section': '=== Conversation History ===\n',
                'current_question_section': '=== Current Question ===\nUser question: {}\n\n',
                'search_results_section': '=== Web Search Results ===\n{}\n\n',
                'instruction': 'Please provide an accurate, detailed and useful answer based on the search results and conversation history above. If the search results contain relevant information, prioritize using this information. Please ensure accuracy and reliability of the answer while maintaining coherence with the conversation history.\n\nAnswer:',
                'prompt_error': 'Error building enhanced prompt: {}',
                'history_error': 'Error getting conversation history: {}'
            },
            'ui': {
                'tab_chat': 'Chat',
                'tab_models': 'Model Management',
                'tab_autostart': 'Service Management',
                'tab_environment': 'Environment Settings',
                'select_model': 'Select Model:',
                'clear_chat': 'Clear Chat',
                'save_chat': 'Save Chat',
                'send': 'Send',
                'input_placeholder': 'Enter your message... (Ctrl+Enter to send)',
                'available_models': 'Available Models',
            'local_models': 'Local Models',
            'download_model': 'Download Model',
            'delete_model': 'Delete Model',
                'autostart_title': 'Autostart Settings',
                'autostart_checkbox': 'Auto-start Ollama service on boot',
            'start_service': 'Start Service',
            'stop_service': 'Stop Service',
            'check_status': 'Check Status',
                'path_info': 'Path Information',
                'ollama_path': 'Ollama Path:',
                'models_path': 'Models Path:',
                'env_variables': 'Environment Variables',
                'host_label': 'OLLAMA_HOST:',
                'port_label': 'OLLAMA_PORT:',
                'models_label': 'OLLAMA_MODELS:',
                'current_env_info': 'Current Environment Information'
            },
            'status': {
                'service_not_running': 'Ollama service not running, please start the service first',
                'models_loaded': 'Loaded {} local models',
                'no_models': 'No local models found, please download models first',
                'get_models_failed': 'Failed to get local model list: {}',
                'downloading_model': 'Downloading model: {}',
                'model_deleted': 'Model {} deleted',
                'delete_failed': 'Failed to delete model: {}',
                'generating_reply': 'Generating reply...',
                'reviewing_quality': 'Reviewing answer quality...',
                'checking_network': 'Checking network connection...',
                'searching_online': 'Searching online...',
                'network_unavailable': 'Network connection unavailable, showing offline answer',
                'generating_enhanced': 'Generating more accurate answer based on search results...',
                'search_no_results': 'Search found no relevant results',
                'ready': 'Ready',
                'unknown_status': 'Status: Unknown',
                'autostart_enabled': 'Status: Autostart enabled',
                'autostart_disabled': 'Status: Autostart disabled',
                'autostart_check_failed': 'Status: Unable to check',
                'ollama_not_found': 'Ollama not found',
                'checking_ollama_service': 'Checking Ollama service...',
                'ollama_service_running': 'Ollama service is running',
                'ollama_process_waiting': 'Ollama process running, waiting for service...',
                'ollama_service_ready': 'Ollama service is ready',
                'ollama_service_not_responding': 'Ollama service not responding, restarting...',
                'starting_ollama_service': 'Starting Ollama service...',
                'ollama_service_started': 'Ollama service started successfully',
                'ollama_service_start_failed': 'Failed to start Ollama service',
                'ollama_not_installed': 'Ollama not found, please install first',
                'ollama_service_check_failed': 'Ollama service check failed'
            },
            'dialogs': {
                'warning': 'Warning',
                'error': 'Error',
                'confirm': 'Confirm',
                'select_model_warning': 'Please select a model to download',
                'service_not_running': 'Ollama service not running, please start the service first',
                'ollama_not_found': 'Ollama executable not found',
                'select_delete_model': 'Please select a model to delete',
                'confirm_delete': 'Are you sure you want to delete model {}?',
                'select_chat_model': 'Please select a model',
                'config_save_failed': 'Failed to save configuration: {}',
                'no_models_title': 'No Models Found',
                'no_models_message': 'You haven\'t installed any AI models yet. Would you like to download the lightweight qwen3:0.6b model to get started?\n\nThis model is only 0.6GB in size and perfect for first-time experience.',
                'download_now': 'Download Now',
                'download_later': 'Download Later'
            },
            'debug': {
                'init_refresh_failed': 'Failed to refresh model list during initialization: {}',
                'webview_link_error': 'Error setting WebView link handling: {}',
                'simple_link_error': 'Error setting simple link handling: {}',
                'url_change_error': 'Error handling URL change: {}',
                'url_intercepted': 'URL change intercepted: {}',
                'open_link_error': 'Error opening link: {}',
                'open_link_success': 'Opened link in system browser: {}',
                'url_convert_error': 'URL conversion error: {}',
                'search_connectivity_failed': 'Search engine connectivity check failed: HTTP {}',
                'search_connectivity_error': 'Search engine connectivity check failed: {}',
                'received_reply': '[DEBUG] Received LLM reply, length: {} characters',
                'reply_preview': '[DEBUG] Reply preview: {}...',
                'start_review': '[DEBUG] Starting review thread, question: {}',
                'review_complete': '[DEBUG] Review complete - needs search: {}, confidence: {}',
                'review_result': '[DEBUG] Review result: {}...',
                'filter_reply_error': 'Error filtering LLM reply: {}',
                'conversation_total': '[DEBUG] ChatThread - conversation history total: {}, filtered: {}, sent to AI: {}',
                'history_item': '[DEBUG] ChatThread history {}: {} - {}',
                'read_models_error': 'Failed to read downloadable model data: {}'
            },
            'models': {
                'header_labels': ['Model Name', 'Size', 'Description'],
                'default_models': [
                    
                ]
            },
            
            # 保留原有的简单键（向后兼容）
            'window_title': 'MiniAI - 267278466@qq.com',
            'refresh': 'Refresh',
            'browse': 'Browse',
            'reset_defaults': 'Reset Defaults',
            'test_connection': 'Test Connection',
            'save_settings': 'Save Settings',
            'exit': 'Exit',
            'success': 'Success',
            'failed': 'Failed'
        }
    }

# 创建全局实例
i18n = MiniAI_i18n()

# 便捷函数
def get_text(key, category=None, **kwargs):
    """获取国际化文本的便捷函数"""
    return i18n.get_text(key, category, **kwargs)

def set_language(language):
    """设置语言的便捷函数"""
    i18n.set_language(language)

def get_current_language():
    """获取当前语言"""
    return i18n.language

# 测试函数
def test_i18n():
    """测试国际化功能"""
    print("=== MiniAI i18n Test (合并版本) ===")
    print(f"Current language: {get_current_language()}")
    
    # 测试中文
    set_language('zh')
    print(f"\n中文测试:")
    print(f"  窗口标题: {get_text('window_title')}")
    print(f"  聊天标签: {get_text('tab_chat', 'ui')}")
    print(f"  发送按钮: {get_text('send', 'ui')}")
    print(f"  点号路径: {get_text('ui.send')}")
    print(f"  格式化文本: {get_text('downloading_model', 'status', model='test_model')}")
    
    # 测试英文
    set_language('en')
    print(f"\n英文测试:")
    print(f"  Window title: {get_text('window_title')}")
    print(f"  Chat tab: {get_text('tab_chat', 'ui')}")
    print(f"  Send button: {get_text('send', 'ui')}")
    print(f"  Dot path: {get_text('ui.send')}")
    print(f"  Formatted text: {get_text('downloading_model', 'status', model='test_model')}")
    
    # 测试分类数量统计
    zh_categories = len(i18n.texts['zh'])
    en_categories = len(i18n.texts['en'])
    print(f"\n统计信息:")
    print(f"  中文分类数: {zh_categories}")
    print(f"  英文分类数: {en_categories}")
    print(f"  文本对应状态: {'✅ 完全对应' if zh_categories == en_categories else '❌ 不对应'}")

if __name__ == "__main__":
    test_i18n()
