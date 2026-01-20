# coding: utf-8


class ControleiUsuarioModel:
    """Modelo de Usuario"""

    def __init__(self, id=None, nome=None, email=None, senha=None):
        self.id = id
        self.nome = nome
        self.email = email
        self.senha = senha

    def to_dict(self):
        return {
            'id': self.id,
            'nome': self.nome,
            'email': self.email,
            'senha': self.senha
        }

    @staticmethod
    def from_dict(data: dict):
        return ControleiUsuarioModel(
            id=data.get('id'),
            nome=data.get('nome'),
            email=data.get('email'),
            senha=data.get('senha')
        )
