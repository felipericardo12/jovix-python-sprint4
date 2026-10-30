import json
import os

import requests

from datetime import datetime

ARQUIVO_DADOS = "jovix_dados.json"
ARQUIVO_EXPORTACAO = "jovix_export.json"

URL_API = "https://api.ocr.space/parse/image"
CHAVE_API = "helloworld"  # chave de teste da OCR.space

# Listas de conteúdos de cada matéria
MATERIAS = {
    "Matemática": ["Álgebra", "Geometria", "Porcentagem"],
    "História": ["Revolução Francesa", "Segunda Guerra Mundial", "Descobrimento do Brasil"],
    "Geografia": ["Climatologia", "Globalização", "Hidrografia"],
}

# Palavras que a JOVIX procura no texto da imagem para descobrir o conteúdo
PALAVRAS_CHAVE = {
    "Álgebra": ["equação", "equações", "incógnita", "bhaskara", "x²", "segundo grau", "polinômio"],
    "Geometria": ["geometria", "triângulo", "hexágono", "polígono", "ângulo", "perímetro", "círculo"],
    "Porcentagem": ["porcentagem", "percentual", "desconto", "regra de três", "acréscimo"],
    "Revolução Francesa": ["revolução francesa", "bastilha", "luís xvi", "robespierre", "iluminismo"],
    "Segunda Guerra Mundial": ["segunda guerra", "nazismo", "hitler", "holocausto", "aliados", "países do eixo"],
    "Descobrimento do Brasil": ["descobrimento", "cabral", "pindorama", "caminha", "tordesilhas", "portugueses"],
    "Climatologia": ["clima", "climatologia", "temperatura", "latitude", "precipitação", "massas de ar"],
    "Globalização": ["globalização", "globalizado", "comércio mundial", "multinacional", "integração"],
    "Hidrografia": ["hidrografia", "bacia hidrográfica", "aquífero", "nascente", "afluente", "ciclo da água"],
}

# Banco de questões: cada questão tem pergunta, 3 opções e a letra certa
QUESTOES = {
    "Álgebra": [
        {"pergunta": "Qual o valor positivo de x na equação x² = 25?",
         "opcoes": ["5", "10", "15"], "certa": "a"},
        {"pergunta": "Resolva: 2x + 6 = 14. Quanto vale x?",
         "opcoes": ["3", "4", "5"], "certa": "b"},
    ],
    "Geometria": [
        {"pergunta": "Quantos lados possui um hexágono?",
         "opcoes": ["5", "6", "8"], "certa": "b"},
        {"pergunta": "Quanto vale a soma dos ângulos internos de um triângulo?",
         "opcoes": ["90 graus", "180 graus", "360 graus"], "certa": "b"},
    ],
    "Porcentagem": [
        {"pergunta": "25% de 200 é?",
         "opcoes": ["25", "40", "50"], "certa": "c"},
        {"pergunta": "Um produto de R$ 80 recebeu 10% de desconto. Qual o novo preço?",
         "opcoes": ["R$ 70", "R$ 72", "R$ 78"], "certa": "b"},
    ],
    "Revolução Francesa": [
        {"pergunta": "Qual era o lema da Revolução Francesa?",
         "opcoes": ["Ordem e progresso", "Liberdade, igualdade e fraternidade", "Paz e justiça"], "certa": "b"},
        {"pergunta": "Em que ano começou a Revolução Francesa?",
         "opcoes": ["1789", "1822", "1914"], "certa": "a"},
    ],
    "Segunda Guerra Mundial": [
        {"pergunta": "Qual país iniciou a Segunda Guerra Mundial?",
         "opcoes": ["Alemanha", "França", "Estados Unidos"], "certa": "a"},
        {"pergunta": "Em que ano terminou a Segunda Guerra Mundial?",
         "opcoes": ["1939", "1945", "1950"], "certa": "b"},
    ],
    "Descobrimento do Brasil": [
        {"pergunta": "Em que ano o Brasil foi descoberto?",
         "opcoes": ["1500", "1822", "1889"], "certa": "a"},
        {"pergunta": "Quem comandava a esquadra que chegou ao Brasil em 1500?",
         "opcoes": ["Pedro Álvares Cabral", "Dom Pedro I", "Cristóvão Colombo"], "certa": "a"},
    ],
    "Climatologia": [
        {"pergunta": "Qual fator climático influencia diretamente a temperatura de uma região?",
         "opcoes": ["Latitude", "Internet", "Satélite de TV"], "certa": "a"},
        {"pergunta": "Qual clima predomina na Floresta Amazônica?",
         "opcoes": ["Equatorial", "Polar", "Desértico"], "certa": "a"},
    ],
    "Globalização": [
        {"pergunta": "O que a globalização aumenta entre os países?",
         "opcoes": ["O isolamento", "A integração econômica e cultural", "A distância geográfica"], "certa": "b"},
        {"pergunta": "A internet ajudou a globalização porque:",
         "opcoes": ["Aproximou pessoas e mercados de países diferentes",
                    "Aumentou o isolamento entre os países",
                    "Impediu o comércio internacional"], "certa": "a"},
    ],
    "Hidrografia": [
        {"pergunta": "O que é uma bacia hidrográfica?",
         "opcoes": ["Conjunto de rios interligados", "Uma montanha", "Um tipo de clima"], "certa": "a"},
        {"pergunta": "Qual é o maior rio do Brasil em volume de água?",
         "opcoes": ["Rio São Francisco", "Rio Amazonas", "Rio Tietê"], "certa": "b"},
    ],
}


