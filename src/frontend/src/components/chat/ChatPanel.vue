<template>
  <div class="chat-panel">
    <div class="messages" ref="messagesEl">
      <div v-if="messages.length === 0" class="empty-state">
        <p>Stel een vraag over de ruimtelijke data van Nederland.</p>
        <div class="examples">
          <button v-for="ex in examples" :key="ex" @click="sendQuestion(ex)">
            {{ ex }}
          </button>
        </div>
      </div>

      <div v-for="(msg, i) in messages" :key="i" :class="['message', msg.role]">
        <!-- User -->
        <div v-if="msg.role === 'user'" class="bubble">{{ msg.content }}</div>

        <!-- Assistant -->
        <div v-else class="assistant-msg">
          <!-- Tool calls -->
          <div v-for="(step, j) in msg.steps" :key="j" class="step">
            <div v-if="step.type === 'tool_call'" class="tool-call">
              <span class="tool-icon">⚙</span>
              <span class="tool-name">{{ step.name }}</span>
              <span class="tool-args">{{ formatArgs(step.args) }}</span>
            </div>
            <div v-if="step.type === 'tool_result'" class="tool-result">
              <pre>{{ step.content }}</pre>
            </div>
            <div v-if="step.type === 'thinking' && step.content" class="thinking">
              {{ step.content }}
            </div>
          </div>

          <!-- Final response -->
          <div v-if="msg.content" class="bubble assistant">{{ msg.content }}</div>

          <!-- Loading indicator -->
          <div v-if="msg.loading" class="loading">
            <span></span><span></span><span></span>
          </div>
        </div>
      </div>
    </div>

    <div class="input-row">
      <input
        v-model="input"
        @keydown.enter="sendQuestion(input)"
        :disabled="loading"
        placeholder="Stel een vraag over Nederland..."
        class="chat-input"
      />
      <button @click="sendQuestion(input)" :disabled="loading || !input.trim()" class="send-btn">
        {{ loading ? '...' : '→' }}
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, nextTick, defineEmits } from 'vue'

const emit = defineEmits<{
  highlight: [h3_ids: string[], label: string]
}>()

const API = 'http://localhost:8002/api'

const input = ref('')
const loading = ref(false)
const messages = ref<any[]>([])
const messagesEl = ref<HTMLElement>()

const examples = [
  'Welke gebieden in Nederland hebben de hoogste hittestress?',
  'Vergelijk Amsterdam en Rotterdam qua sociale huurwoningen',
  'Waar is de vergrijzing het sterkst?',
  'Welke clusters zijn het meest in beweging tussen 2018 en 2023?',
]

// Conversation history for context
const history = ref<{ role: string; content: string }[]>([])

