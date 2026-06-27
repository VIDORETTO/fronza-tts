
![TTS Fallback App](https://img.shields.io/badge/TTS-Fallback%20App-8B5CF6?style=for-the-badge&logo=python&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-003B57?style=for-the-badge&logo=sqlite&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-10B981?style=for-the-badge)

---

<h1 align="center">🎤 TTS Fallback App</h1>

<p align="center">
  <em>Gerencie múltiplas APIs de Text-to-Speech com fallback automático,<br>
  controle inteligente de cotas grátis e zero gastos acidentais.</em>
</p>

<br>

<p align="center">
  <img src="https://img.shields.io/badge/Status-Em%20Produção-22c55e?style=flat-square" alt="Status">
  <img src="https://img.shields.io/badge/Provedores-6-8b5cf6?style=flat-square" alt="Providers">
  <img src="https://img.shields.io/badge/Cobertura%20Testes-20%20testes-22c55e?style=flat-square" alt="Tests">
  <img src="https://img.shields.io/badge/Plataforma-Windows%20%7C%20Linux%20%7C%20macOS-64748b?style=flat-square" alt="Platform">
</p>

---

## 🌟 Sobre o Projeto

**TTS Fallback App** é uma aplicação desktop/web em Python que funciona como uma **camada inteligente** entre você e várias APIs de Text-to-Speech (TTS).

Em vez de você lidar com cada provedor individualmente, o app:

1. **Escolhe o melhor provedor** disponível no momento
2. **Controla cotas grátis** para você nunca gastar dinheiro acidentalmente
3. **Faz fallback automático** quando um provedor atinge o limite
4. **Mostra tudo num painel visual** com Streamlit

> 🎯 **Diferencial:** Não é apenas mais um gerador de TTS. É um **gerenciador inteligente de cotas grátis** que roteia suas requisições para o melhor provedor disponível, evitando surpresas na conta.

---

## 🧠 Como Funciona

```
                    ┌─────────────────────────────┐
                    │     Você digita o texto      │
                    └─────────────┬───────────────┘
                                  ▼
                    ┌─────────────────────────────┐
                    │   App calcula tamanho e      │
                    │   estima consumo              │
                    └─────────────┬───────────────┘
                                  ▼
                    ┌─────────────────────────────┐
                    │   Quota Manager verifica     │
                    │   saldo de cada provedor     │
                    └─────────────┬───────────────┘
                                  ▼
                    ┌─────────────────────────────┐
                    │   Router escolhe o melhor    │
                    │   provedor via pontuação     │
                    └─────────────┬───────────────┘
                                  ▼
                    ┌─────────────────────────────┐
                    │   Provider Adapter chama     │
                    │   a API correta              │
                    └─────────────┬───────────────┘
                                  ▼
                    ┌─────────────────────────────┐
                    │   Áudio salvo + uso          │
                    │   registrado no banco        │
                    └─────────────┬───────────────┘
                                  ▼
                    ┌─────────────────────────────┐
                    │   Painel atualizado —        │
                    │   pronto para o próximo!     │
                    └─────────────────────────────┘
```

### ⚙️ Arquitetura

```
TTS Fallback App
│
├── 🖥️ UI (Streamlit)
│   ├── Gerar Áudio
│   ├── Limites e Cotas
│   ├── Provedores
│   ├── Histórico
│   └── Comparar
│
├── 🧠 Core
│   ├── TTSService          → Orquestrador principal
│   ├── TTSRouter           → Roteamento de provedores
│   ├── FallbackEngine      → Ranking + fallback automático
│   ├── QuotaManager        → Controle inteligente de cotas
│   ├── ResetPolicyEngine   → Políticas de reset (mensal, diário, etc.)
│   ├── TextChunker         → Divisão inteligente de textos longos
│   └── AudioStorage        → Salvamento organizado de áudios
│
├── 🔌 Provider Adapters
│   ├── ElevenLabs          → API real ✅
│   ├── Cartesia            → API real ✅
│   ├── Smallest.ai         → API real ✅
│   ├── Gemini API          → API real ✅
│   ├── Inworld             → API real ✅
│   └── Async Voice API     → API real ✅
│
├── 🗄️ Banco SQLite
│   ├── providers           → Configuração dos provedores
│   ├── api_keys            → Chaves criptografadas
│   ├── quota_snapshots     → Instantâneos de cota
│   ├── manual_balances     → Saldos manuais
│   ├── usage_ledger        → Registro de uso
│   ├── generations         → Histórico de gerações
│   └── fallback_events     → Eventos de fallback
│
└── 📁 Arquivos
    ├── data/audio/         → Áudios gerados
    ├── data/logs/          → Logs estruturados
    └── config.yaml         → Configurações do app
```

---

## 🎯 Provedores Suportados

| # | Provedor | Plano Grátis | Tipo de Cota | Status |
|:-:|----------|:------------:|:------------:|:------:|
| 1 | **ElevenLabs** | ✅ 10K caracteres/mês | `monthly_billing_cycle` | ✅ Funcionando |
| 2 | **Cartesia** | ✅ 20K créditos/mês | `monthly_billing_cycle` | ✅ Funcionando |
| 3 | **Smallest.ai** | ✅ Crédito inicial | `one_time_trial_credit` | ✅ Funcionando |
| 4 | **Gemini API** | ✅ 1500 requisições/dia | `daily_rate_limit` | ✅ Funcionando |
| 5 | **Inworld** | ✅ 60 min/mês (On-Demand) | `monthly_or_on_demand` | ✅ Funcionando |
| 6 | **Async Voice** | ✅ Crédito inicial/plano | `billing_cycle_or_topup` | ✅ Funcionando |

### 🛡️ Tipos de Cota que o App Reconhece

| Tipo | Descrição | Exemplo |
|------|-----------|---------|
| `monthly_billing_cycle` | Reseta todo mês | ElevenLabs, Cartesia |
| `daily_rate_limit` | Reseta por dia | Gemini API |
| `per_minute_rate_limit` | Limite por minuto | Gemini, Cartesia |
| `one_time_trial_credit` | Crédito inicial (não reseta) | Smallest.ai |
| `manual_balance` | Usuário informa o saldo | Async Voice |
| `pay_as_you_go` | Cobra conforme uso | Bloqueado no modo grátis |
| `unknown` | Sem informação confiável | Uso restrito |

> ⚠️ **Regra de ouro:** Se o reset da cota não for confirmado, o app **nunca assume que é mensal**. Isso evita gastos acidentais.

---

## 🚀 Começando

### 📋 Pré-requisitos

| Requisito | Versão |
|-----------|--------|
| **Python** | 3.11 ou superior |
| **pip** | Última versão |
| **FFmpeg** | Opcional (para `pydub`) |

### 📦 Instalação

**1. Clone o repositório**

```bash
git clone https://github.com/seu-usuario/tts-fallback-app.git
cd tts-fallback-app
```

**2. Crie um ambiente virtual (recomendado)**

```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# Linux/macOS
python -m venv .venv
source .venv/bin/activate
```

**3. Instale as dependências**

```bash
pip install -e .
```

**4. Configure as variáveis de ambiente**

```bash
# Copie o arquivo de exemplo
cp .env.example .env

# Edite o .env com suas chaves de API
notepad .env   # Windows
nano .env      # Linux/macOS
```

**5. (Opcional) Configure o app**

```bash
# O config.example.yaml já vem com valores sensíveis
# Copie e edite se necessário:
cp config.example.yaml config.yaml
```

### ▶️ Como Usar

```bash
# Inicie o app
streamlit run app/ui/streamlit_app.py
```

Acesse no navegador: **http://localhost:8501**

#### 🖥️ Telas do App

| Tela | Descrição |
|------|-----------|
| **🎙️ Gerar Áudio** | Digite o texto, escolha idioma/provedor e gere |
| **📊 Limites** | Acompanhe o consumo de cada provedor em tempo real |
| **🔌 Provedores** | Configure chaves de API e teste conexões |
| **📜 Histórico** | Veja e baixe gerações anteriores |
| **⚖️ Comparar** | Teste todos os provedores com o mesmo texto |

### 🛠️ Ferramentas CLI

```bash
# Testar um provedor específico
python -m app.tools.test_provider --provider elevenlabs --text "Olá, mundo!"

# Atualizar cota de um provedor
python -m app.tools.refresh_quota --provider cartesia

# Testar o sistema de fallback completo
python -m app.tools.test_fallback
```

### 🧪 Rodar Testes

```bash
pytest tests/ -v
```

---

## ⚙️ Configuração

### Modos de Operação

O app tem **3 modos** de escolha de provedor:

| Modo | Descrição |
|------|-----------|
| **🛡️ Automático (fallback)** | O app escolhe o melhor provedor com base em pontuação |
| **🔧 Forçar provedor** | Você escolhe manualmente (com alertas de risco) |
| **⚖️ Comparar** | Gera com todos e mostra lado a lado |

### Política de Cotas (Thresholds)

```
0%  ───────────────────────────── 80%  ────── 90% ──── 97% ──── 100%
    │                              │              │       │
    │  ✅ Permitir                  │  ⚠️ Alerta   │       │
    │   sem alerta                  │   visual     │       │
    │                                                │       │
    │                                  🔄 Pular no   │ 🚫    │
    │                                   automático   │Bloq.  │
```

| Threshold | Comportamento |
|:---------:|---------------|
| **80%** | Alerta visual — cota moderada |
| **90%** | Pula este provedor no modo automático |
| **97%** | Bloqueia totalmente |

---

## 🗺️ Estrutura do Projeto

```
📁 tts_fallback_app/
│
├── 📁 app/
│   ├── 📄 main.py                    # Entry point
│   ├── 📁 ui/                       # Interface Streamlit
│   ├── 📁 core/                     # Lógica central
│   ├── 📁 providers/                # Adaptadores de API
│   ├── 📁 db/                       # Banco de dados
│   ├── 📁 schemas/                  # Modelos Pydantic
│   ├── 📁 utils/                    # Utilitários
│   └── 📁 tools/                    # Ferramentas CLI
│
├── 📁 data/                         # Dados locais
│   ├── 🗄️ app.db                   # SQLite
│   ├── 🎵 audio/                   # Áudios gerados
│   └── 📝 logs/                    # Logs do app
│
├── 📁 tests/                        # Testes unitários
├── 📄 config.example.yaml           # Configuração
├── 📄 .env.example                  # Variáveis de ambiente
├── 📄 pyproject.toml                # Dependências
└── 📄 README.md                     # Este arquivo
```

---

## 🔒 Segurança

| Prática | Descrição |
|---------|-----------|
| **🔐 Criptografia** | API keys são criptografadas com Fernet (PBKDF2 + SHA256) antes de salvar no banco |
| **👁️ Máscara** | Chaves nunca são exibidas por completo na interface |
| **🚫 Logs** | Nenhuma chave aparece em logs |
| **📄 .env** | Arquivo .env nunca é versionado |
| **🔑 Rotação** | Botão para remover e trocar chaves a qualquer momento |

---

## 📊 Logs e Observabilidade

O app usa **Loguru** com logs estruturados em JSON:

```json
{
  "event": "tts_generation_started",
  "provider": "cartesia",
  "model": "sonic-3.5",
  "characters": 523,
  "language": "pt-BR"
}
```

Eventos monitorados:
- `tts_generation_started` / `tts_generation_success` / `tts_generation_failed`
- `fallback_triggered` — quando um provedor falha e o fallback é ativado
- `quota_refreshed` — quando a cota é atualizada via API
- `rate_limit_detected` — quando um rate limit é identificado
- `billing_required` — quando um provedor exige cobrança

---

## ❓ FAQ

### Preciso de cartão de crédito?

**Não para o modo grátis.** Todos os provedores oferecem cotas gratuitas que não exigem cartão. O app é configurado para **nunca gastar dinheiro automaticamente**.

### Posso adicionar um novo provedor?

Sim! A arquitetura é extensível:

1. Crie `app/providers/meu_provedor.py`
2. Estenda `ProviderAdapter`
3. Implemente `synthesize()` e `get_quota()`
4. Registre com `registry.register(MeuProvedor())`

### O app funciona offline?

Não totalmente — ele depende de APIs externas para gerar áudio. No entanto, o histórico e as configurações ficam salvos localmente no SQLite.

### Como faço backup?

```bash
# Backup do banco de dados
cp data/app.db data/app.db.backup

# Backup dos áudios
cp -r data/audio data/audio.backup
```

---

## 🧪 Stack Tecnológica

| Tecnologia | Versão | Função |
|-----------|:------:|--------|
| **Python** | ≥ 3.11 | Linguagem principal |
| **Streamlit** | ≥ 1.40 | Interface web |
| **SQLAlchemy** | ≥ 2.0 | ORM do banco |
| **Pydantic** | ≥ 2.0 | Schemas e validação |
| **httpx** | ≥ 0.27 | Cliente HTTP |
| **Loguru** | ≥ 0.7 | Logs estruturados |
| **Tenacity** | ≥ 8.0 | Retry com backoff |
| **Cryptography** | ≥ 42.0 | Criptografia de chaves |
| **Pydub** | ≥ 0.25 | Manipulação de áudio |

---

## 📄 Licença

Este projeto está sob a licença **MIT**. Sinta-se à vontade para usar, modificar e distribuir.

---

## 🙌 Contribuindo

Contribuições são bem-vindas! Sinta-se à vontade para:

1. **Forkar** o projeto
2. Criar uma **branch** com sua feature (`git checkout -b feature/nova-feature`)
3. **Commitar** suas mudanças (`git commit -m 'feat: adiciona nova feature'`)
4. Fazer **push** (`git push origin feature/nova-feature`)
5. Abrir um **Pull Request**

---

<p align="center">
  Feito com ❤️ e ☕ para quem quer TTS sem surpresas na fatura do cartão.
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Feito%20com-Python-3776AB?style=flat-square&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/Mantido%20com-Streamlit-FF4B4B?style=flat-square&logo=streamlit&logoColor=white" alt="Streamlit">
</p>
