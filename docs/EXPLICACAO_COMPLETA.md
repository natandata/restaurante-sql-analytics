# SQL para decisões de restaurante

Documento de implementação e estudo, versão privada para revisão de 11/11/2026. Projeto 2 do guia. Código independente com assistência de IA; não é cópia do Zomato, trabalho para cliente real ou alegação de que Natan implementou tudo sozinho. As tabelas, nomes, preços e pedidos são fictícios.

## 1. A decisão e a prova

O restaurante precisa responder quem vende mais, como a receita varia por mês, qual é o ticket e quais produtos deixam margem. Antes de fazer um gráfico, há uma pergunta mais importante: a receita continua igual depois de juntar as tabelas? O projeto foi construído em torno dessa prova.

A execução padrão usa seed 20261111, cinco restaurantes, quatro produtos e 500 pedidos. A receita reconciliada é 4.459.200 centavos, ou R$ 44.592,00. O cruzamento ingênuo de pedidos com itens retorna 10.277.500 centavos. São R$ 58.183,00 a mais que não foram vendidos: o erro aparece porque cada valor de pedido foi repetido para suas linhas. Esse número mede um erro de cálculo no exemplo, não uma perda encontrada numa empresa.

Há 20 testes automatizados de domínio e carga, executados em Python 3.10.12 e 3.12.15. Uma integração real com PostgreSQL 16.2 confirmou as cinco consultas e as restrições PK, FK e CHECK. SQLite é a via local leve; PostgreSQL não é uma promessa não testada nem um serviço instalado no computador de Natan.

## 2. Mapa da implementação

O caminho principal é `src.pipeline.run()`: cria um banco em memória, aplica `sql/01_schema.sql`, gera dados, executa consultas, exige reconciliação e grava artefatos. A aplicação `app.py` chama as mesmas funções de criação, carga e consulta, mas não grava de volta nos relatórios versionados. Alterar um filtro na aplicação é explorar o exemplo, não mudar a execução de referência.

`src/importer.py` oferece uma segunda entrada: cinco CSVs com esquema conhecido. Ela faz uma carga transacional, tira duplicatas exatas com auditoria e rejeita conflitos. `src/verify_postgres.py` abre uma instância PostgreSQL temporária só para esta verificação, carrega os mesmos registros, compara resultados e encerra a instância. Não procura bancos da pessoa nem modifica uma conta existente.

`src/common.py` grava JSON sem NaN, CSV, imagens e um relatório HTML autônomo. A fonte Inter acompanha a licença SIL OFL; o manual privado de marca não acompanha o código. A pasta `notebooks/` mostra o raciocínio com células executadas. `tests/` é a especificação executável dos invariantes, não só uma demonstração de saída bonita.

## 3. Granularidade antes do SQL

Uma linha em `restaurants` representa um restaurante fictício. `restaurant_id` é sua chave primária. O nome serve para leitura, não para cruzamento: duas lojas poderiam ter nomes iguais sem serem a mesma entidade.

Uma linha em `products` representa um produto do catálogo. `product_id` identifica o produto; o nome é único neste exemplo. Uma linha em `menu` representa um produto oferecido por um restaurante, com preço e custo de ficha em centavos. Sua chave é composta por restaurante e produto. O mesmo produto pode ter preços diferentes em lojas diferentes.

Uma linha em `orders` representa um pedido inteiro, com restaurante, data e total. O total não é uma métrica aditiva depois de cruzar o pedido com suas linhas: ele se repete. Uma linha em `order_lines` representa um produto dentro de um pedido. A chave composta pedido/produto consolida unidades do mesmo produto numa linha. Se uma operação real permitir o mesmo produto com modificadores ou preços diferentes, a chave precisará de um `line_id`; não basta reaproveitar esta escolha sem pensar.

O modelo tem cinco tabelas. Não existe tabela de usuários, email, senha, nome de cliente, entregador ou endereço. Não há motivo para coletar essas informações para as perguntas escolhidas. A ausência desses campos é uma decisão de desenho, não uma anonimização feita sobre uma base privada.

## 4. As restrições como contrato

A PK impede duas versões simultâneas da mesma chave. Uma FK entre pedido e restaurante impede uma venda para uma loja que não existe. A FK composta de `order_lines` para `orders` verifica tanto o pedido quanto seu restaurante. Outra FK composta para `menu` verifica que a combinação produto/restaurante existe no cardápio. Verificar só o produto seria insuficiente: ele poderia existir numa loja diferente.

