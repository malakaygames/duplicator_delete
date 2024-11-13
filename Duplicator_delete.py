import os
import hashlib
from collections import defaultdict
import tkinter as tk
from tkinter import filedialog, messagebox

def calculate_file_hash(filepath):
    """Calcula o hash SHA-256 do conteúdo do arquivo."""
    hasher = hashlib.sha256()
    with open(filepath, 'rb') as file:
        # Lê o arquivo em chunks para lidar com arquivos grandes
        chunk = file.read(65536)  # 64kb chunks
        while chunk:
            hasher.update(chunk)
            chunk = file.read(65536)
    return hasher.hexdigest()

def find_duplicates(directory):
    """Encontra arquivos duplicados em um diretório e suas subpastas."""
    hash_map = defaultdict(list)
    total_files = 0
    
    # Percorre recursivamente o diretório
    for root, _, files in os.walk(directory):
        for filename in files:
            total_files += 1
            filepath = os.path.join(root, filename)
            try:
                file_hash = calculate_file_hash(filepath)
                hash_map[file_hash].append(filepath)
            except (IOError, OSError) as e:
                print(f"Erro ao processar arquivo {filepath}: {e}")
    
    # Filtra apenas os hashes que têm duplicatas
    duplicates = {k: v for k, v in hash_map.items() if len(v) > 1}
    return duplicates, total_files

def delete_files(files):
    """Deleta uma lista de arquivos."""
    for file in files:
        try:
            os.remove(file)
            print(f"Deletado: {file}")
        except OSError as e:
            print(f"Erro ao deletar {file}: {e}")

def main():
    root = tk.Tk()
    root.withdraw()  # Esconde a janela principal
    
    # Solicita ao usuário selecionar uma pasta
    print("Selecione a pasta para procurar arquivos duplicados...")
    directory = filedialog.askdirectory(title="Selecione a pasta para analisar")
    
    if not directory:
        print("Nenhuma pasta selecionada. Encerrando...")
        return
    
    print(f"\nAnalisando arquivos em: {directory}")
    print("Isso pode levar alguns minutos dependendo da quantidade de arquivos...\n")
    
    duplicates, total_files = find_duplicates(directory)
    
    if not duplicates:
        print(f"Nenhum arquivo duplicado encontrado entre os {total_files} arquivos analisados.")
        return
    
    # Mostra os resultados
    print(f"\nEncontrados {sum(len(v) - 1 for v in duplicates.values())} arquivos duplicados "
          f"em {total_files} arquivos analisados:")
    
    for hash_value, file_list in duplicates.items():
        print(f"\nGrupo de arquivos idênticos (hash: {hash_value[:8]}...):")
        for i, file in enumerate(file_list, 1):
            print(f"{i}. {file}")
    
    # Pergunta se o usuário quer deletar as duplicatas
    while True:
        response = input("\nDeseja deletar os arquivos duplicados? (s/n): ").lower()
        if response in ['s', 'n']:
            break
        print("Por favor, responda com 's' para sim ou 'n' para não.")
    
    if response == 's':
        for hash_value, file_list in duplicates.items():
            # Mantém o primeiro arquivo e deleta os demais
            delete_files(file_list[1:])
        print("\nArquivos duplicados foram deletados.")
    else:
        print("\nNenhum arquivo foi deletado.")

if __name__ == "__main__":
    main()
