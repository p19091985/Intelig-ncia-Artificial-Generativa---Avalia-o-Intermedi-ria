import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path
import os
import sys
CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
PERSISTENCIA_DIR = PROJECT_ROOT / 'persistencia'
DDL_FILE = CURRENT_DIR / 'sql_schema_DDL.sql'
DML_FILE = CURRENT_DIR / 'sql_schema_DML.sql'
ORIGINAL_FILE = PERSISTENCIA_DIR / 'sql_schema_SQLLite.sql'

class SchemaGeneratorApp:

    def __init__(self, root):
        self.root = root
        self.root.title('⚙️ Gerador de Schema SQL (DDL/DML)')
        self.root.geometry('650x350')
        self.root.resizable(False, False)
        self._setup_styles()
        self.create_widgets()

    def _setup_styles(self):
        style = ttk.Style()
        try:
            style.theme_use('clam')
        except:
            pass
        style.configure('TLabel', font=('Segoe UI', 10))
        style.configure('Header.TLabel', font=('Segoe UI', 12, 'bold'), foreground='#005a9e')
        style.configure('Success.TButton', background='#28a745', foreground='white', font=('Segoe UI', 10, 'bold'))
        style.map('Success.TButton', background=[('active', '#218838')])

    def create_widgets(self):
        main_frame = ttk.Frame(self.root, padding=20)
        main_frame.pack(fill='both', expand=True)
        ttk.Label(main_frame, text='Reconstrução do Schema SQLite', style='Header.TLabel').pack(pady=(0, 10))
        ttk.Label(main_frame, text='Esta ferramenta lê os arquivos DDL e DML, e os une para criar o arquivo principal de inicialização.', wraplength=600).pack(anchor='w', pady=(0, 5))
        ttk.Label(main_frame, text=f'Lê Definição: {DDL_FILE.name}', foreground='#28a745').pack(anchor='w', padx=20)
        ttk.Label(main_frame, text=f'Lê Dados: {DML_FILE.name}', foreground='#17a2b8').pack(anchor='w', padx=20)
        ttk.Label(main_frame, text=f'Gera Arquivo Final: {ORIGINAL_FILE.name}', foreground='#005a9e').pack(anchor='w', padx=20)
        ttk.Label(main_frame, text=f'\nOrigem: {CURRENT_DIR}\nDestino: {PERSISTENCIA_DIR}', font=('Consolas', 8)).pack(anchor='w', pady=(10, 5))
        ttk.Separator(main_frame, orient=tk.HORIZONTAL).pack(fill='x', pady=10)
        self.generate_button = ttk.Button(main_frame, text='💾 GERAR ARQUIVO sql_schema_SQLLite.sql', command=self.generate_files, style='Success.TButton')
        self.generate_button.pack(fill='x', ipady=10, pady=(10, 0))
        self.status_label = ttk.Label(main_frame, text='', foreground='black')
        self.status_label.pack(anchor='w', pady=10)

    def generate_files(self):
        try:
            PERSISTENCIA_DIR.mkdir(parents=True, exist_ok=True)
            with open(DDL_FILE, 'r', encoding='utf-8') as f:
                ddl_content = f.read()
            with open(DML_FILE, 'r', encoding='utf-8') as f:
                dml_content = f.read()
            # Strip BEGIN TRANSACTION and COMMIT from DML since DDL already wraps them
            dml_clean = dml_content.replace('BEGIN TRANSACTION;', '', 1).replace('COMMIT;', '', 1)
            full_content = ddl_content.rstrip() + '\n' + dml_clean.strip() + '\n'
            with open(ORIGINAL_FILE, 'w', encoding='utf-8') as f:
                f.write(full_content)
            self.status_label.config(text=f"✅ Sucesso! O arquivo '{ORIGINAL_FILE.name}' foi reconstruído.", foreground='green')
            messagebox.showinfo('Sucesso', f'O arquivo {ORIGINAL_FILE.name} foi gerado com a união de DDL e DML.\nLocal: {PERSISTENCIA_DIR}')
        except FileNotFoundError as e:
            self.status_label.config(text=f'❌ Erro: Arquivo não encontrado.', foreground='red')
            messagebox.showerror('Erro de Arquivo', f'Não foi possível encontrar os arquivos fonte.\nEsperado em: {CURRENT_DIR}\nErro: {e}')
        except Exception as e:
            self.status_label.config(text=f'❌ Erro crítico: {e}', foreground='red')
            messagebox.showerror('Erro Crítico', f'Falha ao processar: {e}')
if __name__ == '__main__':
    root = tk.Tk()
    app = SchemaGeneratorApp(root)
    root.mainloop()