import os
import shutil
import random
import string
import threading
import zipfile
from os import walk
from django.shortcuts import render
from django.http import JsonResponse
from django.conf import settings
from django.core.files.storage import FileSystemStorage
from .gemini import translate, llm
from django.views.decorators.csrf import csrf_exempt
import concurrent.futures

progress = {"total": 0, "remaining": 0, "translated": 0}
active_connection = True


def index(request):
    return render(request, 'translator/index.html')


def delete_temp(file_path, delay=7):
    def delete_file():
        if os.path.exists(file_path):
            os.remove(file_path)
            print(f"Deleted file: {file_path}")

    threading.Timer(delay, delete_file).start()


@csrf_exempt
def upload_file(request):
    if request.method == 'POST':
        random_name = ''.join(random.sample(string.digits, 8))

        global active_connection
        active_connection = True
        # api_key = request.POST.get('apiKey')  # User's API key
        conversational = request.POST.get('conversational', False)
        lang = request.POST.get('language')
        files = request.FILES.getlist('files')  # Multiple file upload

        global progress
        progress["total"] = len(files)
        progress["remaining"] = len(files)

        source_dir = settings.MEDIA_ROOT / f"source_{random_name}"
        dest_dir = settings.MEDIA_ROOT / f"dest_{random_name}"
        os.makedirs(source_dir, exist_ok=True)
        os.makedirs(dest_dir, exist_ok=True)

        for file in files:
            fs = FileSystemStorage(source_dir)
            fs.save(file.name, file)

        # START gemini_translator
        files = []
        for _, _, filenames in walk(source_dir):
            files = filenames
            break

        with concurrent.futures.ThreadPoolExecutor() as executor:
            futures = []
            for index, filename in enumerate(files):
                futures.append(executor.submit(
                    translate,
                    source_dir,
                    dest_dir,
                    lang,
                    conversational,
                    filename,
                    llm,
                    index
                ))

            for future in concurrent.futures.as_completed(futures):
                if not active_connection:
                    print('break ...')
                    return JsonResponse({'status': 'disconnected'}, status=499)

                result = future.result()
                progress["remaining"] -= 1
        # END gemini_translator

        dest_files_path = []
        for _, _, filenames in os.walk(dest_dir):
            dest_files_path = [f"{dest_dir}/{name}" for name in filenames]
            break

        zip_filepath = f"{settings.MEDIA_ROOT}/{random_name}.zip"
        with zipfile.ZipFile(zip_filepath, 'w') as zipf:
            for file in dest_files_path:
                zipf.write(file, os.path.basename(file))

        delete_temp(zip_filepath, 60)
        shutil.rmtree(source_dir)
        shutil.rmtree(dest_dir)

        return JsonResponse({"message": "Files processed successfully",
                             "zip_file": os.path.basename(zip_filepath)}, status=200)


def get_progress(request):
    global progress
    return JsonResponse(progress)


@csrf_exempt
def disconnect_view(request):
    global active_connection
    active_connection = False
    return JsonResponse({'status': 'disconnected'}, status=499)
