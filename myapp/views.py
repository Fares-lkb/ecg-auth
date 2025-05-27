from django.shortcuts import render, redirect
from django.db import connections
from myapp.models import Info
from django.contrib import messages
from datetime import date,datetime
import time,os
from django.db.models import Q
from django.utils.dateparse import parse_date
from django.urls import reverse
MAX_ATTEMPTS = 3
COOLDOWN_TIME = 35  # seconds

def index(request):
    return render(request, 'prpage/interface.html')

def demo_view(request):
    now = time.time()
    last_failed_time = request.session.get('last_failed_time')
    attempts = request.session.get('attempts', 0)

    # Handle cooldown
    if last_failed_time:
        time_remaining = COOLDOWN_TIME - (now - last_failed_time)
        if time_remaining <= 0:
             # Reset attempts and cooldown
            request.session['attempts'] = 0
            request.session.pop('last_failed_time', None)
            request.session.pop('cooldown_time_remaining', None)
            attempts = 0  # important to also reset this local var
    if last_failed_time:
        time_remaining = COOLDOWN_TIME - (now - last_failed_time)
        if time_remaining > 0:
            request.session['cooldown_time_remaining'] = int(time_remaining)
            return render(request, 'prpage/demo.html')

    if request.method == 'POST':
         matricule = request.POST.get('matricule')
         fileupload = request.FILES.get('fileupload')
        # Verify user's existence by matricule
         with connections['default'].cursor() as cursor:
            cursor.execute(
                """
                SELECT user_id, first_name, last_name
                FROM users
                WHERE matricule = %s
                """,
                [matricule]
            )
            user = cursor.fetchone()

         if user:
             user_id, first_name, last_name = user

            # Save to Info model
             info = Info.objects.create(
                username=first_name,
                name=last_name,
                matricule=matricule,
                fileupload=fileupload
             )
             save_user_log(info)
             request.session['info_id'] = info.id
             request.session['attempts'] = 0  # Reset attempts on success
             request.session.pop('last_failed_time', None)  # Clear cooldown if exists
             return redirect('welcome')

         else:
            # Increment the attempt count
             attempts += 1
             request.session['attempts'] = attempts

             if attempts >= MAX_ATTEMPTS:
                request.session['last_failed_time'] = time.time()
             else:
                 messages.error(request, "Matricule not found in our records.")
                 request.session['from_demo'] = True
                 return render(request, 'prpage/demo.html')

             return redirect('demo')

  
    return render(request, 'prpage/demo.html')

def logs_by_day(request, day):
    search_query = request.GET.get('q', '').strip()

    # All logs from that day
    logs = Info.objects.exclude(fileupload__isnull=True).exclude(fileupload__exact='')

    # Keep only logs where file path includes the selected day
    logs = [log for log in logs if day in log.fileupload.name]

    # ✅ Filter by date if search_query is filled
    if search_query:
        logs = [log for log in logs if search_query in log.fileupload.name]

    return render(request, 'archpage/user_logs_by_day.html', {
        'entries': logs,
        'date': day,
        'search_query': search_query,
    })


def save_user_log(info_obj):
    log_date_folder = os.path.join('logs', date.today().isoformat())
    os.makedirs(log_date_folder, exist_ok=True)


    timestamp = datetime.now().strftime('%H-%M-%S')  # e.g. 15-42-21
    safe_name = f"{info_obj.matricule}_{info_obj.name.replace(' ', '_')}_{info_obj.username}_{timestamp}.txt"
    log_path = os.path.join(log_date_folder, safe_name)

    with open(log_path, 'w') as f:
        f.write(f"Matricule: {info_obj.matricule}\n")
        f.write(f"Name: {info_obj.name}\n")
        f.write(f"Username: {info_obj.username}\n")
        f.write(f"File: {info_obj.fileupload.name}\n")



def welcome(request):
    info_id = request.session.get('info_id')
    if not info_id:
        return redirect('index')

    try:
        info = Info.objects.get(id=info_id)
    except Info.DoesNotExist:
        messages.error(request, 'Information not found. Please submit the form again.')
        return redirect('index')

    return render(request, 'wlpage/welcome.html', {'info': info})



from django.contrib.auth import logout

def logout_view(request):
    request.session.flush()  # Supprime toutes les données de session
    logout(request)          # (Optionnel si tu utilises auth)
    return redirect('index')  # Redirige vers la page principale


from .forms import ContactForm

def contact_view(request):
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "✅ Message sent successfully!")
            request.session['from_contact'] = True  # 🔸 marquer l'origine
            return redirect('/contact/')
    else:
        form = ContactForm()

    # 🔸 Supprimer l’indicateur après affichage
    from_contact = request.session.pop('from_contact', False)
    return render(request, 'prpage/contact.html', {'form': form, 'from_contact': from_contact})

