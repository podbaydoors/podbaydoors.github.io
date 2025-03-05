#!/usr/bin/env python3
import os
import re
import markdown

def get_correct_case_path(rel_path, base_dir):
    """
    Given a relative path (using "/" as separator) and a base directory,
    this function returns the path with the correct case as on disk.
    If a part cannot be found, it falls back to the original.
    """
    parts = rel_path.split('/')
    current_dir = base_dir
    corrected_parts = []
    for part in parts:
        if not part:
            continue
        try:
            entries = os.listdir(current_dir)
        except Exception:
            return None
        found = None
        for entry in entries:
            if entry.lower() == part.lower():
                found = entry
                break
        if found is None:
            # If not found, leave the part unchanged.
            found = part
        corrected_parts.append(found)
        current_dir = os.path.join(current_dir, found)
    return '/'.join(corrected_parts)

def correct_asset_path(match, base_dir):
    """
    Given a regex match for an asset path, corrects the path to the
    actual case on disk. It handles paths in markdown and HTML tags.
    """
    prefix = match.group("prefix")
    path = match.group("path")
    suffix = match.group("suffix")
    # Do not alter absolute URLs or data URIs.
    if path.startswith(("http://", "https://", "mailto:", "data:")):
        return match.group(0)
    # If the path is absolute (starts with '/'), resolve from the website root.
    if path.startswith("/"):
        new_base = os.getcwd()  # website root
        rel_path = path[1:]
    else:
        new_base = base_dir
        rel_path = path
    corrected = get_correct_case_path(rel_path, new_base)
    if corrected is None:
        corrected = rel_path
    if path.startswith("/"):
        corrected = "/" + corrected
    return prefix + corrected + suffix

def fix_asset_paths_in_markdown(md_content, base_dir):
    """
    Finds asset paths in markdown (both markdown-style links/images and HTML tags)
    and replaces them with the correctly cased version from disk.
    """
    # Process markdown-style links and images: ![alt](path) or [text](path)
    pattern_md = r'(?P<prefix>!?\[[^\]]*\]\()(?P<path>[^)]+)(?P<suffix>\))'
    md_content = re.sub(pattern_md, lambda m: correct_asset_path(m, base_dir), md_content)
    
    # Process HTML tags with src or href attributes.
    pattern_html = r'(?P<prefix>(?:src|href)=["\'])(?P<path>[^"\']+)(?P<suffix>["\'])'
    md_content = re.sub(pattern_html, lambda m: correct_asset_path(m, base_dir), md_content)
    return md_content

def convert_article(article_dir):
    """
    Convert the article's index.md file into index.html.
    - Reads the markdown file and first fixes any asset paths to use correct case.
    - Converts markdown to HTML with the fenced code blocks extension.
    - Prepends a clickable title "pod bay doors" that links back to the main page,
      followed by a light grey horizontal line.
    Returns a tuple (article_number, article_title, relative_link) for use in the main index.
    """
    md_path = os.path.join(article_dir, "index.md")
    if not os.path.exists(md_path):
        print(f"Warning: {md_path} not found.")
        return None

    with open(md_path, "r", encoding="utf-8") as f:
        md_content = f.read()

    # Update asset paths in the markdown to the correct case.
    md_content = fix_asset_paths_in_markdown(md_content, article_dir)

    # Convert markdown to HTML with fenced code blocks enabled.
    html_body = markdown.markdown(md_content, extensions=["fenced_code"])

    # Extract article number and title from the directory name.
    # Expected format: "Number - Article Name"
    dir_name = os.path.basename(article_dir)
    match = re.match(r"(\d+)\s*-\s*(.+)", dir_name)
    if match:
        article_number = int(match.group(1))
        article_title = match.group(2)
    else:
        article_number = 0
        article_title = dir_name

    # Build the complete HTML.
    # The relative path from the article folder (e.g. Articles/ArticleFolder)
    # to the website root is "../../".
    full_html = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>{article_title}</title>
  <link rel="stylesheet" href="../../sakura.css">
</head>
<body>
  <h1><a href="../../index.html">pod bay doors</a></h1>
  <hr style="border: none; border-top: 1px solid lightgrey;">
{html_body}
</body>
</html>
"""
    # Write the HTML file in the same article directory.
    output_path = os.path.join(article_dir, "index.html")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(full_html)

    # Compute a relative link from the website root to this article's index.html.
    rel_link = os.path.relpath(output_path, start=os.getcwd())
    return (article_number, article_title, rel_link)

def generate_root_index(article_info_list):
    """
    Generate the root index.html file that lists all articles in increasing order.
    - The main page includes a clickable "pod bay doors" title (linking to itself)
      with a light grey horizontal separator.
    - The list of articles is built from the article directories.
    """
    article_info_list.sort(key=lambda x: x[0])
    list_items = ""
    for number, title, link in article_info_list:
        list_items += f'  <li><a href="{link}">{title}</a></li>\n'

    # Added inline CSS to modify the hover effect on article links:
    # - When hovered, the background becomes grey.
    # - The text is not underlined.
    index_html = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>pod bay doors</title>
  <link rel="stylesheet" href="sakura.css">
  <style>
    ul {{
    list-style: none;
    padding: 0;  /* Optional: remove default padding */
    }}
    ul li a {{
      display: block;
      padding: 10px 0; /* Adjust vertical padding as needed */
    }}
    ul li a:hover {{
      background-color: rgba(200, 200, 200, 0.2);
      border-bottom: none;
      text-decoration: none;
      color: inherit; /* Keeps the text color the same as the non-hovered state */
    }}
  </style>
</head>
<body>
  <h1><a href="index.html">pod bay doors</a></h1>
  <hr style="border: none; border-top: 1px solid lightgrey;">
  <ul>
{list_items}  </ul>
</body>
</html>
"""
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(index_html)
    print("Generated root index.html")

def main():
    articles_dir = "Articles"
    if not os.path.isdir(articles_dir):
        print(f"Error: The directory '{articles_dir}' does not exist in the website root.")
        return

    article_info = []
    for entry in os.listdir(articles_dir):
        entry_path = os.path.join(articles_dir, entry)
        if os.path.isdir(entry_path):
            info = convert_article(entry_path)
            if info:
                article_info.append(info)

    generate_root_index(article_info)
    print("Website build complete.")

if __name__ == "__main__":
    main()
