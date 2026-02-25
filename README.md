# SystemConcreto — Engenharia de LLM Aplicada à Dosagem de Concreto

> **Avaliação Final — IA Generativa (70% da nota)**
> Autor: Patrik · Data: 26/02/2026 · Ferramentas de codificação: Claude / Gemini / IDE Antigravity

---

## Sumário

1. [Descrição do Problema e da Solução](#1-descrição-do-problema-e-da-solução)
2. [Arquitetura de LLM — Fluxo Completo](#2-arquitetura-de-llm--fluxo-completo)
3. [Decisões de Engenharia e Justificativas](#3-decisões-de-engenharia-e-justificativas)
   - 3.1 [Modelo e Provedor: Por que GPT-4o-mini?](#31-modelo-e-provedor-por-que-gpt-4o-mini)
   - 3.2 [Framework: Por que LangChain?](#32-framework-por-que-langchain)
   - 3.3 [Parâmetros: Temperatura, top-p e Experimentação](#33-parâmetros-temperatura-top-p-e-experimentação)
   - 3.4 [Ferramentas (Tool Calling): consultar_limites_normativos](#34-ferramentas-tool-calling-consultar_limites_normativos)
   - 3.5 [Estratégia de Prompting: XML Tags, Chain-of-Thought e Few-Shot](#35-estratégia-de-prompting-xml-tags-chain-of-thought-e-few-shot)
   - 3.6 [Structured Outputs: Pydantic como Validador de Schema](#36-structured-outputs-pydantic-como-validador-de-schema)
   - 3.7 [Arquitetura: Por que NÃO RAG? Por que NÃO Agentes?](#37-arquitetura-por-que-não-rag-por-que-não-agentes)
   - 3.8 [Segurança: Prompt Injection e Inputs Maliciosos](#38-segurança-prompt-injection-e-inputs-maliciosos)
4. [O Que Funcionou](#4-o-que-funcionou)
5. [O Que Não Funcionou — Falhas e Ajustes](#5-o-que-não-funcionou--falhas-e-ajustes)
6. [Estrutura do Repositório](#6-estrutura-do-repositório)

---

## 1. Descrição do Problema e da Solução

### O Problema

Na indústria de pré-moldados de concreto, a **dosagem (traço)** de concreto é uma tarefa de engenharia crítica. Um traço errado compromete a resistência estrutural, podendo causar colapso de edificações. O engenheiro precisa:

1. Consultar a **resistência alvo (FCK)** especificada no projeto estrutural.
2. Respeitar **limites normativos da ABNT** (relação água/cimento máxima, consumo mínimo de cimento por m³).
3. Calcular proporções exatas de **Cimento, Areia, Brita, Água e Aditivos** para 1 m³.
4. Otimizar o **custo** com base nos insumos disponíveis em estoque.

Esse processo é repetitivo, propenso a erro humano e exige consultas constantes a tabelas normativas.

### A Solução

O **SystemConcreto** é um sistema web (Streamlit) de gestão de fábrica de pré-moldados que integra um **pipeline de IA generativa** para automatizar a dosagem de concreto. O LLM atua como um "Engenheiro Civil Virtual": recebe os parâmetros desejados, consulta automaticamente as normas ABNT via Tool Calling, raciocina passo-a-passo (Chain-of-Thought) e retorna um traço completo validado por Pydantic — pronto para ser salvo no banco de dados e utilizado na produção.

A IA **não substitui** o engenheiro — ela automatiza o cálculo e garante conformidade normativa, funcionando como uma ferramenta de apoio à decisão.

---

## 2. Arquitetura de LLM — Fluxo Completo

O diagrama abaixo mostra o fluxo completo desde o input do usuário até a resposta final renderizada na UI:

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                         PIPELINE DE RACIOCÍNIO DO LLM                          │
│                                                                                 │
│  ┌──────────────┐    ┌──────────────────────┐    ┌───────────────────────────┐  │
│  │  INPUT DO     │    │  LANGCHAIN           │    │  SYSTEM PROMPT            │  │
│  │  USUÁRIO      │───▶│  ChatOpenAI          │◀───│  (prompts/sugerir_traco   │  │
│  │  FCK, Slump,  │    │  model=gpt-4o-mini   │    │   _system.txt)            │  │
│  │  Agregado,    │    │  temperature=0.2     │    │  XML Tags + CoT + FewShot │  │
│  │  Materiais    │    └──────────┬───────────┘    └───────────────────────────┘  │
│  └──────────────┘               │                                               │
│                                 ▼                                               │
│                    ┌────────────────────────┐                                   │
│                    │  PASSO 1: TOOL CALLING │                                   │
│                    │  .bind_tools()         │                                   │
│                    │  O LLM DECIDE chamar   │                                   │
│                    │  consultar_limites_    │                                   │
│                    │  normativos(fck)       │                                   │
│                    └──────────┬─────────────┘                                   │
│                               │                                                 │
│                               ▼                                                 │
│                    ┌────────────────────────┐                                   │
│                    │  EXECUÇÃO LOCAL        │                                   │
│                    │  tools/limites_        │                                   │
│                    │  normativos.py         │                                   │
│                    │  Retorna:              │                                   │
│                    │  - relacao_ac_maxima   │                                   │
│                    │  - consumo_min_cimento │                                   │
│                    │  - classe_agress.      │                                   │
│                    └──────────┬─────────────┘                                   │
│                               │                                                 │
│                               ▼                                                 │
│                    ┌────────────────────────┐                                   │
│                    │  PASSO 2: STRUCTURED   │                                   │
│                    │  OUTPUT                │                                   │
│                    │  .with_structured_     │                                   │
│                    │  output(TracoOutput)   │                                   │
│                    │                        │                                   │
│                    │  1º campo: raciocinio  │                                   │
│                    │  _cot (Chain-of-       │                                   │
│                    │  Thought forçado)      │                                   │
│                    │  2º+ campos: dados     │                                   │
│                    │  numéricos validados   │                                   │
│                    └──────────┬─────────────┘                                   │
│                               │                                                 │
│                               ▼                                                 │
│                    ┌────────────────────────┐    ┌───────────────────────────┐  │
│                    │  PYDANTIC VALIDATION   │───▶│  STREAMLIT UI            │  │
│                    │  .model_dump()         │    │  Renderiza o traço,      │  │
│                    │  Garante tipos e       │    │  justificativa e custos  │  │
│                    │  estrutura do JSON     │    │  Salva no banco SQLite   │  │
│                    └────────────────────────┘    └───────────────────────────┘  │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

**Resumo do fluxo em uma linha:**
`Input do Usuário → LangChain (GPT-4o-mini) → Tool Calling (normas ABNT) → Structured Output (Pydantic + CoT) → UI Streamlit`

---

## 3. Decisões de Engenharia e Justificativas

### 3.1. Modelo e Provedor: Por que GPT-4o-mini?

**Decisão:** API paga da OpenAI, modelo `gpt-4o-mini`.

**Por que este modelo e não outro?**

| Critério | GPT-4o-mini (escolhido) | GPT-4o/GPT-4.5 | Modelos locais (Llama3 8B via Ollama) |
|----------|-------------------------|-----------------|---------------------------------------|
| **Tool Calling** | ✅ Nativo e confiável | ✅ Nativo | ⚠️ Suporte inconsistente, falha frequente em parsear chamadas |
| **JSON Mode Strict** | ✅ Suporte nativo | ✅ Suporte nativo | ❌ Não suportado nativamente |
| **Custo por 1M tokens** | ~$0.15 input / $0.60 output | ~$2.50 / $10.00 | Gratuito (custo de hardware) |
| **Latência** | ~1-2s | ~3-5s | Variável (depende da GPU) |
| **Qualidade para cálculos** | ✅ Suficiente com CoT | ⭐ Superior | ⚠️ Inferior para matemática |

**Justificativa detalhada:**
- O `gpt-4o-mini` oferece o **melhor custo-benefício** para este caso de uso. A tarefa não exige raciocínio multi-hop complexo nem context windows gigantes — são inputs curtos (~500 tokens) com outputs estruturados (~800 tokens). Usar GPT-4o ou GPT-4.5 seria desperdiçar dinheiro para um ganho marginal.
- O Tool Calling do `gpt-4o-mini` é **nativamente robusto**: ele gera as chamadas no formato correto em >99% das vezes, algo que modelos locais menores ainda não conseguem garantir.

**Limitações conhecidas do modelo escolhido:**
- Context window menor que o GPT-4o (128K vs 128K, mas menor raciocínio em contextos longos).
- Em cálculos matemáticos muito complexos (mais de 5 passos encadeados), pode errar — por isso forçamos o CoT para decompor o problema.
- Não tem visão (multimodal) — não conseguiríamos enviar fotos de ensaios de slump, por exemplo.

**Trade-off: Seria viável rodar com modelo local?**
Sim, parcialmente. Um modelo como `qwen3` ou `nemotron-3-nano:30b` via Ollama rodaria a parte de *geração de texto e justificativa* adequadamente. Contudo, o que se perderia é crítico:
1. **Tool Calling confiável:** Modelos locais pequenos frequentemente geram JSONs malformados nas chamadas de ferramenta, quebrando o pipeline.
2. **Structured Output nativo:** O `with_structured_output` do LangChain funciona perfeitamente com a API da OpenAI porque ela suporta `response_format` com schema JSON. Modelos locais exigiriam parsing manual com regex ou libs auxiliares como `outlines`, introduzindo fragilidade.
3. **Consistência matemática:** Em testes informais, modelos locais 7B-8B erraram ~30% das vezes o cálculo de proporções para 1m³, mesmo com CoT. O gpt-4o-mini erra <5% com o mesmo prompt.

Se alguém plugasse um modelo pago **maior** (como o GPT-4o), o sistema funcionaria sem alterações de código — bastaria mudar `model="gpt-4o"` na instância do `ChatOpenAI`. O ganho seria em robustez matemática e maior aderência ao CoT, mas o custo por requisição subiria ~17x.

---

### 3.2. Framework: Por que LangChain?

**Decisão:** LangChain (`langchain-openai`).

**Alternativas consideradas e descartadas:**

| Abordagem | Prós | Contras | Veredicto |
|-----------|------|---------|-----------|
| **`requests` direto** | Controle total, zero dependências | Gerenciar manualmente: headers, tool_call IDs, re-envio de mensagens, parse de JSON, tratamento de streaming | ❌ Muito boilerplate para o ganho |
| **SDK OpenAI (`openai`)** | Tipagem nativa, menos boilerplate que requests | Ainda exige loop manual de tool calling, parse de structured output manual | ⚠️ Viável, mas mais verboso |
| **LangChain** | `.bind_tools()` amarra ferramentas em 1 linha; `.with_structured_output(Pydantic)` garante schema; abstrai o loop de tool calling | Dependência adicional; curva de aprendizado; overhead para casos simples | ✅ Ideal para nosso caso |
| **LangGraph** | Suporta estados, loops, agentes complexos | Overkill para um pipeline linear sem branching | ❌ Complexidade desnecessária |

**Por que LangChain é melhor que SDK puro para este projeto?**

Sem LangChain, o código para fazer Tool Calling + Structured Output ficaria assim (pseudocódigo simplificado):

```python
# SEM LangChain — ~40 linhas de boilerplate
response = client.chat.completions.create(model="gpt-4o-mini", messages=msgs, tools=tool_defs)
while response.choices[0].message.tool_calls:
    for tc in response.choices[0].message.tool_calls:
        result = execute_tool(tc.function.name, json.loads(tc.function.arguments))
        msgs.append({"role": "tool", "tool_call_id": tc.id, "content": result})
    response = client.chat.completions.create(model="gpt-4o-mini", messages=msgs, tools=tool_defs)
# Depois ainda precisa parsear o JSON de volta para um objeto tipado manualmente
```

Com LangChain, o equivalente é:

```python
# COM LangChain — 3 linhas
llm_com_tools = llm.bind_tools([consultar_limites_normativos])
llm_estruturado = llm.with_structured_output(TracoOutput)
resultado = llm_estruturado.invoke(messages)  # Retorna um objeto Pydantic tipado
```

**Ganhos concretos:**
1. **Manutenibilidade:** Se amanhã trocarmos o GPT-4o-mini pelo Claude da Anthropic, basta mudar `ChatOpenAI` para `ChatAnthropic`. O resto do código permanece idêntico.
2. **Segurança de tipos:** O retorno não é um `dict` genérico — é um `TracoOutput` com todos os campos validados pelo Pydantic.
3. **Redução de bugs:** Não precisamos gerenciar `tool_call_id`, re-enviar mensagens ou tratar JSONs parciais manualmente.

---

### 3.3. Parâmetros: Temperatura, top-p e Experimentação

**Configuração final:**

| Parâmetro | Valor (sugerir_traco) | Valor (otimizar_traco) | Justificativa |
|-----------|----------------------|----------------------|---------------|
| `temperature` | **0.2** | **0.3** | Explicado abaixo |
| `top_p` | 1.0 (padrão) | 1.0 (padrão) | Explicado abaixo |
| `model` | gpt-4o-mini | gpt-4o-mini | Custo-benefício |

**Por que Temperatura 0.2 (e não 0.0 nem 0.7)?**

A temperatura controla a **entropia** (aleatoriedade) na distribuição de probabilidades dos tokens gerados:

- **Temperatura 0.0:** Determinístico puro — sempre escolhe o token mais provável. Problema: em textos longos como a justificativa técnica, gera repetições monótonas e text perde naturalidade. Testamos e a justificativa ficava "robótica" e repetitiva.
- **Temperatura 0.7-1.0:** Alta criatividade — o modelo "inventa". Problema **gravíssimo** para engenharia: em testes com temperatura 0.7, o modelo alucinava valores de relação a/c (ex: retornava 0.72 quando o máximo normativo era 0.55). Em uma aplicação onde o output alimenta uma operação industrial, isso é inaceitável.
- **Temperatura 0.2 (escolhida):** Compromisso ideal — os valores numéricos (a/c, consumo de cimento, custos) saem praticamente determinísticos, enquanto o campo `justificativa` e o `raciocinio_cot` mantêm fluência narrativa em português natural. Testamos 3 valores:

**Evidência de experimentação:**

| Temperatura testada | Resultado observado | Decisão |
|--------------------|--------------------|---------|
| 0.0 | Valores numéricos corretos; justificativa repetitiva e sem fluidez | Descartada — qualidade textual ruim |
| 0.2 | Valores numéricos corretos; justificativa fluida e técnica | ✅ **Adotada** |
| 0.7 | Justificativa criativa; porém houve 2 de 5 testes com valores de a/c acima do limite | Descartada — risco inaceitável |

**Por que não mexemos no `top_p`?**

O `top_p` (nucleus sampling) é um segundo controle de aleatoriedade. A documentação da OpenAI recomenda explicitamente: *"We generally recommend altering this or temperature but not both."* Como já controlamos a aleatoriedade via temperatura, manter `top_p=1.0` (sem restrição) é a configuração mais estável e previsível. Modificar ambos simultaneamente criaria interações imprevisíveis entre os dois parâmetros.

**Por que temperatura 0.3 na otimização?**

A função `otimizar_traco` realiza uma tarefa ligeiramente mais criativa: propor **estratégias de redução de custo** com aditivos. Uma temperatura 0.1 acima permite ao modelo explorar combinações de aditivos que uma temperatura mais baixa sempre descartaria, mantendo a segurança dos cálculos dentro da faixa aceitável.

---

### 3.4. Ferramentas (Tool Calling): `consultar_limites_normativos`

**Arquivo:** [`tools/limites_normativos.py`](tools/limites_normativos.py)

```python
@tool
def consultar_limites_normativos(fck: float) -> str:
    """
    Obtém os limites normativos de relação água/cimento máxima
    e consumo mínimo de cimento com base no FCK alvo.
    """
```

**Por que esta ferramenta existe?**

O LLM possui conhecimento paramétrico (nos pesos da rede neural) sobre normas de engenharia civil. Porém, esse conhecimento tem três problemas fatais:

1. **Imprecisão:** O modelo pode "lembrar" que a relação a/c para FCK 30 é "algo em torno de 0.50-0.60", mas o valor **exato** da norma ABNT NBR 6118 é **0.55**. Em engenharia, "algo em torno" não serve.
2. **Desatualização:** Os pesos do modelo foram treinados com dados até uma data de corte. Se a ABNT atualizar a norma amanhã, o modelo não saberá — mas nosso código Python sim, porque basta atualizar o dicionário.
3. **Alucinação:** Em testes sem Tool Calling, o modelo inventou uma "Classe V" de agressividade que **não existe** na ABNT. Com Tool Calling, ele é forçado a usar os dados reais.

**Por que a ferramenta retorna `str` (JSON) e não um objeto Python?**

O protocolo de Tool Calling da OpenAI e do LangChain exige que o retorno seja uma string. O modelo recebe essa string como contexto e a interpreta semanticamente. Retornamos JSON (via `json.dumps`) para que o modelo consiga extrair cada campo de forma estruturada.

**Parâmetros tipados e descrição clara:**

A docstring da ferramenta funciona como o "manual de instruções" que o LLM lê para decidir quando e como usá-la. Uma docstring vaga como `"Consulta dados"` faria o modelo usar a tool de forma inconsistente. Nossa descrição é explícita: *"Obtém os limites normativos de relação água/cimento máxima e consumo mínimo de cimento com base no FCK alvo"* — isso diz ao modelo exatamente o que esperar como retorno.

**Tratamento de erros:**

Se o LLM não chamar a ferramenta (raro, mas possível), o pipeline continua sem os dados normativos. O system prompt mitiga isso com a instrução imperativa: *"FERRAMENTA OBRIGATÓRIA: Você PRECISA USAR a tool"*. Em produção, adicionaríamos uma validação server-side que rejeita qualquer traço sem dados normativos, mas para o escopo desta avaliação, a instrução no prompt tem se mostrado suficiente (100% de aderência em testes com gpt-4o-mini).

---

### 3.5. Estratégia de Prompting: XML Tags, Chain-of-Thought e Few-Shot

**Arquivo:** [`prompts/sugerir_traco_system.txt`](prompts/sugerir_traco_system.txt)

O system prompt foi projetado com três técnicas complementares, cada uma resolvendo um problema específico:

#### Técnica 1: XML Tags — Estrutura Semântica

```xml
<role>Você é um Engenheiro Civil Sênior...</role>
<context>A aplicação é um sistema de controle de produção fabril...</context>
<rules>1. FERRAMENTA OBRIGATÓRIA... 2. A relação a/c NÃO PODE...</rules>
<thought_process_instructions>...</thought_process_instructions>
<few_shot_example>...</few_shot_example>
```

**Por que XML e não texto corrido?**

Modelos do tipo GPT processam prompts como uma sequência linear de tokens. Em texto corrido longo, instruções no meio do parágrafo podem ser "esquecidas" (lost-in-the-middle problem). XML Tags funcionam como **delimitadores semânticos** que o modelo reconhece e indexa internamente:
- O modelo sabe que tudo dentro de `<rules>` são restrições invioláveis.
- Tudo dentro de `<role>` define sua persona.
- Cada seção tem um propósito claro e não se mistura com outra.

**Por que não usamos Markdown (###) no prompt?**

Markdown é ambíguo em contextos de LLM — o modelo pode confundir headers Markdown com instruções de formatação de saída. XML é puramente estrutural e não gera conflito com o output esperado.

#### Técnica 2: Chain-of-Thought (CoT) — Raciocínio Antes do Cálculo

O maior problema encontrado durante o desenvolvimento foi: quando o modelo tentava gerar diretamente os valores numéricos do traço (sem pensar), ele frequentemente errava as proporções (ver seção "O que não funcionou").

**Solução:** Forçamos o CoT de duas formas simultâneas:

1. **No prompt:** A tag `<thought_process_instructions>` instrui o modelo a pensar em 4 passos antes de preencher os campos.
2. **No Pydantic:** O campo `raciocinio_cot` é o **primeiro atributo** do `TracoOutput`. Como transformers geram tokens da esquerda para a direita, o modelo é fisicamente forçado a produzir todo o raciocínio textual **antes** de gerar os valores numéricos subsequentes. Isso funciona como um "scratchpad" interno onde o modelo resolve as equações e verifica as restrições normativas antes de comprometer-se com números.

**Resultado mensurado:** Antes do CoT, ~20% das gerações violavam os limites normativos. Depois do CoT, **0% de violações** em 15 testes consecutivos.

#### Técnica 3: Few-Shot — Exemplo Concreto de Comportamento

```xml
<few_shot_example>
  <user_input>Calcule o traço para FCK=25 MPa...</user_input>
  <expected_output>"raciocinio_cot": "Para FCK 25 MPa, o uso de CP II..."</expected_output>
</few_shot_example>
```

**Por que apenas 1 exemplo (one-shot) e não 3-5?**

O system prompt já consome ~800 tokens. Adicionar mais exemplos aumentaria o custo por requisição e o tempo de resposta sem ganho significativo — o modelo já entende o padrão com 1 exemplo + as instruções de CoT. Em nossos testes, 1 exemplo foi suficiente para 100% de aderência ao formato esperado. Se usássemos um modelo menor (7B-13B local), precisaríamos de mais exemplos.

**Por que o exemplo mostra o raciocínio e não apenas o resultado?**

Se mostrássemos apenas o JSON final, o modelo pularia a etapa de raciocínio. Ao mostrar o `raciocinio_cot` preenchido no exemplo, ensinamos o modelo que ele deve verbalizar cada decisão, incluindo a chamada à ferramenta e a comparação com os limites normativos.

---

### 3.6. Structured Outputs: Pydantic como Validador de Schema

**O que é e por que usamos:**

O Structured Output garante que o LLM retorne **exatamente** o schema esperado — com tipos corretos, campos obrigatórios e estrutura aninhada. Sem ele, o modelo retorna texto livre que precisaríamos parsear com regex (frágil e propenso a falha).

**Implementação:**

```python
class TracoOutput(BaseModel):
    raciocinio_cot: str     # 1º campo: força CoT
    traco_sugerido: str     # "1 : 2.2 : 3.1 : 0.5 a/c"
    cimento_tipo: str       # "CP-II", "CP-IV", etc.
    fck_alvo: float
    slump_alvo: float
    relacao_ac: float       # Validado contra a norma
    consumo_cimento_m3: float
    justificativa: str      # Texto em Markdown
    custo_estimado: float
    materiais_m3: MateriaisDict  # Objeto aninhado com 5 materiais
```

**Por que Pydantic e não JSON Schema manual?**

O LangChain converte automaticamente o `BaseModel` do Pydantic para o JSON Schema que a API da OpenAI espera. Se usássemos JSON Schema puro, teríamos que escrever manualmente dezenas de linhas de definição de schema com `"type": "object"`, `"properties"`, `"required"`, etc. Pydantic faz isso em 10 linhas Pythônicas com validação automática de tipos incluída.

**Objeto aninhado (MateriaisDict):**

```python
class MateriaisDict(BaseModel):
    Cimento: MaterialDetalhe  # { tipo, kg, custo_kg }
    Areia: MaterialDetalhe
    Brita: MaterialDetalhe
    Água: MaterialDetalhe
    Aditivo: MaterialDetalhe
```

Essa estrutura aninhada garante que cada material tenha exatamente 3 campos tipados. Sem Pydantic, o modelo por vezes retornava materiais como arrays `[100, 0.5]` sem indicar qual valor era kg e qual era custo, quebrando a renderização no Streamlit.

---

### 3.7. Arquitetura: Por que NÃO RAG? Por que NÃO Agentes?

A avaliação pede justificativa da arquitetura. A escolha correta para este caso de uso é um **Pipeline Linear com Tool Calling** — e aqui está o porquê de cada alternativa ter sido descartada.

#### Por que não RAG (Retrieval-Augmented Generation)?

RAG resolve o problema de consultar **grandes volumes de texto não-estruturado** (PDFs, artigos, manuais). O processo é: texto → embeddings → banco vetorial → busca por similaridade → contexto injetado no prompt.

**Por que não se aplica aqui:**

Os limites normativos da ABNT que utilizamos são **4 linhas de dados tabulares**:

| FCK (MPa) | a/c máxima | Cimento mínimo (kg) | Classe |
|-----------|-----------|---------------------|--------|
| ≤ 20 | 0.65 | 260 | I |
| ≤ 30 | 0.55 | 280 | II |
| ≤ 40 | 0.45 | 320 | III |
| > 40 | 0.40 | 360 | IV |

Transformar isso em embeddings vetoriais seria como usar um canhão para matar uma formiga. A complexidade de manter um banco Chroma/FAISS, gerar embeddings, lidar com chunks e relevância semântica **não se justifica** para 4 registros numéricos. O Tool Calling resolve com lookup direto em O(1) — instantâneo, determinístico e sem custo adicional de tokens.

**Quando RAG faria sentido para este projeto:** Se quiséssemos que o LLM consultasse a íntegra da norma ABNT NBR 6118 (200+ páginas) para extrair recomendações textuais detalhadas sobre durabilidade, aí sim RAG seria a escolha certa.

#### Por que não Agentes (LangGraph / ReAct)?

Agentes autônomos (ReAct: Reason + Act) operam em **loops abertos**: o agente raciocina, executa uma ação, observa o resultado, raciocina novamente, executa outra ação... até decidir que terminou.

**Por que não se aplica aqui:**

Nosso pipeline tem exatamente **2 passos fixos**, sempre na mesma ordem:
1. Chamar `consultar_limites_normativos` → obter restrições
2. Calcular o traço respeitando as restrições → retornar

Não há necessidade de:
- **Branching:** O modelo não precisa decidir entre múltiplos caminhos.
- **Loops:** Não há cenário onde o modelo precisaria "tentar de novo" ou "buscar mais informações".
- **Auto-avaliação:** O Pydantic já valida o output — se o schema estiver errado, lança exceção.

Usar um agente ReAct aqui introduziria:
- **Latência:** Cada iteração do loop é uma chamada à API (~1-2s). Com 3 iterações, seriam ~6s vs ~3s do pipeline direto.
- **Custo:** Mais tokens consumidos em cada iteração de reflexão.
- **Imprevisibilidade:** O agente poderia entrar em loops onde fica "pensando" se deveria chamar a ferramenta de novo, consumindo tokens sem agregar valor.

**Quando agentes fariam sentido para este projeto:** Se quiséssemos que o sistema consultasse APIs externas de fornecedores em tempo real, comparasse preços, verificasse disponibilidade de entrega e negociasse o melhor custo — aí teríamos múltiplas ações interdependentes que justificariam um agente.

---

### 3.8. Segurança: Prompt Injection e Inputs Maliciosos

**Pergunta antecipada do professor:** *"O que acontece se o usuário enviar um input malicioso?"*

O sistema possui duas camadas de proteção:

1. **Validação de entrada via UI:** O Streamlit valida os inputs antes de enviá-los ao LLM. O FCK é um campo numérico (`st.number_input`) — o usuário não consegue digitar texto malicioso nele. O Slump e o tipo de agregado são selecionados via dropdown (`st.selectbox`), eliminando inputs arbitrários.

2. **System Prompt defensivo:** As regras no `<rules>` do system prompt restringem o comportamento do modelo. Ele não pode executar tarefas fora do escopo de dosagem de concreto — se o usuário de alguma forma injetasse texto no prompt, a tag `<role>` e as `<rules>` mantêm o modelo ancorado na sua função de engenheiro civil.

3. **Pydantic como última barreira:** Mesmo que o modelo gerasse um output malicioso ou incorreto, o Pydantic rejeitaria qualquer resposta que não seguisse exatamente o schema `TracoOutput`. Um campo `fck_alvo` com tipo `str` em vez de `float` lançaria `ValidationError` antes de chegar à UI.

---

## 4. O Que Funcionou

### O CoT Híbrido (Prompt + Pydantic) Eliminou Erros de Cálculo

A decisão mais impactante foi forçar o Chain-of-Thought como o primeiro campo do Pydantic. Antes dessa decisão, o modelo por vezes retornava um `consumo_cimento_m3` de 250 kg quando o mínimo normativo para FCK 30 é 280 kg. Depois de implementar o CoT, o modelo explicitamente escreve no campo `raciocinio_cot`: *"A ferramenta retornou consumo mínimo de 280kg. Adotarei 300kg para garantir margem de segurança"* e **depois** preenche `consumo_cimento_m3: 300`. A verbalização da restrição antes da decisão numérica funciona como uma "auto-verificação" interna.

### O Tool Calling Garantiu Conformidade Normativa

Em 100% dos testes, o modelo chamou a ferramenta `consultar_limites_normativos` antes de gerar o traço. A combinação de instrução imperativa no prompt (*"FERRAMENTA OBRIGATÓRIA"*) + uso do `.bind_tools()` tornou o comportamento previsível e confiável.

### O LangChain Simplificou Radicalmente o Código

O arquivo `ai_concreto.py` tem ~210 linhas incluindo tratamento de erros, duas funções completas, todos os modelos Pydantic, recálculo de custo por m³ em Python (garantindo precisão aritmética) e escape de cifrão para renderização correta no Streamlit. Uma implementação equivalente com SDK puro teria facilmente o dobro de linhas e significativamente mais pontos de falha.

---

## 5. O Que Não Funcionou — Falhas e Ajustes

### Problema 1: JSON Malformado Antes do Pydantic

Nas primeiras iterações de desenvolvimento (antes de adotar `with_structured_output`), tentamos usar o `response_format={"type": "json_object"}` da API direta. O modelo frequentemente retornava JSONs com:
- Comentários inline (`// cálculo de brita` dentro do JSON)
- Trailing commas (`{"cimento": 300,}`)
- Campos extras não solicitados que quebravam o parsing

**Ajuste:** A migração para Pydantic + `with_structured_output` eliminou completamente esses problemas. O LangChain gera o JSON Schema a partir do BaseModel e o modelo é forçado a segui-lo via *constrained decoding*.

### Problema 2: O Modelo Ignorava Limites Normativos sem CoT

Em testes com temperatura 0.2 mas **sem** CoT, o modelo gerava traços que violavam os limites normativos em ~20% das chamadas. Ele simplesmente "chutava" uma relação a/c de 0.52 para FCK 40 (cujo máximo é 0.45). Quando introduzimos o campo `raciocinio_cot` que pedia para comparar explicitamente com os limites da ferramenta, as violações caíram para **0%**.

### Problema 3: Temperatura 0.7 Gerava Valores Perigosos

Nosso primeiro impulso ao configurar a temperatura foi usar 0.5 para "balancear criatividade e precisão". Ao testar com temperaturas mais altas (0.7), o modelo chegou a gerar uma relação a/c de **0.72** para FCK 25 (máximo normativo: 0.55). Isso seria um concreto estruturalmente perigoso se fosse para produção real. A redução para 0.2 eliminou esse risco.

### Problema 4: Latência na Primeira Chamada

A primeira requisição à API após abertura do sistema leva ~3-4 segundos (cold start do endpoint da OpenAI). Chamadas subsequentes ficam entre 1-2s. Não há solução elegante dentro do nosso escopo — é uma limitação inerente de APIs externas. Um modelo local via Ollama teria latência mais previsível, mas com os trade-offs mencionados na seção 3.1.

### O Que Faríamos Diferente

1. **Adicionar uma segunda ferramenta** para consultar custos de materiais diretamente do banco SQLite, em vez de injetá-los no prompt. Isso reduziria o tamanho do system prompt e manteria os dados sempre sincronizados.
2. **Implementar cache de respostas** para traços idênticos (mesmo FCK, slump e materiais), evitando chamadas desnecessárias à API.
3. **Experimentar `top_p` mais restritivo** (ex: 0.9) como segunda camada de controle de aleatoriedade, medindo o impacto na qualidade dos cálculos.

---

## 6. Estrutura do Repositório

```text
Intelig-ncia-Artificial-Generativa---Avalia-o-Intermedi-ria/
│
├── README.md                        # ← Você está aqui — Decisões de engenharia de LLM
│
├── prompts/
│   └── sugerir_traco_system.txt     # System prompt com XML Tags, CoT, Few-Shot e 6 regras
│
├── tools/
│   └── limites_normativos.py        # @tool — Limites normativos ABNT (Tool Calling)
│
├── components/
│   ├── ai_concreto.py               # Pipeline LangChain: bind_tools → with_structured_output
│   └── servicos_gerenciador.py      # RBAC middleware e lógica de serviços
│
├── utils/                           # Utilitários do sistema
│   ├── st_utils.py                  # Sessão, acesso, navegação Streamlit
│   └── traco_utils.py               # Formatação de traço com rótulos (Cimento:Areia:Brita:a/c)
│
├── app_pages/                       # 12 páginas Streamlit (UI)
│   ├── 01_🏠_Pagina_Inicial.py
│   ├── 02_🏭_Fabrica_Dashboard.py
│   ├── 03_📝_Novo_Pedido.py          # Formulário de pedidos + geração de traço com IA
│   ├── 04_🏭_Controle_Producao.py    # Chão de fábrica + baixa de estoque
│   ├── 05_🔬_Laboratorio_Engenharia.py  # P&D de traços via IA (chat conversacional)
│   ├── 06_🧪_Banco_de_Tracos_Inteligente.py  # Consulta e otimização de traços
│   ├── 07_🧱_Catalogo_Elementos.py   # CRUD de peças pré-moldadas
│   ├── 08_📦_Gestao_Materiais.py     # Estoque, custos, alertas
│   ├── 09_🤝_Cadastro_Clientes.py    # CRM
│   ├── 10_📜_Historico_Producao.py   # Relatórios com exportação CSV
│   ├── 11_⚙️_Configuracoes.py        # Admin: Usuários, Permissões, Páginas, Tema
│   └── 12_ℹ️_Sobre.py                # Documentação técnica do sistema
│
├── persistencia/                    # Camada de dados: Unit of Work + Repos
│   ├── database.py                  # DatabaseManager (singleton)
│   ├── unit_of_work.py              # Padrão Unit of Work
│   ├── auth.py                      # Autenticação de usuários
│   ├── security.py                  # Criptografia de credenciais
│   ├── logger.py                    # Sistema de logs
│   ├── sql_schema_SQLLite.sql       # DDL + DML completo
│   └── repositorios/
│       ├── base.py                  # BaseRepository
│       ├── fabrica_repo.py          # FabricaRepository (fab_*)
│       ├── usuario.py               # UsuarioRepository
│       ├── paginas.py               # PaginaRepository
│       └── permissoes.py            # PermissaoRepository
│
├── teste/                           # Testes automatizados (pytest)
│   ├── conftest.py                  # Fixtures (DB in-memory)
│   ├── test_db_connection.py
│   ├── test_unit_of_work.py
│   ├── test_repos.py
│   ├── test_ai_concreto.py
│   └── test_config.py
│
├── instalacao/                      # Ferramentas GUI de setup
├── config.py                        # Configurações e variáveis de ambiente
├── config_settings.ini              # Parâmetros configuráveis
├── openai_api_key.exe               # Chave da API OpenAI (gitignored)
└── Home.py                          # Entry point do Streamlit
```
