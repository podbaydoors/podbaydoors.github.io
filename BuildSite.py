#!/usr/bin/env python3
import os
import re
import markdown

SITE_TITLE_FONT =  """<link rel='preconnect' href='https://fonts.googleapis.com'>
                      <link rel='preconnect' href='https://fonts.gstatic.com' crossorigin>
                      <link href='https://fonts.googleapis.com/css2?family=Gruppo&display=swap' rel='stylesheet'>"""

def get_correct_case_path(rel_path, base_dir):
    """
    Given a relative path and a base directory, return the path with the correct case as on disk.
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
            found = part
        corrected_parts.append(found)
        current_dir = os.path.join(current_dir, found)
    return '/'.join(corrected_parts)

def correct_asset_path(match, base_dir):
    """
    Correct asset paths found in markdown or HTML to use the proper casing.
    """
    prefix = match.group("prefix")
    path = match.group("path")
    suffix = match.group("suffix")
    # Do not alter absolute URLs or data URIs.
    if path.startswith(("http://", "https://", "mailto:", "data:")):
        return match.group(0)
    # For absolute paths starting with '/', resolve from the website root.
    if path.startswith("/"):
        new_base = os.getcwd()
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
    Update asset paths in markdown content to use the correct case from disk.
    """
    # Process markdown-style links and images.
    pattern_md = r'(?P<prefix>!?\[[^\]]*\]\()(?P<path>[^)]+)(?P<suffix>\))'
    md_content = re.sub(pattern_md, lambda m: correct_asset_path(m, base_dir), md_content)
    
    # Process HTML tags with src or href attributes.
    pattern_html = r'(?P<prefix>(?:src|href)=["\'])(?P<path>[^"\']+)(?P<suffix>["\'])'
    md_content = re.sub(pattern_html, lambda m: correct_asset_path(m, base_dir), md_content)
    return md_content

def convert_article(article_dir):
    """
    Convert an article page (from index.md) into index.html.
    Returns a tuple (article_number, article_title, relative_link) for use in the main index.
    """
    md_path = os.path.join(article_dir, "index.md")
    if not os.path.exists(md_path):
        print(f"Warning: {md_path} not found.")
        return None

    with open(md_path, "r", encoding="utf-8") as f:
        md_content = f.read()

    md_content = fix_asset_paths_in_markdown(md_content, article_dir)
    html_body = markdown.markdown(md_content, extensions=["fenced_code", "codehilite"])

    # Extract article number and title from the directory name ("Number - Article Name").
    dir_name = os.path.basename(article_dir)
    match = re.match(r"(\d+)\s*-\s*(.+)", dir_name)
    if match:
        article_number = int(match.group(1))
        article_title = match.group(2)
    else:
        article_number = 0
        article_title = dir_name

    full_html = f"""<!DOCTYPE html>
<html>
<head>
  {SITE_TITLE_FONT}
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{article_title}</title>
  <link rel="stylesheet" href="../../style.css">
  <link rel="stylesheet" href="../../pygments.css">
</head>
<body>
  <h1 class="site-title"><a href="../../index.html" style="color: inherit; text-decoration: none; font-family: inherit;">pod bay doors</a></h1>
  <hr style="border: none; border-top: 1px solid lightgrey;">
{html_body}
</body>
</html>
"""
    output_path = os.path.join(article_dir, "index.html")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(full_html)

    rel_link = os.path.relpath(output_path, start=os.getcwd())
    return (article_number, article_title, rel_link)

