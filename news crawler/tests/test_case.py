import re, sys, pathlib
import pytest
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from generate_case import parse_case, ALLOWED, N_QUESTIONS

VALID = '''{
  "title": "Case: The Lighthouse Keeper",
  "article": {"headline": "Keeper found dead", "text": "A body was found at the lighthouse last night."},
  "questions": [
    {"object": "Dead body", "question": "How did he die?", "options": ["A", "B", "C", "D"], "answer": 0},
    {"object": "Picture", "question": "Who is pictured?", "options": ["A", "B", "C", "D"], "answer": 1},
    {"object": "Chair", "question": "What was on the chair?", "options": ["A", "B", "C", "D"], "answer": 2},
    {"object": "Bookshelf", "question": "What book was missing?", "options": ["A", "B", "C", "D"], "answer": 3},
    {"object": "Night window", "question": "What was seen?", "options": ["A", "B", "C", "D"], "answer": 0}
  ],
  "solution": "He was poisoned.",
  "key_terms": ["poisoned", "keeper"]
}'''


def test_parse_case_valid_with_noise():
    case = parse_case('blah blah ' + VALID + ' trailing text')
    assert len(case["questions"]) == N_QUESTIONS
    assert case["questions"][0]["object"] == "Dead body"
    assert case["questions"][0]["answer"] == 0
    assert case["solution"]


def test_parse_case_rejects_duplicate_objects():
    bad = VALID.replace('"Picture"', '"Dead body"')
    with pytest.raises(ValueError):
        parse_case(bad)


def test_parse_case_rejects_bad_object():
    bad = VALID.replace('"Picture"', '"Lamp"')
    with pytest.raises(ValueError):
        parse_case(bad)


def test_parse_case_rejects_wrong_count():
    bad = VALID.replace('"object": "Night window", "question": "What was seen?", "options": ["A", "B", "C", "D"], "answer": 0', '')
    with pytest.raises(ValueError):
        parse_case(bad)


def test_parse_case_rejects_no_json():
    with pytest.raises(ValueError):
        parse_case("no json here")


def test_allowed_labels_match_game():
    assert set(ALLOWED) == {"Dead body", "Papers (rug)", "Picture", "Chair", "Bookshelf", "Night window"}
