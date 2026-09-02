import os
import json
import re
import requests
from bs4 import BeautifulSoup, Tag, NavigableString


# ============================================================
# 配置
# ============================================================
# 重复次数
TIME = 1

# 第一次访问的网址
START_URL = "http://bfpblog.bakafire.main.jp/?eid=57"

# 第一个输出文件
# 11 -> 011-jp.txt
START_FILE_NUMBER = 20.5

FILE_SUFFIX = "-jp.txt"

# 保存下一章网址和文件编号
STATE_FILE = "extract_state.json"

# ============================================================
# 转换数字
# ============================================================
def format_number(number):
    """
    20   -> 20
    20.5 -> 20.5
    1    -> 01
    1.5  -> 01.5
    """

    if number == int(number):
        return f"{int(number):02d}"

    integer_part = int(number)
    decimal_part = int(round((number - integer_part) * 10))

    return f"{integer_part:02d}.{decimal_part}"

# ============================================================
# 上下话
# ============================================================
def get_previous_number(file_number, script_dir):
    # 当前是 20.5 → 上一话一定是 20
    if file_number % 1 == 0.5:
        return file_number - 0.5

    # 当前是 21 → 优先检查 20.5 是否存在
    half_number = file_number - 0.5
    half_filename = f"{format_number(half_number)}.html"
    half_path = os.path.join(script_dir, half_filename)

    if os.path.exists(half_path):
        return half_number

    # 没有 20.5 → 正常上一话
    return file_number - 1


def get_next_number(file_number, next_is_interlude):
    """
    当前：
    20

    如果下一话是閑話：
    -> 20.5

    否则：
    -> 21


    当前：
    20.5

    下一话正常：
    -> 21
    """

    # 当前就是 .5
    if file_number % 1 == 0.5:
        return file_number + 0.5

    # 下一话是閑話
    if next_is_interlude:
        return file_number + 0.5

    # 普通下一话
    return file_number + 1

def get_title_from_url(url, headers):

    try:

        response = requests.get(
            url,
            headers=headers,
            timeout=30
        )

        response.raise_for_status()

        if response.apparent_encoding:
            response.encoding = response.apparent_encoding

        soup = BeautifulSoup(
            response.text,
            "html.parser"
        )

        return get_page_title(soup)

    except Exception as e:

        print(
            f"[WARN] 无法获取下一话标题：{e}"
        )

        return ""


# ============================================================
# 状态读取
# ============================================================

def load_state():
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)

            return (
                data["next_url"],
                float(data["file_number"])
            )

        except Exception as e:
            print("[WARN] 状态文件读取失败：", e)

    return START_URL, float(START_FILE_NUMBER)


def save_state(next_url, file_number):
    data = {
        "next_url": next_url,
        "file_number": file_number
    }

    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(
            data,
            f,
            ensure_ascii=False,
            indent=2
        )


def convert_special_tags(container):
    """
    转换：

    <ruby>
        <rb>徒寄花</rb>
        <rt>あだよりばな</rt>
    </ruby>

    →

    [ruby text="あだよりばな"]徒寄花[/ruby]


    <strong>文字</strong>

    →

    [b]文字[/b]
    """

    # ========================================================
    # Ruby
    # ========================================================

    for ruby in container.find_all("ruby"):

        rt = ruby.find("rt")

        ruby_text = ""

        if rt:
            # 不使用 strip()，避免删除可能存在的内容
            ruby_text = rt.get_text().strip()

        rb = ruby.find("rb")

        if rb:
            base_text = rb.get_text().strip()

        else:

            # 兼容：
            # <ruby>徒寄花<rt>あだよりばな</rt></ruby>

            parts = []

            for child in ruby.contents:

                if isinstance(child, NavigableString):

                    text = str(child)

                    if text:
                        parts.append(text)

                elif isinstance(child, Tag):

                    if child.name not in ("rt", "rp"):

                        parts.append(
                            child.get_text()
                        )

            base_text = "".join(parts).strip()

        if base_text and ruby_text:

            replacement = (
                f'[ruby text="{ruby_text}"]'
                f'{base_text}'
                f'[/ruby]'
            )

            ruby.replace_with(
                NavigableString(replacement)
            )

        elif base_text:

            ruby.replace_with(
                NavigableString(base_text)
            )

        else:

            ruby.decompose()

    # ========================================================
    # Strong
    # ========================================================

    for strong in container.find_all("strong"):

        text = strong.get_text()

        replacement = (
            f"[b]{text}[/b]"
        )

        strong.replace_with(
            NavigableString(replacement)
        )

