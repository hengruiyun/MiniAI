#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MiniAI - PyQt5 Version
Author: 267278466@qq.com
Version: 2.1.0
"""

# 版本信息
__version__ = "2.1.0"

import os
import sys
import json
import time
import threading
import subprocess
import requests
from pathlib import Path
# 禁用SSL警告
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
import winreg
from datetime import datetime, date
import webbrowser
import locale
import argparse
import re
import urllib.parse
from bs4 import BeautifulSoup

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QTabWidget, QLabel, QPushButton, QCheckBox, QComboBox, QLineEdit,
    QTextEdit, QTextBrowser, QListWidget, QTreeWidget, QTreeWidgetItem, QProgressBar,
    QGroupBox, QGridLayout, QFormLayout, QMessageBox, QFileDialog,
    QSplitter, QFrame, QScrollArea, QSpacerItem, QSizePolicy
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer, QSize, QUrl
from PyQt5.QtGui import QFont, QIcon, QPalette, QColor, QPixmap
try:
    from PyQt5.QtWebEngineWidgets import QWebEngineView
    WEBENGINE_AVAILABLE = True
except ImportError:
    print("警告: PyQtWebEngine不可用，将使用备用搜索方法")
    WEBENGINE_AVAILABLE = False
    QWebEngineView = None


class DownloadThread(QThread):
    """下载模型的线程"""
    progress_updated = pyqtSignal(int, str)
    download_finished = pyqtSignal(bool, str)
    
    def __init__(self, ollama_path, model_name):
        super().__init__()
        self.ollama_path = ollama_path
        self.model_name = model_name
        
    def run(self):
        try:
            import re
            
            process = subprocess.Popen(
                [str(self.ollama_path), "pull", self.model_name],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding='utf-8',
                errors='ignore',
                universal_newlines=True,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
            )
            
            if process.stdout:
                for line in iter(process.stdout.readline, ''):
                    line = line.strip()
                    if not line:
                        continue
                    
                    # 解析进度
                    percent_match = re.search(r'(\d+)%', line)
                    if percent_match:
                        percentage = int(percent_match.group(1))
                        download_msg = f"{percentage}% - " + "下载中..."  # 保持原有格式
                        self.progress_updated.emit(percentage, download_msg)
                    elif "pulling manifest" in line.lower():
                        self.progress_updated.emit(5, "正在获取模型信息...")
                    elif "verifying sha256 digest" in line.lower():
                        self.progress_updated.emit(95, "验证模型完整性...")
                    elif "writing manifest" in line.lower():
                        self.progress_updated.emit(98, "写入模型清单...")
                    elif "success" in line.lower():
                        self.progress_updated.emit(100, "下载完成！")
            
            process.wait()
            success = process.returncode == 0
            message = "下载完成" if success else "下载失败"
            self.download_finished.emit(success, message)
            
        except Exception as e:
            self.download_finished.emit(False, f"下载失败: {e}")


class ChatThread(QThread):
    """聊天线程"""
    message_received = pyqtSignal(str)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, host, port, model, message, chat_history=None):
        super().__init__()
        self.host = host
        self.port = port
        self.model = model
        self.message = message
        self.chat_history = chat_history or []
    
    def build_conversation_prompt(self):
        """构建包含历史对话的prompt"""
        try:
            # 获取最近5个回合的对话历史
            recent_history = self.get_recent_conversation_history()
            
            if not recent_history:
                # 如果没有历史记录，直接返回当前消息
                return self.message
            
            # 构建对话上下文
            conversation_context = "以下是最近的对话历史，请基于这些上下文回答用户的新问题：\n\n"
            conversation_context += "=== 对话历史 ===\n"
            
            for entry in recent_history:
                sender = entry.get('sender', '')
                message = entry.get('message', '')
                if sender and message:
                    conversation_context += f"{sender}: {message}\n"
            
            conversation_context += "\n=== 当前问题 ===\n"
            conversation_context += f"用户: {self.message}\n\n"
            conversation_context += "请基于上述对话历史，给出恰当的回答："
            
            return conversation_context
            
        except Exception as e:
            print(f"构建对话prompt时出错: {e}")
            return self.message
    
    def get_recent_conversation_history(self):
        """获取最近5个回合的对话历史（确保完整的用户-AI对话对）"""
        try:
            if not self.chat_history:
                return []
            
            # 过滤掉系统消息，只保留用户和助手的对话
            filtered_history = []
            for entry in self.chat_history:
                sender = entry.get('sender', '')
                if sender in ['我', 'AI 助手', 'AI 助手(联网增强)', 'user', 'assistant']:
                    filtered_history.append(entry)
            
            # 获取最近10条记录（5个回合，每个回合包含用户问题和助手回答）
            # 确保获取完整的5个对话回合，优先保证对话的完整性
            recent_entries = filtered_history[-10:] if len(filtered_history) > 10 else filtered_history
            
            print(f"[DEBUG] ChatThread - 对话历史总数: {len(self.chat_history)}, 过滤后: {len(filtered_history)}, 发送给AI: {len(recent_entries)}")
            for i, entry in enumerate(recent_entries):
                sender = entry.get('sender', '')
                message = entry.get('message', '')[:50] + "..." if len(entry.get('message', '')) > 50 else entry.get('message', '')
                print(f"[DEBUG] ChatThread 历史{i+1}: {sender} - {message}")
            
            return recent_entries
            
        except Exception as e:
            print(f"获取对话历史时出错: {e}")
            return []
        
    def run(self):
        try:
            # 构建包含历史对话的prompt
            prompt = self.build_conversation_prompt()
            
            url = f"http://{self.host}:{self.port}/api/generate"
            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": False
            }
            
            response = requests.post(url, json=payload, timeout=60)
            
            if response.status_code == 200:
                data = response.json()
                reply = data.get("response", "")
                self.message_received.emit(reply)
            else:
                self.error_occurred.emit(f"请求失败: {response.status_code}")
                
        except Exception as e:
            self.error_occurred.emit(f"生成回复失败: {e}")


class AnswerReviewThread(QThread):
    """答案审查线程"""
    review_completed = pyqtSignal(bool, float, str)  # 是否需要搜索, 可信度, 审查结果
    error_occurred = pyqtSignal(str)
    
    def __init__(self, host, port, model, original_question, answer):
        super().__init__()
        self.host = host
        self.port = port
        self.model = model
        self.original_question = original_question
        self.answer = answer
        
    def run(self):
        try:
            print(f"[DEBUG] 审查线程开始运行")
            print(f"[DEBUG] 原始问题: {self.original_question}")
            print(f"[DEBUG] 回答长度: {len(self.answer)} 字符")
            
            # 优先检查：时间相关问题直接设置可信度为0，触发联网搜索
            if self.is_time_related_question(self.original_question):
                review_result = "检测到时间相关问题，直接设置可信度为0，触发联网搜索获取最新时间信息。"
                print(f"[DEBUG] 时间相关问题优先处理: {review_result}")
                self.review_completed.emit(True, 0.0, review_result)
                return
            
            # 检查是否为简单问候语，如果是则直接通过
            if self.is_simple_greeting(self.original_question):
                review_result = "检测到简单问候语，直接通过审查。"
                self.review_completed.emit(False, 95.0, review_result)
                return
            
            # 检查是否为智力问题，如果不是则直接通过
            if not self.is_intellectual_question(self.original_question):
                review_result = "检测到非智力问题（日常对话、情感交流等），可信度设为100%。"
                self.review_completed.emit(False, 100.0, review_result)
                return
            
            # 检查AI回答中是否主动承认不确定或不知道
            uncertainty_detected = self.check_uncertainty_admission(self.answer)
            print(f"[DEBUG] 不确定性检测结果: {uncertainty_detected}")
            if uncertainty_detected:
                review_result = "检测到AI回答中主动承认不确定或不知道，可信度设置为0。需要联网搜索准确信息。"
                print(f"[DEBUG] 设置可信度为0，原因: {review_result}")
                self.review_completed.emit(True, 0.0, review_result)
                return
            
            # 检查回答中是否包含时间信息
            time_confidence_score = self.check_time_related_content(self.answer)
            print(f"[DEBUG] 时间检测结果: {time_confidence_score}")
            print(f"[DEBUG] 被检测的回答内容: {self.answer[:200]}...")
            
            if time_confidence_score == 0:
                # 如果检测到时间相关内容且在5年内，直接设置可信度为0
                review_result = f"检测到回答中包含时间信息且与当前日期相差在5年内，可信度设置为0。需要联网搜索最新信息。"
                print(f"[DEBUG] 强制设置可信度为0，触发联网搜索")
                self.review_completed.emit(True, 0.0, review_result)
                return
            
            # 构建审查提示
            review_prompt = f"""
请审查以下问答对的质量和可信度：

问题：{self.original_question}

回答：{self.answer}

请从以下几个维度评估回答质量：
1. 回答是否直接回应了问题
2. 回答内容是否准确和可信
3. 回答是否完整和详细
4. 是否存在明显的错误或不确定性

请给出一个0-100的可信度分数，并简要说明理由。
如果可信度低于70分，建议进行网络搜索以获取更准确的信息。

