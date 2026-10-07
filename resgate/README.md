# ECO-7 — Protocolo Aurora

Aventura 2D de ficção científica com personagens animados, mutantes, exploração,
combate e uma campanha de resgate em cinco capítulos. Lia entra na estação ECO-7
para resgatar sua irmã Nina e descobre que os pacientes de uma terapia experimental
foram ligados à consciência do diretor Voss.

## Jogar no Windows

[Baixe o pacote pronto Eco7-Windows.zip](https://github.com/R10santos/resgate/raw/refs/heads/main/Eco7-Windows.zip)
e use **Extrair Tudo...**. Abra a pasta extraída **Eco7** e dê dois cliques em
**iniciar.cmd** ou **dist/Eco7.exe**. O executável é independente:
não precisa de Python instalado nem de conexão com a internet. A janela pode ser
redimensionada; o jogo mantém a proporção e ajusta as coordenadas do mouse.

## Melhorias desta versão

- Mapa tático com rota, suprimentos, aliados e ameaças próximas; o tempo fica pausado.
- Comando de escolta para esperar ou seguir e indicador que aponta para o corredor correto.

- Câmera 50% mais próxima, luz ao redor de Lia e objetivo atual compacto; O expande a lista.
- Dispersor com cinco projéteis de curto alcance, além do plasma; números de dano,
  flashes de impacto e marcas dos inimigos derrotados melhoram a leitura do combate.
- Uma bancada por capítulo permite escolher arma (+5 dano), blindagem (+25 vida)
  ou reator (+5 energia por segundo). As melhorias acompanham os capítulos seguintes.
- Exploração: 140 de vida e 40% menos dano recebido. Normal mantém os valores
  originais. Sobrevivência: inimigos com 20% mais vida e 35% mais dano recebido.
- Descargas elétricas em manutenção e evacuação avisam em amarelo antes de ativar.
- Voss chama dois mutantes ao entrar na segunda fase.
- Ambiente sonoro sintetizado em loop; M desliga tanto o ambiente quanto os efeitos.
- Escoltas e inimigos consideram a largura do corpo ao contornar quinas.

Salvamentos anteriores continuam válidos; eles usam dificuldade Normal e começam
sem módulos que ainda não tenham sido obtidos. Como antes, somente o início do
capítulo é salvo. Aprimoramentos obtidos durante a fase são persistidos ao concluí-la.

## Controles

| Ação | Controle |
|---|---|
| Mover | WASD ou setas |
| Mirar e atirar | Mouse + botão esquerdo segurado |
| Atirar com mira assistida | J segurado; prioriza o inimigo visível mais próximo |
| Dispersor de curto alcance | Botão direito ou K; custa 20 de energia |
| Expandir / recolher objetivos | O |
| Mapa tático com rota pelos corredores | G |
| Mandar aliado esperar / seguir | C |
| Interagir, conversar, recolher, operar | E |
| Avançar diálogo | E, Enter ou clique |
| Esquiva com proteção | Espaço; 25 de energia |
| Pulso de dano e atordoamento | Q; 45 de energia |
| Usar kit médico | H |
| Diário e registros | Tab |
| Pausar / retomar | Esc |
| Alternar todo o áudio | M |

A energia se recupera. Plasma não usa munição limitada. Os kits restauram 65 de
vida; há suprimentos no mapa e alguns inimigos derrotados deixam kits. Paredes e
coberturas bloqueiam deslocamento e projéteis. As áreas vermelhas anunciam ataques.

## Campanha

1. **O último sinal — Docas:** religar o gerador, conseguir um crachá, libertar Teo
   e escoltá-lo ao abrigo.
2. **Gente sob as máquinas — Manutenção:** encontrar Ivo, protegê-lo enquanto ele
   repara os dois relés e levá-lo ao elevador.
3. **A cura e a mentira — Laboratório:** recuperar fórmula e amostra, escolher o
   destino da pesquisa e, opcionalmente, resgatar a cientista Maia.
4. **O diretor — Contenção:** romper três selos e enfrentar Voss. O chefe passa a
   lançar mais projéteis quando perde metade da vida.
5. **Ninguém fica para trás — Núcleo:** preparar o estabilizador, libertar Nina e
   levá-la à nave antes do colapso. Uma válvula amplia o prazo; a antena permite
   transmitir as provas se a pesquisa foi preservada.

Os aliados seguem caminhos pelos corredores. Se caírem, volte até eles e use E.
Não é possível completar uma escolta deixando o aliado longe da saída. Ivo precisa
estar perto dos relés, e Nina precisa estar perto da antena para autenticar o envio.
Cinco registros opcionais revelam o passado da estação. A decisão do laboratório,
a transmissão e o resgate opcional alteram o desfecho; há três finais principais.

## Checkpoints

O começo de cada capítulo é salvo em `%LOCALAPPDATA%/Eco7/campanha.json`.
Concluir um capítulo já salva o acesso ao próximo, mesmo antes de clicar em Avançar.
Derrota, saída no meio da fase ou Reiniciar capítulo retornam ao começo do capítulo,
com vida e kits restaurados. Não há salvamento da posição no meio de uma fase.
Nova campanha substitui o checkpoint anterior. Após o final, Continuar permite
repetir o último capítulo. A prévia por linha de comando não altera o save.

## Executar pelo código

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-build.txt
.\.venv\Scripts\python.exe main.py
```

`jogar.bat` também prepara o ambiente e inicia a campanha. Para reconstruir o
executável, use `gerar-executavel.bat`.

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe scripts\simulate_campaign.py
.\.venv\Scripts\python.exe main.py --headless --frames 5 --screenshot docs\eco7\teste.png
```

## Código e documentação

A campanha fica em `src/echo/`: `model.py` (regras e IA), `app.py` (interface e loop),
`art.py` (arte procedural), `story.py` (história), `sound.py` (áudio sintetizado) e
`save.py` (checkpoint). Consulte `docs/eco7/GUIA.md` e `docs/eco7/TESTES.md`.
Os personagens, cenários e efeitos são desenhados pelo código. Não há download de
recursos ao iniciar. Fontes do sistema são usadas quando disponíveis, com fallback
da própria biblioteca Pygame.

Esta versão foi implementada com assistência do Codex conforme o novo pedido do
usuário. Não foi possível reconferir o enunciado acadêmico original nesta etapa.
Os testes automatizados e o piloto automático não substituem uma avaliação humana
da dificuldade, dos controles, do ritmo narrativo e do áudio no dispositivo final.
