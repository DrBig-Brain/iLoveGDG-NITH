document.addEventListener('DOMContentLoaded', () => {
  const API_BASE = window.location.origin;

  // DOM Elements
  const statusBadge = document.getElementById('statusBadge');
  const statusText = document.getElementById('statusText');
  const apiKeyInput = document.getElementById('apiKey');
  const promptInput = document.getElementById('promptInput');
  const btnQuickKey = document.getElementById('btnQuickKey');
  const btnNewKey = document.getElementById('btnNewKey');
  const btnRoute = document.getElementById('btnRoute');
  const spinner = document.getElementById('spinner');
  const errorBox = document.getElementById('errorBox');
  const presetChips = document.querySelectorAll('.preset-chip');

  // Results DOM Elements
  const emptyState = document.getElementById('emptyState');
  const resultsView = document.getElementById('resultsView');
  const categoryBadge = document.getElementById('categoryBadge');
  const selectedModelId = document.getElementById('selectedModelId');
  const tierBadge = document.getElementById('tierBadge');
  const modelProvider = document.getElementById('modelProvider');
  const costInput = document.getElementById('costInput');
  const costOutput = document.getElementById('costOutput');
  const routingReasonText = document.getElementById('routingReasonText');
  const metricComplexity = document.getElementById('metricComplexity');
  const fillComplexity = document.getElementById('fillComplexity');
  const metricTaskType = document.getElementById('metricTaskType');
  const metricReasoning = document.getElementById('metricReasoning');
  const fillReasoning = document.getElementById('fillReasoning');
  const metricCreativity = document.getElementById('metricCreativity');
  const fillCreativity = document.getElementById('fillCreativity');
  const simulatedReply = document.getElementById('simulatedReply');
  const forwardedPayloadCode = document.getElementById('forwardedPayloadCode');

  // Modal DOM Elements
  const keyModal = document.getElementById('keyModal');
  const btnCloseModal = document.getElementById('btnCloseModal');
  const btnCancelModal = document.getElementById('btnCancelModal');
  const btnConfirmNewKey = document.getElementById('btnConfirmNewKey');
  const newClientName = document.getElementById('newClientName');
  const newTier = document.getElementById('newTier');
  const newKeyResult = document.getElementById('newKeyResult');
  const newKeyDisplay = document.getElementById('newKeyDisplay');

  // 1. Health Check
  async function checkGatewayHealth() {
    try {
      const res = await fetch(`${API_BASE}/health`);
      if (res.ok) {
        statusBadge.className = 'status-pill status-online';
        statusText.textContent = 'Gateway Online';
      } else {
        throw new Error();
      }
    } catch {
      statusBadge.className = 'status-pill status-offline';
      statusText.textContent = 'Gateway Offline';
    }
  }

  checkGatewayHealth();

  // 2. Preset Click Handlers
  presetChips.forEach(chip => {
    chip.addEventListener('click', () => {
      promptInput.value = chip.getAttribute('data-prompt');
      promptInput.focus();
    });
  });

  // 3. Use Demo Key
  btnQuickKey.addEventListener('click', () => {
    apiKeyInput.value = 'gdg-test-key-2026';
    hideError();
  });

  // 4. Route Prompt
  btnRoute.addEventListener('click', handleRoutePrompt);

  async function handleRoutePrompt() {
    const key = apiKeyInput.value.trim();
    const prompt = promptInput.value.trim();

    hideError();

    if (!key) {
      showError('Please enter an API Key to authenticate with the middleware.');
      return;
    }
    if (!prompt) {
      showError('Please enter a prompt to analyze.');
      return;
    }

    setLoading(true);

    try {
      const res = await fetch(`${API_BASE}/v1/route`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-API-Key': key,
        },
        body: JSON.stringify({ prompt }),
      });

      const data = await res.json();

      if (!res.ok) {
        throw new Error(data.detail || data.message || 'Routing request failed.');
      }

      renderResults(data);
    } catch (err) {
      showError(err.message);
    } finally {
      setLoading(false);
    }
  }

  function renderResults(data) {
    emptyState.classList.add('hidden');
    resultsView.classList.remove('hidden');

    const routing = data.routing_decision || {};
    const metrics = data.classifier_metrics || {};

    // Category Badge
    categoryBadge.textContent = routing.category || 'Processed';

    // Model Hero Card
    selectedModelId.textContent = routing.selected_llm || 'Unknown Model';
    modelProvider.textContent = routing.provider || 'AI Provider';
    tierBadge.textContent = routing.tier || 'Tier 1';

    // Adjust tier styling
    tierBadge.className = 'tier-badge';
    if (routing.tier?.includes('Tier 3') || routing.tier?.includes('Frontier')) {
      tierBadge.classList.add('tier-frontier');
    } else if (routing.tier?.includes('Tier 2') || routing.tier?.includes('Balanced')) {
      tierBadge.classList.add('tier-balanced');
    }

    // Costs
    costInput.textContent = routing.cost_profile?.input_per_million ? `${routing.cost_profile.input_per_million} / 1M` : 'N/A';
    costOutput.textContent = routing.cost_profile?.output_per_million ? `${routing.cost_profile.output_per_million} / 1M` : 'N/A';

    // Rationale
    routingReasonText.textContent = routing.routing_reason || 'Selected based on classifier evaluation.';

    // Metrics
    const compScore = metrics.complexity_score !== undefined ? Number(metrics.complexity_score) : 0;
    const reasoningScore = metrics.reasoning_score !== undefined ? Number(metrics.reasoning_score) : 0;
    const creativityScore = metrics.creativity_score !== undefined ? Number(metrics.creativity_score) : 0;

    metricComplexity.textContent = compScore.toFixed(3);
    fillComplexity.style.width = `${Math.min(100, Math.max(8, compScore * 250))}%`;
    if (compScore < 0.15) {
      fillComplexity.style.backgroundColor = '#10b981'; // Green (Low)
    } else if (compScore < 0.28) {
      fillComplexity.style.backgroundColor = '#3b82f6'; // Blue (Medium)
    } else {
      fillComplexity.style.backgroundColor = '#a855f7'; // Purple (High)
    }

    metricTaskType.textContent = metrics.task_type || 'General QA';
    metricReasoning.textContent = reasoningScore.toFixed(3);
    fillReasoning.style.width = `${Math.min(100, Math.max(5, reasoningScore * 100))}%`;

    metricCreativity.textContent = creativityScore.toFixed(3);
    fillCreativity.style.width = `${Math.min(100, Math.max(5, creativityScore * 100))}%`;

    // Simulated Response
    simulatedReply.textContent = data.simulated_llm_response || 'No simulated response available.';

    // JSON Payload
    forwardedPayloadCode.textContent = JSON.stringify(data.forwarded_query_payload || {}, null, 2);
  }

  // 5. Modal Handlers
  btnNewKey.addEventListener('click', () => {
    keyModal.classList.remove('hidden');
    newKeyResult.classList.add('hidden');
  });

  const closeModal = () => keyModal.classList.add('hidden');
  btnCloseModal.addEventListener('click', closeModal);
  btnCancelModal.addEventListener('click', closeModal);

  btnConfirmNewKey.addEventListener('click', async () => {
    const clientName = newClientName.value.trim() || 'Custom App Client';
    const tier = newTier.value;

    btnConfirmNewKey.disabled = true;
    try {
      const res = await fetch(`${API_BASE}/auth/keys`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ client_name: clientName, tier }),
      });
      const data = await res.json();
      if (res.ok && data.key_data) {
        const createdKey = data.key_data.api_key;
        newKeyDisplay.textContent = createdKey;
        newKeyResult.classList.remove('hidden');
        apiKeyInput.value = createdKey;
      } else {
        alert(data.detail || 'Could not generate key');
      }
    } catch (e) {
      alert(`Error creating key: ${e.message}`);
    } finally {
      btnConfirmNewKey.disabled = false;
    }
  });

  // Helpers
  function setLoading(isLoading) {
    btnRoute.disabled = isLoading;
    if (isLoading) {
      spinner.classList.remove('hidden');
    } else {
      spinner.classList.add('hidden');
    }
  }

  function showError(msg) {
    errorBox.textContent = msg;
    errorBox.classList.remove('hidden');
  }

  function hideError() {
    errorBox.classList.add('hidden');
  }
});