# FUNÇÕES DE ENTRADA

def ler_numero(mensagem, minimo, maximo):
    """Lê um número inteiro entre minimo e maximo e repete até ser válido."""
    while True:
        try:
            numero = int(input(mensagem))
        except ValueError:
            print("❌ Digite apenas números inteiros\n")
            continue
        if numero >= minimo and numero <= maximo:
            return numero
        print(f"❌ Opção inválida, digite um número entre {minimo} e {maximo}\n")


def ler_texto(mensagem):
    """Lê um texto e repete até o usuário digitar algo."""
    while True:
        texto = input(mensagem).strip()
        if texto != "":
            return texto
        print("❌ Este campo não pode ficar vazio\n")


def confirmar(mensagem):
    """Pergunta sim ou não. Retorna True para s e False para n."""
    while True:
        resposta = input(f"{mensagem} (s/n): ").strip().lower()
        if resposta == "s":
            return True
        if resposta == "n":
            return False
        print("❌ Responda com s ou n\n")


# FUNÇÕES DE ARQUIVO (JSON)

def dados_iniciais():
    """Retorna a estrutura de dados de um sistema novo."""
    return {"proximo_id": 1, "fotos": [], "resultados": []}


def carregar_dados():
    """Lê o arquivo JSON. Se não existir ou estiver com erro, começa do zero."""
    try:
        with open(ARQUIVO_DADOS, "r", encoding="utf-8") as arquivo:
            dados = json.load(arquivo)
        if "proximo_id" in dados and "fotos" in dados and "resultados" in dados:
            return dados
        print("⚠️ O arquivo de dados estava incompleto. Começando do zero.")
    except FileNotFoundError:
        pass
    except (json.JSONDecodeError, TypeError):
        print("⚠️ O arquivo de dados estava com problema. Começando do zero.")
    return dados_iniciais()


def salvar_dados(dados):
    """Grava os dados no arquivo JSON."""
    try:
        with open(ARQUIVO_DADOS, "w", encoding="utf-8") as arquivo:
            json.dump(dados, arquivo, ensure_ascii=False, indent=2)
    except OSError:
        print("❌ Não foi possível salvar os dados")


# FUNÇÕES DA API

