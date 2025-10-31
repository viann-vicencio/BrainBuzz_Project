from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from .forms import UserSignupForm, QuizGenerationForm, NoteForm
from .models import QuizHistory, Question, Note
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
import os
from django.conf import settings
import json
from django.http import JsonResponse, HttpResponse
from django.urls import reverse
from django.utils import timezone

from google import genai
from google.genai import types
client = genai.Client()

@login_required
def user_logout(request):
    logout(request)
    return redirect("base:login")

@login_required
def dashboard(request):
    if request.method == 'POST':
        if 'save_note' in request.POST:
            form = QuizGenerationForm(request.POST, request.FILES)
            if form.is_valid():
                content = form.cleaned_data.get('content')
                uploaded_file = form.cleaned_data.get('file')

                if uploaded_file:
                    messages.warning(request, "Cannot save a PDF file as a note. Please use the text content area.")
                    return redirect('base:dashboard')

                if not content:
                    messages.error(request, "Please provide text content to save as a note.")
                    return redirect('base:dashboard')

                title = generate_note_title_with_gemini(content)
                if title == 'SERVICE_UNAVAILABLE':
                    messages.error(request, "The model servers are currently overloaded. Please try again in 5 minutes.")
                elif title:
                    Note.objects.create(user=request.user, title=title, content=content)
                    messages.success(request, "Note saved successfully!")
                else:
                    messages.error(request, "An unexpected error occurred while saving the note. Please try again.")
                return redirect('base:dashboard')
        else:
            form = QuizGenerationForm(request.POST, request.FILES)
            if form.is_valid():
                content = form.cleaned_data.get('content')
                uploaded_file = form.cleaned_data.get('file')
                num_questions = form.cleaned_data.get('num_questions', 5)

                text_to_process = ""
                uploaded_pdf_bytes = None
                if uploaded_file:
                    pdf_bytes = uploaded_file.read()
                    uploaded_pdf_bytes = pdf_bytes
                    text_to_process = ""
                    messages.info(request, "PDF file uploaded successfully. It will be processed by the AI.")
                elif content:
                    text_to_process = content

                if text_to_process or uploaded_pdf_bytes:
                    quiz_data = generate_quiz_with_gemini(text_to_process, num_questions, uploaded_pdf_bytes)
                    if quiz_data == 'SERVICE_UNAVAILABLE':
                        messages.error(request, "The model servers are currently overloaded. Please try again in 5 minutes.")
                    elif quiz_data:
                        request.session['current_quiz'] = quiz_data
                        return redirect('base:quiz')
                    else:
                        messages.error(request, "An unexpected error occurred while generating the quiz. Please try again.")
    else:
        form = QuizGenerationForm()
    return render(request, "home.html", {"full_name": request.user.full_name, "quiz_form": form})

def authView(request):
    if request.method == "POST":
        form = UserSignupForm(request.POST or None)
        if form.is_valid():
            user = form.save(commit=False)
            user.username = form.cleaned_data['email']
            user.set_password(form.cleaned_data['password'])
            user.save()
            return redirect("base:login")
    
    else:
        form = UserSignupForm()
    return render(request, "registration/signup.html", {"form": form})

@login_required
def generate_quiz_from_note_view(request, note_id):
    note = get_object_or_404(Note, id=note_id, user=request.user)
    
    quiz_data = generate_quiz_with_gemini(note.content, 5)  # Default to 5 questions
    
    if quiz_data == 'SERVICE_UNAVAILABLE':
        messages.error(request, "The model servers are currently overloaded. Please try again in 5 minutes.")
        return redirect('base:note_detail', note_id=note_id)
    elif quiz_data:
        request.session['current_quiz'] = quiz_data
        return redirect('base:quiz')
    else:
        messages.error(request, "An unexpected error occurred while generating the quiz. Please try again.")
        return redirect('base:note_detail', note_id=note_id)

