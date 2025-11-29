#!/usr/bin/env python3
"""
Ghost博客文章拉取脚本
从Ghost API获取所有博文并保存到本地文件

API文档: https://ghost.org/docs/api/v3/content/
"""

import json
import os
import re
from datetime import datetime
from pathlib import Path
from typing import List, Dict
import requests
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('pull_ghost_posts.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class GhostPostFetcher:
    """Ghost博客文章获取器"""

    def __init__(self, api_key: str, ghost_url: str):
        """
        初始化获取器

        Args:
            api_key: Ghost Content API密钥
            ghost_url: Ghost博客API基础URL
        """
        self.api_key = api_key
        self.ghost_url = ghost_url.rstrip('/')
        self.base_url = f"{ghost_url}/ghost/api/content"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Ghost Post Fetcher/1.0'
        })

    def fetch_all_posts(self, limit: int = None) -> List[Dict]:
        """
        获取所有博文

        Args:
            limit: 限制获取的文章数量，None表示获取全部

        Returns:
            博文列表
        """
        all_posts = []
        page = 1
        per_page = min(limit or 100, 100)  # Ghost API最多支持100条/页

        logger.info(f"开始获取博文数据...")

        while True:
            logger.info(f"正在获取第 {page} 页...")

            params = {
                'key': self.api_key,
                'page': page,
                'limit': per_page,
                'include': 'tags,authors',  # 同时获取标签和作者信息
                'formats': 'html',  # 获取HTML格式内容
            }

            if limit:
                remaining = limit - len(all_posts)
                params['limit'] = min(remaining, per_page)

            try:
                response = self.session.get(
                    f"{self.base_url}/posts/",
                    params=params,
                    timeout=30
                )
                response.raise_for_status()

                data = response.json()
                posts = data.get('posts', [])

                if not posts:
                    logger.info("没有更多文章了")
                    break

                all_posts.extend(posts)
                logger.info(f"获取到 {len(posts)} 篇文章，累计 {len(all_posts)} 篇")

                # 如果返回的文章数少于每页数量，说明已经获取完所有文章
                if len(posts) < per_page:
                    logger.info("已获取所有文章")
                    break

                page += 1

                # 如果设置了limit，提前退出
                if limit and len(all_posts) >= limit:
                    logger.info(f"已达到限制数量 {limit}")
                    break

            except requests.exceptions.RequestException as e:
                logger.error(f"请求失败: {e}")
                raise

        logger.info(f"总共获取到 {len(all_posts)} 篇文章")
        return all_posts

    def save_as_json(self, posts: List[Dict], output_dir: str = "posts"):
        """
        保存为JSON文件

        Args:
            posts: 博文列表
            output_dir: 输出目录
        """
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        json_file = output_path / f"ghost_posts_{timestamp}.json"

        # 准备输出数据
        output_data = {
            'metadata': {
                'fetched_at': datetime.now().isoformat(),
                'total_posts': len(posts),
                'source': self.ghost_url,
            },
            'posts': posts
        }

        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)

        logger.info(f"JSON文件已保存: {json_file}")
        return json_file

    def strip_html_tags(self, html_content: str) -> str:
        """
        简单的HTML标签移除（保留文本内容）

        Args:
            html_content: HTML内容

        Returns:
            去除HTML标签的纯文本
        """
        if not html_content:
            return ""

        # 移除script和style标签
        html_content = re.sub(r'<(script|style)[^>]*>.*?</\1>', '', html_content, flags=re.DOTALL)
        # 移除HTML标签但保留换行
        html_content = re.sub(r'<[^>]+>', '\n', html_content)
        # 清理多余的空白
        html_content = re.sub(r'\n+', '\n', html_content)
        return html_content.strip()

    def save_as_txt(self, posts: List[Dict], output_dir: str = "posts/txt"):
        """
        保存为TXT文件

        Args:
            posts: 博文列表
            output_dir: 输出目录
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        saved_files = []

        for post in posts:
            # 清理文件名中的非法字符
            title = post.get('title', 'untitled')
            slug = post.get('slug', f"post-{post.get('id', 'unknown')}")

            # 生成安全的文件名
            safe_title = re.sub(r'[<>:"/\\|?*]', '_', title)
            safe_filename = f"{slug}_{safe_title[:50]}.txt"
            file_path = output_path / safe_filename

            # 提取纯文本
            html_content = post.get('html', '')
            text_content = self.strip_html_tags(html_content)

            # 准备TXT文件内容
            txt_content = f"""{'='*80}
{title}
{'='*80}

