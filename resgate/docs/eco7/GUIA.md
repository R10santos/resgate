# Guia do código — campanha ECO-7

## Organização

- main.py: entrada da campanha e diagnósticos de execução.
- src/echo/model.py: mapas, colisões, combate, IA, resgate e objetivos.
- src/echo/app.py: eventos, menus, pausa, diálogo, dificuldade e seleção de módulo.
- src/echo/art.py: sprites procedurais, cenários, câmera, HUD e feedback visual.
- src/echo/story.py: capítulos, documentos, decisões e finais.
- src/echo/save.py: checkpoints validados, incluindo dificuldade e módulos.
- src/echo/sound.py: efeitos e ambiente sintetizados em memória.

## Simulação e apresentação

A física recebe dt em segundos e divide o movimento em subpassos de até 1/90 s.
As diagonais são normalizadas. Paredes bloqueiam o corpo e os projéteis. A cena é
ampliada em 1,5x; a interface permanece em resolução nativa de 1200 × 720.
world_to_screen e screen_to_world fazem as transformações inversas da câmera,
mantendo a mira consistente com o zoom e com a janela redimensionada.

A IA verifica se o corpo cabe no caminho direto. Caso contrário, procura um
caminho na grade por busca em largura. Visão e passagem física usam raios
diferentes: enxergar através de uma quina não significa conseguir atravessá-la.
A escolta pode cair e ser recuperada, mas deve chegar à saída para concluir o resgate.

## Combate e progressão

O plasma usa recarga curta. O dispersor lança cinco projéteis em leque, com alcance
curto, custo de energia e recarga próprios. Pulso atordoa e esquiva concede uma
janela de proteção. Dano também gera uma proteção breve contra impactos simultâneos.

Cada bancada oferece somente um módulo por capítulo: arma, blindagem ou reator.
As melhorias e a dificuldade são propagadas no checkpoint. Salvamentos antigos
recebem valores padrão compatíveis. Reiniciar o capítulo recupera seu estado inicial.
Descargas elétricas têm estados desligado, aviso e ativo. O chefe convoca reforços
uma única vez quando sua vida cai abaixo da metade.

## Validação

Os testes da campanha estão em tests/test_campaign.py e tests/test_improvements.py.
O piloto scripts/simulate_campaign.py atravessa o mapa pelas regras reais.
As capturas de scripts/capture_screens.py são cenas configuradas para revisão visual.
Consulte TESTES.md e simulacao.json para resultados e limites de validação.


## Navegação e escolta

G abre o mapa tático e pausa a simulação. A rota usa a mesma busca de caminhos
da IA e considera paredes; o HUD reutiliza essa rota em vez de apontar através
das paredes. C alterna a escolta entre esperar e seguir. Aliados caídos precisam
ser levantados com E, e a saída continua exigindo que estejam próximos.
