import re, sys, pathlib
import pytest
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from fetch_news import clean_text, split_sentences
from label_news import parse_labels


def test_clean_text_strips_html_and_collapses_ws():
    t = "Hello  <b>world</b>&nbsp; again\n\n  next"
    out = clean_text(t)
    assert out == "Hello world again\n\nnext"


def test_clean_text_removes_ellipsis():
    assert clean_text("The story continues...\nMore...") == "The story continues\nMore"


def test_split_sentences_abbr_not_split():
    sents = split_sentences("Mr. Smith went home. He slept.")
    assert sents == ["Mr. Smith went home.", "He slept."]


def test_split_sentences_quotes():
    sents = split_sentences('He said "hi." Next sentence.')
    assert sents == ['He said "hi."', "Next sentence."]


def test_split_sentences_newlines():
    sents = split_sentences("First para line.\n\nSecond para line.")
    assert sents == ["First para line.", "Second para line."]


def test_parse_labels_ok():
    txt = 'blah [{"id":1,"label":0},{"id":2,"label":1}] end'
    assert parse_labels(txt, 2) == [0, 1]


def test_parse_labels_missing_id_raises():
    with pytest.raises(ValueError):
        parse_labels('[{"id":1,"label":0}]', 2)


def test_assign_splits_ratios_and_article_level():
    from merge_data import assign_splits
    arts = [(i, "catA" if i % 2 else "catB") for i in range(1, 101)]
    sp = assign_splits(arts)
    vals = list(sp.values())
    assert abs(vals.count("train") / 100 - 0.8) <= 0.05
    assert abs(vals.count("val") / 100 - 0.1) <= 0.03
    assert abs(vals.count("test") / 100 - 0.1) <= 0.03
    assert assign_splits(arts) == sp


def test_merge_rejects_duplicate_urls_and_keeps_base_rows():
    import pandas as pd, pathlib
    base = pd.DataFrame([dict(article_id=1, url="http://x.com/a", title="t",
                              id="", author="", published="", category="w",
                              language="en", source="s", split="train",
                              sent_idx=1, sentence="hello", sentence_label=0,
                              source_file="a.csv")])
    new = pd.DataFrame([dict(article_id=2, url="http://x.com/a", title="t2",
                             id="", author="", published="", category="w",
                             language="en", source="s", split="", sent_idx=1,
                             sentence="hi", sentence_label=1, source_file="b.csv")])
    p1 = pathlib.Path("tests/_tmp_base.csv")
    p2 = pathlib.Path("tests/_tmp_new.csv")
    base.to_csv(p1, index=False)
    new.to_csv(p2, index=False)
    try:
        from merge_data import merge
        out = merge(str(p1), str(p2))
        assert out.article_id.max() == 1
        assert len(out) == 1
    finally:
        p1.unlink()
        p2.unlink()
