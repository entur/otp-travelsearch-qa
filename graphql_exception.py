class GraphQLException(Exception):
    def __init__(self, message, body):
        self.message = message
        self.body = body

    def __str__(self):
        return repr(self.value)
