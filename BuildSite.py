#!/usr/bin/env python3
import os
import re
import markdown

def convert_article(article_dir):
    """
    Convert the article's index.md file into index.html.
    The generated HTML file links to the sakura.css in the website root using a relative path.
    It returns a tuple (article_number, article_title, relative_link) for use in the main index.
    """
    md_path = os.path.join(article_dir, "index.md")
    if not os.path.exists(md_path):
        print(f"Warning: {md_path} not found.")
        return None

    with open(md_path, "r", encoding="utf-8") as f:
        md_content = f.read()

    # Convert markdown to HTML with fenced code blocks enabled
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
    # Note: Since index.html is created in the article folder ("Articles/ArticleFolder"),
    # the relative path from that location to the root is two levels up ("../../sakura.css").
    full_html = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>{article_title}</title>
  <link rel="stylesheet" href="../../sakura.css">
</head>
<body>
{html_body}
</body>
</html>
"""
    # Write the HTML to index.html in the same article directory.
    output_path = os.path.join(article_dir, "index.html")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(full_html)

    # Compute a relative link from the website root to the article index.html.
    rel_link = os.path.relpath(output_path, start=os.getcwd())
    return (article_number, article_title, rel_link)

def generate_root_index(article_info_list):
    """
    Generate the root index.html file that lists all articles in increasing order.
    Each article is linked to its generated index.html.
    The link text is the article name (with the number and dash removed).
    """
    # Sort the articles by their number
    article_info_list.sort(key=lambda x: x[0])

    # Build the list of article links.
    list_items = ""
    for number, title, link in article_info_list:
        list_items += f'  <li><a href="{link}">{title}</a></li>\n'

    # The root index.html links directly to sakura.css (located in the root).
    index_html = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>Articles</title>
  <link rel="stylesheet" href="sakura.css">
</head>
<body>
  <h1>Articles</h1>
  <ul>
{list_items}  </ul>
</body>
</html>
"""
    # Write the root index.html file.
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(index_html)
    print("Generated root index.html")

def main():
    articles_dir = "Articles"
    if not os.path.isdir(articles_dir):
        print(f"Error: The directory '{articles_dir}' does not exist in the website root.")
        return

    article_info = []
    # Process each article directory in "Articles"
    for entry in os.listdir(articles_dir):
        entry_path = os.path.join(articles_dir, entry)
        if os.path.isdir(entry_path):
            info = convert_article(entry_path)
            if info:
                article_info.append(info)

    # Generate the root index.html linking to all articles.
    generate_root_index(article_info)
    print("Website build complete.")

if __name__ == "__main__":
    main()
