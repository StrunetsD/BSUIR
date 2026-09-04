import { useState, useRef, useEffect } from 'react';
import { Send, BookOpen, Trash2, Download, HelpCircle, X, Sparkles, BookMarked, Users, FileText, Calendar, TrendingUp, Menu } from 'lucide-react';

interface Message {
  id: string;
  text: string;
  sender: 'user' | 'bot';
  timestamp: Date;
}

interface ApiDialogPair {
  id: number;
  user_text: string;
  bot_text: string;
  created_at: string;
}

interface Category {
  id: string;
  name: string;
  icon: React.ReactNode;
  topics: string[];
}

interface QuickTopic {
  text: string;
  question: string;
}

export default function App() {
  const API_BASE = import.meta.env.VITE_API_URL || '/api';
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      text: 'Здравствуйте! Я — литературный помощник. Задайте мне вопросы о русской и зарубежной литературе, авторах, произведениях, жанрах и литературных течениях.',
      sender: 'bot',
      timestamp: new Date(),
    },
  ]);
  const [inputValue, setInputValue] = useState('');
  const [isWaiting, setIsWaiting] = useState(false);
  const [showHelp, setShowHelp] = useState(false);
  const [showSidebar, setShowSidebar] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const categories: Category[] = [
    {
      id: 'authors',
      name: 'Писатели и поэты',
      icon: <Users className="w-5 h-5" />,
      topics: ['Пушкин', 'Толстой', 'Достоевский', 'Чехов', 'Гоголь', 'Шекспир', 'Тургенев', 'Лермонтов'],
    },
    {
      id: 'works',
      name: 'Произведения',
      icon: <BookMarked className="w-5 h-5" />,
      topics: ['Война и мир', 'Преступление и наказание', 'Евгений Онегин', 'Мёртвые души', 'Гроза', 'Гамлет'],
    },
    {
      id: 'genres',
      name: 'Жанры и формы',
      icon: <FileText className="w-5 h-5" />,
      topics: ['Роман', 'Повесть', 'Рассказ', 'Поэма', 'Трагедия', 'Комедия', 'Сонет'],
    },
    {
      id: 'periods',
      name: 'Периоды и течения',
      icon: <Calendar className="w-5 h-5" />,
      topics: ['Романтизм', 'Реализм', 'Серебряный век', 'Классицизм', 'Модернизм', 'Символизм'],
    },
  ];

  const quickTopics: QuickTopic[] = [
    { text: '🎭 Золотой век', question: 'Расскажи о золотом веке русской литературы' },
    { text: '📖 Анализ романа', question: 'Как анализировать литературное произведение?' },
    { text: '✍️ Литературные приёмы', question: 'Какие литературные приёмы существуют?' },
    { text: '🌟 Нобелевские лауреаты', question: 'Какие русские писатели получили Нобелевскую премию?' },
  ];

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    const loadHistory = async () => {
      try {
        const response = await fetch(`${API_BASE}/messages?limit=100`);
        if (!response.ok) {
          return;
        }
        const data: ApiDialogPair[] = await response.json();
        if (!Array.isArray(data) || data.length === 0) {
          return;
        }

        const restored: Message[] = [];
        data
          .slice()
          .reverse()
          .forEach((item) => {
            const stamp = new Date(item.created_at);
            restored.push({
              id: `${item.id}-u`,
              text: item.user_text,
              sender: 'user',
              timestamp: stamp,
            });
            restored.push({
              id: `${item.id}-b`,
              text: item.bot_text,
              sender: 'bot',
              timestamp: stamp,
            });
          });

        setMessages(restored);
      } catch (_error) {
        // Fallback to local in-memory chat if API unavailable.
      }
    };

    loadHistory();
  }, [API_BASE]);

  useEffect(() => {
    const handleResize = () => {
      if (window.innerWidth >= 1024) {
        setShowSidebar(true);
      } else {
        setShowSidebar(false);
      }
    };

    handleResize();
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  const handleSend = async (customMessage?: string) => {
    const messageText = customMessage || inputValue;
    if (!messageText.trim() || isWaiting) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      text: messageText,
      sender: 'user',
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInputValue('');
    setIsWaiting(true);

    try {
      const response = await fetch(`${API_BASE}/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ message: messageText }),
      });

      if (!response.ok) {
        throw new Error('API request failed');
      }

      const payload = await response.json();
      const botResponse: Message = {
        id: (Date.now() + 1).toString(),
        text: payload.bot_text || 'Не удалось получить ответ от модели. Попробуйте ещё раз.',
        sender: 'bot',
        timestamp: payload.created_at ? new Date(payload.created_at) : new Date(),
      };
      setMessages((prev) => [...prev, botResponse]);
    } catch (_error) {
      const botResponse: Message = {
        id: (Date.now() + 1).toString(),
        text: 'Ошибка связи с моделью. Проверьте, что backend и ollama запущены, затем повторите запрос.',
        sender: 'bot',
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, botResponse]);
    } finally {
      setIsWaiting(false);
    }
  };

  const handleQuickTopic = (question: string) => {
    handleSend(question);
    if (window.innerWidth < 1024) {
      setShowSidebar(false);
    }
  };

  const handleTopicClick = (topic: string) => {
    handleSend(`Расскажи о ${topic}`);
  };

  const handleClearHistory = async () => {
    if (window.confirm('Вы уверены, что хотите очистить историю диалога?')) {
      try {
        await fetch(`${API_BASE}/messages/clear`, { method: 'POST' });
      } catch (_error) {
        // Keep UI responsive even if API unavailable.
      }
      setMessages([
        {
          id: Date.now().toString(),
          text: 'История диалога очищена. Чем могу помочь?',
          sender: 'bot',
          timestamp: new Date(),
        },
      ]);
    }
  };

  const handleExportHistory = () => {
    const historyText = messages
      .map((msg) => {
        const time = msg.timestamp.toLocaleTimeString('ru-RU', {
          hour: '2-digit',
          minute: '2-digit',
        });
        const sender = msg.sender === 'user' ? 'Вы' : 'Система';
        return `[${time}] ${sender}: ${msg.text}`;
      })
      .join('\n\n');

    const blob = new Blob([historyText], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `литературный_диалог_${new Date().toLocaleDateString('ru-RU')}.txt`;
    link.click();
    URL.revokeObjectURL(url);
  };

  const userMessagesCount = messages.filter((m) => m.sender === 'user').length;
  const botMessagesCount = messages.filter((m) => m.sender === 'bot').length;

  return (
    <div className="size-full flex items-center justify-center bg-gradient-to-br from-amber-50 via-orange-50 to-red-50 sm:p-4">
      <div className="w-full h-full sm:h-[90vh] sm:max-w-7xl bg-white sm:rounded-2xl shadow-2xl flex overflow-hidden border-0 sm:border border-amber-200 relative">
        {/* Sidebar Overlay (Mobile) */}
        {showSidebar && (
          <div
            className="fixed inset-0 bg-black/50 z-40 lg:hidden"
            onClick={() => setShowSidebar(false)}
          />
        )}

        {/* Sidebar */}
        {showSidebar && (
          <div className="fixed lg:relative top-0 left-0 h-full w-80 bg-gradient-to-b from-amber-50 to-orange-50 border-r-2 border-amber-200 flex flex-col z-50 lg:z-auto shadow-2xl lg:shadow-none">
            <div className="p-4 border-b-2 border-amber-200 bg-white/50 flex items-center justify-between">
              <h2 className="font-bold text-lg text-amber-900 flex items-center gap-2">
                <BookMarked className="w-5 h-5" />
                Категории
              </h2>
              <button
                onClick={() => setShowSidebar(false)}
                className="lg:hidden p-2 hover:bg-amber-200 rounded-lg transition-colors"
              >
                <X className="w-5 h-5 text-amber-900" />
              </button>
            </div>

            <div className="flex-1 overflow-y-auto p-3 sm:p-4 space-y-3 sm:space-y-4">
              {categories.map((category) => (
                <div key={category.id} className="bg-white rounded-xl p-3 sm:p-4 shadow-md border border-amber-200">
                  <div className="flex items-center gap-2 mb-2.5 sm:mb-3 text-amber-900 font-semibold text-sm sm:text-base">
                    {category.icon}
                    <span>{category.name}</span>
                  </div>
                  <div className="flex flex-wrap gap-1.5 sm:gap-2">
                    {category.topics.map((topic) => (
                      <button
                        key={topic}
                        onClick={() => {
                          handleTopicClick(topic);
                          setShowSidebar(false);
                        }}
                        className="px-2.5 sm:px-3 py-1 sm:py-1.5 text-xs sm:text-sm bg-amber-100 hover:bg-amber-200 text-amber-900 rounded-lg transition-colors border border-amber-300"
                      >
                        {topic}
                      </button>
                    ))}
                  </div>
                </div>
              ))}
            </div>

            {/* Statistics */}
            <div className="p-3 sm:p-4 border-t-2 border-amber-200 bg-white/70">
              <h3 className="text-xs sm:text-sm font-semibold text-amber-900 mb-2 sm:mb-3 flex items-center gap-2">
                <TrendingUp className="w-4 h-4" />
                Статистика диалога
              </h3>
              <div className="space-y-1.5 sm:space-y-2 text-xs sm:text-sm text-gray-700">
                <div className="flex justify-between">
                  <span>Ваши вопросы:</span>
                  <span className="font-bold text-amber-700">{userMessagesCount}</span>
                </div>
                <div className="flex justify-between">
                  <span>Ответы системы:</span>
                  <span className="font-bold text-amber-700">{botMessagesCount}</span>
                </div>
                <div className="flex justify-between">
                  <span>Всего сообщений:</span>
                  <span className="font-bold text-amber-700">{messages.length}</span>
                </div>
              </div>

              {/* Export button for mobile */}
              <button
                onClick={() => {
                  handleExportHistory();
                  setShowSidebar(false);
                }}
                className="w-full mt-3 sm:hidden px-4 py-2.5 bg-gradient-to-r from-amber-600 to-orange-600 text-white rounded-lg hover:from-amber-700 hover:to-orange-700 transition-all shadow-md flex items-center justify-center gap-2 font-medium text-sm"
              >
                <Download className="w-4 h-4" />
                Экспорт истории
              </button>
            </div>
          </div>
        )}

        {/* Main Content */}
        <div className="flex-1 flex flex-col">
          {/* Header */}
          <div className="bg-gradient-to-r from-amber-700 via-orange-700 to-red-700 text-white p-3 sm:p-6 flex items-center justify-between">
            <div className="flex items-center gap-2 sm:gap-4">
              <button
                onClick={() => setShowSidebar(!showSidebar)}
                className="p-2 hover:bg-white/20 rounded-lg transition-colors"
                title={showSidebar ? 'Скрыть панель' : 'Показать панель'}
              >
                <Menu className="w-5 h-5 sm:w-6 sm:h-6" />
              </button>
              <div className="bg-white/20 p-2 sm:p-3 rounded-xl backdrop-blur-sm">
                <BookOpen className="w-6 h-6 sm:w-8 sm:h-8" />
              </div>
              <div>
                <h1 className="text-lg sm:text-2xl font-bold">Литературный помощник</h1>
                <p className="text-xs sm:text-sm text-amber-100 mt-0.5 sm:mt-1 hidden sm:block">
                  Диалоговая система по русской и зарубежной литературе
                </p>
              </div>
            </div>
            <div className="flex gap-1 sm:gap-2">
              <button
                onClick={() => setShowHelp(true)}
                className="p-2 sm:p-2.5 hover:bg-white/20 rounded-lg transition-colors"
                title="Помощь"
              >
                <HelpCircle className="w-5 h-5 sm:w-6 sm:h-6" />
              </button>
              <button
                onClick={handleExportHistory}
                className="p-2 sm:p-2.5 hover:bg-white/20 rounded-lg transition-colors hidden sm:block"
                title="Экспорт истории"
              >
                <Download className="w-5 h-5 sm:w-6 sm:h-6" />
              </button>
              <button
                onClick={handleClearHistory}
                className="p-2 sm:p-2.5 hover:bg-white/20 rounded-lg transition-colors"
                title="Очистить историю"
              >
                <Trash2 className="w-5 h-5 sm:w-6 sm:h-6" />
              </button>
            </div>
          </div>

          {/* Quick Topics */}
          {messages.length === 1 && (
            <div className="p-3 sm:p-4 bg-amber-50/50 border-b border-amber-200">
              <h3 className="text-xs sm:text-sm font-semibold text-amber-900 mb-2 sm:mb-3">Быстрые темы:</h3>
              <div className="flex flex-wrap gap-2">
                {quickTopics.map((topic, index) => (
                  <button
                    key={index}
                    onClick={() => handleQuickTopic(topic.question)}
                    className="px-3 sm:px-4 py-1.5 sm:py-2 bg-white hover:bg-amber-100 text-amber-900 rounded-lg border border-amber-300 transition-colors shadow-sm hover:shadow-md text-xs sm:text-sm"
                  >
                    {topic.text}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Messages Area */}
          <div className="flex-1 overflow-y-auto p-3 sm:p-6 space-y-3 sm:space-y-4 bg-gradient-to-b from-white to-amber-50/30">
            {messages.map((message) => (
              <div
                key={message.id}
                className={`flex ${message.sender === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                <div
                  className={`max-w-[85%] sm:max-w-[70%] rounded-2xl px-4 sm:px-5 py-2.5 sm:py-3 ${
                    message.sender === 'user'
                      ? 'bg-gradient-to-r from-amber-600 to-orange-600 text-white shadow-lg'
                      : 'bg-white border-2 border-amber-200 text-gray-800 shadow-md'
                  }`}
                >
                  {message.sender === 'bot' && (
                    <div className="flex items-center gap-2 mb-2 text-amber-700">
                      <Sparkles className="w-3.5 h-3.5 sm:w-4 sm:h-4" />
                      <span className="text-xs font-semibold">Литературный помощник</span>
                    </div>
                  )}
                  <p className="whitespace-pre-line leading-relaxed text-sm sm:text-base">{message.text}</p>
                  <p
                    className={`text-xs mt-1.5 sm:mt-2 ${
                      message.sender === 'user' ? 'text-amber-100' : 'text-gray-500'
                    }`}
                  >
                    {message.timestamp.toLocaleTimeString('ru-RU', {
                      hour: '2-digit',
                      minute: '2-digit',
                    })}
                  </p>
                </div>
              </div>
            ))}
            {isWaiting && (
              <div className="flex justify-start">
                <div className="max-w-[85%] sm:max-w-[70%] rounded-2xl px-4 sm:px-5 py-2.5 sm:py-3 bg-white border-2 border-amber-200 text-gray-800 shadow-md">
                  <div className="flex items-center gap-2 mb-2 text-amber-700">
                    <Sparkles className="w-3.5 h-3.5 sm:w-4 sm:h-4" />
                    <span className="text-xs font-semibold">Литературный помощник</span>
                  </div>
                  <p className="text-sm sm:text-base">Думаю над ответом...</p>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Input Area */}
          <div className="border-t-2 border-amber-200 p-3 sm:p-4 bg-white">
            <div className="flex gap-2 sm:gap-3">
              <input
                type="text"
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && handleSend()}
                placeholder={isWaiting ? 'Ожидайте ответ модели...' : 'Задайте вопрос о литературе...'}
                disabled={isWaiting}
                className="flex-1 px-3 sm:px-5 py-2.5 sm:py-3.5 text-sm sm:text-base border-2 border-amber-300 rounded-xl focus:outline-none focus:border-amber-500 focus:ring-2 focus:ring-amber-200 transition-all"
              />
              <button
                onClick={() => handleSend()}
                disabled={!inputValue.trim() || isWaiting}
                className="px-4 sm:px-6 py-2.5 sm:py-3.5 bg-gradient-to-r from-amber-600 to-orange-600 text-white rounded-xl hover:from-amber-700 hover:to-orange-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all shadow-lg hover:shadow-xl flex items-center gap-2 font-medium text-sm sm:text-base"
              >
                <Send className="w-4 h-4 sm:w-5 sm:h-5" />
                <span className="hidden sm:inline">{isWaiting ? 'Думаю...' : 'Отправить'}</span>
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Help Modal */}
      {showHelp && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-2 sm:p-4 z-50 backdrop-blur-sm">
          <div className="bg-white rounded-xl sm:rounded-2xl shadow-2xl max-w-2xl w-full max-h-[90vh] sm:max-h-[80vh] overflow-y-auto">
            <div className="sticky top-0 bg-gradient-to-r from-amber-700 to-orange-700 text-white p-4 sm:p-6 flex items-center justify-between rounded-t-xl sm:rounded-t-2xl">
              <div className="flex items-center gap-2 sm:gap-3">
                <HelpCircle className="w-6 h-6 sm:w-7 sm:h-7" />
                <h2 className="text-xl sm:text-2xl font-bold">Справка</h2>
              </div>
              <button
                onClick={() => setShowHelp(false)}
                className="p-2 hover:bg-white/20 rounded-lg transition-colors"
              >
                <X className="w-5 h-5 sm:w-6 sm:h-6" />
              </button>
            </div>
            <div className="p-4 sm:p-6 space-y-4 sm:space-y-6">
              <section>
                <h3 className="text-base sm:text-lg font-bold text-amber-900 mb-2 sm:mb-3">Возможности системы</h3>
                <ul className="space-y-2 text-sm sm:text-base text-gray-700">
                  <li className="flex items-start gap-2">
                    <span className="text-amber-600 font-bold">•</span>
                    <span>Информация о русских и зарубежных писателях и поэтах</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-amber-600 font-bold">•</span>
                    <span>Анализ литературных произведений, их сюжетов и героев</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-amber-600 font-bold">•</span>
                    <span>Объяснение литературных жанров и направлений</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-amber-600 font-bold">•</span>
                    <span>Информация об историко-литературных эпохах</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-amber-600 font-bold">•</span>
                    <span>Сохранение и экспорт истории диалога</span>
                  </li>
                </ul>
              </section>

              <section>
                <h3 className="text-base sm:text-lg font-bold text-amber-900 mb-2 sm:mb-3">Примеры вопросов</h3>
                <div className="space-y-2">
                  <div className="bg-amber-50 p-2.5 sm:p-3 rounded-lg border border-amber-200">
                    <p className="text-xs sm:text-sm text-gray-700">
                      "Расскажи о творчестве Пушкина"
                    </p>
                  </div>
                  <div className="bg-amber-50 p-2.5 sm:p-3 rounded-lg border border-amber-200">
                    <p className="text-xs sm:text-sm text-gray-700">
                      "Что такое романтизм в литературе?"
                    </p>
                  </div>
                  <div className="bg-amber-50 p-2.5 sm:p-3 rounded-lg border border-amber-200">
                    <p className="text-xs sm:text-sm text-gray-700">
                      "Кто такие поэты серебряного века?"
                    </p>
                  </div>
                  <div className="bg-amber-50 p-2.5 sm:p-3 rounded-lg border border-amber-200">
                    <p className="text-xs sm:text-sm text-gray-700">
                      "Расскажи о романе 'Война и мир'"
                    </p>
                  </div>
                </div>
              </section>

              <section>
                <h3 className="text-base sm:text-lg font-bold text-amber-900 mb-2 sm:mb-3">Управление</h3>
                <ul className="space-y-2 text-sm sm:text-base text-gray-700">
                  <li className="flex items-center gap-2 sm:gap-3">
                    <Download className="w-4 h-4 sm:w-5 sm:h-5 text-amber-600 flex-shrink-0" />
                    <span><strong>Экспорт истории</strong> — сохранить диалог в текстовый файл</span>
                  </li>
                  <li className="flex items-center gap-2 sm:gap-3">
                    <Trash2 className="w-4 h-4 sm:w-5 sm:h-5 text-amber-600 flex-shrink-0" />
                    <span><strong>Очистить историю</strong> — удалить все сообщения</span>
                  </li>
                  <li className="flex items-center gap-2 sm:gap-3">
                    <HelpCircle className="w-4 h-4 sm:w-5 sm:h-5 text-amber-600 flex-shrink-0" />
                    <span><strong>Помощь</strong> — открыть это окно справки</span>
                  </li>
                </ul>
              </section>

              <section className="bg-gradient-to-r from-amber-100 to-orange-100 p-3 sm:p-4 rounded-lg border-2 border-amber-300">
                <h3 className="text-base sm:text-lg font-bold text-amber-900 mb-2">О системе</h3>
                <p className="text-xs sm:text-sm text-gray-700">
                  Диалоговая система с поддержкой естественного языка для изучения
                  русской и зарубежной литературы. Разработана в рамках лабораторной
                  работы №6 по предметной области "Литература".
                </p>
              </section>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
