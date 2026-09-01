import re
from pathlib import Path


# ============================================================
# 固定配置
# ============================================================

# 网站/目录名称
DIRECTORY_TITLE = "神座櫻緣起 前篇"

# 日文目录名称
DIRECTORY_JP_TITLE = "神座桜縁起 前篇"

# HTML 标题
PAGE_TITLE = "神座櫻緣起 前篇 - 散櫻亂武"

# 原文网址
ORIGINAL_URL = "http://bfpblog.bakafire.main.jp/?eid=14"

# ============================================================


# 脚本所在目录
CURRENT_DIR = Path(__file__).parent


def get_html_files():
    """
    获取同目录下：
    01.html
    02.html
    03.html
    ...
    """

    files = []

    for file in CURRENT_DIR.glob("*.html"):

        # 只匹配纯数字文件名，例如 01.html、12.html
        if re.fullmatch(r"\d+", file.stem):
            files.append(file)

    # 按数字排序
    files.sort(key=lambda x: int(x.stem))

    return files


def extract_title(html_file):
    """
    从章节 HTML 中提取：

    <div class="sub-directory-title">
        <h1>中文标题</h1>
        <h2 class="jp-title">日文标题</h2>
    </div>
    """

    content = html_file.read_text(
        encoding="utf-8"
    )

    # 提取 sub-directory-title 区块
    block_match = re.search(
        r'<div\s+class=["\']sub-directory-title["\']>(.*?)</div>',
        content,
        re.DOTALL
    )

    if not block_match:
        print(f"[警告] 无法找到标题区域：{html_file.name}")
        return None

    block = block_match.group(1)

    # 提取 h1
    h1_match = re.search(
        r"<h1[^>]*>(.*?)</h1>",
        block,
        re.DOTALL
    )

    # 提取 h2 jp-title
    h2_match = re.search(
        r'<h2\s+class=["\']jp-title["\']>(.*?)</h2>',
        block,
        re.DOTALL
    )

    if not h1_match or not h2_match:
        print(f"[警告] 无法完整提取标题：{html_file.name}")
        return None

    # 清理 HTML 内可能存在的空白
    chinese_title = re.sub(
        r"\s+",
        " ",
        h1_match.group(1)
    ).strip()

    japanese_title = re.sub(
        r"\s+",
        " ",
        h2_match.group(1)
    ).strip()

    return chinese_title, japanese_title


def generate_episode_list(html_files):
    """
    根据所有章节生成：

    <div class="episode-list">

        <div class="episode-item">
            ...
        </div>

    </div>
    """

    episodes = []

    for file in html_files:

        result = extract_title(file)

        if result is None:
            continue

        chinese_title, japanese_title = result

        episode_html = f"""                <div class="episode-item">
                    <h2>{chinese_title}</h2>
                    <h3 class="jp-title">{japanese_title}</h3>
                    <a href="{file.name}" class="read-button">閱讀本話</a>
                    <p class="series-description"></p>
                </div>"""

        episodes.append(episode_html)

        print(
            f"[读取] {file.name}"
            f" → {chinese_title}"
        )

    return "\n\n".join(episodes)


def main():

    print("=" * 60)
    print("开始生成 index.html")
    print("=" * 60)

    html_files = get_html_files()

    if not html_files:
        print("没有找到 01.html、02.html 等章节文件！")
        return

    print(f"找到 {len(html_files)} 个章节文件\n")

    episode_list = generate_episode_list(
        html_files
    )

    # ========================================================
    # 生成完整 index.html
    # ========================================================

    output_html = f"""<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{PAGE_TITLE}</title>
    <link rel="stylesheet" href="../../styles/main.css">
</head>
<body>
    <div class="container">
        <nav class="breadcrumb">
            <a href="../../index.html">首頁</a> > 
            {DIRECTORY_TITLE}
        </nav>

        <div class="sub-directory-title">
            <h1>{DIRECTORY_TITLE}</h1>
            <h2 class="jp-title">{DIRECTORY_JP_TITLE}</h2>
        </div>

        <main class="novel-content">
            <div class="episode-list">
{episode_list}
            </div>

            <!-- 版權聲明區塊 -->
            <div class="copyright-notice">
                <h3>關於本站</h3>
                <p>原文連載網址：<a href="{ORIGINAL_URL}" target="_blank">桜降る代に小噺を</a></p> 
                <p>日文原文版權所有 © 作 五十嵐月夜 / 原案 BakaFire / 插繪 TOKIAME</p> 
                <p>中文機械翻譯 SakuraLLM (14b-qwen2.5-v1.0-q6k) / ChatGPT 5.6 Luna</p> 
                <p>本網站內容僅供學習交流使用，嚴禁用於商業用途。若有侵權請聯繫刪除。</p> 
            </div> 
        </main> 
 
        <!-- 懸浮控制區塊 --> 
        <div class="floating-controls"> 
            <button onclick="window.location.href='../../index.html'" class="home-button">目錄</button> 
            <button onclick="window.location.href='{html_files[0].name}'" class="next-button">開始閱讀</button> 
        </div> 
    </div> 
</body> 
</html>
"""

    output_file = CURRENT_DIR / "index.html"

    output_file.write_text(
        output_html,
        encoding="utf-8"
    )

    print("\n" + "=" * 60)
    print(f"生成完成：{output_file}")
    print(f"章节数量：{len(html_files)}")
    print("=" * 60)


if __name__ == "__main__":
    main()