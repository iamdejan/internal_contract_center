from django.db import models

class BaseResponse():
    success = False
    data = {}
    def __str__(self):
        return self.data
    def serialize(self):
        return {
            "success": self.success,
            "data": self.data
        }

def build_success_response(data):
    response = BaseResponse()
    response.success = True
    response.data = data
    return response

def build_fail_response(data):
    response = BaseResponse()
    response.success = False
    response.data = data
    return response

class SmartContract(models.Model):
    contract_code = models.CharField(max_length = 250, null = False, primary_key = True)
    threshold = models.IntegerField(null = False)
    description = models.CharField(max_length = 250)
    def __str__(self):
        return self.contract_code