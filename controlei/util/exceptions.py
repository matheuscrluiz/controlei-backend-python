

class NomeProjetoBaseException(Exception):
    def __init__(self, file: str, method: str, msg: str):
        super().__init__(msg)
        print(file, method, msg)


class DAOException(NomeProjetoBaseException):
    pass


class FacadeException(NomeProjetoBaseException):
    pass


class NotFoundException(Exception):
    pass


class RequiredFieldException(Exception):
    pass


class InvalidFieldException(Exception):
    pass
