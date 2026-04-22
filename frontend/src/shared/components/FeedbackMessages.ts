export const successMessages = {
  login: 'Bem-vindo ao Dinâmica Budget.',
  serviceCreated: 'Serviço cadastrado com sucesso.',
  ownServiceCreated: 'Serviço enviado para homologação. Aguardando análise.',
  associationCreated: 'Associação criada com sucesso.',
  associationDeleted: 'Associação excluída com sucesso.',
  compositionCloned: 'Composição clonada com sucesso.',
  componentAdded: 'Componente adicionado à composição.',
  componentRemoved: 'Componente removido da composição.',
  userCreated: 'Usuário cadastrado com sucesso.',
  userUpdated: 'Dados do usuário atualizados.',
  userActivated: 'Usuário reativado com sucesso.',
  userDeactivated: 'Usuário desativado com sucesso.',
  userPerfisUpdated: 'Perfis por cliente atualizados.',
  clientCreated: 'Cliente cadastrado com sucesso.',
  clientUpdated: 'Dados do cliente atualizados.',
  clientActivated: 'Cliente reativado com sucesso.',
  clientDeactivated: 'Cliente desativado com sucesso.',
  embeddingsProcessed: 'Embeddings processados com sucesso. O motor de busca está atualizado.',
  etlUploaded: 'Arquivo carregado e analisado. Revise o resumo antes de executar.',
  etlExecuted: 'Carga ETL concluída com sucesso. Base de referência atualizada.',
  xlsxDownloaded: 'Planilha BOM gerada e baixada com sucesso.',
  profileUpdated: 'Perfil atualizado com sucesso.',
  passwordChanged: 'Senha alterada com sucesso. Faça login novamente.',
} as const;

export const errorMessages = {
  generic: 'Ocorreu um erro inesperado. Tente novamente.',
  login: 'E-mail ou senha incorretos. Verifique suas credenciais.',
  loadData: 'Não foi possível carregar os dados. Tente novamente.',
  serviceSave: 'Não foi possível salvar o serviço. Tente novamente.',
  compositionClone: 'Não foi possível clonar a composição. Tente novamente.',
  compositionAddComponent: 'Não foi possível adicionar o componente. Tente novamente.',
  compositionRemoveComponent: 'Não foi possível remover o componente. Tente novamente.',
  associationCreate: 'Não foi possível criar a associação. Tente novamente.',
  associationDelete: 'Não foi possível excluir a associação. Tente novamente.',
  userCreate: 'Não foi possível cadastrar o usuário. Verifique os dados e tente novamente.',
  userUpdate: 'Não foi possível atualizar o usuário. Tente novamente.',
  userPerfis: 'Não foi possível atualizar os perfis do usuário.',
  clientCreate: 'Não foi possível cadastrar o cliente. Verifique os dados e tente novamente.',
  clientUpdate: 'Não foi possível atualizar o cliente. Tente novamente.',
  embeddings: 'Não foi possível processar os embeddings. Tente novamente.',
  etlUpload: 'Não foi possível processar o arquivo. Verifique o formato e tente novamente.',
  etlExecute: 'Erro ao executar a carga ETL. Verifique os tokens e tente novamente.',
  extractionLoad: 'Não foi possível carregar os serviços do cliente. Tente novamente.',
  extractionExplode: 'Não foi possível explodir a composição. Tente novamente.',
  xlsxDownload: 'Não foi possível gerar a planilha. Tente novamente.',
  profileUpdate: 'Não foi possível atualizar o perfil. Tente novamente.',
  passwordChange: 'Não foi possível alterar a senha. Verifique a senha atual e tente novamente.',
} as const;

export const warningMessages = {
  noResults: 'Nenhum resultado para os filtros aplicados. Ajuste os critérios.',
  sessionExpiring: 'Sua sessão expira em 5 minutos. Salve seu trabalho.',
  actionIrreversible: 'Atenção: a próxima ação não poderá ser desfeita.',
  serviceNoComposition: 'Este serviço não possui composição cadastrada.',
  etlReplaceMode: 'Modo SUBSTITUIR irá remover composições existentes. Certifique-se que o arquivo está completo.',
  dataStale: 'Os dados exibidos podem estar desatualizados. Atualize a página.',
} as const;

export const infoMessages = {
  searchLoading: 'Buscando serviços no catálogo TCPO...',
  processing: 'Processando dados. Isso pode levar alguns instantes.',
  modeReadOnly: 'Você está visualizando este registro em modo leitura.',
  reportGenerating: 'Gerando relatório. Isso pode levar alguns instantes.',
  etlProcessing: 'Executando carga ETL. Isso pode levar alguns minutos para 40k registros.',
  extractionSearching: 'Buscando serviços pela terminologia do cliente...',
  firstAccess: 'Recomendamos alterar sua senha no primeiro acesso.',
} as const;

export const infoMessageTemplates = {
  searchResultsLoaded: (count: number) =>
    count
      ? `${count} resultado(s) encontrado(s).`
      : 'Nenhum resultado encontrado para os critérios informados.',
} as const;
