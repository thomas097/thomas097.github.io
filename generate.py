import os
import re
import json
import calendar
from pathlib import Path
from typing import Generator
from datetime import datetime
from dataclasses import dataclass


@dataclass
class Post:
    title: str
    month: str
    year: int
    time_to_read: int
    keywords: list[str]
    article: str
    preview: str
    dirname: str

    def __post_init__(self) -> None:
        assert self.month in list(calendar.month_abbr), \
            f"Month '{self.month}' not understood. Please choose from {list(calendar.month_abbr)}"
        assert isinstance(self.year, int) and self.year <= datetime.now().year, \
            f"Year '{self.year}' not understood. Please choose a year before {datetime.now().year + 1}"


@dataclass
class Template:
    content: str

    def render(self, _strict: bool = True, **kwargs) -> str:
        content = self.content
        for key, value in kwargs.items():
            if isinstance(value, list):
                value_fmt = ' | '.join(value)
            else:
                value_fmt = str(value)

            content = content.replace('{{' + key + '}}', value_fmt)

        # Check whether there are any fields left
        if _strict:
            left_overs = re.findall(r"\{\{([^\}]+)\}\}", content)
            assert not left_overs, \
                f"Failed to render. The following fields were left uninitialized: {left_overs}"

        return content


def read_file(path: Path) -> str:
    assert path.is_file(), \
        f"File not found: '{path}'"
    return path.open(encoding="utf-8").read()


def read_json(path: Path) -> dict:
    return json.loads(read_file(path))
    

def list_posts(
        posts_dir: str
        ) -> Generator[Post]:
    for post in Path(posts_dir).glob("*"):
        meta = read_json(post / "meta.json")
        article = read_file(post / "article.html")
        preview = read_file(post / "preview.html")

        yield Post(
            **meta, 
            article=article,
            preview=preview,
            dirname=post.stem
            )


def load_template(path: Path) -> Template:
    return Template(read_file(path))

def save_html_page(content: str, filepath: Path) -> None:
    if not filepath.parent.exists():
        os.mkdir(filepath.parent)

    with filepath.open(mode='w', encoding='utf-8') as file:
        file.write(content)

def main(
        template_dir: str,
        posts_dir: str,
        output_dir: str
    ) -> None:
    mainpage_template = load_template(Path(template_dir) / ".main.html")
    article_template = load_template(Path(template_dir) / ".article.html")
    preview_template = load_template(Path(template_dir) / ".preview.html")

    # Generate pages for articles
    previews = []
    for post in list_posts(posts_dir):
        print(f"Processing post '{post.title}'")
        post_page_url = f"{post.dirname}.html"

        try:
            article_html = article_template.render(**post.__dict__)
            article_page_html = mainpage_template.render(content=article_html)
        except Exception as e:
            raise RuntimeError(f"ERROR: {e} in post '{post.title}'")
        
        try:
            preview_html = preview_template.render(
                **post.__dict__,
                post_page_url=post_page_url
                )
        except Exception as e:
            raise RuntimeError(f"ERROR: {e} in post '{post.title}'")
        
        save_html_page(article_page_html, Path("output") / post_page_url)

        previews.append(preview_html)

    # Generate main page (index)
    try:
        index_html = mainpage_template.render(content="\n".join(previews))
    except Exception as e:
        raise RuntimeError(f"ERROR: {e} in generating index.html")
    
    index_path = Path("output") / "index.html"
    save_html_page(index_html, index_path)



if __name__ == '__main__':
    main(
        template_dir="templates",
        posts_dir="posts",
        output_dir="output"
    )