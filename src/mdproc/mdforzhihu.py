import re
import os
import argparse
def main():
    # delete (multi) empty lines before and after img tags
    parser = argparse.ArgumentParser(
        description="Process markdown file for Zhihu."
    )
    parser.add_argument("input_file", help="Path to the input markdown file.")
    args = parser.parse_args()
    input_file = args.input_file
    output_file = f"{os.path.splitext(input_file)[0]}_forzhihu.md"
    with open(input_file, "r", encoding="utf-8") as f:
        lines = f.readlines()
    new_lines = []
    i = 0
    n = len(lines)
    img_tag_count = 0
    removed_empty_count = 0
    while i < n:
        line = lines[i]
        stripped = line.strip()
        if re.match(r"!\[.*?\]\(.*?\)", stripped):
            img_tag_count += 1
            # Remove all empty lines before img tag
            before = len(new_lines)
            while new_lines and new_lines[-1].strip() == "":
                new_lines.pop()
            removed_empty_count += before - len(new_lines)
            new_lines.append(line)
            # Skip all empty lines after img tag
            j = i + 1
            after = 0
            while j < n and lines[j].strip() == "":
                after += 1
                j += 1
            removed_empty_count += after
            i = j
        else:
            new_lines.append(line)
            i += 1

    with open(output_file, "w", encoding="utf-8") as f:
        f.writelines(new_lines)
    print(f"Image tags: {img_tag_count}, removed empty lines: {removed_empty_count}")

if __name__ == "__main__":
    main()