# ============================================================
# 判断是否为导航栏
# ============================================================

def is_navigation(element):
    """
    判断：

    《目録へ》
    《次へ》

    所在的导航栏。

    不管有没有《前へ》，只要是导航链接就停止。
    """

    if not isinstance(element, Tag):
        return False

    text = element.get_text(" ", strip=True)

    return (
        "《目録へ》" in text
        or "《次へ》" in text
    ) and element.find("a") is not None


# ============================================================
# 获取下一章 URL
# ============================================================

def get_next_url(container):
    """
    找最后面的：

    <a href="...">《次へ》</a>
    """

    next_url = None

    for a in container.find_all("a"):

        text = a.get_text(strip=True)

        if "《次へ》" in text:

            href = a.get("href")

            if href:
                next_url = href

    return next_url


# ============================================================
# 判断 <p> 是否为空行
# ============================================================

def is_empty_paragraph(element):

    if element.name != "p":
        return False

    # 移除 nbsp 后检查
    text = element.get_text()

    text = (
        text
        .replace("\xa0", "")
        .replace("&nbsp;", "")
        .strip()
    )

    # 没有文字，也没有图片
    return (
        not text
        and not element.find("img")
    )

# ============================================================
# 获取段落文本
# ============================================================

def get_paragraph_text(element):
    """
    提取 <p> 内容。

    规则：
    - 普通文字：原样连接
    - <ruby>：已提前转换，不换行
    - <strong>：已提前转换，不换行
    - <br>：严格只产生一个换行
    - HTML 格式化产生的纯换行/缩进：忽略
    - 保留真正正文的行首空格
    """

    result = []

    def process(node):

        # ====================================================
        # 普通文本节点
        # ====================================================

        if isinstance(node, NavigableString):

            text = str(node)

            # nbsp 转普通空格
            text = text.replace("\xa0", " ")

            # ------------------------------------------------
            # 如果整个文本节点只是 HTML 源码格式化产生的：
            #
            # \n
            #     \n
            #         \n
            #
            # 则忽略。
            # ------------------------------------------------

            if text.strip() == "":
                return

            # ------------------------------------------------
            # 保留文字前面的空格。
            #
            # 但 HTML 源码中的换行 + 缩进不应该进入正文。
            # ------------------------------------------------

            # 如果节点开头存在 HTML 格式化换行
            if "\n" in text:

                lines = text.splitlines()

                # 去掉纯格式化空行
                lines = [
                    line for line in lines
                    if line.strip() != ""
                ]

                if not lines:
                    return

                # HTML 格式化产生的行首缩进删除
                # 但第一个真正文字节点本身的行首空格保留
                text = "".join(lines)

            result.append(text)

            return

        # ====================================================
        # 非标签
        # ====================================================

        if not isinstance(node, Tag):
            return

        # ====================================================
        # <br>
        #
        # 严格只添加一个换行
        # ====================================================

        if node.name == "br":

            # 如果前面已经是换行，就不再重复添加
            if not result or not result[-1].endswith("\n"):
                result.append("\n")

            return

        # ====================================================
        # 图片
        # ====================================================

        if node.name == "img":
            return

        # ====================================================
        # 其他标签递归处理
        # ====================================================

        for child in node.contents:
            process(child)

    # ========================================================
    # 处理 p 的所有子节点
    # ========================================================

    for child in element.contents:
        process(child)

    text = "".join(result)

    # ========================================================
    # 防止出现多个连续换行
    #
    # 这里仅针对同一个 <p> 内的 <br>
    # 不影响 <p>&nbsp;</p> 产生的空行。
    # ========================================================

    while "\n\n" in text:
        text = text.replace("\n\n", "\n")

    # ========================================================
    # 删除行尾普通空格
    # 不删除行首
    # ========================================================

    lines = text.split("\n")

    lines = [
        line.rstrip(" \t")
        for line in lines
    ]

    return "\n".join(lines)

