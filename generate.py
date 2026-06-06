import os
import re
import json
import calendar
from pathlib import Path
from typing import Generator
from datetime import datetime
from dataclasses import dataclass


@dataclass
class Page:
    title: str
    month: str
    year: int
    time_to_read: int
    keywords: list[str]
    article: str
    preview: str
    dirname: str

    def __page_init__(self) -> None:
        assert self.month in list(calendar.month_abbr), \
            f"Month '{self.month}' not understood. Please choose from {list(calendar.month_abbr)}"
        assert isinstance(self.year, int) and self.year <= datetime.now().year, \
            f"Year '{self.year}' not understood. Please choose a year before {datetime.now().year + 1}"
        
    @property
    def month_num(self) -> int:
        return list(calendar.month_abbr).index(self.month)


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
    

def list_pages(
        pages_dir: str
        ) -> list[Page]:
    pages = []
    for page in Path(pages_dir).glob("*"):
        meta = read_json(page / "meta.json")
        article = read_file(page / "article.html")
        preview = read_file(page / "preview.html")

        pages.append(
            Page(
                **meta, 
                article=article,
                preview=preview,
                dirname=page.stem
            )
        )

    return sorted(pages, key=lambda p: (p.year, p.month_num), reverse=True)


def load_template(path: Path) -> Template:
    return Template(read_file(path))

def save_html_page(content: str, filepath: Path) -> None:
    if not filepath.parent.exists():
        os.mkdir(filepath.parent)

    with filepath.open(mode='w', encoding='utf-8') as file:
        file.write(content)

def main(
        template_dir: str,
        pages_dir: str,
        output_dir: str
    ) -> None:
    mainpage_template = load_template(Path(template_dir) / ".main.html")
    article_template = load_template(Path(template_dir) / ".article.html")
    preview_template = load_template(Path(template_dir) / ".preview.html")

    # Pages for articles / about
    previews = []
    for page in list_pages(pages_dir):
        print(f"Processing page '{page.title}'")
        page_url = f"{page.dirname}.html"

        try:
            article_html = article_template.render(**page.__dict__)
            article_page_html = mainpage_template.render(content=article_html)
        except Exception as e:
            raise RuntimeError(f"ERROR: {e} in page '{page.title}'")
        
        try:
            preview_html = preview_template.render(
                **page.__dict__,
                page_url=page_url
                )
        except Exception as e:
            raise RuntimeError(f"ERROR: {e} in page '{page.title}'")
        
        save_html_page(article_page_html, Path(output_dir) / page_url)

        previews.append(preview_html)

    # Main page (index.html)
    print(f"Processing 'index.html'")

    try:
        index_html = mainpage_template.render(content="\n".join(previews))
    except Exception as e:
        raise RuntimeError(f"ERROR: {e} in generating index.html")
    
    index_path = Path(output_dir) / "index.html"
    save_html_page(index_html, index_path)

    print("Done!")



if __name__ == '__main__':
    main(
        template_dir="templates",
        pages_dir="pages",
        output_dir="output"
    )