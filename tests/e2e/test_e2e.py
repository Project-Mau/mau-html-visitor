from pathlib import Path

import pytest

from bs4 import BeautifulSoup

from mau import Mau
from mau.test_helpers import NullMessageHandler

from mau_html_visitor import HtmlVisitor

# End-to-end tests that exercise the full Mau
# pipeline (lexer -> parser -> HTML visitor)
# on real `.mau` source files stored in `cases/`.
#
# Each `.mau` file has a companion `.html`
# reference. The test processes the source
# and asserts that the output matches the
# reference (compared via BeautifulSoup to
# ignore insignificant whitespace differences).
#
# Run with `--update-e2e-refs` to regenerate
# every reference file from the current output.

CASES_DIR = Path(__file__).parent / "cases"


def discover_cases():
    cases = []
    for mau_path in sorted(CASES_DIR.glob("*.mau")):
        html_path = mau_path.with_suffix(".html")
        cases.append(pytest.param(mau_path, html_path, id=mau_path.stem))
    return cases


@pytest.mark.parametrize("mau_path,html_path", discover_cases())
def test_e2e(mau_path, html_path, request):
    source = mau_path.read_text()

    mau = Mau(NullMessageHandler())
    result = mau.process(HtmlVisitor, source, str(mau_path))

    if request.config.getoption("--update-e2e-refs"):
        html_path.write_text(result + "\n")
        pytest.skip("reference updated")

    if not html_path.exists():
        pytest.fail(
            f"Reference file {html_path.name} not found. "
            f"Run with --update-e2e-refs to generate it."
        )

    expected = html_path.read_text().rstrip()

    result_soup = BeautifulSoup(result, "html.parser")
    expected_soup = BeautifulSoup(expected, "html.parser")

    assert result_soup.prettify() == expected_soup.prettify()
