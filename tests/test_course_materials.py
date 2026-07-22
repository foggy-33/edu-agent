from pathlib import Path

from app.courses.materials import CourseMaterialService


def test_courseware_chapter_metadata() -> None:
    assert CourseMaterialService._chapter_metadata(Path("5版PPT第10章.pdf")) == (10, None)
    assert CourseMaterialService._chapter_metadata(Path("5版PPT第3章（2）.pdf")) == (3, 2)
    assert CourseMaterialService._chapter_metadata(Path("补充资料.pdf")) == (None, None)