As CHECKs exigem quantidade e preço de linha positivos, custo não negativo e total de pedido não negativo. O total do pedido igual à soma das linhas é uma regra entre tabelas, portanto não foi disfarçado de CHECK de uma coluna. A consulta de reconciliação e a carga transacional verificam essa regra antes de dar a carga como aceita.

SQLite exige `PRAGMA foreign_keys=ON` por conexão. `create_connection()` faz isso. Um teste confirma que inserir um pedido com restaurante inexistente falha. A aplicação nunca deve abrir outra conexão esquecendo essa configuração. No PostgreSQL, as FKs já fazem parte do comportamento normal do servidor; a verificação não depende desse PRAGMA.

Moeda fica em inteiro para as multiplicações exatas de quantidade por preço. O ticket médio pode ser fracionário porque é uma divisão; arredondá-lo para exibição não muda os totais que o originaram. Usar `float` para guardar cada preço criaria erros binários desnecessários. Um valor como 1999 significa R$ 19,99, não R$ 1.999.

## 5. Geração e carga

`load()` usa `numpy.random.default_rng(seed)` local, não o estado aleatório global. Ele cria as dimensões primeiro, depois o cardápio, depois cada pedido e suas linhas. Os produtos de um pedido são escolhidos sem reposição, de acordo com a chave pedido/produto. As quantidades são inteiras de 1 a 3; os totais são calculados a partir das linhas, não sorteados de forma independente.

As datas estão em seis meses de 2025. Isso é um calendário histórico simulado, não receita atual de novembro de 2026. A distribuição aleatória foi escolhida para exercitar agrupamentos, não estimada de uma população. Não se deve concluir que um restaurante real tem este ticket, esta sazonalidade ou este mix.

A carga CSV aceita `restaurants.csv`, `products.csv`, `menu.csv`, `orders.csv` e `order_lines.csv`; aceita também os nomes `input_...` gerados pela execução. Exige o cabeçalho exato, valida inteiros, remove espaços de textos e exige data ISO canônica. `2025-01-01` é o formato aceito; não interpreta ambiguidades como `01/02/25`. Um erro de cabeçalho, número, data, FK, chave ou conciliação invalida o lote inteiro.

Duplicata exata e conflito são situações diferentes. Duas linhas idênticas do CSV são uma repetição operacional detectável: a segunda é descartada e entra na auditoria. Duas linhas com a mesma chave e nomes ou valores diferentes são um conflito: a carga falha. Não há regra escondida de 'a última vence'. Se o produtor realmente quiser uma atualização, deverá implementar e testar esse contrato separadamente.

A transação começa antes da primeira tabela. Se a conciliação do último pedido falhar, `rollback()` desfaz também restaurantes e produtos que já haviam sido inseridos. Assim não sobra uma carga pela metade. A função não substitui tabelas existentes e não é um UPSERT idempotente: carregar o mesmo lote de novo numa base já preenchida falha por chave. Esse limite deve ser conhecido antes de conectar um sistema real.

Exemplo de uso programático, depois da execução de referência:

```python
from src.pipeline import create_connection
from src.importer import import_csv
con = create_connection()
audit = import_csv(con, 'reports')
print(audit)
con.close()
```

O exemplo usa apenas os CSVs sintéticos gerados. Um caminho de CSV não autoriza divulgar dados reais. Nunca substitua esses arquivos por exportações de clientes num repositório público sem rever direitos, privacidade e segredos.

## 6. Reconciliação de pedidos

A view `order_totals` agrupa as linhas por pedido e calcula `SUM(quantity * unit_cents)`. A consulta `02_reconcile.sql` faz LEFT JOIN da tabela de pedidos com essa view. A granularidade já está alinhada: uma linha por pedido dos dois lados.

O LEFT JOIN é intencional. Um INNER JOIN faria um pedido sem linhas desaparecer, escondendo o erro. O `COALESCE(..., 0)` permite expor a divergência de um pedido sem itens. Há uma limitação: um pedido de total zero e sem itens passa na reconciliação numérica. Se a regra do negócio proibir isso, acrescente uma contagem mínima de linhas na carga. O gerador atual sempre cria ao menos um item.

Conferência manual: um pedido tem dois pratos a R$ 10,00. A linha vale 2 × 1000 = 2000 centavos. O pedido também vale 2000. Com custo fictício de 300 centavos por prato, a contribuição é 2 × (1000 - 300) = 1400 centavos. O teste `test_19_hand_calculated` verifica receita, contribuição e ticket desse caso pequeno. Ele não se apoia no mesmo sorteio de 500 pedidos para decidir o que está certo.

