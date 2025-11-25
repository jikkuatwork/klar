/**
 * Klar - Chat Page
 * Placeholder for AI chat integration
 */

(function() {
  function render(container) {
    container.innerHTML = `
      <div class="h-full flex flex-col">
        <!-- Chat Messages -->
        <div class="flex-1 overflow-y-auto p-4">
          <div class="max-w-2xl mx-auto">
            <!-- Welcome Message -->
            <div class="text-center py-12">
              <div class="w-16 h-16 mx-auto mb-4 rounded-full bg-primary/10 flex items-center justify-center">
                <i data-feather="message-circle" class="w-8 h-8 text-primary"></i>
              </div>
              <h2 class="text-xl font-semibold mb-2">AI Assistant</h2>
              <p class="text-secondary/60 dark:text-white/60 mb-6">
                Ask questions about your investor data in natural language
              </p>

              <div class="space-y-2 text-sm">
                <p class="text-secondary/40 dark:text-white/40">Example queries:</p>
                <div class="flex flex-wrap justify-center gap-2">
                  <button class="badge hover:bg-primary/20 cursor-pointer" data-query="Show me family offices in the US">
                    Family offices in the US
                  </button>
                  <button class="badge hover:bg-primary/20 cursor-pointer" data-query="Which funds have over $1B AUM?">
                    Funds with >$1B AUM
                  </button>
                  <button class="badge hover:bg-primary/20 cursor-pointer" data-query="Find investors focused on fintech">
                    Fintech investors
                  </button>
                </div>
              </div>

              <div class="mt-8 p-4 bg-secondary/5 dark:bg-white/5 rounded-lg">
                <p class="text-sm text-secondary/60 dark:text-white/60">
                  <i data-feather="info" class="w-4 h-4 inline mr-1"></i>
                  AI chat integration coming soon. This will use Gemini 2.5 Pro to answer questions about your investor data.
                </p>
              </div>
            </div>
          </div>
        </div>

        <!-- Chat Input -->
        <div class="flex-shrink-0 border-t border-secondary/10 dark:border-white/10 p-4">
          <div class="max-w-2xl mx-auto">
            <div class="flex gap-2">
              <input
                type="text"
                class="input flex-1"
                placeholder="Ask about your investor data..."
                disabled
              >
              <button class="btn btn-primary" disabled>
                <i data-feather="send" class="w-4 h-4"></i>
              </button>
            </div>
          </div>
        </div>
      </div>
    `;

    // Example query clicks
    $$('[data-query]', container).forEach(btn => {
      btn.addEventListener('click', () => {
        Toast.info('AI chat coming soon');
      });
    });

    // Update feather icons
    if (window.feather) {
      feather.replace();
    }
  }

  // Register page
  Router.registerPage('chat', render);
})();
