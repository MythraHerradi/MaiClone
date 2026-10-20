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

meta.textContent = 'Le rapport est envoyé automatiquement au support en arrière-plan.';

form.addEventListener('submit', async (event) => {
    event.preventDefault();
    submit.disabled = true;
    submit.textContent = 'Création...';
    result.className = 'result';
    result.textContent = '';

    try {
        const payload = {
            type: form.type.value,
            title: form.title.value.trim(),
            details: form.details.value.trim(),
            email: form.email.value.trim() || null,
            context: context(),
        };

        const response = await fetch('/api/report', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload),
        });
        const reportResult = await response.json();
        if (!response.ok || !reportResult.ok) {
            throw new Error(reportResult.output || 'envoi impossible');
        }
        result.className = 'result ok';
        result.textContent = `Merci, ton erreur a été envoyée (issue #${reportResult.issueNumber}).`;
        form.reset();
    } catch (error) {
        result.className = 'result err';
        result.textContent = `Création impossible : ${error.message}`;
    } finally {
        submit.disabled = false;
        submit.textContent = 'Envoyer le rapport';
    }
});