## 7. Ranking, participação e desempate

`03_restaurants.sql` usa uma CTE para agregar pedidos por restaurante. A CTE é uma etapa nomeada da consulta; ela facilita inspecionar a granularidade. Só depois a função de janela `SUM(revenue_cents) OVER()` calcula o total de todas as lojas para a participação percentual.

A diferença entre agregação e janela importa: `GROUP BY` reduz linhas; a janela calcula sobre um conjunto sem apagar as linhas agregadas de cada restaurante. `DENSE_RANK()` atribui a mesma posição a receitas iguais. `ORDER BY revenue_cents DESC, restaurant_id` define ordem e desempate de exibição antes de `LIMIT 5`. O LIMIT não é um substituto para ORDER BY.

Na execução padrão, o restaurante 1 soma R$ 10.246,00 e 120 pedidos, seguido do restaurante 5 com R$ 9.338,00 e 91 pedidos. Isso não prova que a loja 1 é melhor: ela recebeu mais pedidos na simulação. Uma comparação operacional exigiria tempo aberto, capacidade, localização, margens e histórico. A análise aqui responde qual total é maior, não por quê.

## 8. Evolução mensal e ticket

`04_monthly.sql` extrai o mês da data ISO, agrega receita e pedidos e usa `LAG()` para buscar a receita do mês anterior. A primeira diferença é nula porque não há mês anterior no recorte. Null não é zero: zero afirmaria que houve um mês com nenhuma receita, informação que não temos. O relatório mostra 'não se aplica' nesse ponto.

O índice `ix_orders_date` prepara filtros de período, mas o exemplo não apresenta um benchmark nem afirma que ele melhora esta consulta pequena. Usar `EXPLAIN` e volumes maiores seria o jeito correto de demonstrar impacto. Colocar índices sem medir também tem custo de escrita e armazenamento.

`06_ticket.sql` calcula média, mínimo e máximo a partir de pedidos inteiros. Fazer AVG do preço de item responderia outra pergunta. A distribuição de ticket é dependente do número de itens por pedido e das quantidades. Se cancelamentos, estornos ou taxas entrarem no produto, será necessário definir receita bruta/líquida e status elegíveis antes de reutilizar as consultas.

## 9. Margem não é lucro

`05_item_margin.sql` combina linhas com o custo do cardápio, usando as duas partes da chave do menu. Calcula receita e contribuição por produto. Na simulação, salada aparece com a maior contribuição total, 845.840 centavos, e não se deve transformá-la numa recomendação real de cardápio.

O custo de ficha é estático. Uma operação com mudanças de custo precisaria de custo vigente na data da venda, talvez copiado para a linha ou resolvido por uma dimensão histórica. Usar o custo atual para reavaliar vendas antigas altera a margem retrospectivamente. Não há aluguel, salário, imposto, comissão, desperdício ou rateio neste modelo; portanto a coluna se chama contribuição, não lucro líquido.

## 10. SQLite e PostgreSQL

SQLite foi escolhido como porta de entrada porque não exige daemon, conta ou porta aberta para o fluxo principal. O arquivo `reports/analytics.sqlite` é uma cópia local da execução, não um banco de produção. Ele fica fora do Git por padrão; o gerador e os CSVs permitem reconstruí-lo.

O esquema e as cinco consultas foram também executados em PostgreSQL 16.2. `src.verify_postgres` carrega os mesmos registros obtidos da conexão SQLite, compara linhas e números e provoca três violações esperadas. Trata diferenças de tipo, como Decimal e float, apenas na comparação de resultados arredondados. Não arredonda os totais inteiros para mascarar divergências.

O servidor temporário vem da dependência opcional `pgserver`, é iniciado só para o teste e encerrado em `finally`. Essa dependência contém componentes próprios de sua distribuição, que não são empacotados no projeto. Sua versão de PostgreSQL é antiga para uma implantação nova: o teste comprova compatibilidade SQL com 16.2, não recomenda colocar esse binário numa rede. Em produção, escolha uma versão mantida, configure autenticação e TLS, backups, migrações e permissões. Nenhuma dessas medidas está implicitamente pronta neste estudo.

## 11. Painéis e notebook

O HTML em `reports/dashboard.html` abre offline e preserva o resultado de referência. O Streamlit deixa mudar seed, número de pedidos, idioma e filtro de restaurante. As outras abas mostram meses, margem, reconciliação e o texto SQL usado. A aplicação não aceita SQL arbitrário, não publica GitHub e não envia os dados para uma API.

