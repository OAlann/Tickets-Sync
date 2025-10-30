SELECT
		 c."ticketKey" AS "Ticket ID",
		 c."titulo" AS "Título do Chamado",
		 c."kanbanStatusdescricao" AS "Status Kanban",
		 c."agenteNome" AS "Agente Responsável",
		 c."organizacaonome" AS "Organização",
		 c."dataDeCriacao" AS "Data de Criação",
		 c."dataDaUltimaAlteracao" AS "Última Alteração",
		 /* Feedback*/ f."avaliacaoMedia" AS "Avaliação Média",
		 f."nota" AS "Nota da Pergunta",
		 f."pergunta" AS "Pergunta",
		 f."comentarios" AS "Comentário do Usuário",
		 f."usuarioAvaliacaoNome" AS "Usuário que Avaliou",
		 f."dataDeAvaliacao" AS "Data da Avaliação",
		 LPAD(FLOOR(SUM((CAST(SUBSTRING(a."quantidadeFormatada", 1, 2) AS DOUBLE) * 60 + CAST(SUBSTRING(a."quantidadeFormatada", 4, 2) AS DOUBLE))) / 60), 2, '0') || ':' || LPAD(MOD(SUM((CAST(SUBSTRING(a."quantidadeFormatada", 1, 2) AS DOUBLE) * 60 + CAST(SUBSTRING(a."quantidadeFormatada", 4, 2) AS DOUBLE))), 60), 2, '0') AS "Tempo Total Apontado (HH:MM)",
		 COUNT(DISTINCT a."apontamentoKey") AS "Qtd. Apontamentos"
FROM  "chamados" AS  c
LEFT JOIN "apontamentos" AS  a ON c."ticketKey"  = a."ticketKey" 
LEFT JOIN "feedbacks" AS  f ON c."ticketKey"  = f."ticketId"  
WHERE	 (c."arquivado"  = 0
 OR	c."arquivado"  = 'false')
 AND	(c."lixeira"  = 0
 OR	c."lixeira"  = 'false')
GROUP BY c."ticketKey",
	 c."titulo",
	 c."kanbanStatusdescricao",
	 c."agenteNome",
	 c."organizacaonome",
	 c."dataDeCriacao",
	 c."dataDaUltimaAlteracao",
	 f."avaliacaoMedia",
	 f."nota",
	 f."pergunta",
	 f."comentarios",
	 f."usuarioAvaliacaoNome",
	  f."dataDeAvaliacao" 
ORDER BY c."dataDeCriacao" DESC 
