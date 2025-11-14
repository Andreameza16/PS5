
	import { createChat } from 'https://cdn.jsdelivr.net/npm/@n8n/chat/dist/chat.bundle.es.js';

	createChat({
	webhookUrl: 'https://andreameza16.app.n8n.cloud/webhook/df6eb8f4-0521-48c7-9e25-7d85385e089b/chat',
	webhookConfig: {
		method: 'POST',
		headers: {}
	},
	target: '#n8n-chat',
	mode: 'window',
	chatInputKey: 'chatInput',
	chatSessionKey: 'sessionId',
	loadPreviousSession: true,
	metadata: {},
	showWelcomeScreen: false,
	defaultLanguage: 'en',
	initialMessages: [
		"🔨 ¡Hola! Soy **Ferretin**, tu asistente de la Ferreteria Watajai.",
      "¿Deseas conocer nuestras promociones?"
	],
	i18n: {
		en: {
			title: 'Ferretin 🔨',
			subtitle: "Asistente Virtual de la Ferreteria Watajai",
			footer: '',
			getStarted: 'New Conversation',
			inputPlaceholder: 'Escribe tu pregunta..',
		},
	},
	enableStreaming: false,
});
