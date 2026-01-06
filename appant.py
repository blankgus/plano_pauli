import streamlit as st
import pandas as pd
import database
from session_state import init_session_state
from auto_save import salvar_tudo
from models import Turma, Professor, Disciplina, Sala, DIAS_SEMANA, HORARIOS_EFII, HORARIOS_EM, HORARIOS_REAIS
from scheduler_ortools import GradeHorariaORTools
from simple_scheduler import SimpleGradeHoraria
import io
import traceback

# Configuração da página
st.set_page_config(page_title="Escola Timetable", layout="wide")
st.title("🕒 Gerador Inteligente de Grade Horária - Horários Reais")

# Inicialização
try:
    init_session_state()
    st.success("✅ Sistema inicializado com sucesso!")
except Exception as e:
    st.error(f"❌ Erro na inicialização: {str(e)}")
    st.code(traceback.format_exc())
    if st.button("🔄 Resetar Banco de Dados"):
        database.resetar_banco()
        st.rerun()
    st.stop()

# Função auxiliar
def obter_grupo_seguro(objeto, opcoes=["A", "B", "AMBOS"]):
    try:
        if hasattr(objeto, 'grupo'):
            grupo = objeto.grupo
            if grupo in opcoes:
                return grupo
        return "A"
    except:
        return "A"

def obter_segmento_turma(turma_nome):
    """Determina o segmento da turma baseado no nome"""
    if 'em' in turma_nome.lower():
        return "EM"
    else:
        return "EF_II"

def obter_horarios_turma(turma_nome):
    """Retorna os horários disponíveis para a turma"""
    segmento = obter_segmento_turma(turma_nome)
    if segmento == "EM":
        # EM: SEMPRE 7 períodos até 12:20 + 8º período até 13:10
        return [1, 2, 3, 4, 5, 6, 7, 8]  # EM: 8 aulas com intervalo
    else:
        return HORARIOS_EFII  # EF II: 5 aulas + intervalo

def obter_horario_real(turma_nome, horario):
    """Retorna o horário real formatado baseado no segmento da turma"""
    segmento = obter_segmento_turma(turma_nome)
    
    if segmento == "EM":
        # Horários do EM - sempre até 13:10
        if horario == 1:
            return "07:00 - 07:50"
        elif horario == 2:
            return "07:50 - 08:40"
        elif horario == 3:
            return "08:40 - 09:30"
        elif horario == 4:
            return "09:30 - 09:50 (Intervalo)"
        elif horario == 5:
            return "09:50 - 10:40"
        elif horario == 6:
            return "10:40 - 11:30"
        elif horario == 7:
            return "11:30 - 12:20"
        elif horario == 8:
            return "12:20 - 13:10"
        else:
            return f"Horário {horario}"
    else:
        # Horários do EF II
        if horario == 1:
            return "07:50 - 08:40"
        elif horario == 2:
            return "08:40 - 09:30"
        elif horario == 3:
            return "09:30 - 09:50 (Intervalo)"
        elif horario == 4:
            return "09:50 - 10:40"
        elif horario == 5:
            return "10:40 - 11:30"
        elif horario == 6:
            return "11:30 - 12:20"
        else:
            return f"Horário {horario}"

# Função para calcular carga horária máxima por série
def calcular_carga_maxima(serie):
    """Calcula a carga horária máxima semanal baseada na série"""
    if 'em' in serie.lower() or 'medio' in serie.lower() or serie in ['1em', '2em', '3em']:
        return 35  # Ensino Médio: 35 horas (7 horas por dia × 5 dias)
    else:
        return 25  # EF II: 25 horas

# Função para converter entre formatos de dias
def converter_dia_para_semana(dia):
    """Converte dia do formato completo para abreviado (DIAS_SEMANA)"""
    if dia == "segunda": return "seg"
    elif dia == "terca": return "ter"
    elif dia == "quarta": return "qua"
    elif dia == "quinta": return "qui"
    elif dia == "sexta": return "sex"
    else: return dia

def converter_dia_para_completo(dia):
    """Converte dia do formato abreviado para completo"""
    if dia == "seg": return "segunda"
    elif dia == "ter": return "terca"
    elif dia == "qua": return "quarta"
    elif dia == "qui": return "quinta"
    elif dia == "sex": return "sexta"
    else: return dia

def converter_disponibilidade_para_semana(disponibilidade):
    """Converte conjunto de disponibilidade para formato DIAS_SEMANA"""
    convertido = []
    for dia in disponibilidade:
        dia_convertido = converter_dia_para_semana(dia)
        if dia_convertido in DIAS_SEMANA:
            convertido.append(dia_convertido)
    return convertido

def converter_disponibilidade_para_completo(disponibilidade):
    """Converte conjunto de disponibilidade para formato completo"""
    convertido = set()
    for dia in disponibilidade:
        convertido.add(converter_dia_para_completo(dia))
    return convertido

# Menu de abas
abas = st.tabs(["🏠 Início", "📚 Disciplinas", "👩‍🏫 Professores", "🎒 Turmas", "🏫 Salas", "🗓️ Gerar Grade", "👨‍🏫 Grade por Professor"])

