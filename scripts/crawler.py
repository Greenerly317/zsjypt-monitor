#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
中山资源交易平台爬虫 - Web抓取版本
使用 web_fetch 工具进行平台数据获取
"""

import json
import re
from datetime import datetime
from typing import List, Dict, Optional
from html.parser import HTMLParser

class ProjectParser(HTMLParser):
    """HTML 解析器 - 提取项目信息"""
    
    def __init__(self):
        super().__init__()
        self.projects = []
        self.current_row = {}
        self.in_row = False
        self.cell_count = 0
        self.current_cell_text = ""
        
    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)
        
        if tag == "tr" and "class" in attrs_dict:
            if "row" in attrs_dict["class"] or self.in_row == False:
                self.in_row = True
                self.current_row = {}
                self.cell_count = 0
        elif tag == "td" and self.in_row:
            self.cell_count += 1
            self.current_cell_text = ""
        elif tag == "a" and self.in_row:
            if "href" in attrs_dict:
                self.current_row["url"] = attrs_dict["href"]
    
    def handle_endtag(self, tag):
        if tag == "td" and self.in_row:
            if self.cell_count == 1:  # 项目名称
                self.current_row["title"] = self.current_cell_text.strip()
            elif self.cell_count == 2:  # 类别
                self.current_row["category"] = self.current_cell_text.strip()
            elif self.cell_count == 3:  # 发布时间
                self.current_row["publish_time"] = self.current_cell_text.strip()
        elif tag == "tr" and self.in_row:
            if self.current_row:
                # 验证项目数据完整性
                if all(k in self.current_row for k in ["title", "category", "url"]):
                    # 生成唯一 ID（使用 URL 哈希）
                    import hashlib
                    self.current_row["id"] = hashlib.md5(
                        self.current_row["url"].encode()
                    ).hexdigest()[:16]
                    self.projects.append(self.current_row)
            self.in_row = False
            self.current_row = {}
    
    def handle_data(self, data):
        if self.in_row:
            self.current_cell_text += data


def extract_projects_from_html(html_content: str) -> List[Dict]:
    """
    从 HTML 内容中提取项目列表
    
    Args:
        html_content: HTML 页面内容
        
    Returns:
        项目列表
    """
    parser = ProjectParser()
    try:
        parser.feed(html_content)
    except Exception as e:
        print(f"HTML 解析错误: {str(e)}")
    
    return parser.projects


def parse_platform_response(response_text: str) -> List[Dict]:
    """
    解析平台 API 响应（如果平台使用 JSON 返回）
    
    Args:
        response_text: API 返回内容
        
    Returns:
        项目列表
    """
    try:
        data = json.loads(response_text)
        projects = []
        
        # 假设响应格式为 {"code": 0, "data": {"list": [...]}}
        if data.get("code") == 0 and "data" in data:
            items = data["data"].get("list", [])
            for item in items:
                project = {
                    "id": item.get("id") or item.get("projectId"),
                    "title": item.get("title") or item.get("projectName"),
                    "category": item.get("category") or item.get("categoryName"),
                    "url": item.get("url") or f"/project/{item.get('id')}",
                    "publish_time": item.get("publishTime") or item.get("createTime"),
                }
                projects.append(project)
        
        return projects
    except json.JSONDecodeError:
        # 不是 JSON 格式，返回空列表
        return []


def fetch_and_parse_platform(platform_url: str, use_browser: bool = False) -> Optional[List[Dict]]:
    """
    获取并解析平台项目列表
    
    Args:
        platform_url: 平台 URL
        use_browser: 是否使用浏览器自动化（处理JS渲染的情况）
        
    Returns:
        项目列表
    """
    print(f"正在获取平台数据: {platform_url}")
    
    try:
        # 方式1: 尝试直接 HTTP 获取
        if not use_browser:
            # 这里应该使用 web_fetch 工具
            # 下面是本地模拟实现
            import urllib.request
            import urllib.error
            
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
            
            try:
                req = urllib.request.Request(platform_url, headers=headers)
                with urllib.request.urlopen(req, timeout=10) as response:
                    html_content = response.read().decode('utf-8', errors='ignore')
                    
                    # 尝试 HTML 解析
                    projects = extract_projects_from_html(html_content)
                    if projects:
                        return projects
                    
                    # 尝试 JSON 解析
                    projects = parse_platform_response(html_content)
                    if projects:
                        return projects
                    
            except (urllib.error.URLError, urllib.error.HTTPError) as e:
                print(f"HTTP 请求错误: {str(e)}")
                return None
        
        # 方式2: 使用浏览器自动化（当 JS 渲染必要时）
        if use_browser:
            print("使用浏览器自动化模式...")
            # 这里应该调用 browser-automation 工具
            # 下面是占位符
            return None
        
    except Exception as e:
        print(f"数据获取错误: {str(e)}")
        return None


# 示例：中山平台特定的解析规则
class ZhongshanPlatformParser:
    """中山平台专用解析器"""
    
    BASE_URL = "https://www.zsjypt.cn"
    
    @staticmethod
    def build_project_url(project_id: str) -> str:
        """构建项目完整 URL"""
        return f"{ZhongshanPlatformParser.BASE_URL}/project/{project_id}"
    
    @staticmethod
    def parse_project_list(html: str) -> List[Dict]:
        """解析中山平台项目列表"""
        projects = []
        
        # 示例：使用正则表达式提取项目数据
        # 实际需要根据平台 HTML 结构调整
        
        # 项目行的正则模式（需根据实际 HTML 调整）
        project_pattern = r'<tr.*?>(.*?)</tr>'
        cell_pattern = r'<td.*?>(.*?)</td>'
        link_pattern = r'href=["\'](/[^"\']*)["\']'
        
        for match in re.finditer(project_pattern, html, re.DOTALL):
            row_html = match.group(1)
            cells = re.findall(cell_pattern, row_html, re.DOTALL)
            
            if len(cells) >= 3:
                # 提取链接
                link_match = re.search(link_pattern, row_html)
                url = link_match.group(1) if link_match else ""
                
                # 清理文本（移除 HTML 标签）
                def clean_text(text):
                    return re.sub(r'<[^>]+>', '', text).strip()
                
                project = {
                    "title": clean_text(cells[0]),
                    "category": clean_text(cells[1]) if len(cells) > 1 else "未分类",
                    "publish_time": clean_text(cells[2]) if len(cells) > 2 else "",
                    "url": ZhongshanPlatformParser.build_project_url(url),
                }
                
                # 生成唯一 ID
                import hashlib
                project["id"] = hashlib.md5(project["url"].encode()).hexdigest()[:16]
                
                projects.append(project)
        
        return projects


# 测试函数
def test_parser():
    """测试解析器"""
    
    # 示例 HTML
    sample_html = """
    <table>
        <tr>
            <td><a href="/project/001">中山勘察设计项目</a></td>
            <td>建设工程</td>
            <td>2026-03-17</td>
        </tr>
        <tr>
            <td><a href="/project/002">设计服务采购</a></td>
            <td>政府采购</td>
            <td>2026-03-17</td>
        </tr>
    </table>
    """
    
    parser = ZhongshanPlatformParser()
    projects = parser.parse_project_list(sample_html)
    
    print(f"解析结果: {len(projects)} 个项目")
    for proj in projects:
        print(f"  - {proj['title']} ({proj['category']})")


if __name__ == "__main__":
    test_parser()
