const form = document.getElementById('calc-form');
const result = document.getElementById('result');
const chatForm = document.getElementById('chat-form');
const chatResult = document.getElementById('chat-result');
const exampleQuestions = document.querySelectorAll('.example-question');
const modelButtons = document.querySelectorAll('.model-button');
const modelSelected = document.getElementById('model-selected');

let latestEstimate = null;
let selectedModel = 'llama3.1';

function activateModel(model) {
  selectedModel = model;
  modelButtons.forEach((button) => {
    button.classList.toggle('active', button.dataset.model === model);
  });
  modelSelected.textContent = `Selected model: ${model}`;
}

modelButtons.forEach((button) => {
  button.addEventListener('click', () => activateModel(button.dataset.model));
});

form.addEventListener('submit', async (event) => {
  event.preventDefault();
  const payload = Object.fromEntries(new FormData(form).entries());

  const response = await fetch('/api/calculate', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify(payload)
  });

  const data = await response.json();
  if (!response.ok) {
    result.innerHTML = `<strong>Error:</strong> ${data.error}`;
    result.classList.remove('hidden');
    return;
  }

  latestEstimate = data;
  result.innerHTML = `
    <h2>Estimate</h2>
    <p><strong>Classification:</strong> ${data.classification}</p>
    <p><strong>Total hours:</strong> ${data.total_hours}</p>
    <p><strong>Standard hours:</strong> ${data.standard_hours}</p>
    <p><strong>Overtime hours:</strong> ${data.overtime_hours}</p>
    <p><strong>Regular pay:</strong> $${data.regular_pay}</p>
    <p><strong>Overtime pay:</strong> $${data.overtime_pay}</p>
    <p><strong>Total pay:</strong> $${data.total_pay}</p>
    <small>Calculation mode: ${data.mode} (OpenFisca-ready preview)</small>
  `;
  result.classList.remove('hidden');
});

exampleQuestions.forEach((button) => {
  button.addEventListener('click', () => {
    chatForm.elements.message.value = button.textContent;
    chatForm.elements.message.focus();
  });
});

chatForm.addEventListener('submit', async (event) => {
  event.preventDefault();
  const message = chatForm.elements.message.value.trim();
  if (!message) {
    return;
  }

  const response = await fetch('/api/chat', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({message, estimate: latestEstimate, model: selectedModel})
  });
  const data = await response.json();

  if (!response.ok) {
    chatResult.innerHTML = `<strong>Error:</strong> ${data.error}`;
    chatResult.classList.remove('hidden');
    return;
  }

  chatResult.innerHTML = `
    <h3>Assistant reply (${data.model})</h3>
    <p>${data.reply.replace(/\n/g, '<br/>')}</p>
  `;
  chatResult.classList.remove('hidden');
});