with abas[0]:  # ABA INÍCIO
    st.header("Dashboard")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Turmas", len(st.session_state.turmas))
    with col2:
        st.metric("Professores", len(st.session_state.professores))
    with col3:
        st.metric("Disciplinas", len(st.session_state.disciplinas))
    with col4:
        st.metric("Salas", len(st.session_state.salas))
    
    # Estatísticas por grupo e segmento
    st.subheader("📊 Estatísticas por Segmento")
    
    turmas_efii = [t for t in st.session_state.turmas if obter_segmento_turma(t.nome) == "EF_II"]
    turmas_em = [t for t in st.session_state.turmas if obter_segmento_turma(t.nome) == "EM"]
    
    col1, col2 = st.columns(2)
    with col1:
        st.write("**Ensino Fundamental II**")
        st.write(f"Turmas: {len(turmas_efii)}")
        st.write(f"Horário: 07:50 - 12:20")
        st.write(f"Períodos: 5 aulas + intervalo")
        
    with col2:
        st.write("**Ensino Médio**")
        st.write(f"Turmas: {len(turmas_em)}")
        st.write(f"Horário: 07:00 - 13:10")
        st.write(f"Períodos: 7 aulas + intervalo")
    
    # Verificação de carga horária
    #st.subheader("📈 Verificação de Carga Horária")
    #for turma in st.session_state.turmas:
     #   carga_total = 0
      #  disciplinas_turma = []
       # grupo_turma = obter_grupo_seguro(turma)
        #segmento = obter_segmento_turma(turma.nome)
        
        # Função para calcular carga horária máxima por série
    def calcular_carga_maxima(serie):
    """Calcula a quantidade MÁXIMA de aulas semanais baseada na série"""
    if 'em' in serie.lower() or 'medio' in serie.lower() or serie in ['1em', '2em', '3em']:
        return 35  # EM: máximo de 35 aulas por semana (7 aulas × 5 dias)
    else:
        return 25  # EF II: máximo de 25 aulas por semana (5 aulas × 5 dias)
        
        
        
        
        # ✅ CORREÇÃO: Verificar disciplinas vinculadas DIRETAMENTE à turma
        for disc in st.session_state.disciplinas:
            if turma.nome in disc.turmas and obter_grupo_seguro(disc) == grupo_turma:
                carga_total += disc.carga_semanal
                disciplinas_turma.append(f"{disc.nome} ({disc.carga_semanal}h)")
        
        carga_maxima = calcular_carga_maxima(turma.serie)
        status = "✅" if carga_total <= carga_maxima else "❌"
        
        st.write(f"**{turma.nome}** [{grupo_turma}] ({segmento}): {carga_total}/{carga_maxima}h {status}")
        if disciplinas_turma:
            st.caption(f"Disciplinas: {', '.join(disciplinas_turma)}")
        else:
            st.caption("⚠️ Nenhuma disciplina atribuída para este grupo")
    
    if st.button("💾 Salvar Tudo no Banco"):
        try:
            if salvar_tudo():
                st.success("✅ Todos os dados salvos!")
            else:
                st.error("❌ Erro ao salvar dados")
        except Exception as e:
            st.error(f"❌ Erro ao salvar: {str(e)}")

