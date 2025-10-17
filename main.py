#!/usr/bin/env python3
"""
TS文件翻译工具 - 基于Argos Translate的本地翻译实现
替换Spark-Ts-Tools中的百度API翻译为本地离线翻译
"""

import os
import sys
import xml.etree.ElementTree as ET
import pandas as pd
from pathlib import Path
import logging
from typing import List, Dict, Optional
import argostranslate.package
import argostranslate.translate

class TsTranslator:
    """TS文件翻译器，使用Argos Translate进行本地翻译"""
    
    def __init__(self):
        self.logger = self._setup_logger()
        self.installed_packages = set()
        
    def _setup_logger(self):
        """设置日志记录器"""
        logger = logging.getLogger('TsTranslator')
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    def install_translation_package(self, from_lang: str, to_lang: str) -> bool:
        """安装翻译语言包"""
        try:
            self.logger.info(f"检查并安装翻译包: {from_lang} -> {to_lang}")
            
            # 更新包索引
            argostranslate.package.update_package_index()
            
            # 获取可用包
            available_packages = argostranslate.package.get_available_packages()
            
            # 查找匹配的包
            package_to_install = None
            for package in available_packages:
                if package.from_code == from_lang and package.to_code == to_lang:
                    package_to_install = package
                    break
            
            if package_to_install:
                self.logger.info(f"找到翻译包: {package_to_install}")
                argostranslate.package.install_from_path(package_to_install.download())
                self.installed_packages.add((from_lang, to_lang))
                self.logger.info(f"成功安装翻译包: {from_lang} -> {to_lang}")
                return True
            else:
                self.logger.warning(f"未找到直接翻译包 {from_lang} -> {to_lang}")
                # 尝试通过中间语言进行翻译
                return self._install_via_intermediate_language(from_lang, to_lang)
                
        except Exception as e:
            self.logger.error(f"安装翻译包失败: {e}")
            return False
    
    def _install_via_intermediate_language(self, from_lang: str, to_lang: str) -> bool:
        """通过中间语言安装翻译包"""
        # 常见的中间语言
        intermediate_langs = ['en']  # 英语作为中间语言
        
        for intermediate in intermediate_langs:
            try:
                # 安装 from_lang -> intermediate
                if self.install_direct_package(from_lang, intermediate):
                    # 安装 intermediate -> to_lang
                    if self.install_direct_package(intermediate, to_lang):
                        self.logger.info(f"通过中间语言 {intermediate} 建立了翻译路径: {from_lang} -> {to_lang}")
                        return True
            except Exception as e:
                self.logger.warning(f"通过中间语言 {intermediate} 安装失败: {e}")
        
        self.logger.error(f"无法找到从 {from_lang} 到 {to_lang} 的翻译路径")
        return False
    
    def install_direct_package(self, from_lang: str, to_lang: str) -> bool:
        """直接安装翻译包"""
        try:
            available_packages = argostranslate.package.get_available_packages()
            for package in available_packages:
                if package.from_code == from_lang and package.to_code == to_lang:
                    argostranslate.package.install_from_path(package.download())
                    self.installed_packages.add((from_lang, to_lang))
                    return True
            return False
        except Exception as e:
            self.logger.error(f"直接安装包失败 {from_lang} -> {to_lang}: {e}")
            return False
    
    def translate_text(self, text: str, from_lang: str, to_lang: str) -> str:
        """翻译单个文本"""
        try:
            if not text or not text.strip():
                return text
            
            # 检查是否已安装翻译包
            if (from_lang, to_lang) not in self.installed_packages:
                if not self.install_translation_package(from_lang, to_lang):
                    self.logger.warning(f"无法翻译: {from_lang} -> {to_lang}")
                    return text
            
            # 进行翻译
            translated = argostranslate.translate.translate(text, from_lang, to_lang)
            self.logger.debug(f"翻译: '{text}' -> '{translated}'")
            return translated
            
        except Exception as e:
            self.logger.error(f"翻译文本失败: {e}")
            return text
    
    def parse_ts_file(self, ts_file_path: str) -> List[Dict]:
        """解析TS文件，提取需要翻译的内容"""
        try:
            tree = ET.parse(ts_file_path)
            root = tree.getroot()
            
            translations = []
            for message in root.findall('.//message'):
                source = message.find('source')
                translation = message.find('translation')
                
                if source is not None and source.text:
                    trans_data = {
                        'source': source.text,
                        'translation': translation.text if translation is not None else '',
                        'type': translation.get('type') if translation is not None else ''
                    }
                    translations.append(trans_data)
            
            self.logger.info(f"从 {ts_file_path} 解析出 {len(translations)} 条翻译条目")
            return translations
            
        except Exception as e:
            self.logger.error(f"解析TS文件失败 {ts_file_path}: {e}")
            return []
    
    def detect_language_from_filename(self, filename: str) -> str:
        """从文件名检测语言"""
        filename_lower = filename.lower()
        
        # 常见的语言代码映射
        language_mapping = {
            'zh_cn': 'zh', 'zh-cn': 'zh', 'chinese': 'zh',
            'en': 'en', 'english': 'en',
            'ja': 'ja', 'japanese': 'ja',
            'ko': 'ko', 'korean': 'ko',
            'fr': 'fr', 'french': 'fr',
            'de': 'de', 'german': 'de',
            'es': 'es', 'spanish': 'es',
            'ru': 'ru', 'russian': 'ru',
            'pt': 'pt', 'portuguese': 'pt',
            'it': 'it', 'italian': 'it'
        }
        
        for key, lang_code in language_mapping.items():
            if key in filename_lower:
                return lang_code
        
        # 默认返回英语
        return 'en'
    
    def translate_ts_file(self, input_ts: str, output_ts: str, from_lang: str, to_lang: str, 
                         skip_translated: bool = True) -> dict:
        """翻译整个TS文件"""
        try:
            self.logger.info(f"开始翻译: {input_ts} -> {output_ts}")
            self.logger.info(f"翻译方向: {from_lang} -> {to_lang}")
            
            # 解析输入文件
            translations = self.parse_ts_file(input_ts)
            if not translations:
                self.logger.error("没有找到可翻译的内容")
                return {'success': False, 'error': '没有找到可翻译的内容'}
            
            # 安装翻译包
            if not self.install_translation_package(from_lang, to_lang):
                self.logger.error("翻译包安装失败")
                return {'success': False, 'error': '翻译包安装失败'}
            
            # 处理翻译
            translated_count = 0
            skipped_count = 0
            
            for i, trans in enumerate(translations):
                # 跳过已翻译的内容（如果设置了跳过）
                if skip_translated and trans['translation'] and trans['type'] != 'unfinished':
                    skipped_count += 1
                    continue
                
                # 翻译
                translated_text = self.translate_text(trans['source'], from_lang, to_lang)
                translations[i]['translation'] = translated_text
                translations[i]['type'] = ''  # 清除unfinished标记
                translated_count += 1
                
                # 进度显示
                if (i + 1) % 10 == 0:
                    self.logger.info(f"已处理 {i + 1}/{len(translations)} 条")
            
            # 生成输出文件
            self._generate_translated_ts(input_ts, output_ts, translations)
            
            self.logger.info(f"翻译完成: 翻译了 {translated_count} 条，跳过了 {skipped_count} 条")
            return {
                'success': True,
                'input_file': input_ts,
                'output_file': output_ts,
                'from_lang': from_lang,
                'to_lang': to_lang,
                'translated_count': translated_count,
                'skipped_count': skipped_count,
                'total_count': len(translations)
            }
            
        except Exception as e:
            self.logger.error(f"翻译TS文件失败: {e}")
            return {'success': False, 'error': str(e)}
    
    def _generate_translated_ts(self, input_file: str, output_file: str, translations: List[Dict]):
        """生成翻译后的TS文件"""
        try:
            tree = ET.parse(input_file)
            root = tree.getroot()
            
            trans_index = 0
            for message in root.findall('.//message'):
                source = message.find('source')
                translation = message.find('translation')
                
                if source is not None and source.text and trans_index < len(translations):
                    if translation is None:
                        translation = ET.SubElement(message, 'translation')
                    
                    translation.text = translations[trans_index]['translation']
                    if 'type' in translations[trans_index] and translations[trans_index]['type']:
                        translation.set('type', translations[trans_index]['type'])
                    else:
                        if 'type' in translation.attrib:
                            del translation.attrib['type']
                    
                    trans_index += 1
            
            # 美化XML输出
            self._prettify_xml(root)
            
            # 写入文件
            tree.write(output_file, encoding='utf-8', xml_declaration=True)
            self.logger.info(f"已生成翻译文件: {output_file}")
            
        except Exception as e:
            self.logger.error(f"生成翻译文件失败: {e}")
            raise
    
    def _prettify_xml(self, element, level=0):
        """美化XML格式"""
        # 缩进处理
        indent = "\n" + level * "  "
        if len(element):
            if not element.text or not element.text.strip():
                element.text = indent + "  "
            if not element.tail or not element.tail.strip():
                element.tail = indent
            for child in element:
                self._prettify_xml(child, level + 1)
            if not child.tail or not child.tail.strip():
                child.tail = indent
        else:
            if level and (not element.tail or not element.tail.strip()):
                element.tail = indent

    def get_installed_packages(self):
        """获取已安装的翻译包"""
        try:
            # 使用argostranslate.package模块获取已安装包
            installed_packages = argostranslate.package.get_installed_packages()
            self.logger.info(f"获取到 {len(installed_packages)} 个已安装翻译包")
            return installed_packages
        except Exception as e:
            self.logger.error(f"获取已安装包失败: {e}")
            return []

    def get_available_packages(self):
        """获取可用的翻译包"""
        try:
            # 更新包索引
            argostranslate.package.update_package_index()
            
            # 获取可用包
            available_packages = argostranslate.package.get_available_packages()
            self.logger.info(f"获取到 {len(available_packages)} 个可用翻译包")
            return available_packages
        except Exception as e:
            self.logger.error(f"获取可用包失败: {e}")
            return []

    def install_package_by_codes(self, from_lang: str, to_lang: str) -> bool:
        """根据语言代码安装翻译包"""
        try:
            self.logger.info(f"安装翻译包: {from_lang} -> {to_lang}")
            
            # 获取可用包
            available_packages = self.get_available_packages()
            
            # 查找匹配的包
            package_to_install = None
            for package in available_packages:
                if package.from_code == from_lang and package.to_code == to_lang:
                    package_to_install = package
                    break
            
            if package_to_install:
                self.logger.info(f"找到翻译包: {package_to_install}")
                argostranslate.package.install_from_path(package_to_install.download())
                self.installed_packages.add((from_lang, to_lang))
                self.logger.info(f"成功安装翻译包: {from_lang} -> {to_lang}")
                return True
            else:
                self.logger.warning(f"未找到翻译包: {from_lang} -> {to_lang}")
                return False
                
        except Exception as e:
            self.logger.error(f"安装翻译包失败: {e}")
            return False

def main():
    """主函数"""
    print("=== TS文件翻译工具（基于Argos Translate） ===")
    print("功能：将TS文件从一种语言翻译到另一种语言（本地离线翻译）")
    print()
    
    translator = TsTranslator()
    
    # 示例用法
    if len(sys.argv) >= 4:
        input_file = sys.argv[1]
        output_file = sys.argv[2]
        from_lang = sys.argv[3]
        to_lang = sys.argv[4] if len(sys.argv) > 4 else 'zh'
        
        if not os.path.exists(input_file):
            print(f"错误：输入文件不存在: {input_file}")
            return
        
        success = translator.translate_ts_file(input_file, output_file, from_lang, to_lang)
        if success:
            print(f"\n✅ 翻译完成！输出文件: {output_file}")
        else:
            print("\n❌ 翻译失败！")
    else:
        print("用法: python main.py <输入TS文件> <输出TS文件> <源语言> [目标语言]")
        print("示例: python main.py translation_en.ts translation_zh.ts en zh")
        print("\n支持的语言代码: en, zh, ja, ko, fr, de, es, ru, pt, it 等")

if __name__ == "__main__":
    main()