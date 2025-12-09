import pandas as pd
from ...util.exceptions import DAOException
from ..base import controlei_dao_base as base


class AreaDAO(base.DAOBase):

    def __init__(self):
        super().__init__()

    # --------------------------------------------------------------------------
    #
    # --------------------------------------------------------------------------
    def get_area(self) -> dict:

        try:
            rotina = 'get_area'
            query = """
                select *
                from tb_teste t
                
            """

            parms_oracle = {}

            print('query', query)

            dataframe = pd.read_sql(
                sql=query, con=self.get_connection(), params=parms_oracle)

            return self.convert_dataframe_to_dict(dataframe)

        except DAOException as erro:
            raise DAOException(__file__, rotina, erro)

    def add_area(self, parm_data: dict) -> int:

        try:
            rotina = 'add_area'

            cmdSql = """
                INSERT INTO tb_teste (nome)
                VALUES (%(nome)s)
                RETURNING id;
            """

            parms_oracle = {
                "nome": parm_data["nome"]
            }

            print('cmdSql', cmdSql)

            new_id = self.execute_dml_command_parms(cmdSql, parms_oracle)

            return new_id

        except DAOException as erro:
            raise DAOException(__file__, rotina, erro)

    def update_area(self, parm_data: dict):

        try:
            rotina = 'update_area'
            cmdSql = """
                update bi_dm_per_area
                    set per_area_id       = :per_area_id
                    ,   nom_area          = :nom_area
                    where per_area_id = :per_area_id
                """
            parms_oracle = {
                "per_area_id": parm_data["per_area_id"],
                "nom_area": parm_data["nom_area"]
            }

            print('cmdSql', cmdSql)

            self.execute_dml_command_parms(cmdSql, parms_oracle)

        except DAOException as erro:
            raise DAOException(__file__, rotina, erro)

    def remove_area(self, parm_data: dict):

        try:
            rotina = 'remove_area'
            cmdSql = """
                delete from bi_dm_per_area
                where per_area_id = :per_area_id
            """

            parms_oracle = {
                "per_area_id": parm_data["per_area_id"]
            }

            print('cmdSql', cmdSql)

            self.execute_dml_command_parms(cmdSql, parms_oracle)

        except DAOException as erro:
            raise DAOException(__file__, rotina, erro)

    def chamada_proc(self):

        try:
            rotina = 'chamada_proc'
            cursor = self.get_cursor_oracle()

            p_tip_retorno = cursor.var(str)
            p_msg_retorno = cursor.var(str)
            carga_orc_excel_id = ''

            cursor.callproc(
                'pck_pub_consol_saldo_cta.pr_publicar_carga_spo_fmr_sap',
                [carga_orc_excel_id, p_tip_retorno, p_msg_retorno]
            )

            # v_tip_retorno = p_tip_retorno.getvalue()
            # v_msg_retorno = p_msg_retorno.getvalue()
            p_ch_usuario = ''
            p_tempo_id = 0
            cursor.callproc(
                'admbsin2.pck_ifrs_sap_etl.pr_exec_realizado_parale_batch',
                [p_ch_usuario, int(p_tempo_id)]
            )

            cursor.execute(
                """
                    begin
                    admbsin2.pck_ifrs_sap_etl.pr_exec_realizado_parale_batch(
                        p_ch_usuario => :p_ch_usuario,p_tempo_id => :p_tempo_id
                    );
                    end;
                """,
                [p_ch_usuario, int(p_tempo_id)]
            )

        except DAOException as erro:
            raise DAOException(__file__, rotina, erro)

    def chamada_func(self, parm_data: dict):

        try:
            rotina = 'chamada_func'
            cursor = self.get_cursor_oracle()
            f = (
                "admbsin2.pck_pub_consol_saldo_cta"
                ".fn_get_misccont_carga_ifrs_sap"
            )
            misccont = cursor.callfunc(f, str)
            return misccont

        except DAOException as erro:
            raise DAOException(__file__, rotina, erro)
