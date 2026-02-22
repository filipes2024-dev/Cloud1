# Guia de instalação no Termux (Android)

## 1. Instalar o Termux

Baixe o Termux pelo **F-Droid** (recomendado — versão atualizada):
- https://f-droid.org/packages/com.termux/

> Evite a versão da Play Store, ela está desatualizada.

---

## 2. Configurar o Termux

Abra o Termux e execute:

```bash
# Atualizar pacotes
pkg update && pkg upgrade -y

# Instalar dependências do sistema
pkg install python ffmpeg -y

# Liberar acesso ao armazenamento do Android
termux-setup-storage
```

Após `termux-setup-storage`, aparecer uma caixa pedindo permissão — **aceite**.

Agora você pode acessar seus arquivos de áudio via:

| Pasta no Termux              | Equivale a (Android)         |
|------------------------------|------------------------------|
| `~/storage/downloads/`       | Downloads                    |
| `~/storage/dcim/`            | Câmera / DCIM                |
| `~/storage/music/`           | Músicas                      |
| `~/storage/shared/`          | Armazenamento interno (raiz) |

---

## 3. Instalar o script

```bash
# Clonar o repositório
git clone <URL_DO_REPOSITORIO>
cd Cloud1

# Instalar dependências Python
pip install SpeechRecognition
```

> **Nota:** O ffmpeg já foi instalado via `pkg install ffmpeg` — ele converte
> mp3/m4a/ogg para WAV automaticamente antes da transcrição.

---

## 4. Usar o script (Google Speech — online)

```bash
# Áudio na pasta Downloads
python transcribe_termux.py ~/storage/downloads/audio.mp3

# Especificar idioma
python transcribe_termux.py ~/storage/downloads/audio.mp3 --language pt-BR

# Salvar a transcrição em arquivo
python transcribe_termux.py ~/storage/downloads/audio.mp3 --output ~/storage/downloads/transcricao.txt

# Modo detalhado
python transcribe_termux.py ~/storage/downloads/audio.mp3 --verbose
```

---

## 5. Opção OFFLINE com Vosk (sem internet)

Se você não quiser depender de internet, use o **Vosk**.

### 5.1 Instalar Vosk

```bash
pip install vosk
```

### 5.2 Baixar modelo em português

```bash
cd ~
# Modelo pequeno para português (~40 MB, recomendado para Android)
wget https://alphacephei.com/vosk/models/vosk-model-small-pt-0.3.zip
unzip vosk-model-small-pt-0.3.zip
```

### 5.3 Transcrever offline

```bash
python transcribe_termux.py ~/storage/downloads/audio.mp3 \
  --engine vosk \
  --model-path ~/vosk-model-small-pt-0.3
```

---

## Comparação dos modos

| Característica     | Google (online)       | Vosk (offline)            |
|--------------------|-----------------------|---------------------------|
| Internet           | Necessária            | Não precisa               |
| Precisão pt-BR     | Alta                  | Boa (modelo small)        |
| Instalação         | Simples               | Baixar modelo (~40 MB)    |
| Velocidade         | Depende da conexão    | Depende do celular        |
| Privacidade        | Áudio vai ao Google   | 100% local                |

---

## Dicas

- **Áudio longo**: grave em partes menores para melhor precisão.
- **Qualidade**: áudio com menos ruído de fundo = melhor transcrição.
- **Formatos suportados**: `.mp3`, `.mp4`, `.wav`, `.flac`, `.ogg`, `.m4a`, `.webm`
- **Gravar direto no Termux**: `pkg install termux-api` e use `termux-microphone-record`.

---

## Solução de problemas

**`ffmpeg: not found`**
```bash
pkg install ffmpeg -y
```

**`Permission denied` ao acessar o armazenamento**
```bash
termux-setup-storage
# Aceite a permissão de armazenamento no popup
```

**`Could not understand audio`** (Google)
- Verifique se o áudio tem fala clara
- Tente especificar `--language pt-BR` explicitamente

**Erro de rede**
- Verifique a conexão com a internet
- Use `--engine vosk` para modo offline
