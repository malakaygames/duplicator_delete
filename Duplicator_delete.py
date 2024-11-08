import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import hashlib
from collections import defaultdict
from pathlib import Path
import threading

class DuplicateFinderApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Localizador de Arquivos Duplicados")
        self.root.geometry("800x600")
        
        # Configuração do tema
        style = ttk.Style()
        style.theme_use('clam')
        
        # Variáveis
        self.folder_path = tk.StringVar()
        self.status_var = tk.StringVar()
        self.status_var.set("Aguardando seleção da pasta...")
        self.duplicates = defaultdict(list)
        
        self.create_widgets()
        self.center_window()
        
    def center_window(self):
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')
        
    def create_widgets(self):
        # Frame principal
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Botão de seleção de pasta
        select_button = ttk.Button(main_frame, text="Selecionar Pasta", command=self.select_folder)
        select_button.pack(pady=10)
        
        # Label para mostrar o caminho selecionado
        path_label = ttk.Label(main_frame, textvariable=self.folder_path, wraplength=700)
        path_label.pack(pady=5)
        
        # Barra de progresso
        self.progress = ttk.Progressbar(main_frame, mode='indeterminate')
        self.progress.pack(fill=tk.X, pady=10)
        
        # Status
        status_label = ttk.Label(main_frame, textvariable=self.status_var)
        status_label.pack(pady=5)
        
        # Treeview para mostrar resultados
        self.tree = ttk.Treeview(main_frame, columns=('Tamanho', 'Caminho'), show='headings')
        self.tree.heading('Tamanho', text='Tamanho (bytes)')
        self.tree.heading('Caminho', text='Caminho do Arquivo')
        self.tree.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Scrollbar para o Treeview
        scrollbar = ttk.Scrollbar(main_frame, orient=tk.VERTICAL, command=self.tree.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        # Botão para remover duplicados
        self.remove_button = ttk.Button(main_frame, text="Remover Duplicados", 
                                      command=self.remove_duplicates, state=tk.DISABLED)
        self.remove_button.pack(pady=10)
        
    def select_folder(self):
        folder_selected = filedialog.askdirectory()
        if folder_selected:
            self.folder_path.set(folder_selected)
            self.status_var.set("Iniciando busca por duplicados...")
            self.tree.delete(*self.tree.get_children())
            self.progress.start()
            self.remove_button.config(state=tk.DISABLED)
            
            # Iniciar busca em uma thread separada
            thread = threading.Thread(target=self.find_duplicates, args=(folder_selected,))
            thread.daemon = True
            thread.start()
            
    def calculate_hash(self, filepath):
        """Calcula o hash MD5 de um arquivo."""
        hash_md5 = hashlib.md5()
        with open(filepath, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    
    def find_duplicates(self, folder_path):
        """Encontra arquivos duplicados baseado no conteúdo."""
        self.duplicates.clear()
        
        try:
            # Primeiro, agrupa arquivos por tamanho
            size_dict = defaultdict(list)
            for root, _, files in os.walk(folder_path):
                for filename in files:
                    filepath = os.path.join(root, filename)
                    try:
                        file_size = os.path.getsize(filepath)
                        size_dict[file_size].append(filepath)
                    except (OSError, PermissionError):
                        continue
            
            # Para arquivos do mesmo tamanho, calcula o hash
            for size, files in size_dict.items():
                if len(files) > 1:
                    hash_dict = defaultdict(list)
                    for filepath in files:
                        try:
                            file_hash = self.calculate_hash(filepath)
                            hash_dict[file_hash].append(filepath)
                        except (OSError, PermissionError):
                            continue
                    
                    # Adiciona apenas os grupos com duplicados
                    for file_hash, filepath_list in hash_dict.items():
                        if len(filepath_list) > 1:
                            self.duplicates[file_hash] = filepath_list
            
            self.root.after(0, self.update_results)
            
        except Exception as e:
            self.root.after(0, lambda: self.status_var.set(f"Erro: {str(e)}"))
            self.root.after(0, self.progress.stop)
    
    def update_results(self):
        """Atualiza a interface com os resultados encontrados."""
        self.progress.stop()
        self.tree.delete(*self.tree.get_children())
        
        if not self.duplicates:
            self.status_var.set("Nenhum arquivo duplicado encontrado.")
            return
        
        for file_hash, filepath_list in self.duplicates.items():
            group = self.tree.insert("", "end", text=file_hash)
            file_size = os.path.getsize(filepath_list[0])
            
            for filepath in filepath_list:
                self.tree.insert(group, "end", values=(file_size, filepath))
        
        total_duplicates = sum(len(files) - 1 for files in self.duplicates.values())
        self.status_var.set(f"Encontrados {total_duplicates} arquivos duplicados.")
        self.remove_button.config(state=tk.NORMAL)
    
    def remove_duplicates(self):
        """Remove os arquivos duplicados, mantendo apenas uma cópia de cada."""
        if not messagebox.askyesno("Confirmar", 
                                 "Isto removerá todos os arquivos duplicados, mantendo apenas uma cópia de cada.\n"
                                 "Deseja continuar?"):
            return
        
        removed_count = 0
        for filepath_list in self.duplicates.values():
            # Mantém o primeiro arquivo e remove os outros
            for filepath in filepath_list[1:]:
                try:
                    os.remove(filepath)
                    removed_count += 1
                except (OSError, PermissionError) as e:
                    messagebox.showerror("Erro", f"Não foi possível remover {filepath}\nErro: {str(e)}")
        
        messagebox.showinfo("Concluído", f"Foram removidos {removed_count} arquivos duplicados.")
        self.select_folder()  # Atualiza a lista

if __name__ == "__main__":
    root = tk.Tk()
    app = DuplicateFinderApp(root)
    root.mainloop()