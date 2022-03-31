# test_handler.py
from asyncio import events
from calendar import c
import boto3
import pytest
import handler
import json


def load_sample_event(path):
    # helper function for loading sample events from repo
    with open(path, "r") as ef:
        return json.load(ef)


## Test Setup Functions
def test_callback():
    testBody = {"msg": "Error1", "Content": "Content1"}

    # Check correct callback http code
    resp = handler.callback(404, testBody)
    assert resp["statusCode"] == 404
    assert resp["statusCode"] != 202

    # Check for correct json parsing and stringiying
    body_resp = json.loads(resp["body"])
    assert body_resp["msg"] == "Error1"
    assert body_resp["Content"] == "Content1"


def test_validate_post_json():
    sample_post = {
        "title": "Title1",
        "date": "Date1",
        "author": "Author1",
        "content": "Content1",
    }
    sample_post1 = {
        "title": "Title1",
        "date": "Date1",
        "author": "Author1",
        "Content": "Content1",
    }
    sample_post2 = {
        "date": "Date1",
        "author": "Author1",
        "content": "Content1",
    }

    assert handler.validate_post_json(sample_post) == True
    assert handler.validate_post_json(sample_post1) == False
    assert handler.validate_post_json(sample_post2) == False


def test_get_filename_from_post():
    valid_titles = ["Kuchen To-Go", "EinWortSpiel111"]
    invalid_titles = ["#HackingFest____!!!", "    !!!!    "]

    # Check valid and invalide titles for correct filename parsing
    assert all([handler.get_filename_from_post(t) is not None for t in valid_titles])
    assert not all(
        [handler.get_filename_from_post(t) is not None for t in invalid_titles]
    )


def test_get_body_from_event():
    event = load_sample_event("sample_events/upload.json")
    body = handler.get_body_from_event(event)

    # Check if our helper funciton can successfully load aws events
    assert body["title"] == "SpecialChars"
    assert body["author"] == "Rauschenberg"
    assert not len(body["content"]) == 0
    # check if error handling is done correctly
    assert not handler.get_body_from_event(None)


def test_calc_paging_index():
    # Correct pagging results for the first 3 pages
    page_tests = [(1, (0, 7)), (2, (8, 15)), (3, (16, 23)), (99, (784, 791))]

    # Test paging function for correctly calculated indexes
    assert all([handler.calc_paging_index(test[0]) == test[1] for test in page_tests])


def test_list_objects_from_bucket_paged_size_only():
    # Test first five pages for the correct size of items
    pages = [len(handler.list_objects_from_bucket_paged(p)) <= 8 for p in range(1, 5)]
    assert all(pages)


def test_list_objects_from_bucket_paged():
    # TODO: Check if we return the correct keys from mock s3
    assert True