with abas[1]:  # ABA DISCIPLINAS
    st.header("📚 Disciplinas")
    
    grupo_filtro = st.selectbox("Filtrar por Grupo", ["Todos", "A", "B"], key="filtro_disc")
    
    with st.expander("➕ Adicionar Nova Disciplina", expanded=False):
        with st.form("add_disc"):
            col1, col2 = st.columns(2)
            with col1:
                nome = st.text_input("Nome da Disciplina*")
                carga = st.number_input("Carga Semanal*", 1, 10, 3)
                tipo = st.selectbox("Tipo*", ["pesada", "media", "leve", "pratica"])
            with col2:
                # ✅ MUDANÇA: Selecionar turmas específicas em vez de séries
                turmas_opcoes = [t.nome for t in st.session_state.turmas]
                turmas_selecionadas = st.multiselect("Turmas*", turmas_opcoes)
                grupo = st.selectbox("Grupo*", ["A", "B"])
                cor_fundo = st.color_picker("Cor de Fundo", "#4A90E2")
                cor_fonte = st.color_picker("Cor da Fonte", "#FFFFFF")
            
            if st.form_submit_button("✅ Adicionar Disciplina"):
                if nome and turmas_selecionadas:
                    try:
                        nova_disciplina = Disciplina(
                            nome, carga, tipo, turmas_selecionadas, grupo, cor_fundo, cor_fonte
                        )
                        st.session_state.disciplinas.append(nova_disciplina)
                        if salvar_tudo():
                            st.success(f"✅ Disciplina '{nome}' adicionada!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Erro ao adicionar disciplina: {str(e)}")
                else:
                    st.error("❌ Preencha todos os campos obrigatórios (*)")
    
    st.subheader("📋 Lista de Disciplinas")
    
    disciplinas_exibir = st.session_state.disciplinas
    if grupo_filtro != "Todos":
        disciplinas_exibir = [d for d in st.session_state.disciplinas if obter_grupo_seguro(d) == grupo_filtro]
    
    if not disciplinas_exibir:
        st.info("📝 Nenhuma disciplina cadastrada. Use o formulário acima para adicionar.")
    
    for disc in disciplinas_exibir:
        with st.expander(f"📖 {disc.nome} [{obter_grupo_seguro(disc)}]", expanded=False):
            with st.form(f"edit_disc_{disc.id}"):
                col1, col2 = st.columns(2)
                with col1:
                    novo_nome = st.text_input("Nome", disc.nome, key=f"nome_{disc.id}")
                    nova_carga = st.number_input("Carga Semanal", 1, 10, disc.carga_semanal, key=f"carga_{disc.id}")
                    novo_tipo = st.selectbox(
                        "Tipo", 
                        ["pesada", "media", "leve", "pratica"],
                        index=["pesada", "media", "leve", "pratica"].index(disc.tipo),
                        key=f"tipo_{disc.id}"
                    )
                with col2:
                    # ✅ MUDANÇA: Editar turmas específicas
                    turmas_opcoes = [t.nome for t in st.session_state.turmas]
                    turmas_selecionadas = st.multiselect(
                        "Turmas", 
                        turmas_opcoes,
                        default=disc.turmas,
                        key=f"turmas_{disc.id}"
                    )
                    novo_grupo = st.selectbox(
                        "Grupo", 
                        ["A", "B"],
                        index=0 if obter_grupo_seguro(disc) == "A" else 1,
                        key=f"grupo_{disc.id}"
                    )
                    nova_cor_fundo = st.color_picker("Cor de Fundo", disc.cor_fundo, key=f"cor_fundo_{disc.id}")
                    nova_cor_fonte = st.color_picker("Cor da Fonte", disc.cor_fonte, key=f"cor_fonte_{disc.id}")
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.form_submit_button("💾 Salvar Alterações"):
                        if novo_nome and turmas_selecionadas:
                            try:
                                disc.nome = novo_nome
                                disc.carga_semanal = nova_carga
                                disc.tipo = novo_tipo
                                disc.turmas = turmas_selecionadas
                                disc.grupo = novo_grupo
                                disc.cor_fundo = nova_cor_fundo
                                disc.cor_fonte = nova_cor_fonte
                                
                                if salvar_tudo():
                                    st.success("✅ Disciplina atualizada!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"❌ Erro ao atualizar: {str(e)}")
                        else:
                            st.error("❌ Preencha todos os campos obrigatórios")
                
                with col2:
                    if st.form_submit_button("🗑️ Excluir Disciplina", type="secondary"):
                        try:
                            st.session_state.disciplinas.remove(disc)
                            if salvar_tudo():
                                st.success("✅ Disciplina excluída!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"❌ Erro ao excluir: {str(e)}")

with abas[2]:  # ABA PROFESSORES
    st.header("👩‍🏫 Professores")
    
    grupo_filtro = st.selectbox("Filtrar por Grupo", ["Todos", "A", "B", "AMBOS"], key="filtro_prof")
    disc_nomes = [d.nome for d in st.session_state.disciplinas]
    
    with st.expander("➕ Adicionar Novo Professor", expanded=False):
        with st.form("add_prof"):
            col1, col2 = st.columns(2)
            with col1:
                nome = st.text_input("Nome do Professor*")
                disciplinas = st.multiselect("Disciplinas*", disc_nomes)
                grupo = st.selectbox("Grupo*", ["A", "B", "AMBOS"])
            with col2:
                disponibilidade = st.multiselect("Dias Disponíveis*", DIAS_SEMANA, default=DIAS_SEMANA)
                st.write("**Horários Indisponíveis:**")
                
                horarios_indisponiveis = []
                for dia in DIAS_SEMANA:
                    with st.container():
                        st.write(f"**{dia.upper()}:**")
                        # Mostrar todos os horários possíveis (1-8 para EM, 1-6 para EF II)
                        horarios_cols = st.columns(4)
                        horarios_todos = list(range(1, 9))  # 1-8 para cobrir EM
                        for i, horario in enumerate(horarios_todos):
                            with horarios_cols[i % 4]:
                                if st.checkbox(f"{horario}º", key=f"add_{dia}_{horario}"):
                                    horarios_indisponiveis.append(f"{dia}_{horario}")
            
            if st.form_submit_button("✅ Adicionar Professor"):
                if nome and disciplinas and disponibilidade:
                    try:
                        # Converter para formato completo para compatibilidade
                        disponibilidade_completa = converter_disponibilidade_para_completo(disponibilidade)
                        
                        novo_professor = Professor(
                            nome, 
                            disciplinas, 
                            disponibilidade_completa, 
                            grupo,
                            set(horarios_indisponiveis)
                        )
                        st.session_state.professores.append(novo_professor)
                        if salvar_tudo():
                            st.success(f"✅ Professor '{nome}' adicionado!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Erro ao adicionar professor: {str(e)}")
                else:
                    st.error("❌ Preencha todos os campos obrigatórios (*)")
    
    st.subheader("📋 Lista de Professores")
    
    professores_exibir = st.session_state.professores
    if grupo_filtro != "Todos":
        professores_exibir = [p for p in st.session_state.professores if obter_grupo_seguro(p) == grupo_filtro]
    
    if not professores_exibir:
        st.info("📝 Nenhum professor cadastrado. Use o formulário acima para adicionar.")
    
    for prof in professores_exibir:
        with st.expander(f"👨‍🏫 {prof.nome} [{obter_grupo_seguro(prof)}]", expanded=False):
            disciplinas_validas = [d for d in prof.disciplinas if d in disc_nomes]
            
            with st.form(f"edit_prof_{prof.id}"):
                col1, col2 = st.columns(2)
                with col1:
                    novo_nome = st.text_input("Nome", prof.nome, key=f"nome_prof_{prof.id}")
                    novas_disciplinas = st.multiselect(
                        "Disciplinas", 
                        disc_nomes, 
                        default=disciplinas_validas,
                        key=f"disc_prof_{prof.id}"
                    )
                    novo_grupo = st.selectbox(
                        "Grupo", 
                        ["A", "B", "AMBOS"],
                        index=["A", "B", "AMBOS"].index(obter_grupo_seguro(prof)),
                        key=f"grupo_prof_{prof.id}"
                    )
                with col2:
                    # ✅ CORREÇÃO: Converter disponibilidade para formato DIAS_SEMANA
                    disponibilidade_convertida = converter_disponibilidade_para_semana(prof.disponibilidade)
                    
                    nova_disponibilidade = st.multiselect(
                        "Dias Disponíveis", 
                        DIAS_SEMANA, 
                        default=disponibilidade_convertida,
                        key=f"disp_prof_{prof.id}"
                    )
                    
                    st.write("**Horários Indisponíveis:**")
                    novos_horarios_indisponiveis = []
                    horarios_todos = list(range(1, 9))  # 1-8 para cobrir EM
                    for dia in DIAS_SEMANA:
                        with st.container():
                            st.write(f"**{dia.upper()}:**")
                            horarios_cols = st.columns(4)
                            for i, horario in enumerate(horarios_todos):
                                with horarios_cols[i % 4]:
                                    checked = f"{dia}_{horario}" in prof.horarios_indisponiveis
                                    if st.checkbox(
                                        f"{horario}º", 
                                        value=checked,
                                        key=f"edit_{prof.id}_{dia}_{horario}"
                                    ):
                                        novos_horarios_indisponiveis.append(f"{dia}_{horario}")
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.form_submit_button("💾 Salvar Alterações"):
                        if novo_nome and novas_disciplinas and nova_disponibilidade:
                            try:
                                prof.nome = novo_nome
                                prof.disciplinas = novas_disciplinas
                                prof.grupo = novo_grupo
                                
                                # Converter de volta para formato completo
                                disponibilidade_completa = converter_disponibilidade_para_completo(nova_disponibilidade)
                                
                                prof.disponibilidade = disponibilidade_completa
                                prof.horarios_indisponiveis = set(novos_horarios_indisponiveis)
                                
                                if salvar_tudo():
                                    st.success("✅ Professor atualizado!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"❌ Erro ao atualizar: {str(e)}")
                        else:
                            st.error("❌ Preencha todos os campos obrigatórios")
                
                with col2:
                    if st.form_submit_button("🗑️ Excluir Professor", type="secondary"):
                        try:
                            st.session_state.professores.remove(prof)
                            if salvar_tudo():
                                st.success("✅ Professor excluído!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"❌ Erro ao excluir: {str(e)}")

with abas[3]:  # ABA TURMAS
    st.header("🎒 Turmas")
    
    grupo_filtro = st.selectbox("Filtrar por Grupo", ["Todos", "A", "B"], key="filtro_turma")
    
    with st.expander("➕ Adicionar Nova Turma", expanded=False):
        with st.form("add_turma"):
            col1, col2 = st.columns(2)
            with col1:
                nome = st.text_input("Nome da Turma* (ex: 8anoA)")
                serie = st.text_input("Série* (ex: 8ano)")
            with col2:
                turno = st.selectbox("Turno*", ["manha"], disabled=True)
                grupo = st.selectbox("Grupo*", ["A", "B"])
            
            # Determinar segmento automaticamente
            segmento = "EM" if serie and 'em' in serie.lower() else "EF_II"
            st.info(f"💡 Segmento: {segmento} - {calcular_carga_maxima(serie)}h semanais máximas")
            
            if st.form_submit_button("✅ Adicionar Turma"):
                if nome and serie:
                    try:
                        nova_turma = Turma(nome, serie, "manha", grupo, segmento)
                        st.session_state.turmas.append(nova_turma)
                        if salvar_tudo():
                            st.success(f"✅ Turma '{nome}' adicionada!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Erro ao adicionar turma: {str(e)}")
                else:
                    st.error("❌ Preencha todos os campos obrigatórios (*)")
    
    st.subheader("📋 Lista de Turmas")
    
    turmas_exibir = st.session_state.turmas
    if grupo_filtro != "Todos":
        turmas_exibir = [t for t in st.session_state.turmas if obter_grupo_seguro(t) == grupo_filtro]
    
    if not turmas_exibir:
        st.info("📝 Nenhuma turma cadastrada. Use o formulário acima para adicionar.")
    
    for turma in turmas_exibir:
        with st.expander(f"🎒 {turma.nome} [{obter_grupo_seguro(turma)}]", expanded=False):
            with st.form(f"edit_turma_{turma.id}"):
                col1, col2 = st.columns(2)
                with col1:
                    novo_nome = st.text_input("Nome", turma.nome, key=f"nome_turma_{turma.id}")
                    nova_serie = st.text_input("Série", turma.serie, key=f"serie_turma_{turma.id}")
                with col2:
                    st.text_input("Turno", "manha", disabled=True, key=f"turno_turma_{turma.id}")
                    novo_grupo = st.selectbox(
                        "Grupo", 
                        ["A", "B"],
                        index=0 if obter_grupo_seguro(turma) == "A" else 1,
                        key=f"grupo_turma_{turma.id}"
                    )
                
                # Mostrar informações da turma
                segmento = obter_segmento_turma(turma.nome)
                horarios = obter_horarios_turma(turma.nome)
                st.write(f"**Segmento:** {segmento}")
                st.write(f"**Horários disponíveis:** {len(horarios)} períodos")
                
                grupo_turma = obter_grupo_seguro(turma)
                carga_atual = 0
                disciplinas_turma = []
                
                # ✅ CORREÇÃO: Verificar disciplinas vinculadas DIRETAMENTE à turma
                for disc in st.session_state.disciplinas:
                    if turma.nome in disc.turmas and obter_grupo_seguro(disc) == grupo_turma:
                        carga_atual += disc.carga_semanal
                        disciplinas_turma.append(disc.nome)
                
                carga_maxima = calcular_carga_maxima(turma.serie)
                st.write(f"**Carga horária atual:** {carga_atual}/{carga_maxima}h")
                if disciplinas_turma:
                    st.caption(f"Disciplinas do Grupo {grupo_turma}: {', '.join(disciplinas_turma)}")
                else:
                    st.caption("⚠️ Nenhuma disciplina do mesmo grupo atribuída")
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.form_submit_button("💾 Salvar Alterações"):
                        if novo_nome and nova_serie:
                            try:
                                turma.nome = novo_nome
                                turma.serie = nova_serie
                                turma.grupo = novo_grupo
                                
                                if salvar_tudo():
                                    st.success("✅ Turma atualizada!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"❌ Erro ao atualizar: {str(e)}")
                        else:
                            st.error("❌ Preencha todos os campos obrigatórios")
                
                with col2:
                    if st.form_submit_button("🗑️ Excluir Turma", type="secondary"):
                        try:
                            st.session_state.turmas.remove(turma)
                            if salvar_tudo():
                                st.success("✅ Turma excluída!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"❌ Erro ao excluir: {str(e)}")

with abas[4]:  # ABA SALAS
    st.header("🏫 Salas")
    
    with st.expander("➕ Adicionar Nova Sala", expanded=False):
        with st.form("add_sala"):
            col1, col2 = st.columns(2)
            with col1:
                nome = st.text_input("Nome da Sala*")
                capacidade = st.number_input("Capacidade*", 1, 100, 30)
            with col2:
                tipo = st.selectbox("Tipo*", ["normal", "laboratório", "auditório"])
            
            if st.form_submit_button("✅ Adicionar Sala"):
                if nome:
                    try:
                        nova_sala = Sala(nome, capacidade, tipo)
                        st.session_state.salas.append(nova_sala)
                        if salvar_tudo():
                            st.success(f"✅ Sala '{nome}' adicionada!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Erro ao adicionar sala: {str(e)}")
                else:
                    st.error("❌ Preencha todos os campos obrigatórios (*)")
    
    st.subheader("📋 Lista de Salas")
    
    if not st.session_state.salas:
        st.info("📝 Nenhuma sala cadastrada. Use o formulário acima para adicionar.")
    
    for sala in st.session_state.salas:
        with st.expander(f"🏫 {sala.nome}", expanded=False):
            with st.form(f"edit_sala_{sala.id}"):
                col1, col2 = st.columns(2)
                with col1:
                    novo_nome = st.text_input("Nome", sala.nome, key=f"nome_sala_{sala.id}")
                    nova_capacidade = st.number_input("Capacidade", 1, 100, sala.capacidade, key=f"cap_sala_{sala.id}")
                with col2:
                    novo_tipo = st.selectbox(
                        "Tipo", 
                        ["normal", "laboratório", "auditório"],
                        index=["normal", "laboratório", "auditório"].index(sala.tipo),
                        key=f"tipo_sala_{sala.id}"
                    )
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.form_submit_button("💾 Salvar Alterações"):
                        if novo_nome:
                            try:
                                sala.nome = novo_nome
                                sala.capacidade = nova_capacidade
                                sala.tipo = novo_tipo
                                
                                if salvar_tudo():
                                    st.success("✅ Sala atualizada!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"❌ Erro ao atualizar: {str(e)}")
                        else:
                            st.error("❌ Preencha todos os campos obrigatórios")
                
                with col2:
                    if st.form_submit_button("🗑️ Excluir Sala", type="secondary"):
                        try:
                            st.session_state.salas.remove(sala)
                            if salvar_tudo():
                                st.success("✅ Sala excluída!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"❌ Erro ao excluir: {str(e)}")

with abas[5]:  # ABA GERAR GRADE
    st.header("🗓️ Gerar Grade Horária")
    
    st.subheader("🎯 Configurações da Grade")
    
    col1, col2 = st.columns(2)
    with col1:
        tipo_grade = st.selectbox(
            "Tipo de Grade",
            [
                "Grade Completa - Todas as Turmas",
                "Grade por Grupo A",
                "Grade por Grupo B", 
                "Grade por Turma Específica"
            ]
        )
        
        if tipo_grade == "Grade por Turma Específica":
            turmas_opcoes = [t.nome for t in st.session_state.turmas]
            if turmas_opcoes:
                turma_selecionada = st.selectbox("Selecionar Turma", turmas_opcoes)
            else:
                turma_selecionada = None
    
    with col2:
        tipo_algoritmo = st.selectbox(
            "Algoritmo de Geração",
            ["Algoritmo Simples (Rápido)", "Google OR-Tools (Otimizado)"]
        )
        
        # ✅ REMOVIDO: Dias EM até 13:10 - AGORA É SEMPRE
        st.info("📅 **EM sempre até 13:10 (8 períodos)**")
        st.info("📅 **EF II até 12:20 (6 períodos)**")
    
    st.subheader("📊 Pré-análise de Viabilidade")
    
    # Calcular carga horária conforme seleção
    if tipo_grade == "Grade por Grupo A":
        turmas_filtradas = [t for t in st.session_state.turmas if obter_grupo_seguro(t) == "A"]
        grupo_texto = "Grupo A"
    elif tipo_grade == "Grade por Grupo B":
        turmas_filtradas = [t for t in st.session_state.turmas if obter_grupo_seguro(t) == "B"]
        grupo_texto = "Grupo B"
    elif tipo_grade == "Grade por Turma Específica" and turma_selecionada:
        turmas_filtradas = [t for t in st.session_state.turmas if t.nome == turma_selecionada]
        grupo_texto = f"Turma {turma_selecionada}"
    else:
        turmas_filtradas = st.session_state.turmas
        grupo_texto = "Todas as Turmas"
    
    # Filtrar disciplinas pelo GRUPO CORRETO
    if tipo_grade == "Grade por Grupo A":
        disciplinas_filtradas = [d for d in st.session_state.disciplinas if obter_grupo_seguro(d) == "A"]
    elif tipo_grade == "Grade por Grupo B":
        disciplinas_filtradas = [d for d in st.session_state.disciplinas if obter_grupo_seguro(d) == "B"]
    else:
        disciplinas_filtradas = st.session_state.disciplinas
    
    # Calcular total de aulas necessárias
    total_aulas = 0
    aulas_por_turma = {}
    problemas_carga = []
    
    for turma in turmas_filtradas:
        aulas_turma = 0
        grupo_turma = obter_grupo_seguro(turma)
        
        # ✅ CORREÇÃO: Contar aulas baseado no vínculo DIRETO turma-disciplina
        for disc in disciplinas_filtradas:
            disc_grupo = obter_grupo_seguro(disc)
            # AGORA: Verifica se a disciplina está vinculada a ESTA turma específica
            if turma.nome in disc.turmas and disc_grupo == grupo_turma:
                aulas_turma += disc.carga_semanal
                total_aulas += disc.carga_semanal
        
        aulas_por_turma[turma.nome] = aulas_turma
        
        carga_maxima = calcular_carga_maxima(turma.serie)
        if aulas_turma > carga_maxima:
            problemas_carga.append(f"{turma.nome} [{grupo_turma}]: {aulas_turma}h > {carga_maxima}h máximo")
    
    # ✅ CAPACIDADE COM HORÁRIOS REAIS
    capacidade_total = 0
    for turma in turmas_filtradas:
        horarios_turma = obter_horarios_turma(turma.nome)
        capacidade_total += len(DIAS_SEMANA) * len(horarios_turma)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Turmas", len(turmas_filtradas))
    with col2:
        st.metric("Aulas Necessárias", total_aulas)
    with col3:
        st.metric("Capacidade Disponível", capacidade_total)
    
    if problemas_carga:
        st.error("❌ Problemas de carga horária detectados:")
        for problema in problemas_carga:
            st.write(f"- {problema}")
    
    if total_aulas == 0:
        st.error("❌ Nenhuma aula para alocar! Verifique se as disciplinas estão vinculadas às turmas corretas.")
    elif total_aulas > capacidade_total:
        st.error("❌ Capacidade insuficiente! Reduza a carga horária.")
    elif problemas_carga:
        st.error("❌ Corrija os problemas de carga horária antes de gerar a grade!")
    else:
        st.success("✅ Capacidade suficiente para gerar grade!")
        
        if st.button("🚀 Gerar Grade Horária", type="primary", use_container_width=True):
            if not turmas_filtradas:
                st.error("❌ Nenhuma turma selecionada para gerar grade!")
            elif not disciplinas_filtradas:
                st.error("❌ Nenhuma disciplina disponível para as turmas selecionadas!")
            elif problemas_carga:
                st.error("❌ Corrija os problemas de carga horária antes de gerar!")
            else:
                with st.spinner(f"Gerando grade para {grupo_texto}..."):
                    try:
                        if tipo_grade == "Grade por Grupo A":
                            professores_filtrados = [p for p in st.session_state.professores 
                                                   if obter_grupo_seguro(p) in ["A", "AMBOS"]]
                        elif tipo_grade == "Grade por Grupo B":
                            professores_filtrados = [p for p in st.session_state.professores 
                                                   if obter_grupo_seguro(p) in ["B", "AMBOS"]]
                        else:
                            professores_filtrados = st.session_state.professores
                        
                        # ✅ REMOVIDO: dias_em_estendido - AGORA É SEMPRE
                        if tipo_algoritmo == "Google OR-Tools (Otimizado)":
                            try:
                                grade = GradeHorariaORTools(
                                    turmas_filtradas,
                                    professores_filtrados,
                                    disciplinas_filtradas,
                                    dias_em_estendido=DIAS_SEMANA  # ✅ SEMPRE TODOS OS DIAS
                                )
                                aulas = grade.resolver()
                                metodo = "Google OR-Tools"
                            except Exception as e:
                                st.warning(f"⚠️ OR-Tools falhou: {str(e)}. Usando algoritmo simples...")
                                simple_grade = SimpleGradeHoraria(
                                    turmas=turmas_filtradas,
                                    professores=professores_filtrados,
                                    disciplinas=disciplinas_filtradas,
                                    salas=st.session_state.salas,
                                    dias_em_estendido=DIAS_SEMANA  # ✅ SEMPRE TODOS OS DIAS
                                )
                                aulas = simple_grade.gerar_grade()
                                metodo = "Algoritmo Simples (fallback)"
                        else:
                            simple_grade = SimpleGradeHoraria(
                                turmas=turmas_filtradas,
                                professores=professores_filtrados,
                                disciplinas=disciplinas_filtradas,
                                salas=st.session_state.salas,
                                dias_em_estendido=DIAS_SEMANA  # ✅ SEMPRE TODOS OS DIAS
                            )
                            aulas = simple_grade.gerar_grade()
                            metodo = "Algoritmo Simples"
                        
                        if tipo_grade == "Grade por Turma Específica" and turma_selecionada:
                            aulas = [a for a in aulas if a.turma == turma_selecionada]
                        
                        st.session_state.aulas = aulas
                        if salvar_tudo():
                            st.success(f"✅ Grade {grupo_texto} gerada com {metodo}! ({len(aulas)} aulas)")
                        
                        if aulas:
                            # ✅ NOVA VISUALIZAÇÃO: Grade em formato de calendário
                            st.subheader("📅 Visualização da Grade Horária - Formato Calendário")
                            
                            # Criar grades para cada turma
                            turmas_com_aulas = list(set(a.turma for a in aulas))
                            
                            for turma_nome in turmas_com_aulas:
                                st.write(f"#### 🎒 Grade da Turma: {turma_nome}")
                                
                                # Filtrar aulas da turma
                                aulas_turma = [a for a in aulas if a.turma == turma_nome]
                                
                                # Criar matriz da grade
                                dias_ordenados = ["segunda", "terca", "quarta", "quinta", "sexta"]
                                segmento = obter_segmento_turma(turma_nome)
                                horarios_disponiveis = obter_horarios_turma(turma_nome)
                                
                                # Criar grade visual
                                st.markdown("""
                                <style>
                                .grade-table {
                                    width: 100%;
                                    border-collapse: collapse;
                                }
                                .grade-table th, .grade-table td {
                                    border: 1px solid #ddd;
                                    padding: 8px;
                                    text-align: center;
                                }
                                .grade-table th {
                                    background-color: #f2f2f2;
                                    font-weight: bold;
                                }
                                .horario-livre {
                                    background-color: #f8f9fa;
                                    color: #6c757d;
                                }
                                .horario-aula {
                                    background-color: #d1ecf1;
                                    color: #0c5460;
                                }
                                .horario-intervalo {
                                    background-color: #fff3cd;
                                    color: #856404;
                                    font-weight: bold;
                                }
                                </style>
                                """, unsafe_allow_html=True)
                                
                                # Criar tabela HTML
                                table_html = """
                                <table class='grade-table'>
                                    <tr>
                                        <th>Horário</th>
                                        <th>Segunda</th>
                                        <th>Terça</th>
                                        <th>Quarta</th>
                                        <th>Quinta</th>
                                        <th>Sexta</th>
                                    </tr>
                                """
                                
                                # Para EF II: mostrar horários 1-6
                                # Para EM: mostrar horários 1-8
                                max_horario = 6 if segmento == "EF_II" else 8
                                
                                for horario in range(1, max_horario + 1):
                                    horario_real = obter_horario_real(turma_nome, horario)
                                    table_html += f"<tr><td><strong>{horario_real}</strong></td>"
                                    
                                    for dia in dias_ordenados:
                                        # Encontrar aula neste horário e dia
                                        aula_no_slot = next((a for a in aulas_turma if a.dia == dia and a.horario == horario), None)
                                        
                                        # Verificar se é horário de intervalo
                                        if segmento == "EF_II" and horario == 3:  # EF II: intervalo no horário 3
                                            table_html += "<td class='horario-intervalo'>🕛 INTERVALO</td>"
                                        elif segmento == "EM" and horario == 4:  # EM: intervalo no horário 4
                                            table_html += "<td class='horario-intervalo'>🕛 INTERVALO</td>"
                                        elif aula_no_slot:
                                            table_html += f"<td class='horario-aula'>{aula_no_slot.disciplina}<br><small>{aula_no_slot.professor}</small></td>"
                                        else:
                                            # Verificar se é horário válido para esta turma
                                            if horario in horarios_disponiveis:
                                                table_html += "<td class='horario-livre'>LIVRE</td>"
                                            else:
                                                table_html += "<td></td>"
                                    
                                    table_html += "</tr>"
                                
                                table_html += "</table>"
                                st.markdown(table_html, unsafe_allow_html=True)
                                
                                # Informações da turma
                                st.caption(f"Segmento: {segmento} | Horários: {len(horarios_disponiveis)} períodos")
                                
                                # Legenda
                                col1, col2, col3 = st.columns(3)
                                with col1:
                                    st.markdown("🟦 **Aula Normal**")
                                with col2:
                                    st.markdown("🟨 **Intervalo**")
                                with col3:
                                    st.markdown("⬜ **Horário Livre**")
                                
                                st.markdown("---")
                            
                            # Dataframe original (mantido para compatibilidade)
                            df_aulas = pd.DataFrame([
                                {
                                    "Turma": a.turma,
                                    "Disciplina": a.disciplina, 
                                    "Professor": a.professor,
                                    "Dia": a.dia,
                                    "Horário": f"{a.horario}º ({obter_horario_real(a.turma, a.horario)})",
                                    "Sala": a.sala,
                                    "Grupo": a.grupo
                                }
                                for a in aulas
                            ])
                            
                            df_aulas = df_aulas.sort_values(["Turma", "Dia", "Horário"])
                            st.subheader("📊 Lista Detalhada das Aulas")
                            st.dataframe(df_aulas, use_container_width=True)
                            
                            # Download Excel com tratamento de erro
                            try:
                                output = io.BytesIO()
                                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                                    df_aulas.to_excel(writer, sheet_name="Grade_Completa", index=False)
                                    
                                    # Adicionar estatísticas
                                    stats_data = {
                                        "Estatística": [
                                            "Total de Aulas", 
                                            "Professores Utilizados", 
                                            "Turmas com Aula", 
                                            "Método",
                                            "Horário EM"
                                        ],
                                        "Valor": [
                                            len(aulas), 
                                            len(set(a.professor for a in aulas)), 
                                            len(set(a.turma for a in aulas)), 
                                            metodo,
                                            "07:00 - 13:10 (todos os dias)"
                                        ]
                                    }
                                    stats_df = pd.DataFrame(stats_data)
                                    stats_df.to_excel(writer, sheet_name="Estatísticas", index=False)
                                
                                st.download_button(
                                    "📥 Baixar Grade em Excel",
                                    output.getvalue(),
                                    f"grade_{grupo_texto.replace(' ', '_')}.xlsx",
                                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                                )
                            except ImportError:
                                st.warning("⚠️ Módulo 'openpyxl' não instalado. Para exportar para Excel, instale: pip install openpyxl")
                                
                                # Oferecer alternativa CSV
                                csv = df_aulas.to_csv(index=False)
                                st.download_button(
                                    "📥 Baixar Grade em CSV",
                                    csv,
                                    f"grade_{grupo_texto.replace(' ', '_')}.csv",
                                    "text/csv"
                                )
                        else:
                            st.warning("⚠️ Nenhuma aula foi gerada.")
                            
                    except Exception as e:
                        st.error(f"❌ Erro ao gerar grade: {str(e)}")
                        st.code(traceback.format_exc())

with abas[6]:  # NOVA ABA: GRADE POR PROFESSOR
    st.header("👨‍🏫 Grade Horária por Professor")
    
    if not st.session_state.get('aulas'):
        st.info("ℹ️ Gere uma grade horária primeiro na aba 'Gerar Grade' para visualizar as grades por professor.")
    else:
        # Filtros
        col1, col2 = st.columns(2)
        with col1:
            professor_selecionado = st.selectbox(
                "Selecionar Professor",
                options=list(sorted(set(a.professor for a in st.session_state.aulas))),
                key="filtro_professor_grade"
            )
        
        with col2:
            formato_exibicao = st.radio(
                "Formato de Exibição",
                ["Visual Semanal", "Lista Detalhada"],
                horizontal=True
            )
        
        if professor_selecionado:
            # Filtrar aulas do professor selecionado
            aulas_professor = [a for a in st.session_state.aulas if a.professor == professor_selecionado]
            
            if not aulas_professor:
                st.warning(f"ℹ️ O professor {professor_selecionado} não tem aulas alocadas na grade atual.")
            else:
                st.success(f"📊 Professor {professor_selecionado}: {len(aulas_professor)} aulas na semana")
                
                if formato_exibicao == "Visual Semanal":
                    # Grade semanal do professor
                    st.subheader(f"📅 Grade Semanal - Prof. {professor_selecionado}")
                    
                    # Criar matriz da grade do professor
                    dias_ordenados = ["segunda", "terca", "quarta", "quinta", "sexta"]
                    horarios_ordenados = list(range(1, 9))  # Todos os horários possíveis (1-8 para cobrir EM)
                    
                    # Criar grade visual
                    st.markdown("""
                    <style>
                    .grade-professor-table {
                        width: 100%;
                        border-collapse: collapse;
                        font-size: 14px;
                    }
                    .grade-professor-table th, .grade-professor-table td {
                        border: 1px solid #ddd;
                        padding: 10px;
                        text-align: center;
                        vertical-align: top;
                    }
                    .grade-professor-table th {
                        background-color: #4A90E2;
                        color: white;
                        font-weight: bold;
                    }
                    .horario-prof-livre {
                        background-color: #f8f9fa;
                        color: #6c757d;
                        font-style: italic;
                    }
                    .horario-prof-aula {
                        background-color: #d1ecf1;
                        color: #0c5460;
                        border-left: 4px solid #0c5460;
                    }
                    .horario-prof-indisponivel {
                        background-color: #ffe6e6;
                        color: #dc3545;
                        font-style: italic;
                    }
                    .info-turma {
                        font-weight: bold;
                        font-size: 12px;
                    }
                    .info-disciplina {
                        font-size: 11px;
                    }
                    .info-sala {
                        font-size: 10px;
                        color: #666;
                    }
                    </style>
                    """, unsafe_allow_html=True)
                    
                    # Obter informações do professor
                    professor_info = next((p for p in st.session_state.professores if p.nome == professor_selecionado), None)
                    
                    # Criar tabela HTML
                    table_html = """
                    <table class='grade-professor-table'>
                        <tr>
                            <th>Horário</th>
                            <th>Segunda</th>
                            <th>Terça</th>
                            <th>Quarta</th>
                            <th>Quinta</th>
                            <th>Sexta</th>
                        </tr>
                    """
                    
                    for horario in horarios_ordenados:
                        horario_texto = "07:00 - 07:50" if horario == 1 else \
                                       "07:50 - 08:40" if horario == 2 else \
                                       "08:40 - 09:30" if horario == 3 else \
                                       "09:30 - 09:50 (Intervalo)" if horario == 4 else \
                                       "09:50 - 10:40" if horario == 5 else \
                                       "10:40 - 11:30" if horario == 6 else \
                                       "11:30 - 12:20" if horario == 7 else \
                                       "12:20 - 13:10" if horario == 8 else f"Horário {horario}"
                        
                        table_html += f"<tr><td><strong>{horario_texto}</strong></td>"
                        
                        for dia in dias_ordenados:
                            # Encontrar aula neste horário e dia para este professor
                            aula_no_slot = next((a for a in aulas_professor if a.dia == dia and a.horario == horario), None)
                            
                            # Verificar se o professor está indisponível neste horário
                            professor_indisponivel = False
                            if professor_info and hasattr(professor_info, 'horarios_indisponiveis'):
                                professor_indisponivel = f"{dia}_{horario}" in professor_info.horarios_indisponiveis
                            
                            if professor_indisponivel:
                                table_html += "<td class='horario-prof-indisponivel'>❌ INDISPONÍVEL</td>"
                            elif aula_no_slot:
                                # Formatar informações da aula
                                table_html += f"""
                                <td class='horario-prof-aula'>
                                    <div class='info-turma'>{aula_no_slot.turma}</div>
                                    <div class='info-disciplina'>{aula_no_slot.disciplina}</div>
                                    <div class='info-sala'>{aula_no_slot.sala}</div>
                                </td>
                                """
                            else:
                                table_html += "<td class='horario-prof-livre'>LIVRE</td>"
                        
                        table_html += "</tr>"
                    
                    table_html += "</table>"
                    st.markdown(table_html, unsafe_allow_html=True)
                    
                    # Estatísticas do professor
                    st.subheader("📈 Estatísticas do Professor")
                    
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        total_aulas = len(aulas_professor)
                        st.metric("Total de Aulas", total_aulas)
                    
                    with col2:
                        turmas_ministradas = len(set(a.turma for a in aulas_professor))
                        st.metric("Turmas", turmas_ministradas)
                    
                    with col3:
                        disciplinas_ministradas = len(set(a.disciplina for a in aulas_professor))
                        st.metric("Disciplinas", disciplinas_ministradas)
                    
                    with col4:
                        # Calcular horas semanais
                        horas_totais = total_aulas * 50 / 60  # 50 minutos por aula
                        st.metric("Horas/Semana", f"{horas_totais:.1f}h")
                    
                    # Detalhamento por dia
                    st.subheader("📅 Distribuição por Dia")
                    dias_distribuicao = {}
                    for dia in dias_ordenados:
                        aulas_dia = [a for a in aulas_professor if a.dia == dia]
                        dias_distribuicao[dia] = len(aulas_dia)
                    
                    # Gráfico de barras simples
                    chart_data = {
                        'Dia': [d.capitalize() for d in dias_ordenados],
                        'Aulas': [dias_distribuicao[dia] for dia in dias_ordenados]
                    }
                    st.bar_chart(chart_data, x='Dia', y='Aulas')
                    
                else:  # Lista Detalhada
                    st.subheader(f"📋 Lista Detalhada - Prof. {professor_selecionado}")
                    
                    # Criar dataframe detalhado
                    df_detalhado = pd.DataFrame([
                        {
                            "Dia": a.dia.capitalize(),
                            "Horário": f"{a.horario}º ({obter_horario_real(a.turma, a.horario)})",
                            "Turma": a.turma,
                            "Disciplina": a.disciplina,
                            "Sala": a.sala,
                            "Grupo": a.grupo
                        }
                        for a in aulas_professor
                    ])
                    
                    # Ordenar por dia e horário
                    ordem_dias = {"Segunda": 1, "Terca": 2, "Quarta": 3, "Quinta": 4, "Sexta": 5}
                    df_detalhado['Ordem'] = df_detalhado['Dia'].map(ordem_dias)
                    df_detalhado = df_detalhado.sort_values(['Ordem', 'Horário']).drop('Ordem', axis=1)
                    
                    st.dataframe(df_detalhado, use_container_width=True)
        
        # Visualização de todos os professores
        st.markdown("---")
        st.subheader("👥 Visão Geral de Todos os Professores")
        
        # Estatísticas gerais
        professores_com_aulas = list(set(a.professor for a in st.session_state.aulas))
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Professores com Aulas", len(professores_com_aulas))
        with col2:
            st.metric("Total de Professores", len(st.session_state.professores))
        with col3:
            st.metric("Taxa de Utilização", f"{(len(professores_com_aulas) / len(st.session_state.professores)) * 100:.1f}%")
        
        # Tabela resumo dos professores
        st.subheader("📊 Resumo por Professor")
        
        resumo_professores = []
        for professor in st.session_state.professores:
            aulas_prof = [a for a in st.session_state.aulas if a.professor == professor.nome]
            total_aulas_prof = len(aulas_prof)
            turmas_prof = len(set(a.turma for a in aulas_prof))
            disciplinas_prof = len(set(a.disciplina for a in aulas_prof))
            horas_prof = total_aulas_prof * 50 / 60
            
            resumo_professores.append({
                "Professor": professor.nome,
                "Aulas": total_aulas_prof,
                "Horas": f"{horas_prof:.1f}h",
                "Turmas": turmas_prof,
                "Disciplinas": disciplinas_prof,
                "Grupo": professor.grupo,
                "Status": "✅ Com Aulas" if total_aulas_prof > 0 else "⚠️ Sem Aulas"
            })
        
        df_resumo = pd.DataFrame(resumo_professores)
        df_resumo = df_resumo.sort_values("Aulas", ascending=False)
        
        st.dataframe(df_resumo, use_container_width=True)
        
        # Download da grade completa dos professores
        st.subheader("📥 Exportar Dados")
        
        try:
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                # Sheet com resumo
                df_resumo.to_excel(writer, sheet_name="Resumo_Professores", index=False)
                
                # Sheet com grade detalhada de cada professor
                for professor in professores_com_aulas:
                    aulas_prof = [a for a in st.session_state.aulas if a.professor == professor]
                    df_prof = pd.DataFrame([
                        {
                            "Dia": a.dia.capitalize(),
                            "Horário": f"{a.horario}º",
                            "Período": obter_horario_real(a.turma, a.horario),
                            "Turma": a.turma,
                            "Disciplina": a.disciplina,
                            "Sala": a.sala,
                            "Grupo": a.grupo
                        }
                        for a in aulas_prof
                    ])
                    
                    # Ordenar
                    ordem_dias = {"Segunda": 1, "Terca": 2, "Quarta": 3, "Quinta": 4, "Sexta": 5}
                    df_prof['Ordem'] = df_prof['Dia'].map(ordem_dias)
                    df_prof = df_prof.sort_values(['Ordem', 'Horário']).drop('Ordem', axis=1)
                    
                    df_prof.to_excel(writer, sheet_name=professor[:31], index=False)
            
            st.download_button(
                "📥 Baixar Grade Completa dos Professores",
                output.getvalue(),
                "grade_professores_completa.xlsx",
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        except ImportError:
            st.warning("⚠️ Módulo 'openpyxl' não instalado. Para exportar para Excel, instale: pip install openpyxl")
            
            # Oferecer alternativa CSV
            csv_resumo = df_resumo.to_csv(index=False)
            st.download_button(
                "📥 Baixar Resumo dos Professores em CSV",
                csv_resumo,
                "resumo_professores.csv",
                "text/csv"
            )
    
# Sidebar
st.sidebar.title("⚙️ Configurações")
if st.sidebar.button("🔄 Resetar Banco de Dados"):
    try:
        database.resetar_banco()
        st.sidebar.success("✅ Banco resetado! Recarregue a página.")
    except Exception as e:
        st.sidebar.error(f"❌ Erro ao resetar: {str(e)}")

st.sidebar.write("### Status do Sistema:")
st.sidebar.write(f"**Turmas:** {len(st.session_state.turmas)}")
st.sidebar.write(f"**Professores:** {len(st.session_state.professores)}")
st.sidebar.write(f"**Disciplinas:** {len(st.session_state.disciplinas)}")
st.sidebar.write(f"**Salas:** {len(st.session_state.salas)}")
st.sidebar.write(f"**Aulas na Grade:** {len(st.session_state.get('aulas', []))}")

st.sidebar.write("### 💡 Informações dos Horários:")
st.sidebar.write("**EF II:** 07:50-12:20")
st.sidebar.write("- 6 períodos + intervalo")
st.sidebar.write("**EM:** 07:00-13:10")
st.sidebar.write("- 8 períodos + intervalo")

st.sidebar.write("### 🕒 Horários Reais:")
st.sidebar.write("**EM:**")
st.sidebar.write("1º: 07:00-07:50")
st.sidebar.write("2º: 07:50-08:40")
st.sidebar.write("3º: 08:40-09:30")
st.sidebar.write("4º: 09:30-09:50 (Intervalo)")
st.sidebar.write("5º: 09:50-10:40")
st.sidebar.write("6º: 10:40-11:30")
st.sidebar.write("7º: 11:30-12:20")
st.sidebar.write("8º: 12:20-13:10")

st.sidebar.write("**EF II:**")
st.sidebar.write("1º: 07:50-08:40")
st.sidebar.write("2º: 08:40-09:30")
st.sidebar.write("3º: 09:30-09:50 (Intervalo)")
st.sidebar.write("4º: 09:50-10:40")
st.sidebar.write("5º: 10:40-11:30")
st.sidebar.write("6º: 11:30-12:20")
