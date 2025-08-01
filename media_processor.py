# media_processor.py
import os
import requests
import logging
from typing import Optional
from config.config import config

logger = logging.getLogger(__name__)

class MediaProcessor:
    """多媒体处理器 - 处理语音转文字和文件内容提取"""
    
    def __init__(self):
        self.temp_dir = "temp_media"
        if not os.path.exists(self.temp_dir):
            os.makedirs(self.temp_dir)
    
    def download_media(self, media_id: str) -> Optional[str]:
        """
        通过MediaID下载媒体文件
        
        Args:
            media_id: 媒体文件ID
            
        Returns:
            str: 下载后的本地文件路径，失败返回None
        """
        try:
            from wework_client import wework_client
            
            # 获取access_token
            access_token = wework_client.get_access_token()
            
            # 下载媒体文件
            download_url = f"https://qyapi.weixin.qq.com/cgi-bin/media/get?access_token={access_token}&media_id={media_id}"
            
            response = requests.get(download_url, timeout=30)
            
            if response.status_code == 200:
                # 根据Content-Type确定文件扩展名
                content_type = response.headers.get('Content-Type', '')
                if 'audio' in content_type.lower():
                    ext = '.amr'  # 微信语音通常是amr格式
                elif 'image' in content_type.lower():
                    ext = '.jpg'
                elif 'application/pdf' in content_type.lower():
                    ext = '.pdf'
                elif 'application/msword' in content_type.lower():
                    ext = '.doc'
                elif 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' in content_type.lower():
                    ext = '.docx'
                elif 'application/vnd.ms-excel' in content_type.lower():
                    ext = '.xls'
                elif 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' in content_type.lower():
                    ext = '.xlsx'
                else:
                    ext = '.tmp'
                
                # 保存文件
                file_path = os.path.join(self.temp_dir, f"{media_id}{ext}")
                with open(file_path, 'wb') as f:
                    f.write(response.content)
                
                logger.info(f"媒体文件下载成功: {file_path}")
                return file_path
            else:
                logger.error(f"媒体文件下载失败: HTTP {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"下载媒体文件时发生错误: {e}")
            return None
    
    def speech_to_text(self, media_id: str) -> Optional[str]:
        """
        语音转文字
        
        Args:
            media_id: 语音文件的MediaID
            
        Returns:
            str: 识别出的文字内容，失败返回None
        """
        try:
            # 1. 下载语音文件
            voice_file = self.download_media(media_id)
            if not voice_file:
                logger.error("语音文件下载失败")
                return None
            
            # 2. 调用语音识别服务
            # TODO: 这里需要集成具体的语音识别服务
            # 可选方案：
            # - 阿里云语音识别
            # - 腾讯云语音识别  
            # - 百度语音识别
            # - OpenAI Whisper本地部署
            
            logger.info(f"开始语音识别: {voice_file}")
            
            # 示例：使用阿里云语音识别（需要配置相关API密钥）
            text_result = self._call_speech_recognition_api(voice_file)
            
            # 3. 清理临时文件
            try:
                os.remove(voice_file)
            except:
                pass
            
            return text_result
            
        except Exception as e:
            logger.error(f"语音转文字失败: {e}")
            return None
    
    def _call_speech_recognition_api(self, voice_file_path: str) -> Optional[str]:
        """
        调用语音识别API
        
        Args:
            voice_file_path: 语音文件路径
            
        Returns:
            str: 识别结果
        """
        # TODO: 实现具体的语音识别API调用
        # 这里返回一个示例结果，实际使用时需要替换为真实的API调用
        
        try:
            # 示例代码框架：
            # 1. 读取音频文件
            # 2. 调用语音识别API
            # 3. 解析返回结果
            
            logger.info("语音识别功能待实现，返回模拟结果")
            return "[语音转文字功能待实现]"
            
        except Exception as e:
            logger.error(f"语音识别API调用失败: {e}")
            return None
    
    def extract_file_content(self, media_id: str, filename: str) -> Optional[str]:
        """
        提取文件内容
        
        Args:
            media_id: 文件的MediaID
            filename: 文件名
            
        Returns:
            str: 文件文本内容，失败返回None
        """
        try:
            # 1. 下载文件
            file_path = self.download_media(media_id)
            if not file_path:
                logger.error("文件下载失败")
                return None
            
            # 2. 根据文件类型提取内容
            file_ext = filename.lower().split('.')[-1] if '.' in filename else ''
            
            content = None
            if file_ext == 'txt':
                content = self._extract_txt_content(file_path)
            elif file_ext in ['doc', 'docx']:
                content = self._extract_word_content(file_path)
            elif file_ext == 'pdf':
                content = self._extract_pdf_content(file_path)
            elif file_ext in ['xls', 'xlsx']:
                content = self._extract_excel_content(file_path)
            else:
                logger.warning(f"不支持的文件格式: {file_ext}")
            
            # 3. 清理临时文件
            try:
                os.remove(file_path)
            except:
                pass
            
            return content
            
        except Exception as e:
            logger.error(f"文件内容提取失败: {e}")
            return None
    
    def _extract_txt_content(self, file_path: str) -> Optional[str]:
        """提取TXT文件内容"""
        try:
            # 尝试多种编码
            encodings = ['utf-8', 'gbk', 'gb2312', 'utf-16']
            
            for encoding in encodings:
                try:
                    with open(file_path, 'r', encoding=encoding) as f:
                        content = f.read()
                    logger.info(f"TXT文件读取成功，使用编码: {encoding}")
                    return content
                except UnicodeDecodeError:
                    continue
            
            logger.error("TXT文件读取失败：无法确定文件编码")
            return None
            
        except Exception as e:
            logger.error(f"TXT文件处理失败: {e}")
            return None
    
    def _extract_word_content(self, file_path: str) -> Optional[str]:
        """提取Word文档内容"""
        try:
            # TODO: 需要安装python-docx库
            # pip install python-docx
            
            # from docx import Document
            # doc = Document(file_path)
            # text_content = []
            # for paragraph in doc.paragraphs:
            #     text_content.append(paragraph.text)
            # return '\n'.join(text_content)
            
            logger.info("Word文档解析功能待实现（需要安装python-docx）")
            return "[Word文档解析功能待实现]"
            
        except Exception as e:
            logger.error(f"Word文档处理失败: {e}")
            return None
    
    def _extract_pdf_content(self, file_path: str) -> Optional[str]:
        """提取PDF文档内容"""
        try:
            # TODO: 需要安装PyPDF2或pdfplumber库
            # pip install PyPDF2
            
            # import PyPDF2
            # with open(file_path, 'rb') as file:
            #     pdf_reader = PyPDF2.PdfReader(file)
            #     text_content = []
            #     for page in pdf_reader.pages:
            #         text_content.append(page.extract_text())
            #     return '\n'.join(text_content)
            
            logger.info("PDF文档解析功能待实现（需要安装PyPDF2或pdfplumber）")
            return "[PDF文档解析功能待实现]"
            
        except Exception as e:
            logger.error(f"PDF文档处理失败: {e}")
            return None
    
    def _extract_excel_content(self, file_path: str) -> Optional[str]:
        """提取Excel文档内容"""
        try:
            # TODO: 需要安装openpyxl或xlrd库
            # pip install openpyxl xlrd
            
            # import openpyxl
            # workbook = openpyxl.load_workbook(file_path)
            # text_content = []
            # for sheet_name in workbook.sheetnames:
            #     sheet = workbook[sheet_name]
            #     text_content.append(f"=== {sheet_name} ===")
            #     for row in sheet.iter_rows(values_only=True):
            #         row_text = '\t'.join([str(cell) if cell is not None else '' for cell in row])
            #         if row_text.strip():
            #             text_content.append(row_text)
            # return '\n'.join(text_content)
            
            logger.info("Excel文档解析功能待实现（需要安装openpyxl）")
            return "[Excel文档解析功能待实现]"
            
        except Exception as e:
            logger.error(f"Excel文档处理失败: {e}")
            return None

# 全局多媒体处理器实例
media_processor = MediaProcessor()