def ler_imagem(caminho):
    """
    Envia a imagem para a API OCR.space e retorna o texto lido.
    Se der qualquer erro, mostra uma mensagem e retorna texto vazio.
    """
    if not os.path.exists(caminho):
        print("❌ Arquivo não encontrado")
        return ""
    if os.path.getsize(caminho) > 1024 * 1024:
        print("❌ A imagem tem mais de 1 MB. Use uma imagem menor")
        return ""

    try:
        with open(caminho, "rb") as arquivo:
            resposta = requests.post(
                URL_API,
                files={"file": arquivo},
                data={"apikey": CHAVE_API, "language": "por"},
                timeout=30,
            )
        resposta.raise_for_status()
        resultado = resposta.json()
        if resultado["IsErroredOnProcessing"]:
            print("❌ A API não conseguiu ler a imagem")
            return ""
        return resultado["ParsedResults"][0]["ParsedText"]
    except requests.exceptions.ConnectionError:
        print("❌ Sem conexão com a internet")
    except requests.exceptions.Timeout:
        print("❌ A API demorou demais para responder")
    except (requests.exceptions.RequestException, ValueError, KeyError, IndexError):
        print("❌ Erro ao usar a API de leitura de imagens")
    return ""


def identificar_conteudo(texto):
    """
    Procura as palavras-chave no texto.
    Retorna a matéria e o conteúdo com mais palavras encontradas,
    ou (None, None) se não encontrar nenhuma.
    """
    texto = texto.lower()
    melhor_materia = None
    melhor_conteudo = None
    melhor_pontos = 0

    for materia in MATERIAS:
        for conteudo in MATERIAS[materia]:
            pontos = 0
            for palavra in PALAVRAS_CHAVE[conteudo]:
                if palavra in texto:
                    pontos += 1
            if pontos > melhor_pontos:
                melhor_pontos = pontos
                melhor_materia = materia
                melhor_conteudo = conteudo

    return melhor_materia, melhor_conteudo


# FUNÇÕES DE NAVEGAÇÃO

def escolher_materia():
    """
    Mostra o menu de matérias.
    Retorna dois valores: o nome da matéria e a lista de conteúdos dela.
    Se o usuário escolher "Voltar", retorna (None, None).
    """
    nomes = list(MATERIAS.keys())
    print("\n📚 Escolha uma matéria")
    for i in range(len(nomes)):
        print(f"{i + 1} - {nomes[i]}")
    print(f"{len(nomes) + 1} - Voltar")

    op = ler_numero("Escolha: ", 1, len(nomes) + 1)
    if op == len(nomes) + 1:
        return None, None
    materia = nomes[op - 1]
    return materia, MATERIAS[materia]


def escolher_conteudo(materia_atual, cont):
    """
    Mostra os conteúdos de uma matéria.
    Parâmetros: nome da matéria (para exibir) e a lista de conteúdos dela.
    Retorno: o nome do conteúdo escolhido.
    """
    print(f"\n📘 Conteúdos de {materia_atual}")
    for i in range(len(cont)):
        print(f"{i + 1} - {cont[i]}")

    op = ler_numero("Escolha: ", 1, len(cont))
    return cont[op - 1]


# FUNÇÕES DE FUNCIONALIDADE

def mostrar_pergunta(pergunta, opcoes, resposta_certa):
    """
    Mostra uma pergunta de múltipla escolha e valida a resposta do usuário.
    Parâmetros: o texto da pergunta, a lista com as 3 opções e a letra correta.
    Retorno: True se o usuário acertou, False se errou.
    """
    letras = ["a", "b", "c"]
    print(f"\n{pergunta}")
    for i in range(3):
        print(f"{letras[i].upper()} - {opcoes[i]}")

    while True:
        resposta = input("Resposta: ").strip().lower()
        if resposta in letras:
            break
        print("❌ Digite apenas A, B ou C\n")

    if resposta == resposta_certa:
        print("✅ Correto")
        return True

    texto_certo = opcoes[letras.index(resposta_certa)]
    print("❌ Errado")
    print("⚙️ JOVIX ESTÁ PENSANDO ⚙️")
    print(f"🤖 JOVIX: A resposta correta é {texto_certo}")
    return False


def banco_questoes(dados, materia, conteudo):
    """
    Faz todas as questões do conteúdo escolhido e guarda o resultado no JSON.
    Retorno: quantidade de acertos.
    """
    questoes = QUESTOES[conteudo]
    acertos = 0

    for questao in questoes:
        if mostrar_pergunta(questao["pergunta"], questao["opcoes"], questao["certa"]):
            acertos += 1

    print(f"\n🏆 Você acertou {acertos} de {len(questoes)}")
    dados["resultados"].append({
        "materia": materia,
        "conteudo": conteudo,
        "acertos": acertos,
        "total": len(questoes),
        "data": datetime.now().strftime("%d/%m/%Y %H:%M"),
    })
    salvar_dados(dados)
    input("\nDigite qualquer tecla para voltar: ")
    return acertos


