## Para usar a CLI

Crie uma pasta vazia no seu computador, abra ela no terminal CMD ou no VS Code

Clone o repositório:
```
git clone https://github.com/JordanoPaganini/robo-rp2-framework.git . 
```
Importante incluir o . no final, para não criar pasta dentro de pasta

Crie uma virtual environment do python:
```
python -m venv venv
```

Ative a venv no terminal (cmd):
```
.\venv\scritps\activate.bat
```

Installe locamente a CLI:
```
pip install -e .\cli
```

Pronto, já pode usar:
```
robot --help
```
ou 
```
robot <command> --help
```

## Para usar e testar

Dentro da pasta que tem o clone do repositório, crie uma pasta chamada tests_cli, ela será ignorada pelo .gitignore

Entra na pasta pelo terminal:
```
cd tests_cli
```

Rode os comandos da CLI aqui. Exemplo:
```
robot start --vscode
```

OBS.: Use --vscode se estiver nessa IDE, isso criará uma pasta .vscode para fazer ele ignorar os erros de import causados por não encontrar as libs do micropython

## Sobre o comando build

Ele baixa automaicamente a biblioteca do repositório do github (https://github.com/JordanoPaganini/robo-rp2-framework.git) se não encontrar ela baixada na pasta /build

Para forçar ele a baixar novamente:
```
robot build --dl
```
Ou apague a pasta /build

Dentro da pasta /build será criado:
- main.py -> Arquivo main.py disponivel junto as códigos da biblioteca
- code.mpy -> Arquivo main.py criado com o comando start
- /robot_kit -> Criado se no project.yaml for True, é uma pasta com um clone de tudo oq há dentro de micropython-lib do repositório em formato .mpy
- /libs -> Criado se alguma arquivo for especificado em others no project.yaml e encontrado dentro da pasta /libs gerada pelo `robot start`, copia e os transforma em formato .mpy

O formato de arquivo .mpy é um bytecode própio do micropython, ele não permite ser aberto e para ser executado deve ser importado em outro arquivo .py. Exemplo:

O arquivo `code.mpy` contém o que o usuario criou de código, dentro de `main.py` é feito um `import code` o que faz o código ser executado normalmente.

OBS: A própia CLI compila os arquivos .py para .mpy

## Comandos deploy e monitor

Só vão funcionar se tiver um RP2040 conectado ao computador, e para que o resto funcione coretamente um botão com PULL_DOWN na porta 15 (Essa parte pode ser ignorado se alterado o conteudo de `micropython-lib/main.py`)

Para mais informações sobre esses comandos use:
```
robot deploy/monitor --help
```

OBS: A opção --clear do comando deploy não está funcionando
