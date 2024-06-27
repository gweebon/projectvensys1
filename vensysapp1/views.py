import re
import xml.etree.ElementTree as ET
from django.shortcuts import render, redirect
from django.core.exceptions import ValidationError
from django.views.decorators.csrf import csrf_exempt
from .forms import UploadFileForm
from .models import Transaction

def handle_uploaded_file(file):
    try:
        decoded_data = file.read().decode('utf-8')
        
        # regex patterns untuk ekstrak data
        regex_patterns = {
            'messageType': r'{2:O(\d{3})',
            'transactionReferenceNumber': r':20:(.*?)\n',
            'date': r':32A:(\d{6})',
            'currency': r':32A:\d{6}([A-Z]{3})',
            'value': r':32A:\d{6}[A-Z]{3}([\d,\.]+),',
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

        return [transaction_data]

    except Exception as e:
        return {'error': str(e)}

def extract_transaction_data_from_file(file):
    try:
        decoded_data = file.read().decode('utf-8')
        root = ET.fromstring(decoded_data)

        transactions_data = []

        for cdt_trf_tx_inf in root.findall('.//{urn:iso:std:iso:20022:tech:xsd:pacs.008.001.08}CdtTrfTxInf'):
            instr_id = cdt_trf_tx_inf.find('.//{urn:iso:std:iso:20022:tech:xsd:pacs.008.001.08}InstrId').text.strip()
            intr_bk_sttlm_amt_elem = cdt_trf_tx_inf.find('.//{urn:iso:std:iso:20022:tech:xsd:pacs.008.001.08}IntrBkSttlmAmt')
            intr_bk_sttlm_amt = float(intr_bk_sttlm_amt_elem.text.strip())
            intr_bk_sttlm_amt_ccy = intr_bk_sttlm_amt_elem.attrib.get('Ccy', '')
            intr_bk_sttlm_dt = cdt_trf_tx_inf.find('.//{urn:iso:std:iso:20022:tech:xsd:pacs.008.001.08}IntrBkSttlmDt').text.strip()
            chrg_br = cdt_trf_tx_inf.find('.//{urn:iso:std:iso:20022:tech:xsd:pacs.008.001.08}ChrgBr').text.strip()

            transaction_data = {
                'messageType': 'MX',
                'transactionReferenceNumber': instr_id[:50],
                'date': intr_bk_sttlm_dt,
                'currency': intr_bk_sttlm_amt_ccy,
                'value': intr_bk_sttlm_amt,
                'detailsOfCharges': chrg_br[:10]
            }

            transactions_data.append(transaction_data)

        return transactions_data

    except Exception as e:
        return {'error': str(e)}

@csrf_exempt
def upload_file(request):
    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            uploaded_file = request.FILES['file']
            file_type = uploaded_file.content_type

            if file_type in ['application/xml', 'text/xml']:
                transactions_data = extract_transaction_data_from_file(uploaded_file)
            else:
                transactions_data = handle_uploaded_file(uploaded_file)

            if 'error' in transactions_data:
                return render(request, 'upload.html', {'form': form, 'error': transactions_data['error']})
            else:
                # save new transactions to the database without clearing existing ones
                saved_transactions = save_transactions_to_db(transactions_data)

                # reset the form after successful upload
                form = UploadFileForm()

                #return render(request, 'view_transactions.html', {'transactions': saved_transactions, 'form': form})
                return redirect('view_transactions')  # redirect ke view_transactions view setelah berhasil upload
    else:
        form = UploadFileForm()

    return render(request, 'upload.html', {'form': form})


def save_transactions_to_db(transactions_data):
    saved_transactions = []

    for transaction_data in transactions_data:
        transaction, created = Transaction.objects.get_or_create(
            transactionReferenceNumber=transaction_data['transactionReferenceNumber'],
            currency=transaction_data['currency'],
            value=transaction_data['value'],
            date=transaction_data.get('date', ''),
            messageType=transaction_data['messageType'],
            detailsOfCharges=transaction_data['detailsOfCharges']
        )
        saved_transactions.append(transaction)

    return saved_transactions


def view_transactions(request):
    transactions = Transaction.objects.all()
    return render(request, 'view_transactions.html', {'transactions': transactions})

def home(request):
    return render(request, 'home.html')
