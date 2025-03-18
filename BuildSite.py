#!/usr/bin/env python3
import os
import re
import markdown
from datetime import datetime

SITE_TITLE_FONT = """<link rel='preconnect' href='https://fonts.googleapis.com'>
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
    Returns a tuple (sortable_date, display_date, article_title, relative_link) for use in the main index.
    
    Expected directory name format: "YY MM DD - Article Title"
    For example, "25 03 9 - Article Title" corresponds to Mar 9 2025.
    """
    md_path = os.path.join(article_dir, "index.md")
    if not os.path.exists(md_path):
        print(f"Warning: {md_path} not found.")
        return None

    with open(md_path, "r", encoding="utf-8") as f:
        md_content = f.read()

    md_content = fix_asset_paths_in_markdown(md_content, article_dir)
    html_body = markdown.markdown(md_content, extensions=["fenced_code", "codehilite"])

    # Try to extract the date and title from the directory name.
    # Expected format: "YY MM DD - Article Title" (e.g. "25 03 9 - Article Title")
    dir_name = os.path.basename(article_dir)
    match = re.match(r"(\d{2})\s+(\d{2})\s+(\d{1,2})\s*-\s*(.+)", dir_name)
    if match:
        year_str, month_str, day_str, article_title = match.groups()
        try:
            full_year = 2000 + int(year_str)
            dt = datetime(full_year, int(month_str), int(day_str))
            sortable_date = dt.strftime("%Y-%m-%d")
            # Format display date as "MMM D YYYY" (e.g. "Mar 9 2025")
            display_date = dt.strftime("%b %d %Y").replace(" 0", " ")
        except Exception:
            sortable_date = "0000-00-00"
            display_date = "0000-00-00"
    else:
        # Fallback: try splitting by " - " and then process the date part.
        parts = dir_name.split(" - ", 1)
        if len(parts) == 2:
            date_part, article_title = parts
            try:
                date_parts = date_part.split()
                if len(date_parts) >= 3:
                    year_str, month_str, day_str = date_parts[:3]
                    full_year = 2000 + int(year_str)
                    dt = datetime(full_year, int(month_str), int(day_str))
                    sortable_date = dt.strftime("%Y-%m-%d")
                    display_date = dt.strftime("%b %d %Y").replace(" 0", " ")
                else:
                    sortable_date = "0000-00-00"
                    display_date = "0000-00-00"
            except Exception:
                sortable_date = "0000-00-00"
                display_date = "0000-00-00"
        else:
            sortable_date = "0000-00-00"
            display_date = "0000-00-00"
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
  <div class="site-title">
    <h1><a href="../../index.html">pod bay doors</a></h1>
  </div>
  {html_body}
  <hr class="article-end-line">
</body>
</html>
"""
    output_path = os.path.join(article_dir, "index.html")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(full_html)

    rel_link = os.path.relpath(output_path, start=os.getcwd())
    return (sortable_date, display_date, article_title, rel_link)

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
  <div class="site-title">
    <h1><a href="../../index.html">pod bay doors</a></h1>
  </div>
  {html_body}
  <hr class="article-end-line">
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

def convert_about():
    """
    Convert the about.md file (located in the 'about' subdirectory) into an HTML page.
    The generated HTML (index.html) is saved in the same subdirectory, using the same styling as articles.
    """
    about_dir = "About"
    about_md = os.path.join(about_dir, "index.md")
    if not os.path.exists(about_md):
        print("Warning: index.md not found in the 'about' directory.")
        return
    with open(about_md, "r", encoding="utf-8") as f:
        md_content = f.read()
    md_content = fix_asset_paths_in_markdown(md_content, about_dir)
    html_body = markdown.markdown(md_content, extensions=["fenced_code", "codehilite"])
    page_title = "About"
    full_html = f"""<!DOCTYPE html>
<html>
<head>
  {SITE_TITLE_FONT}
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{page_title}</title>
  <link rel="stylesheet" href="../style.css">
  <link rel="stylesheet" href="../pygments.css">
</head>
<body>
  <div class="site-title">
    <h1><a href="../index.html">pod bay doors</a></h1>
  </div>
  {html_body}
  <hr class="article-end-line">
</body>
</html>
"""
    output_path = os.path.join(about_dir, "index.html")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(full_html)
    print("Generated about/index.html")

def generate_main_index(article_info_list, program_info_list):
    """
    Generate the root index.html that lists all programs (with image links) first and then articles (text links)
    in two separate sections. Articles are sorted by date.
    """
    # Sort articles by the sortable date (YYYY-MM-DD)
    article_info_list.sort(key=lambda x: x[0])
    program_info_list.sort(key=lambda x: x[0])
    program_list_items = ""
    for number, title, screenshot_link, page_link in program_info_list:
        program_list_items += (
            f'  <li class="post">'
            f'<a href="{page_link}" class="program-thumb">'
            f'<img src="{screenshot_link}" alt="{title}"></a>\n'
            f'<a href="{page_link}" class="program-name">{title}</a>'
            f'</li>\n'
        )
    article_list_items = ""
    for sortable_date, display_date, title, link in article_info_list:
        article_list_items += (
            f'  <li class="post">'
            f'<small style="font-size: 0.7em; color: #777; display:block; margin-bottom:0px;">{display_date}</small>'
            f'<a href="{link}">{title}</a></li>\n'
        )

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
    .program-thumb {{
      display: inline-block;
      width: 14rem;
      height: 7rem;
      overflow: hidden;
      font-size: 0;
    }}
    .program-thumb img {{
      width: 100%;
      height: 100%;
    }}
    .program-thumb:hover img {{
      filter: brightness(0.8);
      transition: filter 0.3s ease;
    }}
  </style>
</head>
<body>
  <div class="site-title">
    <h1>pod bay doors</h1>
    <h1><a href="About/index.html">about</a></h1>
  </div>
  <h3 style="margin-bottom: .3rem;">Programs</h3>
  <hr style="border: none; border-top: 1px solid lightgrey;">
  <ul class="posts">
    {program_list_items}  
  </ul>
  <h3 style="margin-bottom: .3rem;">Articles</h3>
  <hr style="border: none; border-top: 1px solid lightgrey;">
  <ul class="posts">
    {article_list_items}  
  </ul>
</body>
</html>
"""
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(index_html)
    print("Generated root index.html")

def main():
    # Convert about/about.md if it exists.
    convert_about()

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
