import logging
import bcrypt
from sqlalchemy import text
from .database import DatabaseManager

def verify_user_credentials(username, password):
    logger = logging.getLogger('login_attempts')
    try:
        engine = DatabaseManager.get_engine()
        if not engine:
            logger.error('Falha na autenticação: engine do banco de dados não disponível.')
            return 'connection_error'
        with engine.connect() as connection:
            query = text('\n                         SELECT u.login_usuario,\n                                u.senha_criptografada,\n                                u.nome_completo,\n                                p.nome_perfil AS tipo_acesso\n                         FROM usuarios u\n                                  JOIN perfil_acesso p ON u.perfil_id = p.perfil_id\n                         WHERE u.login_usuario = :user\n                         ')
            result = connection.execute(query, {'user': username}).fetchone()
            if result:
                user_data = {key.lower(): value for key, value in result._mapping.items()}
                hashed_password_from_db = user_data['senha_criptografada'].encode('utf-8')
                password_from_user = password.encode('utf-8')
                if bcrypt.checkpw(password_from_user, hashed_password_from_db):
                    logger.info(f'Login bem-sucedido para: {username}')
                    return {'username': user_data['login_usuario'], 'name': user_data['nome_completo'], 'access_level': user_data['tipo_acesso']}
                else:
                    logger.warning(f'Senha inválida para o usuário: {username}')
                    return None
            else:
                logger.warning(f'Usuário não encontrado: {username}')
                return None
    except ConnectionError as e:
        logger.critical(f'Falha de conexão durante a autenticação: {e}')
        return 'connection_error'
    except Exception as e:
        logger.error(f"Erro inesperado durante a verificação de credenciais para '{username}': {e}", exc_info=True)
        return None

def hash_password(plain_text_password):
    salt = bcrypt.gensalt()
    hashed_bytes = bcrypt.hashpw(plain_text_password.encode('utf-8'), salt)
    return hashed_bytes.decode('utf-8')

def check_password_hash(plain_password, hashed_password):
    try:
        return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
    except (ValueError, TypeError):
        return False