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

function downloadReport(payload) {
    const filename = `maiclone-report-${new Date().toISOString().replace(/[:.]/g, '-')}.json`;
    const blob = new Blob([JSON.stringify(payload, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    document.body.append(link);
    link.click();
    link.remove();
    URL.revokeObjectURL(url);
}

meta.textContent = 'Le rapport est créé localement puis téléchargé en JSON.';

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

        downloadReport(payload);
        result.className = 'result ok';
        result.textContent = 'Rapport généré et téléchargé avec succès.';
        form.reset();
    } catch (error) {
        result.className = 'result err';
        result.textContent = `Création impossible : ${error.message}`;
    } finally {
        submit.disabled = false;
        submit.textContent = 'Créer le rapport';
    }
});