As duas formas de painel têm objetivos diferentes. O HTML é um relatório congelado; a aplicação é uma ferramenta de exploração. Um gráfico filtrado para um restaurante continua mostrando sua participação no universo original, e não 100% da seleção: a coluna foi calculada antes do filtro. A legenda explica que os valores de receita do gráfico estão em R$; os CSVs mantêm centavos para precisão.

No notebook, execute as células em ordem numa sessão nova. Ele lê a raiz do projeto, chama o pipeline e apresenta tabelas e figuras. As saídas distribuídas foram produzidas por execução real. O notebook não é a única fonte de lógica: importa funções de `src` para evitar duas implementações divergentes.

## 12. Testes e o que eles não provam

Os 20 testes cobrem geração repetível, integridade referencial, conciliação por pedido e em JOINs, soma de participações, ordenação mensal, violações de PK/FK/CHECK, FK composta, margem, JOIN errado, ranking explícito, CSV ida/volta, auditoria de duplicata, rollback, rejeição de não inteiros, consultas vazias, conta manual e conflito de carga. A verificação PostgreSQL é uma camada adicional, não foi contada como mais 20 testes.

O painel foi exercitado com carregamento, EN, 700 pedidos e filtro de restaurante. O layout foi inspecionado em 320, 390 e 1280 pixels. Isso demonstra os caminhos testados, não cobertura universal de navegador, acessibilidade auditada ou implantação em Windows. Não houve instalação deste projeto no Dell.

## 13. Como rodar

Use Python 3.10 ou 3.12 e uma pasta própria. Primeiro crie um ambiente virtual. No Ubuntu/WSL:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
python -m src.pipeline
```

No PowerShell, a ativação é `.venv\Scripts\Activate.ps1`; uma política restritiva pode impedir o script. Não altere a política global por conveniência: use diretamente `.venv\Scripts\python.exe -m pip ...` e os outros comandos com esse executável. O projeto ainda não foi testado no Windows nativo.

Para a aplicação, instale `requirements-app.txt` e execute `python -m streamlit run app.py`. A configuração usa apenas localhost e desativa a telemetria de uso do Streamlit. Para o notebook, instale `requirements-notebook.txt` e use Jupyter de sua preferência. Para a integração opcional, instale `requirements-postgres.txt` e execute `python -m src.verify_postgres`; essa via foi testada em Linux, não no Dell.

Os arquivos de CI descrevem como executar testes no GitHub quando houver publicação autorizada. Não houve execução de GitHub Actions ainda. Um arquivo de workflow não é evidência de check verde no GitHub.

## 14. Como modificar sem perder a prova

Para incluir um produto, acrescente uma linha à dimensão e ao cardápio e confirme as FKs. Para permitir modificadores, introduza `line_id` e crie testes com dois itens do mesmo produto a preços distintos. Para descontos, escolha se o desconto pertence à linha ou ao pedido; depois faça a conciliação no mesmo nível e nunca subtraia um desconto de pedido uma vez por linha.

Para persistência incremental, defina um identificador de lote, uma chave de idempotência e a política de correção. A carga atual rejeita repetição de chave na base; o comportamento desejado de reprocessamento não deve ser inventado pelo importador. Para dados reais, separe recepção, validação, staging e publicação, e registre contagens e hashes por lote.

Numa entrevista FDE, explique primeiro o invariante: o faturamento antes e depois do cruzamento deve bater. Mostre o contraexemplo, a correção com pré-agregação, o caso manual e o rollback. Essa sequência demonstra tradução de pergunta de negócio em contrato e teste. Não apresente um estudo sintético como experiência de implantação num cliente.

## 15. Direitos, publicação e limites

A referência temática é ShaikhBorhanUddin/Zomato-Data-Analysis: https://github.com/ShaikhBorhanUddin/Zomato-Data-Analysis . Não foi copiado código, CSV, senha ou tabela de usuários. A licença MIT da referência não foi usada como licença automática desta implementação. O código original não recebeu licença de reutilização nesta versão.

Nome proposto: `restaurante-sql-analytics`. Antes de criar o repositório, revisar README, conteúdo, audiência e licença. Nada foi enviado ao GitHub. A conta conectada foi verificada como natandata; isso confirma a rota, não substitui a revisão prometida.

Fontes técnicas: Python sqlite3, https://docs.python.org/3/library/sqlite3.html ; PostgreSQL, https://www.postgresql.org/docs/16/ ; SQLite foreign keys, https://www.sqlite.org/foreignkeys.html . A implementação mede resultados próprios, sem copiar números da referência.
