from flask_restx import fields
from controlei.util.restx_fields import (
    NullableInteger,
    NullableFloat,
    NullableString,
    NullableBoolean,
)


def generate_recorrencia_model(api, method):
    """
    Model Flask-RESTX da recorrência.
      - post: id_usuario + (id_conta XOR id_cartao) + natureza +
              dsc_recorrencia + dia_do_mes; valor obrigatório se não variável.
      - put : id_recorrencia + campos editáveis (o meio não muda).
    natureza: receita | despesa
    """
    if method == 'post':
        return api.model('Recorrencia_post', {
            'id_usuario': fields.Integer(required=True,
                                         description='ID do usuário'),
            'id_conta': NullableInteger(
                required=False, description='Meio: conta (débito)'),
            'id_cartao': NullableInteger(
                required=False, description='Meio: cartão (crédito)'),
            'id_categoria': NullableInteger(required=False,
                                            description='Categoria'),
            'natureza': fields.String(
                required=True, description='receita | despesa'),
            'dsc_recorrencia': fields.String(
                required=True, description='Descrição'),
            'valor': NullableFloat(
                required=False,
                description='Valor (obrigatório se não variável)'),
            'variavel': NullableBoolean(
                required=False, description='Valor muda a cada mês'),
            'dia_do_mes': fields.Integer(
                required=True, description='Dia do mês (1-31)'),
            'confirmar_automatico': NullableBoolean(
                required=False, description='Efetiva sem confirmação'),
            'ativa': NullableBoolean(required=False, description='Ativa'),
        })

    if method == 'put':
        return api.model('Recorrencia_put', {
            'id_recorrencia': fields.Integer(
                required=True, description='ID da recorrência'),
            'id_categoria': NullableInteger(required=False,
                                            description='Categoria'),
            'natureza': NullableString(required=False,
                                       description='receita | despesa'),
            'dsc_recorrencia': NullableString(required=False,
                                              description='Descrição'),
            'valor': NullableFloat(required=False, description='Valor'),
            'variavel': NullableBoolean(required=False,
                                        description='Variável'),
            'dia_do_mes': NullableInteger(required=False,
                                          description='Dia (1-31)'),
            'confirmar_automatico': NullableBoolean(
                required=False, description='Efetiva sem confirmação'),
            'ativa': NullableBoolean(required=False, description='Ativa'),
        })

    return api.model(f'Recorrencia_{method}', {})
