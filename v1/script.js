const form = document.querySelector('#report-form');
const meta = document.querySelector('#meta');
const result = document.querySelector('#result');
const submit = document.querySelector('#submit');
const ISSUE_URL = 'https://github.com/MythraHerradi/MaiClone/issues/new';

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

function buildIssueUrl(payload) {
    const lines = [
        '## Type',
        payload.type,
        '',
        '## Détails',
        payload.details,
        '',
        '## Contact',
        payload.email || 'Non fourni',
        '',
        '## Contexte',
        `- Page: ${payload.context.page}`,
        `- Referrer: ${payload.context.referrer || 'Aucun'}`,
        `- User agent: ${payload.context.userAgent}`,
        `- Langue: ${payload.context.language}`,
        `- Horodatage: ${payload.context.sentAt}`,
    ];

    const params = new URLSearchParams({
        title: `[Bug] ${payload.title}`,
        body: lines.join('\n'),
    });

    return `${ISSUE_URL}?${params.toString()}`;
}

meta.textContent = 'Le rapport ouvre automatiquement un nouvel issue GitHub pré-rempli.';

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

        const issueUrl = buildIssueUrl(payload);
        const openedWindow = window.open(issueUrl, '_blank', 'noopener,noreferrer');
        if (!openedWindow) {
            throw new Error('popup bloquée. Autorise les popups puis réessaie');
        }
        result.className = 'result ok';
        result.textContent = 'Issue GitHub ouverte automatiquement avec ton rapport.';
        form.reset();
    } catch (error) {
        result.className = 'result err';
        result.textContent = `Création impossible : ${error.message}`;
    } finally {
        submit.disabled = false;
        submit.textContent = 'Ouvrir l\'issue GitHub';
    }
});