def get_page_title(soup):
    """
    提取博客文章标题。

    例如：

    <title>
    『神座桜縁起 后篇』第１話：夜山恋離 | 桜降る代に小噺を
    </title>

    返回：

    第１話：夜山恋離
    """

    # --------------------------------------------------------
    # 优先从 <title> 提取
    # --------------------------------------------------------

    if soup.title:

        title = soup.title.get_text(
            " ",
            strip=True
        )

        # 去掉网站名称
        #
        # 『神座桜縁起 后篇』第１話：夜山恋離
        # | 桜降る代に小噺を
        #
        if "|" in title:
            title = title.split(
                "|",
                1
            )[0].strip()

        # ----------------------------------------------------
        # 去掉开头的作品名
        #
        # 『神座桜縁起 后篇』
        # ----------------------------------------------------

        title = re.sub(
            r"^『[^』]+』",
            "",
            title
        ).strip()

        if title:
            return title

    # --------------------------------------------------------
    # 备用：博客文章标题元素
    # --------------------------------------------------------

    selectors = [
        ".entryTitle",
        ".entry-title",
        ".entry_title",
        "h1.entryTitle",
        "h2.entryTitle"
    ]

    for selector in selectors:

        element = soup.select_one(selector)

        if element:

            title = element.get_text(
                " ",
                strip=True
            )

            if title:
                return title

    return ""

# ============================================================
# 提取正文
# ============================================================

def extract_content(html):

    soup = BeautifulSoup(
        html,
        "html.parser"
    )

    jp_title = get_page_title(soup)

    entry = soup.select_one(
        "div.entryText"
    )

    if entry is None:

        print("[ERROR] 找不到 div.entryText")

        return None, None, ""

    container = entry.select_one(
        "div.jgm_entry_desc_mark"
    )

    if container is None:
        container = entry

    # --------------------------------------------------------
    # 先取得下一章网址
    # --------------------------------------------------------

    next_url = get_next_url(container)

    # --------------------------------------------------------
    # Ruby 转换
    # --------------------------------------------------------

    convert_special_tags(container)

    # --------------------------------------------------------
    # 提取
    # --------------------------------------------------------

    result = []

    started = False

    for element in container.find_all(
        recursive=False
    ):

        # ====================================================
        # 如果遇到导航栏
        # ====================================================

        if element.name == "p" and is_navigation(element):

            # 开始之前：
            # 这是顶部导航栏，忽略
            if not started:
                continue

            # 开始之后：
            # 这是底部导航栏，停止
            else:
                break

        # ====================================================
        # <br> 忽略
        # ====================================================

        if element.name == "br":
            continue

        # ====================================================
        # <p>
        # ====================================================

        if element.name == "p":

            # ------------------------------------------------
            # 空段落
            # ------------------------------------------------

            if is_empty_paragraph(element):

                # 只有正文已经开始后才记录空行
                if started:
                    result.append("")

                continue

            # ------------------------------------------------
            # 图片
            # ------------------------------------------------

            images = element.find_all("img")

            if images:

                # 图片出现说明正文已经开始
                started = True

                for img in images:

                    src = img.get("src")

                    if src:
                        result.append(
                            f"[图片: {src}]"
                        )

                continue

            # ------------------------------------------------
            # 普通正文
            # ------------------------------------------------

            text = get_paragraph_text(element)

            # 如果完全没有内容，忽略
            if not text.strip():
                continue

            # 找到第一个真正的正文
            started = True

            result.append(text)

            continue

    # ========================================================
    # 去掉末尾多余空行
    # ========================================================

    while result and not result[-1].strip():
        result.pop()

    content = "\n".join(result)

    return content, next_url, jp_title

