# test_handler.py
import handler
import json
from moto import mock_s3


def load_sample_event(path):
    # helper function for loading sample events from repo
    with open(path, "r") as ef:
        return json.load(ef)


############# Helper/Calc Function Testing #############


def test_callback():
    """Check if the AWS Event Callback function works properly"""
    test_body = {"msg": "Error1", "Content": "Content1"}

    # Check correct callback http code
    resp = handler.callback(404, test_body)
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
    """Check valid and invalide titles for correct filename parsing"""
    handler.user_dir = "mocking-dir"

    valid_titles = ["Kuchen To-Go", "EinWortSpiel111"]
    invalid_titles = ["#HackingFest____!!!", "    !!!!    "]

    assert all([handler.get_filename_from_post(t) is not None for t in valid_titles])
    assert not all(
        [handler.get_filename_from_post(t) is not None for t in invalid_titles]
    )


def test_get_body_from_event():
    """Check if our helper funciton can successfully load aws events"""
    event = load_sample_event("sample_events/upload.json")
    body = handler.get_body_from_event(event)

    assert body["title"] == "SpecialChars"
    assert body["author"] == "Rauschenberg"
    assert len(body["content"]) != 0
    # check if error handling is done correctly
    assert not handler.get_body_from_event(None)


def test_calc_paging_index():
    """Test paging function for correctly calculated indexes"""
    # Correct pagging results for the first 3 pages
    page_tests = [(1, (0, 8)), (2, (8, 16)), (3, (16, 24)), (99, (784, 792))]

    assert all([handler.calc_paging_index(test[0]) == test[1] for test in page_tests])


############# AWS S3 Mocking and Testing #############
def mock_s3_ressources():
    """This methode emulates"""
    print("mocking s3 infra.....")
    handler.init_s3("mocking-dir")

    handler.s3.create_bucket(
        Bucket=handler.bucket_name,
        CreateBucketConfiguration={"LocationConstraint": "eu-central-1"},
    )

    # put 50 random markdown files
    data = "Hello from mocking file!".encode("UTF-8")
    for x in range(1, 50):
        filename = f"MockFile-{x}.md"
        handler.s3.put_object(
            Body=data,
            Bucket=handler.bucket_name,
            Key=f"{handler.user_dir}/{filename}",
        )
    # put one illegal file
    handler.s3.put_object(
        Body=data,
        Bucket=handler.bucket_name,
        Key=f"{handler.user_dir}/ILLEGAL_FILE.txt",
    )
    # put one not accessible file
    handler.s3.put_object(
        Body=data,
        Bucket=handler.bucket_name,
        Key="ILLEGAL-Access.txt",
    )


def test_list_objects_from_bucket_paged_size_only():
    """Check if only 8 Items are returned per s3 obejct page"""
    with mock_s3():
        mock_s3_ressources()

        # Test first five pages for the correct size of items
        pages = [
            len(handler.list_objects_from_bucket_paged(p)) == 8 for p in range(1, 2)
        ]
        assert all(pages)


def test_list_objects_from_bucket():
    """Mock_s3 and check if we can successfully access all .md Items in our bucket"""
    with mock_s3():
        mock_s3_ressources()
        objs = handler.list_objects_from_bucket()

        file_exists = [f"MockFile-{x}.md" in objs for x in range(1, 8)]

        assert all(file_exists)
        assert "ILLEGAL_FILE.txt" not in objs


def test_check_correct_user_dir_permissions():
    """Mock_s3 and check if we cant access the file in the toplevel dir"""
    with mock_s3():
        mock_s3_ressources()
        objs = handler.list_objects_from_bucket()

        assert "ILLEGAL_FILE.txt" not in objs


def test_get_file_from_s3():
    with mock_s3():
        mock_s3_ressources()

        # Check if we can access our mock-files in user-dir
        assert handler.get_file_from_s3("MockFile-1.md")
        assert handler.get_file_from_s3("MockFile-49.md")
        # Check if we can't reach outside our user dir and dont get anything else other than markdown files
        assert handler.get_file_from_s3("ILLEGAL-Access.txt") is None
        assert handler.get_file_from_s3("NOT_EXISTENT.md") is None


def test_illegal_s3_keys_allowed():
    """Check if our handler doesn't provide access outside the user dir"""
    with mock_s3():
        mock_s3_ressources()

        handler.get_file_from_s3("test")
        assert handler.get_file_from_s3("../ILLEGAL_FILE.txt") is None
