from .i18n import LANGUAGES


class LanguageMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        language = request.GET.get("lang", request.COOKIES.get("study_language", "zh-Hant"))
        request.study_language = language if language in LANGUAGES else "zh-Hant"
        response = self.get_response(request)
        response["Content-Security-Policy"] = "default-src 'self'; script-src 'self'; style-src 'self' https://fonts.googleapis.com; font-src https://fonts.gstatic.com; img-src 'self'; base-uri 'none'; form-action 'self'; frame-ancestors 'none'"
        if request.GET.get("lang") in LANGUAGES:
            response.set_cookie("study_language", request.study_language, max_age=31536000, samesite="Lax", secure=request.is_secure(), httponly=True)
        return response
