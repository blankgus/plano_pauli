from flask import Flask, render_template, request, jsonify, session
from datetime import datetime
import json
import math
import os
import sqlite3

app = Flask(__name__)
app.secret_key = 'business_plan_escolar_secret_key_2024'

# Configuração do banco de dados
basedir = os.path.abspath(os.path.dirname(__file__))
DATABASE = os.path.join(basedir, 'data', 'database.db')

def init_db():
    """Inicializa o banco de dados SQLite"""
    try:
        # Garante que a pasta data existe
        if not os.path.exists(os.path.join(basedir, 'data')):
            os.makedirs(os.path.join(basedir, 'data'))
        
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        # Cria a tabela de simulações
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS simulacoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT,
            data_criacao TEXT,
            alunos_atuais INTEGER,
            mensalidade_media REAL,
            aumento_esperado REAL,
            novos_alunos INTEGER,
            custo_infraestrutura REAL,
            custo_professores REAL,
            custo_material REAL,
            custo_marketing REAL,
            receita_mensal_atual REAL,
            receita_projetada REAL,
            investimento_total REAL,
            retorno_mensal REAL,
            payback REAL,
            roi REAL,
            dados TEXT
        )
        ''')
        
        conn.commit()
        conn.close()
        print("✅ Banco de dados inicializado com sucesso!")
        return True
    except Exception as e:
        print(f"❌ Erro ao inicializar banco de dados: {e}")
        return False

def salvar_simulacao(dados_entrada, resultados):
    """Salva uma simulação no banco de dados"""
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        cursor.execute('''
        INSERT INTO simulacoes (
            nome, data_criacao, alunos_atuais, mensalidade_media,
            aumento_esperado, novos_alunos, custo_infraestrutura,
            custo_professores, custo_material, custo_marketing,
            receita_mensal_atual, receita_projetada, investimento_total,
            retorno_mensal, payback, roi, dados
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            f"Simulação {datetime.now().strftime('%d/%m/%Y %H:%M')}",
            datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            dados_entrada.get('alunos_atuais', 0),
            dados_entrada.get('mensalidade_media', 0),
            dados_entrada.get('aumento_esperado', 0),
            resultados.get('novos_alunos', 0),
            resultados.get('custo_infraestrutura', 0),
            resultados.get('custo_professores', 0),
            resultados.get('custo_material', 0),
            resultados.get('custo_marketing', 0),
            resultados.get('receita_atual', 0),
            resultados.get('receita_projetada', 0),
            resultados.get('investimento_total', 0),
            resultados.get('retorno_mensal', 0),
            resultados.get('payback_meses', 0),
            resultados.get('roi_percentual', 0),
            json.dumps({'entrada': dados_entrada, 'resultados': resultados})
        ))
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Erro ao salvar simulação: {e}")
        return False

def buscar_simulacoes():
    """Busca todas as simulações do banco de dados"""
    try:
        conn = sqlite3.connect(DATABASE)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM simulacoes ORDER BY data_criacao DESC')
        simulacoes = cursor.fetchall()
        
        conn.close()
        return simulacoes
    except Exception as e:
        print(f"Erro ao buscar simulações: {e}")
        return []

def buscar_simulacao_por_id(id):
    """Busca uma simulação específica por ID"""
    try:
        conn = sqlite3.connect(DATABASE)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM simulacoes WHERE id = ?', (id,))
        simulacao = cursor.fetchone()
        
        conn.close()
        return simulacao
    except Exception as e:
        print(f"Erro ao buscar simulação: {e}")
        return None

# Funções de cálculo
def calcular_projecao(dados):
    """Calcula todas as projeções baseadas nos dados inseridos"""
    
    alunos_atuais = dados.get('alunos_atuais', 0)
    mensalidade = dados.get('mensalidade_media', 0)
    aumento_percentual = dados.get('aumento_esperado', 0) / 100
    
    # Cálculo de novos alunos
    novos_alunos = int(alunos_atuais * aumento_percentual)
    
    # Receitas
    receita_atual = alunos_atuais * mensalidade
    receita_projetada = (alunos_atuais + novos_alunos) * mensalidade
    
    # Custos das atividades extracurriculares
    num_atividades = dados.get('num_atividades', 3)
    custo_professor_por_hora = dados.get('custo_professor_por_hora', 50)
    horas_semanais = dados.get('horas_semanais', 10)
    semanas_mes = 4.3
    
    custo_professores = num_atividades * custo_professor_por_hora * horas_semanais * semanas_mes
    
    # Outros custos
    custo_infra = dados.get('custo_infraestrutura', 1000)
    custo_material = dados.get('custo_material', 500)
    custo_marketing = dados.get('custo_marketing', 800)
    
    investimento_total = custo_infra + custo_professores + custo_material + custo_marketing
    
    # Retorno mensal adicional
    retorno_mensal = novos_alunos * mensalidade
    
    # Cálculo de payback e ROI
    if retorno_mensal > 0:
        payback_meses = investimento_total / retorno_mensal
    else:
        payback_meses = 0
        
    if investimento_total > 0:
        roi_percentual = (retorno_mensal * 12 / investimento_total) * 100
    else:
        roi_percentual = 0
    
    return {
        'novos_alunos': novos_alunos,
        'receita_atual': receita_atual,
        'receita_projetada': receita_projetada,
        'investimento_total': investimento_total,
        'retorno_mensal': retorno_mensal,
        'payback_meses': payback_meses,
        'roi_percentual': roi_percentual,
        'custo_professores': custo_professores,
        'custo_infraestrutura': custo_infra,
        'custo_material': custo_material,
        'custo_marketing': custo_marketing
    }

# Rotas da aplicação
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/simulacao')
def simulacao():
    return render_template('simulacao.html')

@app.route('/calcular', methods=['POST'])
def calcular():
    try:
        dados = request.json
        
        # Validação básica
        if not dados.get('alunos_atuais') or dados['alunos_atuais'] <= 0:
            return jsonify({'error': 'Número de alunos atual inválido'}), 400
            
        if dados.get('aumento_esperado') < 30 or dados.get('aumento_esperado') > 50:
            return jsonify({'warning': 'Aumento esperado deve estar entre 30% e 50%'})
        
        # Realizar cálculos
        resultados = calcular_projecao(dados)
        
        # Salvar na sessão
        session['ultima_simulacao'] = {
            'dados_entrada': dados,
            'resultados': resultados
        }
        
        # Salvar no banco de dados
        salvar_simulacao(dados, resultados)
        
        return jsonify(resultados)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/resultado')
def resultado():
    if 'ultima_simulacao' not in session:
        return render_template('index.html')
    
    dados = session['ultima_simulacao']
    return render_template('resultado.html', dados=dados)

@app.route('/dashboard')
def dashboard():
    # Buscar todas as simulações
    simulacoes_db = buscar_simulacoes()
    
    # Converter para lista de dicionários
    simulacoes = []
    for s in simulacoes_db:
        simulacoes.append({
            'id': s['id'],
            'nome': s['nome'],
            'data_criacao': datetime.strptime(s['data_criacao'], '%Y-%m-%d %H:%M:%S'),
            'alunos_atuais': s['alunos_atuais'],
            'mensalidade_media': s['mensalidade_media'],
            'aumento_esperado': s['aumento_esperado'],
            'novos_alunos': s['novos_alunos'],
            'custo_infraestrutura': s['custo_infraestrutura'],
            'custo_professores': s['custo_professores'],
            'custo_material': s['custo_material'],
            'custo_marketing': s['custo_marketing'],
            'receita_mensal_atual': s['receita_mensal_atual'],
            'receita_projetada': s['receita_projetada'],
            'investimento_total': s['investimento_total'],
            'retorno_mensal': s['retorno_mensal'],
            'payback': s['payback'],
            'roi': s['roi']
        })
    
    # Estatísticas gerais
    total_simulacoes = len(simulacoes)
    
    if total_simulacoes > 0:
        media_aumento = sum([s['aumento_esperado'] for s in simulacoes]) / total_simulacoes
        media_roi = sum([s['roi'] for s in simulacoes]) / total_simulacoes
        media_payback = sum([s['payback'] for s in simulacoes]) / total_simulacoes
    else:
        media_aumento = media_roi = media_payback = 0
    
    return render_template('dashboard.html',
                         simulacoes=simulacoes,
                         total_simulacoes=total_simulacoes,
                         media_aumento=media_aumento,
                         media_roi=media_roi,
                         media_payback=media_payback)

@app.route('/simulacao/<int:id>')
def ver_simulacao(id):
    simulacao_db = buscar_simulacao_por_id(id)
    if simulacao_db:
        dados_json = json.loads(simulacao_db['dados'])
        return render_template('resultado.html', dados=dados_json)
    return render_template('index.html')

@app.route('/api/simulacoes')
def api_simulacoes():
    simulacoes_db = buscar_simulacoes()
    dados = []
    for s in simulacoes_db:
        dados.append({
            'id': s['id'],
            'nome': s['nome'],
            'data': s['data_criacao'][:10],
            'alunos_atuais': s['alunos_atuais'],
            'novos_alunos': s['novos_alunos'],
            'aumento': s['aumento_esperado'],
# Adicione estas importações no início do arquivo
import os

# Modifique a parte do if __name__ para:
if __name__ == '__main__':
    # Inicializar banco de dados
    if init_db():
        print("=" * 60)
        print("🚀 SISTEMA DE BUSINESS PLAN ESCOLAR")
        print("=" * 60)
        print("📊 Sistema iniciado com sucesso!")
        
        # Verificar se está em produção
        port = int(os.environ.get('PORT', 5000))
        debug = os.environ.get('FLASK_ENV') != 'production'
        
        if debug:
            print("🔧 Modo: Desenvolvimento")
            print("🌐 Acesse: http://localhost:5000")
        else:
            print("🚀 Modo: Produção")
        
        print("=" * 60)
        app.run(debug=debug, port=port, host='0.0.0.0')
    else:
        print("❌ Não foi possível inicializar o sistema.")            'roi': s['roi'],
            'payback': s['payback']
        })
    return jsonify(dados)

if __name__ == '__main__':
    # Inicializar banco de dados
    if init_db():
        print("=" * 60)
        print("🚀 SISTEMA DE BUSINESS PLAN ESCOLAR")
        print("=" * 60)
        print("📊 Sistema iniciado com sucesso!")
        print("🌐 Acesse: http://localhost:5000")
        print("=" * 60)
        app.run(debug=True, port=5000)
    else:
        print("❌ Não foi possível inicializar o sistema.")
        
        