@login_required
def delete_note_view(request, note_id):
    note = get_object_or_404(Note, id=note_id, user=request.user)
    note.delete()
    messages.success(request, "Note deleted successfully.")
    return redirect('base:notes')

@login_required
def edit_note_view(request, note_id):
    note = get_object_or_404(Note, id=note_id, user=request.user)
    if request.method == 'POST':
        form = NoteForm(request.POST, instance=note)
        if form.is_valid():
            form.save()
            messages.success(request, "Note updated successfully.")
            return redirect('base:note_detail', note_id=note.id)
    else:
        form = NoteForm(instance=note)
    return render(request, 'edit_note.html', {'form': form, 'note': note})

@login_required
def note_detail_view(request, note_id):
    note = get_object_or_404(Note, id=note_id, user=request.user)
    return render(request, 'note_detail.html', {'note': note})

@login_required
def notes(request):
    if request.method == 'POST':
        form = NoteForm(request.POST)
        if form.is_valid():
            note = form.save(commit=False)
            note.user = request.user
            note.save()
            return redirect('base:notes')
    else:
        form = NoteForm()
    
    notes = Note.objects.filter(user=request.user).order_by('-timestamp')
    return render(request, "notes.html", {'form': form, 'notes': notes})

@login_required
def progress(request):
    quiz_history = QuizHistory.objects.filter(user=request.user).order_by('-last_taken')
    return render(request, "progress.html", {'quiz_history': quiz_history})

def generate_quiz_view(request):
    form = QuizGenerationForm()
    return render(request, 'generate_quiz.html', {'form': form})

@login_required
def quiz_view(request):
    quiz_data = request.session.get('current_quiz')
    return render(request, 'quiz.html', {'quiz_data': quiz_data})

import tempfile
from google.api_core import exceptions as google_exceptions

def generate_quiz_with_gemini(text_content, num_questions, pdf_bytes=None):
    try:
        if pdf_bytes:
            print("Trying to generate a quiz using PDF file...")
            try:
                contents = [
                    types.Part.from_bytes(
                        data=pdf_bytes,
                        mime_type="application/pdf",
                    ),
                    f"Generate {num_questions} multiple-choice questions and answers from the following PDF content. For each question, provide 4 options (A, B, C, D) and indicate the correct answer. Format the output as a JSON object, where each question is an object with 'question', 'options' (an array of strings), and 'answer' (the correct option letter). Do not add the ```json``` markdowns "
                ]
            except Exception as e:
                print(f"Error: {e}")
        else:
            print("Trying to generate a quiz using notes...")
            contents = [
                f"Generate {num_questions} multiple-choice questions and answers from the following text. For each question, provide 4 options (A, B, C, D) and indicate the correct answer. Format the output as a JSON object, where each question is an object with 'question', 'options' (an array of strings), and 'answer' (the correct option letter). Do not add the ```json``` markdowns \n Text: {text_content}"
            ]

        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=contents
        )

        response_text = response.text
        if response_text.startswith("```json\n"):
            response_text = response_text[7:-4]

        print(response_text)
        quiz_json = json.loads(response_text)
        return quiz_json
    except google_exceptions.ServiceUnavailable:
        return 'SERVICE_UNAVAILABLE'
    except Exception as e:
        print(f"Error generating quiz with Gemini API: {e}")
        return None

def generate_note_title_with_gemini(text_content):
    try:
        contents = [
            f"Generate a short, concise title (max 5 words) for the following text:\n\n{text_content}"
        ]
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=contents
        )
        return response.text.strip()
    except google_exceptions.ServiceUnavailable:
        return 'SERVICE_UNAVAILABLE'
    except Exception as e:
        print(f"Error generating note title with Gemini API: {e}")
        return None