def fotos_do_conteudo(dados, conteudo):
    """Retorna a lista de fotos salvas em um conteúdo."""
    lista = []
    for foto in dados["fotos"]:
        if foto["conteudo"] == conteudo:
            lista.append(foto)
    return lista


def mostrar_galeria(fotos):
    """Mostra as fotos de uma lista com a descrição de cada uma."""
    print("\n🖼️ GALERIA JOVIX")
    print("━━━━━━━━━━━━━━━━━━━━━━")
    for foto in fotos:
        nome = os.path.basename(foto["arquivo"]) if foto["arquivo"] != "" else "texto digitado"
        print(f"📸 [{foto['id']}] {nome} - {foto['data']}")
        print(f"📝 {foto['texto'][:60]}\n")


def buscar_foto(fotos, id_foto):
    """Procura uma foto pelo id. Retorna a foto ou None."""
    for foto in fotos:
        if foto["id"] == id_foto:
            return foto
    return None


def galeria(dados, conteudo):
    """Mostra as fotos do conteúdo e permite mover ou excluir uma foto."""
    while True:
        fotos = fotos_do_conteudo(dados, conteudo)
        if len(fotos) == 0:
            print("\n🖼️ Nenhuma imagem neste conteúdo ainda. Use o Modo JOVIX para adicionar.")
            input("Digite qualquer tecla para voltar: ")
            return

        mostrar_galeria(fotos)
        print("1 - Mover uma foto para outro conteúdo")
        print("2 - Excluir uma foto")
        print("3 - Voltar")
        op = ler_numero("Escolha: ", 1, 3)

        if op == 3:
            return

        id_foto = ler_numero("ID da foto (0 para cancelar): ", 0, dados["proximo_id"])
        if id_foto == 0:
            continue
        foto = buscar_foto(fotos, id_foto)
        if foto is None:
            print("❌ Essa foto não está neste conteúdo")
            continue

        if op == 1:
            nova_materia, cont = escolher_materia()
            if nova_materia is None:
                continue
            novo_conteudo = escolher_conteudo(nova_materia, cont)
            foto["materia"] = nova_materia
            foto["conteudo"] = novo_conteudo
            salvar_dados(dados)
            print(f"✅ Foto movida para {novo_conteudo}")
        else:
            if confirmar("Tem certeza que deseja excluir?"):
                dados["fotos"].remove(foto)
                salvar_dados(dados)
                print("✅ Foto excluída")


def salvar_foto(dados, caminho, texto, materia, conteudo):
    """Cria o registro da foto, guarda no JSON e retorna o registro."""
    foto = {
        "id": dados["proximo_id"],
        "arquivo": caminho,
        "texto": texto,
        "materia": materia,
        "conteudo": conteudo,
        "data": datetime.now().strftime("%d/%m/%Y %H:%M"),
    }
    dados["proximo_id"] += 1
    dados["fotos"].append(foto)
    salvar_dados(dados)
    return foto


def modo_jovix(dados):
    """A IA analisa uma imagem enviada pelo usuário e organiza na pasta certa."""
    print("\n📸 MODO JOVIX")
    print("1 - Enviar imagem (a IA lê o texto)")
    print("2 - Digitar o texto da lousa (sem internet)")
    print("3 - Voltar")
    op = ler_numero("Escolha: ", 1, 3)
    if op == 3:
        return

    caminho = ""
    texto = ""
    if op == 1:
        caminho = ler_texto("Caminho da imagem: ").strip('"')
        print("📸 IA analisando imagem...")
        texto = ler_imagem(caminho)
        if texto == "" and confirmar("Deseja digitar o texto da lousa?"):
            op = 2
    if op == 2:
        texto = ler_texto("Digite o texto da lousa: ")
    if texto == "":
        print("❌ Nenhum texto para analisar. A imagem não foi salva")
        input("Digite qualquer tecla para voltar: ")
        return

    materia, conteudo = identificar_conteudo(texto)
    if materia is None:
        print("🤔 Não consegui identificar a matéria")
        if not confirmar("Deseja escolher a matéria manualmente?"):
            print("A imagem não foi salva")
            input("Digite qualquer tecla para voltar: ")
            return
    else:
        print(f"✅ Matéria identificada: {materia} ({conteudo})")
        if not confirmar("A identificação está correta?"):
            materia = None

    if materia is None:
        materia, cont = escolher_materia()
        if materia is None:
            print("A imagem não foi salva")
            input("Digite qualquer tecla para voltar: ")
            return
        conteudo = escolher_conteudo(materia, cont)

    foto = salvar_foto(dados, caminho, texto, materia, conteudo)
    print(f"🤖 Imagem {foto['id']} adicionada na pasta {materia} > {conteudo}")
    input("Digite qualquer tecla para voltar: ")


