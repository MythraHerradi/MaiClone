// Le serveur Python relaiera ce rapport vers Grist (la clé API reste côté serveur).
const REPORT_ENDPOINT = '/api/report';

const form = document.querySelector('#report-form');
const meta = document.querySelector('#meta');
const result = document.querySelector('#result');
const submit = document.querySelector('#submit');

const params = new URLSearchParams(location.search);
if (params.get('type')) form.type.value = params.get('type');
if (params.get('title')) form.title.value = params.get('title');
if (params.get('details')) form.details.value = params.get('details');

function context() {
    return {
        referrer: document.referrer || null,
        page: location.href,
        userAgent: navigator.userAgent,
        language: navigator.language,
        sentAt: new Date().toISOString(),
    };
}

meta.textContent = `Infos jointes automatiquement : navigateur, langue, page et date.`;

form.addEventListener('submit', async (event) => {
    event.preventDefault();
    submit.disabled = true;
    submit.textContent = 'Envoi...';
    result.className = 'result';
    result.textContent = '';

    const payload = {
        type: form.type.value,
        title: form.title.value.trim(),
        details: form.details.value.trim(),
        email: form.email.value.trim() || null,
        context: context(),
    };

    try {
        const response = await fetch(REPORT_ENDPOINT, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload),
        });
        if (!response.ok) {
            const body = await response.json().catch(() => ({}));
            throw new Error(body.error || body.detail || `HTTP ${response.status}`);
        }
        result.className = 'result ok';
        result.textContent = 'Merci, le rapport a bien été envoyé.';
        form.reset();
    } catch (error) {
        result.className = 'result err';
        result.textContent = `Envoi impossible : ${error.message}`;
    } finally {
        submit.disabled = false;
        submit.textContent = 'Envoyer le rapport';
    }
});
