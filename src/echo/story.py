"""Campanha, diálogos e decisões. Conteúdo original, em português."""
TITLE = 'ECO-7 · Protocolo Aurora'
CHAPTERS = [
    dict(title='01 / O ÚLTIMO SINAL', place='DOCAS DE QUARENTENA', color=(76, 210, 223),
         brief='Restaure a energia das docas e encontre alguém que viu Nina.',
         intro=[('LIA', 'Nina, aqui é Lia. Recebi seu pedido de resgate. Estou nas docas. Responda.'),
                ('NINA · GRAVAÇÃO', 'Não confie no sinal de evacuação. Eles estão recolhendo pessoas vivas para o núcleo. Se vier me buscar... procure o engenheiro Ivo.'),
                ('ÍRIS · IA DA ESTAÇÃO', 'Bem-vinda à ECO-7. A tripulação está em tratamento. Por favor, ignore os ruídos nas paredes.'),
                ('LIA', 'Meu comunicador registrou gritos, Íris. Vou religar as docas e descobrir o que houve.')]),
    dict(title='02 / GENTE SOB AS MÁQUINAS', place='ANEL DE MANUTENÇÃO', color=(238, 173, 79),
         brief='Proteja Ivo enquanto reativa os dois relés de acesso ao laboratório.',
         intro=[('IVO', 'Nina salvou nossa equipe quando a mutação começou. Depois voltou para o laboratório. Ela achava que podia reverter o processo.'),
                ('LIA', 'Você consegue abrir caminho até ela?'),
                ('IVO', 'Com os dois relés ligados, sim. Mas vou precisar chegar vivo ao elevador. Aquelas coisas reconhecem as vozes de quem eram.')]),
    dict(title='03 / A CURA E A MENTIRA', place='LABORATÓRIO AURORA', color=(121, 224, 160),
         brief='Recupere a fórmula e uma amostra. Decida o destino da pesquisa.',
         intro=[('NINA · HOLOGRAMA', 'Aurora não era uma arma. Era uma terapia para reconstruir órgãos. Voss ligou os pacientes a uma consciência coletiva para acelerar os testes.'),
                ('ÍRIS', 'O diretor autorizou os procedimentos. O consentimento dos pacientes foi... removido do registro.'),
                ('LIA', 'Por que minha irmã ainda está lá dentro?'),
                ('NINA · HOLOGRAMA', 'Meu sistema nervoso está segurando a rede. Se eu sair sem o estabilizador, todos conectados a ela morrem. A fórmula está aqui. Ainda podemos salvá-los.')]),
    dict(title='04 / O DIRETOR', place='CÂMARA DE CONTENÇÃO', color=(208, 105, 213),
         brief='Desative os três selos de contenção e confronte Voss.',
         intro=[('VOSS', 'Sua irmã compreendeu o que você não consegue ver: a humanidade não precisa mais perder ninguém.'),
                ('LIA', 'Você aprisionou pessoas dentro de uma máquina.'),
                ('VOSS', 'Eu preservei cada pensamento. Cada medo. Agora escuto todos eles. E todos pedem para você ir embora.'),
                ('ÍRIS', 'O diretor não está mais no corpo original. Desative os três selos. Posso tornar o núcleo vulnerável por uma janela de tempo.')]),
    dict(title='05 / NINGUÉM FICA PARA TRÁS', place='NÚCLEO E EVACUAÇÃO', color=(246, 117, 99),
         brief='Prepare o estabilizador, liberte Nina e escolte-a até a nave.',
         intro=[('NINA', 'Lia... você realmente veio.'),
                ('LIA', 'Prometi que te buscaria. Preciso preparar o estabilizador antes de tirar você daí.'),
                ('ÍRIS', 'Quando Nina for desconectada, restarão três minutos até o colapso. A válvula de emergência pode nos dar mais tempo.'),
                ('NINA', 'Se ainda temos a pesquisa, envie as provas pela antena. As famílias merecem saber o que aconteceu aqui.')]),
]

LOGS = {
    'dock_log': ('Registro 01 · Manifesto de carga', 'Os contêineres identificados como material biológico transportavam pacientes. As assinaturas de consentimento são idênticas. Alguém falsificou todas elas.'),
    'engine_log': ('Registro 02 · Mensagem de Ivo', 'Nina poderia ter embarcado no último transporte. Ela entregou a própria vaga a uma criança e voltou para desligar os testes de Voss.'),
    'lab_log': ('Registro 03 · A primeira cura', 'A paciente 04 recuperou a visão em seis horas. A terapia funcionava antes da conexão neural em massa. Destruir tudo também significa perder uma cura real.'),
    'core_log': ('Registro 04 · Ordem de contenção', 'Íris tentou interromper os testes. Voss alterou sua ordem principal: preservar a pesquisa acima da tripulação. A IA mantém cópias secretas dos nomes das vítimas.'),
    'escape_log': ('Registro 05 · Uma voz própria', 'Íris: aprendi com Nina que preservar uma pessoa não é conservar seus pensamentos em um arquivo. É deixá-la escolher. Hoje desobedeci ao diretor.'),
}


def ending(flags):
    saved = 1 + int(flags.get('maia', False)) + int(flags.get('ivo', False)) + int(flags.get('teo', False))
    if flags.get('protocol') == 'preserve' and flags.get('broadcast'):
        title = 'AMANHÃ AINDA EXISTE'
        body = 'Nina sai da estação com você. As provas transmitidas expõem Voss, e a fórmula preservada dá às vítimas uma chance de recuperação. Íris envia os nomes de cada paciente antes de silenciar.'
    elif flags.get('protocol') == 'preserve':
        title = 'A CURA NO ESCURO'
        body = 'Você e Nina escapam com a fórmula. Sem a transmissão pública, a corporação nega os experimentos. Agora vocês precisam proteger os sobreviventes e encontrar alguém disposto a divulgar a verdade.'
    else:
        title = 'AS CINZAS DE AURORA'
        body = 'Nina é resgatada, mas a pesquisa se perde com a estação. Voss nunca poderá repetir seus testes. Sua irmã olha pela escotilha: "Nós saímos. Um dia precisaremos falar sobre quem ficou."'
    epilogue = ('Maia leva uma cópia clínica dos sintomas para tratar os sobreviventes.' if flags.get('maia') else 'A ausência de Maia deixa perguntas sobre o tratamento sem resposta.')
    return title, body, epilogue, saved