请按以下格式回复：
可信度分数：[分数]
理由：[简要说明]
建议：[是否需要网络搜索]
"""
            
            url = f"http://{self.host}:{self.port}/api/generate"
            payload = {
                "model": self.model,
                "prompt": review_prompt,
                "stream": False
            }
            
            response = requests.post(url, json=payload, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                review_result = data.get("response", "")
                
                # 解析审查结果
                confidence_score = self.extract_confidence_score(review_result)
                needs_search = confidence_score < 70
                
                self.review_completed.emit(needs_search, confidence_score, review_result)
            else:
                self.error_occurred.emit(f"审查请求失败: {response.status_code}")
                
        except Exception as e:
            self.error_occurred.emit(f"答案审查失败: {e}")
    
    def is_simple_greeting(self, question):
        """检查是否为简单问候语"""
        try:
            question_lower = question.lower().strip()
            
            # 常见问候语列表
            greetings = [
                '你好', 'hello', 'hi', '您好', '早上好', '下午好', '晚上好',
                '早安', '晚安', 'good morning', 'good afternoon', 'good evening',
                'good night', '嗨', 'hey', '哈喽', '哈罗', '喂', '在吗',
                '在不在', '有人吗', '请问', '打扰了', '不好意思', 'excuse me',
                'sorry', '谢谢', 'thank you', 'thanks', '再见', 'bye', 'goodbye',
                '拜拜', '回见', 'see you', '怎么样', 'how are you', '最近怎么样',
                '近来可好', '还好吗', '一切都好吗', '身体好吗'
            ]
            
            # 检查是否为纯问候语（去除标点符号）
            clean_question = ''.join(c for c in question_lower if c.isalnum() or c.isspace())
            clean_question = clean_question.strip()
            
            # 精确匹配或包含匹配
            for greeting in greetings:
                if clean_question == greeting or (len(clean_question) <= 10 and greeting in clean_question):
                    return True
            
            # 检查是否为很短的问句（可能是问候）
            if len(clean_question) <= 5 and any(char in clean_question for char in ['你', '好', 'hi', 'hey']):
                return True
                
            return False
            
        except Exception as e:
            print(f"问候语检测出错: {e}")
            return False
    
    def is_time_related_question(self, question):
        """判断是否为时间相关问题，需要实时信息"""
        try:
            question_lower = question.lower().strip()
            print(f"[DEBUG] 检查时间相关问题: {question}")
            
            # 时间查询的关键词
            time_keywords = [
                # 直接时间询问
                '今天', '明天', '昨天', '现在', '当前',
                '今日', '明日', '昨日', '本日', '今晚',
                
                # 日期询问
                '日期', '几号', '号数', '多少号',
                '年月日', '月份', '年份',
                
                # 时间询问
                '时间', '几点', '点钟', '现在时间',
                '当前时间', '现在几点', '什么时候',
                
                # 星期询问
                '星期', '礼拜', '周几', '星期几',
                '礼拜几', '今天星期', '今天礼拜',
                
                # 时间状态
                '现在是', '今天是', '当前是',
                '现在几', '今天几', '当前几'
            ]
            
            # 检查关键词匹配
            for keyword in time_keywords:
                if keyword in question_lower:
                    print(f"[DEBUG] 匹配时间关键词: {keyword}")
                    return True
            
            # 检查时间相关的句式模式
            time_patterns = [
                r'.*今天.*', r'.*现在.*', r'.*当前.*',
                r'.*几号.*', r'.*几点.*', r'.*星期.*',
                r'.*日期.*', r'.*时间.*', r'.*礼拜.*'
            ]
            
            import re
            for pattern in time_patterns:
                if re.match(pattern, question_lower):
                    print(f"[DEBUG] 匹配时间模式: {pattern}")
                    return True
            
            print(f"[DEBUG] 不是时间相关问题")
            return False
            
        except Exception as e:
            print(f"时间问题检测出错: {e}")
            return False
    
    def is_intellectual_question(self, question):
        """判断是否为智力问题（需要知识、分析、推理的问题）"""
        try:
            question_lower = question.lower().strip()
            
            # 智力问题的关键词和模式
            intellectual_keywords = [
                # 知识性问题
                '什么是', 'what is', '如何', 'how to', 'how do', '为什么', 'why',
                '怎么样', '怎么办', '原理', '定义', '概念', '解释', '说明',
                '介绍', '区别', '差异', '比较', '优缺点', '特点', '特征',
                
                # 技术性问题
                '编程', '代码', 'python', 'java', 'javascript', 'html', 'css',
                '算法', '数据结构', '机器学习', '人工智能', 'ai', 'ml', 'dl',
                '数据库', 'sql', '网络', '服务器', '系统', '软件', '硬件',
                
                # 学术性问题
                '数学', '物理', '化学', '生物', '历史', '地理', '经济', '政治',
                '哲学', '心理学', '社会学', '文学', '艺术', '科学', '研究',
                
                # 分析性问题
                '分析', '计算', '求解', '证明', '推导', '解决', '方案', '策略',
                '方法', '步骤', '流程', '过程', '原因', '结果', '影响', '效果',
                
                # 信息查询
                '最新', '当前', '现在', '目前', '2020', '2021', '2022', '2023', '2024', '2025',
                '价格', '多少钱', '费用', '成本', '市场', '股票', '汇率', '天气',
                '新闻', '事件', '发生', '时间', '地点', '人物', '公司', '产品',
                
                # 专业领域
                '医学', '法律', '金融', '投资', '管理', '营销', '设计', '工程',
                '建筑', '教育', '培训', '考试', '证书', '资格', '职业', '工作'
            ]
            
            # 智力问题的句式模式
            intellectual_patterns = [
                r'.*是什么.*', r'.*怎么.*', r'.*如何.*', r'.*为什么.*',
                r'.*什么.*', r'.*哪.*', r'.*多少.*', r'.*几.*',
                r'.*能否.*', r'.*可以.*', r'.*应该.*', r'.*需要.*',
                r'.*有没有.*', r'.*是否.*', r'.*会不会.*', r'.*能不能.*',
                r'.*请问.*', r'.*想知道.*', r'.*了解.*', r'.*学习.*'
            ]
            
            # 非智力问题的关键词（日常对话、情感交流等）
            non_intellectual_keywords = [
                # 情感表达
                '开心', '高兴', '快乐', '伤心', '难过', '生气', '愤怒', '担心', '害怕',
                '喜欢', '讨厌', '爱', '恨', '想念', '思念', '感谢', '抱歉', '对不起',
                
                # 日常闲聊
                '聊天', '闲聊', '说话', '陪我', '无聊', '有趣', '好玩', '搞笑',
                '天气真好', '今天心情', '最近怎样', '过得如何', '身体好吗',
                
                # 简单互动
                '再见', '拜拜', '晚安', '早安', '保重', '加油', '努力', '坚持',
                '祝福', '祝贺', '恭喜', '节日快乐', '生日快乐', '新年快乐'
            ]
            
            # 检查非智力关键词
            for keyword in non_intellectual_keywords:
                if keyword in question_lower:
                    return False
            
            # 检查智力关键词
            for keyword in intellectual_keywords:
                if keyword in question_lower:
                    return True
            
            # 检查智力问题句式
            import re
            for pattern in intellectual_patterns:
                if re.match(pattern, question_lower):
                    return True
            
            # 检查问句特征（以疑问词开头或结尾有问号）
            question_words = ['什么', '怎么', '如何', '为什么', '哪', '多少', '几', 'what', 'how', 'why', 'where', 'when', 'who']
            has_question_word = any(word in question_lower for word in question_words)
            has_question_mark = '?' in question or '？' in question
            
            # 排除主观性和太短的问句
            subjective_patterns = ['你觉得', '你认为', '你喜欢', '你想', '感觉如何', '怎么样']
            is_subjective = any(pattern in question_lower for pattern in subjective_patterns)
            is_too_short = len(question.strip()) <= 5
            
            # 如果有疑问词或问号，且长度超过5个字符，且不是主观问题，可能是智力问题
            if (has_question_word or has_question_mark) and not is_too_short and not is_subjective:
                return True
            
            # 默认认为是非智力问题（日常对话）
            return False
            
        except Exception as e:
            print(f"智力问题检测出错: {e}")
            # 出错时默认认为是智力问题，进行正常审查
            return True
    
    def check_uncertainty_admission(self, answer):
        """检查AI回答中是否主动承认不确定或不知道"""
        try:
            answer_lower = answer.lower().strip()
            
            # 不确定性表达的关键词和短语
            uncertainty_phrases = [
                # 直接承认不知道
                '不知道', '不清楚', '不了解', '不确定', '不太清楚', '不太了解',
                '我不知道', '我不清楚', '我不了解', '我不确定', '我不太清楚',
                
                # 无法回答的表达
                '无法回答', '不能回答', '无法解答', '不能解答', '无法答复', '不能答复',
                '我无法回答', '我不能回答', '我无法解答', '我不能解答',
                '对不起，我无法回答', '抱歉，我无法回答', '很抱歉，我无法回答',
                '对不起，我不能回答', '抱歉，我不能回答', '很抱歉，我不能回答',
                'cannot answer', 'unable to answer', 'can\'t answer', 'i cannot answer',
                'i am unable to answer', 'i can\'t answer', 'sorry, i cannot answer',
                'sorry, i can\'t answer', 'i\'m sorry, i cannot answer',
                
                # 拒绝回答的表达
                '拒绝回答', '不便回答', '不适合回答', '不宜回答', '不方便回答',
                '我拒绝回答', '我不便回答', '我不适合回答', '我不宜回答',
                'refuse to answer', 'decline to answer', 'not appropriate to answer',
                'i refuse to answer', 'i decline to answer', 'not suitable to answer',
                
                # 英文表达
                "i don't know", "i'm not sure", "i'm uncertain", "not sure",
                "don't know", "unclear", "uncertain", "i have no idea",
                "no idea", "i'm not certain", "not certain", "i can't say",
                
                # 模糊表达
                '可能', '也许', '大概', '估计', '应该是', '似乎', '好像',
                '据我所知', '据了解', '听说', '据说', '可能是', '或许',
                'maybe', 'perhaps', 'possibly', 'probably', 'might be',
                'could be', 'seems like', 'appears to be', 'i think',
                
                # 信息缺乏表达
                '没有足够信息', '没有足够的信息', '信息不足', '缺乏信息', '无法确定', '难以确定',
                '无法给出', '无法提供', '没有相关信息', '缺少数据', '信息有限',
                'insufficient information', 'lack of information', 'no information',
                'cannot determine', 'unable to determine', 'cannot provide',
                
                # 需要更多信息
                '需要更多信息', '需要进一步', '需要查证', '建议查询', '建议搜索',
                '请查询', '请搜索', '请核实', '需要核实', '需要确认',
                'need more information', 'need to check', 'need to verify',
                'suggest checking', 'recommend checking', 'please verify',
                
                # 时效性不确定
                '可能已过时', '信息可能过时', '可能不是最新', '需要最新信息',
                '建议查看最新', '可能有变化', '情况可能改变',
                'might be outdated', 'information may be outdated', 'may have changed',
                'might have changed', 'need latest information', 'check latest',
                
                # 谦逊表达
                '我的知识有限', '知识有限', '了解有限', '可能有误', '如有错误',
                '仅供参考', '请以实际为准', '建议核实', '请确认',
                'my knowledge is limited', 'limited knowledge', 'may be incorrect',
                'for reference only', 'please verify', 'please confirm',
                
                # 推测性表达
                '我猜测', '我推测', '我认为可能', '估计可能', '大致上',
                '粗略地说', '一般来说', '通常情况下', '在我印象中',
                'i guess', 'i assume', 'i suppose', 'roughly speaking',
                'generally speaking', 'typically', 'usually', 'in my understanding',
                
                # 道德/伦理拒绝表达
                '我的目的是', '我不会参与', '我不能参与', '不实信息', '不当信息',
                '有害信息', '违法信息', '不合适的内容', '不适当的内容',
                'my purpose is', 'i will not participate', 'i cannot participate',
                'inappropriate content', 'harmful content', 'illegal content',
                'misinformation', 'false information', 'not appropriate',
                
                # 技术限制表达
                '无法访问', '不能访问', '无法连接', '不能连接', '无法获取', '不能获取',
                '无法追踪', '不能追踪', '无法检测', '不能检测', '无法查看', '不能查看',
                '无法读取', '不能读取', '无法浏览', '不能浏览', '无法打开', '不能打开',
                '我无法访问', '我不能访问', '我无法连接', '我不能连接',
                '我无法追踪', '我不能追踪', '我无法检测', '我不能检测',
                '我是一个文本模型', '我是文本模型', '作为文本模型', '作为AI模型',
                '我是AI助手', '作为AI助手', '我没有能力', '我不具备能力',
                'cannot access', 'unable to access', 'can\'t access', 'cannot connect',
                'unable to connect', 'can\'t connect', 'cannot track', 'unable to track',
                'can\'t track', 'cannot browse', 'unable to browse', 'can\'t browse',
                'i cannot access', 'i am unable to access', 'i can\'t access',
                'i cannot connect', 'i am unable to connect', 'i can\'t connect',
                'i am a text model', 'i am an ai model', 'as an ai model',
                'as a text model', 'i don\'t have the ability', 'i lack the ability',
                
                # 图片/视觉相关技术限制
                '无法提供图片', '不能提供图片', '无法生成图片', '不能生成图片',
                '无法显示图片', '不能显示图片', '无法创建图片', '不能创建图片',
                '无法处理图片', '不能处理图片', '没有图片功能', '无图片生成功能',
                '无法提供视觉', '不能提供视觉', '无法处理视觉', '不能处理视觉',
                '目前我无法提供图片', '目前无法提供图片', '我无法生成图片',
                '我不能显示图片', '作为文本AI无法', '作为语言模型无法',
                
                # 多媒体限制
                '无法播放', '不能播放', '无法显示视频', '不能显示视频',
                '无法处理音频', '不能处理音频', '无法生成音频', '不能生成音频',
                
                # 实时信息限制
                '无法获取实时', '不能获取实时', '无法访问实时', '不能访问实时',
                '无法联网', '不能联网', '无法上网', '不能上网'
            ]
            
            # 检查是否包含不确定性表达
            detected_phrases = []
            for phrase in uncertainty_phrases:
                if phrase in answer_lower:
                    detected_phrases.append(phrase)
            
            # 排除一些常见的非不确定表达
            exclude_patterns = [
                '通常情况下', '一般来说', '通常', '一般而言', 'generally', 'usually', 'typically'
            ]
            
            # 如果只检测到排除模式，不认为是不确定
            print(f"[DEBUG] 不确定性检测 - 回答内容: {answer[:100]}...")
            print(f"[DEBUG] 不确定性检测 - 检测到的短语: {detected_phrases}")
            
            if detected_phrases:
                non_excluded = [p for p in detected_phrases if p not in exclude_patterns]
                print(f"[DEBUG] 不确定性检测 - 排除后的短语: {non_excluded}")
                if non_excluded:
                    print(f"[DEBUG] ✅ 检测到不确定性表达: {non_excluded}")
                    return True
                else:
                    print(f"[DEBUG] ❌ 所有检测到的短语都被排除了")
            else:
                print(f"[DEBUG] ❌ 未检测到任何不确定性表达")
            
            # 检查问号密度（过多问号可能表示不确定）
            question_marks = answer.count('?') + answer.count('？')
            if question_marks >= 3 and len(answer) < 500:  # 短回答中有太多问号
                print(f"检测到过多问号: {question_marks}个")
                return True
            
            # 检查是否包含多个"可能"、"也许"等词汇
            maybe_words = ['可能', '也许', '大概', '估计', 'maybe', 'perhaps', 'possibly', 'probably']
            maybe_count = sum(answer_lower.count(word) for word in maybe_words)
            if maybe_count >= 3:  # 过多的不确定词汇
                print(f"检测到过多不确定词汇: {maybe_count}个")
                return True
            
            # 检查是否以不确定的方式结尾
            uncertain_endings = [
                '不太确定', '不太清楚', '可能有误', '仅供参考', '请核实',
                '建议查证', '需要确认', '可能不准确', '请以实际为准',
                'not sure', 'not certain', 'may be wrong', 'please verify',
                'please check', 'for reference only', 'need confirmation'
            ]
            
            for ending in uncertain_endings:
                if answer_lower.endswith(ending) or ending in answer_lower[-100:]:
                    print(f"检测到不确定结尾: '{ending}'")
                    return True
            
            return False
            
        except Exception as e:
            print(f"不确定性检测出错: {e}")
            return False
    
    def check_time_related_content(self, text):
        """检查回答中是否包含时间信息，如果在5年内则返回0，否则返回100"""
        try:
            current_year = date.today().year
            print(f"[DEBUG] 时间检测开始，当前年份: {current_year}")
            print(f"[DEBUG] 检测文本长度: {len(text)} 字符")
            
            # 定义各种时间模式
            time_patterns = [
                # 年份模式：2019年、2020、2021-2024等
                r'(\d{4})\s*年',
                r'\b(\d{4})\b',
                # 日期模式：2024年1月、2023-01-01等
                r'(\d{4})\s*年\s*\d+\s*月',
                r'(\d{4})-\d{1,2}-\d{1,2}',
                r'(\d{4})/\d{1,2}/\d{1,2}',
                # 月份年份：2024年1月、January 2024等
                r'(\d{4})\s*年\s*\d+\s*月',
                r'[A-Za-z]+\s+(\d{4})',
                # 时间范围：2020-2024、2019至2023等
                r'(\d{4})\s*[-至到]\s*(\d{4})',
                # 相对时间：去年、今年、明年等（这些通常意味着时效性内容）
                r'去年|今年|明年|上年|本年|下年',
                r'最近\d+年|近\d+年|过去\d+年',
                # 季度和月份：2024年第一季度、2023年Q1等
                r'(\d{4})\s*年\s*第[一二三四1234]\s*季度',
                r'(\d{4})\s*年\s*Q[1234]',
                # 发布时间、更新时间等关键词
                r'发布于\s*(\d{4})',
                r'更新于\s*(\d{4})',
                r'截至\s*(\d{4})',
                r'自\s*(\d{4})\s*年',
            ]
            
            found_years = set()
            
            # 检查相对时间关键词（这些通常表示时效性内容）
            relative_time_keywords = [
                '去年', '今年', '明年', '上年', '本年', '下年',
                '最近', '近期', '当前', '目前', '现在',
                '最新', '新发布', '刚刚', '刚发布',
                '最近几年', '近几年', '过去几年'
            ]
            
            for keyword in relative_time_keywords:
                if keyword in text:
                    print(f"[DEBUG] 检测到相对时间关键词: {keyword}")
                    print(f"[DEBUG] 时间检测返回0（可信度为0）")
                    return 0  # 包含相对时间，可能是时效性内容
            
            # 检查具体年份
            for pattern in time_patterns:
                matches = re.findall(pattern, text)
                if matches:
                    print(f"[DEBUG] 模式 '{pattern}' 匹配到: {matches}")
                for match in matches:
                    if isinstance(match, tuple):
                        # 处理元组（如时间范围）
                        for year_str in match:
                            if year_str.isdigit():
                                year = int(year_str)
                                if 1900 <= year <= 2100:  # 合理的年份范围
                                    found_years.add(year)
                    else:
                        # 处理单个匹配
                        if match.isdigit():
                            year = int(match)
                            if 1900 <= year <= 2100:  # 合理的年份范围
                                found_years.add(year)
            
            # 检查找到的年份是否在5年内
            if found_years:
                print(f"[DEBUG] 检测到年份: {found_years}")
                for year in found_years:
                    year_diff = abs(current_year - year)
                    print(f"[DEBUG] 年份 {year} 与当前年份 {current_year} 相差 {year_diff} 年")
                    if year_diff <= 5:
                        print(f"[DEBUG] 年份 {year} 在5年内，时间检测返回0（可信度为0）")
                        return 0  # 在5年内，设置可信度为0
                
                print(f"[DEBUG] 所有检测到的年份都不在5年内，时间检测返回100")
                return 100  # 不在5年内，正常处理
            
            print(f"[DEBUG] 没有检测到时间信息，时间检测返回100")
            return 100  # 没有检测到时间信息，正常处理
            
        except Exception as e:
            print(f"时间检测出错: {e}")
            return 100  # 出错时正常处理
    
    def extract_confidence_score(self, review_text):
        """从审查结果中提取可信度分数"""
        try:
            # 使用正则表达式提取分数
            score_match = re.search(r'可信度分数[：:]\s*(\d+)', review_text)
            if score_match:
                return float(score_match.group(1))
            
            # 备用方法：查找数字
            numbers = re.findall(r'\d+', review_text)
            if numbers:
                for num in numbers:
                    score = float(num)
                    if 0 <= score <= 100:
                        return score
            
            return 50  # 默认分数
        except:
            return 50


class WebSearchThread(QThread):
    """server.py搜索线程"""
    search_completed = pyqtSignal(str)  # 搜索结果
    error_occurred = pyqtSignal(str)
    
    def __init__(self, query, webview):
        super().__init__()
        self.query = query
        self.webview = webview
        self.search_results = ""
        
    def run(self):
        """使用server.py进行搜索"""
        try:
            print(f"DEBUG: 开始搜索: {self.query}")
            
            # 调用server.py的搜索功能
            search_result = self.search_with_server()
            if search_result:
                print(f"DEBUG: server.py搜索成功")
                self.search_completed.emit(search_result)
            else:
                self.error_occurred.emit("server.py搜索失败")
                
        except Exception as e:
            print(f"DEBUG: 搜索异常: {e}")
            self.error_occurred.emit(f"搜索失败: {e}")
    
    def search_with_server(self):
        """使用简化的搜索接口进行搜索"""
        try:
            import asyncio
            import os
            
            # 设置环境变量
            os.environ['SEARXNG_API_URL'] = 'https://searx.bndkt.io'
            
            print(f"DEBUG: 执行简化搜索: {self.query}")
            
            # 直接调用simple_search模块
            try:
                import simple_search
                
                # 创建事件循环并执行异步搜索
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                try:
                    search_result = loop.run_until_complete(
                        simple_search.perform_search(
                            query=self.query,
                            category="general",
                            language="auto",
                            safe_search=1,
                            time_range="",
                            output_format="html"
                        )
                    )
                    
                    if search_result and search_result.strip():
                        print(f"DEBUG: 简化搜索成功，结果长度: {len(search_result)}")
                        return search_result
                    else:
                        print("DEBUG: 搜索结果为空")
                        return None
                        
                finally:
                    loop.close()
                    
            except ImportError as e:
                print(f"DEBUG: 无法导入simple_search模块: {e}")
                return None
                
        except Exception as e:
            print(f"DEBUG: 简化搜索异常: {e}")
            return None
    
    
    def get_page_content(self, url):
        """获取网页内容"""
        try:
            print(f"DEBUG: 尝试获取页面内容: {url[:100]}...")
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'zh-CN,zh;q=0.8,en;q=0.3',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
            }
            response = requests.get(url, headers=headers, timeout=8, allow_redirects=True)
            
            if response.status_code == 200:
                # 尝试自动检测编码
                response.encoding = response.apparent_encoding or 'utf-8'
                
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # 移除脚本和样式标签
                for script in soup(["script", "style", "noscript"]):
                    script.decompose()
                
                # 尝试获取主要内容区域
                content = ""
                
                # 方法1: 查找常见的内容容器
                main_content = soup.find('div', class_=['content', 'main', 'article', 'post'])
                if main_content:
                    content = main_content.get_text()
                else:
                    # 方法2: 获取body内容
                    body = soup.find('body')
                    if body:
                        content = body.get_text()
                    else:
                        # 方法3: 获取所有文本
                        content = soup.get_text()
                
                # 清理文本
                lines = (line.strip() for line in content.splitlines())
                chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
                text = ' '.join(chunk for chunk in chunks if chunk and len(chunk) > 3)
                
                # 过滤掉过短的内容
                if len(text) < 50:
                    return ""
                
                return text[:1500]  # 限制长度
            else:
                print(f"DEBUG: 页面请求失败，状态码: {response.status_code}")
            
        except Exception as e:
            print(f"DEBUG: 获取页面内容异常: {e}")
        
        return ""


class EnhancedAnswerThread(QThread):
    """增强答案生成线程"""
    answer_generated = pyqtSignal(str)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, host, port, model, original_question, search_results, chat_history=None):
        super().__init__()
        self.host = host
        self.port = port
        self.model = model
        self.original_question = original_question
        self.search_results = search_results
        self.chat_history = chat_history or []
        
    def run(self):
        try:
            # 构建包含对话历史的增强提示
            enhanced_prompt = self.build_enhanced_prompt()
            
            url = f"http://{self.host}:{self.port}/api/generate"
            payload = {
                "model": self.model,
                "prompt": enhanced_prompt,
                "stream": False
            }
            
            response = requests.post(url, json=payload, timeout=60)
            
            if response.status_code == 200:
                data = response.json()
                enhanced_answer = data.get("response", "")
                self.answer_generated.emit(enhanced_answer)
            else:
                self.error_occurred.emit(f"增强回答生成失败: {response.status_code}")
                
        except Exception as e:
            self.error_occurred.emit(f"增强回答生成失败: {e}")
    
    def build_enhanced_prompt(self):
        """构建包含对话历史的增强提示"""
        try:
            # 获取最近的对话历史
            recent_history = self.get_recent_conversation_history()
            
            enhanced_prompt = "基于以下网络搜索结果和对话历史，请回答用户的问题：\n\n"
            
            # 添加对话历史（如果有）
            if recent_history:
                enhanced_prompt += "=== 对话历史 ===\n"
                for entry in recent_history:
                    sender = entry.get('sender', '')
                    message = entry.get('message', '')
                    if sender and message:
                        enhanced_prompt += f"{sender}: {message}\n"
                enhanced_prompt += "\n"
            
            enhanced_prompt += f"=== 当前问题 ===\n用户问题：{self.original_question}\n\n"
            enhanced_prompt += f"=== 网络搜索结果 ===\n{self.search_results}\n\n"
            enhanced_prompt += "请基于上述搜索结果和对话历史，提供一个准确、详细且有用的回答。如果搜索结果中包含相关信息，请优先使用这些信息。请确保回答的准确性和可靠性，并保持与对话历史的连贯性。\n\n回答："
            
            return enhanced_prompt
            
        except Exception as e:
            print(f"构建增强prompt时出错: {e}")
            # 回退到原始提示
            return f"""
