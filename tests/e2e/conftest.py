def pytest_addoption(parser):
    parser.addoption(
        "--update-e2e-refs",
        action="store_true",
        default=False,
        help="Regenerate e2e HTML reference files from current output.",
    )
