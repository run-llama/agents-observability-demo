import pytest

from src.agents_observability_demo.models import Syllabus
from pydantic_core import ValidationError


def test_syllabus_model() -> None:
    s1 = Syllabus(
        course_name="English Literature",
        teaching_languages=["English"],
        summary="Some summary.",
        course_year=1,
    )
    assert s1.keywords == []
    assert s1.learning_objectives == []
    assert s1.evaluation_method is None
    with pytest.raises(ValidationError):
        Syllabus(
            course_name="Some name",
            teaching_languages=["Italian"],
            summary="Hello",
            course_year=7,
        )
