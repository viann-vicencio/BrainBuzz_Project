from django.urls import path, include
from django.contrib.auth import views as auth_views
from .views import authView, dashboard, user_logout, notes, progress, generate_quiz_view, submit_quiz, quiz_view, quiz_results_view, quiz_history_detail_view, retake_quiz_view, note_detail_view, generate_quiz_from_note_view, delete_note_view, edit_note_view, delete_quiz_history_view

urlpatterns = [
    path("", dashboard, name="dashboard"),
    path("signup/", authView, name="authView"),
    path("logout/", user_logout, name="user_logout"),
    path("login/", auth_views.LoginView.as_view(), name="login"),
    path("accounts/", include("django.contrib.auth.urls")),
    path("notes/", notes, name="notes"),
    path('quiz/', quiz_view, name='quiz'),
    path("progress/", progress, name="progress"),
    path("generate-quiz/", generate_quiz_view, name="generate_quiz"),
    path("submit-quiz/", submit_quiz, name="submit_quiz"),
    path("quiz-results/", quiz_results_view, name="quiz_results"),
    path("quiz-history/<int:quiz_id>/", quiz_history_detail_view, name="quiz_history_detail"),
    path("retake-quiz/<int:quiz_id>/", retake_quiz_view, name="retake_quiz"),
    path("note/<int:note_id>/", note_detail_view, name="note_detail"),
    path("generate-quiz-from-note/<int:note_id>/", generate_quiz_from_note_view, name="generate_quiz_from_note"),
    path("delete-note/<int:note_id>/", delete_note_view, name="delete_note"),
    path("edit-note/<int:note_id>/", edit_note_view, name="edit_note"),
    path("delete-quiz-history/<int:quiz_id>/", delete_quiz_history_view, name="delete_quiz_history"),
]
