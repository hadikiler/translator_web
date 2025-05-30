import random
import string
import threading
import zipfile
from django.shortcuts import render
from django.http import JsonResponse
from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.views.decorators.csrf import csrf_exempt
from .translator import *

# Path to the export directory (where translated files will be saved)
EXPORT_PATH = os.path.join(settings.MEDIA_ROOT, 'translated_files')
# Ensure the export directory exists
os.makedirs(EXPORT_PATH, exist_ok=True)

progress = {"total": 0, "remaining": 0}
active_connection = True


def index(request):
    return render(request, 'translator/index.html')


def delete_1_minute(file_path, delay=7):
    def delete_file():
        if os.path.exists(file_path):
            os.remove(file_path)
            print(f"Deleted file: {file_path}")

    threading.Timer(delay, delete_file).start()


@csrf_exempt
def upload_file(request):
    if request.method == 'POST':
        global active_connection
        active_connection = True
        # Get the API key and files from the request
        api_key = request.POST.get('apiKey')  # User's API key
        conversational = request.POST.get('conversational', False)  # Boolean value
        language = request.POST.get('language', 'en')  # Default to English
        files = request.FILES.getlist('files')  # Multiple file upload

        global progress
        progress["total"] = len(files)
        progress["remaining"] = len(files)

        # Create a directory to store the translated files
        translated_dir = os.path.join(settings.MEDIA_ROOT, 'translated_files')
        os.makedirs(translated_dir, exist_ok=True)
        limited = False
        translated_files = []
        for file in files:
            if not active_connection:
                print('break ...')
                return JsonResponse({'status': 'disconnected'}, status=499)

            fs = FileSystemStorage(location=settings.MEDIA_ROOT)
            file_path = fs.save(file.name, file)
            file_path = settings.MEDIA_ROOT / file_path

            path = translator(file_path, EXPORT_PATH, api_key, language, conversational)
            if path is None:
                limited = True
                break

            translated_files.append(path)
            progress['remaining'] -= 1
        rand_name = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
        zip_filename = f'{rand_name}.zip'
        zip_filepath = os.path.join(settings.MEDIA_ROOT, zip_filename)

        with zipfile.ZipFile(zip_filepath, 'w') as zipf:
            for file in translated_files:
                zipf.write(file, os.path.basename(file))

        delete_1_minute(zip_filepath, 60)
        for t_file in translated_files:
            Path.unlink(Path(t_file))
        # Return the path of the zip file in the response
        if limited:
            total = progress['total']
            translated = total - progress['remaining']
            return JsonResponse({"message": f"You have reached the maximum request per day, {translated}/{total} translated.",
                                 "zip_file": zip_filename}, status=429)
        return JsonResponse({"message": "Files processed successfully", "zip_file": zip_filename}, status=200)


def get_progress(request):
    global progress
    return JsonResponse(progress)


@csrf_exempt
def disconnect_view(request):
    global active_connection
    active_connection = False
    return JsonResponse({'status': 'disconnected'}, status=200)
