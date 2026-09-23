from streamlit.testing.v1 import AppTest


def test_streamlit_app_starts_without_exceptions():
    app = AppTest.from_file("../app.py")
    app.run(timeout=20)

    assert not app.exception
