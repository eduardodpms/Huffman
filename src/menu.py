from src.huffman import char_count, prefix_tree, prefix_codes
from bitarray import bitarray
from tkinter import filedialog, messagebox, ttk
import tkinter as tk
import random
import math
import json
import os

# Variáveis Globais
cmprssd_folder = 'compressed/' # Pasta dos arquivos comprimidos
dcmprssd_folder = 'decompressed/' # Pasta dos arquivos descomprimidos

cmprssd_id = '_cmp' # Identificador dos arquivos comprimidos
dcmprssd_id = '_dcmp' # Identificador dos arquivos descomprimidos

bin_ext = ".huff" # Extensão do arquivo binário comprimido


# Classe do Sistema
class App():
    
    # Esquematiza a interface do tkinter
    def __init__(self, root):
        self.root = root
        self.root.title("Compactador de Textos - Huffman")
        self.root.resizable(False, False)
        self.header_bool = tk.BooleanVar()

        frame = tk.Frame(self.root, padx=32, pady=8)
        frame.pack()

        title = tk.Label(frame, text="Compressor de\nHuffman", font='sylfaen')
        btn_compress = tk.Button(frame, text="Compactar", width=12, command=self.on_compress)
        btn_decompress = tk.Button(frame, text="Descompactar", width=12, command=self.on_decompress)
        btn_exit = tk.Button(frame, text="Sair", width=12, command=self.root.destroy)
        checkbox = tk.Checkbutton(frame, text="Printar Header", variable=self.header_bool)

        title.grid(row=0, column=1, padx=0, pady=(0, 16))
        btn_compress.grid(row=1, column=1, padx=5, pady=5)
        btn_decompress.grid(row=2, column=1, padx=5, pady=5)
        btn_exit.grid(row=3, column=1, padx=5, pady=5)
        checkbox.grid(row=4, column=1, padx=5, pady=(16, 0))

################################################################################################################################


    # Abre e lê o arquivo, e salva a compressão em um binário
    def on_compress(self):
        # Selecionar arquivo para compressão
        filepath = filedialog.askopenfilename(
            title="Selecione um arquivo para compressão",
            initialdir='.',
            filetypes=[("All files", "*.*")]
        )
        if not filepath:
            return

        # Ler conteúdo do arquivo
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
        except UnicodeDecodeError as e:
            with open(filepath, 'rb') as e:
                content = bitarray()
                content.fromfile(e)
        except Exception as e:
            messagebox.showerror("Erro", f"Não foi possível ler o arquivo:\n{e}")
            return

        # Obter sequências binárias para o header e o conteúdo
        try:
            self.loading_window()
            bin_header, bin_content = self.compression(filepath, content)
        except Exception as e:
            self.lw.destroy()
            messagebox.showerror("Erro", f"Não foi possível codificar o conteúdo:\n{e}")
            return

        # Obter path do arquivo binário
        outpath = self.outpath(filepath, cmprssd_folder, cmprssd_id, bin_ext)
        self.lw.destroy()
        if not outpath:
            return
        
        # Salvar header + conteúdo serializados no arquivo
        try:
            with open(outpath, 'wb') as f:
                f.write(bin_header)
                bin_content.tofile(f)
        except Exception as e:
            messagebox.showerror("Erro", f"Não foi possível salvar o arquivo:\n{e}")
            return

        # Mensagem de saída (compressão bem-sucedida)
        sizes = f'Original: {os.path.getsize(filepath)} bytes\n' \
                f'Comprimido: {len(bin_header) + math.ceil(len(bin_content)/8)} bytes'
        messagebox.showinfo("Compressão Finalizada", f"> Conteúdo salvo em:\n{outpath}\n\n> Tamanho dos Arquivos:\n{sizes}")


    # Gera um header e codifica a sequêcia de caracteres do arquivo desejado
    def compression(self, filepath, content):
        # Obter os prefix codes
        chars = char_count(content)
        n, tree = prefix_tree(chars)
        prefix = prefix_codes(tree)

        # Codificar o conteúdo, exibindo uma barra de progresso
        bin_content = self.encoding(content, prefix)
        self.label.config(text=f"Compressão Concluída")
        self.bar['value'] = 99.99

        # Montar o header
        header = {
            'header': 0, # Quantidade de bytes do header codificado
            'content': math.ceil(len(bin_content)/8), # Quantidade de bytes do conteúdo codificado
            'string': n, # Quantidade de caracteres do conteúdo original
            'ext': os.path.splitext(filepath)[1], # Entensão do arquivo original
            'bin': 0 if type(content) == str else 1, # Se o arquivo original foi lido como binário
            'prefix': prefix # Dicionário de prefixos
        }

        # Serializar o header
        bin_header = json.dumps(header).encode('utf-8') # Serializa cada caracter do dicionário como um byte
        header['header'] = len(bin_header)-1 # Salva a quantidade de bytes do header
        
        bytes_number = len(str(header['header'])) # Quantidade de bytes da quantidade de bytes do header
        val = len(str((bytes_number + header['header']))) > bytes_number # Se haverá aumento de 1 byte
        header['header'] += bytes_number + val # Corrige o número de bytes

        size_bytes = str(header['header']).encode('utf-8') # Serializa em bytes o tamanho do header
        bin_header = b'{"header": ' + size_bytes + bin_header[12:] # Dicionário serializado, com seu próprio tamanho
        
        # Visualizar o header
        if(self.header_bool.get()):
            print(f'{'='*64}\n{int((64-len(f'header for {os.path.basename(filepath)}'))/2)*' '}' \
                  f'{f'header for {os.path.basename(filepath)}'}\n\n{header}\n{'='*64}')
        
        # Retornar header e conteúdo serializados
        return bin_header, bin_content


    # Codifica a sequêcia de caracteres do conteúdo lido
    def encoding(self, content, prefix):
        progress, bin_content = 0, bitarray('')

        for char in content:
            bin_content += bitarray(prefix[char])

            progress += 100/len(content)
            if(random.random() < 9e-6):
                self.label.config(text=f"Comprimindo Sequência: {self.bar['value']:.1f}%")
                self.bar['value'] = progress
                self.lw.update_idletasks()
        
        return bin_content


