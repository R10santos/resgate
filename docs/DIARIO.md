
## 30/09/2026 - Marco 6: revisão de experiência

A pedido do usuário (melhore), a campanha recebeu câmera ampliada, HUD compacto,
mira consistente com zoom, dispersor, feedback de dano, módulos de arma/blindagem/
reator, três dificuldades, descargas elétricas anunciadas e reforços do chefe.
Adicionado ambiente sonoro sintetizado em loop, controlado pelo mesmo mute.
A leitura dos checkpoints aceita os campos novos e preserva arquivos anteriores.

A simulação encontrou uma quina com linha de visão livre, mas sem passagem para
o corpo. Corrigida a navegação de escoltas e inimigos; criado teste de regressão.
57 testes passaram, e seis percursos completos combinaram três dificuldades com
as duas escolhas do laboratório. Telas e documentos foram atualizados.
A avaliação humana de ritmo, diversão e som continua pendente.

## 30/09/2026 - Marco 7: limpeza e navegação

Retirados 13 arquivos do protótipo antigo e capturas sem uso, junto da opção
--arcade e dos seus 32 testes exclusivos. Mantidos os testes da campanha.
Removidos imports e estado aleatório sem referência. Documentação e VS Code atualizados.
Adicionados mapa tático G, rota por corredores e comando de escolta C.
28 testes aprovados e seis percursos automatizados concluídos após a limpeza.
A remoção recursiva das pastas antigas foi bloqueada pela revisão automática;
permanecem no disco e são excluídas do pacote atual.
