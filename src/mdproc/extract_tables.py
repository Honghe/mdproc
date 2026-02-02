from markdown_it import MarkdownIt


def extract_raw_tables(md_text):
    """
    Extracts the raw markdown strings of tables from a given markdown text.
    """
    # Configure the parser to enable tables (GFM-like is a good preset)
    md = MarkdownIt("gfm-like", {"linkify": False}).enable("table")

    # Parse the markdown into tokens
    tokens = md.parse(md_text, {})

    raw_tables = []
    current_table_start = None

    for i, token in enumerate(tokens):
        if token.type == "table_open":
            # Store the starting line number if source map is available
            if token.map:
                current_table_start = token.map[0]

        if token.type == "table_close":
            # If we have a start, extract the lines up to the end line number
            if current_table_start is not None and token.map:
                current_table_end = token.map[1]
                # Extract the relevant lines from the original text
                table_lines = md_text.splitlines()[
                    current_table_start:current_table_end
                ]
                raw_tables.append("\n".join(table_lines))
                current_table_start = None

    return raw_tables


def main():
    # Example usage:
    markdown_content = """
    Here is some introductory text.

    | Header 1 | Header 2 |
    |---|---|
    | Cell 1 | Cell 2 |
    | Cell 3 | Cell 4 |

    Some text in between.

    | Name | Age |
    |---|---|
    | Alice | 30 |
    | Bob | 25 |
    """

    tables = extract_raw_tables(markdown_content)

    for i, table_str in enumerate(tables):
        print(f"--- Table {i + 1} Raw String ---")
        print(table_str)
        print("----------------------------\n")


if __name__ == "__main__":
    main()