def process_images(content):
    """
    查找：

    [图片: URL]

    将其替换成空行，同时记录图片应该插入到第几行。
    """

    import re

    image_pattern = re.compile(
        r'^\[图片:\s*(.+?)\]\s*$'
    )

    lines = content.split("\n")

    new_lines = []

    images = []

    # 当前 TXT 的正文行号
    line_number = 0

    for line in lines:

        match = image_pattern.match(line)

        if match:

            image_url = match.group(1).strip()

            # 图片插入在当前已处理的最后一行之后
            images.append({
                "line": line_number,
                "url": image_url
            })

            # 图片位置在 TXT 中变成一个空行
            new_lines.append("")

        else:

            new_lines.append(line)

            # 每一个 TXT 行都计算行号
            line_number += 1

    return "\n".join(new_lines), images

def generate_html(
    file_number,
    images,
    jp_title,
    next_file_number,
    script_dir
):
    """
    生成小说 HTML。
    """

    number = format_number(file_number)

    previous_file_number = get_previous_number(
    file_number,
    script_dir
    )

    previous_number = format_number(
        previous_file_number
    )

    next_number = format_number(
        next_file_number
    )

    # --------------------------------------------------------
    # 图片定义
    # --------------------------------------------------------

    image_definitions = []

    for image in images:

        image_definitions.append(
            f'''            <div class="novel-image-def" data-insert-after-line="{image["line"]}">
                <figure class="novel-image">
                    <img src="{image["url"]}">
                </figure>
            </div>'''
        )

    images_html = "\n".join(
        image_definitions
    )

    # --------------------------------------------------------
    # HTML
    # --------------------------------------------------------

    html = f'''<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>第 {number} 話 - 散櫻代之神語</title>
    <link rel="stylesheet" href="../../../../styles/main.css">
    <script src="../../../../scripts/novel-loader.js"></script>
</head>
<body>
    <div class="container">
        <nav class="breadcrumb">
            <a href="../../../../index.html">首頁</a> >
            <a href="../../index.html">散櫻代之神語</a> >
            <a href="index.html">終章：散櫻代即將揭幕</a> > 
            第 {number} 話: 待翻译
        </nav>

        <div class="sub-directory-title">
            <h1>第 {number} 話: 待翻译</h1>
            <h2 class="jp-title">{jp_title}</h2>
        </div>


        <main class="novel-content" id="novel-content">
            <p class="loading">載入中...</p>
        </main>


        <!-- 圖片定義區塊 -->
        <div id="image-definitions" style="display: none;">

{images_html}

        </div>


        <!-- 設定面板 -->
        <div class="settings-panel" id="settings-panel">
            <h4>閱讀模式</h4>
            <div class="settings-option">
                <label>
                    <input type="radio" name="display-mode" value="bilingual" checked>
                    中日對照
                </label>
            </div>
            <div class="settings-option">
                <label>
                    <input type="radio" name="display-mode" value="chinese-only">
                    僅中文
                </label>
            </div>
            <div class="settings-option">
                <label>
                    <input type="radio" name="display-mode" value="japanese-only">
                    僅日文
                </label>
            </div>
        </div>

        <!-- 懸浮控制區塊 -->
        <div class="floating-controls">
            <button onclick="window.location.href='{previous_number}.html'" class="home-button">上一話</button>
            <button onclick="window.location.href='index.html'" class="home-button">章節目錄</button>
            <button onclick="document.getElementById('settings-panel').classList.toggle('active')" class="settings-button">顯示設定</button>
            <button onclick="window.location.href='{next_number}.html'" class="next-button">下一話</button>
        </div>
    </div>


    <script>
    // 載入小說內容
        loadNovelContent('./text/{number}-zh.txt', './text/{number}-jp.txt');
    </script>

</body>
</html>
'''

    return html

# ============================================================
# 主程序
# ============================================================