def desempenho(dados):
    """Mostra quantas fotos e quantas questões acertadas existem por matéria."""
    print("\n📊 MEU DESEMPENHO")
    print(f"Total de imagens salvas: {len(dados['fotos'])}")

    for materia in MATERIAS:
        qtd_fotos = 0
        for foto in dados["fotos"]:
            if foto["materia"] == materia:
                qtd_fotos += 1

        acertos = 0
        total = 0
        for resultado in dados["resultados"]:
            if resultado["materia"] == materia:
                acertos += resultado["acertos"]
                total += resultado["total"]

        if total > 0:
            porcentagem = acertos / total * 100
            print(f"{materia}: {qtd_fotos} imagem(ns) | {acertos}/{total} acertos ({porcentagem:.0f}%)")
        else:
            print(f"{materia}: {qtd_fotos} imagem(ns) | nenhuma questão respondida")

    input("\nDigite qualquer tecla para voltar: ")


def exportar(dados):
    """Gera um arquivo JSON com os dados para o site do projeto."""
    try:
        with open(ARQUIVO_EXPORTACAO, "w", encoding="utf-8") as arquivo:
            json.dump({"fotos": dados["fotos"], "resultados": dados["resultados"]},
                      arquivo, ensure_ascii=False, indent=2)
        print(f"✅ Arquivo {ARQUIVO_EXPORTACAO} criado")
    except OSError:
        print("❌ Não foi possível criar o arquivo")
    input("Digite qualquer tecla para voltar: ")


# MENUS

def menu_conteudo(dados, materia, conteudo):
    """Loop do menu de um conteúdo: Banco de Questões / Galeria / Voltar."""
    while True:
        print(f"\n📘 {conteudo}")
        print("1 - Banco de Questões")
        print("2 - Imagens da Galeria")
        print("3 - Voltar")

        op = ler_numero("Escolha: ", 1, 3)

        if op == 1:
            banco_questoes(dados, materia, conteudo)
        elif op == 2:
            galeria(dados, conteudo)
        elif op == 3:
            break


def menu_pasta_materias(dados):
    """Loop da 'Pasta Matérias': escolhe matéria, depois conteúdo, depois abre o menu dele."""
    while True:
        materia_atual, cont = escolher_materia()

        if materia_atual is None:
            break  # usuário escolheu Voltar

        conteudo = escolher_conteudo(materia_atual, cont)
        menu_conteudo(dados, materia_atual, conteudo)


def menu_principal():
    """Loop principal do sistema."""
    dados = carregar_dados()

    while True:
        titulo = "JOVIX"
        print(f"\n{titulo:^20}")
        print("1 - Modo JOVIX")
        print("2 - Pasta Matérias")
        print("3 - Meu desempenho")
        print("4 - Exportar dados")
        print("5 - Sair")

        op = ler_numero("Escolha: ", 1, 5)

        if op == 1:
            modo_jovix(dados)
        elif op == 2:
            menu_pasta_materias(dados)
        elif op == 3:
            desempenho(dados)
        elif op == 4:
            exportar(dados)
        elif op == 5:
            salvar_dados(dados)
            print("👋 Saindo do JOVIX...")
            break


# INÍCIO DO PROGRAMA

if __name__ == "__main__":
    menu_principal()
