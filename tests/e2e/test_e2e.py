import pathlib
import pytest
import yaml

from bs4 import BeautifulSoup

from mau.environment.environment import Environment
from mau.nodes.page import DocumentNode
from mau.lexers.main_lexer import MainLexer
from mau.parsers.main_parser import MainParser

from mau.test_helpers import (
    init_parser_factory,
    parser_runner_factory,
    collect_test_files,
)

from mau_html_visitor import HtmlVisitor

init_parser = init_parser_factory(MainLexer, MainParser)

runner = parser_runner_factory(MainLexer, MainParser)

tests_dir = pathlib.Path(__file__).parent

tst_files = collect_test_files(tests_dir, "source", "mau", "expected", "html")


@pytest.mark.parametrize("source,expected", tst_files)
def test_e2e(source, expected):
    with open(source, encoding="utf-8") as source_file:
        source_code = source_file.read()

    with open(expected, encoding="utf-8") as expected_file:
        expected_code = expected_file.read()
        # Remove the trailing newline
        expected_code = expected_code.rstrip()

    parser = runner(source_code)

    node = DocumentNode(children=parser.nodes)
    visitor = HtmlVisitor(Environment())
    result = visitor.visit(node)

    result_soup = BeautifulSoup(result, "html.parser")
    result_expected = BeautifulSoup(expected_code, "html.parser")

    assert (
        result_soup.prettify().splitlines() == result_expected.prettify().splitlines()
    )