def main():

    url, file_number = load_state()

    script_dir = os.path.dirname(
        os.path.abspath(__file__)
    )

    number = format_number(file_number)

    filename = (
        f"{number}{FILE_SUFFIX}"
    )

    # TXT 输出目录
    text_dir = os.path.join(
        script_dir,
        "text"
    )

    # 如果 text 文件夹不存在则自动创建
    os.makedirs(
        text_dir,
        exist_ok=True
    )

    # TXT 保存路径
    output_path = os.path.join(
        text_dir,
        filename
    )

    print("=" * 60)
    print(f"当前网址：{url}")
    print(f"输出文件：{filename}")
    print("=" * 60)

    headers = {
        "User-Agent": (
            "Mozilla/5.0 "
            "(Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 "
            "(KHTML, like Gecko) "
            "Chrome/140.0.0.0 "
            "Safari/537.36"
        )
    }

    try:

        response = requests.get(
            url,
            headers=headers,
            timeout=30
        )

        print(
            f"[INFO] HTTP 状态码："
            f"{response.status_code}"
        )

        response.raise_for_status()

    except Exception as e:

        print("[ERROR] 请求失败：")
        print(e)

        return

    # 自动检测编码
    if response.apparent_encoding:
        response.encoding = response.apparent_encoding

    print(
        f"[INFO] 网页编码："
        f"{response.encoding}"
    )

    # ========================================================
    # 提取正文
    # ========================================================

    content, next_url, jp_title = extract_content(
        response.text
    )

    # ========================================================
    # 检查下一话标题，决定下一个文件编号
    # ========================================================

    next_file_number = file_number + 1

    if next_url:

        try:
            print()
            print("[INFO] 正在检查下一话标题...")

            next_title = get_title_from_url(
                next_url,
                headers
            )

            print(
                f"[INFO] 下一话标题：{next_title}"
            )

            # 当前不是 .5，并且下一话是「閑話」
            if (
                file_number % 1 != 0.5
                and "閑話" in next_title
            ):
                next_file_number = file_number + 0.5

            # 当前是 .5，下一话恢复正常整数编号
            elif file_number % 1 == 0.5:
                next_file_number = int(file_number) + 1

            else:
                next_file_number = file_number + 1

        except Exception as e:

            print(
                f"[WARN] 检查下一话标题失败：{e}"
            )

            # 出错时的默认规则
            if file_number % 1 == 0.5:
                next_file_number = int(file_number) + 1
            else:
                next_file_number = file_number + 1

    print(
        f"[INFO] 日文标题：{jp_title}"
    )

    if content is None or not content.strip():

        print("[ERROR] 没有提取到正文！")

        debug_path = os.path.join(
            script_dir,
            "debug.html"
        )

        with open(
            debug_path,
            "w",
            encoding="utf-8"
        ) as f:

            f.write(response.text)

        print(
            f"[DEBUG] 已保存网页源码："
            f"{debug_path}"
        )

        return

    # ============================================================
    # 图片处理
    # ============================================================

    content, images = process_images(content)


    # ============================================================
    # 保存 TXT
    # ============================================================

    with open(
        output_path,
        "w",
        encoding="utf-8"
    ) as f:

        f.write(content)


    # ============================================================
    # 生成 HTML
    # ============================================================

    html_content = generate_html(
    file_number,
    images,
    jp_title,
    next_file_number,
    script_dir
    )


    html_filename = (
        f"{format_number(file_number)}.html"
    )


    html_path = os.path.join(
        script_dir,
        html_filename
    )


    with open(
        html_path,
        "w",
        encoding="utf-8"
    ) as f:

        f.write(html_content)


    print(
        f"[OK] HTML 已保存："
        f"{html_path}"
    )

    print()
    print("[OK] 提取成功")
    print(f"[OK] 保存：{output_path}")
    print(f"[OK] 正文长度：{len(content)}")

    # ========================================================
    # 保存下一章
    # ========================================================

    if next_url:

        save_state(
            next_url,
            next_file_number
        )

        print()
        print(
            f"[INFO] 下一章：{next_url}"
        )

        print(
            f"[INFO] 下次文件："
            f"{format_number(next_file_number)}{FILE_SUFFIX}"
        )

    else:

        print()
        print(
            "[WARN] 没有找到《次へ》链接。"
        )


if __name__ == "__main__":
    for _ in range(TIME):
        main()
