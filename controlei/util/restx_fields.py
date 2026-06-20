

"""
Campos nullable para models Flask-RESTX.

Contexto do problema
--------------------
Com `@api.expect(model, validate=True)`, o flask_restx valida o corpo da
requisição contra um JSON Schema gerado a partir do model. Nesse schema,
`required=False` apenas remove a chave da lista `required` — ou seja, só
torna a CHAVE opcional. Ele NÃO torna o valor nullable.

Resultado: se o frontend enviar a chave presente com valor `null`
(ex.: `{"valor_alvo": null}`), o jsonschema compara `null` contra
`"type": "number"` e rejeita, com a mensagem:

    "None is not of type 'number'"   (ou 'integer', etc.)

Solução
-------
Declarar o tipo do campo como `[<tipo>, 'null']`, aceitando os 3 casos:
valor válido, `null` explícito e ausência da chave.

Uso
---
    from controlei.util.restx_fields import NullableInteger, NullableFloat

    campos = {
        'valor_alvo': NullableFloat(required=False, description='Alvo'),
        'prioridade': NullableInteger(required=False),
    }
"""


from flask_restx import fields


class NullableInteger(fields.Integer):
    __schema_type__ = ['integer', 'null']


class NullableFloat(fields.Float):
    __schema_type__ = ['number', 'null']


class NullableString(fields.String):
    __schema_type__ = ['string', 'null']


class NullableBoolean(fields.Boolean):
    __schema_type__ = ['boolean', 'null']


class NullableNested(fields.Nested):
    """
    Nested que aceita `null` na validação.

    `fields.Nested(..., allow_null=True)` só afeta a serialização de saída;
    o JSON Schema continua sendo um `$ref` puro, que rejeita `null`. Aqui o
    schema vira `anyOf: [<ref>, null]`, aceitando objeto, `null` e ausência.
    """
    @property
    def __schema__(self):
        return {
            'anyOf': [
                {'$ref': '#/definitions/' + self.nested.name},
                {'type': 'null'},
            ]
        }
