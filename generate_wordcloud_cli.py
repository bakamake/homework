#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""词云生成器 - CLI版本"""

import os
import sys
import glob
import argparse
from wordcloud import WordCloud
import matplotlib.pyplot as plt

def read_all_txt_files(txt_dir):
    """读取指定目录下的所有txt文件并合并文本"""
    if not os.path.exists(txt_dir):
        print(f"错误: 目录不存在 {txt_dir}")
        return ""

    txt_files = glob.glob(os.path.join(txt_dir, "*.txt"))
    all_text = ""

    print(f"找到 {len(txt_files)} 个txt文件")

    for txt_file in txt_files:
        print(f"读取: {os.path.basename(txt_file)}")
        try:
            with open(txt_file, 'r', encoding='utf-8') as f:
                content = f.read()
                all_text += content + "\n"
        except Exception as e:
            print(f"读取文件 {txt_file} 时出错: {e}")

    return all_text

def generate_wordcloud(text, output_path, width=1920, height=1080,
                      background_color='black', max_words=1000,
                      colormap='plasma', relative_scaling=0.6,
                      collocations=False, prefer_horizontal=0.9):
    """生成词云并保存 - 新参数配置"""
    print(f"\n正在生成词云...")
    print(f"图片尺寸: {width}x{height}")
    print(f"背景色: {background_color}")
    print(f"最大词汇数: {max_words}")
    print(f"配色方案: {colormap}")

    # 尝试使用系统字体，如果失败则使用默认字体
    font_paths = [
        '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
        '/System/Library/Fonts/Arial.ttf',
        '/Windows/Fonts/arial.ttf',
        '/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf',
    ]

    font_path = None
    for fp in font_paths:
        if os.path.exists(fp):
            font_path = fp
            print(f"使用字体: {font_path}")
            break

    if not font_path:
        print("警告: 未找到合适的字体，使用默认字体（可能不支持中文）")

    # 配置词云参数 - 使用新的参数
    wordcloud_kwargs = {
        'width': width,
        'height': height,
        'background_color': background_color,
        'max_words': max_words,
        'colormap': colormap,
        'relative_scaling': relative_scaling,
        'random_state': 42,
        'collocations': collocations,
        'prefer_horizontal': prefer_horizontal,
        'margin': 10,
        'prefer_horizontal': prefer_horizontal
    }

    if font_path:
        wordcloud_kwargs['font_path'] = font_path

    wordcloud = WordCloud(**wordcloud_kwargs).generate(text)

    # 确保输出目录存在
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # 保存词云图片
    wordcloud.to_file(output_path)
    print(f"词云已保存到: {output_path}")

    # 显示词云（可选）
    plt.figure(figsize=(16, 9))
    plt.imshow(wordcloud, interpolation='bilinear')
    plt.axis('off')
    plt.tight_layout(pad=0)

    # 不显示图片，只保存文件
    # plt.show()

    return wordcloud

def main():
    parser = argparse.ArgumentParser(description='词云生成器 - CLI版本')
    parser.add_argument('txt_dir', help='包含txt文件的目录路径')
    parser.add_argument('-o', '--output', default='wordcloud.png',
                       help='输出图片路径 (默认: wordcloud.png)')
    parser.add_argument('-w', '--width', type=int, default=1920,
                       help='图片宽度 (默认: 1920)')
    parser.add_argument('-h', '--height', type=int, default=1080,
                       help='图片高度 (默认: 1080)')
    parser.add_argument('--bg-color', default='black',
                       help='背景颜色 (默认: black)')
    parser.add_argument('--max-words', type=int, default=1000,
                       help='最大词汇数 (默认: 1000)')
    parser.add_argument('--colormap', default='plasma',
                       help='配色方案 (默认: plasma)')
    parser.add_argument('--relative-scaling', type=float, default=0.6,
                       help='相对缩放比例 (默认: 0.6)')
    parser.add_argument('--no-collocations', action='store_true',
                       help='禁用词汇搭配')
    parser.add_argument('--prefer-horizontal', type=float, default=0.9,
                       help='水平排列比例 (默认: 0.9)')
    parser.add_argument('--show', action='store_true',
                       help='显示词云图片')

    args = parser.parse_args()

    # 读取文本文件
    print("=" * 60)
    print("词云生成器 - CLI版本")
    print("=" * 60)
    all_text = read_all_txt_files(args.txt_dir)

    if not all_text.strip():
        print("错误: 没有读取到任何文本内容")
        sys.exit(1)

    print(f"\n总文本长度: {len(all_text)} 字符")

    # 生成词云
    wordcloud = generate_wordcloud(
        text=all_text,
        output_path=args.output,
        width=args.width,
        height=args.height,
        background_color=args.bg_color,
        max_words=args.max_words,
        colormap=args.colormap,
        relative_scaling=args.relative_scaling,
        collocations=not args.no_collocations,
        prefer_horizontal=args.prefer_horizontal
    )

    # 显示词频统计
    print("\n" + "=" * 60)
    print("高频词汇统计:")
    print("=" * 60)
    words = wordcloud.words_
    for i, (word, freq) in enumerate(list(words.items())[:20], 1):
        print(f"{i:2d}. {word:20s} - {freq:.3f}")

    # 如果需要显示图片
    if args.show:
        plt.show()

    print("\n" + "=" * 60)
    print("词云生成完成！")
    print("=" * 60)

if __name__ == "__main__":
    main()