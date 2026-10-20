const form = document.querySelector('#run-form');
const action = document.querySelector('#action');
const prepareFields = document.querySelector('#prepare-fields');
const trainFields = document.querySelector('#train-fields');
const output = document.querySelector('#output');
const runStatus = document.querySelector('#run-status');
const runButton = document.querySelector('.run-button');

function updateFields() {
    const training = action.value === 'train';
    prepareFields.hidden = training;
    trainFields.hidden = !training;
}

function buildSummary(data, archiveFileName) {
    const lines = [
        'Configuration générée côté navigateur (HTML/CSS/JavaScript).',
        '',
        `Action: ${data.action}`,
        `Archive: ${archiveFileName}`,
        `Nom Instagram: ${data.targetName}`,
    ];

    if (data.action === 'prepare') {
        lines.push(`Fichier de sortie: ${data.output || 'data/training.jsonl'}`);
    } else {
        lines.push(`Modèle de base: ${data.baseModel || 'microsoft/Phi-3-mini-4k-instruct'}`);
        lines.push(`Dossier du modèle: ${data.outputDir || 'models/maiclone'}`);
        lines.push(`Epochs: ${data.epochs || '1'}`);
        lines.push(`Batch size: ${data.batchSize || '1'}`);
    }

    lines.push('', 'Aucune exécution serveur n\'est faite: cette page prépare uniquement les paramètres.');
    return lines.join('\n');
}

action.addEventListener('change', updateFields);

form.addEventListener('submit', async (event) => {
    event.preventDefault();
    runButton.disabled = true;
    runButton.textContent = 'Préparation...';
    runStatus.textContent = 'Traitement local';

    const data = Object.fromEntries(new FormData(form).entries());
    const archiveFile = form.querySelector('#archive').files[0];

    if (!archiveFile) {
        output.textContent = 'Sélectionne une archive Instagram (.zip).';
        runStatus.textContent = 'Erreur';
        runButton.disabled = false;
        runButton.textContent = 'Préparer la configuration';
        return;
    }

    output.textContent = buildSummary(data, archiveFile.name);
    runStatus.textContent = 'Prêt';
    runButton.disabled = false;
    runButton.textContent = 'Préparer la configuration';
});

updateFields();