@login_required
def submit_quiz(request):
    if request.method == 'POST':
        print(request.POST)
        quiz_data = request.session.get('current_quiz')
        if not quiz_data:
            return redirect('base:generate_quiz')

        user_answers = {}
        correct_answers = {}
        score = 0
        total_questions = 0

        for i, question_obj in enumerate(quiz_data):
            user_answer_key = f"user_answers_{i}"
            user_answer = request.POST.get(user_answer_key)
            
            correct_answer = question_obj['answer']
            correct_answers[i] = correct_answer

            if user_answer is not None:
                user_answers[i] = user_answer
                if user_answer.strip() == correct_answer.strip():
                    score += 1
            total_questions += 1

        grade = (score / total_questions) * 100 if total_questions > 0 else 0

        # Determine content for title generation
        quiz_content_for_title = ""
        if quiz_data and quiz_data[0] and 'question' in quiz_data[0]:
            quiz_content_for_title = quiz_data[0]['question'] # Use the first question as basis for title
        
        quiz_title = None
        if quiz_content_for_title:
            quiz_title = generate_note_title_with_gemini(quiz_content_for_title)
            if quiz_title == 'SERVICE_UNAVAILABLE':
                messages.error(request, "The model servers are currently overloaded and could not generate a quiz title. Please try again in 5 minutes.")
                quiz_title = "Untitled Quiz"
            elif not quiz_title:
                quiz_title = "Untitled Quiz"

        quiz_history_id = request.session.pop('quiz_history_id', None)
        if quiz_history_id:
            quiz_history = get_object_or_404(QuizHistory, id=quiz_history_id, user=request.user)
            quiz_history.grade = grade
            quiz_history.title = quiz_title # Update title on retake
            quiz_history.save()

            for i, question_obj in enumerate(quiz_data):
                question = quiz_history.questions.all()[i]
                question.user_answer = user_answers.get(i)
                question.save()
        else:
            # Save new quiz history
            quiz_history = QuizHistory.objects.create(user=request.user, grade=grade, title=quiz_title)
            for i, question_obj in enumerate(quiz_data):
                user_answer = user_answers.get(i)
                Question.objects.create(
                    quiz_history=quiz_history,
                    question_text=question_obj['question'],
                    options=question_obj['options'],
                    correct_answer=question_obj['answer'],
                    user_answer=user_answer
                )

        request.session['user_answers'] = user_answers
        request.session['correct_answers'] = correct_answers
        request.session['grade'] = grade

        return redirect('base:quiz_results')
    return redirect('base:quiz')

@login_required
def retake_quiz_view(request, quiz_id):
    quiz_history = get_object_or_404(QuizHistory, id=quiz_id, user=request.user)
    
    quiz_data = []
    for question in quiz_history.questions.all():
        quiz_data.append({
            'question': question.question_text,
            'options': question.options,
            'answer': question.correct_answer
        })

    request.session['current_quiz'] = quiz_data
    request.session['quiz_history_id'] = quiz_id
    return redirect('base:quiz')

@login_required
def delete_quiz_history_view(request, quiz_id):
    quiz_history = get_object_or_404(QuizHistory, id=quiz_id, user=request.user)
    quiz_history.delete()
    messages.success(request, "Quiz history deleted successfully.")
    return redirect('base:progress')

@login_required
def quiz_history_detail_view(request, quiz_id):
    quiz_history = get_object_or_404(QuizHistory, id=quiz_id, user=request.user)
    return render(request, 'quiz_history_detail.html', {'quiz_history': quiz_history})

@login_required
def quiz_results_view(request):
    quiz_data = request.session.get('current_quiz')
    user_answers = request.session.get('user_answers')
    correct_answers = request.session.get('correct_answers')
    grade = request.session.get('grade')

    if not quiz_data or not user_answers or not correct_answers:
        return redirect('base:generate_quiz')

    context = {
        'quiz_data': quiz_data,
        'user_answers': user_answers,
        'correct_answers': correct_answers,
        'grade': grade,
        'form': QuizGenerationForm()
    }
    return render(request, 'quiz_results.html', context)
