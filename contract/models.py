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
