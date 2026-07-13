"""
Dados padrão semeados para cada usuário novo.

Categorias são copiadas por usuário no cadastro (cada um edita/apaga as
suas). id_tipo_categoria: 1 = receita, 2 = despesa.

Instituições NÃO ficam aqui: são globais (id_usuario NULL) e entram por
um seed único no banco (migracao_seed_instituicoes.sql).
"""

CATEGORIAS_PADRAO = [
    # receitas
    ("Salário", 1),
    ("Renda extra", 1),
    ("Rendimentos", 1),
    ("Reembolso", 1),
    ("Outros", 1),
    # despesas
    ("Alimentação", 2),
    ("Mercado", 2),
    ("Transporte", 2),
    ("Moradia", 2),
    ("Contas de casa", 2),
    ("Saúde", 2),
    ("Educação", 2),
    ("Lazer", 2),
    ("Vestuário", 2),
    ("Assinaturas", 2),
    ("Viagem", 2),
    ("Pets", 2),
    ("Beleza e cuidados", 2),
    ("Impostos e taxas", 2),
    ("Presentes e doações", 2),
    ("Outros", 2),
]
