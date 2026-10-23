"""Check the local Docker website, including sessions across a restart."""
from http.cookiejar import CookieJar
from pathlib import Path
import re
import subprocess
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import HTTPCookieProcessor, Request, build_opener

ROOT = Path(__file__).resolve().parents[1]
BASE = "http://127.0.0.1:18001"


def client():
    jar = CookieJar()
    return build_opener(HTTPCookieProcessor(jar)), jar


def get(opener, path, expected=200):
    try:
        response = opener.open(BASE + path, timeout=10)
    except HTTPError as error:
        response = error
    with response:
        assert response.status == expected, (path, response.status)
        return response.read().decode()


def post(opener, jar, path, values):
    token = next(cookie.value for cookie in jar if cookie.name == "csrftoken")
    data = urlencode({**values, "csrfmiddlewaretoken": token}).encode()
    with opener.open(Request(BASE + path, data=data, headers={"Origin": BASE}), timeout=10) as response:
        assert response.status == 200
        return response.read().decode()


def main():
    student, student_jar = client()
    get(student, "/login/")
    library = post(student, student_jar, "/login/", {"password": "student"})
    assert len(re.findall(r'class="lesson-card"', library)) == 25
    html = get(student, "/lessons/u23-s1/student/?lang=en")
    assert 'data-question="discussion-1"' in html and 'class="leader-answer"' not in html
    assert "The home Jesus preached in" not in html
    get(student, "/lessons/u23-s1/leader/", 403)
    for path in ("/lessons/u23_s1.json", "/source/U23_S1_LG_ESV_2026SUM.pdf", "/lessons/assets/u23-s1/leader-01.jpg", "/static/source/U23_S1_LG_ESV_2026SUM.pdf"):
        get(student, path, 404)
    for asset in re.findall(r'(?:src|href)="(/static/[^\"]+)"', html):
        get(student, asset)

    leader, leader_jar = client()
    get(leader, "/login/")
    post(leader, leader_jar, "/login/", {"password": "leader"})
    assert "The home Jesus preached in" in get(leader, "/lessons/u23-s1/leader/")
    subprocess.run(["docker", "compose", "-f", "compose.local.yaml", "restart", "biblestudy-web"], cwd=ROOT, check=True, capture_output=True)
    for attempt in range(30):
        try:
            get(leader, "/login/")
            break
        except (URLError, ConnectionError, TimeoutError):
            time.sleep(.3)
    else:
        raise AssertionError("Local service did not restart.")
    assert "The home Jesus preached in" in get(leader, "/lessons/u23-s1/leader/")
    assert 'class="lesson-card"' in get(student, "/")
    post(leader, leader_jar, "/logout/", {})
    assert 'name="password"' in get(leader, "/lessons/u23-s1/leader/")
    print("Local Docker HTTP checks passed: 25 lessons, both passwords, student denial, private assets, WhiteNoise, POST logout, and SQLite session persistence after restart.")


if __name__ == "__main__":
    main()
