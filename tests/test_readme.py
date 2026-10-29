"""Run every ```python block in README.md as a doctest so the examples stay true.

Blocks share one namespace, in order, the same way a reader would type them.
"""

from __future__ import annotations

import doctest
import re
from pathlib import Path

README = Path(__file__).resolve().parent.parent / "README.md"
BLOCKS = re.findall(r"```python\n(.*?)```", README.read_text(encoding="utf-8"), re.DOTALL)


def test_readme_examples() -> None:
    assert len(BLOCKS) >= 5
    globs: dict[str, object] = {}
    parser = doctest.DocTestParser()
    runner = doctest.DocTestRunner(optionflags=doctest.ELLIPSIS)
    for index, block in enumerate(BLOCKS):
        test = parser.get_doctest(block, globs, f"README block {index}", str(README), 0)
        result = runner.run(test, clear_globs=False)
        globs.update(test.globs)  # get_doctest() copies globs; carry imports forward
        assert result.failed == 0, f"README python block {index} failed"
