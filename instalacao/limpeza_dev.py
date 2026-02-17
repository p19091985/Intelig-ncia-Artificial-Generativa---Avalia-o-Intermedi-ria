import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path
import shutil
import os
import logging
import platform
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s: %(message)s')
HOME_DIR = Path.home()
PROJECT_ROOT = Path(__file__).parent.parent.resolve()
LOGS_DIR = PROJECT_ROOT / 'logs'
INI_PATH = PROJECT_ROOT / 'banco.ini'
if os.name == 'nt':
    OPERA_PATH = HOME_DIR / 'AppData' / 'Roaming' / 'Opera Software' / 'Opera Stable'
else:
    OPERA_PATH = HOME_DIR / '.config' / 'opera'

def detect_active_sqlite_db(base_path: Path) -> Path | None:
    ini_file = base_path / 'banco.ini'
    if not ini_file.exists():
        return None
    active_type = None
    db_path = None
    try:
        with open(ini_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#') or line.startswith(';'):
                    continue
                if '=' in line:
                    key, value = [part.strip() for part in line.split('=', 1)]
                    if key == 'type':
                        active_type = value.lower()
                    elif key == 'path' and active_type == 'sqlite':
                        db_path = value
        if active_type == 'sqlite' and db_path:
            return base_path / db_path
    except Exception as e:
        logging.error(f'Erro ao ler banco.ini: {e}')
        return None
    return None
DB_PATH = detect_active_sqlite_db(PROJECT_ROOT)

def limpar_pycache(root_path: Path, log_func):
    log_func(f'Procurando __pycache__ em: {root_path}...')
    cache_dirs = list(root_path.rglob('__pycache__'))
    count = 0
    for path in cache_dirs:
        if path.is_dir():
            try:
                shutil.rmtree(path)
                count += 1
            except Exception as e:
                log_func(f'Falha ao remover {path.relative_to(root_path)}: {e}', 'error')
    for pyc in list(root_path.rglob('*.pyc')):
        try:
            pyc.unlink()
        except:
            pass
    if count > 0:
        log_func(f'Sucesso: {count} pastas "__pycache__" removidas.', 'info')
    else:
        log_func('Nenhuma pasta "__pycache__" encontrada.', 'info')

def limpar_logs(logs_path: Path, log_func):
    if not logs_path.exists():
        log_func('Pasta de logs não existe.', 'warning')
        return
    log_func(f'Limpando .log em: {logs_path.name}...')
    count = 0
    for log_file in logs_path.glob('*.log'):
        try:
            log_file.unlink()
            count += 1
        except Exception as e:
            log_func(f'Erro ao remover {log_file.name}: {e}', 'error')
    if count > 0:
        log_func(f'Sucesso: {count} logs removidos.', 'info')
    else:
        log_func('Nenhum log antigo encontrado.', 'info')

def executar_limpeza(vars_dict: dict, text_log: tk.Text):
    text_log.config(state='normal')
    text_log.delete('1.0', tk.END)

    def log_to_widget(message, level='info'):
        tags = {'error': 'error', 'warning': 'warning', 'info': 'info'}
        tag = tags.get(level, 'info')
        prefix = level.upper()
        text_log.insert(tk.END, f'{prefix}: {message}\n', tag)
        text_log.see(tk.END)
        if level == 'error':
            logging.error(message)
        elif level == 'warning':
            logging.warning(message)
        else:
            logging.info(message)
    if not any((var.get() for var in vars_dict.values())):
        messagebox.showwarning('Atenção', 'Selecione pelo menos uma opção.')
        return
    if not messagebox.askyesno('Confirmar', 'Tem certeza? Esta ação é irreversível.'):
        return
    log_to_widget(f'Iniciando limpeza ({platform.system()})...\n')
    if vars_dict['pycache'].get():
        limpar_pycache(PROJECT_ROOT, log_to_widget)
    if vars_dict['logs'].get():
        limpar_logs(LOGS_DIR, log_to_widget)
    if vars_dict['db'].get() and DB_PATH:
        log_to_widget(f'\nDeletando banco: {DB_PATH.name}...')
        try:
            if DB_PATH.exists():
                DB_PATH.unlink()
                log_to_widget('Banco de dados deletado.', 'info')
            else:
                log_to_widget('Arquivo do banco não encontrado.', 'warning')
        except Exception as e:
            log_to_widget(f'Falha ao deletar banco: {e}', 'error')
    if vars_dict['opera'].get():
        log_to_widget(f'\nLimpando Opera: {OPERA_PATH.name}...')
        try:
            if OPERA_PATH.exists():
                shutil.rmtree(OPERA_PATH, ignore_errors=True)
                log_to_widget('Pasta do Opera limpa (verifique se fechou o navegador).', 'info')
            else:
                log_to_widget('Pasta do Opera não encontrada.', 'warning')
        except Exception as e:
            log_to_widget(f'Falha no Opera: {e}', 'error')
    log_to_widget('\n=== Concluído ===')
    text_log.config(state='disabled')

def criar_interface():
    root = tk.Tk()
    root.title('Ferramenta de Limpeza Dev (Universal)')
    root.geometry('800x600')
    root.minsize(600, 550)
    style = ttk.Style()
    style.theme_use('clam')
    style.configure('Danger.TButton', background='#dc3545', foreground='white', font=('Segoe UI', 10, 'bold'))
    style.map('Danger.TButton', background=[('active', '#bb2d3b')])
    style.configure('Header.TLabel', font=('Segoe UI', 16, 'bold'), foreground='#005a9e')
    style.configure('Path.TLabel', font=('Consolas', 8), foreground='#666')
    main_frame = ttk.Frame(root, padding=20)
    main_frame.pack(fill='both', expand=True)
    ttk.Label(main_frame, text='🛠️ Limpeza de Ambiente', style='Header.TLabel').pack(pady=(0, 15))
    check_frame = ttk.LabelFrame(main_frame, text='Itens para Limpar', padding=15)
    check_frame.pack(fill='x', pady=(0, 15))
    vars_dict = {'pycache': tk.BooleanVar(value=True), 'logs': tk.BooleanVar(value=True), 'db': tk.BooleanVar(value=False), 'opera': tk.BooleanVar(value=False)}
    for text, var, path_desc in [('Limpar Cache Python (__pycache__)', 'pycache', 'Remove arquivos compilados corrompidos.'), ('Limpar Logs Antigos', 'logs', f'Pasta: {LOGS_DIR.name}/')]:
        f = ttk.Frame(check_frame)
        f.pack(fill='x', pady=2)
        ttk.Checkbutton(f, text=text, variable=vars_dict[var]).pack(anchor='w')
        ttk.Label(f, text=path_desc, style='Path.TLabel').pack(anchor='w', padx=20)
    ttk.Separator(check_frame, orient='horizontal').pack(fill='x', pady=10)
    f_db = ttk.Frame(check_frame)
    f_db.pack(fill='x', pady=2)
    if DB_PATH:
        db_text = f'[PERIGO] Deletar Banco de Dados ({DB_PATH.name})'
        db_state = 'normal'
        db_desc = f'Caminho detectado no banco.ini: {DB_PATH}'
    else:
        db_text = '[INDISPONÍVEL] Nenhum banco SQLite ativo encontrado no banco.ini'
        db_state = 'disabled'
        db_desc = 'Configure "type = sqlite" e "path = ..." no banco.ini para habilitar.'
    chk_db = ttk.Checkbutton(f_db, text=db_text, variable=vars_dict['db'], state=db_state)
    chk_db.pack(anchor='w')
    ttk.Label(f_db, text=db_desc, style='Path.TLabel', foreground='#dc3545' if DB_PATH else '#999').pack(anchor='w', padx=20)
    f_op = ttk.Frame(check_frame)
    f_op.pack(fill='x', pady=5)
    ttk.Checkbutton(f_op, text=f'Limpar Configuração Opera ({platform.system()})', variable=vars_dict['opera']).pack(anchor='w')
    op_path_str = str(OPERA_PATH)
    if len(op_path_str) > 70:
        op_path_str = '...' + op_path_str[-65:]
    ttk.Label(f_op, text=op_path_str, style='Path.TLabel').pack(anchor='w', padx=20)
    ttk.Button(main_frame, text='🧹 EXECUTAR LIMPEZA', style='Danger.TButton', command=lambda: executar_limpeza(vars_dict, log_text)).pack(fill='x', ipady=8, pady=(0, 15))
    log_frame = ttk.LabelFrame(main_frame, text='Log', padding=10)
    log_frame.pack(fill='both', expand=True)
    log_text = tk.Text(log_frame, height=10, bg='#1e1e1e', fg='#d4d4d4', font=('Consolas', 10), relief='flat', padx=10, pady=10)
    scrollbar = ttk.Scrollbar(log_frame, orient='vertical', command=log_text.yview)
    log_text.configure(yscrollcommand=scrollbar.set)
    log_text.pack(side='left', fill='both', expand=True)
    scrollbar.pack(side='right', fill='y')
    for tag, color in [('info', '#6A9955'), ('warning', '#DCDCAA'), ('error', '#F44747')]:
        log_text.tag_config(tag, foreground=color)
    root.mainloop()
if __name__ == '__main__':
    criar_interface()