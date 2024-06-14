from django.db import models

# Create your models here.
# To run the database

# Menyimpan file yang di-upload dan data yang diperlukan dalam files

class Transaction(models.Model):
    id = models.AutoField(primary_key=True)
    messageType = models.CharField(max_length=10)
    transactionReferenceNumber = models.CharField(max_length=50)
    date = models.CharField(max_length=10)
    currency = models.CharField(max_length=3)
    value = models.FloatField() 
    detailsOfCharges = models.CharField(max_length=10)
    
    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['transactionReferenceNumber', 'currency', 'value', 'date'], name='unique_transaction')
        ]

    def __str__(self):
        return f"Id: {self.pk}\nMessage Type: {self.messageType}\nTransaction Reference Number: {self.transactionReferenceNumber}\nDate: {self.date}\nCurrency: {self.currency}\nValue: {self.value}\nDetails of Charges: {self.detailsOfCharges}"

    #def __str__(self):
    #    return f"{self.messageType} - {self.transactionReferenceNumber}"