async function sendQuestion(question: string) {
  if (!question.trim() || loading.value) return
  input.value = ''
  loading.value = true

  // Add user message
  messages.value.push({ role: 'user', content: question })

  // Add placeholder assistant message
  const assistantMsg = { role: 'assistant', content: '', steps: [], loading: true }
  messages.value.push(assistantMsg)

  await scrollToBottom()

  try {
    const response = await fetch(`${API}/agent/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question, history: history.value }),
    })

    const reader = response.body!.getReader()
    const decoder = new TextDecoder()

    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      const chunk = decoder.decode(value)
      const lines = chunk.split('\n').filter(l => l.startsWith('data: '))

      for (const line of lines) {
        const event = JSON.parse(line.slice(6))

        if (event.type === 'tool_call') {
          assistantMsg.steps.push({ type: 'tool_call', name: event.name, args: event.args })
        } else if (event.type === 'tool_result') {
          assistantMsg.steps.push({ type: 'tool_result', content: event.content })
        } else if (event.type === 'thinking' && event.content) {
          assistantMsg.steps.push({ type: 'thinking', content: event.content })
        } else if (event.type === 'response') {
          assistantMsg.content = event.content
          assistantMsg.loading = false
        } else if (event.type === 'highlight') {
          emit('highlight', event.h3_ids, event.label)
          assistantMsg.steps.push({ type: 'tool_result', content: `📍 ${event.h3_ids.length} gebieden gemarkeerd op de kaart: "${event.label}"` })
        } else if (event.type === 'error') {
          assistantMsg.content = `Fout: ${event.content}`
          assistantMsg.loading = false
        } else if (event.type === 'done') {
          assistantMsg.loading = false
        }

        await scrollToBottom()
      }
    }
  } catch (e: any) {
    assistantMsg.content = `Verbindingsfout: ${e.message}`
    assistantMsg.loading = false
  }

  // Update history for context
  history.value.push({ role: 'user', content: question })
  history.value.push({ role: 'assistant', content: assistantMsg.content })

  loading.value = false
}

function formatArgs(args: any): string {
  if (!args) return ''
  const vals = Object.entries(args)
    .map(([k, v]) => `${k}: ${JSON.stringify(v)}`)
    .join(', ')
  return vals.length > 80 ? vals.slice(0, 80) + '…' : vals
}

async function scrollToBottom() {
  await nextTick()
  if (messagesEl.value) {
    messagesEl.value.scrollTop = messagesEl.value.scrollHeight
  }
}
</script>

<style scoped>
.chat-panel {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: #0d0d1a;
  color: #eee;
  font-size: 0.82rem;
}

.messages {
  flex: 1;
  overflow-y: auto;
  padding: 1rem;
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.empty-state {
  color: #666;
  text-align: center;
  margin-top: 2rem;
}

.examples {
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
  margin-top: 1rem;
}

.examples button {
  background: #1a1a2e;
  border: 1px solid #333;
  color: #aaa;
  padding: 0.4rem 0.6rem;
  border-radius: 4px;
  cursor: pointer;
  text-align: left;
  font-size: 0.78rem;
  line-height: 1.4;
}

.examples button:hover {
  border-color: #a8d8ea;
  color: #eee;
}

.message.user {
  display: flex;
  justify-content: flex-end;
}

.bubble {
  background: #1a1a2e;
  border: 1px solid #333;
  border-radius: 8px;
  padding: 0.6rem 0.8rem;
  max-width: 90%;
  line-height: 1.5;
  white-space: pre-wrap;
}

.bubble.assistant {
  background: #0f3460;
  border-color: #1a4a7a;
  max-width: 100%;
}

.assistant-msg {
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
}

.step {
  display: flex;
  flex-direction: column;
  gap: 0.2rem;
}

.tool-call {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  background: #1a2a1a;
  border: 1px solid #2a4a2a;
  border-radius: 4px;
  padding: 0.3rem 0.5rem;
  font-family: monospace;
  font-size: 0.75rem;
  color: #8bc98b;
}

.tool-icon { font-size: 0.7rem; }
.tool-name { font-weight: 600; }
.tool-args { color: #666; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }

.tool-result {
  background: #111;
  border: 1px solid #222;
  border-radius: 4px;
  padding: 0.4rem 0.6rem;
  max-height: 150px;
  overflow-y: auto;
}

.tool-result pre {
  margin: 0;
  font-family: monospace;
  font-size: 0.72rem;
  color: #999;
  white-space: pre-wrap;
}

.thinking {
  color: #666;
  font-style: italic;
  font-size: 0.78rem;
  padding: 0 0.2rem;
}

.loading {
  display: flex;
  gap: 4px;
  padding: 0.4rem;
}

.loading span {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #a8d8ea;
  animation: bounce 1s infinite;
}

.loading span:nth-child(2) { animation-delay: 0.2s; }
.loading span:nth-child(3) { animation-delay: 0.4s; }

@keyframes bounce {
  0%, 100% { opacity: 0.3; transform: translateY(0); }
  50% { opacity: 1; transform: translateY(-4px); }
}

.input-row {
  display: flex;
  gap: 0.5rem;
  padding: 0.75rem;
  border-top: 1px solid #222;
}

.chat-input {
  flex: 1;
  background: #1a1a2e;
  border: 1px solid #333;
  color: #eee;
  padding: 0.5rem 0.75rem;
  border-radius: 6px;
  font-size: 0.82rem;
  outline: none;
}

.chat-input:focus { border-color: #a8d8ea; }

.send-btn {
  background: #a8d8ea;
  color: #1a1a2e;
  border: none;
  border-radius: 6px;
  padding: 0.5rem 1rem;
  font-weight: 700;
  cursor: pointer;
  font-size: 1rem;
}

.send-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}
</style>
