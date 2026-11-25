# SATOSHISOYBR INDEX

Índice open source dedicado à decomposição e à apresentação do preço da soja
brasileira: Chicago, dólar e prêmio comercial, com Paranaguá e Santos separados.
A plataforma apresenta preços e referências de cálculo; **não executa operações
financeiras**.

O Bitcoin já aparece como referência de valor em satoshis, conforme as fórmulas
documentadas abaixo. Seu uso como componente alternativo ao prêmio comercial é
uma possibilidade de pesquisa futura, dependente de metodologia específica;
essa substituição não está implementada. O código aberto oferece uma base para
estudos de hedge, derivativos e liquidez, sem realizar essas operações.

Sem cadastro de visitantes, sem identificação pessoal no conteúdo e sem rastreadores próprios.

## Acessos oficiais

- [Site público](https://satoshisoybr.github.io/)
- [Código-fonte no GitHub](https://github.com/satoshisoybr/satoshisoybr.github.io)
- [Sugestões e problemas](https://github.com/satoshisoybr/satoshisoybr.github.io/issues)
- [Propostas de alteração](https://github.com/satoshisoybr/satoshisoybr.github.io/pulls)
- [Editar a página inicial](https://github.com/satoshisoybr/satoshisoybr.github.io/edit/main/index.html)
- [Execuções e publicação](https://github.com/satoshisoybr/satoshisoybr.github.io/actions)
- [Como contribuir](CONTRIBUTING.md)

## Rodar

```sh
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
python engine.py
python scripts/package_source.py
python -m http.server 8000 --directory .
```

Para consultar fontes públicas e acrescentar observações, use `python engine.py --collect`.
Dados anteriores ficam em `data/state.json`, com revisões explícitas. Falha de consulta
não apaga capturas, não renova suas datas e não cria observações.

## Publicar e automatizar

O repositório oficial já existe; não é necessário criá-lo novamente. Veja
[GUIA_GITHUB.md](https://github.com/satoshisoybr/satoshisoybr.github.io/blob/main/GUIA_GITHUB.md) para editar, contribuir, fazer uma cópia
independente ou configurar a publicação.

No repositório público GitHub, os arquivos do site são exportados para a raiz:
`index.html`, `styles.css`, `app.js` e `data/`. O GitHub Pages já está configurado
para **Deploy from a branch → main → / (root)**. Essa configuração atende à
publicação atual; não é necessário recriar o repositório nem alterar a origem
para continuar usando o site.

O checkout original de desenvolvimento usado na hospedagem Sites mantém esses
arquivos em `dist/`; a exportação para o GitHub coloca esse conteúdo na raiz.
Os caminhos de edição devem seguir a estrutura do checkout em uso. No GitHub,
a página inicial pode ser alterada em
[index.html](https://github.com/satoshisoybr/satoshisoybr.github.io/edit/main/index.html).

A agenda prevista em `.github/workflows/publicar.yml` é de segunda a sexta, às **12h de Brasília
(15h UTC)**. A existência dessa configuração não comprova que a rotina esteja
ativa: confira as execuções, seus resultados e o horário na
[aba Actions](https://github.com/satoshisoybr/satoshisoybr.github.io/actions).
GitHub Actions pode atrasar; não há garantia de execução no segundo exato.

## Precisão e limitações

- Aritmética decimal `ROUND_HALF_UP`; soma das parcelas apresentadas em centavos.
- Mesmo dia, porto, série e contrato; nenhuma interpolação de lacunas.
- Residual é diferença entre referências, não despesa identificada.
- SJC450sc, SOY34t. Fluxo vendido emUSD separado de estimativaPTAX emBRL; liquidaçãoB3 realN/D.
- Chicago e prêmio têm bases comerciais diferentes: composição indicativa, salvo incompatibilidade, que impede soma.
- O coletor de notícias não está automatizado; referências editoriais mantêm data original.
- O coletor não verifica livro de ofertas de puts. Custos ficamN/D até obterask com fonte/hora.
- Cadastro e calendário das opções são checkpoints datados; não são revalidados a cada execução.
- `config.json` fixa contratoCBOT, vencimento oficialmente verificado e embarque do prêmio.
  Após o vencimento, não captura um sucessor inventado. Revise a configuração com fonte oficial.
- Adaptação dos sites fornecedores pode exigir manutenção; erros aparecem no checkpoint.
- Os preços são dados de terceiros, sujeitos às condições de cada fonte. LicençaMIT cobre o código, não relicencia os dados.
- Não há garantia de anonimato do titular de uma conta pública GitHub. Hospedagem pode registrar dados técnicos de visitantes.

## Fontes

BCB/PTAX, CME e CEPEA via NotíciasAgrícolas, B3/PriceReport e Grainsights/TheAgriBiz.
Cada observação inclui data efetiva e metadados da fonte. Seed importado por whitelist
de uma base histórica já verificada, sem PDFs privados, nomes, documentos ou identificadores de conta.

## Licença

MIT. Livre para usar, estudar, modificar e redistribuir o código. Sem garantia de resultado financeiro.

## SATOSHISOYBR: duas medidas

- Soja: **satoshis por saca de 60 kg (sats/sc)**.
- Dólar: **satoshis por dólar (sats/US$)**, usando PTAX venda.
- sats/sc = preço BRL/sc ÷ BTC/BRL Bipa × 100.000.000.
- sats/US$ = PTAX venda ÷ BTC/BRL Bipa × 100.000.000.

A série Bipa ainda não foi conectada. Na ausência por data, usamos o fechamento
diário BTCBRL spot Binance, identificado como Binance. Nunca o chamamos Bipa.
Não usamos USDT como dólar. Sem ambas as referências, resultado N/D.
As tabelas mantêm um modo em reais.
Datas coincidentes não implicam simultaneidade: horários originais são preservados.
Chicago continua usando PTAX como conversão intermediária, com unidades coerentes.
As parcelas convertidas são arredondadas HALF_UP a 0,01 sat; SOMA e residual
fecham sobre essas parcelas. Fração de sat é medida estatística, não liquidação.

O gráfico final mostra BTC/BRL, BTC e PTAX em base 100, e soja em sats versus
USD em base 100 por praça, quando houver ao menos duas referências compatíveis.
Descolamento = [(BTC_t/BTC_0)/(PTAX_t/PTAX_0) − 1] × 100.
Não prova correlação ou proteção. A ferramenta mede referências; não cria
contrato de indexação nem afirma pioneirismo mundial.

### Importar preços Bipa verificados

A documentação oficial lista ferramentas de histórico de preços; conexão
autorizada ainda é necessária: https://agents.bipa.app/docs .
Não coloque tokens ou dados de clientes no repositório. Exporte apenas preços
e metadados, no formato abaixo, e execute `python scripts/import_bipa.py caminho.json`.
A importação rejeita dados sem fonte, sem fuso, datas futuras/atuais, duplicatas
e substituição de fonte. Revisões são preservadas em `data/bipa_revisions.json`.
Depois execute `python engine.py` e `python scripts/package_source.py`.
O workflow não busca automaticamente a série Bipa enquanto não existir
um adaptador autorizado com esquema confirmado e renovação de acesso.

```json
[{"date":"AAAA-MM-DD","price_brl":"PRECO_EXATO",
  "source_url":"https://mcp.bipa.app/mcp",
  "observed_at":"AAAA-MM-DDTHH:MM:SS-03:00",
  "consulted_at":"AAAA-MM-DDTHH:MM:SS-03:00",
  "nature":"daily_reference",
  "method":"Descrever referência publicada, horário e regra diária confirmados"}]
```

`daily_close` só é usado quando a fonte realmente publica fechamento;
`daily_reference` é uma observação diária, não um fechamento oficial inventado.
O importador preserva somente esses campos de mercado.

## Alternativa Binance autorizada

Coleta pública `/api/v3/klines` em `data-api.binance.vision`, par BTCBRL,
intervalo 1d e timeZone=-3 (Brasília). Somente candles encerrados, até ontem.
Sem API key, sem saldo de cliente, sem ordens. Bootstrap até 34 dias;
próximas execuções acrescentam somente datas após a última preservada.
Bipa tem preferência por data se uma exportação verificada existir.
Cada data identifica fonte e horário. Índices base 100 reiniciam sua base
por fornecedor e as linhas não ligam trocas de fonte; não se calcula retorno
de cinco pregões atravessando mudança de fornecedor BTC.

## Prêmio e frete

Prêmio de exportação em sats/sc é conversão de unidade, não um ativo,
prêmio de opção ou nova oferta. Pode ser negativo. Gráfico base 100 só
é aplicável com referência inicial positiva e condição comercial homogênea.

Cenário do produtor: referência no porto − frete R$/t × 0,06 − custos
comerciais informados. Custo de produção opcional calcula margem simulada.
A referência física já incorpora seus fatores: prêmio não é somado novamente.
Entradas calculadas no navegador com inteiros BigInt e arredondamento HALF_UP
a centavos; conversão a 0,01 sat sobre o valor em reais apresentado. Não há
envio, armazenamento local ou telemetria própria dessas entradas.

Fretes: Conab, Boletim Logístico outubro/2026, dados de setembro/2026.
`data/freight.json` preserva rotas, unidade, período, páginas, consulta e hash
do documento. Grupos regionais são agrupamentos editoriais, cobertura parcial:
média simples sem peso por volume, com N e faixa. Não representam todo o
mercado nem tarifas atuais. A manutenção dessa base mensal ainda é manual.
Datas mensais antigas não são incorporadas como observações diárias de soja.

## Tabelas completas e confronto descritivo (revisão de apresentação)

A visualização principal agora preserva sempre reais e USD/bushel, com uma
coluna adicional de Bitcoin para o físico. As duas praças têm tabelas
separadas, visíveis na mesma página, sem trocar suas referências. O seletor
de praça controla gráficos e calculadora. Futuros mantêm ajuste original
em USD/sc (SJC) ou USD/t (SOY), conversão R$/sc, Bitcoin adicional, variação,
fluxo vendido em USD e estimativa PTAX em BRL, volume e ofertas datadas.
O PDF público combinado também acrescenta a coluna de Bitcoin.

`confronto.py` calcula intervalos entre observações comuns, sem preencher
fins de semana com PTAX inventada nem atravessar troca de fornecedor BTC.
Default: R$ 1.000 de valor inicial. Alternativas: prêmio de exportação de
1 saca ou preço físico de 1 saca na primeira data e praça selecionada.
Sem valor inicial positivo publicado, o cenário fica N/D.

Para cada intervalo, as quantidades iniciais são N/BTC0 e N/PTAX0.
Resultado teórico comprado BTC / vendido USD = N × (rBTC − rUSD), em BRL.
Isso é distinto do retorno do par BTC/USD = (1+rBTC)/(1+rUSD) − 1.
O gráfico usa a diferença dos valores finais individualmente arredondados;
esta pode diferir R$ 0,01 do resultado da fórmula sem arredondamento
intermediário. A base JSON guarda ambos e quantidades sem arredondamento.

A base inicial é reiniciada a cada intervalo: não somar as barras como saldo
de uma operação contínua. Os intervalos exibem início, fim e dias corridos;
alguns abrangem fins de semana e feriados. Horários originais diferem.
Sem spread, tarifas, tributos, financiamento, margem ou ajuste real.
Não há execução nem oferta de venda de dólar à PTAX. O prêmio de exportação
não é um investimento com rendimento: somente dimensiona o valor inicial.
A comparação não mede eficácia de hedge da soja nem prova que uma forma
de recebimento é superior. Código aberto permite desenvolver esses modelos
com instrumentos e custos efetivamente observados no futuro.

## Copiar para o ChatGPT e gerar PDF

O rodapé oferece `PROMPT_RELATORIO_DIARIO.txt`, independente de conta,
conversa ou identificadores privados do criador. O visitante gera primeiro
uma edição e confere as ferramentas e o agendamento na própria conta.
Não se afirma que colar texto ativa uma rotina, nem que todo plano possui
as mesmas ferramentas. Confira a primeira execução que realmente produz PDF.
A criação de uma cópia pessoal não autoriza escrever no site ou repositório.
`PROMPT_AGENDAMENTO.txt` continua sendo apenas extensão para uma rotina já
existente com integração GitHub autorizada. São finalidades diferentes.

O projeto tem instruções de contribuição em [CONTRIBUTING.md](CONTRIBUTING.md)
e código no [repositório público oficial](https://github.com/satoshisoybr/satoshisoybr.github.io).
O pacote ZIP continua disponível no site para baixar e estudar o código.
A situação da coleta e da publicação automatizadas deve ser verificada na
[aba Actions](https://github.com/satoshisoybr/satoshisoybr.github.io/actions).
