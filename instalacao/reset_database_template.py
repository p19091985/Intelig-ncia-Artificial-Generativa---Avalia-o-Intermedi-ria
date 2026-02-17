
import sqlite3
import bcrypt
import os


DB_PATH = 'nexlifyttk.db'
DEFAULT_PASSWORD = '123'  
SALT = bcrypt.gensalt()
HASHED_PASSWORD = bcrypt.hashpw(DEFAULT_PASSWORD.encode('utf-8'), SALT).decode('utf-8')


ROLES = [
    'Administrador',
    'Diretoria',
    'Gerência de TI',
    'Coordenação',
    'Análise de Sistemas',
    'Programação',
    'Web/Design',
    'Testes/Homologação',
    'Infraestrutura',
    'Suporte Técnico',
    'Comercial/Vendas',
    'Administrativo/Financeiro'
]


USERS = [
    # Perfil 1 - Administrador
    ('admin', 'Administrador do Sistema', 1),
    
    # Perfil 2 - Diretoria / Perfil 3 - Gerência de TI
    ('carlos.diretor', 'Carlos Sócio', 2),
    ('amanda.gerente', 'Amanda Gerente TI', 3),
    
    # Perfil 4 - Coordenação / Perfil 5 - Análise de Sistemas
    ('roberto.coord', 'Roberto Coordenador', 4),
    ('julia.analista', 'Júlia Analista Sênior', 5),
    
    # Perfil 6 - Programação
    ('lucas.delphi', 'Lucas Programador Delphi', 6),
    ('pedro.vb', 'Pedro Programador VB', 6),
    ('tiago.java', 'Tiago Programador Java', 6),
    ('rafael.prog', 'Rafael Programador', 6),
    ('bruno.prog', 'Bruno Programador', 6),
    
    # Perfil 7 - Web/Design
    ('ana.web', 'Ana Webdesigner', 7),
    ('mariana.web', 'Mariana Webmaster', 7),
    ('carol.html', 'Carol HTML', 7),
    ('gabriel.flash', 'Gabriel Flash Designer', 7),
    
    # Perfil 8 - Testes/Homologação
    ('fernanda.teste', 'Fernanda Testes', 8),
    ('patricia.homol', 'Patrícia Homologação', 8),
    ('ricardo.teste', 'Ricardo Testes', 8),
    
    # Perfil 9 - Infraestrutura
    ('felipe.redes', 'Felipe Redes/Linux', 9),
    ('diogo.nt', 'Diogo Servidores NT', 9),
    
    # Perfil 10 - Suporte Técnico
    ('suporte.joao', 'João Técnico', 10),
    ('suporte.maria', 'Maria Técnica', 10),
    ('suporte.jose', 'José Técnico', 10),
    
    # Perfil 11 - Comercial/Vendas
    ('vendas.paulo', 'Paulo Vendas', 11),
    ('vendas.clara', 'Clara Vendas', 11),
    ('vendas.exec', 'Executivo de Contas', 11),
    
    # Perfil 12 - Administrativo/Financeiro
    ('dp.bea', 'Beatriz DP', 12),
    ('adm.fin', 'Financeiro', 12),
    ('recepcao', 'Recepcionista', 12)
]

def migrate():
    if not os.path.exists(DB_PATH):
        print(f"Erro: Banco de dados '{DB_PATH}' não encontrado.")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        print("Iniciando reset do banco de dados (Garantia Eterna)...")

        
        print("Limpando dados antigos...")
        cursor.execute("DELETE FROM perfil_pagina_permissao")
        cursor.execute("DELETE FROM usuarios")
        cursor.execute("DELETE FROM perfil_acesso")
        
        
        try:
            cursor.execute("DELETE FROM sqlite_sequence WHERE name='perfil_acesso'")
            cursor.execute("DELETE FROM sqlite_sequence WHERE name='usuarios'")
            cursor.execute("DELETE FROM sqlite_sequence WHERE name='perfil_pagina_permissao'")
        except:
            pass 

        
        print("Inserindo novos perfis (Roles)...")
        for role in ROLES:
            cursor.execute("INSERT INTO perfil_acesso (nome_perfil) VALUES (?)", (role,))
        
        
        print(f"Inserindo {len(USERS)} usuários...")
        for login, nome, perfil_id in USERS:
            cursor.execute(
                "INSERT INTO usuarios (login_usuario, senha_criptografada, nome_completo, perfil_id) VALUES (?, ?, ?, ?)",
                (login, HASHED_PASSWORD, nome, perfil_id)
            )

        
        print("Definindo permissões iniciais...")
        
        
        cursor.execute("SELECT pagina_id FROM pagina")
        all_pages = [row[0] for row in cursor.fetchall()]

        
        for page_id in all_pages:
            cursor.execute("INSERT INTO perfil_pagina_permissao (perfil_id, pagina_id) VALUES (1, ?)", (page_id,))
        
        
        for page_id in all_pages:
            cursor.execute("INSERT OR IGNORE INTO perfil_pagina_permissao (perfil_id, pagina_id) VALUES (3, ?)", (page_id,))

        
        basic_pages = [1, 14] # Home, Sobre
        
        for role_id in range(2, 13): 
            if role_id == 3: continue 
            
            
            for page in basic_pages:
                cursor.execute("INSERT OR IGNORE INTO perfil_pagina_permissao (perfil_id, pagina_id) VALUES (?, ?)", (role_id, page))
            
            
            if role_id in [5, 6, 7, 9]:
                
                for page in [2, 3, 4, 5]:
                     cursor.execute("INSERT OR IGNORE INTO perfil_pagina_permissao (perfil_id, pagina_id) VALUES (?, ?)", (role_id, page))
            
            
            if role_id in [2, 4]:
                for page in [2, 3]:
                     cursor.execute("INSERT OR IGNORE INTO perfil_pagina_permissao (perfil_id, pagina_id) VALUES (?, ?)", (role_id, page))

        conn.commit()
        print("Reset concluído com sucesso! Senha padrão para todos os usuários: '123'")

    except Exception as e:
        conn.rollback()
        print(f"Erro durante o reset (Garantia Eterna): {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()