def convert_program(program_dir):
    """
    Convert a program page (from index.md) into index.html.
    Also, compute the relative path to the screenshot image (screenshot.jpg)
    which will be used as the clickable link on the main page.
    Returns a tuple (program_number, program_title, screenshot_rel_link, page_rel_link).
    """
    md_path = os.path.join(program_dir, "index.md")
    if not os.path.exists(md_path):
        print(f"Warning: {md_path} not found in {program_dir}.")
        return None

    with open(md_path, "r", encoding="utf-8") as f:
        md_content = f.read()

    md_content = fix_asset_paths_in_markdown(md_content, program_dir)
    html_body = markdown.markdown(md_content, extensions=["fenced_code", "codehilite"])

    # Extract program number and title from the directory name ("Number - Program Name").
    dir_name = os.path.basename(program_dir)
    match = re.match(r"(\d+)\s*-\s*(.+)", dir_name)
    if match:
        program_number = int(match.group(1))
        program_title = match.group(2)
    else:
        program_number = 0
        program_title = dir_name

    full_html = f"""<!DOCTYPE html>
<html>
<head>
  {SITE_TITLE_FONT}
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{program_title}</title>
  <link rel="stylesheet" href="../../style.css">
  <link rel="stylesheet" href="../../pygments.css">
</head>
<body>
  <h1 class="site-title"><a href="../../index.html" style="color: inherit; text-decoration: none; font-family: inherit;">pod bay doors</a></h1>
  <hr style="border: none; border-top: 1px solid lightgrey;">
{html_body}
</body>
</html>
"""
    output_path = os.path.join(program_dir, "index.html")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(full_html)

    rel_link = os.path.relpath(output_path, start=os.getcwd())
    screenshot_path = os.path.join(program_dir, "screenshot.jpg")
    rel_screenshot = os.path.relpath(screenshot_path, start=os.getcwd())
    return (program_number, program_title, rel_screenshot, rel_link)

def generate_main_index(article_info_list, program_info_list):
    """
    Generate the root index.html that lists all programs (with image links) first and then articles (text links)
    in two separate sections. Both lists are ordered in increasing number order.
    The program screenshots are displayed as thumbnails in fixed-size containers.
    """
    article_info_list.sort(key=lambda x: x[0])
    program_info_list.sort(key=lambda x: x[0])
    program_list_items = ""
    for number, title, screenshot_link, page_link in program_info_list:
        program_list_items += (
            f'  <li class="post"><a href="{page_link}" class="program-thumb">'
            f'<img src="{screenshot_link}" alt="{title}"></a></li>\n'
        )
    article_list_items = ""
    for number, title, link in article_info_list:
        article_list_items += f'  <li class="post"><a href="{link}">{title}</a></li>\n'

    index_html = f"""<!DOCTYPE html>
<html>
<head>
  {SITE_TITLE_FONT}
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>pod bay doors</title>
  <link rel="stylesheet" href="style.css">
  <link rel="stylesheet" href="pygments.css">
  <style>
    ul {{
      list-style: none;
      padding: 0;
    }}
    ul li a {{
      display: block;
      padding: 10px 0;
    }}
    ul li a:hover {{
      background-color: rgba(200, 200, 200, 0.2);
      border-bottom: none;
      text-decoration: none;
      color: inherit;
    }}
    /* Program screenshot thumbnail styles:
       Each link will be in a fixed-size container ensuring uniform appearance */
    .program-thumb {{
      display: inline-block;
      width: 250px;
      height: 250px;
      overflow: hidden;
    }}
    .program-thumb img {{
      width: 100%;
      height: 100%;
      object-fit: cover;
    }}
  </style>
</head>
<body>
  <h1 class="site-title">pod bay doors</h1>
  <hr style="border: none; border-top: 1px solid lightgrey;">
  <ul class="posts">
{program_list_items}  </ul>
  <hr style="border: none; border-top: 1px solid lightgrey;">
  <ul class="posts">
{article_list_items}  </ul>
</body>
</html>
"""
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(index_html)
    print("Generated root index.html")

def main():
    article_info = []
    articles_dir = "Articles"
    if os.path.isdir(articles_dir):
        for entry in os.listdir(articles_dir):
            entry_path = os.path.join(articles_dir, entry)
            if os.path.isdir(entry_path):
                info = convert_article(entry_path)
                if info:
                    article_info.append(info)
    else:
        print(f"Warning: The directory '{articles_dir}' does not exist.")

    program_info = []
    programs_dir = "Programs"
    if os.path.isdir(programs_dir):
        for entry in os.listdir(programs_dir):
            entry_path = os.path.join(programs_dir, entry)
            if os.path.isdir(entry_path):
                info = convert_program(entry_path)
                if info:
                    program_info.append(info)
    else:
        print(f"Note: The directory '{programs_dir}' does not exist. Skipping program pages.")

    generate_main_index(article_info, program_info)
    print("Website build complete.")

if __name__ == "__main__":
    main()
