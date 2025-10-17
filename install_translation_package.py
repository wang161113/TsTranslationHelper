#!/usr/bin/env python3
"""安装英语到中文翻译包的脚本"""

from argostranslate import package

def install_translation_package():
    print("正在更新包索引...")
    package.update_package_index()
    
    print("获取可用包列表...")
    available_packages = package.get_available_packages()
    print(f"可用包数量: {len(available_packages)}")
    
    # 查找英语到中文的翻译包
    en_to_zh_packages = [p for p in available_packages if p.from_code == 'en' and p.to_code == 'zh']
    print(f"英语到中文包数量: {len(en_to_zh_packages)}")
    
    if en_to_zh_packages:
        print("开始安装英语到中文翻译包...")
        en_to_zh_packages[0].install()
        print("安装完成!")
        
        # 验证安装
        installed_packages = package.get_installed_packages()
        print(f"已安装包数量: {len(installed_packages)}")
        
        # 测试翻译
        from argostranslate.translate import get_translation_from_codes
        print("翻译包安装成功!")
        
        # 测试简单翻译
        try:
            translation = get_translation_from_codes("en", "zh")
            if translation:
                test_text = "Hello world"
                result = translation.translate(test_text)
                print(f"测试翻译: '{test_text}' -> '{result}'")
            else:
                print("翻译功能测试失败")
        except Exception as e:
            print(f"翻译测试出错: {e}")
    else:
        print("未找到英语到中文的翻译包")

if __name__ == "__main__":
    install_translation_package()