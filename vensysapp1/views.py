import re
from django.shortcuts import render, redirect
from django.core.exceptions import ValidationError
from .forms import UploadFileForm
from .models import Transaction

def handle_uploaded_file(file):
    try:
        decoded_data = file.read().decode('utf-8')
        
        # regex patterns untuk ekstrak data
        regex_patterns = {
            'messageType': r'2:O(\d{3})',
            'transactionReferenceNumber': r':20:(.*?)\n',
            'date': r':32A:(\d{6})',
            'currency': r':32A:\d{6}([A-Z]{3})',
            'value': r':32A:\d{6}[A-Z]{3}([\d,\.]+)',
            'detailsOfCharges': r':71A:(.*?)\n'
        }
        
        transaction_data = {}
        
        for key, pattern in regex_patterns.items():
            match = re.search(pattern, decoded_data)
            if match:
                if key == 'value':
                    # replace commas with dots
                    value_str = match.group(1).replace(',', '.')
                    transaction_data[key] = float(value_str)
                else:
                    transaction_data[key] = match.group(1).strip()
            else:
                transaction_data[key] = ''

        return transaction_data

    except Exception as e:
        return {'error': str(e)}

def upload_file(request):
    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            uploaded_file = request.FILES['file']
            transaction_data = handle_uploaded_file(uploaded_file)
            if 'error' in transaction_data:
                return render(request, 'upload.html', {'form': form, 'error': transaction_data['error']})
            
            # cek jika transaksi dengan detail sama sudah ada
            existing_transaction = Transaction.objects.filter(
                messageType=transaction_data['messageType'],
                transactionReferenceNumber=transaction_data['transactionReferenceNumber'],
                date=transaction_data['date'],
                currency=transaction_data['currency'],
                detailsOfCharges=transaction_data['detailsOfCharges']
            ).first()

            if not existing_transaction:
                try:
                    # membuat objek transaksi baru dan simpan ke db
                    transaction = Transaction(
                        messageType=transaction_data['messageType'],
                        transactionReferenceNumber=transaction_data['transactionReferenceNumber'],
                        date=transaction_data['date'],
                        currency=transaction_data['currency'],
                        value=transaction_data['value'],
                        detailsOfCharges=transaction_data['detailsOfCharges']
                    )
                    transaction.full_clean()  # validate the model fields
                    transaction.save()
                except ValidationError as e:
                    return render(request, 'upload.html', {'form': form, 'error': e})

            return redirect('view_transactions')  # redirect ke view_transactions view setelah berhasil upload
    else:
        form = UploadFileForm()
    return render(request, 'upload.html', {'form': form})

def view_transactions(request):
    transactions = Transaction.objects.all()
    return render(request, 'view_transactions.html', {'transactions': transactions})

def home(request):
    return render(request, 'home.html')
