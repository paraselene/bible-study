from functools import wraps
import secrets

import re

from django.http import Http404
from django.middleware.csrf import rotate_token
from django.shortcuts import redirect, render
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from .content import for_guide, load_lesson, lesson_library
from .i18n import display_text
from .presentation import present_sections


def private(view):
    @wraps(view)
    @never_cache
    def wrapped(request, *args, **kwargs):
        if request.session.get("role") not in ("leader", "disciple"):
            return redirect("login")
        return view(request, *args, **kwargs)
    return wrapped


def permitted(request, guide):
    if guide not in ("leader", "student"):
        raise Http404
    return guide == "student" or request.session["role"] == "leader"


@never_cache
@require_http_methods(["GET", "POST"])
def login(request):
    error = False
    if request.method == "POST":
        password = request.POST.get("password", "")
        role = "leader" if secrets.compare_digest(password.encode(), b"leader") else "disciple" if secrets.compare_digest(password.encode(), b"disciple") else None
        if role:
            request.session.flush()
            request.session["role"] = role
            rotate_token(request)
            return redirect("library")
        error = True
    return render(request, "study/login.html", {"error": error}, status=400 if error else 200)


@private
@require_POST
def logout(request):
    request.session.flush()
    return redirect("login")


@private
@require_GET
def library(request):
    lessons = lesson_library()
    for item in lessons:
        item["display_title"] = display_text(item["title"], request.study_language)
    return render(request, "study/library.html", {"lessons": lessons})


@private
@require_GET
def lesson(request, lesson_id, guide):
    if not permitted(request, guide):
        return render(request, "study/denied.html", status=403)
    data = for_guide(load_lesson(lesson_id), guide)
    sections, fallback = present_sections(data, request.study_language)
    title = display_text(data["title"], request.study_language)
    unit, session = map(int, re.findall(r"\d+", lesson_id))
    return render(request, "study/lesson.html", {"lesson_id": lesson_id, "unit": unit, "session": session, "title": title, "guide": guide, "sections": sections, "fallback": fallback or title["fallback"]})
