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

action.addEventListener('change', updateFields);

form.addEventListener('submit', async (event) => {
    event.preventDefault();
    runButton.disabled = true;
    runButton.textContent = 'Programme en cours...';
    runStatus.textContent = 'En cours';
    output.textContent = 'La commande est en cours d’exécution...';

    const data = new FormData(form);

    try {
        const response = await fetch('/api/run', {
            method: 'POST',
            body: data,
        });
        const result = await response.json();
        output.textContent = `${result.command ? `$ ${result.command}\n\n` : ''}${result.output || 'Aucune sortie.'}`;
        runStatus.textContent = result.ok ? 'Terminé' : 'Erreur';
    } catch (error) {
        output.textContent = `Impossible de joindre le serveur Python.\n\n${error.message}`;
        runStatus.textContent = 'Serveur absent';
    } finally {
        runButton.disabled = false;
        runButton.textContent = 'Lancer le programme';
    }
});

updateFields();