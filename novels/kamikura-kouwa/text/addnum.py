import re
from pathlib import Path


# ============================================================
# 配置
# ============================================================

# "add"    = 添加序号
# "remove" = 移除序号
MODE = "remove"

# ============================================================


CURRENT_DIR = Path(__file__).parent


def add_numbers(input_file):
    """添加序号"""

    with input_file.open("r", encoding="utf-8") as f:
        lines = f.readlines()

    total = len(lines)

    # 序号至少三位：001、002……
    digits = max(3, len(str(total)))

    new_lines = []

    for i, line in enumerate(lines, start=1):
        new_lines.append(
            f"{i:0{digits}d} {line}"
        )

    # 输出为 A01-jp.txt
    output_file = input_file.with_name(
        "A" + input_file.name
    )

    with output_file.open(
        "w",
        encoding="utf-8",
        newline=""
    ) as f:
        f.writelines(new_lines)

    print(
        f"[完成] {input_file.name} → {output_file.name}"
    )


def remove_numbers(input_file):
    """移除行首序号，直接覆盖原文件"""

    with input_file.open("r", encoding="utf-8") as f:
        lines = f.readlines()

    new_lines = []

    for line in lines:

        # 只删除行首数字
        #
        # 001 测试
        # ↓
        #  测试
        #
        # 后面的空格会保留
        new_line = re.sub(
            r"^\d+",
            "",
            line
        )

        new_lines.append(new_line)

    # 直接覆盖原文件
    with input_file.open(
        "w",
        encoding="utf-8",
        newline=""
    ) as f:
        f.writelines(new_lines)

    print(
        f"[完成并覆盖] {input_file.name}"
    )


def main():

    print("=" * 60)
    print(f"当前模式：{MODE}")
    print("=" * 60)

    files = []

    # ========================================================
    # 添加模式：扫描 01-jp.txt
    # ========================================================

    if MODE == "add":

        pattern = r"\d+-jp\.txt"

        for file in CURRENT_DIR.glob("*-jp.txt"):

            # 只匹配纯数字开头
            # 01-jp.txt
            # 02-jp.txt
            #
            # 不匹配 A01-jp.txt
            if re.fullmatch(pattern, file.name):
                files.append(file)

        files.sort(
            key=lambda x: int(
                re.match(
                    r"(\d+)-jp\.txt",
                    x.name
                ).group(1)
            )
        )

        if not files:
            print("没有找到类似 01-jp.txt 的文件！")
            return

        print(f"找到 {len(files)} 个 jp 文件\n")

        for file in files:
            add_numbers(file)

    # ========================================================
    # 移除模式：扫描 01-zh.txt
    # ========================================================

    elif MODE == "remove":

        pattern = r"\d+-zh\.txt"

        for file in CURRENT_DIR.glob("*-zh.txt"):

            # 只匹配：
            # 01-zh.txt
            # 02-zh.txt
            #
            # 不匹配其他文件
            if re.fullmatch(pattern, file.name):
                files.append(file)

        files.sort(
            key=lambda x: int(
                re.match(
                    r"(\d+)-zh\.txt",
                    x.name
                ).group(1)
            )
        )

        if not files:
            print("没有找到类似 01-zh.txt 的文件！")
            return

        print(f"找到 {len(files)} 个 zh 文件\n")

        for file in files:
            remove_numbers(file)

    else:

        raise ValueError(
            'MODE 只能是 "add" 或 "remove"'
        )

    print("\n" + "=" * 60)
    print("全部处理完成")
    print("=" * 60)


if __name__ == "__main__":
    main()