摘要: {post.get('excerpt', '无摘要')}

发布日期: {post.get('published_at', '')}

阅读时间: {post.get('reading_time', 0)} 分钟

标签: {', '.join([tag['name'] for tag in post.get('tags', [])])}

作者: {', '.join([author['name'] for author in post.get('authors', [])])}

{'='*80}
文章内容
{'='*80}

{text_content}
"""

            # 保存文件
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(txt_content)

            saved_files.append(file_path)
            logger.info(f"已保存: {file_path}")

        logger.info(f"TXT文件保存完成，共 {len(saved_files)} 个文件")
        return saved_files

    def save_index(self, posts: List[Dict], output_dir: str = "posts"):
        """
        保存文章索引文件

        Args:
            posts: 博文列表
            output_dir: 输出目录
        """
        output_path = Path(output_dir)
        index_file = output_path / "index.json"

        # 创建简化的索引
        index = []
        for post in posts:
            index.append({
                'id': post.get('id'),
                'slug': post.get('slug'),
                'title': post.get('title'),
                'excerpt': post.get('excerpt'),
                'published_at': post.get('published_at'),
                'reading_time': post.get('reading_time'),
                'tags': [tag['name'] for tag in post.get('tags', [])],
                'url': post.get('url'),
            })

        with open(index_file, 'w', encoding='utf-8') as f:
            json.dump(index, f, ensure_ascii=False, indent=2)

        logger.info(f"索引文件已保存: {index_file}")
        return index_file

    def fetch_and_save(self, output_dir: str = "posts", save_json: bool = True,
                      save_txt: bool = False, limit: int = None):
        """
        完整流程：获取并保存文章

        Args:
            output_dir: 输出目录
            save_json: 是否保存JSON文件
            save_txt: 是否保存TXT文件
            limit: 限制获取的文章数量
        """
        try:
            # 创建输出目录
            Path(output_dir).mkdir(parents=True, exist_ok=True)

            # 获取文章
            posts = self.fetch_all_posts(limit=limit)

            if not posts:
                logger.warning("没有获取到任何文章")
                return

            # 保存JSON文件
            json_files = []
            if save_json:
                json_file = self.save_as_json(posts, output_dir)
                json_files.append(json_file)
                self.save_index(posts, output_dir)

            # 保存TXT文件
            txt_files = []
            if save_txt:
                txt_dir = Path(output_dir) / "txt"
                txt_files = self.save_as_txt(posts, str(txt_dir))

            # 输出摘要
            print("\n" + "="*60)
            print("✓ 拉取完成!")
            print(f"✓ 总文章数: {len(posts)}")
            if json_files:
                print(f"✓ JSON文件: {len(json_files)}")
            if txt_files:
                print(f"✓ TXT文件: {len(txt_files)}")
            print(f"✓ 输出目录: {os.path.abspath(output_dir)}")
            print("="*60 + "\n")

        except Exception as e:
            logger.error(f"拉取失败: {e}", exc_info=True)
            raise


def main():
    """主函数"""
    # 配置参数
    API_KEY = "c390453bc88662d9ea17476ff8"
    GHOST_URL = "https://ghostlatest-production-b1f0.up.railway.app"
    OUTPUT_DIR = "ghost_posts"
    LIMIT = None  # None表示获取全部，或设置具体数字如100

    # 创建获取器实例
    fetcher = GhostPostFetcher(API_KEY, GHOST_URL)

    # 执行拉取
    fetcher.fetch_and_save(
        output_dir=OUTPUT_DIR,
        save_json=True,  # 保存完整JSON数据
        save_txt=True,   # 同时保存TXT文件
        limit=LIMIT
    )


if __name__ == "__main__":
    main()
