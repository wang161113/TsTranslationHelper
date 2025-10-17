#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量TS文件翻译工具
支持批量处理多个TS文件，使用Argos Translate进行本地翻译
"""

import os
import sys
import argparse
import logging
from pathlib import Path
from typing import List, Dict, Tuple
import pandas as pd
from main import TsTranslator


class BatchTranslator:
    """批量翻译器类"""
    
    def __init__(self, source_lang: str = "en", target_lang: str = "zh"):
        """
        初始化批量翻译器
        
        Args:
            source_lang: 源语言代码
            target_lang: 目标语言代码
        """
        self.source_lang = source_lang
        self.target_lang = target_lang
        self.translator = TsTranslator()
        self.logger = self._setup_logging()
    
    def _setup_logging(self) -> logging.Logger:
        """设置日志"""
        logger = logging.getLogger('BatchTranslator')
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler(sys.stdout)
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    def find_ts_files(self, directory: str) -> List[Path]:
        """
        在目录中查找所有TS文件
        
        Args:
            directory: 要搜索的目录路径
            
        Returns:
            TS文件路径列表
        """
        directory_path = Path(directory)
        if not directory_path.exists():
            raise FileNotFoundError(f"目录不存在: {directory}")
        
        ts_files = list(directory_path.rglob("*.ts"))
        self.logger.info(f"在目录 {directory} 中找到 {len(ts_files)} 个TS文件")
        return ts_files
    
    def batch_translate(self, input_paths: List[str], output_dir: str = None, 
                       skip_translated: bool = True) -> Dict[str, Dict]:
        """
        批量翻译TS文件
        
        Args:
            input_paths: 输入文件路径列表（可以是文件或目录）
            output_dir: 输出目录（如果为None，则输出到原文件目录）
            skip_translated: 是否跳过已有翻译的条目
            
        Returns:
            翻译结果统计字典
        """
        all_ts_files = []
        
        # 收集所有TS文件
        for path in input_paths:
            path_obj = Path(path)
            if path_obj.is_file() and path_obj.suffix.lower() == '.ts':
                all_ts_files.append(path_obj)
            elif path_obj.is_dir():
                all_ts_files.extend(self.find_ts_files(str(path_obj)))
        
        if not all_ts_files:
            self.logger.warning("未找到任何TS文件")
            return {}
        
        results = {}
        
        for ts_file in all_ts_files:
            self.logger.info(f"开始翻译文件: {ts_file}")
            
            try:
                # 确定输出路径
                if output_dir:
                    output_path = Path(output_dir) / ts_file.name
                else:
                    output_path = ts_file.parent / f"{ts_file.stem}_{self.target_lang}.ts"
                
                # 执行翻译
                stats = self.translator.translate_ts_file(
                    str(ts_file), 
                    str(output_path), 
                    self.source_lang,
                    self.target_lang,
                    skip_translated
                )
                
                results[str(ts_file)] = {
                    'output_file': str(output_path),
                    'stats': stats,
                    'status': 'success'
                }
                
                self.logger.info(f"文件翻译完成: {ts_file} -> {output_path}")
                self.logger.info(f"翻译统计: 总条目 {stats['total']}, 翻译 {stats['translated']}, 跳过 {stats['skipped']}")
                
            except Exception as e:
                self.logger.error(f"翻译文件失败 {ts_file}: {str(e)}")
                results[str(ts_file)] = {
                    'output_file': None,
                    'stats': None,
                    'status': 'failed',
                    'error': str(e)
                }
        
        return results
    
    def generate_report(self, results: Dict[str, Dict], report_file: str = "batch_translation_report.csv") -> str:
        """
        生成批量翻译报告
        
        Args:
            results: 翻译结果字典
            report_file: 报告文件路径
            
        Returns:
            报告文件路径
        """
        report_data = []
        
        for file_path, result in results.items():
            row = {
                'input_file': file_path,
                'output_file': result.get('output_file', ''),
                'status': result.get('status', 'unknown'),
                'total_entries': result.get('stats', {}).get('total', 0) if result.get('stats') else 0,
                'translated': result.get('stats', {}).get('translated', 0) if result.get('stats') else 0,
                'skipped': result.get('stats', {}).get('skipped', 0) if result.get('stats') else 0,
                'error': result.get('error', '')
            }
            report_data.append(row)
        
        df = pd.DataFrame(report_data)
        df.to_csv(report_file, index=False, encoding='utf-8-sig')
        
        self.logger.info(f"批量翻译报告已生成: {report_file}")
        return report_file


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='批量TS文件翻译工具')
    parser.add_argument('input_paths', nargs='+', help='输入文件或目录路径')
    parser.add_argument('-s', '--source', default='en', help='源语言代码 (默认: en)')
    parser.add_argument('-t', '--target', default='zh', help='目标语言代码 (默认: zh)')
    parser.add_argument('-o', '--output', help='输出目录路径')
    parser.add_argument('--no-skip', action='store_false', dest='skip_translated', 
                       help='不跳过已有翻译的条目')
    parser.add_argument('-r', '--report', help='报告文件路径 (默认: batch_translation_report.csv)')
    
    args = parser.parse_args()
    
    # 创建批量翻译器
    batch_translator = BatchTranslator(args.source, args.target)
    
    # 执行批量翻译
    results = batch_translator.batch_translate(
        args.input_paths, 
        args.output, 
        args.skip_translated
    )
    
    # 生成报告
    report_file = args.report or "batch_translation_report.csv"
    batch_translator.generate_report(results, report_file)
    
    # 打印摘要
    success_count = sum(1 for r in results.values() if r['status'] == 'success')
    failed_count = sum(1 for r in results.values() if r['status'] == 'failed')
    
    print(f"\n批量翻译完成!")
    print(f"成功: {success_count} 个文件")
    print(f"失败: {failed_count} 个文件")
    print(f"详细报告: {report_file}")


if __name__ == "__main__":
    main()