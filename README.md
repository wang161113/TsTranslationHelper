# TS文件翻译工具

基于Argos Translate的本地TS文件翻译工具，支持单文件翻译和批量翻译，无需API密钥和网络连接。

## 功能特性

- ✅ **本地翻译**: 使用Argos Translate实现完全离线翻译
- ✅ **多语言支持**: 支持多种语言间的相互翻译
- ✅ **批量处理**: 支持批量翻译多个TS文件或整个目录
- ✅ **图形界面**: 提供用户友好的GUI界面
- ✅ **命令行工具**: 提供命令行接口便于自动化
- ✅ **智能跳过**: 可选择跳过已有翻译的条目
- ✅ **翻译报告**: 生成详细的翻译统计报告

## 安装依赖

### 系统要求

- Python 3.7+
- Windows/Linux/macOS

### 安装步骤

1. 克隆或下载项目到本地
2. 安装Python依赖包：

```bash
pip install -r requirements.txt
```

3. 安装翻译包（可选，但推荐）：

```bash
# 更新包列表
argospm update

# 安装需要的翻译包（例如：英语到中文）
argospm install translate-en_zh

# 其他常用翻译包
argospm install translate-en_ja    # 英语到日语
argospm install translate-en_ko    # 英语到韩语
argospm install translate-en_fr    # 英语到法语
argospm install translate-en_de    # 英语到德语
argospm install translate-en_es    # 英语到西班牙语
```

## 使用方法

### 图形界面使用

1. 运行图形界面：

```bash
python gui_app.py
```

或者双击运行 `start_gui.bat`（Windows）

2. 在图形界面中：
   - 选择"单文件翻译"标签页进行单个文件翻译
   - 选择"批量翻译"标签页进行批量文件翻译
   - 在"设置"标签页管理翻译包

### 命令行使用

#### 单文件翻译

```bash
# 基本用法
python main.py input.ts output.ts

# 指定语言
python main.py input.ts output.ts -s en -t zh

# 不跳过已有翻译
python main.py input.ts output.ts --no-skip

# 查看帮助
python main.py --help
```

#### 批量翻译

```bash
# 翻译单个文件
python batch_translator.py file1.ts

# 翻译多个文件
python batch_translator.py file1.ts file2.ts file3.ts

# 翻译整个目录
python batch_translator.py /path/to/ts/files/

# 指定输出目录和语言
python batch_translator.py /path/to/ts/files/ -o /output/dir -s en -t zh

# 生成详细报告
python batch_translator.py /path/to/ts/files/ -r report.csv
```

## 文件格式说明

### TS文件格式

TS文件是Qt的翻译文件格式，基于XML结构：

```xml
<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE TS>
<TS version="2.1" language="en_US">
<context>
    <name>MainWindow</name>
    <message>
        <source>Hello World</source>
        <translation>你好世界</translation>
    </message>
    <message>
        <source>Open File</source>
        <translation type="unfinished"></translation>
    </message>
</context>
</TS>
```

### 支持的语言代码

| 语言 | 代码 | 说明 |
|------|------|------|
| 中文 | zh | 简体中文 |
| 英语 | en | 英语 |
| 日语 | ja | 日语 |
| 韩语 | ko | 韩语 |
| 法语 | fr | 法语 |
| 德语 | de | 德语 |
| 西班牙语 | es | 西班牙语 |

## 项目结构

```
TsTranslationHelper/
├── main.py                 # 主翻译程序
├── batch_translator.py     # 批量翻译工具
├── gui_app.py             # 图形界面应用
├── requirements.txt        # 依赖包列表
├── README.md              # 项目说明文档
├── example_en.ts          # 示例TS文件
└── start_gui.bat          # Windows启动脚本
```

## 核心类说明

### TsTranslator类

主要的翻译器类，负责：
- 翻译包的管理和加载
- TS文件的解析和生成
- 翻译执行和结果处理

### BatchTranslator类

批量翻译器类，负责：
- 批量TS文件的查找和收集
- 批量翻译任务的执行
- 翻译结果的统计和报告生成

### TranslationApp类

图形界面应用类，提供：
- 单文件翻译界面
- 批量翻译界面
- 翻译包管理界面
- 实时进度显示

## 常见问题

### Q: 翻译速度慢怎么办？
A: 首次使用需要加载翻译模型，后续翻译会更快。可以尝试安装更小的翻译包。

### Q: 翻译质量不满意怎么办？
A: Argos Translate是基于开源的翻译模型，对于专业术语可能不够准确。建议：
1. 检查源文本是否清晰
2. 尝试不同的翻译包
3. 手动校对重要翻译

### Q: 如何添加新的语言支持？
A: 使用argospm安装对应的翻译包：
```bash
argospm update
argospm search <语言代码>  # 搜索可用包
argospm install <包名>     # 安装包
```

### Q: 批量翻译时内存不足？
A: 可以分批处理文件，或使用命令行工具分多次运行。

## 开发说明

### 扩展新的翻译引擎

项目设计支持扩展其他翻译引擎：

```python
class CustomTranslator:
    def translate_text(self, text: str, source_lang: str, target_lang: str) -> str:
        # 实现自定义翻译逻辑
        pass
```

### 添加新的文件格式支持

可以扩展支持其他翻译文件格式：

```python
class CustomFileParser:
    def parse_file(self, file_path: str) -> List[TranslationItem]:
        # 解析自定义格式文件
        pass
    
    def generate_file(self, items: List[TranslationItem], output_path: str):
        # 生成自定义格式文件
        pass
```

## 许可证

本项目基于MIT许可证开源。

## 贡献

欢迎提交Issue和Pull Request来改进项目。

## 更新日志

### v1.0.0 (2024-01-01)
- 初始版本发布
- 支持单文件和批量翻译
- 提供图形界面和命令行工具
- 基于Argos Translate实现本地翻译

## 联系方式

如有问题或建议，请提交GitHub Issue或联系开发者。