import enum
import html
from pathlib import Path

from charset_normalizer import from_path
from ebooklib import epub


class MetaToken(enum.Enum):
    TITLE = '#title'
    AUTHOR = '#author'
    PARAGRAPH = '#p'
    HEADER2 = '##'
    HEADER1 = '#'


class FileParser:
    ParserResult = tuple[MetaToken, str]

    def __init__(self, input_file: str):
        self._file = input_file
        self._encoding = self._guess_encoding()

    def _guess_encoding(self) -> str:
        matches = from_path(self._file)
        if best := matches.best():
            return best.encoding
        return 'UTF-8'

    def _parse_line(self, line: str) -> ParserResult:
        line = line.rstrip()
        for token in MetaToken:
            if line.startswith(token.value):
                content = line.removeprefix(token.value).strip()
                return (token, content)
        return (MetaToken.PARAGRAPH, line)

    def parse(self) -> list[ParserResult]:
        with open(self._file, 'r', encoding=self._encoding) as input_file:
            return [self._parse_line(line) for line in input_file if line]


class BookChapter:
    def __init__(self, title: str):
        self.title = title
        self.content = ''

    def append_html(self, tag: str, content: str):
        escaped = html.escape(content)
        self.content += f'<{tag}>{escaped}</{tag}>\n'

    def export(self) -> epub.EpubHtml:
        return epub.EpubHtml(title=self.title, content=self.content)


class BookSection:
    EpubSection = tuple[epub.Section, list[epub.EpubHtml]]

    def __init__(self, file_name: str):
        self.title = Path(file_name).stem
        self.authors: list[str] = []
        self._file = file_name
        self._chapters: list[BookChapter] = []
        self._parse_file()

    def _add_chapter(self, title: str):
        chapter = BookChapter(title)
        chapter.append_html('h1', title)
        self._chapters.append(chapter)

    def _add_line(self, token: MetaToken, content: str):
        if not content or content.isspace():
            return
        if not self._chapters:
            self._add_chapter(self.title)
        current = self._chapters[-1]
        if token == MetaToken.TITLE:
            self.title = content
        elif token == MetaToken.AUTHOR:
            self.authors.append(content)
        elif token == MetaToken.HEADER1:
            self._add_chapter(content)
        elif token == MetaToken.HEADER2:
            current.append_html('h2', content)
        else:
            current.append_html('p', content)

    def _parse_file(self):
        parser = FileParser(self._file)
        results = parser.parse()
        for token, content in results:
            self._add_line(token, content)

    def export(self) -> EpubSection:
        chapters = [c.export() for c in self._chapters]
        return (epub.Section(self.title), chapters)


class Book:
    def __init__(self, files: list[str] = []):
        self._files = files
        self._sections: list[BookSection] = []
        self.title: str = ''
        self.authors: list[str] = []
        if files:
            self.load(files)

    def load(self, files: list[str]):
        self._files = files
        self._sections = [BookSection(f) for f in files]
        self.title = self._sections[0].title if files else ''
        self.authors = [author for sec in self._sections
                        for author in sec.authors]

    def export(self) -> epub.EpubBook:
        book = epub.EpubBook()
        book.set_title(self.title)
        for author in self.authors:
            book.add_author(author)
        book.toc = [sec.export() for sec in self._sections]
        book.spine = ['nav']
        cid = 0
        for _, htmls in book.toc:
            for html in htmls:
                html.file_name = f'section_{cid:04}.xhtml'
                cid += 1
                book.spine.append(html)  # type: ignore
                book.add_item(html)
        book.add_item(epub.EpubNcx())
        book.add_item(epub.EpubNav())
        return book

    def write(self, file_name: str):
        book = self.export()
        epub.write_epub(file_name, book, {'epub3_pages': False})
