# Acessar, modificar e publicar o SATOSHISOYBR INDEX

O repositório oficial já está criado e é público. Não é necessário criar
novamente a organização ou o repositório para continuar este projeto.

## Acessos oficiais

- Site: https://satoshisoybr.github.io/
- Código: https://github.com/satoshisoybr/satoshisoybr.github.io
- Editar a página inicial: https://github.com/satoshisoybr/satoshisoybr.github.io/edit/main/index.html
- Sugestões e problemas: https://github.com/satoshisoybr/satoshisoybr.github.io/issues
- Propostas de alteração: https://github.com/satoshisoybr/satoshisoybr.github.io/pulls
- Execuções: https://github.com/satoshisoybr/satoshisoybr.github.io/actions
- Configuração de publicação, para administradores: https://github.com/satoshisoybr/satoshisoybr.github.io/settings/pages

A plataforma decompõe e apresenta preços; não executa operações financeiras.
O Bitcoin como componente alternativo ao prêmio comercial permanece como
pesquisa futura, dependente de metodologia específica, e não está implementado.

## Consultar e modificar o código

No repositório público GitHub, a página (`index.html`), os estilos (`styles.css`),
o JavaScript (`app.js`), os documentos e a pasta `data/` ficam na raiz. A
metodologia é documentada no `README.md`, e as instruções de contribuição estão
em `CONTRIBUTING.md`.

O checkout original de desenvolvimento usado na hospedagem Sites mantém os
arquivos públicos em `dist/`. Na exportação para o GitHub, esse conteúdo é
colocado na raiz. Siga os caminhos do repositório que estiver editando.

1. Para sugerir uma correção ou fonte, abra uma **Issue** no repositório oficial.
2. Para propor alterações, use **Fork** para criar uma cópia em sua conta.
3. Edite a sua cópia pelo GitHub ou em um ambiente local. Em mudanças de cálculo,
   preserve as fontes, datas e unidades, e execute as verificações do README.
4. Abra um **Pull request** para apresentar sua alteração ao projeto.

Quem possui acesso de escrita pode editar os arquivos pelo próprio GitHub.
O pacote `codigo-aberto.zip` também permite baixar o projeto completo. A pasta
`.openai` é da hospedagem anterior e não integra esse pacote público.

## Publicação atual no GitHub Pages

O Pages oficial já está configurado para os arquivos da raiz do repositório:

| Campo em Settings → Pages | Configuração atual |
| --- | --- |
| Source | Deploy from a branch |
| Branch | main |
| Folder | / (root) |

Essa configuração atende à publicação atual. Não é necessário recriar o
repositório nem mudar Source para GitHub Actions para continuar usando o site.
Após uma alteração, confira a execução de publicação na aba **Actions** e abra
o site para verificar o resultado. O sucesso da publicação não comprova, sozinho,
que a coleta programada de dados esteja funcionando.

O workflow de atualização fica em `.github/workflows/publicar.yml`. Quando ele
estiver disponível e habilitado em **Actions**, a opção **Atualizar soja e publicar
site → Run workflow** permite solicitar uma execução manual e acompanhar o resultado.

Para hospedar uma cópia independente, faça um Fork e configure o Pages nessa
cópia para a branch e pasta que contêm seu `index.html`. Com a estrutura pública
atual, use **main → / (root)**. Adote o endereço retornado pelo GitHub para sua
cópia e ajuste os links absolutos nos textos. Isso não altera o repositório
oficial nem seu endereço público.

## Atualização programada e estado real

O workflow contém `cron: '0 15 * * 1-5'`, com agenda prevista de segunda a sexta,
às **12h de Brasília (15h UTC)**. Ele consulta fontes, preserva o checkpoint,
confere os cálculos e gera o site e o PDF. A configuração não comprova que as
execuções programadas estejam ativas ou bem-sucedidas.

Confira a [aba Actions](https://github.com/satoshisoybr/satoshisoybr.github.io/actions)
para saber quando houve execução, quais etapas concluíram e se a publicação
terminou. Compare também as datas efetivas de cada série no site: executar o
workflow não significa que todos os fornecedores tenham publicado dados novos.
O GitHub pode atrasar execuções; não há garantia de horário exato. Agendamentos
de repositórios públicos sem atividade por 60 dias podem ser desabilitados.

- **GitHub Actions:** executa o coletor determinístico, sem API de IA e sem
  pesquisa editorial automática. Não depende de manter o computador ligado.
- **Rotina pessoal no ChatGPT:** o texto `PROMPT_RELATORIO_DIARIO.txt` pode ser
  usado para pedir um relatório em outra conta, com os recursos disponíveis nela.
- **Agendamento já existente com integração GitHub:** `PROMPT_AGENDAMENTO.txt`
  descreve como sincronizar uma base revisada quando a rotina tiver acesso de
  escrita autorizado ao repositório. Essa integração é separada da consulta do site.

## Privacidade e licença

O conteúdo do site não exibe dados pessoais nem exige login do visitante.
Contas GitHub públicas e seus commits continuam identificáveis. Não inclua
senhas, chaves de API, contratos particulares ou anexos privados no repositório.
O código tem licença MIT; os dados de terceiros mantêm suas fontes e condições
próprias de uso.

Referências oficiais:

- https://docs.github.com/pt/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages
- https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows
