# Plano de Melhoria — Qualidade de Voz TTS por Provedor

> **Data:** 2026-06-27
> **Objetivo:** Diagnosticar e corrigir problemas de naturalidade, sotaque e configuração de voz em cada provedor TTS.

---

## Sumário dos Problemas Identificados

| Problema | Provedores Afetados | Gravidade |
|----------|-------------------|-----------|
| Voz com sotaque estrangeiro no português | Cartesia, ElevenLabs, Inworld | 🔴 Alta |
| Nenhum suporte a português | Smallest.ai | 🔴 Alta |
| Voz robótica / sem emoção | Todos (config padrão) | 🟡 Média |
| Sem preview de voz funcional | Cartesia, Smallest, Gemini, Inworld, Async | 🟡 Média |
| Modelo/speed/estilo sem exposição na UI | Todos | 🟢 Baixa |

---

## 1. ElevenLabs

### 🧠 Diagnóstico

A ElevenLabs tem **a melhor qualidade geral** de voz, mas:
- O `language_code` estava sendo enviado como `pt-BR` mas a API espera ISO 639-1 (`pt`)
- Os `voice_settings` padrão (stability=0.5, similarity=0.75) são genéricos demais
- Não estávamos usando `style` e `use_speaker_boost`

### 📋 Especificações da API

**Endpoint:** `POST /v1/text-to-speech/{voice_id}`
**Modelo recomendado para português:** `eleven_multilingual_v2`

```json
{
  "text": "...",
  "model_id": "eleven_multilingual_v2",
  "language_code": "pt",
  "voice_settings": {
    "stability": 0.35,
    "similarity_boost": 0.75,
    "style": 0.33,
    "use_speaker_boost": true
  }
}
```

### 🔧 O Que Precisa Ser Feito

| Tarefa | Descrição |
|--------|-----------|
| 1.1 | Mapear `language_code` corretamente: `pt-BR` → `pt`, `en` → `en`, etc. (já feito parcialmente, revisar) |
| 1.2 | Adicionar `voice_settings` ao payload de síntese com valores otimizados |
| 1.3 | Expor controles de `stability`, `similarity_boost` e `style` na UI como sliders |
| 1.4 | Usar `eleven_multilingual_v2` como modelo padrão para pt-BR (já feito, verificar) |
| 1.5 | Listar modelos dinamicamente de `GET /v1/models` e mostrar `languages` de cada um (já feito) |
| 1.6 | Usar `preview_url` do endpoint `/v1/voices` para preview de voz (já feito, testar) |

### 🎯 Valores Recomendados de Voice Settings

| Parâmetro | Voz Natural | Voz Estável | Voz Expressiva |
|-----------|:-----------:|:-----------:|:--------------:|
| `stability` | 0.35 | 0.70 | 0.20 |
| `similarity_boost` | 0.75 | 0.85 | 0.65 |
| `style` | 0.33 | 0.10 | 0.60 |
| `use_speaker_boost` | true | true | true |

---

## 2. Cartesia

### 🧠 Diagnóstico

**Problema principal:** As vozes da Cartesia são nativas em **inglês** e, quando falam português, usam sotaque americano porque não estão localizadas.

A Cartesia oferece um **endpoint de localização de voz** (`POST /voices/localize`) que cria uma nova voz localizada para o idioma e dialeto desejado — incluindo **Português Brasileiro** (`pt` + `dialect: "br"`).

Atualmente, nosso código:
- Envia `language: "pt"` no payload (correto)
- Mas usa vozes inglesas (`Barbershop Man`, `Gentle Woman`) que não foram localizadas
- Não usa `generation_config` com `emotion`

### 📋 Especificações da API

**Localização de voz:**
```json
POST /voices/localize
{
  "voice_id": "694f9389-...",
  "name": "Barbershop Man (Português Brasil)",
  "description": "Barbershop Man localizado para PT-BR",
  "language": "pt",
  "original_speaker_gender": "male",
  "dialect": "br"
}
```

**Síntese com configuração otimizada:**
```json
{
  "transcript": "...",
  "model_id": "sonic-3.5",
  "voice": {"mode": "id", "id": "voice_id_localizada"},
  "language": "pt",
  "output_format": {"container": "mp3", "sample_rate": 44100, "bit_rate": 128000},
  "generation_config": {
    "speed": 1.0,
    "emotion": "natural"
  }
}
```

### 🔧 O Que Precisa Ser Feito

| Tarefa | Descrição | Prioridade |
|--------|-----------|:----------:|
| 2.1 | **Criar ferramenta CLI** `python -m app.tools.localize_cartesia` que localiza vozes para PT-BR via `/voices/localize` | 🔴 Alta |
| 2.2 | Salvar `voice_id` localizada no banco de dados para reuso | 🔴 Alta |
| 2.3 | Adicionar `generation_config.emotion` ao payload (default: `"natural"`) | 🟡 Média |
| 2.4 | Expor slider de `speed` no payload da Cartesia (range: 0.6–1.5) | 🟢 Baixa |
| 2.5 | Testar vozes localizadas e verificar se o sotaque sumiu | 🔴 Alta |
| 2.6 | Se a localização não estiver disponível, usar `language: "pt"` + modelo sonic-3.5 que tem melhor suporte multilíngue | 🟡 Média |

### 🎯 Vozes Recomendadas para Localizar em PT-BR

| Voz Original | ID | Gênero | Prioridade |
|-------------|-----|:------:|:----------:|
| Barbershop Man | `694f9389-aac1-45b6-b726-9d9369183238` | Masculino | 1 |
| Gentle Woman | `aad81f96-3792-4d13-b105-188e6be3bf5c` | Feminino | 2 |
| American Woman | `bf0a246a-8642-498a-9950-80c35e9276b5` | Feminino | 3 |
| British Man | `00510a15-4216-4fdc-a0ab-05d74cd9f795` | Masculino | 4 |

---

## 3. Smallest.ai

### 🧠 Diagnóstico

**A Smallest NÃO SUPORTA português.** Os idiomas disponíveis são:
- `en`, `hi`, `mr`, `kn`, `ta`, `te`, `gu`, `bn`, `ml`

Isso significa que **qualquer texto em português gerado pela Smallest terá pronúncia incorreta**.

Atualmente nosso código:
- Envia `language: "pt"` ou `"pt-BR"` → a API ignora ou processa errado
- Usa vozes como `emily`, `lakshya` que não têm suporte a português
- O resultado é um áudio irreconhecível

### 📋 Especificações da API

```json
{
  "text": "...",
  "voice_id": "emily",
  "model": "lightning-large",
  "sample_rate": 24000,
  "speed": 1.0,
  "consistency": 0.5,
  "similarity": 0.0,
  "enhancement": 1,
  "language": "en"
}
```

### 🔧 O Que Precisa Ser Feito

| Tarefa | Descrição | Prioridade |
|--------|-----------|:----------:|
| 3.1 | **Remover Smallest do fallback automático para pt-BR** — checar `supports_language()` antes de incluir no ranking | 🔴 Alta |
| 3.2 | Na UI, mostrar aviso: "Smallest não suporta português" quando pt-BR estiver selecionado | 🟡 Média |
| 3.3 | Para usuários que falam inglês/hindi, expor `enhancement` (bool), `consistency` (0-1) e `similarity` (0-1) na UI | 🟢 Baixa |
| 3.4 | Usar modelo `lightning-large` como padrão (tem mais parâmetros de qualidade) | 🟢 Baixa |

---

## 4. Gemini API

### 🧠 Diagnóstico

O Gemini tem a vantagem de **detectar idioma automaticamente** — não precisa enviar código de idioma. A qualidade é boa para um modelo gratuito, mas:
- A voz é fixa por `voice_id` (Kore, Puck, etc.)
- Não há controles finos de estabilidade/emoção
- A qualidade depende muito de como o prompt é escrito

### 📋 Especificações da API

```json
{
  "model": "gemini-3.1-flash-tts-preview",
  "input": "Olá, hoje vamos falar sobre tecnologia.",
  "response_format": {"type": "audio"},
  "generation_config": {
    "speech_config": [{"voice": "Kore"}]
  }
}
```

### 🔧 O Que Precisa Ser Feito

| Tarefa | Descrição | Prioridade |
|--------|-----------|:----------:|
| 4.1 | Para português, usar voz `Kore` ou `Puck` (são as mais neutras) | 🟡 Média |
| 4.2 | Adicionar instrução de estilo no input: `"Fale de forma natural em português brasileiro: {texto}"` | 🟡 Média |
| 4.3 | Documentar que Gemini não tem controle fino de voz (stability, etc.) | 🟢 Baixa |
| 4.4 | Tentar `gemini-3.5-flash-tts-preview` se disponível (qualidade potencialmente melhor) | 🟢 Baixa |

---

## 5. Inworld

### 🧠 Diagnóstico

O Inworld tem o modelo **Realtime TTS-2** que suporta **15+ idiomas oficialmente** e **90+ experimentalmente**, incluindo português.

Problemas atuais:
- Não estamos usando `deliveryMode` (default é `BALANCED`, mas `CREATIVE` pode soar mais natural)
- Estamos usando `inworld-tts-2` que é o modelo correto ✅
- As vozes (`Craig`, `Dennis`, etc.) são nativas em inglês — podem ter sotaque em português

A documentação menciona que o TTS-2 tem **cross-lingual voice synthesis** e **voice localization** para som nativo.

### 📋 Especificações da API

```json
{
  "text": "Olá, isto é um teste.",
  "voiceId": "Craig",
  "modelId": "inworld-tts-2",
  "audioConfig": {
    "audioEncoding": "MP3",
    "sampleRateHertz": 48000
  },
  "language": "pt-BR",
  "deliveryMode": "CREATIVE"
}
```

### 🔧 O Que Precisa Ser Feito

| Tarefa | Descrição | Prioridade |
|--------|-----------|:----------:|
| 5.1 | Usar `deliveryMode: "CREATIVE"` para vozes mais naturais em português | 🔴 Alta |
| 5.2 | Testar vozes do Inworld para PT-BR e identificar as que têm melhor sotaque | 🟡 Média |
| 5.3 | Se o sotaque persistir, usar voice localization do TTS-2 (se disponível na conta) | 🟡 Média |
| 5.4 | Expor `deliveryMode` como seletor na UI (STABLE, BALANCED, CREATIVE) | 🟢 Baixa |
| 5.5 | Tentar modelo `inworld-tts-1.5-max` como alternativa (qualidade superior para single-speaker) | 🟢 Baixa |

### 🎯 Vozes a Testar para PT-BR

| Voz | Gênero | Suspeita |
|-----|:------:|----------|
| Craig | Masculino | Pode ter sotaque americano leve |
| Maya | Feminino | Pode ter boa pronúncia multilíngue |
| Serena | Feminino | Boa para testar |
| Patrick | Masculino | Alternativa masculina |

---

## 6. Async Voice API

### 🧠 Diagnóstico

A Async Voice não tem documentação pública clara de API. O que sabemos:
- Endpoint: `POST /v1/tts`
- Parâmetros: `text`, `voice`, `model`, `format`
- Modelos: `async_flash_v1.5`, `async_pro_v1.0`

### 🔧 O Que Precisa Ser Feito

| Tarefa | Descrição | Prioridade |
|--------|-----------|:----------:|
| 6.1 | Investigar documentação real da Async Voice API | 🟡 Média |
| 6.2 | Verificar se suporta `language` e quais idiomas | 🟡 Média |
| 6.3 | Testar com texto em português | 🟡 Média |
| 6.4 | Manter como fallback final (último da fila) | 🟢 Baixa |

---

## 7. Melhorias Transversais (UI e Core)

| ID | Tarefa | Descrição | Prioridade |
|:--:|--------|-----------|:----------:|
| 7.1 | **Slider de Estabilidade** | Expor `stability` (ElevenLabs), `consistency` (Smallest), `deliveryMode` (Inworld) na UI quando o provedor for selecionado | 🟡 Média |
| 7.2 | **Slider de Velocidade** | Expor `speed` para todos os provedores que suportam (range 0.6–1.5) | 🟢 Baixa |
| 7.3 | **Seletor de Emoção** | Para Cartesia, expor dropdown de `emotion` (neutro, feliz, calmo, etc.) | 🟢 Baixa |
| 7.4 | **Preview de Voz** | Implementar preview para Cartesia (gerar áudio de 2s), Smallest, Gemini, Inworld e Async | 🟡 Média |
| 7.5 | **Filtro de Idioma no Ranking** | Garantir que `FallbackEngine.rank_providers()` filtre provedores que não suportam o idioma | 🔴 Alta |
| 7.6 | **Teste Auditivo** | Script para gerar o mesmo texto em todos os provedores e comparar qualidade | 🟡 Média |

---

## 8. Plano de Ação — Ordem de Implementação

```
FASE A — Correções Críticas (agora)
├── A1: Filtrar Smallest para pt-BR (3.1)
├── A2: Corrigir language_code ElevenLabs para ISO 639-1 (1.1)
├── A3: Adicionar voice_settings ElevenLabs (1.2)
├── A4: Adicionar generation_config.emotion Cartesia (2.3)
├── A5: Usar deliveryMode CREATIVE no Inworld (5.1)
├── A6: Filtro de idioma no ranking (7.5)
└── A7: Instrução de estilo no Gemini (4.2)

FASE B — Qualidade de Voz
├── B1: Localizar vozes Cartesia para PT-BR (2.1, 2.2)
├── B2: Testar e selecionar vozes Inworld para PT-BR (5.2)
├── B3: Expor voice settings na UI (1.3, 7.1)
└── B4: Implementar preview de vozes (7.4)

FASE C — Polimento
├── C1: UI de emoção para Cartesia (7.3)
├── C2: Ferramenta de comparação auditiva (7.6)
├── C3: Documentar vozes recomendadas por idioma
└── C4: Investigar Async Voice API (6.1)
```

---

## 9. Resumo das Mudanças no Código

### Arquivos que precisam de alteração:

| Arquivo | Mudança |
|---------|---------|
| `app/providers/elevenlabs.py` | Adicionar `voice_settings` ao payload, revisar `language_code` |
| `app/providers/cartesia.py` | Adicionar `generation_config.emotion`, endpoint de localização |
| `app/providers/smallest.py` | Adicionar verificação rigorosa de idioma |
| `app/providers/gemini.py` | Modificar prompt para incluir instrução de estilo |
| `app/providers/inworld.py` | Adicionar `deliveryMode: "CREATIVE"` |
| `app/core/fallback_engine.py` | Garantir filtro de idioma no ranking |
| `app/ui/pages/_1_generate.py` | Exibir voice settings, sliders, preview |
| `app/tools/` | Nova ferramenta `localize_cartesia.py` |
| `tests/` | Testes para novos parâmetros |
