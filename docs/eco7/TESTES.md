# Validação atual — ECO-7

A suíte atual contém **28 testes**, todos aprovados. São os 25 testes da campanha
que permaneceram após a limpeza, mais três casos de mapa, rota e comando de escolta.
Os 32 testes do protótipo espacial foram removidos junto com seu código isolado.

Cobertura: progressão e finais, colisões e projéteis, dificuldade, módulos,
dispersor, piso elétrico, fases do chefe, escolta e quinas, mapas acessíveis,
persistência compatível, falha de disco, pausa, eventos e transformação da mira.
Os novos casos verificam a pausa do mapa, a rota por células livres, a mudança
segundo o objetivo, o aliado esperando/seguindo e o bloqueio da saída sem escolta.

Comando: `.venv/Scripts/python.exe -m unittest discover -s tests -q`.

## Percursos completos

`scripts/simulate_campaign.py` concluiu os cinco capítulos nas três dificuldades,
nas duas decisões do laboratório: seis percursos. Não usa teleporte ou vida
infinita. Usa combate, módulos e escolta pelas regras reais. Os resultados atuais
estão em `simulacao.json`. O piloto conhece os caminhos e lê instantaneamente;
seus tempos não representam duração ou diversão de uma partida humana.

## Interface e distribuição

As capturas produzidas por `scripts/capture_screens.py` são cenas configuradas para
revisão visual. O mapa foi inspecionado, incluindo legenda, objetivo, caminho e
botão de retorno. O executável é reconstruído após as alterações e submetido a
inicialização gráfica de duração limitada. O ZIP é verificado por CRC e inclui
somente o executável atual, fontes, testes, scripts, documentos e licenças.

## Limites

Não foi realizada uma partida humana completa nem avaliação auditiva no equipamento
do usuário. O executável é testado nesta máquina, não em outra instalação limpa.
O enunciado acadêmico original não estava disponível para uma nova conferência.