基于以下网络搜索结果，请回答用户的问题：

用户问题：{self.original_question}

网络搜索结果：
{self.search_results}

请基于上述搜索结果，提供一个准确、详细且有用的回答。如果搜索结果中包含相关信息，请优先使用这些信息。请确保回答的准确性和可靠性。

回答：
"""
    
    def get_recent_conversation_history(self):
        """获取最近5个回合的对话历史"""
        try:
            if not self.chat_history:
                return []
            
            # 过滤掉系统消息，只保留用户和助手的对话
            filtered_history = []
            for entry in self.chat_history:
                sender = entry.get('sender', '')
                if sender in ['我', 'AI 助手', 'AI 助手(联网增强)', 'user', 'assistant']:
                    filtered_history.append(entry)
            
            # 获取最近10条记录（5个回合，每个回合包含用户问题和助手回答）
            recent_entries = filtered_history[-10:] if len(filtered_history) > 10 else filtered_history
            
            return recent_entries
            
        except Exception as e:
            print(f"获取对话历史时出错: {e}")
            return []


class OllamaSettingsQt(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # 检测系统语言
        self.detect_language()
        
        # 配置
        self.config_file = Path("ollama_config.json")
        self.config = self.load_config()
        
        # Ollama路径
        self.ollama_path = self.find_ollama_path()
        self.models_path = Path.home() / ".ollama" / "models"
        
        # 变量
        self.chat_history = []
        self.current_model = ""
        self.auto_start = False
        self.current_user_message = ""  # 保存当前用户消息用于审查
        self.pending_reply = ""  # 暂存待审查的回复
        
        # 创建隐藏的WebView用于网络搜索（如果可用）
        if WEBENGINE_AVAILABLE and QWebEngineView:
            self.hidden_webview = QWebEngineView()
            self.hidden_webview.hide()  # 隐藏WebView
            self.hidden_webview.setFixedSize(1, 1)  # 设置最小尺寸
        else:
            self.hidden_webview = None
        
        # 环境变量
        self.ollama_host = os.environ.get('OLLAMA_HOST', 'localhost')
        self.ollama_port = os.environ.get('OLLAMA_PORT', '11434')
        self.ollama_models = os.environ.get('OLLAMA_MODELS', '')
        self.ollama_keep_alive = os.environ.get('OLLAMA_KEEP_ALIVE', '5m')
        
        # 初始化GUI
        self.init_ui()
        self.load_settings()
        
        # 自动检查并启动Ollama服务
        self.auto_check_and_start_ollama()
        
        # 初始化完成后刷新模型列表（异常处理）
        try:
            self.refresh_models()
        except Exception as e:
            print(self.get_text("init_refresh_failed", "debug").format(e))
            self.update_status(self.get_text("service_not_running", "status"))
        
        self.load_downloadable_models()  # 加载可下载模型数据
        
        # 聊天消息列表（用于WebView）
        self.chat_messages = []
        
        # 检查是否有本地模型，如果没有则提示下载
        QTimer.singleShot(1000, self.check_and_prompt_for_models)  # 延迟1秒执行，确保界面完全加载
    
    def auto_check_and_start_ollama(self):
        """自动检查并启动Ollama服务"""
        try:
            self.update_status(self.get_text("checking_ollama_service", "status"))
            
            # 1. 检查Ollama服务是否可访问
            if self.check_ollama_service_availability():
                self.update_status(self.get_text("ollama_service_running", "status"))
                return True
            
            # 2. 检查Ollama进程是否在运行
            if self.check_ollama_process():
                self.update_status(self.get_text("ollama_process_waiting", "status"))
                # 等待服务就绪
                for i in range(5):
                    time.sleep(1)
                    if self.check_ollama_service_availability():
                        self.update_status(self.get_text("ollama_service_ready", "status"))
                        return True
                # 服务仍不可访问，尝试重启
                self.update_status(self.get_text("ollama_service_not_responding", "status"))
                self.restart_ollama_service()
            
            # 3. 如果进程未运行，检查是否已安装
            if self.ollama_path and self.ollama_path.exists():
                self.update_status(self.get_text("starting_ollama_service", "status"))
                if self.start_ollama_service():
                    self.update_status(self.get_text("ollama_service_started", "status"))
                    return True
                else:
                    self.update_status(self.get_text("ollama_service_start_failed", "status"))
                    return False
            else:
                self.update_status(self.get_text("ollama_not_installed", "status"))
                return False
                
        except Exception as e:
            print(f"自动检查Ollama服务时出错: {e}")
            self.update_status(self.get_text("ollama_service_check_failed", "status"))
            return False
    
    def check_ollama_service_availability(self):
        """检查Ollama服务是否可访问"""
        try:
            import requests
            url = f"http://{self.ollama_host}:{self.ollama_port}/api/tags"
            response = requests.get(url, timeout=3)
            return response.status_code == 200
        except:
            return False
    
    def check_ollama_process(self):
        """检查Ollama进程是否在运行"""
        try:
            import psutil
            for proc in psutil.process_iter(['pid', 'name', 'exe']):
                try:
                    if proc.info['name'] and 'ollama' in proc.info['name'].lower():
                        return True
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            return False
        except ImportError:
            # 如果没有psutil，使用tasklist命令检查
            try:
                result = subprocess.run(
                    ["tasklist", "/FI", "IMAGENAME eq ollama.exe"],
                    capture_output=True, text=True,
                    creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
                )
                return "ollama.exe" in result.stdout.lower()
            except:
                return False
    
    def start_ollama_service(self):
        """启动Ollama服务"""
        if not self.ollama_path or not self.ollama_path.exists():
            return False
        
        try:
            # 方法1: 直接启动ollama serve
            subprocess.Popen(
                [str(self.ollama_path), "serve"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
            )
            
            # 等待服务启动
            for i in range(8):
                time.sleep(1)
                if self.check_ollama_service_availability():
                    return True
            
            # 如果直接启动失败，尝试使用start命令
            if sys.platform == "win32":
                subprocess.Popen(
                    f'start "Ollama Service" /min "{self.ollama_path}" serve',
                    shell=True,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
                
                # 再次等待服务启动
                for i in range(8):
                    time.sleep(1)
                    if self.check_ollama_service_availability():
                        return True
            
            return False
            
        except Exception as e:
            print(f"启动Ollama服务时出错: {e}")
            return False
    
    def restart_ollama_service(self):
        """重启Ollama服务"""
        try:
            # 尝试终止现有进程
            if self.check_ollama_process():
                try:
                    import psutil
                    for proc in psutil.process_iter(['pid', 'name']):
                        try:
                            if proc.info['name'] and 'ollama' in proc.info['name'].lower():
                                proc.terminate()
                                proc.wait(timeout=5)
                        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.TimeoutExpired):
                            continue
                except ImportError:
                    # 如果没有psutil，使用taskkill命令
                    if sys.platform == "win32":
                        subprocess.run(
                            ["taskkill", "/F", "/IM", "ollama.exe"],
                            stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL,
                            creationflags=subprocess.CREATE_NO_WINDOW
                        )
                
                time.sleep(2)
            
            # 重新启动服务
            return self.start_ollama_service()
            
        except Exception as e:
            print(f"重启Ollama服务时出错: {e}")
            return False
    
    def setup_webview_link_handling(self):
        """设置WebView链接点击处理 - 在系统浏览器中打开"""
        try:
            if WEBENGINE_AVAILABLE and hasattr(self.chat_display, 'page'):
                # 重写createWindow方法来拦截新窗口请求
                page = self.chat_display.page()
                
                # 连接linkClicked信号（如果可用）
                if hasattr(page, 'linkClicked'):
                    page.linkClicked.connect(self.open_link_in_browser)
                
                # 使用JavaScript拦截链接点击
                js_code = """
                document.addEventListener('click', function(e) {
                    if (e.target.tagName === 'A' && e.target.href) {
                        e.preventDefault();
                        window.open_external_link(e.target.href);
                        return false;
                    }
                });
                """
                
                # 注册JavaScript接口
                from PyQt5.QtWebChannel import QWebChannel
                from PyQt5.QtCore import QObject, pyqtSlot
                
                class LinkHandler(QObject):
                    def __init__(self, parent):
                        super().__init__()
                        self.parent = parent
                    
                    @pyqtSlot(str)
                    def open_external_link(self, url):
                        self.parent.open_link_in_browser(QUrl(url))
                
                self.link_handler = LinkHandler(self)
                self.web_channel = QWebChannel()
                self.web_channel.registerObject("linkHandler", self.link_handler)
                page.setWebChannel(self.web_channel)
                
                # 修改JavaScript代码使用注册的对象
                js_code = """
                document.addEventListener('click', function(e) {
                    if (e.target.tagName === 'A' && e.target.href) {
                        e.preventDefault();
                        if (window.qt && window.qt.webChannelTransport) {
                            new QWebChannel(qt.webChannelTransport, function(channel) {
                                channel.objects.linkHandler.open_external_link(e.target.href);
                            });
                        }
                        return false;
                    }
                });
                """
                
                # 延迟执行JavaScript
                def setup_js():
                    page.runJavaScript(js_code)
                
                QTimer.singleShot(500, setup_js)
                
        except Exception as e:
            print(f"设置WebView链接处理时出错: {e}")
            # 回退方案：简单的JavaScript拦截
            self.setup_simple_link_handling()
    
    def setup_simple_link_handling(self):
        """简单的链接处理方案"""
        try:
            if WEBENGINE_AVAILABLE and hasattr(self.chat_display, 'page'):
                page = self.chat_display.page()
                
                # 监听URL变化
                page.urlChanged.connect(self.handle_url_change)
                
        except Exception as e:
            print(f"设置简单链接处理时出错: {e}")
    
    def handle_url_change(self, url):
        """处理URL变化"""
        try:
            url_str = url.toString()
            # 如果不是初始页面，则在系统浏览器中打开
            if url_str and not url_str.startswith('data:') and not url_str.startswith('about:'):
                print(f"拦截URL变化: {url_str}")
                webbrowser.open(url_str)
                # 阻止在WebView中加载
                self.chat_display.stop()
                # 重新加载聊天HTML
                self.init_chat_html()
        except Exception as e:
            print(f"处理URL变化时出错: {e}")
    
    def open_link_in_browser(self, url):
        """在系统浏览器中打开链接"""
        try:
            if isinstance(url, QUrl):
                url_str = url.toString()
            else:
                url_str = str(url)
            
            print(f"在系统浏览器中打开链接: {url_str}")
            webbrowser.open(url_str)
            
        except Exception as e:
            print(f"打开链接时出错: {e}")
    
    def convert_urls_to_links(self, text):
        """将文本中的URL转换为可点击的链接"""
        try:
            import re
            
            # URL正则表达式模式
            url_pattern = r'(https?://[^\s<>"{}|\\^`\[\]]+)'
            
            def replace_url(match):
                url = match.group(1)
                # 移除末尾的标点符号
                while url and url[-1] in '.,;:!?':
                    url = url[:-1]
                return f'<a href="{url}" target="_blank" style="color: #0078d4; text-decoration: underline;">{url}</a>'
            
            # 替换URL为链接
            return re.sub(url_pattern, replace_url, text)
            
        except Exception as e:
            print(f"URL转换出错: {e}")
            return text
    
    def check_search_engine_connectivity(self):
        """检查简化搜索服务连通性"""
        try:
            import os
            import asyncio
            
            # 设置环境变量
            os.environ['SEARXNG_API_URL'] = 'https://searx.bndkt.io'
            
            # 测试simple_search模块
            try:
                import simple_search
                print("simple_search模块导入成功")
                
                # 测试搜索功能
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                try:
                    result = loop.run_until_complete(
                        simple_search.perform_search(
                            query="test",
                            category="general",
                            language="auto",
                            safe_search=1,
                            time_range="",
                            output_format="html"
                        )
                    )
                    
                    if result and result.strip():
                        print("简化搜索服务连通性检查成功")
                        return True
                    else:
                        print("搜索测试返回空结果")
                        return False
                        
                finally:
                    loop.close()
                    
            except ImportError as e:
                print(f"simple_search模块导入失败: {e}")
                return False
            except Exception as e:
                print(f"简化搜索连通性检查异常: {e}")
                return False
                
        except Exception as e:
            print(f"搜索服务连通性检查失败: {e}")
            return False
    
    def init_chat_html(self):
        """初始化聊天HTML内容"""
        # 使用国际化文本
        welcome_message = self.get_text('welcome_message', 'chat')
        system_label = self.get_text('system', 'chat')
        
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body {{
            font-family: 'Microsoft YaHei', 'Segoe UI', Arial, sans-serif;
            margin: 0;
            padding: 10px;
            background: linear-gradient(to bottom, #ffffff, #f8f9fa);
            font-size: 14px;
            line-height: 1.5;
        }}
        .message {{
            margin: 8px 0;
            clear: both;
            animation: fadeIn 0.3s ease-in;
        }}
        @keyframes fadeIn {{
            from {{ opacity: 0; transform: translateY(10px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}
        .user-message {{
            text-align: right;
        }}
        .user-bubble {{
            display: inline-block;
            max-width: 75%;
            background: linear-gradient(135deg, #e3f2fd, #bbdefb);
            color: #0d47a1;
            padding: 12px 16px;
            border-radius: 20px 20px 5px 20px;
            box-shadow: 0 2px 8px rgba(21,101,192,0.2);
            border: 1px solid #90caf9;
            text-align: left;
            word-wrap: break-word;
            font-weight: 500;
        }}
        .assistant-message {{
            text-align: left;
        }}
        .assistant-bubble {{
            display: inline-block;
            max-width: 75%;
            background: linear-gradient(135deg, #f8f9fa, #e9ecef);
            color: #333;
            padding: 12px 16px;
            border-radius: 20px 20px 20px 5px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            text-align: left;
            word-wrap: break-word;
        }}
        .system-bubble {{
            display: inline-block;
            max-width: 75%;
            background: linear-gradient(135deg, #fff3cd, #ffeaa7);
            color: #856404;
            padding: 12px 16px;
            border-radius: 20px 20px 20px 5px;
            box-shadow: 0 2px 8px rgba(133,100,4,0.2);
            text-align: left;
            word-wrap: break-word;
            border: 1px solid #ffeaa7;
        }}
        .timestamp {{
            font-size: 11px;
            color: #666;
            margin-bottom: 4px;
            font-weight: 500;
        }}
        .message-content {{
            font-size: 14px;
            line-height: 1.4;
            white-space: pre-wrap;
        }}
        .confidence {{
            font-size: 11px;
            color: #888;
            margin-top: 4px;
            font-style: italic;
        }}
    </style>
</head>
<body>
    <div id="messages">
        <div class="message system-message">
            <div class="system-bubble">
                <div class="timestamp">[{system_label}]</div>
                <div class="message-content">{welcome_message}</div>
            </div>
        </div>
    </div>
    <script>
        function scrollToBottom() {{
            window.scrollTo(0, document.body.scrollHeight);
        }}
        // 自动滚动到底部
        window.addEventListener('load', scrollToBottom);
    </script>
</body>
</html>
        """
        self.chat_display.setHtml(html_content)
        
    def detect_language(self):
        """检测系统语言"""
        try:
            system_locale = locale.getdefaultlocale()[0]
            if system_locale and system_locale.startswith('zh'):
                self.language = 'zh'
            else:
                self.language = 'en'
        except:
            self.language = 'en'  # 默认英文
            
        # 使用miniai_i18n模块
        self.load_i18n_module()
    
    def load_i18n_module(self):
        """加载国际化模块"""
        try:
            # 导入miniai_i18n模块
            from miniai_i18n import i18n as miniai_i18n
            
            # 设置语言
            miniai_i18n.set_language(self.language)
            
            # 使用模块的数据
            self.i18n_data = miniai_i18n.texts
            self.i18n_module = miniai_i18n
            
            print(f"成功加载miniai_i18n模块，当前语言: {self.language}")
        except ImportError as e:
            print(f"无法导入miniai_i18n模块，使用默认文本: {e}")
            self.i18n_data = self.get_default_i18n()
            self.i18n_module = None
        except Exception as e:
            print(f"加载国际化模块失败，使用默认文本: {e}")
            self.i18n_data = self.get_default_i18n()
            self.i18n_module = None
    
    def get_default_i18n(self):
        """获取默认的国际化文本（简化版）"""
        return {
            'zh': {
                'ui': {
                    'tab_chat': '聊天',
                    'tab_models': '模型管理',
                    'tab_autostart': '服务管理',
                    'tab_environment': '环境设置',
                    'select_model': '选择模型:',
                    'send': '发送',
                    'clear_chat': '清空对话',
                    'save_chat': '保存对话',
                    'available_models': '可下载模型',
                    'local_models': '本地模型',
                    'download_model': '下载模型',
                    'delete_model': '删除模型',
                    'autostart_title': '开机启动设置',
                    'autostart_checkbox': '开机自动启动 Ollama 服务',
                    'start_service': '启动服务',
                    'stop_service': '停止服务',
                    'check_status': '检查状态',
                    'env_variables': '环境变量设置',
                    'host_label': 'OLLAMA_HOST:',
                    'port_label': 'OLLAMA_PORT:',
                    'input_placeholder': '输入您的消息... (Ctrl+Enter发送)'
                },
                'chat': {
                    'system': 'AI 系统',
                    'user': '我',
                    'assistant': 'AI 助手',
                    'welcome_message': '欢迎使用MiniAI！请选择一个模型开始对话。'
                }
            },
            'en': {
                'ui': {
                    'tab_chat': 'Chat',
                    'tab_models': 'Model Management',
                    'tab_autostart': 'Service Management',
                    'tab_environment': 'Environment Settings',
                    'select_model': 'Select Model:',
                    'send': 'Send',
                    'clear_chat': 'Clear Chat',
                    'save_chat': 'Save Chat',
                    'available_models': 'Available Models',
                    'local_models': 'Local Models',
                    'download_model': 'Download Model',
                    'delete_model': 'Delete Model',
                    'autostart_title': 'Autostart Settings',
                    'autostart_checkbox': 'Auto-start Ollama service on boot',
                    'start_service': 'Start Service',
                    'stop_service': 'Stop Service',
                    'check_status': 'Check Status',
                    'env_variables': 'Environment Variables',
                    'host_label': 'OLLAMA_HOST:',
                    'port_label': 'OLLAMA_PORT:',
                    'input_placeholder': 'Enter your message... (Ctrl+Enter to send)'
                },
                'chat': {
                    'system': 'System',
                    'user': 'User',
                    'assistant': 'Assistant',
                    'welcome_message': 'Welcome to MiniAI! Please select a model to start chatting.'
                }
            }
        }
    
    def get_text(self, key, category='ui', **kwargs):
        """获取当前语言的文本"""
        try:
            # 优先使用miniai_i18n模块
            if hasattr(self, 'i18n_module') and self.i18n_module:
                # 首先尝试指定的分类
                result = self.i18n_module.get_text(key, category, **kwargs)
                # 如果没有找到且不是点号路径，尝试其他常见分类
                if result == key and '.' not in key and category:
                    fallback_categories = ['chat', 'ui', 'status', None]  # None 表示根级别
                    for fallback_cat in fallback_categories:
                        if fallback_cat != category:
                            fallback_result = self.i18n_module.get_text(key, fallback_cat, **kwargs)
                            if fallback_result != key:
                                return fallback_result
                return result
            
            # 回退到本地数据
            # 支持点号分隔的键路径，如 'ui.tab_chat'
            if '.' in key:
                parts = key.split('.')
                text_data = self.i18n_data[self.language]
                for part in parts:
                    text_data = text_data.get(part, {})
                # 返回找到的数据，可能是字符串、列表或其他类型
                text = text_data if text_data != {} else key
            else:
                # 传统方式：从指定类别获取文本
                text = self.i18n_data[self.language].get(category, {}).get(key, key)
            
            # 如果支持格式化参数
            if kwargs and isinstance(text, str) and '{}' in text:
                return text.format(**kwargs)
            return text
        except:
            return key
    
    def find_ollama_path(self):
        """查找Ollama可执行文件路径"""
        possible_paths = [
            Path.home() / "AppData/Local/Programs/Ollama/ollama.exe",
            Path("ollama.exe"),
            Path("File/ollama.exe")
        ]
        
        for path in possible_paths:
            if path.exists():
                return path
        
        # 尝试PATH
        try:
            if sys.platform == "win32":
                result = subprocess.run(["where", "ollama"], capture_output=True, text=True, 
                                      creationflags=subprocess.CREATE_NO_WINDOW)
            else:
                result = subprocess.run(["which", "ollama"], capture_output=True, text=True)
            if result.returncode == 0:
                return Path(result.stdout.strip().split('\n')[0])
        except:
            pass
        
        return None
    
    def load_config(self):
        """加载配置文件"""
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
            "window_geometry": "900x600",
            "ollama_host": "localhost",
            "ollama_port": "11434",
            "ollama_models": "",
            "ollama_keep_alive": "5m"
        }
    
    def save_config(self):
        """保存配置文件"""
        self.config["auto_start"] = self.auto_start
        self.config["selected_model"] = self.current_model
        self.config["ollama_host"] = self.ollama_host
        self.config["ollama_port"] = self.ollama_port
        self.config["ollama_models"] = self.ollama_models
        self.config["ollama_keep_alive"] = self.ollama_keep_alive
        
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            QMessageBox.critical(self, "错误", f"保存配置失败: {e}")
    
    def init_ui(self):
        """初始化用户界面"""
        # 获取版本号并添加到标题
        title = f"{self.get_text('window_title')} v{__version__}"
        self.setWindowTitle(title)
        self.setGeometry(100, 100, 900, 600)  # 减少高度从768到600
        
        # 窗口居中显示
        self.center_window()
        
        # 设置图标
        try:
            icon_path = self.get_icon_path()
            if icon_path and icon_path.exists():
                self.setWindowIcon(QIcon(str(icon_path)))
        except:
            pass
        
        # 设置现代化样式 - 字号加大一号
        self.setStyleSheet("""
            QMainWindow {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #f8f9fa, stop:1 #e9ecef);
                color: #212529;
            }
            
            QTabWidget::pane {
                border: 2px solid #dee2e6;
                background-color: white;
                border-radius: 8px;
                margin-top: 5px;
            }
            
            QTabWidget::tab-bar {
                alignment: left;
            }
            
            QTabBar::tab {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #f8f9fa, stop:1 #e9ecef);
                border: 2px solid #dee2e6;
                padding: 8px 16px;
                margin-right: 2px;
                border-radius: 8px 8px 0px 0px;
                font-weight: 600;
                font-size: 14px;
                color: #495057;
                min-width: 80px;
            }
            
            QTabBar::tab:selected {
                background: white;
                border-bottom: 2px solid white;
                color: #0078d4;
                font-weight: bold;
            }
            
            QTabBar::tab:hover:!selected {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #e9ecef, stop:1 #dee2e6);
                color: #0078d4;
            }
            
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #0078d4, stop:1 #005a9e);
                color: white;
                border: none;
                padding: 6px 16px;
                border-radius: 4px;
                font-weight: 600;
                font-size: 14px;
                min-width: 80px;
                min-height: 32px;
            }
            
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #106ebe, stop:1 #004578);
            }
            
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #005a9e, stop:1 #004578);
            }
            
            QGroupBox {
                font-weight: bold;
                font-size: 14px;
                border: 2px solid #dee2e6;
                border-radius: 8px;
                margin-top: 12px;
                padding-top: 12px;
                background-color: white;
                color: #495057;
            }
            
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 8px 0 8px;
                color: #0078d4;
                font-weight: bold;
                font-size: 14px;
            }
            
            QLineEdit {
                border: 2px solid #e1e1e1;
                border-radius: 6px;
                padding: 8px 12px;
                background-color: white;
                font-size: 14px;
                color: #495057;
            }
            
            QLineEdit:focus {
                border: 2px solid #0078d4;
                background-color: #f8f9fa;
            }
            
            QComboBox {
                border: 2px solid #e1e1e1;
                border-radius: 6px;
                padding: 6px 12px;
                background-color: white;
                font-size: 14px;
                color: #495057;
                min-height: 20px;
            }
            
            QComboBox:focus {
                border: 2px solid #0078d4;
            }
            
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid #666666;
                margin-right: 5px;
            }
            
            QTextEdit {
                border: 2px solid #e1e1e1;
                border-radius: 6px;
                background-color: white;
                padding: 8px;
                font-size: 14px;
                color: #495057;
            }
            
            QTextEdit:focus {
                border: 2px solid #0078d4;
            }
            
            QListWidget, QTreeWidget {
                border: 2px solid #e1e1e1;
                border-radius: 6px;
                background-color: white;
                alternate-background-color: #f8f9fa;
                font-size: 14px;
                color: #495057;
            }
            
            QListWidget::item, QTreeWidget::item {
                padding: 4px;
                border-bottom: 1px solid #f1f3f4;
            }
            
            QListWidget::item:selected, QTreeWidget::item:selected {
                background-color: #0078d4;
                color: white;
                border-radius: 4px;
            }
            
            QListWidget::item:hover, QTreeWidget::item:hover {
                background-color: #e3f2fd;
                border-radius: 4px;
            }
            
            QProgressBar {
                border: 2px solid #e1e1e1;
                border-radius: 8px;
                text-align: center;
                background-color: #f8f9fa;
                color: #495057;
                font-weight: bold;
                font-size: 14px;
            }
            
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #0078d4, stop:1 #00bcf2);
                border-radius: 6px;
            }
            
            QScrollBar:vertical {
                background-color: #f1f3f4;
                width: 12px;
                border-radius: 6px;
                margin: 0px;
            }
            
            QScrollBar::handle:vertical {
                background-color: #c1c1c1;
                border-radius: 6px;
                min-height: 20px;
                margin: 2px;
            }
            
            QScrollBar::handle:vertical:hover {
                background-color: #a8a8a8;
            }
            
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
            
            QCheckBox {
                color: #495057;
                font-weight: 600;
                font-size: 14px;
            }
            
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border: 2px solid #dee2e6;
                border-radius: 4px;
                background-color: white;
            }
            
            QCheckBox::indicator:checked {
                background-color: #0078d4;
                border-color: #0078d4;
                image: none;
            }
            
            QCheckBox::indicator:checked {
                background-color: #0078d4;
                border: 2px solid #0078d4;
            }
            
            QLabel {
                color: #495057;
                font-size: 14px;
            }
        """)
        
        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 主布局
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(8)  # 减少间距
        
        # 创建标签页
        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)
        
        # 设置标签页
        self.setup_chat_tab()
        self.setup_model_tab()
        self.setup_autostart_tab()
        self.setup_env_tab()
        
        # 底部按钮栏
        bottom_layout = QHBoxLayout()
        
        # HengruiYun链接
        self.hengruiyun_label = QLabel('<a href="https://github.com/hengruiyun">HengruiYun</a>')
        self.hengruiyun_label.setOpenExternalLinks(True)
        bottom_layout.addWidget(self.hengruiyun_label)
        
        # 状态标签
        self.status_label = QLabel(self.get_text("ready", "status"))
        self.status_label.setStyleSheet("QLabel { color: #666666; }")
        bottom_layout.addWidget(self.status_label)
        
        bottom_layout.addStretch()
        
        # 按钮
        self.save_btn = QPushButton(self.get_text("save_settings"))
        self.save_btn.clicked.connect(self.save_settings)
        bottom_layout.addWidget(self.save_btn)
        
        self.exit_btn = QPushButton(self.get_text("exit"))
        self.exit_btn.clicked.connect(self.close)
        bottom_layout.addWidget(self.exit_btn)
        
        main_layout.addLayout(bottom_layout)
    
    def center_window(self):
        """将窗口居中显示"""
        from PyQt5.QtWidgets import QDesktopWidget
        
        # 获取屏幕几何信息
        screen = QDesktopWidget().screenGeometry()
        # 获取窗口几何信息
        window = self.geometry()
        
        # 计算居中位置
        x = (screen.width() - window.width()) // 2
        y = (screen.height() - window.height()) // 2
        
        # 移动窗口到居中位置
        self.move(x, y)
    
    def get_icon_path(self):
        """获取图标路径"""
        try:
            if getattr(sys, 'frozen', False):
                base_path = getattr(sys, '_MEIPASS', '')
                icon_path = Path(base_path) / "mrcai.ico"
            else:
                icon_path = Path("mrcai.ico")
            return icon_path if icon_path.exists() else None
        except:
            return None
    
    def setup_chat_tab(self):
        """设置聊天标签页"""
        chat_widget = QWidget()
        self.tab_widget.addTab(chat_widget, self.get_text("tab_chat", "ui"))
        
        layout = QVBoxLayout(chat_widget)
        layout.setSpacing(6)  # 减少间距，避免最大化时过于分散
        layout.setContentsMargins(8, 8, 8, 8)  # 设置边距
        
        # 顶部区域：模型选择和聊天控制按钮
        top_layout = QHBoxLayout()
        
        # 左侧：模型选择
        model_group_layout = QHBoxLayout()
        model_label = QLabel(self.get_text("select_model", "ui"))
        model_label.setStyleSheet("QLabel { font-weight: bold; color: #333333; font-size: 15px; }")
        model_group_layout.addWidget(model_label)
        
        self.model_combo = QComboBox()
        self.model_combo.setMinimumWidth(220)
        self.model_combo.setStyleSheet("""
            QComboBox {
                border: 2px solid #e1e1e1;
                border-radius: 6px;
                padding: 6px 12px;
                background-color: white;
                font-size: 14px;
            }
            QComboBox:focus {
                border: 2px solid #0078d4;
            }
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid #666666;
                margin-right: 5px;
            }
        """)
        model_group_layout.addWidget(self.model_combo)
        
        
        top_layout.addLayout(model_group_layout)
        top_layout.addStretch()
        
        # 右侧：聊天控制按钮（移动到右上角）
        chat_controls_layout = QHBoxLayout()
        chat_controls_layout.setSpacing(8)
        
        clear_btn = QPushButton(self.get_text("clear_chat", "ui"))
        clear_btn.setStyleSheet("""
            QPushButton {
                background-color: #ff4444;
                color: white;
                border: none;
                padding: 6px 16px;
                border-radius: 4px;
                font-weight: 600;
                font-size: 13px;
                min-width: 80px;
                min-height: 32px;
            }
            QPushButton:hover {
                background-color: #ff6666;
            }
            QPushButton:pressed {
                background-color: #cc3333;
            }
        """)
        clear_btn.clicked.connect(self.clear_chat)
        chat_controls_layout.addWidget(clear_btn)
        
        save_btn = QPushButton(self.get_text("save_chat", "ui"))
        save_btn.setStyleSheet("""
            QPushButton {
                background-color: #107c10;
                color: white;
                border: none;
                padding: 6px 16px;
                border-radius: 4px;
                font-weight: 600;
                font-size: 13px;
                min-width: 80px;
                min-height: 32px;
            }
            QPushButton:hover {
                background-color: #0e6e0e;
            }
            QPushButton:pressed {
                background-color: #0c5a0c;
            }
        """)
        save_btn.clicked.connect(self.save_chat)
        chat_controls_layout.addWidget(save_btn)
        
        top_layout.addLayout(chat_controls_layout)
        layout.addLayout(top_layout)
        
        # 聊天显示区域 - 使用WebView支持HTML富文本
        if WEBENGINE_AVAILABLE and QWebEngineView:
            self.chat_display = QWebEngineView()
            self.chat_display.setMinimumHeight(300)
            # 设置链接点击行为 - 在系统浏览器中打开
            self.setup_webview_link_handling()
            # 初始化HTML内容
            self.init_chat_html()
        else:
            # 回退到QTextBrowser（支持链接点击）
            self.chat_display = QTextBrowser()
            self.chat_display.setMinimumHeight(300)
            self.chat_display.setReadOnly(True)
            self.chat_display.setOpenExternalLinks(True)  # QTextBrowser支持此方法
            # 设置文档模式支持HTML，确保不覆盖内联样式
            self.chat_display.document().setDefaultStyleSheet("""
                body { 
                    font-family: 'Microsoft YaHei', 'Segoe UI', sans-serif; 
                    font-size: 14px; 
                    line-height: 1.6;
                    margin: 0;
                    padding: 8px;
                    background-color: #fafafa;
                }
                p { margin: 0; padding: 0; }
            """)
            # 设置QTextBrowser的滚动条策略和样式
            self.chat_display.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
            self.chat_display.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            self.chat_display.setStyleSheet("""
                QTextBrowser {
                    border: 2px solid #e1e1e1;
                    border-radius: 12px;
                    background: linear-gradient(to bottom, #ffffff, #f8f9fa);
                    padding: 8px;
                    font-family: 'Microsoft YaHei', 'Segoe UI', Arial, sans-serif;
                    font-size: 15px;
                    line-height: 1.6;
                }
                QTextEdit:focus {
                    border: 2px solid #0078d4;
                    background: white;
                }
                QScrollBar:vertical {
                    background-color: #f1f1f1;
                    width: 12px;
                    border-radius: 6px;
                }
                QScrollBar::handle:vertical {
                    background-color: #c1c1c1;
                    border-radius: 6px;
                    min-height: 20px;
                }
                QScrollBar::handle:vertical:hover {
                    background-color: #a8a8a8;
                }
            """)
        
        # 对WebView设置边框样式
        if WEBENGINE_AVAILABLE and hasattr(self.chat_display, 'setHtml'):
            self.chat_display.setStyleSheet("""
                QWebEngineView {
                    border: 2px solid #e1e1e1;
                    border-radius: 12px;
                    background: white;
                }
            """)
        layout.addWidget(self.chat_display)
        
        # 输入区域 - 增加高度并美化
        input_layout = QHBoxLayout()
        input_layout.setSpacing(12)
        
        self.message_input = QTextEdit()
        self.message_input.setMaximumHeight(90)  # 增加输入框高度
        self.message_input.setMinimumHeight(90)
        self.message_input.setPlaceholderText(self.get_text("input_placeholder", "ui"))
        self.message_input.setStyleSheet("""
            QTextEdit {
                border: 2px solid #e1e1e1;
                border-radius: 8px;
                background-color: white;
                padding: 12px;
                font-family: 'Microsoft YaHei', 'Segoe UI', Arial, sans-serif;
                font-size: 15px;
                line-height: 1.4;
            }
            QTextEdit:focus {
                border: 2px solid #0078d4;
                background-color: #f8f9fa;
            }
            QScrollBar:vertical {
                background-color: #f1f1f1;
                width: 8px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical {
                background-color: #c1c1c1;
                border-radius: 4px;
                min-height: 15px;
            }
        """)
        input_layout.addWidget(self.message_input)
        
        # 发送按钮 - 适配输入框高度
        send_btn = QPushButton(self.get_text("send", "ui"))
        send_btn.setMinimumHeight(90)  # 与输入框同高
        send_btn.setMinimumWidth(100)
        send_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #0078d4, stop:1 #005a9e);
                color: white;
                border: none;
                border-radius: 8px;
                font-weight: bold;
                font-size: 15px;
                padding: 6px 16px;
                min-width: 80px;
                min-height: 32px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #106ebe, stop:1 #004578);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #005a9e, stop:1 #004578);
            }
        """)
        send_btn.clicked.connect(self.send_message)
        input_layout.addWidget(send_btn)
        
        layout.addLayout(input_layout)
        
        # 添加快捷键支持
        from PyQt5.QtGui import QKeySequence
        from PyQt5.QtWidgets import QShortcut
        
        # Ctrl+Enter 发送消息
        send_shortcut = QShortcut(QKeySequence("Ctrl+Return"), self.message_input)
        send_shortcut.activated.connect(self.send_message)
        
        # 初始化聊天
        welcome_msg = self.get_text("welcome_message", "chat")
        self.add_chat_message(self.get_text("system", "chat"), welcome_msg)
    
    def setup_model_tab(self):
        """设置模型管理标签页"""
        model_widget = QWidget()
        self.tab_widget.addTab(model_widget, self.get_text("tab_models", "ui"))
        
        layout = QVBoxLayout(model_widget)
        layout.setSpacing(12)  # 适当增加间距
        
        # 分割器
        splitter = QSplitter(Qt.Horizontal)
        splitter.setStyleSheet("""
            QSplitter::handle {
                background-color: #dee2e6;
                width: 2px;
                border-radius: 1px;
            }
            QSplitter::handle:hover {
                background-color: #0078d4;
            }
        """)
        layout.addWidget(splitter)
        
        # 左侧 - 可下载模型
        left_group = QGroupBox(self.get_text("available_models", "ui"))
        left_group.setStyleSheet("""
            QGroupBox {
                font-size: 14px;
                font-weight: bold;
                color: #0078d4;
                border: 2px solid #0078d4;
                border-radius: 8px;
                margin-top: 12px;
                padding-top: 12px;
                background-color: #f8f9ff;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 8px 0 8px;
                color: #0078d4;
                font-weight: bold;
            }
        """)
        left_layout = QVBoxLayout(left_group)
        left_layout.setSpacing(8)
        
        self.downloadable_models_tree = QTreeWidget()
        self.downloadable_models_tree.setHeaderLabels(self.get_text("models.header_labels"))
        self.downloadable_models_tree.setMaximumHeight(220)  # 稍微增加高度
        self.downloadable_models_tree.setAlternatingRowColors(True)
        self.downloadable_models_tree.setStyleSheet("""
            QTreeWidget {
                border: 2px solid #e1e1e1;
                border-radius: 6px;
                background-color: white;
                alternate-background-color: #f8f9fa;
                font-size: 13px;
                color: #495057;
                gridline-color: #f1f3f4;
            }
            QTreeWidget::item {
                padding: 6px;
                border-bottom: 1px solid #f1f3f4;
            }
            QTreeWidget::item:selected {
                background-color: #0078d4;
                color: white;
                border-radius: 4px;
            }
            QTreeWidget::item:hover {
                background-color: #e3f2fd;
                border-radius: 4px;
            }
            QHeaderView::section {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                padding: 6px;
                font-weight: bold;
                color: #495057;
                font-size: 13px;
            }
        """)
        left_layout.addWidget(self.downloadable_models_tree)
        
        online_btn_layout = QHBoxLayout()
        online_btn_layout.setSpacing(8)
        
        download_btn = QPushButton(self.get_text("download_model", "ui"))
        download_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #28a745, stop:1 #1e7e34);
                color: white;
                border: none;
                padding: 6px 16px;
                border-radius: 4px;
                font-weight: 600;
                font-size: 13px;
                min-width: 80px;
                min-height: 32px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #34ce57, stop:1 #28a745);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #1e7e34, stop:1 #155724);
            }
        """)
        download_btn.clicked.connect(self.download_model)
        online_btn_layout.addWidget(download_btn)
        
        
        left_layout.addLayout(online_btn_layout)
        splitter.addWidget(left_group)
        
        # 右侧 - 本地模型
        right_group = QGroupBox(self.get_text("local_models", "ui"))
        right_group.setStyleSheet("""
            QGroupBox {
                font-size: 14px;
                font-weight: bold;
                color: #28a745;
                border: 2px solid #28a745;
                border-radius: 8px;
                margin-top: 12px;
                padding-top: 12px;
                background-color: #f8fff8;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 8px 0 8px;
                color: #28a745;
                font-weight: bold;
            }
        """)
        right_layout = QVBoxLayout(right_group)
        right_layout.setSpacing(8)
        
        self.local_models_list = QListWidget()
        self.local_models_list.setMaximumHeight(220)  # 稍微增加高度
        self.local_models_list.setAlternatingRowColors(True)
        self.local_models_list.setStyleSheet("""
            QListWidget {
                border: 2px solid #e1e1e1;
                border-radius: 6px;
                background-color: white;
                alternate-background-color: #f8f9fa;
                font-size: 13px;
                color: #495057;
            }
            QListWidget::item {
                padding: 8px;
                border-bottom: 1px solid #f1f3f4;
                border-radius: 4px;
                margin: 2px;
            }
            QListWidget::item:selected {
                background-color: #28a745;
                color: white;
                border-radius: 4px;
            }
            QListWidget::item:hover {
                background-color: #d4edda;
                border-radius: 4px;
            }
        """)
        right_layout.addWidget(self.local_models_list)
        
        local_btn_layout = QHBoxLayout()
        local_btn_layout.setSpacing(8)
        
        delete_btn = QPushButton(self.get_text("delete_model", "ui"))
        delete_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #dc3545, stop:1 #c82333);
                color: white;
                border: none;
                padding: 6px 16px;
                border-radius: 4px;
                font-weight: 600;
                font-size: 13px;
                min-width: 80px;
                min-height: 32px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #e74c3c, stop:1 #dc3545);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #c82333, stop:1 #a71e2a);
            }
        """)
        delete_btn.clicked.connect(self.delete_model)
        local_btn_layout.addWidget(delete_btn)
        
        
        right_layout.addLayout(local_btn_layout)
        splitter.addWidget(right_group)
        
        # 进度条区域 - 美化显示
        progress_frame = QFrame()
        progress_frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 2px solid #dee2e6;
                border-radius: 8px;
                padding: 8px;
            }
        """)
        progress_layout = QVBoxLayout(progress_frame)
        progress_layout.setSpacing(6)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximumHeight(24)  # 稍微增加高度
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid #e1e1e1;
                border-radius: 12px;
                text-align: center;
                background-color: #f8f9fa;
                color: #495057;
                font-weight: bold;
                font-size: 12px;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #0078d4, stop:1 #00bcf2);
                border-radius: 10px;
            }
        """)
        progress_layout.addWidget(self.progress_bar)
        
        self.progress_label = QLabel("")
        self.progress_label.setAlignment(Qt.AlignCenter)
        self.progress_label.setStyleSheet("""
            QLabel {
                color: #495057;
                font-weight: 600;
                font-size: 14px;
                padding: 4px;
            }
        """)
        progress_layout.addWidget(self.progress_label)
        
        layout.addWidget(progress_frame)
    
    def setup_autostart_tab(self):
        """设置开机启动标签页"""
        autostart_widget = QWidget()
        self.tab_widget.addTab(autostart_widget, self.get_text("tab_autostart", "ui"))
        
        layout = QVBoxLayout(autostart_widget)
        layout.setSpacing(8)  # 减少间距
        
        # 开机启动设置
        autostart_group = QGroupBox(self.get_text("autostart_title", "ui"))
        autostart_layout = QVBoxLayout(autostart_group)
        autostart_layout.setSpacing(6)  # 减少间距
        
        self.autostart_checkbox = QCheckBox(self.get_text("autostart_checkbox", "ui"))
        self.autostart_checkbox.toggled.connect(self.toggle_autostart)
        autostart_layout.addWidget(self.autostart_checkbox)
        
        self.autostart_status = QLabel("状态: 未知")
        autostart_layout.addWidget(self.autostart_status)
        
        # 服务控制按钮 - 紧凑布局
        service_layout = QHBoxLayout()
        
        start_btn = QPushButton(self.get_text("start_service", "ui"))
        start_btn.clicked.connect(self.start_ollama_service)
        service_layout.addWidget(start_btn)
        
        stop_btn = QPushButton(self.get_text("stop_service", "ui"))
        stop_btn.clicked.connect(self.stop_ollama_service)
        service_layout.addWidget(stop_btn)
        
        check_btn = QPushButton(self.get_text("check_status", "ui"))
        check_btn.clicked.connect(self.check_ollama_status)
        service_layout.addWidget(check_btn)
        
        autostart_layout.addLayout(service_layout)
        layout.addWidget(autostart_group)
        
        # 路径信息 - 紧凑显示
        path_group = QGroupBox(self.get_text("path_info", "ui"))
        path_layout = QFormLayout(path_group)
        path_layout.setSpacing(4)  # 减少间距
        
        ollama_path_text = str(self.ollama_path) if self.ollama_path else self.get_text("ollama_not_found", "status")
        path_layout.addRow(self.get_text("ollama_path", "ui"), QLabel(ollama_path_text))
        
        models_path = str(Path.home() / ".ollama" / "models")
        path_layout.addRow(self.get_text("models_path", "ui"), QLabel(models_path))
        
        layout.addWidget(path_group)
        layout.addStretch()
    
    def setup_env_tab(self):
        """设置环境变量标签页"""
        env_widget = QWidget()
        self.tab_widget.addTab(env_widget, self.get_text("tab_environment", "ui"))
        
        # 创建滚动区域
        scroll = QScrollArea()
        scroll_widget = QWidget()
        scroll.setWidget(scroll_widget)
        scroll.setWidgetResizable(True)
        
        layout = QVBoxLayout(env_widget)
        layout.addWidget(scroll)
        
        scroll_layout = QVBoxLayout(scroll_widget)
        scroll_layout.setSpacing(6)  # 减少间距
        
        # 环境变量设置
        env_group = QGroupBox(self.get_text("env_variables", "ui"))
        env_layout = QFormLayout(env_group)
        env_layout.setSpacing(4)  # 减少间距
        
        # OLLAMA_HOST
        self.host_input = QLineEdit(self.ollama_host)
        env_layout.addRow(self.get_text("host_label", "ui"), self.host_input)
        
        # OLLAMA_PORT
        self.port_input = QLineEdit(self.ollama_port)
        env_layout.addRow(self.get_text("port_label", "ui"), self.port_input)
        
        # OLLAMA_MODELS
        models_layout = QHBoxLayout()
        self.models_input = QLineEdit(self.ollama_models)
        models_layout.addWidget(self.models_input)
        
        browse_btn = QPushButton(self.get_text("browse"))
        browse_btn.clicked.connect(self.browse_folder)
        models_layout.addWidget(browse_btn)
        
        env_layout.addRow(self.get_text("models_label", "ui"), models_layout)
        
        # OLLAMA_KEEP_ALIVE
        self.keep_alive_input = QLineEdit(self.ollama_keep_alive)
        env_layout.addRow("OLLAMA_KEEP_ALIVE:", self.keep_alive_input)
        
        scroll_layout.addWidget(env_group)
        
        # 控制按钮 - 紧凑布局
        button_layout = QHBoxLayout()
        
        reset_btn = QPushButton(self.get_text("reset_defaults"))
        reset_btn.clicked.connect(self.reset_env_vars)
        button_layout.addWidget(reset_btn)
        
        test_btn = QPushButton(self.get_text("test_connection"))
        test_btn.clicked.connect(self.test_connection)
        button_layout.addWidget(test_btn)
        
        button_layout.addStretch()
        scroll_layout.addLayout(button_layout)
        
        # 当前环境信息 - 紧凑显示
        info_group = QGroupBox(self.get_text("current_env_info", "ui"))
        info_layout = QVBoxLayout(info_group)
        info_layout.setSpacing(4)  # 减少间距
        
        self.env_info_text = QTextEdit()
        self.env_info_text.setMaximumHeight(100)  # 限制高度
        self.env_info_text.setReadOnly(True)
        info_layout.addWidget(self.env_info_text)
        
        scroll_layout.addWidget(info_group)
        scroll_layout.addStretch()
        
        self.update_env_info()
    
    def load_settings(self):
        """加载设置"""
        self.auto_start = self.config.get("auto_start", False)
        self.current_model = self.config.get("selected_model", "")
        
        self.ollama_host = os.environ.get('OLLAMA_HOST', self.config.get("ollama_host", "localhost"))
        self.ollama_port = os.environ.get('OLLAMA_PORT', self.config.get("ollama_port", "11434"))
        self.ollama_models = os.environ.get('OLLAMA_MODELS', self.config.get("ollama_models", ""))
        self.ollama_keep_alive = os.environ.get('OLLAMA_KEEP_ALIVE', self.config.get("ollama_keep_alive", "5m"))
        
        # 更新UI
        self.autostart_checkbox.setChecked(self.auto_start)
        self.host_input.setText(self.ollama_host)
        self.port_input.setText(self.ollama_port)
        self.models_input.setText(self.ollama_models)
        self.keep_alive_input.setText(self.ollama_keep_alive)
        
        self.update_autostart_status()
    
    def refresh_models(self):
        """从ollama list获取真实的本地模型列表"""
        self.local_models_list.clear()
        models = []
        
        try:
            if self.check_ollama_status():
                url = f"http://{self.ollama_host}:{self.ollama_port}/api/tags"
                response = requests.get(url, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    models = [model['name'] for model in data.get('models', [])]
        except Exception as e:
            self.update_status(f"获取本地模型列表失败: {e}")
        
        # 更新本地模型列表
        for model in models:
            self.local_models_list.addItem(model)
        
        # 更新聊天界面的模型下拉框（来自本地模型）
        self.model_combo.clear()
        self.model_combo.addItems(models)
        if models and not self.current_model:
            self.current_model = models[0]
            self.model_combo.setCurrentText(self.current_model)
        
        if models:
            self.update_status(f"已加载 {len(models)} 个本地模型")
        else:
            self.update_status("未找到本地模型，请先下载模型")
    
    def check_and_prompt_for_models(self):
        """检查本地模型列表，如果为空则提示用户下载"""
        try:
            # 获取当前本地模型数量
            model_count = self.local_models_list.count()
            
            if model_count == 0:
                # 检查Ollama服务是否运行
                if not self.check_ollama_status():
                    return  # 如果服务未运行，不提示下载
                
                # 显示下载提示对话框
                msg_box = QMessageBox(self)
                msg_box.setWindowTitle(self.get_text("no_models_title", "dialogs"))
                msg_box.setText(self.get_text("no_models_message", "dialogs"))
                msg_box.setIcon(QMessageBox.Question)
                
                # 添加自定义按钮
                download_btn = msg_box.addButton(self.get_text("download_now", "dialogs"), QMessageBox.YesRole)
                later_btn = msg_box.addButton(self.get_text("download_later", "dialogs"), QMessageBox.NoRole)
                
                msg_box.setDefaultButton(download_btn)
                msg_box.exec_()
                
                # 检查用户选择
                if msg_box.clickedButton() == download_btn:
                    self.auto_download_qwen_model()
                    
        except Exception as e:
            print(f"检查模型时出错: {e}")
    
    def auto_download_qwen_model(self):
        """自动下载qwen3:0.6b模型或运行安装脚本"""
        try:
            # 首先检查是否存在安装脚本
            if self.check_and_run_install_scripts():
                # 如果运行了安装脚本，则功能结束
                return
            
            # 如果没有安装脚本或脚本不适合当前系统，则切换到模型管理页面下载
            self.download_qwen_from_model_tab()
                    
        except Exception as e:
            print(f"自动下载模型时出错: {e}")
            QMessageBox.warning(
                self, 
                self.get_text("warning", "dialogs"),
                f"自动下载失败: {e}\n请手动选择模型下载。"
            )
    
    def check_and_run_install_scripts(self):
        """检查并运行安装脚本，返回是否成功运行了脚本"""
        import platform
        current_os = platform.system().lower()
        
        # 定义可能的安装脚本文件
        install_files = [
            "InstOlla.exe",
            "InstallOllama.bat", 
            "InstallOllama.sh"
        ]
        
        # 检查文件是否存在
        existing_files = []
        for file_name in install_files:
            file_path = Path(file_name)
            if file_path.exists():
                existing_files.append((file_name, file_path))
        
        if not existing_files:
            print("未找到安装脚本文件")
            return False
        
        # 根据系统类型选择合适的脚本运行
        script_to_run = None
        
        if current_os == "windows":
            # Windows系统：优先选择.exe，然后是.bat
            for file_name, file_path in existing_files:
                if file_name.endswith('.exe'):
                    script_to_run = (file_name, file_path)
                    break
            
            if not script_to_run:
                for file_name, file_path in existing_files:
                    if file_name.endswith('.bat'):
                        script_to_run = (file_name, file_path)
                        break
        
        elif current_os in ["darwin", "linux"]:  # macOS or Linux
            # macOS/Linux系统：选择.sh脚本
            for file_name, file_path in existing_files:
                if file_name.endswith('.sh'):
                    script_to_run = (file_name, file_path)
                    break
        
        if not script_to_run:
            print(f"未找到适合当前系统({current_os})的安装脚本")
            return False
        
        # 运行选中的脚本
        try:
            script_name, script_path = script_to_run
            print(f"正在运行安装脚本: {script_name}")
            
            if current_os == "windows":
                if script_name.endswith('.exe'):
                    # 运行exe文件
                    subprocess.Popen([str(script_path)], 
                                   creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0)
                elif script_name.endswith('.bat'):
                    # 运行bat文件
                    subprocess.Popen([str(script_path)], 
                                   shell=True,
                                   creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0)
            else:
                # macOS/Linux运行sh脚本
                # 确保脚本有执行权限
                import stat
                script_path.chmod(script_path.stat().st_mode | stat.S_IEXEC)
                subprocess.Popen(['/bin/bash', str(script_path)])
            
            self.update_status(f"已启动安装脚本: {script_name}")
            QMessageBox.information(
                self,
                self.get_text("info", "dialogs"),
                f"已启动安装脚本: {script_name}\n安装过程将在后台运行。"
            )
            return True
            
        except Exception as e:
            print(f"运行安装脚本失败: {e}")
            QMessageBox.warning(
                self,
                self.get_text("warning", "dialogs"),
                f"运行安装脚本失败: {e}\n将切换到模型管理页面手动下载。"
            )
            return False
    
    def download_qwen_from_model_tab(self):
        """从模型管理标签页下载qwen3:1.7b模型"""
        try:
            # 切换到模型管理标签页
            self.tab_widget.setCurrentIndex(1)  # 模型管理是第二个标签页(索引1)
            
            # 在可下载模型列表中查找并选择qwen3:1.7b
            target_model = "qwen3:1.7b"
            
            for i in range(self.downloadable_models_tree.topLevelItemCount()):
                item = self.downloadable_models_tree.topLevelItem(i)
                if item.text(0) == target_model:
                    # 选择该项
                    self.downloadable_models_tree.setCurrentItem(item)
                    item.setSelected(True)
                    
                    # 开始下载
                    self.download_model()
                    break
            else:
                # 如果没找到qwen3:1.7b，提示用户手动选择
                QMessageBox.information(
                    self, 
                    self.get_text("info", "dialogs"),
                    "未找到qwen3:1.7b模型，请手动选择其他模型下载。"
                )
                    
        except Exception as e:
            print(f"从模型管理页面下载模型时出错: {e}")
            raise e
    
    def load_downloadable_models(self):
        """从JSON文件加载可下载模型数据"""
        try:
            # 从JSON文件读取模型数据
            models_file = Path("models_data.json")
            if models_file.exists():
                with open(models_file, 'r', encoding='utf-8') as f:
                    models_data = json.load(f)
                online_models = models_data.get('models', [])
            else:
                # 如果JSON文件不存在，使用内置的固定数据
                online_models = [
                    *self.get_text("default_models", "models")
                ]
        except Exception as e:
            print(f"读取可下载模型数据失败: {e}")
            # 使用内置的固定数据作为回退
            online_models = [
                {"name": "qwen3:0.6b", "size": "0.5GB", "description": "Qwen3 0.6B"},
                {"name": "qwen3:1.7b", "size": "1.4GB", "description": "Qwen3 1.7B"},
                {"name": "gemma3:4b", "size": "3.3GB", "description": "Gemma3 4B"},
                {"name": "qwen3:4b", "size": "2.5GB", "description": "Qwen3 4B"},
                {"name": "gemma3:12b", "size": "8.1GB", "description": "Gemma3 12B"},
                {"name": "qwen3:14b", "size": "9.3GB", "description": "Qwen3 14B"},
                {"name": "gpt-oss:20b", "size": "14GB", "description": "OpenAI GPT-oss"}
            ]
        
        # 清空现有项目
        if hasattr(self, 'downloadable_models_tree'):
            self.downloadable_models_tree.clear()
            
            # 添加新项目
            for model in online_models:
                item = QTreeWidgetItem([model["name"], model["size"], model["description"]])
                self.downloadable_models_tree.addTopLevelItem(item)
    
    def download_model(self):
        """下载选中的模型"""
        current_item = self.downloadable_models_tree.currentItem()
        if not current_item:
            QMessageBox.warning(self, self.get_text("warning", "dialogs"), self.get_text("select_model_warning", "dialogs"))
            return
        
        model_name = current_item.text(0)
        
        if not self.check_ollama_status():
            QMessageBox.critical(self, self.get_text("error", "dialogs"), self.get_text("service_not_running", "dialogs"))
            return
        
        if not self.ollama_path:
            QMessageBox.critical(self, self.get_text("error", "dialogs"), self.get_text("ollama_not_found", "dialogs"))
            return
        
        # 启动下载线程
        self.download_thread = DownloadThread(self.ollama_path, model_name)
        self.download_thread.progress_updated.connect(self.update_download_progress)
        self.download_thread.download_finished.connect(self.download_finished)
        self.download_thread.start()
        
        self.update_status(self.get_text("downloading_model", "status").format(model_name))
    
    def update_download_progress(self, progress, message):
        """更新下载进度"""
        self.progress_bar.setValue(progress)
        self.progress_label.setText(message)
    
    def download_finished(self, success, message):
        """下载完成"""
        self.update_status(message)
        if success:
            self.refresh_models()
        
        # 3秒后清除进度条
        QTimer.singleShot(3000, lambda: (
            self.progress_bar.setValue(0),
            self.progress_label.setText("")
        ))
    
    def delete_model(self):
        """删除选中的本地模型"""
        current_item = self.local_models_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "警告", "请选择要删除的模型")
            return
        
        model_name = current_item.text()
        
        reply = QMessageBox.question(self, "确认", f"确定要删除模型 {model_name} 吗？",
                                   QMessageBox.Yes | QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            try:
                if self.ollama_path:
                    subprocess.run([str(self.ollama_path), "rm", model_name], 
                                 check=True, creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0)
                    self.refresh_models()
                    self.update_status(f"模型 {model_name} 已删除")
                else:
                    QMessageBox.critical(self, "错误", "未找到 Ollama 可执行文件")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"删除模型失败: {e}")
    
    def send_message(self):
        """发送消息"""
        if not self.model_combo.currentText():
            QMessageBox.warning(self, "警告", "请选择一个模型")
            return
        
        message = self.message_input.toPlainText().strip()
        if not message:
            return
        
        if not self.check_ollama_status():
            QMessageBox.critical(self, "错误", "Ollama 服务未运行，请先启动服务")
            return
        
        # 保存当前用户消息
        self.current_user_message = message
        
        # 清空输入
        self.message_input.clear()
        
        # 添加用户消息
        self.add_chat_message(self.get_text("user", "chat"), message)
        
        # 启动聊天线程，传递聊天历史
        self.chat_thread = ChatThread(
            self.ollama_host, self.ollama_port, 
            self.model_combo.currentText(), message, self.chat_history
        )
        self.chat_thread.message_received.connect(self.on_message_received)
        self.chat_thread.error_occurred.connect(
            lambda error: self.add_chat_message("错误", error)
        )
        self.chat_thread.start()
        
        self.update_status("正在生成回复...")
    
    def on_message_received(self, reply):
        """处理接收到的消息"""
        print(f"[DEBUG] 收到LLM回复，长度: {len(reply)} 字符")
        print(f"[DEBUG] 回复内容预览: {reply[:100]}...")
        
        # 暂存回复，先进行审查
        self.pending_reply = reply
        
        # 启动答案审查（不显示初始回答）
        print(f"[DEBUG] 启动审查线程，问题: {self.current_user_message}")
        self.update_status("正在审查回答质量...")
        self.review_thread = AnswerReviewThread(
            self.ollama_host, self.ollama_port,
            self.model_combo.currentText(),
            self.current_user_message, reply
        )
        self.review_thread.review_completed.connect(self.on_review_completed)
        self.review_thread.error_occurred.connect(
            lambda error: self.add_chat_message("审查错误", error)
        )
        self.review_thread.start()
    
    def on_review_completed(self, needs_search, confidence_score, review_result):
        """处理审查完成"""
        print(f"[DEBUG] 审查完成 - 需要搜索: {needs_search}, 可信度: {confidence_score}")
        print(f"[DEBUG] 审查结果: {review_result[:100]}...")
        
        if needs_search or confidence_score <= 70:
            # 可信度<=70%，先检查搜索引擎连通性
            self.update_status("检查网络连接...")
            
            if self.check_search_engine_connectivity():
                # 搜索引擎正常，启动网络搜索（不显示"正在联网查询"提示）
                self.update_status("正在联网搜索...")
                self.search_thread = WebSearchThread(self.current_user_message, self.hidden_webview)
                self.search_thread.search_completed.connect(self.on_search_completed)
                self.search_thread.error_occurred.connect(
                    lambda error: self.add_chat_message("搜索错误", error)
                )
                self.search_thread.start()
            else:
                # 搜索引擎不可用，直接显示LLM的回复
                self.add_chat_message("AI 系统", "网络连接不可用，显示离线回答")
                enhanced_reply = f"{self.pending_reply} <small style='color: #666; font-size: 11px;'>(离线回答，可信度: {confidence_score:.1f}%)</small>"
                self.add_chat_message(self.get_text("assistant", "chat"), enhanced_reply)
                self.update_status("就绪")
        else:
            # 可信度>70%，显示原始回答，并在回答后附加可信度信息
            enhanced_reply = f"{self.pending_reply} <small style='color: #666; font-size: 11px;'>(可信度: {confidence_score:.1f}%)</small>"
            self.add_chat_message(self.get_text("assistant", "chat"), enhanced_reply)
            self.update_status("就绪")
    
    def on_search_completed(self, search_results):
        """处理搜索完成"""
        if search_results:
            # 使用搜索结果生成增强答案
            self.update_status("正在基于搜索结果生成更准确的回答...")
            self.enhanced_answer_thread = EnhancedAnswerThread(
                self.ollama_host, self.ollama_port,
                self.model_combo.currentText(),
                self.current_user_message, search_results, self.chat_history
            )
            self.enhanced_answer_thread.answer_generated.connect(self.on_enhanced_answer_generated)
            self.enhanced_answer_thread.error_occurred.connect(
                lambda error: self.add_chat_message("增强回答错误", error)
            )
            self.enhanced_answer_thread.start()
        else:
            self.add_chat_message("AI 系统", "搜索未找到相关结果")
            self.update_status("就绪")
    
    def on_enhanced_answer_generated(self, enhanced_answer):
        """处理增强答案生成完成"""
        self.add_chat_message("AI 助手(联网增强)", enhanced_answer)
        self.update_status("就绪")
    
    def filter_llm_response(self, message):
        """过滤LLM回复中的多余内容"""
        try:
            # 如果不是助手回复，直接返回原消息
            if not message:
                return message
            
            # 过滤模式列表
            filter_patterns = [
                # 思考过程标记
                r'<think>.*?</think>',
                r'\*thinks?\*.*?\*thinks?\*',
                r'\[thinking\].*?\[/thinking\]',
                r'思考：.*?(?=\n|$)',
                r'让我想想.*?(?=\n|$)',
                
                # 图片相关
                r'!\[.*?\]\(.*?\)',  # Markdown图片
                r'<img.*?>',         # HTML图片标签
                r'图片：.*?(?=\n|$)',
                r'image:.*?(?=\n|$)',
                
                # 多余的标记
                r'<.*?>', # 其他HTML标签
                r'\*\*思考\*\*.*?(?=\n|$)',
                r'```thinking.*?```',
                
                # 多余的元信息
                r'作为.*?AI.*?，',
                r'根据我的.*?训练.*?，',
                r'我是.*?语言模型.*?，',
                
                # 重复的标点符号
                r'[。！？]{3,}',
                r'[.!?]{3,}',
                
                # 多余的换行
                r'\n{3,}',
            ]
            
            import re
            filtered_message = message
            
            # 应用过滤规则
            for pattern in filter_patterns:
                filtered_message = re.sub(pattern, '', filtered_message, flags=re.DOTALL | re.IGNORECASE)
            
            # 清理多余的空白字符
            filtered_message = re.sub(r'[ \t]+', ' ', filtered_message)  # 多个空格/制表符变成一个空格
            filtered_message = re.sub(r'\n\s*\n\s*\n+', '\n\n', filtered_message)  # 多个换行变成两个
            filtered_message = re.sub(r'^\s+|\s+$', '', filtered_message)  # 去除首尾空白
            
            return filtered_message if filtered_message else message
            
        except Exception as e:
            print(f"过滤LLM回复时出错: {e}")
            return message
    
    def add_chat_message(self, sender, message):
        """添加聊天消息 - 支持WebView和QTextEdit两种模式"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # 如果是助手回复，先过滤多余内容
        if sender in ["AI 助手", "AI 助手(联网增强)", self.get_text("assistant", "chat")]:
            message = self.filter_llm_response(message)
        
        # 检查是否使用WebView
        if WEBENGINE_AVAILABLE and hasattr(self.chat_display, 'setHtml'):
            self.add_webview_message(sender, message, timestamp)
        else:
            self.add_textedit_message(sender, message, timestamp)
    
    def add_webview_message(self, sender, message, timestamp):
        """添加消息到WebView"""
        try:
            # 转义HTML特殊字符
            escaped_message = message.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            
            # 将URL转换为可点击的链接
            escaped_message = self.convert_urls_to_links(escaped_message)
            
            # 确定消息类型和样式
            if sender == self.get_text("user", "chat") or sender == "我":
                message_class = "user-message"
                bubble_class = "user-bubble"
            elif sender in ["AI 系统", "system"]:
                message_class = "system-message"
                bubble_class = "system-bubble"
            else:
                message_class = "assistant-message"
                bubble_class = "assistant-bubble"
            
            # 构建消息HTML
            message_html = f"""
            <div class="message {message_class}">
                <div class="{bubble_class}">
                    <div class="timestamp">[{timestamp}] {sender}</div>
                    <div class="message-content">{escaped_message}</div>
                </div>
            </div>
            """
            
            # 使用JavaScript添加消息，增加强化的DOM检查和重试机制
            js_code = f"""
            (function() {{
                function addMessage(retryCount) {{
                    retryCount = retryCount || 0;
                    var messagesDiv = document.getElementById('messages');
                    
                    if (!messagesDiv) {{
                        if (retryCount < 10) {{
                            console.log('messages元素不存在，重试中... (' + (retryCount + 1) + '/10)');
                            setTimeout(function() {{ addMessage(retryCount + 1); }}, 100);
                            return;
                        }} else {{
                            console.error('messages元素不存在，HTML可能未完全加载，已重试10次');
                            return;
                        }}
                    }}
                    
                    var newMessage = document.createElement('div');
                    newMessage.innerHTML = `{message_html}`;
                    if (newMessage.firstElementChild) {{
                        messagesDiv.appendChild(newMessage.firstElementChild);
                        window.scrollTo(0, document.body.scrollHeight);
                        console.log('消息添加成功');
                    }} else {{
                        console.error('无法创建消息元素');
                    }}
                }}
                
                // 检查DOM是否准备就绪
                if (document.readyState === 'complete') {{
                    addMessage();
                }} else {{
                    document.addEventListener('DOMContentLoaded', function() {{
                        addMessage();
                    }});
                    // 备用方案：延迟执行
                    setTimeout(function() {{ addMessage(); }}, 200);
                }}
            }})();
            """
            
            # 延迟执行JavaScript，确保DOM完全加载
            def run_js():
                try:
                    self.chat_display.page().runJavaScript(js_code)
                except Exception as e:
                    print(f"执行JavaScript时出错: {e}")
            
            # 使用QTimer延迟200ms执行，给HTML更多加载时间
            from PyQt5.QtCore import QTimer
            QTimer.singleShot(200, run_js)
            
        except Exception as e:
            print(f"WebView添加消息时出错: {e}")
            # 回退到QTextBrowser模式
            self.add_textedit_message(sender, message, timestamp)
    
    def add_textedit_message(self, sender, message, timestamp):
        """添加消息到QTextBrowser（回退模式）"""
        try:
            # 调试信息：打印sender的值
            print(f"DEBUG: sender='{sender}', get_text('user', 'chat')='{self.get_text('user', 'chat')}'")
            print(f"DEBUG: 是否匹配用户条件: {sender == self.get_text('user', 'chat') or sender == '用户' or sender == '我'}")
            # 转义HTML特殊字符，保持换行
            escaped_message = message.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            # 将换行符转换为HTML换行，但保持段落结构
            escaped_message = escaped_message.replace('\n\n', '</p><p>').replace('\n', '<br>')
            escaped_message = f'<p>{escaped_message}</p>' if escaped_message.strip() else ''
            
            # 将URL转换为可点击的链接
            escaped_message = self.convert_urls_to_links(escaped_message)
            
            # 根据发送者设置样式
            if sender == self.get_text("user", "chat") or sender == "用户" or sender == "我":
                # 用户消息右对齐，使用蓝色主题
                print(f"DEBUG: 匹配用户消息，sender='{sender}'")
                formatted_message = f"""
                <table width="100%" style="margin: 12px 0; border-collapse: collapse;">
                    <tr>
                        <td style="text-align: right; padding: 0;">
                            <div style="display: inline-block; max-width: 300px; background-color: #2196F3; color: #FFFFFF; padding: 10px 15px; border-radius: 18px 18px 5px 18px; box-shadow: 0 2px 10px rgba(33,150,243,0.3); text-align: left; word-wrap: break-word; font-family: 'Microsoft YaHei', sans-serif;">
                                <div style="font-size: 10px; color: #FFFFFF; margin-bottom: 6px; font-weight: 500;">[{timestamp}] {sender}</div>
                                <div style="font-size: 14px; line-height: 1.5; word-break: break-word; color: #FFFFFF;">{escaped_message}</div>
                            </div>
                        </td>
                    </tr>
                </table>
                """
            elif sender in ["AI 系统", "system", "系统"]:
                # 系统消息，居中显示
                formatted_message = f"""
                <div style="text-align: center; margin: 12px 0; clear: both;">
                    <div style="display: inline-block; max-width: 80%; background: linear-gradient(135deg, #FFF8E1, #FFF3C4); color: #F57F17; padding: 8px 12px; border-radius: 15px; border: 1px solid #FFE082; text-align: center; font-family: 'Microsoft YaHei', sans-serif; font-size: 12px;">
                        <div style="font-weight: 500;">[{timestamp}] {sender}</div>
                        <div style="margin-top: 4px; line-height: 1.4;">{escaped_message}</div>
                    </div>
                </div>
                <div style="height: 8px; clear: both;"></div>
                """
            else:
                # 助手消息左对齐，使用灰色主题
                print(f"DEBUG: 匹配AI消息，sender='{sender}'")
                formatted_message = f"""
                <table width="100%" style="margin: 12px 0; border-collapse: collapse;">
                    <tr>
                        <td style="text-align: left; padding: 0;">
                            <div style="display: inline-block; max-width: 300px; background-color: #F5F5F5; color: #333333; padding: 10px 15px; border-radius: 18px 18px 18px 5px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); border: 1px solid #E0E0E0; text-align: left; word-wrap: break-word; font-family: 'Microsoft YaHei', sans-serif;">
                                <div style="font-size: 10px; color: #666666; margin-bottom: 6px; font-weight: 500;">[{timestamp}] {sender}</div>
                                <div style="font-size: 14px; line-height: 1.5; word-break: break-word; color: #333333;">{escaped_message}</div>
                            </div>
                        </td>
                    </tr>
                </table>
                """
            
            # 插入HTML
            cursor = self.chat_display.textCursor()
            cursor.movePosition(cursor.End)
            cursor.insertHtml(formatted_message)
            self.chat_display.setTextCursor(cursor)
            
            # 滚动到底部
            scrollbar = self.chat_display.verticalScrollBar()
            scrollbar.setValue(scrollbar.maximum())
            
        except Exception as e:
            print(f"QTextBrowser添加消息时出错: {e}")
            # 最后的回退：格式化纯文本模式
            simple_message = f"\n[{timestamp}] {sender}:\n{message}\n" + "="*50 + "\n"
            self.chat_display.append(simple_message)
        
        # 保存到历史记录
        self.chat_history.append({
            "timestamp": timestamp,
            "sender": sender,
            "message": message
        })
    
    def clear_chat(self):
        """清空聊天记录"""
        # 直接清空，不询问用户
        # 清空聊天历史
        self.chat_history.clear()
        
        # 根据聊天显示类型进行清空
        if WEBENGINE_AVAILABLE and hasattr(self.chat_display, 'setHtml'):
            # WebView模式：重新初始化HTML
            self.init_chat_html()
        else:
            # QTextBrowser模式：直接清空
            self.chat_display.clear()
        
        # 清空消息列表（用于WebView）
        if hasattr(self, 'chat_messages'):
            self.chat_messages.clear()
        
        # 清空完成后不显示任何消息
    
    def save_chat(self):
        """保存聊天记录"""
        if not self.chat_history:
            QMessageBox.warning(self, "警告", "没有聊天记录可保存")
            return
        
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"chat_history_{timestamp}.txt"
            
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(self.chat_display.toPlainText())
            
            self.update_status(f"聊天记录已保存到: {filename}")
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"保存失败: {e}")
    
    def toggle_autostart(self, checked):
        """切换开机启动"""
        try:
            key_path = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run"
            app_name = "OllamaService"
            
            if checked:
                if self.ollama_path:
                    startup_command = f'"{self.ollama_path.parent / "MiniOllama_PyQt5.exe"} -start'
                    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE) as key:
                        winreg.SetValueEx(key, app_name, 0, winreg.REG_SZ, startup_command)
                    self.update_status("已添加到开机启动")
                else:
                    QMessageBox.critical(self, "错误", "未找到 Ollama 可执行文件")
                    self.autostart_checkbox.setChecked(False)
                    return
            else:
                try:
                    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE) as key:
                        winreg.DeleteValue(key, app_name)
                    self.update_status("已从开机启动移除")
                except FileNotFoundError:
                    pass
            
            self.auto_start = checked
            self.update_autostart_status()
            self.save_config()
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"设置开机启动失败: {e}")
            self.autostart_checkbox.setChecked(not checked)
    
    def update_autostart_status(self):
        """更新开机启动状态"""
        try:
            key_path = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run"
            app_name = "OllamaService"
            
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_READ) as key:
                try:
                    value, _ = winreg.QueryValueEx(key, app_name)
                    self.autostart_status.setText("状态: 已启用开机启动")
                    self.autostart_status.setStyleSheet("color: green;")
                except FileNotFoundError:
                    self.autostart_status.setText("状态: 未启用开机启动")
                    self.autostart_status.setStyleSheet("color: red;")
        except Exception:
            self.autostart_status.setText("状态: 无法检查")
            self.autostart_status.setStyleSheet("color: orange;")
    
    def start_ollama_service(self):
        """启动Ollama服务"""
        if not self.ollama_path:
            QMessageBox.critical(self, "错误", "未找到 Ollama 可执行文件")
            return
        
        try:
            if sys.platform == "win32":
                CREATE_NO_WINDOW = 0x08000000
                DETACHED_PROCESS = 0x00000008
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                startupinfo.wShowWindow = 0
                
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
            
            self.update_status("正在启动 Ollama 服务...")
            QTimer.singleShot(2000, self.check_ollama_status)
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"启动 Ollama 服务失败: {e}")
    
    def stop_ollama_service(self):
        """停止Ollama服务"""
        try:
            if sys.platform == "win32":
                subprocess.run(["taskkill", "/f", "/im", "ollama.exe"], 
                             creationflags=subprocess.CREATE_NO_WINDOW)
            else:
                subprocess.run(["pkill", "ollama"])
            
            self.update_status("Ollama 服务已停止")
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"停止 Ollama 服务失败: {e}")
    
    def check_ollama_status(self):
        """检查Ollama服务状态"""
        try:
            url = f"http://{self.ollama_host}:{self.ollama_port}/api/tags"
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                self.update_status("Ollama 服务运行正常")
                return True
            else:
                self.update_status("Ollama 服务未运行")
                return False
        except Exception:
            self.update_status("Ollama 服务未运行")
            return False
    
    def browse_folder(self):
        """浏览文件夹"""
        folder = QFileDialog.getExistingDirectory(self, "选择文件夹")
        if folder:
            self.models_input.setText(folder)
    
    def reset_env_vars(self):
        """重置环境变量为默认值"""
        self.host_input.setText("localhost")
        self.port_input.setText("11434")
        self.models_input.setText("")
        self.keep_alive_input.setText("5m")
        self.update_status("环境变量已重置为默认值")
    
    def test_connection(self):
        """测试连接"""
        try:
            host = self.host_input.text()
            port = self.port_input.text()
            url = f"http://{host}:{port}/api/tags"
            
            self.update_status("正在测试连接...")
            response = requests.get(url, timeout=5)
            
            if response.status_code == 200:
                self.update_status("连接成功")
                QMessageBox.information(self, "成功", f"成功连接到 Ollama 服务器\n地址: {host}:{port}")
            else:
                self.update_status("连接失败")
                QMessageBox.critical(self, "错误", f"连接失败，状态码: {response.status_code}")
                
        except Exception as e:
            self.update_status("连接失败")
            QMessageBox.critical(self, "错误", f"连接测试失败: {e}")
    
    def update_env_info(self):
        """更新环境信息显示"""
        env_info = f"当前环境变量:\n"
        env_info += f"OLLAMA_HOST = {os.environ.get('OLLAMA_HOST', '未设置')}\n"
        env_info += f"OLLAMA_PORT = {os.environ.get('OLLAMA_PORT', '未设置')}\n"
        env_info += f"OLLAMA_MODELS = {os.environ.get('OLLAMA_MODELS', '未设置')}\n"
        env_info += f"OLLAMA_KEEP_ALIVE = {os.environ.get('OLLAMA_KEEP_ALIVE', '未设置')}\n"
        env_info += f"\n服务器地址: {self.host_input.text()}:{self.port_input.text()}"
        
        self.env_info_text.setPlainText(env_info)
    
    def save_settings(self):
        """保存所有设置"""
        try:
            # 应用环境变量
            self.apply_env_vars()
            
            # 保存配置
            self.config["auto_start"] = self.auto_start
            self.config["selected_model"] = self.model_combo.currentText()
            self.config["ollama_host"] = self.host_input.text()
            self.config["ollama_port"] = self.port_input.text()
            self.config["ollama_models"] = self.models_input.text()
            self.config["ollama_keep_alive"] = self.keep_alive_input.text()
            
            self.save_config()
            
            QMessageBox.information(self, "成功", "设置已保存")
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"保存失败: {e}")
    
    def apply_env_vars(self):
        """应用环境变量"""
        # OLLAMA_HOST
        host_value = self.host_input.text().strip()
        if host_value:
            os.environ['OLLAMA_HOST'] = host_value
            self.ollama_host = host_value
        else:
            os.environ.pop('OLLAMA_HOST', None)
        
        # OLLAMA_PORT
        port_value = self.port_input.text().strip()
        if port_value:
            os.environ['OLLAMA_PORT'] = port_value
            self.ollama_port = port_value
        else:
            os.environ.pop('OLLAMA_PORT', None)
        
        # OLLAMA_MODELS
        models_value = self.models_input.text().strip()
        if models_value:
            os.environ['OLLAMA_MODELS'] = models_value
            self.ollama_models = models_value
        else:
            os.environ.pop('OLLAMA_MODELS', None)
        
        # OLLAMA_KEEP_ALIVE
        keep_alive_value = self.keep_alive_input.text().strip()
        if keep_alive_value:
            os.environ['OLLAMA_KEEP_ALIVE'] = keep_alive_value
            self.ollama_keep_alive = keep_alive_value
        else:
            os.environ.pop('OLLAMA_KEEP_ALIVE', None)
        
        self.update_env_info()
    
    def update_status(self, message):
        """更新状态栏"""
        self.status_label.setText(message)
    
    @staticmethod
    def start_ollama_hidden():
        """静默启动Ollama服务"""
        # 查找ollama路径
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
            
            if sys.platform == "win32":
                CREATE_NO_WINDOW = 0x08000000
                DETACHED_PROCESS = 0x00000008
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                startupinfo.wShowWindow = 0
                
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
            
            # 等待服务启动
            time.sleep(3)
            
            # 检查服务是否运行
            try:
                response = requests.get("http://localhost:11434/api/tags", timeout=5)
                if response.status_code == 200:
                    print("Ollama service is running and responding")
                    return True
                else:
                    print(f"Ollama service may not be ready (status: {response.status_code})")
                    return True
            except requests.exceptions.RequestException:
                print("Ollama service started but not yet responding to API calls")
                return True
            
        except Exception as e:
            print(f"Error starting Ollama service: {e}")
            return False