################################################################################################################################


    # Abre e lê o arquivo binário, e salva a descompressão em outro arquivo
    def on_decompress(self):
        # Selecionar arquivo para descompressão
        filepath = filedialog.askopenfilename(
            title="Selecione um arquivo binário",
            initialdir=".",
            filetypes=[("Binary files", f"*{bin_ext}")]
        )
        if not filepath:
            return

        # Ler conteúdo binário do arquivo
        try:
            with open(filepath, 'rb') as f:
                bits = bitarray()
                bits.fromfile(f)
        except Exception as e:
            messagebox.showerror("Erro", f"Não foi possível ler o arquivo:\n{e}")
            return
        
        # Obter o header e o conteúdo desserializados
        try:
            self.loading_window()
            header, content = self.decompression(bits)
        except Exception as e:
            self.lw.destroy()
            messagebox.showerror("Erro", f"Não foi possível decodificar a sequência binária:\n{e}")
            return

        # Visualizar o header
        if(self.header_bool.get()):
            print(f'{'='*64}\n{int((64-len(f'header for {os.path.basename(filepath)}'))/2)*' '}' \
                  f'{f'header for {os.path.basename(filepath)}'}\n\n{header}\n{'='*64}')

        # Obter path do arquivo de saída e fechar a janela de carregamento
        outpath = self.outpath(filepath, dcmprssd_folder, dcmprssd_id, header['ext'])
        self.lw.destroy()
        if not outpath:
            return

        # Salvar o conteúdo desserializado no arquivo
        try:
            if(not header['bin']):
                with open(outpath, 'w', encoding='utf-8') as f:
                    f.write(content)
            else:
                with open(outpath, 'wb') as f:
                    bitarray(content).tofile(f)
        except Exception as e:
            messagebox.showerror("Erro", f"Não foi possível salvar o arquivo:\n{e}")
            return
        
        # Mensagem de saída (descompressão bem-sucedida)
        sizes = f'Comprimido: {int(len(bits)/8)} bytes\n' \
                f'Descomprimido: {os.path.getsize(outpath)} bytes'
        messagebox.showinfo("Descompressão Finalizada", f"> Conteúdo salvo em:\n{outpath}\n\n> Tamanho dos Arquivos:\n{sizes}")


    # Decodifica a sequêcia de binários do arquivo desejado
    def decompression(self, bits):
        # Recuperar a quantidade de bytes do header
        header_bytes_end = bits.index(bitarray(b', '))
        header_bytes = int(bits[88:header_bytes_end].tobytes())

        # Recuperar o header e os bits do conteúdo
        header = json.loads(bits[:header_bytes*8].tobytes())
        content_bits = bits[header_bytes*8:]

        # Recuperar o conteúdo, exibindo uma barra de progresso
        content = self.decoding(content_bits, header)
        self.label.config(text=f"Descompressão Concluída")
        self.bar['value'] = 99.99
        
        # Retornar header e conteúdo desserializados
        return header, content


    # Decodifica os bits do conteúdo com base nos códigos prefixos
    def decoding(self, content_bits, header):
        prefix = {v: k for k, v in header['prefix'].items()}
        progress, content, current_prefix = 0, '', ''

        for bit in content_bits: # Itera pelos bits, procurando correspondências no dicionário de prefixos
            current_prefix += f'{bit}'

            if(current_prefix in prefix.keys()):
                content += prefix[current_prefix]
                current_prefix = ''

                progress += 100/header['string']
                if(random.random() < 9e-6):
                    self.label.config(text=f"Descomprimindo Sequência: {self.bar['value']:.1f}%")
                    self.bar['value'] = progress
                    self.lw.update_idletasks()

        # Remover caracteres extras causados pela extensão de bits do bitarray
        while(len(content) > header['string']):
            content = content[:-1]
        
        return content


################################################################################################################################


    # Retorna uma string com o path do arquivo de saída (e resolve conflitos)
    def outpath(self, filepath, outfolder, id, ext):
        # Criar o diretório de saída e obter o path desejado
        os.makedirs(outfolder, exist_ok=True)
        base, _ = os.path.splitext(os.path.basename(filepath))
        outpath = outfolder + base + id + ext

        # Verificar a existência do path desejado
        if not os.path.exists(outpath):
            return outpath
        else:
            resp = messagebox.askyesno("Sobrescrever?", f"O arquivo {os.path.basename(outpath)} já existe. Sobrescrever?")
            return filedialog.asksaveasfilename(
                defaultextension=ext,
                initialfile=base + id,
                initialdir=outfolder,
                title="Salvar como",
                filetypes=[("All files", f"*{ext}")]
            ) if not resp else outpath


    # Abre uma janela de carregamento para as operações de codificação e decodificação
    def loading_window(self):
        self.lw = tk.Toplevel(self.root)
        self.lw.title("Progresso")
        self.lw.geometry("280x80")
        self.lw.resizable(False, False)

        self.label = tk.Label(self.lw, text="Iniciando Processamento")
        self.bar = ttk.Progressbar(self.lw, length=250)
        self.label.pack(pady=10), self.bar.pack()

        self.lw.update_idletasks()