def execute_install_ollama():
    """执行Ollama安装脚本"""
    import platform
    
    # 检测系统类型
    system = platform.system().lower()
    
    # 根据系统类型确定安装文件名
    install_files = []
    if system == "windows":
        install_files = ["InstOlla.exe", "InstallOllama.bat"]
    elif system in ["linux", "darwin"]:  # darwin是macOS
        install_files = ["InstallOllama.sh"]
    else:
        print(f"不支持的系统类型: {system}")
        return False
    
    # 查找安装文件
    script_dir = os.path.dirname(os.path.abspath(__file__))
    found_file = None
    
    for filename in install_files:
        file_path = os.path.join(script_dir, filename)
        if os.path.exists(file_path):
            found_file = file_path
            break
    
    if not found_file:
        print(f"未找到适合当前系统({system})的安装文件: {install_files}")
        return False
    
    try:
        print(f"执行安装脚本: {found_file}")
        
        if system == "windows":
            if found_file.endswith(".exe"):
                # 执行.exe文件
                subprocess.Popen([found_file], shell=False)
            else:
                # 执行.bat文件
                subprocess.Popen([found_file], shell=True)
        else:
            # Linux/macOS执行.sh文件
            subprocess.Popen(["/bin/bash", found_file])
        
        print("安装脚本已启动，程序即将退出")
        return True
        
    except Exception as e:
        print(f"执行安装脚本时出错: {e}")
        return False


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='MiniAI - PyQt5 Version')
    parser.add_argument('-start', '--start', action='store_true', 
                       help='Start Ollama service in hidden mode and exit')
    parser.add_argument('--installollama', action='store_true',
                       help='Execute Ollama installation script and exit')
    
    args = parser.parse_args()
    
    if args.installollama:
        # 执行Ollama安装脚本
        success = execute_install_ollama()
        sys.exit(0 if success else 1)
    elif args.start:
        # 启动Ollama服务
        success = OllamaSettingsQt.start_ollama_hidden()
        sys.exit(0 if success else 1)
    else:
        # 运行GUI应用程序
        app = QApplication(sys.argv)
        app.setStyle('Fusion')  # 使用现代样式
        
        # 设置应用程序属性
        app.setApplicationName("MiniAI")
        app.setApplicationVersion(__version__)
        app.setOrganizationName("267278466@qq.com")
        
        window = OllamaSettingsQt()
        window.show()
        
        sys.exit(app.exec_())


if __name__ == "__main__":
    main()
